#!/usr/bin/env python3

import datetime
from inspiderweb.log import logger, logcontrol
from inspiderweb.database import Database
from inspiderweb.dotgraph import DotGraph
import sys
import argparse
from argparse import RawDescriptionHelpFormatter
import os.path
import re
import os

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
                                          'Supply in/output paths...')
action_options = parser.add_argument_group('Action Options',
                                           'What do you want to do?')
misc_options = parser.add_argument_group('Misc', 'Misc Options')

setup_options.add_argument("-d", "--database", required=True,
                           help="Pickle database (db) file. Multiple db files "
                                "are supported. In this case the first one "
                                "will be used to save the resulting merged db",
                           type=str, nargs="+")

setup_options.add_argument("-o", "--output", required=False,
                           help="Output dot file.",
                           type=str)
# todo: rather allow three options:
# -s --searchstring: inspire search
# -r --recids: recids
# -b --bibkeys: file containing bibkeys (will be regexed). Or directory which
#               will be recursively regexed.
setup_options.add_argument("-r", "--recids", required=False,
                           help="Input file with recids as seeds. Multiple "
                                "files are supported.",
                           type=str, nargs="+", default=[])
setup_options.add_argument("-s", "--searchstring", required=False,
                           help="Take the results of inspirehep search query "
                                "(search string you would enter in the "
                                "inspirehep online search "
                                "form) as seeds. Multiple search strings "
                                "supported.",
                           type=str, nargs="+", default=[])
setup_options.add_argument("-b", "--bibkeys", required=False,
                           help="Path of a file or a directory. If the path"
                                "points to a file, it is searched for "
                                "bibkeys, which are then used as seeds. If the"
                                "path points to a directory, we recursively"
                                "go into it (excluding hidden files) and "
                                "search every file for bibkeys.",
                           type=str, nargs="+", default=[])

action_options.add_argument("-p", "--plot", required=False,
                            action="store_true",
                            help="Generate dot output (i.e. plot).",
                            default=False)
action_options.add_argument("-u", "--updateseeds", required=False,
                            help="Get specified information for the seeds. "
                                 "Multiple arguments are supported. ",
                            type=str, default="", nargs="+",
                            choices=["refs", "cites", "bib"])
action_options.add_argument("-t", "--updatedb", required=False,
                            help="Get specified information for the records in"
                                 " the database. "
                                 "Multiple arguments are supported. ",
                            type=str, default="", nargs="+",
                            choices=["refs", "cites", "bib"])

misc_options.add_argument("-h", "--help",
                          help="Print this help message.", action="help")
misc_options.add_argument("--rank", required=False,
                          help="Rank by [year]", default="",
                          type=str,
                          choices=["year"])
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

if args.plot and not args.seeds:
    logger.critical("We need seeds to plot. Exiting.")
    sys.exit(10)
if args.plot and not args.output:
    logger.critical("We need output filename to plot. Exiting.")
    sys.exit(20)
if args.updateseeds and not args.seeds:
    logger.critical("We need seeds to update seeds. Exiting.")
    sys.exit(30)

# todo: maybe use a proper format to save the record data or at least allow ...
# .... to export into such
# todo: add clusters
# todo: extract more infomration; add title as tooltip
# todo: control verbosity

db = Database(args.database[0])
db.load()

for path in args.database[1:]:
    db.load(path)

db.statistics()

recids = set()

for recidsfile in args.recids:
    new_recids = set()
    with open(recidsfile, "r") as seedfile_stream:
        for i, line in enumerate(seedfile_stream):
            if (i + 1) == args.maxseeds:
                # if args.maxseeds == 0 (default), this will never run
                break
            line = line.replace('\n', "").strip()
            if not line:
                continue
            new_recids.add(line)
    logger.info("Got {} seeds from file {}.".format(len(new_recids),
                                                     recidsfile))
    recids.update(new_recids)

for search in args.searchstring:
    new_recids = db.get_recids_from_search(search)
    logger.info("Got {} seeds from search query {}.".format(len(new_recids),
                                                            search))


def get_bibkeys_from_file(bibpath):
    bibkey_regex = re.compile(r"[a-zA-Z]{1,20}:[0-9]{4}[a-z]{0,10}")
    with open(bibpath, "r") as bibfile:
        bibkeys = set()
        for bibline in bibfile:
            bibkeys.update(bibkey_regex.findall(bibline))
    bibkey_recids = db.get_recids_from_bibkeys(bibkeys).keys()
    return bibkey_recids

for path in args.bibkeys:
    new_recids = set()
    if not os.path.exists(path):
        logger.critical("Input file {} does not exist. Abort.".format(path))
        sys.exit(50)
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            # fixme: skip hidden files
            for file in files:
                these_new_recids = \
                    get_bibkeys_from_file(os.path.join(root, file))
                logger.info("Got {} seeds from bibkeys from file {}.".format(
                    len(these_new_recids), path))

    if os.path.isfile(path):
        new_recids = get_bibkeys_from_file(path)
        recids.update(new_recids)
        logger.info("Got {} seeds from bibkeys from file {}.".format(
            len(new_recids), path))

db.autocomplete_records(args.updateseeds, force=args.forceupdate,
                        recids=recids)
db.autocomplete_records(args.updatedb, force=args.forceupdate)

if args.plot:

    dg = DotGraph(db)

    # ALWAYS END EVERYTHING WITH A SEMICOLON
    # EXCEPT THINGS IN SQUARE BRACKETS: USE COMMA
    # todo: move that to config or something
    graph_style = \
        "graph [label=\"inspiderweb {date} {time}\", fontsize=40];".format(
            date=str(datetime.date.today()),
            time=str(datetime.datetime.now().time()))
    node_style = "node[fontsize=20, fontcolor=black, fontname=Arial, " \
                 "style=filled, color=green];"
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

    # todo: Add otion to customize this
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
