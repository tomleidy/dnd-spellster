""" The engine for this madness. The regular expressions and related constants. """
import re

# yes, it would be easier to just use lower and replace these, but these I need to be precise
schools_dict = {
    "abjuration": "Abjuration", "conjuration": "Conjuration", "divination": "Divination",
    "enchantment": "Enchantment", "evocation": "Evocation", "illusion": "Illusion",
    "necromancy": "Necromancy", "transmutation": "Transmutation", "dunamancy": "Dunamancy",
    "dunamancy:chronurgy": "Chronurgy Dunamancy:", "dunamancy:graviturgy": "Graviturgy Dunamancy",
    "ritual": "Ritual", "technomagic": "Technomagic"
}
classes_dict = {
    "Artificer": "artificer", "Bard": "bard", "Cleric": "cleric",
    "Druid": "druid", "Paladin": "paladin", "Ranger": "ranger",
    "Sorcerer": "sorcerer", "Warlock": "warlock", "Wizard": "wizard",
    "Wizard (Dunamancy)": "wizard", "Wizard (Graviturgy)": "wizard",
}
classes_list = [pc + " (Optional)" for pc in classes_dict if "(" not in pc] + \
    [pc for pc in classes_dict]
classes_list.sort()
REGEX_CLASSES = "|".join(classes_list).replace("(", "\(").replace(")", "\)")
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
    "spell_lists": r"^Spell Lists",
    "spell_lists_classes": rf"({REGEX_CLASSES})",
    # might be multiple descriptions, test iterations (make sure they don't match spell list first)
    "descriptions": r"<p>([\w\W]+)</p>"

}
RE_FLAGS = re.IGNORECASE
