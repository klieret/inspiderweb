#!/usr/bin/env python3

import datetime
from inspiderweb.log import logger
from inspiderweb.database import Database
from inspiderweb.dotgraph import DotGraph
import sys

db = Database("db/test2.pickle")
db.load()

db.get_references("566620")
db.get_citations("566620")


db.save()