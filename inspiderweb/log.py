import logging

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
