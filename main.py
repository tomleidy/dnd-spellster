""" Tool for having class and level relevant spells depending on context """
import sys
import os
import re
import argparse
from typing import List, Tuple
from bs4 import BeautifulSoup

# generate database
# get list of spell:* files
# iterate spell:* html files
# parse each file as html using beautiful soup
# create dictionaries of data from each
#
# div.page-content >
# Text source: p{r"Source: (.+)"} # text it comes from
# School, level/cantrip, ritual, etc.:
# two possibilities for school:
# # p>em{(\w)\w{2}-level (\w+)(?:\s*\((ritual)\))?}
# # # first group should be integer (what about cantrips?)
# # # second group is school of magic (all lower case; function to proper case)
# # # actually, there needs to be a special handler if there are third groups
# # # (because there can be more than one grouping)
# # # though it only seems to be two spells
# <p><em>5th-level divination (ritual) (technomagic)</em></p>
# <p><em>2nd-level conjuration (ritual) (dunamancy)</em></p>
#
# # p>em{(\w+)\s cantrip}
# # # how should cantrips be represented in the database? level -1? 0?
# # # -1 prevents accidental assumption that it's a typical spell
# # # but also leaves room for ambiguity about 0 indexed spells
# # # I think 0 is probably ideal. That seems to be how dnd5e at wikidot does it.

# The next few fields are lumped into a p tag:
# <p><strong>Casting Time:</strong> 1 action<br />
# <strong>Range:</strong> 150 feet<br />
# <strong>Components:</strong> V, S, M (a bit of sponge)<br />
# <strong>Duration:</strong> Instantaneous</p>

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


schools = {
    "abjuration": "Abjuration",
    "conjuration": "Conjuration",
    "divination": "Divination",
    "enchantment": "Enchantment",
    "evocation": "Evocation",
    "illusion": "Illusion",
    "necromancy": "Necromancy",
    "transmutation": "Transmutation",
    "dunamancy": "Dunamancy",
    "dunamancy:chronurgy": "Chronurgy Dunamancy:",
    "dunamancy:graviturgy": "Graviturgy Dunamancy",
    "ritual": "Ritual",
    "technomagic": "Technomagic"
}
REGEX_SCHOOLS = "|".join(schools.keys())
REGEX_EXTRA = r"(?: \(([\w:]+)\))?"
REGEX_ORDINAL = r"(?:st|nd|rd|th)"
print(REGEX_SCHOOLS)

regex_dict = {
    "source": r"^Source: ([\w\W]+)$",
    "level_school": rf"(\d+){REGEX_ORDINAL}-level ([\w]+){REGEX_EXTRA}{REGEX_EXTRA}",
    "school_cantrip": rf"^({REGEX_SCHOOLS})\s+(cantrip){REGEX_EXTRA}{REGEX_EXTRA}",
    "ritual_or_subschool": r"\s\(([\S]+)\)",  # might be more than one, so please iterate
    "casting_time": r"Casting Time: ([\w\s]+)",
    "range": r"Range: ([\w\W]+)<br ?/>",
    "components": r"Components: ",
    "duration_concentration": r"Duration: (Concentration), ([\w\s]+)",
    "duration": r"Duration: ([\w\s]+)",
    "spell_lists": "",
    # might be multiple descriptions, test iterations (make sure they don't match spell list first)
    "descriptions": r"<p>([\w\W]+)</p>",

}


DEBUG = {"result"}


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
    elif level_school_result[1] in schools:
        level = int(level_school_result[0])
        school = schools[level_school_result[1]]  # fix case for school

    ritual = False
    subschool = None
    for x in range(2, 4):  # fix case for extra school stuff
        current_extra = level_school_result[x]
        if current_extra == "ritual":
            ritual = True
        elif current_extra in schools:
            subschool = schools[level_school_result[x]]

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
    html = re.sub(combined, "", html, re.IGNORECASE)
    # print(f"{html=}")
    return html


# def get_


def parse_spell_file(soup: BeautifulSoup) -> dict:
    """ Process an individual spell file """
    if not soup:
        return {}
    spell_data = {}

    # let's trust beautifulsoup to remove these tags cleanly instead of regex.
    unwrap_list = ['em', 'strong', 'a']
    for tag in unwrap_list:
        for element in soup.select(tag):
            element.unwrap()
    regex_title = r"^(.+) - DND 5th Edition"
    title = soup.find("title").get_text()
    title = re.search(regex_title, title)
    if title:
        title = title.group(1)
    page_content = soup.find_all('p')
    # print(get_source(page_content))
    spell_dict = {"title": title}
    for x in page_content:
        str_line = strip_tags(str(x))

        source = get_source(str_line)
        if source:
            spell_dict["source"] = source
        level_school_etc = get_level_and_school_etc(str_line)
        if level_school_etc:
            spell_dict.update(level_school_etc)

    if "result" in DEBUG:
        print(spell_dict)

    return spell_data


if __name__ == "__main__":
    main()
