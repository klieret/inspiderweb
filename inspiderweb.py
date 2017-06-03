#!/usr/bin/env python3

import collections
import datetime
import logging
from inspiderweb.database import Database
from inspiderweb.dotgraph import DotGraph

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
#db.load_records_from_urls("insire_urls_example.txt")
#db.autocomplete_records()

#sys.exit(0)

db.save()



dg = DotGraph(db)

graph_style = \
    "graph [label=\"inspiderweb {date} {time}\", fontsize=40];".format(
        date=str(datetime.date.today()),
        time=str(datetime.datetime.now().time()))
node_style = "node[fontsize=20, fontcolor=black, fontname=Arial, shape=box];"
size = ''#''size="14,10";'
style = graph_style + node_style + size
# "//ratio=\"1:1\";\n"
#      "//ratio=\"fill\";\n"
#      "//size=\"11.692,8.267\"; \n"
#      "//size=\"16.53,11.69\"; //a3\n"
#      "//size=\"33.06,11.69\"\n"

valid_source_id = lambda mid: db.get_record(mid).is_complete()
valid_target_id = lambda mid: db.get_record(mid).is_complete()

for mid, record in db._records.items():
    for reference_id in record.references:
        if not valid_target_id(reference_id):
            continue
        if not valid_source_id(mid):
            continue
        dg.add_connection(record.mid, reference_id)
    for citation_id in record.citations:
        if valid_source_id(citation_id):
            continue
        if valid_source_id(mid):
            continue
        dg.add_connection(citation_id, record.mid)


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

