#!/usr/bin/env python3

import os
import re
import collections


material_folder = "/home/kilian/Documents/db_master/material/material/"
citation_folder = "/home/kilian/Dropbox/db_master/material/marc/"

clusters = collections.defaultdict(set)

for root, dirs, files in os.walk(material_folder):
    for file in files:
        if os.path.splitext(file)[1] in [".pdf", ".ps", ".djvu"]:
            mid = os.path.basename(file)[0:4]
            clustername = "ROOT"
            if os.path.basename(root):
                clustername = os.path.basename(root)
            clusters[clustername].add(mid)

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
    my_dots.add(dot_connection[0])

my_dot_connections = []
for dot_connection in dot_connections:
    if dot_connection[1] in my_dots:
        my_dot_connections.append(dot_connection)

# dot_txt = """digraph g {
#  ratio="fill";
#  size="8.3,11.7!";
#  margin=0;\n"""
dot_txt = ""

dot_txt += """digraph g {\n"""

for dot_connection in my_dot_connections:
    dot_txt += '\t"{}" -> "{}"; \n'.format(hep_to_mref[dot_connection[0]],
                                       hep_to_mref[dot_connection[1]])

for cluster, items in clusters.items():
    dot_txt += '\tsubgraph "cluster_{}" {{\n'.format(cluster)
    dot_txt += '\tlabel="{}";\n'.format(cluster)
    for item in items:
        dot_txt += '\t\t"{}";\n'.format(item)
    dot_txt += "\t}\n"


dot_txt += "}"



with open("dotfile.dot", "w") as dotfile:
    dotfile.write(dot_txt)

print("dot connections: {}".format(len(dot_connections)))
print("My dots: {}".format(len(my_dots)))
print("My dot connections: {}".format(len(my_dot_connections)))