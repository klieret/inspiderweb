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

