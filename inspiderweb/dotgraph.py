import re
import collections
from .log import logger
import sys

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
    def __init__(self, db, config):
        self.db = db
        self.config = config
        self._dot_str = ""
        self._all_node_ids = set([])
        self._node_styles = {}
        self._clusters = {}  # clusterlabel: (set of recids, style)
        self._connections = set([])

    def add_node(self, recid, style=""):
        self._node_styles[recid] = style

    def add_connection(self, from_recid: str, to_recid: str) -> None:
        """ Adds connection between two nodes.

        Args:
            from_recid: recid of the record that is referencing
            to_recid: recid of the record that is being referenced
        """
        self._connections.add((from_recid, to_recid))
        # print("here")

    def add_connections(self, connections: set):
        """ Adds connection between a collection of nodes.

        Args:
            connections: set of two-tuples of recids
        """
        for (from_recid, to_recid) in connections:
            self.add_connection(from_recid, to_recid)
        # print(self._connections)

    def add_cluster(self, recids: set, cluster_id: str, style: str):
        """ Add a cluster.

        Args:
            recids: Set (!) of recids for each member of the cluster
            cluster_id: Id for cluster. Must be unique, otherwise arbitrary.
            style: String to style the cluster
        """
        self._clusters[cluster_id] = (recids, style)

    def add_cluster_node(self, cluster_id: str, recid: str):
        self._clusters[cluster_id][0].add(recid)

    def return_dot_str(self) -> str:
        """ Return the string of dot language that describes the graph. """
        return self._dot_str

    def _draw_start(self) -> None:
        """ Begin graph in dot string. """
        self._dot_str = ""
        self._dot_str += "digraph g {\n"
        self._dot_str += self.config["graph_style"] + "\n"

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

            # todo: fix indentation of stuff from config file
            self._dot_str += "{"
            self._dot_str += self.config["year_node_style"]  + "\n"
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
                self._dot_str += self.config["cluster_style"]
                self._dot_str += 'label="{}";\n'.format(cluster)
                for recid in cluster[0]:
                    self._dot_str += '\t\t"{};\n'.format(recid)
                self._dot_str += "\t}\n"

    def _draw_nodes(self) -> None:
        """ Draw nodes/style nodes (assign label etc.) """

        for node_id in self._all_node_ids:
            if node_id not in self._node_styles or not \
                    self._node_styles[node_id]:
                self._node_styles[node_id] = 'label="{}" URL="{}"'.format(
                    self.db.get_record(node_id).label,
                    self.db.get_record(node_id).inspire_url)

        for recid, style in self._node_styles.items():
            self._dot_str += '\t"{}" [{}];\n'.format(recid, style)

    def _draw_connections(self) -> None:
        """ Add the connections to the dot strings.
        """
        for connection in self._connections:
            # logger.debug("Adding connection")
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
