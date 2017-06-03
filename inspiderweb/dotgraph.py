import logging

logger = logging.getLogger("inspirespider")

class DotGraph(object):
    def __init__(self, db):
        self.db = db
        self._dot_str = ""
        self.node_styles = {}
        self.connections = set([])
        self.style = ""

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
        self.node_styles[mid] = style

    def add_connection(self, from_id, to_id):
        self.connections.add((from_id, to_id))

    def return_dot_str(self):
        return self._dot_str

    def generate_dot_str(self):
        self._dot_str = ""
        self._dot_str += "digraph g {\n"
        indented = ";\n".join(['\t' + line for line in self.style.split(';')
                               if line])
        self._dot_str += indented

        for connection in self.connections:
            from_id = connection[0]
            to_id = connection[1]
            if not from_id in self.node_styles or not self.node_styles[from_id]:
                self.node_styles[from_id] = 'label="{}"'.format(
                    self.db.get_record(from_id).label)
            if not to_id in self.node_styles or not self.node_styles[to_id]:
                self.node_styles[from_id] = 'label="{}"'.format(
                    self.db.get_record(to_id).label)

        for mid, style in self.node_styles.items():
            self._dot_str += '\t"{}" [{}];\n'.format(mid, style)

        for connection in self.connections:
            self._dot_str += '\t"{}" -> "{}"; \n'.format(connection[0],
                                                         connection[1])

        self._dot_str += "}"
        return self._dot_str

    def write_to_file(self, filename):
        with open(filename, "w") as dotfile:
            dotfile.write(self._dot_str)