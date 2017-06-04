import logging

""" Part of inspiderweb: Tool to analyze paper reference networks.
Inspiderweb currently hosted at: https://github.com/klieret/inspiderweb

This file sets up logger/logging.
"""

logger = logging.getLogger("inspirespider")

if not len(logger.handlers) == 1:
    # has not been set up
    logger.setLevel(logging.DEBUG)
    sh = logging.StreamHandler()
    sh.setLevel(logging.DEBUG)
    fm = logging.Formatter("%(levelname)s: %(message)s")
    sh.setFormatter(fm)
    logger.addHandler(sh)
    logger.addHandler(sh)
