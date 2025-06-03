""" Utility for pre-cleaning HTML wikidot templated files """

import argparse
import os
import glob
from typing import List, Iterator
from bs4 import BeautifulSoup, Tag

# pylint: disable=C0116


def write_soup_to_file(filepath, soup: BeautifulSoup) -> None:
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(str(soup))


def decompose_unwanted_tags(soup: BeautifulSoup) -> None:
    unwanted_tags = ['div.content-separator']
    for tag in unwanted_tags:
        for element in soup.select(tag):
            element.decompose()


def unwrap_unwanted_tags(soup: BeautifulSoup) -> None:
    # unwrap tags I don't want
    for tag in ['em', 'strong', 'a', 'br', 'span']:
        for element in soup.select(tag):
            element.unwrap()


def get_desired_contents(soup: BeautifulSoup) -> List[Tag]:
    title = soup.title.extract()
    page_content_div = soup.select_one('#page-content')
    if page_content_div:
        page_content_div = page_content_div.extract()
    return [title, page_content_div]


def get_new_soup_with_only_desired_content(contents: List[Tag]):
    base_html = '<html><head><meta charset="utf-8"></head><body></body></html>'
    soup = BeautifulSoup(base_html, 'html.parser')
    for tag in contents:
        soup.body.append(tag)
    return soup


def find_ascent_to_non_list_element(ul: Tag) -> int:
    depth = 0
    parent = ul
    while parent := parent.find_parent('ul'):
        depth += 1
    return depth


def get_list_of_child_lis(ul: Tag) -> List[Tag]:
    return ul.select('li', recursive=False)


def insert_child_li_after_parent(ul: Tag, extracted_li: List[Tag]) -> None:
    parent = ul.find_parent('li')
    rename = False
    if ul.parent.name != "li":
        parent = ul
        rename = True
    reversed_extracted_li: Iterator[Tag] = reversed(extracted_li)
    for child_li in reversed_extracted_li:
        if rename:
            child_li.name = "p"
            if child_li.text.startswith("PREFIX"):
                child_li.string = child_li.text.replace("PREFIX", "")
        parent.insert_after(child_li)


def add_depth_prefix_to_child_li(ul: Tag) -> None:
    li_list = get_list_of_child_lis(ul)
    depth = find_ascent_to_non_list_element(ul)
    prefixes = {0: "* ", 1: " - ", 2: " -- ", 3: " --> ", 4: " " + ("-" * (depth-1)) + "> "}
    if depth not in prefixes:
        depth = 4
    prefix = prefixes[depth]
    for li in li_list:
        if not li.text.startswith("PREFIX"):
            li.string = "PREFIX" + prefix + li.text.strip()


def get_list_of_ul_sorted_deepest_first(soup: BeautifulSoup) -> List[Tag]:
    ul_list = soup.select('ul')
    ul_list.sort(key=lambda ul: sum(1 for _ in ul.parents if ul.name == 'ul'), reverse=True)
    return ul_list


def collect_li_children(ul: Tag):
    return [li.extract() for li in get_list_of_child_lis(ul)]


def clean_html_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    decompose_unwanted_tags(soup)
    unwrap_unwanted_tags(soup)

    ul_list = get_list_of_ul_sorted_deepest_first(soup)
    for ul in ul_list:
        add_depth_prefix_to_child_li(ul)
        extracted_li = collect_li_children(ul)
        insert_child_li_after_parent(ul, extracted_li)
        ul.decompose()

    contents = get_desired_contents(soup)
    soup = get_new_soup_with_only_desired_content(contents)
    write_soup_to_file(filepath, soup)


parser = argparse.ArgumentParser(description='Clean HTML files.')
parser.add_argument('--pattern', default='spell:*', help='Pattern for files (default: spell:*)')
args = parser.parse_args()


def main():
    pattern = os.path.join('.', args.pattern)
    files = glob.glob(pattern)
    for filepath in files:
        if os.path.isfile(filepath):
            print(f"Processing {filepath}")
            clean_html_file(filepath)


if __name__ == '__main__':
    main()
