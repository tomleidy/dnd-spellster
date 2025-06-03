""" Functions to help examine what the parser functions do on files containing all unique examples of various field data """

import os
import sys
from parsers import get_casting_time, get_components, get_duration  # pylint: disable=W0611
from parsers import get_spell_list, get_class_column_name
from patterns import classes_list
from parsers import casting_time_dict_base, range_dict_base, components_dict_base, classes_dict_base

classes_list = [get_class_column_name(pc) for pc in classes_list]


def load_temp_file(filename):
    """ Load text file of sorted and unique examples of text to parse """
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            return file.readlines()
    return []


def run_parser_on_txt_file(parser_func, filename: str) -> None:
    """ Iterate over results from specific file using function"""
    lines = load_temp_file(filename)
    print(f"Test parsing on {len(lines)} lines from {filename}", file=sys.stderr)
    count = 0
    for line in lines:
        result = parser_func(line)
        if result:
            count += 1
        print(result)
    print(f"Finished test parsing: {count} lines parse True", file=sys.stderr)


def count_datapoints(spells) -> None:
    """ Print out count of each type of data """
    keys = ["titles", "sources", "levels", "schools", "subschools", "casting_times",
            "ranges", "components", "durations", "spell_lists", "descriptions"]
    counts = {key: 0 for key in keys}
    casting_time_keys = casting_time_dict_base.keys()
    range_keys = range_dict_base.keys()
    component_keys = components_dict_base.keys()
    classes_keys = classes_dict_base.keys()
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

        if test_for_keys_in_dict(casting_time_keys, spell, "casting time"):
            counts["casting_times"] += 1
        if test_for_keys_in_dict(range_keys, spell, "ranges"):
            counts["ranges"] += 1
        if test_for_keys_in_dict(component_keys, spell, "components"):
            counts["components"] += 1
        if test_for_keys_in_dict(classes_keys, spell, "spell_lists"):
            counts["spell_lists"] += 1

    print(counts)

def test_for_keys_in_dict(keys: list, spell: dict, group: str = ""):
    """ Determine if any key in list is in dictionary and True"""
    for key in keys:
        if key in spell and spell[key]:
            return True
    print(f"{spell['title']} missing in {group}")
    return False

if __name__ == "__main__":
    # run_parser_on_txt_file(get_casting_time, "casting_times.txt")
    run_parser_on_txt_file(get_components, "components.txt")
    # run_parser_on_txt_file(get_duration, "durations.txt")
    #run_parser_on_txt_file(get_spell_list, "spell_lists.txt")
