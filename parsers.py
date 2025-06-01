""" Functions to handle the string parsing """

import re
from typing import Tuple
from patterns import regex_dict, schools_dict, regex_range_dict

casting_time_dict_base_list = ['casting_time_noncombat', 'casting_time_noncombat_unit',
                               'casting_time_combat', 'casting_time_combat_unit',
                               'casting_time_reaction_condition']
casting_time_dict_base = {key: None for key in casting_time_dict_base_list}

range_dict_base = {"range_distance": None, "range_units": None,
                   "range_focus": None, "range_string": None}

RE_FLAGS = re.IGNORECASE | re.MULTILINE


def get_title(soup) -> str:
    """ Take soup, get title """
    regex_title = r"^(.+) - DND 5th Edition"
    title = soup.find("title").get_text()
    title = re.search(regex_title, title)
    if title:
        title = title.group(1)
    return title


def get_source(html) -> str:
    """ Parse and return source from HTML """
    result = re.search(regex_dict["source"], html)
    if result:
        result = result.group(1)
        return {"source": result}
    return {}


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
    return result_list


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


def get_casting_time(html) -> str:
    """ Return casting time from HTML """
    result = re.findall(regex_dict["casting_times_only"], html, RE_FLAGS)
    if not result:
        return None
    casting_time_dict = dict(casting_time_dict_base)
    for group in result:
        if not group:
            continue
        regex_combat = regex_dict["casting_time_combat"]
        regex_noncombat = regex_dict["casting_time_noncombat"]
        combat = re.search(regex_combat, group, RE_FLAGS)
        non_combat = re.search(regex_noncombat, group, RE_FLAGS)
        if combat:
            if casting_time_dict["casting_time_combat"] is not None:
                raise RuntimeError("Data has two combat casting times")
            casting_time_dict.update(get_combat_dict(combat))
        elif non_combat:
            if casting_time_dict["casting_time_noncombat"] is not None:
                raise RuntimeError("Data has two non-combat casting times")
            casting_time_dict.update(get_noncombat_dict(non_combat))
    condition = re.findall(regex_dict["casting_time_reaction_conditions"], html, RE_FLAGS)
    if condition:
        casting_time_dict.update({"casting_time_reaction_condition": condition[0]})
    return casting_time_dict

# TODO: merge the next two functions


def get_noncombat_dict(non_combat):
    """ Return regex data in dictionary form """
    return {"casting_time_noncombat": int(non_combat.group(1)),
            "casting_time_noncombat_unit": non_combat.group(2).lower()
            }


def get_combat_dict(combat):
    """ Return regex data in dictionary form """
    return {"casting_time_combat": int(combat.group(1)),
            "casting_time_combat_unit": combat.group(2).lower()
            }


def get_range(html: str) -> dict:
    """ Get range from provided string """
    section = re.search(regex_dict["range"], html, flags=RE_FLAGS)
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
    return range_dict


components_dict_base = {
    "components_verbal": False,
    "components_somatic": False,
    "components_material": False,
    "components_material_details": None
}


def get_components(html: str) -> dict:
    """ Get components from string """
    components = dict(components_dict_base)
    result = re.search(regex_dict["components"], html, flags=RE_FLAGS)
    for group in result.groups():
        if not group:
            continue
        if re.match(r"[VSM, ]+", group, flags=RE_FLAGS):
            group = re.sub("[ ,]", "", group.upper())
            if "V" in group:
                components["components_verbal"] = True
            if "S" in group:
                components["components_somatic"] = True
            if "M" in group:
                components["components_material"] = True
        else:
            components["components_material_details"] = group
    return components
