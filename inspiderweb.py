#!/usr/bin/env python3

import datetime
from inspiderweb.log import logger, logcontrol
from inspiderweb.database import Database
from inspiderweb.dotgraph import DotGraph, valid_connection
import argparse
from argparse import RawDescriptionHelpFormatter
from inspiderweb.recidextractor import *

""" Main file of inspiderweb: Tool to analyze paper reference networks.
Currently hosted at: https://github.com/klieret/inspiderweb

Run this file via `python3 inspiderweb.py --help` for instructions on
usage. """

# todo: move that to another file so that this file stays easily modifyable etc.
description = r"""
    INSPIDERWEB
 `.,-'\_____/`-.,'     Tool to analyze networks papers referencing and citing each
  /`..'\ _ /`.,'\      other. It acts as a web-crawler, extracting information from
 /  /`.,' `.,'\  \     inspirehep, then uses the dot languageto describe the
/__/__/     \__\__\__  network. The result can then be plotted by the graphviz
\  \  \     /  /  /    Package and similar programs.
 \  \,'`._,'`./  /     More info on the github page
  \,'`./___\,'`./      https://github.com/klieret/inspiderweb
 ,'`-./_____\,-'`.
     /       \
"""


# Use the RawTextHelpFormatter in order to allow linebreaks in the description
parser = argparse.ArgumentParser(description=description,
                                 prog="python3 inspiderweb.py",
                                 formatter_class=RawDescriptionHelpFormatter,
                                 add_help=False)

setup_options = parser.add_argument_group('Setup/Configure Options',
                                          'Supply in/output paths. Note that '
                                          'in most cases, seeds are only '
                                          'added to the database if we '
                                          'perform some action.')
action_options = parser.add_argument_group('Action Options',
                                           'What do you want to do?')
misc_options = parser.add_argument_group('Additional Options',
                                         'Further Configuration...')

setup_options.add_argument("-d", "--database", required=True,
                           help="Pickle database (db) file. Multiple db files "
                                "are supported. In this case the first one "
                                "will be used to save the resulting merged db",
                           type=str, nargs="+")
setup_options.add_argument("-o", "--output", required=False,
                           help="Output dot file.",
                           type=str)
setup_options.add_argument("-r", "--recidpaths", required=False,
                           help="Path of a file or a directory. Multiple paths"
                                "are supported. If the path "
                                "points to a file, each line of the file is "
                                "interpreted as a recid. The collected recids"
                                "are then used as seeds. If the"
                                "path points to a directory, we recursively"
                                "go into it (excluding hidden files) and "
                                "extract recids from every file.",
                           type=str, nargs="+", default=[])
setup_options.add_argument("-q", "--queries", required=False,
                           help="Take the results of inspirehep search query "
                                "(search string you would enter in the "
                                "inspirehep online search "
                                "form) as seeds. Multiple search strings "
                                "supported.",
                           type=str, nargs="+", default=[])
setup_options.add_argument("-b", "--bibkeypaths", required=False,
                           help="Path of a file or a directory. Multiple paths"
                                " are supported. If the path "
                                "points to a file, the file is searched for "
                                "bibkeys, which are then used as seeds. If the"
                                "path points to a directory, we recursively"
                                "go into it (excluding hidden files) and "
                                "search every file for bibkeys.",
                           type=str, nargs="+", default=[])
setup_options.add_argument("-u", "--urlpaths", required=False,
                           help="Path of a file or a directory. If the path "
                                "points to a file, the file is searched for "
                                "inspirehep urls, from which the recids are "
                                "extracted and used as seeds. If the"
                                "path points to a directory, we recursively"
                                "go into it (excluding hidden files) and "
                                "search every file for bibkeys.",
                           type=str, nargs="+", default=[])

# fixme: make that accept arguments on what to plot; combine that with what to download
# todo: make request automatically download stuff it isn't there?
# mayybe it's best to always use db.get_citations and db.get_... instead of
# gettingn the record and using its internal variables...
# a combination of the following:
# -seeds
# -seeds.refs
# -seeds.cites
# -seeds.refs.refs
# -seeds.cites.cites
# similar with all....
# as for implementation: method takes

plot_help = "Generate dot output (i.e. plot). If you do not specify an " \
            "option, only connections between seeds are plotted (this is the" \
            "same as specifying 'seeds>seeds' or 's>s'. If you want to " \
            "customize this, you can supply several rules of the following " \
            "form: 'source selection'>'target selection'. The selections" \
            "for source targets are of the form {seeds,all}[.{refs, cites," \
            "refscites}]. Where e.g. seeds.refscites means that all records" \
            "being cited by a seed or citing a seed are valid starting points"\
            "of an arrow. Short options: s (seeds), a (all), r (refs), c " \
            "(cites). For 'refscites', the following alias exist: " \
            "'citesrefs', 'cr', 'rc'. "

