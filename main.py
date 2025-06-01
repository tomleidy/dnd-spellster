""" Tool for having class and level relevant spells depending on context """
import sys
import os
import re
import argparse
from typing import List, Tuple
from bs4 import BeautifulSoup
from patterns import regex_dict, schools_dict

# pylint: disable=W0612
# choices {"short", "range", "parse_dict", "casting_time, "level_etc", "stripped_tags"}
DEBUG = {"stripped_tags"}


# generate database
# create dictionaries of data from each

# manage character data
# level, max hit points, (current hp?)
# spell slots/levels
# prepared status of spells
# filter out unprepared
# filter by: action type, reaction, bonus action
# filter for concentration / no concentration
# filter for damage, healing, buffing, debuffing
# sort by: range?


parser = argparse.ArgumentParser(description="Parse D&D 5e spell files.")
parser.add_argument('directory', type=str, help='Directory containing spell HTML files.')


def main():
    """ Main operational part of script """
    args = parser.parse_args()
    directory = args.directory

    spell_files = get_list_of_files(directory)
    spells = []
    for file_path in spell_files:
        try:
            soup = open_html_file(file_path)
            spell_data = parse_spell_file(soup)
            spells.append(spell_data)
            if "short" in DEBUG and len(spells) >= 2:
                sys.exit()
        except KeyboardInterrupt:
            print("\nExiting from Ctrl-C...")
            sys.exit()
    count_datapoints(spells)
#        return

    # for spell in spells:
    #     print(spell)


def get_list_of_files(directory) -> List[str]:
    """ Get list of files in directory and return list """
    if os.path.exists(directory):
        return [os.path.join(directory, f) for f in os.listdir(directory) if f.startswith('spell:')]
    return []


def open_html_file(file_path: str) -> BeautifulSoup:
    """ Open HTML file and return BeautifulSoup parsed document """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return BeautifulSoup(content, 'html.parser')


def parse_action(group) -> dict:
    regex_combat_time = r"(\d+) ([\w\s]+)"

    return


def parse_casting_time_and_units(casting_time_list: List[str]) -> dict:
    """ Parse out _just_ casting times and units"""
    casting_time_dict = dict(casting_time_dict_base)
    regex_parsing_casting_time = r"(?:(\d+) ([\s\S]+)|(\d+) (hours?|minutes?))"
    for time_and_units in casting_time_list:
        re_result = re.search(regex_parsing_casting_time, time_and_units, re.IGNORECASE | re.MULTILINE)
        num_groups = re.compile(regex_parsing_casting_time).groups
        result = [re_result.group(x) for x in range(1, num_groups)]
        tmp_value = None
        for group in result:
            if not group:
                continue
            if not tmp_value and group.isnumeric():
                tmp_value = int(group)
                continue
            group = group.lower()
            if tmp_value and "action" in group:
                if casting_time_dict["casting_time_combat_unit"] is not None:
                    raise RuntimeError("Data has two different action based casting times")
                casting_time_dict["casting_time_combat"] = int(tmp_value)
                casting_time_dict["casting_time_combat_unit"] = group
            elif re.search(r"(hours?|minutes?)", group, flags=re.IGNORECASE | re.MULTILINE):
                if casting_time_dict["casting_time_unit"] is not None:
                    raise RuntimeError("Data has two different (non-combat) casting times")
                casting_time_dict["casting_time"] = int(tmp_value)
                casting_time_dict["casting_time_unit"] = group
            tmp_value = None
    return casting_time_dict


def parse_casting_time_and_conditions(casting_time_string: str) -> dict:
    """ Parse sections of casting time out into dictionary """
    casting_time_dict = {}
    if ", " in casting_time_string:
        casting_time_list = casting_time_string.split(", ")
        casting_time_dict["casting_conditions"] = ", ".join(casting_time_list[1:])
        casting_time_string = casting_time_list[0].strip()
    if " or " in casting_time_string:
        casting_time_list = casting_time_string.split(" or ")
    else:
        casting_time_list = [casting_time_string]
    casting_time_dict.update(parse_casting_time_and_units(casting_time_list))
    return casting_time_dict


def get_casting_time(html) -> str:
    """ Return casting time from HTML """
    result = re.search(regex_dict["casting_time"], html, flags=re.IGNORECASE | re.MULTILINE)
    casting_time_dict = {}
    if not result:
        return None
    if debug_this_spell:
        print("get_casting_time html:", html)
        # print("get_casting_time re.search result:", result)
    result = parse_casting_time_and_conditions(result.group(1))
    casting_time_dict.update(result)
    if "casting_time" in DEBUG and casting_time_dict:
        print("DEBUG get_casting_time:", casting_time_dict)
    return casting_time_dict


def get_source(html) -> str:
    """ Parse and return source from HTML """
    result = re.search(regex_dict["source"], html)
    if result:
        result = result.group(1)
        if "source" in DEBUG:
            print(result)
        return {"source": result}
    return None


def normalize_level_school_result(level_school_result: list) -> list:
    """ Re-organize result to be level (int), school (string), extra1, extra2"""
    if not level_school_result:
        return None
    level = -1
    school = ""
    if level_school_result[1] == 'cantrip':
        level = 0
        school = level_school_result[0]
    elif level_school_result[1] in schools_dict:
        level = int(level_school_result[0])
        school = schools_dict[level_school_result[1]]  # fix case for school

    ritual = False
    subschool = None
    for x in range(2, 4):  # fix case for extra school stuff
        current_extra = level_school_result[x]
        if current_extra == "ritual":
            ritual = True
        elif current_extra in schools_dict:
            subschool = schools_dict[level_school_result[x]]

    if level == -1:
        return None

    return {"level": level, "school": school, "ritual": ritual, "subschool": subschool}


