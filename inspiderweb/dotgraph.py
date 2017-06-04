import re
import collections
from .log import logger

""" Part of inspiderweb: Tool to analyze paper reference networks.
Inspiderweb currently hosted at: https://github.com/klieret/inspiderweb

This file defines the DotGraph class which is used to generate the string
in dot language that describes the graph which is formed by the papers/records
referencing each other.
"""


class DotGraph(object):
    """ Objects of DotGraph class is used to generate the string
    in dot language that describes the graph which is formed by the
    papers/records referencing each other.
    """
    def __init__(self, db):
        self.db = db
        self._dot_str = ""
        self._all_node_ids = set([])
        self._node_styles = {}
        self._clusters = {}  # clusterlabel: (set of mids, style)
        self._connections = set([])
        self._style = ""

    def add_node(self, mid, style=""):
        self._node_styles[mid] = style

    def add_connection(self, from_mid: str, to_mid: str) -> None:
        """ Adds connection between two nodes.

        Args:
            from_mid: mid of the record that is referencing
            to_mid: mid of the record that is being referenced
        """
        self._connections.add((from_mid, to_mid))

    def add_cluster(self, mids: set, cluster_id: str, style: str):
        """ Add a cluster.

        Args:
            mids: Set (!) of mids for each member of the cluster
            cluster_id: Id for cluster. Must be unique, otherwise arbitrary.
            style: String to style the cluster
        """
        self._clusters[cluster_id] = (mids, style)

    def add_cluster_node(self, cluster_id: str, mid: str):
        self._clusters[cluster_id][0].add(mid)

    def return_dot_str(self) -> str:
        """ Return the string of dot language that describes the graph. """
        return self._dot_str

    def _draw_start(self) -> None:
        """ Begin graph in dot string. """
        self._dot_str = ""
        self._dot_str += "digraph g {\n"
        indented = ";\n".join(['\t' + line for line in self._style.split(';')
                               if line])
        self._dot_str += indented

    def _draw_ranks(self, rank: str) -> None:
        """ If nodes are added to a `rank=same` part, they will all appear
        on the same vertical coordinate.

        Args:
            rank: Currently only supported option: year. Sorts by years.

        Returns: None
        """
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
            self._dot_str += "\t{\n\t\tnode [shape=circle, fontsize=20, " \
                             "style=filled, color=yellow];\n"
            self._dot_str += "\t\t" + "->".join(
                list(sorted(node_ids_by_year.keys(), reverse=True))) + ";\n"
            self._dot_str += "\t}\n"

            for year, node_ids in node_ids_by_year.items():
                self._dot_str += "\t{{rank=same; {}; {} }}\n".format(
                    year, "; ".join(node_ids))

        else:
            logger.warning("Unknown rank option {}".format(rank))

    def _draw_clusters(self) -> None:
        """ Cluster several entries.
        """

        for cluster_id, cluster in self._clusters.items():
                # for cluster, items in clusters.items():
                self._dot_str += '\t\tsubgraph "cluster_{}" {{\n'.format(
                    cluster_id)
                self._dot_str += ";\n".join(cluster[1].split(';'))
                # self._dot_str += ("\tfontname=Courier;\n"
                #                  "\tfontcolor=red;\n"
                #                  "\tpenwidth=3;\n"
                #                  "\tfontsize=50;\n"
                #                  "\tcolor=\"red\";\n"
                #                  "\tstyle=\"filled\";\n"
                #                  "\tfillcolor=\"gray97\";\n")
                # self._dot_str += '\tlabel="{}";\n'.format(cluster)
                for mid in cluster[0]:
                    self._dot_str += '\t\t"{};\n'.format(mid)
                self._dot_str += "\t}\n"

    def _draw_nodes(self) -> None:
        """ Draw nodes/style nodes (assign label etc.)
        """

        for node_id in self._all_node_ids:
            if node_id not in self._node_styles or not \
                    self._node_styles[node_id]:
                self._node_styles[node_id] = 'label="{}" URL="{}"'.format(
                    self.db.get_record(node_id).label,
                    self.db.get_record(node_id).inspire_url)

        for mid, style in self._node_styles.items():
            self._dot_str += '\t"{}" [{}];\n'.format(mid, style)

    def _draw_connections(self) -> None:
        """ Add the connections to the dot strings.
        """
        for connection in self._connections:
            self._dot_str += '\t"{}" -> "{}"; \n'.format(connection[0],
                                                         connection[1])

    def _draw_end(self) -> None:
        """ End the digraph. """

        self._dot_str += "}"

    def generate_dot_str(self, rank=""):
        """ Generate the string of
        dot language describing the graph.

        Args:
            rank: Currently only support "year".
        """

        for connection in self._connections:
            self._all_node_ids.add(connection[0])
            self._all_node_ids.add(connection[1])

        self._draw_start()
        self._draw_ranks(rank)
        self._draw_clusters()
        self._draw_nodes()
        self._draw_connections()
        self._draw_end()

        return self._dot_str

    def write_to_file(self, path: str):
        """ Prints dot string to file.
        """
        with open(path, "w") as dotfile:
            dotfile.write(self._dot_str)
