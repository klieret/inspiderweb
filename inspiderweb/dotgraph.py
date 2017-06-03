import logging

logger = logging.getLogger("inspirespider")

class DotGraph(object):
    def __init__(self):
        self._dot_str = ""
        self._records = {}
        self._connections = set([])

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

    def add_connection(self, from_record, to_record):
        self._records[from_record.mid] = from_record
        self._records[to_record.mid] = to_record
        self._connections.add((from_record.mid, to_record.mid))


    def return_dot_str(self):
        return self._dot_str

    def generate_dot_str(self, style=""):
        self._dot_str = ""
        self._dot_str += "digraph g {\n"
        indented = ";\n".join(['\t' + line for line in style.split(';')
                               if line])
        self._dot_str += indented

        for mid, record in self._records.items():
            self._dot_str += '\t "{}" [label="{}"];\n'.format(record.mid,
                                                          record.label)

        for connection in self._connections:
            self._dot_str += '\t"{}" -> "{}"; \n'.format(connection[0],
                                                         connection[1])

        self._dot_str += "}"
        return self._dot_str

    def write_to_file(self, filename):
        with open(filename, "w") as dotfile:
            dotfile.write(self._dot_str)