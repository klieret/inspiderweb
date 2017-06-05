import pickle
from .record import Record
import csv
import os.path
import re
import time
from .log import logger
from typing import List

""" Part of inspiderweb: Tool to analyze paper reference networks.
Inspiderweb currently hosted at: https://github.com/klieret/inspiderweb

This file defines the Database class. The Database mostly is a collection of
Record objects (that hold information of a record/paper from inspirehep) plus
some methods to update/save/cache information.
"""


class Database(object):
    """  The Database mostly is a collection of
    Record objects (that hold information of a record/paper from inspirehep)
    plus some methods to update/save/cache information.
    The records are collected in self._records, a dictionary of the form
    mid: record, where record is a Record object and mid is the inspirehep
    id, i.e. the number 566620 for the record inspirehep.net/record/566620/.
    """
    def __init__(self, backup_path):
        self._records = {}
        self.backup_path = backup_path

    def statistics(self):
        """ Print some statistics about the records in the database. """
        logger.info(" database statistics ".upper().center(50, "*"))
        logger.info("Current number of records: {}".format(len(self._records)))
        logger.info("Current number of records with references: {}".format(
            sum([int(r.references_dl) for mid, r in self._records.items()])))
        logger.info("Current number of records with citations: {}".format(
            sum([int(r.citations_dl) for mid, r in self._records.items()])))
        logger.info("Current number of records with cocitations: {}".format(
            sum([int(r.cocitations_dl) for mid, r in self._records.items()])))
        logger.info("Current number of records with bibkey: {}".format(
            sum([int(bool(r.bibkey)) for mid, r in self._records.items()])
        ))
        logger.info("*"*50)

    def load(self, path="") -> bool:
        """ Load/merge the database from file $path.
        Returns True if this was successfull.
        If the path doesn't exist, only a logging.error message will be
        written. If no path is given self.backup_path will be used.

        Args:
            path: Path of other database.
        """

        if not path:
            path = self.backup_path
        if not os.path.exists(path):
            logger.warning("Could not load db from file.")
            return False
        for mid, their_record in pickle.load(open(path, "rb")).items():
            assert mid == their_record.mid
            my_record = self.get_record(mid)
            my_record.merge(their_record)
            self.update_record(mid, my_record)
        logger.debug("Successfully loaded db from {}".format(path))
        return True

    def save(self, path=""):
        """ Save the database to file.
        If no path is given self.backup_path will be used. """

        if not path:
            path = self.backup_path
        pickle.dump(self._records, open(path, "wb"))
        logger.debug("Successfully saved db to {}".format(path))

    def autocomplete_records(self, updates: List, force=False, save_every=5,
                             mids=None, statistics_every=5) -> bool:
        """ Download information for each record from inspirehep.

        Args:
            updates (list): What information should be downloaded.
                            Options are
                            "bib" (bibtex, in particular the bibkey),
                            "refs" (references of the record),
                            "cites" (citations and cocitations of th erecord)
            force (bool): Force redownload of information
            save_every (int): Save database after this many completed records
            mids (list): Only download information for records with id (mid) in
                         this list.
            statistics_every(int): Print statistics after this many downloaded
                                   items.

        Returns: True if we actually did something.
        """

        for update in updates:
            if not update in ["bib", "refs", "cites"]:
                logger.error("Unrecognize update option {}. "
                             "I will simply ignore this for "
                             "now.".format(update))
                updates.remove(update)

        if not updates:
            return

        if not mids:
            mids = self._records.keys()

        logger.debug("Downloading {} for {} records.".format(
            ', '.join(updates), len(mids)))

        for i, mid in enumerate(mids):
            if i and i % save_every == 0:
                self.save()
            if i and i % statistics_every == 0:
                self.statistics()
                logger.debug("Sleeping a bit longer.")
                time.sleep(15)

            record = self.get_record(mid)

            if "bib" in updates:
                record.get_info(force=force)
            if "refs" in updates:
                record.get_references(force=force)
            if "cites" in updates:
                record.get_citations(force=force)

            self.update_record(mid, record)

        return True

    def get_record(self, mid):
        """ Return record with id $mid from database. Record will be created
        if it was not in the database before.
        """

        if mid in self._records:
            return self._records[mid]
        else:
            return Record(mid)

    def update_record(self, mid, record):
        """ Update record with id $mid with record $record. """
        self._records[mid] = record

    def load_labels_from_file(self,
                              path: str,
                              delimiter_char=";",
                              comment_char="#",
                              label_column=0,
                              id_column=1):
        """ Load labels from csv file.

        Args:
            path: Path to csv file.
            delimiter_char: Delimiter of csv file [;]
            comment_char: Ignore lines starting with this [#]
            label_column: Column with the label [0]
            id_column: Column with the mid [1]
        """
        logger.info("Loading labels from {}".format(path))
        with open(path, "r") as inspire_links:
            csv_file = csv.reader(inspire_links, delimiter=delimiter_char)
            for row in csv_file:
                if not row:
                    continue
                if row[0].startswith(comment_char):
                    continue
                try:
                    label = row[label_column].strip()
                except KeyError:
                    continue

                try:
                    mid = re.search("[0-9]+", row[id_column].strip()).group(0)
                except AttributeError or KeyError:
                    continue

                record = self.get_record(mid)
                record.label = label
                self.update_record(mid, record)
        logger.debug("Finished adding records.")
