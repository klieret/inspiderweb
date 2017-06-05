#!/usr/bin/env python3

import logging
from inspiderweb.log import logger
from inspiderweb.database import Database
from inspiderweb.dotgraph import DotGraph
import sys
import unittest
import os.path

# todo: do I really want to disable logging?
logger.setLevel(logging.ERROR)


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.test_recid = "566620"
        assert not os.path.exists("db/tmp_test")
        self.db = Database("db/tmp_test")

    def test_empty_db(self):
        assert not self.db._records
        self.db.load()
        assert os.path.exists(self.db.backup_path)

    def test_add_record(self):
        self.db.get_record(self.test_recid )
        assert len(self.db._records) == 1

    def test_empty_record(self):
        r = self.db._records[0]
        assert r.recid == self.test_recid

    def test_get_references(self):
        record = self.db.get_record(self.test_recid)
        assert not record.references_dl
        assert len(record.references) == 0
        db.get_references(self.test_recid)
        assert len(record.references) == 35
        assert record.references_dl

    def test_get_citations(self):
        record = self.db.get_citations(self.test_recid)
        assert not record.citations_dl
        assert len(record.citations) == 0
        db.get_references(self.test_recid)
        assert len(record.citations) == 9
        assert record.citations_dl

    def test_save(self):
        self.db.save()
        db2 = Database(self.db.backup_path)
        db2.load()
        assert len(db2._records) == len(self.db._records)
        for recid, record in db2._records.items():
            assert record == self.db.get_record(recid)

    def tearDown(self):
        os.remove(self.db.backup_path)
