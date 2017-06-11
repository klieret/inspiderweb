import os.path
from .log import logger
import sys
import re
from typing import List

""" Part of inspiderweb: Tool to analyze paper reference networks.
Inspiderweb currently hosted at: https://github.com/klieret/inspiderweb

Collection of methods to supply the initial seeds. For most methods that
take input files, we define one method
    get_recids_from_[....]_file(path, db),
which may or may not require the db argument,
then define
    get_recids_from_[....]_paths(paths, db)
which may or may not require the db argument, and loops over a list of files
or directories.
The fact that all of the functions can take the db argument (even if they
don't need it) is to make wrapping via
    get_recids_from_paths
easier.
"""


def get_recids_from_paths(paths: List[str], extractor, db=None) -> set():
    """ Iterate over $paths. If $path points to a file, apply
    $function($path, db=$db) and add the returned values to a set.
    If $path points to a directory, walk through
    that whole directory and apply $function to every file, just as above.

    Args:
        paths (list(str)): List of paths of directories or files.
        extractor: Function that should be applied to every file.
        db: Database instance (depending on the function, this can be left
            empty
    Returns:
        The merged return values of all calls of $function.
    """
    new_recids = set()
    for path in paths:
        if not os.path.exists(path):
            logger.critical("Input file {} doesn't exist. Abort.".format(path))
            sys.exit(50)
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                # fixme: skip hidden files
                for file in files:
                    these_new_recids = \
                        extractor(os.path.join(root, file), db=db)
                    if these_new_recids:
                        logger.info("Got {} seeds from bibkeys from file "
                                    "{}.".format(len(these_new_recids),
                                                 os.path.join(root, file)))
                    new_recids.update(these_new_recids)

        if os.path.isfile(path):
            these_new_recids = extractor(path, db=db)
            new_recids.update(these_new_recids)
            logger.info("Got {} seeds from bibkeys from file {}.".format(
                len(these_new_recids), path))
    return new_recids


# noinspection PyUnusedLocal
def get_recids_from_recid_file(path: str, db=None) -> set():
    """ Get recids from a file that only contains recids.
    Args:
        path: Path to a recid file
        db: Can be left empty.
    Returns:
        Set of recids.
    """
    new_recids = set()
    with open(path, "r") as seedfile_stream:
        for line in seedfile_stream:
            line = line.replace('\n', "").strip()
            if not line:
                continue
            new_recids.add(line)
    return new_recids


# noinspection PyUnusedLocal
def get_recids_from_recid_paths(paths: List[str], db=None) -> set():
    """ Get recids from a list of paths.
    If a $path points to a file, we get interpret every line as a recid
    and add all of them to a set.
    If $path points to a directory, walk through
    that whole directory and apply do the same for every file in there.
    Args:
        paths (list(path)): Paths to files or directories.
        db: Can be left empty.
    Returns:
        set of recids.
    """
    return get_recids_from_paths(paths, get_recids_from_recid_file)


def get_recids_from_bibkey_file(path: str, db) -> set():
    """ Get recids from a file that contains (among others, bibkeys(.
    Args:
        path: Path to a file
        db: Database. Must be supplied!
    Returns:
        Set of recids.
    """
    bibkey_regex = re.compile(r"[a-zA-Z]{1,20}:[0-9]{4}[a-z]{0,10}")
    with open(path, "r") as bibfile:
        bibkeys = set()
        for bibline in bibfile:
            bibkeys.update(bibkey_regex.findall(bibline))
    bibkey_recids = db.get_recids_from_bibkeys(bibkeys).keys()
    return bibkey_recids


def get_recids_from_bibkey_paths(paths: List[str], db) -> set():
    """ Get recids from a list of paths.
    If a $path points to a file, we search it for bibkeys, query inspirehep
    for the bibkey, and -- if there is a direct match -- add this to a
    set of return recids.
    If $path points to a directory, walk through
    that whole directory and apply do the same for every file in there.
    Args:
        paths (list(path)): Paths to files or directories.
        db: Database. Must be supplied!
    Returns:
        set of recids.
    """
    return get_recids_from_paths(paths, get_recids_from_bibkey_file, db=db)


# noinspection PyUnusedLocal
def get_recids_from_url_file(path: str, db=None) -> set():
    """ Get recids from a file that contains (among others) inspirehep urls,
    such as "http://inspirehep.net/record/566620/references" or similar.
    From this, extract the record ids and return them as a set.
    Args:
        path: Path to a file
        db: Can be left empty.
    Returns:
        Set of recids.
    """
    url_regex = re.compile("inspirehep.net/record/([0-9]+)")
    new_recids = set()
    with open(path, "r") as stream:
        for line in stream:
            new_recids.update(url_regex.findall(line))
    return new_recids


# noinspection PyUnusedLocal
def get_recids_from_url_paths(paths: List[str], db=None) -> set():
    """ Get recids from a list of paths.
    If a $path points to a file, we search it for inspirehep urls which are
    then added to the return set.
    If $path points to a directory, walk through
    that whole directory and apply do the same for every file in there.
    Args:
        paths (list(path)): Paths to files or directories.
        db: Can be left empty.
    Returns:
        set of recids.
    """
    return get_recids_from_paths(paths, get_recids_from_url_file)


def get_recid_from_queries(queries: List[str], db) -> set():
    """ Get recids from a list of inspirehep query strings, such as
        "recid:123": Get the record with recid 123
        "a feynman and year < 1990": Get all papers from author 'feynman" that
                                     were published prior to 1990.
    returns those recids as a set.
    Args:
        queries (list(str)): List of search strings
        db: Database.
    Returns:
        set of recids.
    """
    new_recids = set()
    for query in queries:
        these_new_recids = db.get_recids_from_query(query)
        logger.info("Got {} seeds from search query {}.".format(
            len(these_new_recids), query))
        new_recids.update(these_new_recids)

    return new_recids
