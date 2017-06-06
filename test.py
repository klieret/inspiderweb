#!/usr/bin/env python3

import logging
from inspiderweb.log import logcontrol
from inspiderweb.database import Database
import unittest
import os.path

# todo: rather log to a file or something
logcontrol.sh.setLevel(logging.ERROR)


class TestBasics(unittest.TestCase):
    # things that don't need to download anything
    def setUp(self):
        self.db_path = "db/tmp_test"
        self.test_recid = "123456"
        # make sure we start over fresh
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = Database(self.db_path)
        self.db.load()

    def test_empty(self):
        self.assertEqual(len(self.db._records), 0)
        self.db.load()
        self.db.get_record(self.test_recid)
        self.assertEqual(len(self.db._records), 1)
        r = self.db._records[self.test_recid]
        self.assertEqual(r.recid, self.test_recid)

    def test_save_load(self):
        # add phony record
        record = self.db.get_record(self.test_recid)
        record.citations_dl = True
        record.citations = {"1", "2", "3"}
        record.bibkey = "asdf:2010x"
        record.custom_label = "blargh"
        self.db.update_record(self.test_recid, record)

        self.db.save()
        self.assertTrue(os.path.exists(self.db_path))
        db2 = Database(self.db.backup_path)
        db2.load()

        self.assertEqual(len(db2._records), len(self.db._records))
        for recid, record in db2._records.items():
            self.assertEqual(record, self.db.get_record(recid))


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.expected_recid_references = {"0699123": 21,
                                          "460528": 0, }
        self.expected_recid_citations = {"0699123": 104,
                                         "460528": 5, }
        self.db_path = "db/tmp_test"
        # make sure we start over fresh
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = Database(self.db_path)
        self.db.load()

    def test_get_references(self):
        for recid, expected in self.expected_recid_references.items():
            with self.subTest(recid=recid):
                self._test_get_references(recid, expected)

    def test_get_citations(self):
        for recid, expected in self.expected_recid_citations.items():
            with self.subTest(recid=recid):
                self._test_get_citations(recid, expected)

    def _test_get_references(self, recid, expected_references):
        record = self.db.get_record(recid)
        self.assertFalse(record.references_dl)
        self.assertEqual(len(record.references), 0)

        self.db.get_references(recid)

        self.assertEqual(len(record.references), expected_references)
        self.assertTrue(record.references_dl)

    def _test_get_citations(self, recid, expected_citations):
        record = self.db.get_record(recid)
        self.assertFalse(record.citations_dl)
        self.assertEqual(len(record.citations), 0)

        self.db.get_citations(recid)

        self.assertEqual(len(record.citations), expected_citations)
        self.assertTrue(record.citations_dl)