action_options.add_argument("-p", "--plot", required=False,
                            help=plot_help,
                            type=str,
                            default="seeds>seeds",
                            nargs="*")

update_help = "Download information. Multiple arguments are supported. " \
              "Each argument must look like this: Starts with 'seeds' or " \
              "'all' (depending on whether every db entry or just the seeds" \
              " will be taken as starting point). Just 'seeds' (short 's') "\
              "or 'all' (short 'a') will" \
              " only download the bibliographic information for every item. " \
              "Furthermore, there are the following options: " \
              "(1) 'refs' (short 'r'): References of each recid " \
              "(2) 'cites' (short 'c'): Citations of each recid " \
              "(3) 'refscites' or 'citesrefs' (short 'rc' or 'cr'): both. " \
              "These options can be chained, e.g. seeds.refs.cites means " \
              "1. For each seed recid, get all reference "\
              "2. For all of the above, get all citations. " \
              "Similarly one could have written 's.r.c'. "

action_options.add_argument("-g", "--get", required=False,
                            help=update_help,
                            type=str, default="", nargs="+")

misc_options.add_argument("-h", "--help",
                          help="Print this help message.", action="help")
misc_options.add_argument("--rank", required=False,
                           help="Rank by [year]", default="",
                          type=str,
                          choices=["year"])
# fixme: reimplement
misc_options.add_argument("--maxseeds", required=False, type=int,
                          help="Maximum number of seeds (for testing "
                               "purposes).",
                          default=0)
misc_options.add_argument("--forceupdate", action="store_true",
                          help="For all information that we get from the "
                               "database: Force redownload")
misc_options.add_argument("-v" "--verbosity", required=False, type=str,
                          help="Verbosity",
                          choices=["debug", "info", "warning", "error",
                                   "critical"],
                          default="debug", dest="verbosity")

args = parser.parse_args()
logcontrol.set_verbosity_from_argparse(args.verbosity)

# fixme: add tests again
if args.plot and not args.output:
    logger.critical("We need output filename to plot. Exiting.")
    sys.exit(20)

# todo: maybe use a proper format to save the record data or at least allow ...
# .... to export into such
# todo: add clusters
# todo: extract more infomration; add title as tooltip

# fixme: Restore .travis to specific tests again.

db = Database(args.database[0])
db.load()

for path in args.database[1:]:
    db.load(path)

db.statistics()

recids = set()


recids.update(get_recid_from_queries(args.queries, db=db))
recids.update(get_recids_from_bibkey_paths(args.bibkeypaths, db=db))
recids.update(get_recids_from_recid_paths(args.recidpaths))
recids.update(get_recids_from_url_paths(args.urlpaths))

db.autocomplete_records(args.get, force=args.forceupdate, recids=recids)


if args.plot:

    dg = DotGraph(db)

    # ALWAYS END EVERYTHING WITH A SEMICOLON
    # EXCEPT THINGS IN SQUARE BRACKETS: USE COMMA
    # todo: move that to config or something
    graph_style = \
        "graph [label=\"inspiderweb {date} {time}\", fontsize=60];".format(
            date=str(datetime.date.today()),
            time=str(datetime.datetime.now().time()))
    node_style = "node[fontsize=25, fontcolor=black, fontname=Arial, " \
                 "style=filled, color=red, fontcolor=white, shape=note];"
    # size = 'ratio="0.3";'#''size="14,10";'
    # size = 'overlap=prism; overlap_scaling=0.01; ratio=0.7'
    size = ";"
    style = '\n'.join([graph_style, node_style, size])
    dg._style = style
    # "//ratio=\"1:1\";\n"
    #      "//ratio=\"fill\";\n"
    #      "//size=\"11.692,8.267\"; \n"
    #      "//size=\"16.53,11.69\"; //a3\n"
    #      "//size=\"33.06,11.69\"\n"

    # fixme: use new code!
    #  want to support the following options
    # Just don't require bibkey. Right now we're always getting it anyways
    # possibilities: list of <start> > <end> strings
    # with default to seeds>seeds (s>s) (note always use qutations)
    # other options: .refs, .cites, .refcites, .citerefs
    # add extra option to plot lonely seeds or db items.


    def valid_connection(source, target):
        sr = db.get_record(source)
        tr = db.get_record(target)
        return sr.bibkey and tr.bibkey and source in recids and target in recids

    # fixme: use getter to get all records
    for recid, record in db._records.items():
        for referece_recid in record.references:
            if not valid_connection(record.recid, referece_recid):
                continue
            dg.add_connection(record.recid, referece_recid)
        for citation_recid in record.citations:
            if not valid_connection(record.recid, citation_recid):
                continue
            dg.add_connection(citation_recid, record.recid)

    dg.generate_dot_str(rank=args.rank)
    dg.write_to_file(args.output)

db.save()
