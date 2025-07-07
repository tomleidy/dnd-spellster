"""Filter utility for spells with damage/healing parsing"""

import json
import argparse
import sys
import re
from typing import Dict, List, Tuple

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


def calculate_dice_average(num_dice: int, die_size: int) -> float:
    """Calculate the average value of XdY dice."""
    return num_dice * (die_size + 1) / 2


def parse_dice_expression(expr: str, spellcasting_mod: int = 0) -> float:
    """
    Parse a dice expression and return its average value.
    Handles patterns like: 4d6, 2d8 + 3, 1d4 + your spellcasting ability modifier
    """
    expr = expr.strip()

    # Replace spellcasting ability modifier references
    expr = re.sub(r"your spellcasting ability modifier", str(spellcasting_mod), expr)
    expr = re.sub(r"spellcasting ability modifier", str(spellcasting_mod), expr)

    # Handle multiplication symbol
    expr = expr.replace("×", "*").replace("\\u00d7", "*")

    total = 0.0

    # Find all dice expressions (XdY)
    dice_pattern = r"(\d+)d(\d+)"
    dice_matches = re.findall(dice_pattern, expr)

    for num_dice_str, die_size_str in dice_matches:
        num_dice = int(num_dice_str)
        die_size = int(die_size_str)
        total += calculate_dice_average(num_dice, die_size)

    # Remove dice expressions from the string to handle remaining modifiers
    expr_no_dice = re.sub(dice_pattern, "", expr)

    # Find numeric modifiers (+ X, - X)
    modifier_pattern = r"([+-])\s*(\d+)"
    modifier_matches = re.findall(modifier_pattern, expr_no_dice)

    for sign, value_str in modifier_matches:
        value = int(value_str)
        if sign == "+":
            total += value
        else:
            total -= value

    return total


def extract_damage_types(text: str) -> List[str]:
    """Extract damage types from spell description."""
    damage_types = [
        "acid",
        "bludgeoning",
        "cold",
        "fire",
        "force",
        "lightning",
        "necrotic",
        "piercing",
        "poison",
        "psychic",
        "radiant",
        "slashing",
        "thunder",
    ]

    found_types = []
    text_lower = text.lower()

    for damage_type in damage_types:
        if damage_type in text_lower:
            found_types.append(damage_type)

    return list(set(found_types))  # Remove duplicates


def find_damage_expressions(text: str) -> List[Tuple[str, str, bool, bool]]:
    """
    Find damage/healing expressions in text.
    Returns list of (expression, context, is_damage, is_ongoing)
    """
    expressions = []

    # Pattern 1: dice + modifiers followed by damage/healing keywords
    pattern1 = r"(\d+d\d+(?:\s*[+\-]\s*(?:\d+|your spellcasting ability modifier))*)\s+([^.]*?(?:damage|hit points|heal))"

    # Pattern 2: "equal to" + dice (for spells like cure wounds)
    pattern2 = (
        r"equal to (\d+d\d+(?:\s*[+\-]\s*(?:\d+|your spellcasting ability modifier))*)"
    )

    # Pattern 3: "regains" + dice + "hit points"
    pattern3 = r"regains.*?(\d+d\d+(?:\s*[+\-]\s*(?:\d+|your spellcasting ability modifier))*)[^.]*?hit points"

    # Check pattern 1
    matches = re.finditer(pattern1, text, re.IGNORECASE)
    for match in matches:
        expr = match.group(1)
        context = match.group(2)

        # Determine if it's damage or healing
        is_damage = "damage" in context.lower()
        is_healing = any(
            word in context.lower() for word in ["hit points", "heal", "regain"]
        )

        # Determine if it's ongoing (happens over multiple turns)
        is_ongoing = any(
            phrase in text.lower()
            for phrase in [
                "at the end of",
                "at the start of",
                "each turn",
                "per turn",
                "each of its turns",
            ]
        )

        expressions.append((expr, context, is_damage, is_ongoing))

    # Check pattern 2 & 3 (healing patterns)
    for pattern in [pattern2, pattern3]:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            expr = match.group(1)
            context = match.group(0)  # Full match as context

            # These patterns are always healing
            is_damage = False
            is_healing = True

            # Determine if it's ongoing
            is_ongoing = any(
                phrase in text.lower()
                for phrase in [
                    "at the end of",
                    "at the start of",
                    "each turn",
                    "per turn",
                    "each of its turns",
                ]
            )

            expressions.append((expr, context, is_damage, is_ongoing))

    return expressions


