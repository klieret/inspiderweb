#!/usr/bin/env python3

import os
import re
import collections
import sys
import datetime
from field_from_mid import init_mid_to_bib_paths, extract_field
import logging

logger = logging.getLogger("inspirespider")
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
fm = logging.Formatter("%(levelname)s: %(message)s")
sh.setFormatter(fm)
logger.addHandler(sh)
logger.addHandler(sh)

mid_to_bib_paths = init_mid_to_bib_paths()

material_folder = os.path.expanduser("~/Dropbox/db_master/material/material/")
citation_folder = os.path.expanduser("~/Dropbox/db_master/material/marc/")

clusters = collections.defaultdict(set)

do_clusters = True
hide_unrelated = True
max_cluster_depth = 2

seeds = []  # initial papers I'm interested in


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


#print(clusters)
#sys.exit(1)


class Record(object):
    def __init__(self, inspire_url, label=None):
        self.inspire_url = inspire_url
        self.label = label
        self.id = self.inspire_url.split('/')[-1]
        # if label:
        #     self.label = label
        # else:
        #     self.label = self.inspire_url.split('/')[-1]


# http://i.imgur.com/gOPS2.png
record_regex = re.compile("/record/([0-9]*)")
def extract_records(string):
    # goes fro string, looking for every record url
    records = record_regex.findall(string)
    return records

def get_cited_by(record):
    pass

def get_references(record):
    pass

logger.debug("Started going files.")
connections = set()
#hep_to_mref = {}
for filename in os.listdir(citation_folder):
    with open(os.path.join(citation_folder, filename), "r") as citefile:
        records = extract_records(citefile.read())
        this_record = records[0]  # fixme: this is a hack; we should know this form before
        mid = os.path.splitext(os.path.basename(filename))[0] # fixme: not done properly either
        #hep_to_mref[this_record] = mid
        these_connections = set([(this_record, record) for record in records if
                           not this_record == record])
        connections.update(these_connections)
        # this_record = None
        # for line in citefile:
        #     if not line:
        #         continue
        #     if record_regex.search(line):
        #         record = record_regex.search(line).group(1)
        #         if not this_record:
        #             this_record = record
        #             mid = os.path.splitext(os.path.basename(filename))[0]
        #             hep_to_mref[this_record] = mid
        #         if not this_record == record:
        #             dot_connections.append((this_record, record))

logger.debug("Finished doing so")
logger.debug("Added a total of {} connections.".format(len(connections)))

keys = [item[0] for item in connections]
allowed_items = keys

# Limit ourselfs to a certain subset of possible papers
# Filter connections
# another possiblilty would to just not add them from before,
# which might improve performance but is less flexible to use
filtered_connections = set([connection for connection in connections
                            if connection[0] in allowed_items and
                            connection[1] in allowed_items])
logger.debug("After filtering, I have {} connections.".format(len(filtered_connections)))

#my_dots = set()
#for dot_connection in dot_connections:
#    my_dots.add(hep_to_mref[dot_connection[0]])

#my_dot_connections = []
# for dot_connection in dot_connections:
#     if not dot_connection[1] in hep_to_mref:
#         continue
#     if hep_to_mref[dot_connection[1]] in my_dots:
#         my_dot_connections.append((hep_to_mref[dot_connection[0]],
#                                    hep_to_mref[dot_connection[1]]))


class DotGraph(object):
    def __init__(self):
        self.dot_str = ""

    def start_digraph(self, style=""):
        self.dot_str += "digraph g {\n"
        indented = ";\n".join(['\t' + line for line in style.split(';')
                               if line])
        self.dot_str += indented

    def end_digraph(self):
        self.dot_str += "}"

    def add_cluster(self, records, style=""):
        # for cluster, items in clusters.items():
        self.dot_str += '\tsubgraph "cluster_{}" {{\n'.format(cluster)
        self.dot_str += ("\tfontname=Courier;\n"
                         "\tfontcolor=red;\n"
                         "\tpenwidth=3;\n"
                         "\tfontsize=50;\n"
                         "\tcolor=\"red\";\n"
                         "\tstyle=\"filled\";\n"
                         "\tfillcolor=\"gray97\";\n")
        self.dot_str += '\tlabel="{}";\n'.format(cluster)
        for record in records:
            self.dot_str += '\t\t"{}" [label="{}"];\n'.format(
                record.id, record.label)
        self.dot_str += "\t}\n"

    def add_connection(self, start, end):
        self.dot_str += '\t"{}" -> "{}"; \n'.format(dot_connection[0],
                                                    dot_connection[1])

    def return_dot_str(self):
        return self.dot_str

    def write_to_file(self, filename):
        with open(filename, "w") as dotfile:
            dotfile.write(self.dot_str)

dg = DotGraph()

graph_style = \
    "graph [label=\"Network as of {date} {time}\", fontsize=100];".format(
        date=str(datetime.date.today()),
        time=str(datetime.datetime.now().time()))
node_style = "node[fontsize=10, fontcolor=black, fontname=Arial, shape=box];"
size = ""
style = graph_style + node_style + size
# "//ratio=\"1:1\";\n"
#      "//ratio=\"fill\";\n"
#      "//size=\"11.692,8.267\"; \n"
#      "//size=\"16.53,11.69\"; //a3\n"
#      "//size=\"33.06,11.69\"\n"
#      "\n".format(date=str(datetime.date.today()),
#                       time=str(datetime.datetime.now().time()))

dg.start_digraph(style)

for dot_connection in filtered_connections:
    dg.add_connection(dot_connection[0], dot_connection[1])

dg.end_digraph()

dg.write_to_file("dotfile.dot")






# print("dot connections: {}".format(len(dot_connections)))
# print("My dots: {}".format(len(my_dots)))
# print("My dot connections: {}".format(len(my_dot_connections)))