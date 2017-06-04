import logging
import time
import urllib.request
import re

logger = logging.getLogger("inspirespider")

class Record(object):
    def __init__(self, mid, label=None):
        self.inspire_url = "http://inspirehep.net/record/{}".format(mid)
        self._label = label
        self.bibkey = ""
        self.mid = mid
        # if label:
        #     self.label = label
        # else:
        #     self.label = self.inspire_url.split('/')[-1]
        self.references_dl = False
        self.references = []
        self.citations_dl = False
        self.citations = []
        self.cocitations_dl = False
        self.cocitations = []

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

    def is_complete(self):
        return bool(self.bibkey and self.references_dl and self.citations_dl
                    and self.cocitations_dl)

    def autocomplete(self, force=False):
        reloaded = self.get_info(force=force)
        if reloaded:
            logger.debug("Sleeping for a bit.")
            time.sleep(1.5)
        reloaded = self.get_citations(force=force)
        if reloaded:
            logger.debug("Sleeping for a bit.")
            time.sleep(1.5)
        reloaded = self.get_references(force=force)
        if reloaded:
            logger.debug("Sleeping for a bit.")
            time.sleep(1.5)

    def get_info(self, force=False):
        if self.bibkey and not force:
            logger.debug("Skipping downloading of info.")
            return False
        bibkey_regex = re.compile(r"@\w*\{([^,]*),")
        logger.debug("Downloading bibfile of {}".format(self.mid))
        bib_entry = urllib.request.urlopen(
            self.inspire_url + "/export/hx").read().decode("utf-8")
        bibkey = bibkey_regex.search(bib_entry).group(1)
        logger.debug("Bibkey of {} is {}".format(self.mid, bibkey))
        self.bibkey = bibkey
        return True

    def get_citations(self, force=False):
        if self.citations_dl and not force:
            logger.debug("Skipping downloading of citations.")
            return False
        record_regex = re.compile("/record/([0-9]*)")
        logger.debug("Downloading citations of {}".format(self.mid))
        citations_html = urllib.request.urlopen(self.inspire_url + "/citations").read().decode("utf-8")
        # logger.debug("decode success")
        citations = []
        cocitations = []
        cocitations_started = False
        for i, line in enumerate(citations_html.split('\n')):
            # print(i, line )
            # line = line.decode("utf-8")
            if "Co-cited with" in line:
                cocitations_started = True
            if not cocitations_started:
                citations += record_regex.findall(line)
            else:
                cocitations += record_regex.findall(line)
        citations = [record for record in citations if not record == self.mid]
        logger.debug("{} is cited by {} records".format(self.mid, len(citations)))
        logger.debug("{} is co-cited with {} records".format(self.mid, len(cocitations)))

        self.citations = citations
        self.cocitations = cocitations
        self.citations_dl = True
        self.cocitations_dl = True
        return True

    def get_references(self, force=False):
        if self.references_dl and not force:
            logger.debug("Skipping downloading of references.")
            return False
        record_regex = re.compile("/record/([0-9]*)")
        logger.debug("Downloading references of {}".format(self.mid))
        reference_html = urllib.request.urlopen(
            self.inspire_url + "/references").read().decode("utf-8")
        records = record_regex.findall(reference_html)
        records = [record for record in records if not record == self.mid]
        logger.debug("{} is citing {} records".format(self.mid, len(records)))
        self.references = records
        self.references_dl = True
        return True

    def __str__(self):
        return "R({})".format(self.mid)

    def __repr__(self):
        return self.__str__()