def parse_spell_damage(description: str, spellcasting_mod: int = 0) -> Dict:
    """
    Parse spell description for damage and healing values.

    Returns dict with:
    - primary_damage: float
    - ongoing_damage: float
    - primary_healing: float
    - ongoing_healing: float
    - total_damage: float
    - total_healing: float
    - damage_types: List[str]
    """
    result = {
        "primary_damage": 0.0,
        "ongoing_damage": 0.0,
        "primary_healing": 0.0,
        "ongoing_healing": 0.0,
        "total_damage": 0.0,
        "total_healing": 0.0,
        "damage_types": [],
    }

    if not description:
        return result

    # Extract damage types
    result["damage_types"] = extract_damage_types(description)

    # Find all damage/healing expressions
    expressions = find_damage_expressions(description)

    for expr, context, is_damage, is_ongoing in expressions:
        value = parse_dice_expression(expr, spellcasting_mod)

        if is_damage:
            if is_ongoing:
                result["ongoing_damage"] += value
            else:
                result["primary_damage"] += value
        else:  # is_healing
            if is_ongoing:
                result["ongoing_healing"] += value
            else:
                result["primary_healing"] += value

    # Calculate totals
    result["total_damage"] = result["primary_damage"] + result["ongoing_damage"]
    result["total_healing"] = result["primary_healing"] + result["ongoing_healing"]

    return result


def format_damage_columns(damage_data: Dict) -> Tuple[str, str, str, str, str, str]:
    """
    Format damage data for display in columns.
    Returns (dmg, ongoing, heal, h_ongoing, total, types)
    """

    def format_value(val: float) -> str:
        return f"{val:.1f}" if val > 0 else "-"

    dmg = format_value(damage_data["primary_damage"])
    ongoing = format_value(damage_data["ongoing_damage"])
    heal = format_value(damage_data["primary_healing"])
    h_ongoing = format_value(damage_data["ongoing_healing"])

    # Total column shows damage OR healing, whichever is higher
    total_dmg = damage_data["total_damage"]
    total_heal = damage_data["total_healing"]

    if total_dmg >= total_heal:
        total = f"-{total_dmg:.1f}" if total_dmg > 0 else "-"
    else:
        total = f"+{total_heal:.1f}" if total_heal > 0 else "-"

    # Format damage types
    types = (
        "/".join(damage_data["damage_types"][:2])
        if damage_data["damage_types"]
        else "-"
    )
    if len(damage_data["damage_types"]) > 2:
        types += "+"

    return dmg, ongoing, heal, h_ongoing, total, types


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


