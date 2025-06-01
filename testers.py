""" Functions to help examine what the parser functions do on files containing all unique examples of various field data """

import os
from parsers import get_casting_time, get_components, get_duration  # pylint: disable=W0611


def load_temp_file(filename):
    """ Load text file of sorted and unique examples of text to parse """
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            return file.readlines()
    return []


def run_parser_on_txt_file(parser_func, filename: str) -> None:
    """ Iterate over results from specific file using function"""
    lines = load_temp_file(filename)
    print(f"Test parsing on {len(lines)} lines from {filename}")
    for line in lines:
        print(parser_func(line))


if __name__ == "__main__":
    # run_parser_on_txt_file(get_casting_time, "casting_times.txt")
    # run_parser_on_txt_file(get_components, "components.txt")
    run_parser_on_txt_file(get_duration, "durations.txt")
