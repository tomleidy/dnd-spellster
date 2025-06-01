import re

schools_dict = {
    "abjuration": "Abjuration", "conjuration": "Conjuration", "divination": "Divination",
    "enchantment": "Enchantment", "evocation": "Evocation", "illusion": "Illusion",
    "necromancy": "Necromancy", "transmutation": "Transmutation", "dunamancy": "Dunamancy",
    "dunamancy:chronurgy": "Chronurgy Dunamancy:", "dunamancy:graviturgy": "Graviturgy Dunamancy",
    "ritual": "Ritual", "technomagic": "Technomagic"
}
REGEX_SCHOOLS = "|".join(schools_dict.keys())
REGEX_EXTRA = r"(?: \(([\w:]+)\))?"
REGEX_ORDINAL = r"(?:st|nd|rd|th)"

regex_dict = {
    "title": r"^Title: .+$",
    "source": r"^Source: ([\w\W]+)$",
    "level_school": rf"^(\d+){REGEX_ORDINAL}-level ([\w]+){REGEX_EXTRA}{REGEX_EXTRA}$",
    "school_cantrip": rf"^({REGEX_SCHOOLS})\s+(cantrip){REGEX_EXTRA}{REGEX_EXTRA}$",
    "casting_time": r"^Casting Time: [, \w]+",
    "casting_times_only": r"(\d+ +(?:action|bonus action|reaction|hours?|minutes?))",
    "casting_time_combat": r"(\d+) +((?:action|bonus action|reaction))",
    "casting_time_noncombat": r"(\d+) +((?:hours?|minutes?))",
    "casting_time_reaction_conditions": r", ([\w ,]+when[\w ,]+)",
    "range": r"Range: ([\w\s(),-]+)(?:\nComponents)?",
    "components": r"^Components: ",
    "duration": r"^Duration: (?:(Concentration), )([\w\s]+)",
    "spell_lists": r"^Spell Lists\. ([\w\s,]+)",
    # might be multiple descriptions, test iterations (make sure they don't match spell list first)
    "descriptions": r"<p>([\w\W]+)</p>",

}
RE_FLAGS = re.IGNORECASE


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