def get_classes_json(filename="classes.json"):
    """Get class data from JSON file"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def get_max_spell_level(character, classes_data):
    """Determine the highest spell level the character can cast"""
    class_name = character["class"]
    char_level = character["level"]

    # Find the class data
    class_info = None
    for class_data in classes_data:
        if class_data["class"].lower() == class_name.lower():
            class_info = class_data
            break

    if not class_info:
        return 0  # Class not found

    # Get the level data
    level_data = class_info["levels"].get(str(char_level))
    if not level_data:
        return 0  # Level not found

    # Check if this class has spell slots
    spell_slots = level_data.get("spell_slots", {})

    # Find the highest spell level with available slots
    max_level = 0
    for slot_level_str in spell_slots.keys():
        try:
            slot_level = int(slot_level_str)
            if spell_slots[slot_level_str] > 0:  # Has at least 1 slot
                max_level = max(max_level, slot_level)
        except ValueError:
            continue  # Skip non-numeric keys

    # If no leveled spell slots but has cantrips, can cast level 0 (cantrips)
    if max_level == 0 and level_data.get("cantrips_known", 0) > 0:
        max_level = 0  # Can cast cantrips
        # But if they have Spellcasting feature and no slots yet, they'll get them soon
        features = level_data.get("features", [])
        if "Spellcasting" in features:
            return 0  # Return 0 to show cantrips only

    return max_level


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
    choices=["name", "level", "school", "range", "damage", "healing"],
    default="name",
    help="sort by name, level, school, range, damage, or healing",
)
parser.add_argument(
    "-u",
    "--unprepared",
    action="store_true",
    help="include unprepared spells (default: prepared only)",
)

args = parser.parse_args()

# Load character data if needed
character = None
spellcasting_mod = 0
classes_data = get_classes_json()

if not args.char_class and not args.level:
    # Load characters.json by default if no class/level specified
    characters_file = args.file if args.file else "characters.json"
    characters = get_characters_json(characters_file)
    character = select_character(characters)

    if character:
        args.char_class = character["class"]

        # Determine max spell level from class progression
        max_spell_level = get_max_spell_level(character, classes_data)
        args.level = max_spell_level

        spellcasting_mod = get_spellcasting_modifier(character)
        print(
            f"Using character: {character['name']} ({character['class']} {character['level']}, +{spellcasting_mod} spell mod, max spell level {max_spell_level})"
        )
    else:
        print("No character selected. Use --help to see filtering options.")
        sys.exit(0)
elif args.char_class and args.level is not None:
    # Manual class/level specified - still check if they can cast spells
    fake_character = {"class": args.char_class, "level": args.level}
    max_spell_level = get_max_spell_level(fake_character, classes_data)

    # Update the level filter to the actual max castable level
    original_level = args.level
    args.level = max_spell_level

    if max_spell_level == -1:
        print(f"Using {args.char_class} level {original_level}: no spellcasting")
    elif max_spell_level == 0:
        print(f"Using {args.char_class} level {original_level}: cantrips only")
    else:
        print(
            f"Using {args.char_class} level {original_level}: max spell level {max_spell_level}"
        )

    if max_spell_level == -1:
        print(f"{args.char_class} level {original_level} cannot cast any spells")
        print("No spells matched the filters.")
        sys.exit(0)
elif args.char_class or args.level is not None:
    print(
        "Both --class and --level must be specified together, or use character selection."
    )
    sys.exit(1)

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


def format_title_line(
    spell: dict,
    title_width: int,
    range_width: int,
    dmg_width: int,
    ongoing_width: int,
    heal_width: int,
    h_ongoing_width: int,
    total_width: int,
    types_width: int,
) -> str:
    """format title line with alignment including damage columns"""
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

    # Parse damage for this spell
    description = spell.get("description", "")
    damage_data = parse_spell_damage(description, spellcasting_mod)
    dmg, ongoing, heal, h_ongoing, total, types = format_damage_columns(damage_data)

    # Format with padding
    padded_title = title.ljust(title_width + 3)
    range_str = format_range(spell)
    padded_range = range_str.ljust(range_width + 3)
    padded_dmg = dmg.ljust(dmg_width + 3)
    padded_ongoing = ongoing.ljust(ongoing_width + 3)
    padded_heal = heal.ljust(heal_width + 3)
    padded_h_ongoing = h_ongoing.ljust(h_ongoing_width + 3)
    padded_total = total.ljust(total_width + 3)
    padded_types = types.ljust(types_width + 3)

    return f"{padded_title}{padded_range}{padded_dmg}{padded_ongoing}{padded_heal}{padded_h_ongoing}{padded_total}{padded_types}{level_part}{tag_part}"


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
        spell_available = any(spell.get(k, False) for k in keys)

        # Also check if it's in the character's extra spells
        if not spell_available and character:
            extra_spells = character.get("extra_spells", [])
            spell_available = spell.get("title") in extra_spells

        if not spell_available:
            return False
    if args.level is not None:
        level = spell.get("level")
        if level > args.level:
            return False
    if args.range:
        spell_range = get_range_for_sorting(spell)
        if spell_range < args.range:
            return False
    # Default to prepared spells only, unless -u flag is used
    if not args.unprepared and character:
        prepared_spells = character.get("prepared_spells", [])
        if spell.get("title") not in prepared_spells:
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


def get_damage_sort_key(spell: dict) -> tuple:
    """Get sorting key for damage: return combined total value for sorting"""
    damage_data = parse_spell_damage(spell.get("description", ""), spellcasting_mod)
    total_damage = damage_data["total_damage"]
    total_healing = damage_data["total_healing"]

    # Return negative damage or positive healing for unified sorting
    if total_damage >= total_healing:
        return (-total_damage, spell.get("title", ""))
    else:
        return (total_healing, spell.get("title", ""))


def get_healing_sort_key(spell: dict) -> tuple:
    """Get sorting key for healing: return combined total value for sorting"""
    damage_data = parse_spell_damage(spell.get("description", ""), spellcasting_mod)
    total_damage = damage_data["total_damage"]
    total_healing = damage_data["total_healing"]

    # Return positive healing or negative damage for unified sorting
    if total_healing >= total_damage:
        return (-total_healing, spell.get("title", ""))
    else:
        return (total_damage, spell.get("title", ""))


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
    elif sort_by == "damage":
        return sorted(filtered_spells, key=get_damage_sort_key)
    elif sort_by == "healing":
        return sorted(filtered_spells, key=get_healing_sort_key)
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

    # Calculate column widths
    max_title_length = max(len(spell["title"]) for spell in filtered_spells)
    max_range_length = max(len(format_range(spell)) for spell in filtered_spells)

    # Calculate damage column widths by processing all spells
    damage_data_list = []
    for spell in filtered_spells:
        description = spell.get("description", "")
        damage_data = parse_spell_damage(description, spellcasting_mod)
        damage_data_list.append(format_damage_columns(damage_data))

    max_dmg_length = max(len(data[0]) for data in damage_data_list)
    max_ongoing_length = max(len(data[1]) for data in damage_data_list)
    max_heal_length = max(len(data[2]) for data in damage_data_list)
    max_h_ongoing_length = max(len(data[3]) for data in damage_data_list)
    max_total_length = max(len(data[4]) for data in damage_data_list)
    max_types_length = max(len(data[5]) for data in damage_data_list)

    # Ensure minimum widths for headers
    max_dmg_length = max(max_dmg_length, 3)  # "Dmg"
    max_ongoing_length = max(max_ongoing_length, 7)  # "Ongoing"
    max_heal_length = max(max_heal_length, 4)  # "Heal"
    max_h_ongoing_length = max(max_h_ongoing_length, 9)  # "H.Ongoing"
    max_total_length = max(max_total_length, 5)  # "Total"
    max_types_length = max(max_types_length, 5)  # "Types"

    # Print header
    header_title = "Spell Name".ljust(max_title_length + 3)
    header_range = "Range".ljust(max_range_length + 3)
    header_dmg = "Dmg".ljust(max_dmg_length + 3)
    header_ongoing = "Ongoing".ljust(max_ongoing_length + 3)
    header_heal = "Heal".ljust(max_heal_length + 3)
    header_h_ongoing = "H.Ongoing".ljust(max_h_ongoing_length + 3)
    header_total = "Total".ljust(max_total_length + 3)
    header_types = "Types".ljust(max_types_length + 3)
    header_level = "Level/School"

    print(
        f"{header_title}{header_range}{header_dmg}{header_ongoing}{header_heal}{header_h_ongoing}{header_total}{header_types}{header_level}"
    )
    print(
        "-"
        * (
            max_title_length
            + max_range_length
            + max_dmg_length
            + max_ongoing_length
            + max_heal_length
            + max_h_ongoing_length
            + max_total_length
            + max_types_length
            + 30
        )
    )

    for spell in filtered_spells:
        print(
            format_title_line(
                spell,
                max_title_length,
                max_range_length,
                max_dmg_length,
                max_ongoing_length,
                max_heal_length,
                max_h_ongoing_length,
                max_total_length,
                max_types_length,
            )
        )

    print(f"\n{len(filtered_spells)} spells matched.")


if __name__ == "__main__":
    filtered_spells_for_printing = filter_spells()
    output_spells(filtered_spells_for_printing)
