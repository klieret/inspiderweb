import re
import collections
from .log import logger

class DotGraph(object):
    def __init__(self, db):
        self.db = db
        self._dot_str = ""
        self._all_node_ids = set([])
        self._node_styles = {}
        self._connections = set([])
        self._style = ""

    # def _add_cluster(self, records, style=""):
    #     # for cluster, items in clusters.items():
    #     self._dot_str += '\tsubgraph "cluster_{}" {{\n'.format(cluster)
    #     self._dot_str += ("\tfontname=Courier;\n"
    #                      "\tfontcolor=red;\n"
    #                      "\tpenwidth=3;\n"
    #                      "\tfontsize=50;\n"
    #                      "\tcolor=\"red\";\n"
    #                      "\tstyle=\"filled\";\n"
    #                      "\tfillcolor=\"gray97\";\n")
    #     self._dot_str += '\tlabel="{}";\n'.format(cluster)
    #     for record in records:
    #         self._dot_str += '\t\t"{}" [label="{}"];\n'.format(
    #             record.id, record.label)
    #     self._dot_str += "\t}\n"

    def add_node(self, mid, style=""):
        self._node_styles[mid] = style

    def add_connection(self, from_id, to_id):
        self._connections.add((from_id, to_id))

    def return_dot_str(self):
        return self._dot_str

    def generate_dot_str(self, rank=""):
        self._dot_str = ""
        self._dot_str += "digraph g {\n"
        indented = ";\n".join(['\t' + line for line in self._style.split(';')
                               if line])
        self._dot_str += indented


        for connection in self._connections:
            self._all_node_ids.add(connection[0])
            self._all_node_ids.add(connection[1])

        if rank == "":
            pass
        elif rank == "year":
            year_regex = re.compile(r".*:([0-9]{4}).*")
            node_ids_by_year = collections.defaultdict(set)
            for node_id in self._all_node_ids:
                bibkey = self.db.get_record(node_id).bibkey
                try:
                    year = year_regex.match(bibkey).group(1)
                except:
                    continue
                node_ids_by_year[year].add(node_id)

            # fixme: style shouldn't be defined here
            self._dot_str += "\t{\n\t\tnode [shape=circle, fontsize=20, style=filled, color=yellow];\n"
            self._dot_str += "\t\t" + "->".join(list(sorted(node_ids_by_year.keys(), reverse=True))) + ";\n"
            self._dot_str += "\t}\n"

            for year, node_ids in node_ids_by_year.items():
                self._dot_str += "\t{{rank=same; {}; {} }}\n".format(year, "; ".join(node_ids))

        else:
            logger.warning("Unknown rank option {}".format(rank))

        for node_id in self._all_node_ids:
            if node_id not in self._node_styles or not self._node_styles[node_id]:
                self._node_styles[node_id] = 'label="{}" URL="{}"'.format(
                    self.db.get_record(node_id).label,
                    self.db.get_record(node_id).inspire_url)

        for mid, style in self._node_styles.items():
            self._dot_str += '\t"{}" [{}];\n'.format(mid, style)


        for connection in self._connections:
            self._dot_str += '\t"{}" -> "{}"; \n'.format(connection[0],
                                                         connection[1])

        self._dot_str += "}"
        return self._dot_str

    def write_to_file(self, filename):
        with open(filename, "w") as dotfile:
            dotfile.write(self._dot_str)