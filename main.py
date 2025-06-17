"""Tool for having class and level relevant spells depending on context"""

import sys
import os
import re
import json
import argparse
from typing import List
from bs4 import BeautifulSoup
from helpers import santize_string
from helpers import (
    is_source,
    is_level_school_etc,
    is_casting_time,
    does_line_need_splitting,
)
from helpers import (
    is_range,
    is_components,
    is_duration,
    is_spell_list,
    is_at_higher_levels,
)

from parsers import RE_FLAGS
from parsers import (
    get_title,
    get_source,
    get_level_and_school_etc,
    get_casting_time,
    get_range,
    get_at_higher_levels,
)
from parsers import get_components, get_duration, get_spell_list

from testers import count_datapoints

# generate database
# create dictionaries of data from each


parser = argparse.ArgumentParser(description="Parse D&D 5e spell files.")
parser.add_argument(
    "directory", type=str, help="Directory containing spell HTML files."
)
parser.add_argument("-s", "--short", action="store_true", help="Run abridged")

args = parser.parse_args()


def main():
    """Main operational part of script"""
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
    write_json(spells)
    count_datapoints(spells)


def write_json(data: dict, filename: str = "spells.json") -> None:
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def get_list_of_files(directory) -> List[str]:
    """Get list of files in directory and return list"""
    if os.path.exists(directory):
        return [
            os.path.join(directory, f)
            for f in os.listdir(directory)
            if f.startswith("spell:")
        ]
    return []


def open_html_file(file_path: str) -> BeautifulSoup:
    """Open HTML file and return BeautifulSoup parsed document"""
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    return BeautifulSoup(content, "html.parser")


def strip_tags(html) -> str:
    """Remove <p> and </p> tags from HTML"""
    p_close = r"</p>"
    p_open = r"<p>"
    html = re.sub(p_close, "\n", html, RE_FLAGS)
    html = re.sub(p_open, "", html, RE_FLAGS)
    return html.strip()


def parse_spell_file(soup: BeautifulSoup) -> dict:
    """Process an individual spell file"""
    if not soup:
        return {}

    # let's trust beautifulsoup to remove these tags cleanly instead of regex.
    for tag in ["em", "strong", "a", "br"]:
        for element in soup.select(tag):
            element.unwrap()
    page_content = soup.find_all("p")

    spell_dict = {"title": get_title(soup)}
    print(f"\n+++ Adding spell {spell_dict["title"]}")

    for x in page_content:
        str_line = strip_tags(str(x))
        lines = []
        if does_line_need_splitting(str_line):
            print(f"=~= Line needs splitting: {str_line.split("\n")}")
            lines = str_line.split("\n")
        else:
            lines = [str_line]
        for line in lines:
            line = santize_string(line)
            if is_source(line):
                source = get_source(line)
                spell_dict.update(source)
                print(f"=== Updated source for {spell_dict["title"]}: {source}")
            elif is_level_school_etc(line):
                level_etc = get_level_and_school_etc(line)
                spell_dict.update(level_etc)
                print(
                    f"=== Updated level, school, etc., for {spell_dict["title"]}: {level_etc}"
                )
            elif is_casting_time(line):
                casting_time = get_casting_time(line)
                spell_dict.update(casting_time)
                print(
                    f"=== Updated casting time for {spell_dict["title"]}: {casting_time}"
                )
            elif is_range(line):
                range_info = get_range(line)
                spell_dict.update(range_info)
                print(f"=== Updated range for {spell_dict["title"]}: {range_info}")
            elif is_components(line):
                components = get_components(line)
                spell_dict.update(components)
                print(f"=== Updated components for {spell_dict["title"]}: {components}")
            elif is_duration(line):
                duration = get_duration(line)
                spell_dict.update(duration)
                print(f"=== Updated duration for {spell_dict["title"]}: {duration}")
            elif is_spell_list(line):
                spell_list = get_spell_list(line)
                spell_dict.update(spell_list)
                print(f"=== Updated spell list for {spell_dict["title"]}: {spell_list}")
            elif is_at_higher_levels(line):
                spell_list = get_at_higher_levels(line)
                spell_dict.update(spell_list)
            else:
                print(f"\n--- Line needs parsing? {line}")
    return spell_dict


if __name__ == "__main__":
    # run_casting_time_txt()
    main()
