#!/usr/bin/env python3

import datetime
from inspiderweb.log import logger, logcontrol
from inspiderweb.database import Database
from inspiderweb.dotgraph import DotGraph, valid_connection
from inspiderweb.recidextractor import *
from inspiderweb.cli import args
import configparser

""" Main file of inspiderweb: Tool to analyze paper reference networks.
Currently hosted at: https://github.com/klieret/inspiderweb

Run this file via `python3 inspiderweb.py --help` for instructions on
usage. """


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

    config = configparser.ConfigParser()
    config.read("config/default.config")
    print(args.config, config, config.sections())
    dg = DotGraph(db, config["dotgraph"])

    # ALWAYS END EVERYTHING WITH A SEMICOLON
    # EXCEPT THINGS IN SQUARE BRACKETS: USE COMMA
    # todo: move that to config or something

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
