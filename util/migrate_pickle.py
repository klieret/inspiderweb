#!/usr/bin/env python3

import pickle

records = pickle.load(open("_pickle.pickle", "rb"))
from inspiderweb.record import Record
# print(records)
new_records = {}
for mid, record in records.items():
    new_record = Record(mid)
    new_record.label = record.label
    new_record.citations = record.citations
    new_record.cocitations = record.cocitations
    new_record.references = record.references
    new_record.citations_dl = bool(record.citations)
    new_record.cocitations_dl = bool(record.cocitations)
    new_record.references_dl = bool(record.references)
    new_record.bibkey = record.bibkey
    new_records[mid] = new_record
    print(new_record.citations)
pickle.dump(new_records, open("pickle.pickle", "wb"))