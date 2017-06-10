import argparse
from argparse import RawDescriptionHelpFormatter

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
parser = argparse.ArgumentParser(description=description,
                                 prog="python3 inspiderweb.py",
                                 formatter_class=RawDescriptionHelpFormatter,
                                 add_help=False)

setup_options = parser.add_argument_group('Setup/Configure Options',
                                          'Supply in/output paths. Note that '
                                          'in most cases, seeds are only '
                                          'added to the database if we '
                                          'perform some action.')
action_options = parser.add_argument_group('Action Options',
                                           'What do you want to do?')
misc_options = parser.add_argument_group('Additional Options',
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
                            default="seeds>seeds",
                            nargs="*")

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
                          default="config/default.py")
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

args = parser.parse_args()