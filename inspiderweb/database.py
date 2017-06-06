import pickle
from .record import Record
import csv
import os.path
import re
import time
from .log import logger
from typing import List
import socket
import urllib.request
import json
import collections

""" Part of inspiderweb: Tool to analyze paper reference networks.
Inspiderweb currently hosted at: https://github.com/klieret/inspiderweb

This file defines the Database class. The Database mostly is a collection of
Record objects (that hold information of a record/paper from inspirehep) plus
some methods to update/save/cache information.
"""


def download(url: str, retries=3, timeout=10, sleep_after=3,
             raise_exception=False) -> str:
    """ Download from url with automatic retries.
    Also prints logging messages.

    Args:
        url: Url to download.
        retries: Number of possible retries.
        timeout: Abort downloading after $timeout s.
        sleep_after: Time [s] to sleep after each attempt.
        raise_exception: Raise Exception if download fails after retries.
    """
    socket.setdefaulttimeout(timeout)
    string = ""
    success = False
    for attempt in range(retries):
        logger.debug("Trying to download from from {}.".format(url))
        try:
            string = urllib.request.urlopen(url).read().decode("utf-8")
        except Exception as ex:
            logger.warning("Download of {} failed because of {}. "
                           "Sleeping for {}s before "
                           "maybe retrying.".format(url, ex,  sleep_after))
            time.sleep(sleep_after)
            continue

        logger.debug("Download successfull. Sleeping for {}s.".format(
            sleep_after))
        time.sleep(sleep_after)
        success = True
        break

    if success:
        return string

    logger.error("Finally failed to download {}. Now stopping.".format(url))
    if raise_exception:
        raise TimeoutError

    return ""


