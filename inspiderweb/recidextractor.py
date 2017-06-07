import os.path
from .log import logger
import sys
import re


def get_recids_from_paths(paths, function, db=None):
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
                        function(os.path.join(root, file), db=db)
                    if these_new_recids:
                        logger.info("Got {} seeds from bibkeys "
                                    "from file {}.".format(
                            len(these_new_recids), os.path.join(root, file)))
                    new_recids.update(these_new_recids)

        if os.path.isfile(path):
            these_new_recids = function(path, db=db)
            new_recids.update(these_new_recids)
            logger.info("Got {} seeds from bibkeys from file {}.".format(
                len(these_new_recids), path))
    return new_recids


def get_recids_from_recid_file(path, db=None):
    new_recids = set()
    with open(path, "r") as seedfile_stream:
        for line in seedfile_stream:
            line = line.replace('\n', "").strip()
            if not line:
                continue
            new_recids.add(line)
    return new_recids


def get_recids_from_recid_paths(paths, db=None):
    return get_recids_from_paths(paths, get_recids_from_recid_file)


def get_recids_from_bibkey_file(path, db):
    bibkey_regex = re.compile(r"[a-zA-Z]{1,20}:[0-9]{4}[a-z]{0,10}")
    with open(path, "r") as bibfile:
        bibkeys = set()
        for bibline in bibfile:
            bibkeys.update(bibkey_regex.findall(bibline))
    bibkey_recids = db.get_recids_from_bibkeys(bibkeys).keys()
    return bibkey_recids


def get_recids_from_bibkey_paths(paths, db):
    return get_recids_from_paths(paths, get_recids_from_bibkey_file, db=db)



