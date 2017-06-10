#!/usr/bin/env python3

from inspiderweb.log import logcontrol, logger
import sys
from inspiderweb.database import Database
from inspiderweb.dotgraph import DotGraph
from inspiderweb.recidextractor import get_recid_from_queries, \
    get_recids_from_bibkey_paths, get_recids_from_url_paths, \
    get_recids_from_recid_paths
from inspiderweb.cli import cli_parser, get_plot_connections
import configparser

""" Main file of inspiderweb: Tool to analyze paper reference networks.
Currently hosted at: https://github.com/klieret/inspiderweb

Run this file via `python3 inspiderweb.py --help` for instructions on
usage. """

args = cli_parser.parse_args()

print(args.plot)

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
db.load(args.database)
db.statistics()

# get recids
recids = set()
recids.update(get_recid_from_queries(args.queries, db=db))
recids.update(get_recids_from_bibkey_paths(args.bibkeypaths, db=db))
recids.update(get_recids_from_recid_paths(args.recidpaths))
recids.update(get_recids_from_url_paths(args.urlpaths))

db.autocomplete_records(args.get, force=args.forceupdate, recids=recids)

if args.labels:
    db.get_labels_from_file(args.labels)

if args.plot:

    config = configparser.ConfigParser()
    config.read(args.config)

    dg = DotGraph(db, config["dotgraph"])
    dg.add_connections(get_plot_connections(args.plot, recids, db))
    dg.generate_dot_str(rank=args.rank)
    dg.write_to_file(args.output)

db.save()
