""" Part of inspiderweb: Tool to analyze paper reference networks.
Inspiderweb currently hosted at: https://github.com/klieret/inspiderweb

This file defines the Record class which collects the necessary information
we need from one record/one paper on inspirehep.
"""


class Record(object):
    """ Instances of the record class describe one paper/record from
    inspirehep.
    """
    def __init__(self, recid, label=None):
        self.inspire_url = "http://inspirehep.net/record/{}".format(recid)
        self.fulltext_url = ""
        self.custom_label = label
        self.bibkey = ""
        self.recid = recid
        self.references = set([])
        self.citations = set([])
        self.cocitations = set([])
        self.references_dl = False
        self.citations_dl = False
        self.cocitations_dl = False
        self.info_dl = False

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

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
        self.info_dl |= other.info_dl

        if not self.custom_label:
            self.custom_label = other.custom_label
        if not self.fulltext_url:
            self.fulltext_url = other.fulltext_url

    @property
    def label(self):
        if self.bibkey:
            if self.custom_label:
                return "{} ({})".format(self.bibkey, self.custom_label)
            else:
                return self.bibkey
        elif self.custom_label:
            return self.custom_label
        return self.recid

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return "R({})".format(self.recid)
