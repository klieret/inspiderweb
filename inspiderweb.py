#!/usr/bin/env python3

import collections
import datetime
import logging
from inspiderweb.database import Database
from inspiderweb.dotgraph import DotGraph
import sys

# todo: add docstrings
# todo: separate in several scripts, that download information or plot the graph
# todo: add argparse interface
# todo: maybe use a proper format to save the record data or at least allow to export into such
# todo: add clusters
# todo: make clickable
# todo: extract more infomration; add title as tooltip

logger = logging.getLogger("inspirespider")
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
fm = logging.Formatter("%(levelname)s: %(message)s")
sh.setFormatter(fm)
logger.addHandler(sh)
logger.addHandler(sh)

# fixme: Use API instead of parsing. But I don't see where there is a clear link to cited documents....

clusters = collections.defaultdict(set)

db = Database("pickle.pickle")


db.load()
db.statistics()
#db.load_records_from_urls("inspire_urls_example.txt")
#db.autocomplete_records()

#sys.exit(0)

# db.save()

seeds = []
with open("seed_ids_all.txt", "r") as seedfile:
    for line in seedfile:
        line = line.replace('\n', "")
        line = line.strip()
        if not line:
            continue
        seeds.append(line)

for seed in seeds:
    record = db.get_record(seed)
    # record.autocomplete()
    for citation in record.references:
        # print(citation, citation in db._records)
        r = db.get_record(citation)
        db.update_record(r.mid, r)
        # print(citation, citation in db._records)
    for citation in record.citations:
        # print(citation, citation in db._records)
        r = db.get_record(citation)
        db.update_record(r.mid, r)
        # print(citation, citation in db._records)


# db.statistics()
# print(db.statistics())

# db.autocomplete_records(citations=False, references=False)
# db.save()

# sys.exit(0)

# print("seeds", seeds)

dg = DotGraph(db)

graph_style = \
    "graph [label=\"inspiderweb {date} {time}\", fontsize=40];".format(
        date=str(datetime.date.today()),
        time=str(datetime.datetime.now().time()))
node_style = "node[fontsize=20, fontcolor=black, fontname=Arial, shape=box];"
# size = 'ratio="0.5";'#''size="14,10";'
# size = 'overlap=prism; overlap_scaling=0.01; ratio=0.7'
size=";"
style = graph_style + node_style + size
dg.style = style
# "//ratio=\"1:1\";\n"
#      "//ratio=\"fill\";\n"
#      "//size=\"11.692,8.267\"; \n"
#      "//size=\"16.53,11.69\"; //a3\n"
#      "//size=\"33.06,11.69\"\n"

valid_source_id = lambda mid: db.get_record(mid).is_complete() and mid in seeds
valid_target_id = lambda mid: db.get_record(mid).is_complete() and mid in seeds

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

import collections
node_ids_by_year = collections.defaultdict(set)
import re
year_regex = re.compile(r".*:([0-9]{4}).*")

for node_id in all_node_ids:
    bibkey = db.get_record(node_id).bibkey
    try:
        year = year_regex.match(bibkey).group(1)
    except:
        continue
    print(node_id, bibkey, year)
    node_ids_by_year[year].add(node_id)



string = "\t{\n \tnode [shape=circle, fontsize=16, style=filled, color=yellow];"

string += "->".join(list(sorted(node_ids_by_year.keys(), reverse=True)))
string += "}\n"

for year, node_ids in node_ids_by_year.items():
    string += "\t {{rank=same; {}; {} }}\n".format(year, "; ".join(node_ids))
dg.rank_specs += string

# for mid in seeds:
#      dg.add_node(mid, 'label="{}",color="cadetblue",style="filled"'.format(
#          db.get_record(mid).label))


dg.generate_dot_str()
dg.write_to_file("dotfile.dot")



# if do_clusters:
#     for root, dirs, files in os.walk(material_folder):
#         for file in files:
#             if os.path.splitext(file)[1] in [".pdf", ".ps", ".djvu"]:
#                 mid = os.path.basename(file)[0:4]
#                 clustername = os.path.join(*os.path.relpath(root, material_folder).split(os.sep)[:max_cluster_depth])
#                 if not clustername:
#                     clustername = "ROOT"
#                 clusters[clustername].add(mid)
#                 # NOTE: Not supported to have node in several clusters
#                 # for i in range(len(relpath)):
#                 #     partial_path = relpath.split(os.sep)[:i]
#                 #     if not partial_path:
#                 #         partial_path = ["ROOT"]
#                 #     # print(partial_path)
#                 #     partial_path = os.path.join(*partial_path)
#                 #     clustername = os.path.basename(partial_path)
#                 #     # if not clustername:
#                 #     #     clustername = "ROOT"
#                 #     print(clustername)
#                 #     clusters[clustername].add(mid)

