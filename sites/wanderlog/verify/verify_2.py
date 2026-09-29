#!/usr/bin/env python3
"""Deterministic verifier for Wanderlog--2 (wanderlog).

Ground truth below is HARDCODED (re-frozen at r3 from the reviewer's independent honest walks on
the r3 review container wh-wanderlog-r3rv, seed md5 b32e9905a17605ce9c983780764c9ee4, with every
hardcoded fact cross-checked against the frozen seed database) —
never read from tasks.jsonl. r3 sync: the task adds a cross-page question point
(the free-attractions list's top two places and BOTH of their descriptions), so
the walk must also open /place/details/1534; the nav_sacre gate and the
free_second/sacre_desc anchors below were asserted live during the reviewer's
walks (two rounds, identical) and match the frozen seed rows exactly.
Usage: python3 verify_2.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_count_at_least,
    check_answer_money, check_answer_number, check_answer_number_absent,
    check_answer_ordered, check_answer_phrase, check_answer_regex,
    check_read_only, check_rows_added, check_rows_changed, check_rows_removed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_all, check_visited_any,
    check_visited_path, final_answer, run_verifier,
)

TASK_ID = "Wanderlog--2"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
    check_visited_path(judge, traj, "nav_search", r"/search\?[^ ]*q=[Ll]ouvre")
    check_visited_path(judge, traj, "nav_louvre", r"/place/details/1529")
    check_visited_path(judge, traj, "nav_attractions", r"/list/geoCategory/104643")
    check_visited_path(judge, traj, "nav_eiffel", r"/place/details/1532")
    check_visited_path(judge, traj, "nav_free", r"/list/geoCategory/129829")
    check_visited_path(judge, traj, "nav_pere", r"/place/details/24882")
    check_visited_path(judge, traj, "nav_sacre", r"/place/details/1534")
    check_visited_path(judge, traj, "nav_restaurants", r"/list/geoCategory/74215")
    check_visited_path(judge, traj, "nav_mokonuts", r"/place/details/115485")
    check_visited_path(judge, traj, "nav_servan", r"/place/details/369538")
    check_answer_phrase(judge, answer, "louvre_about", 'Former historic palace housing huge art collection')
    check_answer_number(judge, answer, "louvre_rank", 3)
    check_answer_phrase(judge, answer, "louvre_rank_cat", 'Attractions')
    check_answer_phrase(judge, answer, "cat1", 'Art museum')
    check_answer_phrase(judge, answer, "cat2", 'Museums')
    check_answer_regex(judge, answer, "coords", r"48\.8606[, ]*2\.3376")
    check_answer_phrase(judge, answer, "list1", 'Top 49 things to do and attractions in Paris')
    check_answer_number(judge, answer, "list1_rank", 2)
    check_answer_phrase(judge, answer, "list2", 'The 49 best free attractions in Paris')
    check_answer_number(judge, answer, "list2_rank", 8)
    check_answer_phrase(judge, answer, "paris_first", 'Eiffel Tower')
    check_answer_phrase(judge, answer, "paris_third", 'Notre-Dame Cathedral of Paris')
    check_answer_phrase(judge, answer, "source_site", 'Travellers Worldwide')
    check_answer_number(judge, answer, "source_pos", 2)
    check_answer_phrase(judge, answer, "eiffel_tip", 'Purchase tickets months in advance from the official website')
    check_answer_phrase(judge, answer, "free_title", 'The 49 best free attractions in Paris')
    check_answer_phrase(judge, answer, "free_top", 'Père-Lachaise')
    check_answer_phrase(judge, answer, "pere_desc", 'Vast tree-lined burial site with famous names including Oscar Wilde, Jim Morrison & Maria Callas')
    check_answer_phrase(judge, answer, "free_second", 'Basilique du Sacré-Cœur de Montmartre')
    check_answer_phrase(judge, answer, "sacre_desc", 'Iconic, domed white church, completed in 1914, with interior mosaics, stained-glass windows & crypt')
    check_answer_phrase(judge, answer, "rest_title", 'Where to eat: the 50 best restaurants in Paris')
    check_answer_number(judge, answer, "rest_count", 50)
    check_answer_phrase(judge, answer, "rest6", 'Mokonuts')
    check_answer_phrase(judge, answer, "mokonuts_cat1", 'Restaurant')
    check_answer_phrase(judge, answer, "mokonuts_cat2", 'French restaurant')
    check_answer_phrase(judge, answer, "rest7", 'Le Servan')
    check_answer_phrase(judge, answer, "servan_desc", 'French-Asian dishes like blood sausage wontons & ginger pork belly, in a space with a vintage vibe')
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
