import re
import logging

_log = logging.getLogger(__name__)


class DecodeError(Exception):
    pass

