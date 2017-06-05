#!/usr/bin/env python3

import datetime
from inspiderweb.log import logger
from inspiderweb.database import Database
from inspiderweb.dotgraph import DotGraph
import sys

db = Database("db/test.pickle")

db.get_recids_from_search("refersto:recid:566620")