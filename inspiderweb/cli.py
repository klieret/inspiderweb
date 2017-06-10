import argparse
from argparse import RawDescriptionHelpFormatter
from .log import logger
from typing import Iterable
import sys

description = r"""
    INSPIDERWEB
 `.,-'\_____/`-.,'     Tool to analyze networks papers referencing and citing each
  /`..'\ _ /`.,'\      other. It acts as a web-crawler, extracting information from
 /  /`.,' `.,'\  \     inspirehep, then uses the dot languageto describe the
/__/__/     \__\__\__  network. The result can then be plotted by the graphviz
\  \  \     /  /  /    Package and similar programs.
 \  \,'`._,'`./  /     More info on the github page
  \,'`./___\,'`./      https://github.com/klieret/inspiderweb
 ,'`-./_____\,-'`.
     /       \
"""


# Use the RawTextHelpFormatter in order to allow linebreaks in the description
cli_parser = argparse.ArgumentParser(description=description,
                                     prog="python3 inspiderweb.py",
                                     formatter_class=RawDescriptionHelpFormatter,
                                     add_help=False)

setup_options = cli_parser.add_argument_group('Setup/Configure Options',
                                          'Supply in/output paths. Note that '
                                          'in most cases, seeds are only '
                                          'added to the database if we '
                                          'perform some action.')
action_options = cli_parser.add_argument_group('Action Options',
                                           'What do you want to do?')
misc_options = cli_parser.add_argument_group('Additional Options',
                                         'Further Configuration...')

setup_options.add_argument("-d", "--database", required=True,
                           help="Pickle database (db) file. Multiple db files "
                                "are supported. In this case the first one "
                                "will be used to save the resulting merged db",
                           type=str, nargs="+")
setup_options.add_argument("-o", "--output", required=False,
                           help="Output dot file.",
                           type=str)
setup_options.add_argument("-r", "--recidpaths", required=False,
                           help="Path of a file or a directory. Multiple paths"
                                "are supported. If the path "
                                "points to a file, each line of the file is "
                                "interpreted as a recid. The collected recids"
                                "are then used as seeds. If the"
                                "path points to a directory, we recursively"
                                "go into it (excluding hidden files) and "
                                "extract recids from every file.",
                           type=str, nargs="+", default=[])
setup_options.add_argument("-q", "--queries", required=False,
                           help="Take the results of inspirehep search query "
                                "(search string you would enter in the "
                                "inspirehep online search "
                                "form) as seeds. Multiple search strings "
                                "supported.",
                           type=str, nargs="+", default=[])
setup_options.add_argument("-b", "--bibkeypaths", required=False,
                           help="Path of a file or a directory. Multiple paths"
                                " are supported. If the path "
                                "points to a file, the file is searched for "
                                "bibkeys, which are then used as seeds. If the"
                                "path points to a directory, we recursively"
                                "go into it (excluding hidden files) and "
                                "search every file for bibkeys.",
                           type=str, nargs="+", default=[])
setup_options.add_argument("-u", "--urlpaths", required=False,
                           help="Path of a file or a directory. If the path "
                                "points to a file, the file is searched for "
                                "inspirehep urls, from which the recids are "
                                "extracted and used as seeds. If the"
                                "path points to a directory, we recursively"
                                "go into it (excluding hidden files) and "
                                "search every file for bibkeys.",
                           type=str, nargs="+", default=[])

# fixme: make that accept arguments on what to plot; combine that with what to download
# todo: make request automatically download stuff it isn't there?
# mayybe it's best to always use db.get_citations and db.get_... instead of
# gettingn the record and using its internal variables...
# a combination of the following:
# -seeds
# -seeds.refs
# -seeds.cites
# -seeds.refs.refs
# -seeds.cites.cites
# similar with all....
# as for implementation: method takes

plot_help = "Generate dot output (i.e. plot). If you do not specify an " \
            "option, only connections between seeds are plotted (this is the" \
            "same as specifying 'seeds>seeds' or 's>s'. If you want to " \
            "customize this, you can supply several rules of the following " \
            "form: 'source selection'>'target selection'. The selections" \
            "for source targets are of the form {seeds,all}[.{refs, cites," \
            "refscites}]. Where e.g. seeds.refscites means that all records" \
            "being cited by a seed or citing a seed are valid starting points"\
            "of an arrow. Short options: s (seeds), a (all), r (refs), c " \
            "(cites). For 'refscites', the following alias exist: " \
            "'citesrefs', 'cr', 'rc'. "

action_options.add_argument("-p", "--plot", required=False,
                            help=plot_help,
                            type=str,
                            const="seeds>seeds",
                            nargs="?")

update_help = "Download information. Multiple arguments are supported. " \
              "Each argument must look like this: Starts with 'seeds' or " \
              "'all' (depending on whether every db entry or just the seeds" \
              " will be taken as starting point). Just 'seeds' (short 's') "\
              "or 'all' (short 'a') will" \
              " only download the bibliographic information for every item. " \
              "Furthermore, there are the following options: " \
              "(1) 'refs' (short 'r'): References of each recid " \
              "(2) 'cites' (short 'c'): Citations of each recid " \
              "(3) 'refscites' or 'citesrefs' (short 'rc' or 'cr'): both. " \
              "These options can be chained, e.g. seeds.refs.cites means " \
              "1. For each seed recid, get all reference "\
              "2. For all of the above, get all citations. " \
              "Similarly one could have written 's.r.c'. "

