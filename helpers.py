"""
Helper functions
- to test if a string matches a pattern
- to replace unexpected characters

"""

import re
from patterns import regex_dict, RE_FLAGS, classes_dict

SANITIZE_PAIRS = [("–", "-"), (" ", " "), ("’", "'")]


def santize_string(line: str) -> str:
    """ Get rid of some weird gunk in strings please"""
    for search, replace in SANITIZE_PAIRS:
        line.replace(search, replace).strip()
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


def is_duration(line: str) -> bool:
    """ Does this line contain a duration? """
    return re.match(regex_dict["duration"], line, flags=RE_FLAGS)


def is_spell_list(line: str) -> bool:
    """ Does this line contain spell lists this spell shows up in? """
    return re.match(regex_dict["spell_lists"], line, flags=RE_FLAGS)


def get_class_column_name(pc_class: str) -> dict:
    """ Helper to get class names for database columns """
    new_class_dict = {}
    lookup_class = pc_class.replace(" (Optional)", "")
    if lookup_class in classes_dict:
        class_name = classes_dict[lookup_class]
        if pc_class.endswith("(Optional)"):
            class_name += "_optional"
        new_class_dict[class_name] = True
    return new_class_dict
