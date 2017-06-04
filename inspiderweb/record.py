import time
import urllib.request
import socket
import re
from .log import logger

""" Part of inspiderweb: Tool to analyze paper reference networks.
Inspiderweb currently hosted at: https://github.com/klieret/inspiderweb

This file defines the Record class which describes one paper/record from
inspirehep.
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
    for attempt in range(retries):
        logger.debug("Downloading from {}.".format(url))
        try:
            string = urllib.request.urlopen(url).read().decode("utf-8")
        except Exception:
            logger.warning("Download of {} failed. Sleeping for {}s"
                           "before maybe retrying.".format(url, sleep_after))
            time.sleep(sleep_after)
            continue

        logger.debug("Download successfull. Sleeping for {}s.".format(
            sleep_after))
        time.sleep(sleep_after)
        break

    if string:
        return string

    logger.error("Finally failed to download {}. Now stopping.".format(url))
    if raise_exception:
        raise TimeoutError

    return ""


class Record(object):
    """ Instances of the record class describe one paper/record from
    inspirehep.
    """
    def __init__(self, mid, label=None):
        self.inspire_url = "http://inspirehep.net/record/{}".format(mid)
        self._label = label
        self.bibkey = ""
        self.mid = mid
        self.references_dl = False
        self.references = set([])
        self.citations_dl = False
        self.citations = set([])
        self.cocitations_dl = False
        self.cocitations = set([])

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
        assert self.mid == other.mid
        self.references.update(other.references)
        self.citations.update(other.citations)
        self.cocitations.update(other.cocitations)

        if not self._label:
            self._label = other.label

    # fixme: Rather separate that from self._label so that we can combine bibkey and label
    @property
    def label(self):
        if self.bibkey:
            return self.bibkey
        if self._label:
            return self._label
        return self.inspire_url.split("/")[-1]

    @label.setter
    def label(self, label):
        self._label = label

    def is_complete(self) -> bool:
        """ Did we download all the information that we can download?"""
        return bool(self.bibkey and self.references_dl and self.citations_dl
                    and self.cocitations_dl)

    # todo: make that accept arguments
    def autocomplete(self, force=False) -> bool:
        """ Download every possible piece of information.

        Args:
            force: Force redownload of the item.

        Returns:  True if successfull.
        """

        a = self.get_info(force=force)
        b = self.get_citations(force=force)
        c = self.get_references(force=force)
        return a and b and c

    def get_info(self, force=False) -> bool:
        """ Download the bibfile of the record from inspirehep and parse it
        to extract the bibkey.

        Args:
            force: Force redownload of the item.

        Returns:  True if successfull.
        """

        if self.bibkey and not force:
            logger.debug("Skipping downloading of info.")
            return False
        bibkey_regex = re.compile(r"@\w*\{([^,]*),")
        logger.debug("Downloading bibfile of {}".format(self.mid))
        bib_entry = download(self.inspire_url + "/export/hx")
        if not bib_entry:
            return False
        bibkey = bibkey_regex.search(bib_entry).group(1)
        logger.debug("Bibkey of {} is {}".format(self.mid, bibkey))
        self.bibkey = bibkey
        return True

    def get_citations(self, force=False) -> bool:
        """ Download (co)citations from inspirehep. Note that the download
        might take quite some time, if the paper got (co)cited really
        often.

        Args:
            force: Force redownload of the item.

        Returns:  True if successfull.
        """

        if self.citations_dl and self.cocitations_dl and not force:
            logger.debug("Skipping downloading of citations.")
            return False
        record_regex = re.compile("/record/([0-9]*)")
        logger.debug("Downloading citations of {}".format(self.mid))
        citations_html = download(self.inspire_url + "/citations")
        if not citations_html:
            return False
        citations = []
        cocitations = []
        # fixme: Parsing should definitely be improved
        cocitations_started = False
        for i, line in enumerate(citations_html.split('\n')):
            if "Co-cited with" in line:
                cocitations_started = True
            if not cocitations_started:
                citations += record_regex.findall(line)
            else:
                cocitations += record_regex.findall(line)
        citations = [record for record in citations if not record == self.mid]
        logger.debug("{} is cited by {} records".format(self.mid, len(citations)))
        logger.debug("{} is co-cited with {} records".format(self.mid, len(cocitations)))

        self.citations.update(citations)
        self.cocitations.update(cocitations)
        self.citations_dl = True
        self.cocitations_dl = True
        return True

    def get_references(self, force=False) -> bool:
        """ Download references from inspirehep.

        Args:
            force: Force redownload of the item.

        Returns:  True if successfull.
        """
        if self.references_dl and not force:
            logger.debug("Skipping downloading of references.")
            return False
        record_regex = re.compile("/record/([0-9]*)")
        logger.debug("Downloading references of {}".format(self.mid))
        reference_html = download(self.inspire_url + "/references")
        if not reference_html:
            return False
        records = record_regex.findall(reference_html)
        records = [record for record in records if not record == self.mid]
        logger.debug("{} is citing {} records".format(self.mid, len(records)))
        self.references.update(records)
        self.references_dl = True
        return True

    def __str__(self):
        return "R({})".format(self.mid)

    def __repr__(self):
        return self.__str__()