action_options.add_argument("-g", "--get", required=False,
                            help=update_help,
                            type=str, default="", nargs="+")

misc_options.add_argument("-h", "--help",
                          help="Print this help message.", action="help")
misc_options.add_argument("--rank", required=False,
                           help="Rank by [year]", default="",
                          type=str,
                          choices=["year"])
misc_options.add_argument("-c", "--config", required=False, type=str,
                          help="Add config file to specify more "
                               "settings such as the style of the nodes."
                               "Default value is 'config/default.py'. ",
                          default="config/default.ini")
# fixme: reimplement
misc_options.add_argument("--maxseeds", required=False, type=int,
                          help="Maximum number of seeds (for testing "
                               "purposes).",
                          default=0)
misc_options.add_argument("--forceupdate", action="store_true",
                          help="For all information that we get from the "
                               "database: Force redownload")
misc_options.add_argument("-v" "--verbosity", required=False, type=str,
                          help="Verbosity",
                          choices=["debug", "info", "warning", "error",
                                   "critical"],
                          default="debug", dest="verbosity")


def should_plot_node(recid: str, rule: str, seeds: Iterable[str], db) -> bool:
    """ Based on the rule $rule and the seeds $seeds that were given as
    parameters, return True if the recid $recid is of interest for us.
    E.g. if the rule is "all.refs", return true if the recid is referenced
    by any paper in the database. See the documentation of the command
    line arguments for more on this syntax. """
    steps = rule.split('.')
    if len(steps) == 1:
        if steps[0] in ["all", "a"]:
            if recid not in db._records:
                return False
        elif steps[0] in ["seeds", "s"]:
            if recid not in seeds:
                return False
        else:
            logger.error("Wrong keywords in  }".format(steps[0]))
    elif len(steps) == 2:
        if steps[0] in ["all", "a"]:
            # if we use "all", we do not need the seeds anyway
            seeds = db._records
        elif steps[0] in ["seeds", "s"]:
            pass
        else:
            logger.error("Wrong keywords in {}".format(steps[0]))
            sys.exit(54)

        if steps[1] in ["refs", "r"]:
            is_ref = False
            for recid in seeds:
                if recid in db.get_record(recid).references:
                    is_ref = True
                    break
            if not is_ref:
                return False
        if steps[1] in ["cites", "c"]:
            is_cite = False
            for recid in seeds:
                if recid in db.get_record(recid).citations:
                    is_cite = True
                    break
            if not is_cite:
                return False
        if steps[1] in ["refscites", "citesrefs", "cr", "rc"]:
            is_rc = False
            for recid in seeds:
                if recid in db.get_record(recid).citations:
                    is_rc = True
                    break
            if not is_rc:
                return False
    else:
        logger.error("Wrong syntax: {}. Must contain at most one '.'. "
                     "".format(rule))
        sys.exit(60)

    return True


def should_plot_connection(source_recid: str, target_recid: str,
                           rules: Iterable[str],
                           seeds: Iterable[str], db) -> bool:
    """ Based on the rules $rules and the seeds $seeds that were given as
    parameters, return True if the connection $source_recid >  $target_recid
    should be plotted.
    E.g. for the rules ["seeds.refs > seeds", "seeds>all"], return True for all
    connections of references of seeds to the seeds and any connection of the
    seeds to anything.
    See the command line arguments for more information. """
    for rule in rules:
        try:
            source_rule, target_rule = rule.split('>')
        except ValueError:
            logger.error("Wrong syntax: {}. Ther should be exactly one "
                         "'>' in this stringl".format(rule))
            sys.exit(58)
        if db.should_plot_node(source_recid, source_rule, seeds) and \
                db.should_plot_node(target_recid, target_rule, seeds):
            return True
    return False


def get_plot_connections(rules: Iterable[str], seeds: Iterable[str],
                         db) -> set:
    """ Returns list of connections that the user wants to have plotted
    (based on the rules in $rules) as a set of two-tuples of the connected
    recids.
    
    Args:
        rules: Iterable of rules (strings, following the guidlines in the 
               command line help)
        seeds: Iterable of recids
        db: Database
    Returns: set of two-tuples (from_recid, to_recid) for all connections
             that we are interested in.
    """
    logger.debug("Getting plot connections for "
                 "rules {}".format(', '.join(rules)))
    connections = set()
    for recid, record in db._records.items():
        for reference_recid in record.references:
            if not should_plot_connection(recid, reference_recid, rules,
                                          seeds, db):
                continue
            connections.add((record.recid, reference_recid))
        for citation_recid in record.citations:
            if not should_plot_connection(citation_recid, recid, rules,
                                          seeds, db):
                continue
            connections.add((citation_recid, record.recid))
    return connections