def get_level_and_school_etc(html: str) -> Tuple[str]:
    """ Parse and return school and level from html """
    html = html.lower()
    result_list = []
    result = re.search(regex_dict["level_school"], html, flags=re.IGNORECASE)
    if result:
        for x in range(1, 5):
            result_list.append(result.group(x))
    else:
        result = re.search(regex_dict["school_cantrip"], html, flags=re.IGNORECASE)
        if result:
            for x in range(1, 5):
                result_list.append(result.group(x))
    result_list = normalize_level_school_result(result_list)
    if "level_etc" in DEBUG and result_list:
        print(result_list)
    return result_list


def strip_tags(html) -> str:
    """ Remove <p> and </p> tags from HTML"""
    global DEBUG
    br_tag = r"<br\s*/\s*>"
    p_close = r"</p>"
    p_open = r"<p>"
    combined = rf"{br_tag}|{p_close}|{p_open}"
    html = re.sub(combined, "", html, flags=re.IGNORECASE | re.MULTILINE)
    if "stripped_tags" in DEBUG:
        print(html)
    return html


def get_title(soup) -> str:
    """ Take soup, get title """
    regex_title = r"^(.+) - DND 5th Edition"
    title = soup.find("title").get_text()
    title = re.search(regex_title, title)
    if title:
        title = title.group(1)
    return title


regex_range_dict = {
    "focus_and_shape": r"Self \((\d+)-(([\w]+)[ -]?([\w ]+)\))",
    "descriptive": r"^(Sight|Special|Touch|Unlimited|Self)$",
    "distance_and_units": r"([\d,]+)[- ]?(feet|ft|miles?)"
}

range_dict_base = {"range_distance": None, "range_units": None,
                   "range_focus": None, "range_string": None}


def get_range(html: str) -> dict:
    """ Get range from provided string """
    section = re.search(regex_dict["range"], html, flags=re.IGNORECASE | re.MULTILINE)
    if not section:
        return None
    section = section.group(1)
    range_dict = dict(range_dict_base)
    unit, distance, focus, shape = [None, None, None, None]
    descriptive = re.match(regex_range_dict["descriptive"], section)
    shaped = re.search(regex_range_dict["focus_and_shape"], section)
    vectored = re.search(regex_range_dict["distance_and_units"], section)
    if descriptive:
        if section == "Self":
            focus = "Self"
        else:
            distance = section
    elif shaped:
        distance = int(shaped.group(1).replace(",", ""))
        unit = shaped.group(3)
        shape = f"{distance}-{shaped.group(3)} {shaped.group(4)}"
        focus = "Self"
        range_dict.update({})
    elif vectored:
        distance = int(vectored.group(1).replace(",", ""))
        unit = vectored.group(2)
    if unit in {"foot", "ft"}:
        unit = "feet"
    range_dict.update({"range_distance": distance, "range_units": unit,
                       "range_focus": focus, "range_string": shape
                       })
    if "range" in DEBUG:
        print(range_dict)
    return range_dict


broken_set = {}
unbroken_set = {
    "Nathair's Mischief",
    "Rime's Binding Ice",
    "Mass Polymorph",
    "Summon Draconic Spirit",
    "Draconic Transformation",
    "Antagonize"
}

casting_time_dict_base_list = ['casting_time', 'casting_time_unit', 'casting_time_combat',
                               'casting_time_combat_unit', 'casting_conditions']
casting_time_dict_base = {key: None for key in casting_time_dict_base_list}


def count_datapoints(spells) -> None:
    """ Print out count of each type of data """
    keys = ["titles", "sources", "levels", "schools", "subschools", "casting_times",
            "ranges", "components", "durations", "lists", "descriptions"]
    counts = {key: 0 for key in keys}
    casting_time_keys = casting_time_dict_base.keys()
    range_keys = range_dict_base.keys()
    for spell in spells:

        if spell["title"]:
            counts["titles"] += 1
        if spell["source"]:
            counts["sources"] += 1
        if spell["level"] is not None:
            counts["levels"] += 1
        if spell["school"]:
            counts["schools"] += 1
        if spell["subschool"] is not None:
            counts["subschools"] += 1

        for idx, key in enumerate(casting_time_keys):
            if idx == len(casting_time_keys)-1:
                print(spell)
            if key in spell and spell[key] is not None:
                counts["casting_times"] += 1
                break
        for key in range_keys:
            if key in spell:
                counts["ranges"] += 1
                break

    print(counts)


debug_this_spell = False


def parse_spell_file(soup: BeautifulSoup) -> dict:
    """ Process an individual spell file """
    if not soup:
        return {}

    # let's trust beautifulsoup to remove these tags cleanly instead of regex.
    unwrap_list = ['em', 'strong', 'a', 'br']
    for tag in unwrap_list:
        for element in soup.select(tag):
            element.unwrap()
    page_content = soup.find_all('p')
    global DEBUG
    global debug_this_spell
    # print(get_source(page_content))
    title = get_title(soup)
    if title in broken_set:
        debug_this_spell = True
    else:
        debug_this_spell = False
    spell_dict = {"title": title}
    page_content.insert(0, f"Title: {title}")
    for x in page_content:

        str_line = strip_tags(str(x))
        source = get_source(str_line)
        level_school_etc = get_level_and_school_etc(str_line)
        casting_time = get_casting_time(str_line)
        spell_range = get_range(str_line)

        for result in [source, level_school_etc, casting_time, spell_range]:
            if result:
                spell_dict.update(result)
    if "parse_dict" in DEBUG or debug_this_spell:
        print(spell_dict)
    # print("")
    return spell_dict


if __name__ == "__main__":
    main()
