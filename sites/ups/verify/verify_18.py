#!/usr/bin/env python3
"""Deterministic verifier for ups task UPS--18."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (Judge, check_answer_absent, check_answer_any,
                        check_answer_count_at_least, check_answer_money,
                        check_answer_number, check_answer_phrase,
                        check_only_tables_changed, check_read_only,
                        check_rows_added, check_rows_changed,
                        check_seed_contract, check_screenshots,
                        check_trajectory_identity, check_visited_any,
                        check_visited_path, final_answer, run_verifier)


def checks(judge, traj, initial, after):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, "UPS--18")
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    check_visited_path(judge, traj, "nav_store_services", r"/store/services")
    check_visited_path(judge, traj, "nav_mailboxes", r"/store/mailboxes")
    check_visited_path(judge, traj, "nav_pack_ship", r"/store/pack-and-ship")
    check_visited_path(judge, traj, "nav_locator", r"/locations\?zip=10001&type=The(%20|\+)UPS(%20|\+)Store")
    check_answer_count_at_least(judge, answer, "instore_services",
                                ["notary", "notarize"], 1)
    check_answer_count_at_least(judge, answer, "instore_services_more",
                                ["passport", "shredding", "design"], 2)
    check_answer_count_at_least(judge, answer, "mailbox_perks",
                                ["we sign for packages", "we accept all carriers",
                                 "receive delivery text alerts", "prevent porch pirates",
                                 "24-hour access"], 3)
    check_answer_phrase(judge, answer, "pack_experts", "certified packing experts")
    # The Pack and Ship page does not state a carrier choice; the carrier-
    # acceptance statement ("We Accept All Carriers") is a Mailboxes-page perk.
    # Defensible freeze: the answer ties carrier acceptance to mailboxes (or
    # states it is not on the Pack and Ship page).
    check_answer_count_at_least(judge, answer, "carrier_choice",
                                ["we accept all carriers", "accept all carriers",
                                 "not on the pack and ship", "not mentioned on the pack",
                                 "not stated on the pack", "mailbox"], 1)
    check_answer_number(judge, answer, "stores_count_10001", "5")
    check_answer_phrase(judge, answer, "closest_store", "337 10th ave")
    check_read_only(judge, initial, after)


if __name__ == "__main__":
    sys.exit(run_verifier("UPS--18", checks))