class Database(object):
    """  The Database mostly is a collection of
    Record objects (that hold information of a record/paper from inspirehep)
    plus some methods to update/save/cache information.
    The records are collected in self._records, a dictionary of the form
    recid: record, where record is a Record object and recid is the inspirehep
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
            sum([int(r.references_dl) for recid, r in self._records.items()])))
        logger.info("Current number of records with citations: {}".format(
            sum([int(r.citations_dl) for recid, r in self._records.items()])))
        logger.info("Current number of records with cocitations: {}".format(
            sum([int(r.cocitations_dl) for recid, r in self._records.items()])))
        logger.info("Current number of records with bibkey: {}".format(
            sum([int(bool(r.bibkey)) for recid, r in self._records.items()])
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
        with open(path, "rb") as dbstream:
            _records = pickle.load(dbstream)
        for recid, their_record in _records.items():
            assert recid == their_record.recid
            my_record = self.get_record(recid)
            my_record.merge(their_record)
            self.update_record(recid, my_record)
        logger.debug("Successfully loaded db from {}".format(path))
        return True

    def save(self, path=""):
        """ Save the database to file.
        If no path is given self.backup_path will be used. """

        if not path:
            path = self.backup_path
        with open(path, "wb") as dbfile:
            pickle.dump(self._records, dbfile)
        logger.debug("Successfully saved db to {}".format(path))

    def get_record(self, recid):
        """ Return record with id $recid from database. Record will be created
        if it was not in the database before.
        """

        if recid in self._records:
            return self._records[recid]
        else:
            self._records[recid] = Record(recid)
            return self._records[recid]

    def update_record(self, recid, record):
        """ Update record with id $recid with record $record. """
        self._records[recid] = record

    def autocomplete_records(self, updates: List, force=False, save_every=5,
                             recids=None, statistics_every=5) -> bool:
        """ Download information for each record from inspirehep.

        Args:
            updates (list): What information should be downloaded.
                            Options are
                            "bib" (bibtex, in particular the bibkey),
                            "refs" (references of the record),
                            "cites" (citations and cocitations of th erecord)
            force (bool): Force redownload of information
            save_every (int): Save database after this many completed records
            recids (list): Only download information for records with id 
                           (recid) in this list.
            statistics_every(int): Print statistics after this many downloaded
                                   items.

        Returns: True if we actually did something.
        """

        for update in updates:
            if update not in ["bib", "refs", "cites"]:
                logger.error("Unrecognize update option {}. "
                             "I will simply ignore this for "
                             "now.".format(update))
                updates.remove(update)

        if not updates:
            return

        if not recids:
            recids = self._records.keys()

        logger.debug("Downloading {} for {} records.".format(
            ', '.join(updates), len(recids)))

        for i, recid in enumerate(recids):
            if i and i % save_every == 0:
                self.save()
            if i and i % statistics_every == 0:
                self.statistics()
                logger.debug("Sleeping a bit longer.")
                time.sleep(15)

            record = self.get_record(recid)

            if "bib" in updates:
                record.get_info(force=force)
            if "refs" in updates:
                record.get_references(force=force)
            if "cites" in updates:
                record.get_citations(force=force)

            self.update_record(recid, record)

        return True

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
            id_column: Column with the recid [1]
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
                    recid = re.search("[0-9]+",
                                      row[id_column].strip()).group(0)
                except AttributeError or KeyError:
                    continue

                record = self.get_record(recid)
                record.custom_label = label
                self.update_record(recid, record)
        logger.debug("Finished adding records.")

    def get_references(self, recid, force=False) -> bool:
        """ Download references from inspirehep.
        """
        record = self.get_record(recid)
        if record.references_dl and not force:
            logger.debug("Skipping downloading of references.")
            return False
        # fixme: those are actually citations
        search_string = "citedby:recid:{}".format(record.recid)
        recids = self.get_recids_from_search(search_string)
        logger.debug("{} is citing {} references.".format(recid, len(recids)))
        record.references.update(recids)
        self.update_record(recid, record)
        record.references_dl = True
        return True

    def get_citations(self, recid, force=False) -> bool:
        """ Download citations from inspirehep.
        """
        record = self.get_record(recid)
        if record.citations_dl and not force:
            logger.debug("Skipping downloading of citations.")
            return False
        search_string = "refersto:recid:{}".format(record.recid)
        recids = self.get_recids_from_search(search_string)
        logger.debug("{} is cited by {} records.".format(recid, len(recids)))
        record.citations.update(recids)
        self.update_record(recid, record)
        record.citations_dl = True
        return True

    # fixme: somehow still doesn't work with recjson:
    # http://inspirehep.net/search?p=cocitedwith:566620&of=h&rg=25&sc=0
    # works perfectly fine but
    # http://inspirehep.net/search?p=cocitedwith:566620&of=recjson&ot=recid&rg=25&sc=0
    # only returns empty '[]'.
    #
    # def get_cocitations(self, recid, force=False) -> bool:
    #     """ Download cocitations from inspirehep.
    #     """
    #     record = self.get_record(recid)
    #     if record.cocitations_dl and not force:
    #         logger.debug("Skipping downloading of citations.")
    #         return False
    #     search_string = "cocitedwith:{}".format(record.recid)
    #     recids = self.get_recids_from_search(search_string)
    #     logger.debug("{} is cocited with {} records.".format(recid,
    #                                                          len(recids)))
    #     record.cocitations.update(recids)
    #     self.update_record(recid, record)
    #     record.cocitations_dl = True
    #     return True

    def get_recids_from_search(self, searchstring: str, record_group=25) -> set:
        # Long responses are split into chunks of $record_group records
        # so we need an additional loop.
        record_offset = 0
        recids = []
        while True:
            new_recids = self.get_recids_from_search_chunk(
                searchstring, record_group, record_offset)
            recids.extend(new_recids)
            # print("recids from rg", record_offset, new_recids)
            if len(new_recids) < record_group:
                break
            record_offset += record_group - 1
        # print(recids)
        recids = map(str, recids)  # fixme: shouldn't need that actually....
        recids_unique = set(recids)
        duplicates = [recid for recid, count in
                      collections.Counter(recids).items() if count > 1]
        if duplicates:
            logger.warning("The following {} records appeared more than once:"
                           "{}".format(len(duplicates),
                                       ', '.join(duplicates)))
        else:
            logger.debug("No duplicates.")
        return recids_unique

    def get_recids_from_search_chunk(self, searchstring: str,
                                     record_group: int,
                                     record_offset: int) -> List:
        """ Returns a list of the recids of all results found, while updating
        the db with pieces of information found on the way.
        """
        api_string = "http://inspirehep.net/search" \
                     "?p={p}&of={of}&ot={ot}&rg={rg}&jrec={jrec}".format(
                      p=searchstring,  # search query
                      of="recjson",  # output format
                      ot="recid,system_control_number",  # output tags
                      rg=record_group,  # how many results/records (default 25)
                      jrec=record_offset)  # result offset
        # result = download(api_string)
        result = download(api_string)
        if not result:
            return []
        pyob = json.loads(result)
        if not pyob:
            return []
        recids = []
        for record in pyob:
            # print(record)
            recid = str(record['recid'])
            bibkey = ""
            arxiv_code = ""
            if not isinstance(record['system_control_number'], list):
                # if there is only one value here, than this is not a list
                # and in this case the only value supplied should be the
                # bibtex key
                system = record['system_control_number']
                assert system["institute"] in ['INSPIRETeX', 'SPIRESTeX']
                bibkey = system["value"]
            else:
                # we have a list and go through it to pick out relevant
                # information
                for system in record['system_control_number']:
                    if system["institute"] == 'arXiv' and "value" in system:
                        arxiv_code = system["value"]
                    if system["institute"] in ['INSPIRETeX', 'SPIRESTeX'] \
                            and "value" in system:
                            if bibkey:
                                # we already met a bibkey, so compare it
                                # with this one
                                assert bibkey == system["value"]
                            else:
                                bibkey = system["value"]
            # todo: maybe use merge instead
            recids.append(recid)
            record = self.get_record(recid)
            if record.bibkey:
                assert record.bibkey == bibkey
            else:
                record.bibkey = bibkey
            if not record.fulltext_url and arxiv_code:
                # The arxiv url looks like: oai:arXiv.org:1701.02937
                # or oai:arXiv.org:hep-ph/0208013
                arxiv_url = "http://arxiv.org/pdf/" + arxiv_code.split(':')[-1]
                record.fulltext_url = arxiv_url
            self.update_record(recid, record)
        return recids
