""" Tool for having class and level relevant spells depending on context """
import sys
import os
import re
import argparse
from typing import List
from bs4 import BeautifulSoup
from helpers import santize_string
from helpers import is_source, is_level_school_etc, is_casting_time, does_line_need_splitting
from helpers import is_range, is_components
from parsers import RE_FLAGS
from parsers import casting_time_dict_base, range_dict_base
from parsers import get_title, get_source, get_level_and_school_etc, get_casting_time, get_range
from parsers import get_components

# generate database
# create dictionaries of data from each


parser = argparse.ArgumentParser(description="Parse D&D 5e spell files.")
parser.add_argument('directory', type=str, help='Directory containing spell HTML files.')
parser.add_argument('-s', '--short', action="store_true", help="Run abridged")

args = parser.parse_args()


def main():
    """ Main operational part of script """
    directory = args.directory

    spell_files = get_list_of_files(directory)
    spells = []
    for file_path in spell_files:
        try:
            soup = open_html_file(file_path)
            spell_data = parse_spell_file(soup)
            spells.append(spell_data)
            if args.short and len(spells) >= 2:
                sys.exit()
        except KeyboardInterrupt:
            print("\nExiting from Ctrl-C...")
            sys.exit()
    count_datapoints(spells)


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


def strip_tags(html) -> str:
    """ Remove <p> and </p> tags from HTML"""
    p_close = r"</p>"
    p_open = r"<p>"
    html = re.sub(p_close, "\n", html, RE_FLAGS)
    html = re.sub(p_open, "", html, RE_FLAGS)
    return html.strip()


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

        for _, key in enumerate(casting_time_keys):
            if key in spell and spell[key] is not None:
                counts["casting_times"] += 1
                break
        for key in range_keys:
            if key in spell:
                counts["ranges"] += 1
                break

    print(counts)


DEBUG_THIS_SPELL = False
broken_set = {}
unbroken_set = {
    "Nathair's Mischief",
    "Rime's Binding Ice",
    "Mass Polymorph",
    "Summon Draconic Spirit",
    "Draconic Transformation",
    "Antagonize"
}


def parse_spell_file(soup: BeautifulSoup) -> dict:
    """ Process an individual spell file """
    if not soup:
        return {}

    # let's trust beautifulsoup to remove these tags cleanly instead of regex.
    for tag in ['em', 'strong', 'a', 'br']:
        for element in soup.select(tag):
            element.unwrap()
    page_content = soup.find_all('p')

    spell_dict = {"title": get_title(soup)}
    print(f"\n+++ Adding spell {spell_dict["title"]}")

    for x in page_content:
        str_line = strip_tags(str(x))
        if is_source(str_line):
            source = get_source(str_line)
            spell_dict.update(source)
            print(f"=== Updated source for {spell_dict["title"]}: {source}")
        elif is_level_school_etc(str_line):
            level_etc = get_level_and_school_etc(str_line)
            spell_dict.update(level_etc)
            print(f"=== Updated level, school, etc., for {spell_dict["title"]}: {level_etc}")
        elif does_line_need_splitting(str_line):
            print(f"=~= Line needs splitting: {str_line.split("\n")}")
            for line in str_line.split("\n"):
                line = santize_string(line)
                if is_casting_time(line):
                    casting_time = get_casting_time(line)
                    spell_dict.update(casting_time)
                    print(f"=== Updated casting time for {spell_dict["title"]}: {casting_time}")
                elif is_range(line):
                    range_info = get_range(line)
                    spell_dict.update(range_info)
                    print(f"=== Updated range for {spell_dict["title"]}: {range_info}")
                elif is_components(line):
                    components = get_components(line)
                    print(f"=== Updated components for {spell_dict["title"]}: {components}")
                else:
                    print(f"--- Line needs parsing? {line}")
        else:
            print(f"-x- broken with line: {str_line}")

    return spell_dict


if __name__ == "__main__":
    # run_casting_time_txt()
    main()
