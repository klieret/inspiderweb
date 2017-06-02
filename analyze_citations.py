#!/usr/bin/env python3

import os
import re
import collections
import sys
import datetime
from field_from_mid import init_mid_to_bib_paths, extract_field

mid_to_bib_paths = init_mid_to_bib_paths()

material_folder = "/home/kilian/Documents/db_master/material/material/"
citation_folder = "/home/kilian/Dropbox/db_master/material/marc/"

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
        # if label:
        #     self.label = label
        # else:
        #     self.label = self.inspire_url.split('/')[-1]


def parse_records(string):
    # goes fro string, looking for every record url
    pass

def get_cited_by(record):
    pass

def get_references(record):
    pass

record_regex = re.compile("/record/([0-9]*)")

dot_connections = []
hep_to_mref = {}
for filename in os.listdir(citation_folder):
    with open(os.path.join(citation_folder, filename), "r") as citefile:
        this_record = None
        for line in citefile:
            if not line:
                continue
            if record_regex.search(line):
                record = record_regex.search(line).group(1)
                if not this_record:
                    this_record = record
                    mid = os.path.splitext(os.path.basename(filename))[0]
                    hep_to_mref[this_record] = mid
                if not this_record == record:
                    dot_connections.append((this_record, record))

my_dots = set()
for dot_connection in dot_connections:
    my_dots.add(hep_to_mref[dot_connection[0]])

my_dot_connections = []
for dot_connection in dot_connections:
    if not dot_connection[1] in hep_to_mref:
        continue
    if hep_to_mref[dot_connection[1]] in my_dots:
        my_dot_connections.append((hep_to_mref[dot_connection[0]],
                                   hep_to_mref[dot_connection[1]]))


class DotGraph(object):
    def __init__(self):
        self.dot_str = ""

    def start_digraph(self):
        self.dot_str += \
            ("digraph g {\n"
             "\tgraph [label=\"Network as of {date} {time}\", fontsize=100];\n"
             "\tnode[fontsize=10, fontcolor=black, fontname=Arial, shape=box];\n"
             "//\tratio=\"1:1\";\n"
             "//\tnode[fontsize=50, fontcolor=\"red\", fontname=Courier, shape=box];\n"
             "//\tratio=\"fill\";\n"
             "//\tsize=\"11.692,8.267\"; \n"
             "//\tsize=\"16.53,11.69\"; //a3\n"
             "//\tsize=\"33.06,11.69\"\n"
             "\n").format(date=str(datetime.date.today()),
                          time=str(datetime.datetime.now().time()))

    def end_digraph(self):
        self.dot_str += "}"

    def add_cluster(self):
        raise NotImplemented

    def add_connection(self, start, end):
        self.dot_str += '\t"{}" -> "{}"; \n'.format(dot_connection[0],
                                                    dot_connection[1])

    def return_dot_str(self):
        return self.dot_str

    def write_to_file(self, filename):
        with open(filename, "w") as dotfile:
            dotfile.write(self.dot_str)

dg = DotGraph()

dg.start_digraph()

for dot_connection in my_dot_connections:
    dg.add_connection(dot_connection[0], dot_connection[1])



dg.end_digraph()
dg.write_to_file("dotfile.dot")

# for cluster, items in clusters.items():
#     dot_txt += '\tsubgraph "cluster_{}" {{\n'.format(cluster)
#     dot_txt += """\tfontname=Courier;
#     \tfontcolor=red;
#     \tpenwidth=3;
#     \tfontsize=50;
#     \tcolor="red";
#     \tstyle="filled";
#     \tfillcolor="gray97";
#     """
#     dot_txt += '\tlabel="{}";\n'.format(cluster)
#     #dot_txt += '\tstyle="filled";'
#     for item in items:
#         if item in my_dots or not hide_unrelated:
#             dot_txt += '\t\t"{}" [label="{}"];\n'.format(item, extract_field(mid_to_bib_paths[item], "title"))
#     dot_txt += "\t}\n"
# dot_txt += "}"




# print("dot connections: {}".format(len(dot_connections)))
# print("My dots: {}".format(len(my_dots)))
# print("My dot connections: {}".format(len(my_dot_connections)))