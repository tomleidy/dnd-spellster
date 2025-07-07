"""Filter utility for spells"""

import json
import argparse
import sys

SPELLCASTING_ABILITIES = {
    "paladin": "charisma",
    "sorcerer": "charisma",
    "warlock": "charisma",
    "bard": "charisma",
    "cleric": "wisdom",
    "druid": "wisdom",
    "ranger": "wisdom",
    "wizard": "intelligence",
    "artificer": "intelligence",
    "eldritch knight": "intelligence",  # fighter subclass
    "arcane trickster": "intelligence",  # rogue subclass
}


def get_spellcasting_modifier(character):
    class_name = character["class"].lower()
    ability = SPELLCASTING_ABILITIES.get(class_name)
    if ability and ability in character:
        return (character[ability] - 10) // 2
    return 0  # fallback for non-casters or missing data


def get_spells_json(filename="spells.json"):
    """Get spells from JSON file"""
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def get_characters_json(filename="characters.json"):
    """Get characters from JSON file"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def select_character(characters):
    """Select a character from the list"""
    if not characters:
        print("No characters found in characters.json")
        return None

    if len(characters) == 1:
        return characters[0]

    print("Available characters:")
    for i, char in enumerate(characters, 1):
        print(f"{i}. {char['name']} ({char['class']} {char['level']})")

    while True:
        try:
            choice = input("Select character (number): ")
            index = int(choice) - 1
            if 0 <= index < len(characters):
                return characters[index]
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")


spells = get_spells_json()

parser = argparse.ArgumentParser(description="Filter D&D Spells")

parser.add_argument("--class", dest="char_class", type=str, help="class")
parser.add_argument("--level", type=int, help="spell level")
parser.add_argument("-nc", "--noncombat", action="store_true", help="non-combat spells")
parser.add_argument(
    "-nc1",
    "--noncombat-minute",
    action="store_true",
    help="1 min cast non-combat spells",
)
parser.add_argument(
    "-c", "--combat", action="store_true", help="combat casting time spells"
)
parser.add_argument("-f", "--file", type=str, help="load character.json")
parser.add_argument("-r", "--range", type=int, help="filter by minimum range in feet")
parser.add_argument(
    "-s",
    "--sort",
    choices=["name", "level", "school", "range"],
    default="name",
    help="sort by name, level, school, or range",
)

args = parser.parse_args()

# Load character data if needed
character = None
if not args.char_class and not args.level:
    # Load characters.json by default if no class/level specified
    characters_file = args.file if args.file else "characters.json"
    characters = get_characters_json(characters_file)
    character = select_character(characters)

    if character:
        args.char_class = character["class"]
        args.level = character["level"]
        spellcasting_mod = get_spellcasting_modifier(character)
        print(
            f"Using character: {character['name']} ({character['class']} {character['level']}, +{spellcasting_mod} spell mod)"
        )
    else:
        print("No character selected. Use --help to see filtering options.")
        sys.exit(0)

display_labels = {
    "casting_time_noncombat": "Casting Time:",
    "casting_time_noncombat_unit": "Casting Time Unit:",
    "casting_time_combat": "Casting Time:",
    "casting_time_combat_unit": "Casting Time Unit:",
    "casting_time_reaction_condition": "Reaction Condition:",
    "range_distance": "Range Distance:",
    "range_units": "Range Units:",
    "range_focus": "Range Focus:",
    "range_string": "Range String:",
    "components_verbal": "Verbal Component:",
    "components_somatic": "Somatic Component:",
    "components_material": "Material Component:",
    "components_material_details": "Material Details:",
    "duration": "Duration:",
    "description": "Description:",
    "at_higher_levels": "At Higher Levels:",
}

display_single_line = {"title", "source", "description", "at_higher_levels"}


def ordinal(n: int) -> str:
    """Get ordinal suffix for a number"""
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def format_range(spell: dict) -> str:
    """Format range for display"""
    range_distance = spell.get("range_distance")
    range_units = spell.get("range_units", "")
    range_focus = spell.get("range_focus")
    range_string = spell.get("range_string", "")

    if range_string:
        # Handle special cases like "Self (10-foot radius)"
        if range_focus == "Self" or range_distance is None or range_distance == 0:
            return f"Self ({range_string})"
        else:
            return range_string
    elif range_focus:
        return range_focus
    elif range_distance is None:
        return "Self"  # Fallback
    elif isinstance(range_distance, str):
        return range_distance
    elif range_distance == 0:
        return "Self"
    else:
        return f"{range_distance} {range_units}"


def get_range_for_sorting(spell: dict) -> int:
    """Get numeric range for sorting purposes"""
    range_distance = spell.get("range_distance")
    range_focus = spell.get("range_focus")

    # Check range_focus first for Self spells
    if range_focus == "Self" or range_distance is None:
        return 0

    # Handle string values in range_distance
    if isinstance(range_distance, str):
        if range_distance.lower() == "touch":
            return 5
        elif range_distance.lower() == "sight":
            return 999998
        elif range_distance.lower() == "special":
            return 999997
        elif range_distance.lower() == "unlimited":
            return 999996
        else:
            # Try to extract a number from the string
            import re

            match = re.search(r"\d+", range_distance)
            if match:
                return int(match.group())
            else:
                return 999995  # Unknown string ranges

    # Handle numeric values
    elif range_distance == 0:
        return 0  # Self
    else:
        return range_distance


def format_title_line(spell: dict, title_width: int, range_width: int) -> str:
    """format title line with alignment"""
    title = spell.get("title", "")
    level = spell.get("level", 0)
    school = spell.get("school", "")
    subschool = spell.get("subschool")
    ritual = spell.get("ritual", False)
    concentration = spell.get("concentration", False)

    if level == 0:
        level_part = f"{school} cantrip"
    else:
        level_part = f"{ordinal(level)} level {school}"

    tags = []
    if subschool:
        tags.append(subschool)
    if ritual:
        tags.append("ritual")
    if concentration:
        tags.append("concentration")

    if tags:
        tag_part = f" ({', '.join(tags)})"
    else:
        tag_part = ""

    padded_title = title.ljust(title_width + 3)
    range_str = format_range(spell)
    padded_range = range_str.ljust(range_width + 3)

    return f"{padded_title}{padded_range}{level_part}{tag_part}"


def format_casting_time(spell: dict) -> str:
    combat_time = spell.get("casting_time_combat")
    combat_unit = spell.get("casting_time_combat_unit")
    noncombat_time = spell.get("casting_time_noncombat")
    noncombat_unit = spell.get("casting_time_noncombat_unit")

    parts = []

    if combat_time is not None and combat_unit:
        parts.append(f"{combat_time} {combat_unit}")
    if noncombat_time is not None and noncombat_unit:
        parts.append(f"{noncombat_time} {noncombat_unit}")

    if not parts:
        return "Casting Time: (none)"

    if len(parts) == 1:
        return f"Casting Time: {parts[0]}"
    else:
        return f"Casting Time: {parts[0]} or {parts[1]}"


def print_field(key: str, spell: dict):
    if key in display_single_line and spell[key]:
        print(f"{display_labels[key]} {spell[key]}")


def class_keys(char_class):
    """class name key format"""
    return [f"class_{char_class.lower()}", f"class_{char_class.lower()}_optional"]


def is_selected(spell):
    """Do we select this spell for inclusion?"""
    if args.char_class:
        keys = class_keys(args.char_class)
        if not any(spell.get(k, False) for k in keys):
            return False
    if args.level:
        level = spell.get("level")
        if level > args.level:
            return False
    if args.range:
        spell_range = get_range_for_sorting(spell)
        if spell_range < args.range:
            return False
    if args.noncombat:
        for nc in ["casting_time_noncombat", "casting_time_noncombat_unit"]:
            if not spell.get(nc):
                return False
    if args.combat:
        for co in ["casting_time_combat", "casting_time_combat_unit"]:
            if not spell.get(co):
                return False
    if args.noncombat_minute:
        time, unit = [
            spell.get("casting_time_noncombat"),
            spell.get("casting_time_noncombat_unit"),
        ]
        if time != 1 or unit != "minute":
            return False
    return True


def sort_spells(filtered_spells, sort_by):
    """Sort spells by the specified criterion"""
    if sort_by == "name":
        return sorted(filtered_spells, key=lambda x: x.get("title", ""))
    elif sort_by == "level":
        return sorted(
            filtered_spells, key=lambda x: (x.get("level", 0), x.get("title", ""))
        )
    elif sort_by == "school":
        return sorted(
            filtered_spells,
            key=lambda x: (x.get("school", ""), x.get("level", 0), x.get("title", "")),
        )
    elif sort_by == "range":
        return sorted(
            filtered_spells,
            key=lambda x: (get_range_for_sorting(x), x.get("title", "")),
        )
    else:
        return filtered_spells


def filter_spells():
    """get list of spells matching filter"""
    filtered_spells = []
    for spell in spells:
        if is_selected(spell):
            filtered_spells.append(spell)
    return sort_spells(filtered_spells, args.sort)


def output_spells(filtered_spells: list):
    """print list of spells"""
    if not filtered_spells:
        print("No spells matched the filters.")
        return

    max_title_length = max(len(spell["title"]) for spell in filtered_spells)
    max_range_length = max(len(format_range(spell)) for spell in filtered_spells)

    for spell in filtered_spells:
        print(format_title_line(spell, max_title_length, max_range_length))

    print(f"\n{len(filtered_spells)} spells matched.")


if __name__ == "__main__":
    filtered_spells_for_printing = filter_spells()
    output_spells(filtered_spells_for_printing)
