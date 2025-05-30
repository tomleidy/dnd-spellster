import os
import re
from typing import List
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
# # # actually, there needs to be a special handler if there are third groups (because there can be more than one grouping)
# # # though it only seems to be two spells
# <p><em>5th-level divination (ritual) (technomagic)</em></p>
# <p><em>2nd-level conjuration (ritual) (dunamancy)</em></p>
#
# # p>em{(\w+)\s cantrip}
# # # how should cantrips be represented in the database? level -1? 0?
# # # -1 prevents accidental assumption that it's a typical spell, but also leaves room for ambiguity about 0 indexed spells
# # # I think 0 is probably ideal. That seems to be how dnd5e at wikidot does it.

# The next few fields are lumped into a p tag:
# <p><strong>Casting Time:</strong> 1 action<br />
# <strong>Range:</strong> 150 feet<br />
# <strong>Components:</strong> V, S, M (a bit of sponge)<br />
# <strong>Duration:</strong> Instantaneous</p>

# Description:
# <p>You draw the moisture from every creature in a 30-foot cube centered on a point you choose within range. Each creature in that area must make a Constitution saving throw. Constructs and undead aren’t affected, and plants and water elementals make this saving throw with disadvantage. A creature takes 12d8 necrotic damage on a failed save, or half as much damage on a successful one.</p>
# <p>Nonmagical plants in the area that aren’t creatures, such as trees and shrubs, wither and die instantly.</p>

# Spell lists:
# <p><strong><em>Spell Lists.</em></strong> <a href="http://dnd5e.wikidot.com/spells:sorcerer">Sorcerer</a>, <a href="http://dnd5e.wikidot.com/spells:wizard">Wizard</a></p>


# manage character data
# level, max hit points, (current hp?)
# spell slots/levels
# prepared status of spells
# filter out unprepared
# filter by: action type, reaction, bonus action
# filter for concentration / no concentration
# filter for damage, healing, buffing, debuffing
# sort by: range?


def get_list_of_files(directory) -> List[str]:
    pass
