#!/usr/bin/env python3

import datetime
from inspiderweb.log import logger
from inspiderweb.database import Database
from inspiderweb.dotgraph import DotGraph
import sys
import argparse
from argparse import RawTextHelpFormatter

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


parser = argparse.ArgumentParser(description=description,
                                 prog="inspiderweb.py",
                                 formatter_class=RawTextHelpFormatter,
                                 add_help=False)

setup_options = parser.add_argument_group('Setup/Configure Options',
                                          'Supply in/output paths...')
action_options = parser.add_argument_group('Action Options',
                                           'What do you want to do?')
misc_options = parser.add_argument_group('Misc', 'Misc Options')

setup_options.add_argument("-d", "--database", required=True,
                           help="Required: Pickle database file.",
                           type=str)
setup_options.add_argument("-o", "--output", required=False,
                           help="Output dot file.",
                           type=str)
setup_options.add_argument("-s", "--seeds", required=False,
                           help="Input seed file.",
                           type=str)

action_options.add_argument("-p", "--plot", required=False,
                            action="store_true",
                            help="Generate dot output (i.e. plot).",
                            default=False)
action_options.add_argument("-u", "--updateseeds", required=False,
                            help="Get the following information for the seeds:"
                                 "'[bib],[cites],[refs]'",
                            type=str, default="")
action_options.add_argument("-t", "--updatedb", required=False,
                            help="Update db with the following information: "
                                 "'[bib],[cites],[refs]'",
                            type=str, default="")

misc_options.add_argument("-h", "--help",
                          help="Print help message", action="help")
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

args = parser.parse_args()

if args.plot and not args.seeds:
    logger.error("We need seeds to plot. Exiting.")
    sys.exit(10)
if args.plot and not args.output:
    logger.error("We need output filename to plot. Exiting.")
    sys.exit(20)
if args.updateseeds and not args.seeds:
    logger.error("We need seeds to update seeds. Exiting.")
    sys.exit(30)

# todo: Use API instead of parsing. But I don't see where there is a clear ...
# ...link to cited documents....
# todo: add docstrings
# todo: maybe use a proper format to save the record data or at least allow ...
# .... to export into such
# todo: add clusters
# todo: extract more infomration; add title as tooltip

db = Database(args.database)
db.load()
db.statistics()

seeds = []
if args.seeds:
    with open(args.seeds, "r") as seedfile:
        for i, line in enumerate(seedfile):
            if (i + 1) == args.maxseeds:
                # if args.maxseeds == 0 (default), this will never run
                break
            line = line.replace('\n', "")
            line = line.strip()
            if not line:
                continue
            seeds.append(line)
    logger.info("Read {} seeds from file {}.".format(len(seeds), args.seeds))

if args.updateseeds:
    updates = args.updateseeds.split(',')
    for update in updates:
        if update not in ["bib", "cites", "refs"]:
            logger.warning("Unrecognized information to get "
                           "for seeds: {}".format(update))

    # todo: this is basically a copy of what is being done in ...
    # ... db.autocomplete_records... maybe join both?
    saveevery = 5
    for i, seed in enumerate(seeds):
        if i % saveevery == 0:
            db.save()
        record = db.get_record(seed)
        if "bib" in updates:
            record.get_info(force=args.forceupdate)
        if "cites" in updates:
            record.get_citations(force=args.forceupdate)
        if "refs" in updates:
            record.get_references(force=args.forceupdate)
        db.update_record(record.mid, record)

        # add citations/references to db
        for related in record.citations + record.references:
            db.get_record(related)

if args.updatedb:
    updates = args.updateseeds.split(',')
    for update in updates:
        if update not in ["bib", "cites", "refs"]:
            logger.warning("Unrecognized information to get "
                           "for seeds: {}".format(update))
    db.autocomplete_records(force=args.forceupdate,
                            info=("bib" in updates),
                            references=("refs" in updates),
                            citations=("cites" in updates))

if args.plot:

    dg = DotGraph(db)

    graph_style = \
        "graph [label=\"inspiderweb {date} {time}\", fontsize=40];".format(
            date=str(datetime.date.today()),
            time=str(datetime.datetime.now().time()))
    node_style = "node[fontsize=20, fontcolor=black, fontname=Arial, " \
                 "style=filled, color=green];"
    # fixme: why is there still no line break/semicolon after this?
    size = 'ratio="0.3";'#''size="14,10";'
    # size = 'overlap=prism; overlap_scaling=0.01; ratio=0.7'
    size = ";"
    style = graph_style + node_style + size
    dg._style = style
    # "//ratio=\"1:1\";\n"
    #      "//ratio=\"fill\";\n"
    #      "//size=\"11.692,8.267\"; \n"
    #      "//size=\"16.53,11.69\"; //a3\n"
    #      "//size=\"33.06,11.69\"\n"

    # fixme: Add otion to customize this
    def valid_connection(source, target):
        sr = db.get_record(source)
        tr = db.get_record(target)
        return sr.bibkey and tr.bibkey and source in seeds and target in seeds

    # fixme: use getter to get all records
    for mid, record in db._records.items():
        for reference_mid in record.references:
            if not valid_connection(record.mid, reference_mid):
                continue
            dg.add_connection(record.mid, reference_mid)
        for citation_mid in record.citations:
            if not valid_connection(record.mid, citation_mid):
                continue
            dg.add_connection(citation_mid, record.mid)

    dg.generate_dot_str(rank=args.rank)
    dg.write_to_file(args.output)

db.save()
