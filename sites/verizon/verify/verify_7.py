#!/usr/bin/env python3
"""Deterministic verifier for Verizon--7 (verizon).

Ground truth below is HARDCODED (frozen from the contributor's two
independent strict-caliber Playwright rounds on the r3 fix container
wh-verizon-fix3, seed md5 f2d20153c24b6945fb5203b81d7f1fb6) — never read
from tasks.jsonl. Navigation gates cover ONLY the surfaces the (r3
deepened) task text requires; answer anchors are page-verbatim with
tolerance for equally-honest renderings.
Usage: python3 verify_7.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_confirmation,
    check_answer_count_at_least, check_answer_money, check_answer_number,
    check_answer_number_absent, check_answer_ordered, check_answer_phrase,
    check_answer_regex, check_read_only, check_rows_added, check_rows_changed,
    check_only_tables_changed, check_screenshots, check_seed_contract,
    check_trajectory_identity, check_visited_all, check_visited_any,
    check_visited_path, db_one, final_answer, run_verifier,
)

TASK_ID = "Verizon--7"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)


    # navigation: only the surfaces the task text requires
    check_visited_path(judge, traj, "nav_stores", r"/stores/$")
    check_visited_path(judge, traj, "nav_wa", r"/stores/washington/$")
    check_visited_path(judge, traj, "nav_seattle", r"/stores/washington/seattle/$")
    check_visited_path(judge, traj, "nav_northgate_detail", r"/store/r00000151174/$")
    check_visited_path(judge, traj, "nav_northgate_appt", r"/store/r00000151174/appointment/")
    check_visited_path(judge, traj, "nav_bellevue", r"/stores/washington/bellevue/$")
    check_visited_path(judge, traj, "nav_bellevue_detail", r"/store/r00000328070/$")
    check_visited_path(judge, traj, "nav_tacoma", r"/stores/washington/tacoma/$")
    check_visited_path(judge, traj, "nav_tacoma_detail", r"/store/r00000002096/$")
    check_visited_path(judge, traj, "nav_redmond", r"/stores/washington/redmond/$")
    check_visited_any(judge, traj, "nav_redmond_detail",
        [r"/store/a00000365426/$", r"/store/a00000254827/$"])
    check_visited_path(judge, traj, "nav_everett", r"/stores/washington/everett/$")

    # answer ground truth
    check_answer_number(judge, answer, "seattle_count", 6)
    check_answer_phrase(judge, answer, "company_store", "Seattle Northgate")
    check_answer_phrase(judge, answer, "company_addr", "401 NE Northgate Way")
    check_answer_phrase(judge, answer, "company_phone", "206-367-0687")
    check_answer_phrase(judge, answer, "company_sunday", "10:00 AM 06:00 PM")
    check_answer_regex(judge, answer, "company_appts", r"[Aa]ppointments? accepted|[Ss]chedule an appointment")
    check_answer_phrase(judge, answer, "company_market", "Seattle-Everett")
    check_answer_count_at_least(judge, answer, "appt_topics",
        ["New line & device purchase", "Device trade-in", "Billing & payments",
         "Technical support", "Fios / Home Internet"], 3)
    check_answer_number(judge, answer, "bellevue_count", 2)
    check_answer_phrase(judge, answer, "locker_store", "Bellevue Square")
    check_answer_count_at_least(judge, answer, "locker_services",
        ["Express Pickup Locker", "Appointments accepted", "Express Pickup"], 2)
    check_answer_number(judge, answer, "tacoma_count", 3)
    check_answer_phrase(judge, answer, "tacoma_company_addr", "4009 Tacoma Mall Blvd")
    check_answer_phrase(judge, answer, "tacoma_company_sunday", "10:00 AM 06:00 PM")
    check_answer_number(judge, answer, "redmond_count", 2)
    check_answer_number(judge, answer, "everett_count", 2)
    check_answer_regex(judge, answer, "no_company_store",
        r"[Rr]edmond[^.]{0,120}(no|lacks?|without) (a )?(Verizon )?[Cc]ompany [Ss]tore|no company[- ]owned[^.]{0,120}Redmond")
    check_answer_regex(judge, answer, "everett_company",
        r"Everett[^.]{0,120}(has|Verizon Company Store)|Verizon Company Store — Everett")
    check_answer_count_at_least(judge, answer, "redmond_services",
        ["Express Pickup In-store", "No Fios equipment return"], 2)
    check_answer_number(judge, answer, "wa_total", 55)

    check_read_only(judge, initial, after)


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
