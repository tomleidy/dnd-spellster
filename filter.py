""" Filter utility for spells """
import json
import argparse

def get_spells_json(filename="spells.json"):
    """ Get spells from JSON file"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)
spells = get_spells_json()

parser = argparse.ArgumentParser(description="Filter D&D Spells")

parser.add_argument('--class', dest='char_class', type=str, help='class')
parser.add_argument('--level', type=int, help='spell level')
parser.add_argument('-nc','--noncombat', action='store_true', help='non-combat spells')
parser.add_argument('-nc1','--noncombat-minute', action='store_true', help='1 min cast non-combat spells')
parser.add_argument('-c','--combat', action='store_true', help='combat casting time spells')
parser.add_argument('-f', '--file', type=str, help="load character.json")

args = parser.parse_args()


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
    "at_higher_levels": "At Higher Levels:"
}

display_single_line = { "title", "source", "description", "at_higher_levels"}

# I'd like a function that does "Casting Time: n combat_units", or "Casting Time: n noncombat_units" or if both exist (only one spell, but still): "Casting Time: n combat_units or n noncombat_units", and then aligned to the width of the casting time, I'd like range, but I need to figure out how to explain the distribution of the fields.
# OK, for the spell components, I want them to format as Components: VSM (component material details) if all of them are there (omitting the ones that are absent), followed by an
def ordinal(n: int) -> str:
    """ Get ordinal suffix for a number """
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"


def format_title_line(spell: dict, title_width: int) -> str:
    """ format title line with alignment """
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

    return f"{padded_title}{level_part}{tag_part}"

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



def print_field(key: str, spell:dict):
    if key in display_single_line and spell[key]:
        print(f"{display_labels[key]} {spell[key]}")


def class_keys(char_class):
    """ class name key format """
    return [f'class_{char_class.lower()}', f'class_{char_class.lower()}_optional']

def is_selected(spell):
    """ Do we select this spell for inclusion? """
    if args.char_class:
        keys = class_keys(args.char_class)
        if not any(spell.get(k, False) for k in keys):
            return False
    if args.level:
        level = spell.get('level')
        if level > args.level:
            return False
    if args.noncombat:
        for nc in ['casting_time_noncombat','casting_time_noncombat_unit']:
            if not spell.get(nc):
                return False
    if args.combat:
        for co in ['casting_time_combat','casting_time_combat_unit']:
            if not spell.get(co):
                return False
    if args.noncombat_minute:
        time, unit = [spell.get('casting_time_noncombat'), spell.get('casting_time_noncombat_unit')]
        if time != 1 or unit != "minute":
            return False
    return True

def filter_spells():
    """ get list of spells matching filter """
    filtered_spells = []
    for spell in spells:
        if is_selected(spell):
            filtered_spells.append(spell)
    return filtered_spells

def output_spells(filtered_spells: list):
    """ print list of spells """
    max_title_length = max(len(spell["title"]) for spell in filtered_spells)
    for spell in filtered_spells:
        print(format_title_line(spell,max_title_length))

    print(f"\n{len(filtered_spells)} spells matched.")


if __name__ == "__main__":
    filtered_spells_for_printing = filter_spells()
    output_spells(filtered_spells_for_printing)
