""" The engine for this madness. The regular expressions and related constants. """
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

regex_range_dict = {
    "focus_and_shape": r"Self \((\d+)-(([\w]+)[ -]?([\w ]+)\))",
    "descriptive": r"^(Sight|Special|Touch|Unlimited|Self)$",
    "distance_and_units": r"([\d,]+)[- ]?(feet|ft|miles?)"
}

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
    "components": r"^Components:\s([VSM, ]+)(?:\s\(([\w\.,;’' -]+)\))?",
    "duration": r"^Duration: (?:(Concentration), )?([\w ,\(\)]+)",
    "spell_lists": r"^Spell Lists\. ([\w\s,]+)",
    # might be multiple descriptions, test iterations (make sure they don't match spell list first)
    "descriptions": r"<p>([\w\W]+)</p>",

}
RE_FLAGS = re.IGNORECASE
