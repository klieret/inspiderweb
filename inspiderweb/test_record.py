import unittest

from . import record

# fixme: still throws errors
class RecordTest(unittest.TestCase):
    def setUp(self):
        self.r = record.Record("1471118")

    def test_recid(self):
        assert self.r.recid == "1471118"

    def test_inspireurl(self):
        assert self.r.inspire_url == \
               "http://inspirehep.net/record/1471118/citations"

    def test_emptylabel(self):
        assert self.r.label == self.r.recid

    def test_dl_remaining(self):
        assert not self.r.references_dl
        assert not self.r.citations_dl
        assert not self.r.cocitations_dl

    def test_dl_info(self):
        self.r.get_info()
        assert self.r.bibkey == "Maruyoshi:2016tqk"

    def test_dl_references(self):
        self.r.get_references()
        assert self.r.references_dl
        assert len(self.r.references) == 27

    def test_dl_citations(self):
        self.r.get_citations()
        assert self.r.citations_dl
        assert self.r.cocitations_dl
        assert len(self.r.citations) == 10
        assert len(self.r.cocitations) == 403
