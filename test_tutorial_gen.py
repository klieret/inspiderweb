#!/usr/bin/env python3

""" Extract all relevant calls of inspiderweb.py and similar programs 
from the readme file, add them to a bash file, which is then run by travis. 
This doesn't really do any
tests on whether the output is correct, but it will ensure that we are
notified if anything exits with an error. 
"""


with open("readme.md", "r") as readme_file, open("test_tutorial.sh", "w") as output_file:
    for line in readme_file:
        if not line:
            continue
        if not line.startswith(" "*4) and not line.startswith("\t"):
            # not inside of code block
            continue
        line = line.strip()
        line.replace("\t", "")
        # only want the calls to inspiderweb, not whatever we do after
        line = line.split("&&")[0]
        # if <...> in the command line, then it probably is a mockup
        if "<" in line and ">" in line:
            continue
        if "python3 inspiderweb.py" not in line:
            continue
        output_file.write(line + "\n")
