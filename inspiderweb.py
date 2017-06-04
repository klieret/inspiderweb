#!/usr/bin/env python3

import collections
import datetime
import inspiderweb.log
import logging
from inspiderweb.database import Database
from inspiderweb.dotgraph import DotGraph
import sys

logger = logging.getLogger("inspirespider")

# todo: Use API instead of parsing. But I don't see where there is a clear link to cited documents....
# todo: add docstrings
# todo: separate in several scripts, that download information or plot the graph
# todo: add argparse interface
# todo: maybe use a proper format to save the record data or at least allow to export into such
# todo: add clusters
# todo: extract more infomration; add title as tooltip

db = Database("pickle.pickle")


db.load()
db.statistics()
#db.load_records_from_urls("inspire_urls_example.txt")
#db.autocomplete_records()

seeds = []
max_seeds = 20
i=0
with open("seed_ids_all.txt", "r") as seedfile:
    for line in seedfile:
        # i+=1
        if i==max_seeds:
            break
        line = line.replace('\n', "")
        line = line.strip()
        if not line:
            continue
        seeds.append(line)

for seed in seeds:
    record = db.get_record(seed)
    # record.autocomplete()
    for citation in record.references:
        r = db.get_record(citation)
        db.update_record(r.mid, r)
    for citation in record.citations:
        r = db.get_record(citation)
        db.update_record(r.mid, r)



dg = DotGraph(db)

graph_style = \
    "graph [label=\"inspiderweb {date} {time}\", fontsize=40];".format(
        date=str(datetime.date.today()),
        time=str(datetime.datetime.now().time()))
node_style = "node[fontsize=20, fontcolor=black, fontname=Arial, style=filled, color=green];"
# size = 'ratio="0.5";'#''size="14,10";'
# size = 'overlap=prism; overlap_scaling=0.01; ratio=0.7'
size=";"
style = graph_style + node_style + size
dg._style = style
# "//ratio=\"1:1\";\n"
#      "//ratio=\"fill\";\n"
#      "//size=\"11.692,8.267\"; \n"
#      "//size=\"16.53,11.69\"; //a3\n"
#      "//size=\"33.06,11.69\"\n"

valid_source_id = lambda mid: db.get_record(mid).is_complete() #and mid in seeds
valid_target_id = lambda mid: db.get_record(mid).is_complete() #and mid in seeds

all_node_ids = set()

for mid, record in db._records.items():
    for reference_id in record.references:
        if not valid_target_id(reference_id):
            continue
        if not valid_source_id(mid):
            continue
        all_node_ids.add(record.mid)
        all_node_ids.add(reference_id)
        dg.add_connection(record.mid, reference_id)
    for citation_id in record.citations:
        if not valid_source_id(citation_id):
            continue
        if not valid_target_id(mid):
            continue
        dg.add_connection(citation_id, record.mid)
        all_node_ids.add(record.mid)
        all_node_ids.add(citation_id)

dg.generate_dot_str(rank="year")
dg.write_to_file("dotfile.dot")
