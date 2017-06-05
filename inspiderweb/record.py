import time
import urllib.request
import socket
import re
import json
# from .log import logger
# import pyinspire.pyinspire

import logging
logger = logging.getLogger("test")

""" Part of inspiderweb: Tool to analyze paper reference networks.
Inspiderweb currently hosted at: https://github.com/klieret/inspiderweb

This file defines the Record class which describes one paper/record from
inspirehep.
"""





class Record(object):
    """ Instances of the record class describe one paper/record from
    inspirehep.
    """
    def __init__(self, recid, label=None):
        self.inspire_url = "http://inspirehep.net/record/{}".format(recid)
        self.fulltext_url = "" # fixme: add to sync
        self.custom_label = label
        self.bibkey = ""
        self.recid = recid
        self.references = set([])
        self.citations = set([])
        self.cocitations = set([])
        self.references_dl = False
        self.citations_dl = False
        self.cocitations_dl = False

    def merge(self, other) -> None:
        """ Merge this record with another Record
        Args:
         other: other record to be merged into this one

        Returns: None
        """

        assert self.inspire_url == other.inspire_url
        if self.bibkey and other.bibkey:
            assert self.bibkey == other.bibkey
        if not self.bibkey:
            self.bibkey = other.bibkey
        assert self.recid == other.recid

        self.references.update(other.references)
        self.citations.update(other.citations)
        self.cocitations.update(other.cocitations)

        self.references_dl |= other.references_dl
        self.citations_dl |= other.citations_dl
        self.cocitations_dl |= other.cocitations_dl

        if not self.custom_label:
            self.custom_label = other.label

    # fixme: Rather separate that from self._label so that we can combine ...
    # bibkey and label
    @property
    def label(self):
        if self.bibkey:
            return self.bibkey
        if self.custom_label:
            return self.custom_label
        return self.inspire_url.split("/")[-1]

    def is_complete(self) -> bool:
        """ Did we download all the information that we can download?"""
        return bool(self.bibkey and self.references_dl and self.citations_dl
                    and self.cocitations_dl)

    # # todo: make that accept arguments
    # def autocomplete(self, force=False) -> bool:
    #     """ Download every possible piece of information.
    #
    #     Args:
    #         force: Force redownload of the item.
    #
    #     Returns:  True if successfull.
    #     """
    #
    #     a = self.get_info(force=force)
    #     b = self.get_citations(force=force)
    #     c = self.get_references(force=force)
    #     return a and b and c
    #
    # def get_info(self, force=False) -> bool:
    #     """ Download the bibfile of the record from inspirehep and parse it
    #     to extract the bibkey.
    #
    #     Args:
    #         force: Force redownload of the item.
    #
    #     Returns:  True if successfull.
    #     """
    #
    #     if self.bibkey and not force:
    #         logger.debug("Skipping downloading of info.")
    #         return False
    #     bibkey_regex = re.compile(r"@\w*\{([^,]*),")
    #     logger.debug("Downloading bibfile of {}".format(self.recid))
    #     bib_entry = download(self.inspire_url + "/export/hx")
    #     if not bib_entry:
    #         return False
    #     bibkey = bibkey_regex.search(bib_entry).group(1)
    #     logger.debug("Bibkey of {} is {}".format(self.recid, bibkey))
    #     self.bibkey = bibkey
    #     return True
    #
    # def get_citations(self, force=False) -> bool:
    #     """ Download (co)citations from inspirehep. Note that the download
    #     might take quite some time, if the paper got (co)cited really
    #     often.
    #
    #     Args:
    #         force: Force redownload of the item.
    #
    #     Returns:  True if successfull.
    #     """
    #
    #     if self.citations_dl and self.cocitations_dl and not force:
    #         logger.debug("Skipping downloading of citations.")
    #         return False
    #     record_regex = re.compile("/record/([0-9]*)")
    #     logger.debug("Downloading citations of {}".format(self.recid))
    #     citations_html = download(self.inspire_url + "/citations")
    #     if not citations_html:
    #         return False
    #     citations = []
    #     cocitations = []
    #     # fixme: Parsing should definitely be improved
    #     cocitations_started = False
    #     for i, line in enumerate(citations_html.split('\n')):
    #         if "Co-cited with" in line:
    #             cocitations_started = True
    #         if not cocitations_started:
    #             citations += record_regex.findall(line)
    #         else:
    #             cocitations += record_regex.findall(line)
    #     citations = [record for record in citations if not record == self.recid]
    #     logger.debug("{} is cited by {} records".format(
    #         self.recid, len(citations)))
    #     logger.debug("{} is co-cited with {} records".format(
    #         self.recid, len(cocitations)))
    #
    #     self.citations.update(citations)
    #     self.cocitations.update(cocitations)
    #     self.citations_dl = True
    #     self.cocitations_dl = True
    #     return True



    def __str__(self):
        return "R({})".format(self.recid)

    def __repr__(self):
        return self.__str__()

if __name__ == "__main__":
    r = Record("566620")
    r.get_references()