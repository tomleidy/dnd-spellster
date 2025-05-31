

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
    "source": r"^Source: ([\w\W]+)$",
    "level_school": rf"(\d+){REGEX_ORDINAL}-level ([\w]+){REGEX_EXTRA}{REGEX_EXTRA}",
    "school_cantrip": rf"^({REGEX_SCHOOLS})\s+(cantrip){REGEX_EXTRA}{REGEX_EXTRA}",
    "casting_time": r"^Casting Time: ([\w\s]+)",
    "range": r"^Range: ([\w\W]+)<br ?/>",
    "components": r"^Components: ",
    "duration": r"^Duration: (?:(Concentration), )([\w\s]+)",
    "spell_lists": r"^Spell Lists\. ([\w\s,]+)",
    # might be multiple descriptions, test iterations (make sure they don't match spell list first)
    "descriptions": r"<p>([\w\W]+)</p>",

}
