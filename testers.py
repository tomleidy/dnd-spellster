import os
from parsers import get_casting_time, get_components


def load_temp_file(filename):
    """ Load text file of sorted and unique examples of text to parse """
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            return file.readlines()
    return []


def run_casting_time_txt():
    """ Iterate over results from file"""
    lines = load_temp_file("casting_times.txt")
    print(f"Testing casting time parsing on {len(lines)} lines")
    for line in lines:
        print(get_casting_time(line))


def run_components_txt():
    """ Iterate over results from file"""
    lines = load_temp_file("components.txt")
    print(f"Testing casting time parsing on {len(lines)} lines")
    for line in lines:
        print(get_components(line))


if __name__ == "__main__":
    run_components_txt()
