""" Tool for having class and level relevant spells depending on context """

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
        soup = open_html_file(file_path)
        spell_data = parse_spell_file(soup)
        spells.append(spell_data)
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
    "transmutation": "Transmutation"
}
regex_schools = re.compile("|".join(schools.keys()), re.IGNORECASE)

extra_schools_data = {
    "dunamancy": "Dunamancy",
    "dunamancy:chronurgy": "Chronurgy Dunamancy:",
    "dunamancy:graviturgy": "Graviturgy Dunamancy",
    "ritual": "Ritual",
    "technomagic": "Technomagic"
}
regex_schools_extra = re.compile("|".join(extra_schools_data.keys()), re.IGNORECASE)

REGEX_ORDINAL_SUFFIXES = r"(?:st|nd|rd|th)"


regex_dict = {
    "source": r"^Source: ([\w\W]+)$",
    "level_school_extra_extra": rf"(\d+){REGEX_ORDINAL_SUFFIXES}-level ({regex_schools}) \(({regex_schools_extra})\) \(({regex_schools_extra})\)",
    "level_school_extra": rf"(\d+){REGEX_ORDINAL_SUFFIXES}-level ({regex_schools}) \(({regex_schools_extra})\)",
    "level_school": rf"(\d+){REGEX_ORDINAL_SUFFIXES}-level \(({regex_schools})\)",
    "school_cantrip": r"(\w+)\s cantrip",
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


DEBUG = {}


def get_source(html) -> str:
    """ Parse and return source from HTML """
    result = re.search(regex_dict["source"], html)
    if result:
        result = result.group(1)
        if "source" in DEBUG:
            print(result)
        return result
    return None


def get_level_and_school_etc(html) -> Tuple[str]:
    """ Parse and return school and level from html """
    result = re.search(regex_dict["level_school"], html, re.IGNORECASE)
    if result:
        level = result.group(1)
        school = result.group(2)
        return (level, school)


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

    page_content = soup.find_all('p')
    # print(get_source(page_content))
    spell_dict = {}
    for x in page_content:
        str_line = strip_tags(str(x))

        source = get_source(str_line)
        spell_dict["source"] = source
        print(str_line)

    # print(page_content)

    # spell_data['source'] = re.search(r'Source: (.+)', source).group(1)

    # school_level = soup.select_one('div.page-content p em').get_text(strip=True)
    # match = re.match(r'(\d+)(?:-level)? (\w+)(?: \((ritual)\))?', school_level)
    # if match:
    #     spell_data['level'] = int(match.group(1))
    #     spell_data['school'] = match.group(2).capitalize()
    #     spell_data['ritual'] = bool(match.group(3))

    # # Extract casting time, range, components, duration
    # details = soup.select_one('div.page-content p').get_text(strip=True)
    # details_parts = details.split('\n')
    # for part in details_parts:
    #     if 'Casting Time:' in part:
    #         spell_data['casting_time'] = part.split(':')[1].strip()
    #     elif 'Range:' in part:
    #         spell_data['range'] = part.split(':')[1].strip()
    #     elif 'Components:' in part:
    #         spell_data['components'] = part.split(':')[1].strip()
    #     elif 'Duration:' in part:
    #         spell_data['duration'] = part.split(':')[1].strip()

    # # Extract description
    # description_paragraphs = soup.select('div.page-content p')[1:]
    # spell_data['description'] = ' '.join([p.get_text(strip=True) for p in description_paragraphs])

    # # Extract spell lists
    # spell_lists = soup.select_one('div.page-content p strong em').find_next_siblings('a')
    # spell_data['spell_lists'] = [a.get_text(strip=True) for a in spell_lists]

    return spell_data


if __name__ == "__main__":
    main()
