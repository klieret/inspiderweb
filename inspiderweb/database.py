import pickle
from .record import Record
import csv
import os.path
import re
import time
from .log import logger
from typing import List, Set
import socket
import urllib.request
import urllib.parse
import json
import collections
import sys

""" Part of inspiderweb: Tool to analyze paper reference networks.
Inspiderweb currently hosted at: https://github.com/klieret/inspiderweb

This file defines the Database class. The Database mostly is a collection of
Record objects (that hold information of a record/paper from inspirehep) plus
some methods to update/save/cache information.
"""


def download(url: str, retries=3, timeout=10, sleep_after=1,
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
            sum([int(r.cocitations_dl) for recid, r in
                 self._records.items()])))
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
            logger.warning("Db does not exist yet. Creating it.")
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

    def get_record(self, recid: str):
        """ Return record with id $recid from database. Record will be created
        if it was not in the database before.
        """
        if isinstance(recid, int):
            # though we support ints as recids, this should be
            # discouraged, as we might swap the id system we use to bibkeys
            # and similar, all of which are strings.
            recid = str(recid)
            logger.warning("{} was supplied as int and not string. Though"
                           "this should work perfectly find, this is"
                           "discouraged.".format(recid))
        assert recid.isdigit()

        if recid in self._records:
            return self._records[recid]
        else:
            self._records[recid] = Record(recid)
            return self._records[recid]

    def get_recids_from_bibkeys(self, bibkeys: set, offline_only=False):
        """ Try to search for as many bibkeys as possible with one run
        as it speeds up the search in the internal database. """
        # 1. search internally
        results = {}
        for recid, record in self._records.items():
            if record.bibkey in bibkeys:
                if record.bibkey in results:
                    assert results[record.bibkey] == recid
                else:
                    results[record.bibkey] = recid
        if offline_only:
            return results
        # 2. search inspire for the remaining
        bibkeys -= set(results.keys())
        for bibkey in bibkeys:
            recids = self.get_recids_from_search(bibkey)
            if len(recids) == 1:
                results[bibkey] = list(recids)[0]
            else:
                logger.error("{} records found for bibkey {}. I won't add "
                             "anything. ".format(len(recids), bibkey))
        return results

    def update_record(self, recid, record):
        """ Update record with id $recid with record $record. """
        self._records[recid] = record

    def autocomplete_records(self, updates: Set[str], force=False,
                             save_every=5, recids=None,
                             statistics_every=5) -> set:
        """ Download information for each record from inspirehep.

        Args:
            updates (set of strings): 
                Which information should be downloaded? There are the 
                following basic options:
                * empty string: Bibliographic info of 
                  each recid.
                * refs (short r): References of each recid
                * cites (short c): Citations of each recid
                * refscites or citesrefs (short rc or cr): both
                The last three options can be chained, 
                e.g. refs.cites means
                1. For each supplied recid, get all reference
                2. For all of the above, get all citations.
                Note: This does not apply to 'info' (as the info 
                part of each of the references/citations will be
                downloaded anyway.
            force (bool): Force redownload of information
            save_every (int): Save database after this many completed records
            recids (list): Only download information for records with id 
                           (recid) in this list.
            statistics_every(int): Print statistics after this many downloaded
                                   items.

        Returns: True if we actually did something.
        """
        if not recids:
            recids = set()
        for update in updates:
            recids.update(self._autocomplete_records(update, force=force,
                          save_every=save_every, recids=recids,
                          statistics_every=statistics_every))
        return recids

    def _autocomplete_records(self, update: str, force=False, save_every=5,
                              recids=None, statistics_every=5) -> set:
        """ Worker function of self.autocomplete_records see there for more
        information on the parameters 
        """

        steps = update.split('.')
        if steps[0] in ['seeds', 's']:
            pass
        elif steps[0] in ['all', 'a']:
            recids = set(self._records.keys())
        else:
            logger.critical("Wrong syntax: Update string starts "
                            "with {}. Will abort.".format(steps[0]))
            sys.exit(1)

        steps = steps[1:]

        if len(steps) == 0:
            for i, recid in enumerate(recids):
                if i and i % save_every == 0:
                    self.save()
                if i and i % statistics_every == 0:
                    self.statistics()
                self.get_info(recid)

        for step in steps:
            logger.info("Downloading {} for {} records.".format(step,
                                                                len(recids)))
            # note how we are iterating over a copy of the set, instead of
            # changing the set itself!
            for i, recid in enumerate(recids.copy()):
                if i and i % save_every == 0:
                    self.save()
                if i and i % statistics_every == 0:
                    self.statistics()

                if step in ["refs", "r"]:
                    recids.update(self.get_references(recid, force=force))
                elif step in ["cites", "c"]:
                    recids.update(self.get_citations(recid, force=force))
                elif step in ["refscites", "rc", "cr", "citesrefs"]:
                    recids.update(self.get_references(recid, force=force))
                    recids.update(self.get_citations(recid, force=force))
                else:
                    logger.error("Unrecognize update option {}. "
                                 "I will simply ignore this for "
                                 "now.".format(step))
        return recids

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

    def get_info(self, recid, force=False) -> bool:
        record = self.get_record(recid)
        if record.info_dl and not force:
            logger.debug("Skipping downloading of info.")
            return False
        search_string = "recid:{}".format(record.recid)
        self.get_recids_from_search(search_string)
        record.info_dl = True
        self.update_record(recid, record)
        return True

    def get_references(self, recid, force=False) -> set():
        """ Download references from inspirehep.
        """
        record = self.get_record(recid)
        if record.references_dl and not force:
            logger.debug("Skipping downloading of references.")
            return record.references
        search_string = "citedby:recid:{}".format(record.recid)
        recids = self.get_recids_from_search(search_string)
        logger.debug("{} is citing {} references.".format(recid, len(recids)))
        record.references.update(recids)
        self.update_record(recid, record)
        record.references_dl = True
        return recids

    def get_citations(self, recid, force=False) -> set():
        """ Download citations from inspirehep.
        """
        record = self.get_record(recid)
        if record.citations_dl and not force:
            logger.debug("Skipping downloading of citations.")
            return record.citations
        search_string = "refersto:recid:{}".format(record.recid)
        recids = self.get_recids_from_search(search_string)
        logger.debug("{} is cited by {} records.".format(recid, len(recids)))
        record.citations.update(recids)
        self.update_record(recid, record)
        record.citations_dl = True
        return recids

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

    def get_recids_from_search(self, searchstring: str,
                               record_group=250) -> set:
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
        # somehow this is being flagged in pycharm, but seems to be correct
        # and runs without an error.
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
        base_url = "http://inspirehep.net/search?"
        api_string = "p={p}&of={of}&ot={ot}&rg={rg}&jrec={jrec}".format(
                      p=urllib.parse.quote_plus(searchstring),  # search query
                      of="recjson",  # output format
                      ot="recid,system_control_number",  # output tags
                      rg=record_group,  # number of records (def: 25, max: 250)
                      jrec=record_offset)  # result offset
        api_url = base_url + api_string
        result = download(api_url)
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
            if 'system_control_number' not in record:
                # this clearly shouldn't happen, because we requested this
                # tag
                logger.error("Key 'system_control_number' not found. This "
                             "shouldn't happen. "
                             "Full string: {}".format(record))
                continue

            if isinstance(record['system_control_number'], list):
                systems = record['system_control_number']
            else:
                systems = [record['system_control_number']]

            for system in systems:
                if not isinstance(system, dict):
                    logger.error("{} is not a dict. This shouldn't "
                                 "happen.".format(system))
                if "institute" not in system:
                    logger.error("{} does not contain the key 'institute'."
                                 "This shouldn't happen.".format(system))
                    continue

                if system["institute"] == 'arXiv' and "value" in system:
                    arxiv_code = system["value"]
                elif system["institute"] in ['INSPIRETeX', 'SPIRESTeX'] \
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
            # fixme: Set record.info_dl?
            if record.bibkey and bibkey:
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
