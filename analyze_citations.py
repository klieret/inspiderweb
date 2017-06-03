#!/usr/bin/env python3

import os
import re
import collections
import sys
import datetime
import logging
import pickle
import urllib.request
import csv

logger = logging.getLogger("inspirespider")
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
fm = logging.Formatter("%(levelname)s: %(message)s")
sh.setFormatter(fm)
logger.addHandler(sh)
logger.addHandler(sh)


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

class Database(object):
    def __init__(self, backup_path):
        self._records = {}
        self.backup_path = backup_path

    def load(self, path=""):
        if not path:
            path = self.backup_path
        if not os.path.exists(path):
            logger.warning("Could not load db from file.")
            return False
        self._records = pickle.load(open(path, "rb"))
        logger.debug("Successfully loaded db from {}".format(path))
        return True

    def save(self, path=""):
        if not path:
            path = self.backup_path
        pickle.dump(self._records, open(path, "wb"))
        logger.debug("Successfully saved db to {}".format(path))


    def get_record(self, mid):
        if mid in self._records:
            return self._records[mid]
        else:
            return Record(mid)

    def update_record(self, mid, record):
        self._records[mid] = record


class Record(object):
    def __init__(self, mid, label=None):
        self.inspire_url = "http://inspirehep.net/record/{}".format(mid)
        self.label = label
        self.bibkey = ""
        self.mid = mid
        # if label:
        #     self.label = label
        # else:
        #     self.label = self.inspire_url.split('/')[-1]
        self.references = []
        self.citations = []

    def get_info(self, force=False):
        if self.bibkey and not force:
            logger.debug("Skipping downloading of info.")
            return False
        bibkey_regex = re.compile(r"@\w*\{([^,]*),")
        logger.debug("Downloading bibfile of {}".format(self.mid))
        bib_entry = urllib.request.urlopen(
            self.inspire_url + "/export/hx").read().decode("utf-8")
        bibkey = bibkey_regex.search(bib_entry).group(1)
        logger.debug("Bibkey of {} is {}".format(self.mid, bibkey))
        self.bibkey = bibkey
        return True

    def get_citations(self, force=False):
        if self.citations and not force:
            logger.debug("Skipping downloading of citations.")
            return False
        record_regex = re.compile("/record/([0-9]*)")
        logger.debug("Downloading citations of {}".format(self.mid))
        citations_html = urllib.request.urlopen(
            self.inspire_url + "/citations").read().decode("utf-8")
        records = record_regex.findall(citations_html)
        records = [record for record in records if not record == self.mid]
        logger.debug("{} is cited by {} records".format(self.mid, len(records)))
        self.citations = records
        return True

    def get_references(self, force=False):
        if self.references and not force:
            logger.debug("Skipping downloading of references.")
            return False
        record_regex = re.compile("/record/([0-9]*)")
        logger.debug("Downloading references of {}".format(self.mid))
        reference_html = urllib.request.urlopen(
            self.inspire_url + "/references").read().decode("utf-8")
        records = record_regex.findall(reference_html)
        records = [record for record in records if not record == self.mid]
        logger.debug("{} is citing {} records".format(self.mid, len(records)))
        self.references = records
        return True

    def __str__(self):
        return "R({})".format(self.mid)

    def __repr__(self):
        return self.__str__()

# http://i.imgur.com/gOPS2.png

# def extract_records(string):
#     # goes fro string, looking for every record url
#     _records = record_regex.findall(string)
#     return _records

db = Database("pickle.pickle")

db.load()

with open("inspirehep_links.txt", "r") as inspire_links:
    csv = csv.reader(inspire_links, delimiter=";")
    for row in csv:
        if not row:
            continue
        if row[0].startswith("#"):
            continue
        if not len(row) == 2:
            continue
        label = row[0].strip()
        if not label:
            continue
        try:
            mid = re.search("[0-9]+", row[1].strip()).group(0)
        except AttributeError:
            continue
        r = db.get_record(mid)
        r.label = label
        db.update_record(mid, r)


db.save()

print(db._records)

sys.exit(1)

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

db.save()

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