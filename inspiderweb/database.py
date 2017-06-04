import logging
import pickle
from .record import Record
import csv
import os.path
import re
import time

logger = logging.getLogger("inspirespider")

class Database(object):
    def __init__(self, backup_path):
        self._records = {}
        self.backup_path = backup_path

    def statistics(self):
        logger.info(" statistics ".upper().center(50, "*"))
        logger.info("Current number of records: {}".format(len(self._records)))
        # print(self._records.keys())
        # for mid, r in self._records.items():
        #     print(r.mid, r.is_complete())
        logger.info("Current number of completed records: {}".format(
            sum([int(r.is_complete()) for mid, r in self._records.items()])))
        logger.info("Current number of records with bibkey: {}".format(
            sum([int(bool(r.bibkey)) for mid, r in self._records.items()])
        ))
        logger.info("*"*50)

    def load(self, path=""):
        if not path:
            path = self.backup_path
        if not os.path.exists(path):
            logger.warning("Could not load db from file.")
            return False
        self._records = pickle.load(open(path, "rb"))
        logger.debug("Successfully loaded db from {}".format(path))
        return True

    def save(self, path=""):
        if not path:
            path = self.backup_path
        pickle.dump(self._records, open(path, "wb"))
        logger.debug("Successfully saved db to {}".format(path))

    def autocomplete_records(self, force=False, save_every=5,
                             info=True,
                             references=True,
                             citations=True):

        i = 0
        for mid, record in self._records.items():
            i += 1
            if i % save_every == 0:
                self.save()
            if i % 10 == 0:
                self.statistics()
                logger.debug("Sleeping a bit longer.")
                time.sleep(15)

            if info:
                record.get_info(force=force)
            if references:
                record.get_references(force=force)
            if citations:
                record.get_citations(force=force)

            self.update_record(mid, record)

    def get_record(self, mid):
        if mid in self._records:
            return self._records[mid]
        else:
            return Record(mid)

    def update_record(self, mid, record):
        self._records[mid] = record

    def load_records_from_urls(self,
                               path: str,
                               delimiter_char=";",
                               comment_char="#",
                               label_column=0,
                               id_column=1):
        logger.info("Adding records from {}".format(path))
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

                r =self.get_record(mid)
                r.label = label
                self.update_record(mid, r)
        logger.debug("Finished adding records.")