""" Tool for having class and level relevant spells depending on context """
import sys
import os
import re
import argparse
from typing import List, Tuple
from bs4 import BeautifulSoup
from patterns import regex_dict, schools_dict

# pylint: disable=W0612
DEBUG = {"casting time"}

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


def get_casting_time_or(result) -> dict:
    """ Parse out the alternative casting times if there's an or (as of 2025/05/31, only one case, but still)"""


def parse_casting_time(casting_time_string: str) -> dict:
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
    regex_parsing_casting_time = r"(?:(\d+) ([\w\s]+)|(\d+) (hours?|minutes?))"
    for time_and_units in casting_time_list:
        re_result = re.search(regex_parsing_casting_time, time_and_units)
        result = [re_result.group(x) for x in range(1, re.compile(regex_parsing_casting_time).groups)]
        tmp_value = None
        for group in result:
            if not tmp_value and group and group.isnumeric():
                tmp_value = int(group)
                continue
            if tmp_value and "action" in group:
                if "casting_time_combat_unit" in casting_time_dict:
                    raise RuntimeError("Data has two different action based casting times")
                casting_time_dict["casting_time_combat"] = int(tmp_value)
                casting_time_dict["casting_time_combat_unit"] = group.lower()
            elif re.search(r"(hours?|minutes?)", group):
                if "casting_time_unit" in casting_time_dict:
                    raise RuntimeError("Data has two different (non-combat) casting times")
                casting_time_dict["casting_time"] = int(tmp_value)
                casting_time_dict["casting_time_unit"] = group.lower()
            tmp_value = None
    return casting_time_dict


def get_casting_time(html) -> str:
    """ Return casting time from HTML """
    result = re.search(regex_dict["casting_time"], html, flags=re.IGNORECASE | re.MULTILINE)
    casting_time_dict = {}
    if not result:
        return None
    print(result)
    result = parse_casting_time(result.group(1))
    casting_time_dict.update(result)
    if "casting time" in DEBUG and casting_time_dict:
        print(casting_time_dict)
    return casting_time_dict


def get_source(html) -> str:
    """ Parse and return source from HTML """
    result = re.search(regex_dict["source"], html)
    if result:
        result = result.group(1)
        if "source" in DEBUG:
            print(result)
        return result
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


def get_level_and_school_etc(html) -> Tuple[str]:
    """ Parse and return school and level from html """
    result_list = []
    result = re.search(regex_dict["level_school"], html, flags=re.IGNORECASE)
    if result:
        for x in range(1, 5):
            result_list.append(result.group(x))

    if not result:
        result = re.search(regex_dict["school_cantrip"], html, flags=re.IGNORECASE)
        if result:
            for x in range(1, 5):
                result_list.append(result.group(x))
    result_list = normalize_level_school_result(result_list)
    if "level etc" in DEBUG and result_list:
        print(result_list)
    return result_list


def strip_tags(html) -> str:
    """ Remove <p> and </p> tags from HTML"""
    br_tag = r"<br\s*/\s*>"
    p_close = r"</p>"
    p_open = r"<p>"
    combined = rf"{br_tag}|{p_close}|{p_open}"
    html = re.sub(combined, "", html, flags=re.IGNORECASE | re.MULTILINE)
    if "stripped tags" in DEBUG:
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


def parse_spell_file(soup: BeautifulSoup) -> dict:
    """ Process an individual spell file """
    if not soup:
        return {}

    # let's trust beautifulsoup to remove these tags cleanly instead of regex.
    unwrap_list = ['em', 'strong', 'a']
    for tag in unwrap_list:
        for element in soup.select(tag):
            element.unwrap()
    page_content = soup.find_all('p')
    # print(get_source(page_content))
    title = get_title(soup)
    spell_dict = {"title": title}
    # page_content.insert(0, f"Title: {title}")
    for x in page_content:
        str_line = strip_tags(str(x))

        source = get_source(str_line)
        if source:
            spell_dict["source"] = source
        level_school_etc = get_level_and_school_etc(str_line)
        if level_school_etc:
            spell_dict.update(level_school_etc)
        casting_time = get_casting_time(str_line)

    if "parse_dict" in DEBUG:
        print(spell_dict)
    print("")

    return spell_dict


if __name__ == "__main__":
    main()
