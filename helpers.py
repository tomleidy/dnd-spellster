"""
Helper functions
- to test if a string matches a pattern
- to replace unexpected characters

"""

import re
from patterns import regex_dict, RE_FLAGS

SANITIZE_PAIRS = [("–", "-"), (" ", " "), ("’", "'")]


def santize_string(line: str) -> str:
    """ Get rid of some weird gunk in strings please"""
    for search, replace in SANITIZE_PAIRS:
        line.replace(search, replace)
    return line


def is_source(line: str) -> bool:
    """ Is this section the source book? """
    return re.match(regex_dict["source"], line, flags=RE_FLAGS)


def is_level_school_etc(line: str) -> bool:
    """ Does this line contain school and level? """
    return re.match(regex_dict["level_school"], line, flags=RE_FLAGS) or \
        re.match(regex_dict["school_cantrip"], line, flags=RE_FLAGS)


def is_casting_time(line: str) -> bool:
    """ Does this line contain casting time? """
    return re.match(regex_dict["casting_time"], line, flags=RE_FLAGS)


def does_line_need_splitting(line: str) -> bool:
    """ Is this a multiline string? """
    return "\n" in line


def is_range(line: str) -> bool:
    """ Does this line contain range information? """
    return re.match(regex_dict["range"], line, flags=RE_FLAGS)


def is_components(line: str) -> bool:
    """ Does this line contain component information? """
    return re.match(regex_dict["components"], line, flags=RE_FLAGS)
