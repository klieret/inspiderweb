import logging

""" Part of inspiderweb: Tool to analyze paper reference networks.
Inspiderweb currently hosted at: https://github.com/klieret/inspiderweb

This file sets up logger/logging.
"""


class LogControl(object):
    """ The only use of this object is so that we have easy access
    to the stream handler etc. associated with the logger. """
    def __init__(self, logger_):
        self.logger = logger_
        self.logger.setLevel(logging.DEBUG)
        self.sh = logging.StreamHandler()
        self.sh.setLevel(logging.DEBUG)
        self.fm = logging.Formatter("%(levelname)s: %(message)s")
        self.sh.setFormatter(self.fm)
        self.logger.addHandler(self.sh)

    def set_verbosity_from_argparse(self, option):
        self.sh.setLevel(getattr(logging, option.upper()))

logger = logging.getLogger("inspirespider")
logcontrol = LogControl(logger)
