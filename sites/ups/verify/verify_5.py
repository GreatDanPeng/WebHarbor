#!/usr/bin/env python3
"""Deterministic verifier for ups task UPS--5."""
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
    check_trajectory_identity(judge, traj, "UPS--5")
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    check_visited_path(judge, traj, "nav_ship", r"/ship")
    check_visited_path(judge, traj, "nav_confirm", r"/ship/confirm/1Z5F71X9")
    check_visited_path(judge, traj, "nav_track_new", r"/track\?tracknums?=.*1Z5F71X9")
    check_answer_phrase(judge, answer, "tracking_number", "1z5f71x90370000152")
    check_answer_phrase(judge, answer, "scheduled_delivery", "2026-10-01")
    check_answer_money(judge, answer, "declared_value_charge", 17.00)
    check_answer_phrase(judge, answer, "track_resolves", "label created")
    # DB: exactly one outbound shipment row + its label event; track number must
    # match the row actually created by the wizard run.
    check_only_tables_changed(judge, initial, after, {"shipments", "tracking_events"})
    # DB: exactly one wizard shipment (deterministic serial 7000015 -> 1Z5F71X90370000152)
    check_only_tables_changed(judge, initial, after, {"shipments", "tracking_events"})
    row = after.execute(
        "SELECT tracking_number, to_name, to_city, to_state, to_zip, weight_lb, "
        "packages, signature, scheduled_delivery, status, declared_value, "
        "service_code, direction FROM shipments "
        "WHERE tracking_number='1Z5F71X90370000152'").fetchone()
    if row is None:
        judge.fail("db_shipment_row", "wizard shipment 1Z5F71X90370000152 missing")
    else:
        want = ("1Z5F71X90370000152", "Bay Line Gifts", "San Francisco", "CA",
                "94105", 5.0, 1, "Signature Required", "2026-10-01",
                "Label Created", 950.0, "GND", "outbound")
        bad = [f"{c}={v!r}" for c, v, w in zip(
            ("tracking_number", "to_name", "to_city", "to_state", "to_zip",
             "weight_lb", "packages", "signature", "scheduled_delivery", "status",
             "declared_value", "service_code", "direction"), row, want) if v != w]
        if bad:
            judge.fail("db_shipment_fields", f"mismatches: {bad}")
        else:
            judge.ok("db_shipment_fields", "Bay Line Gifts / 94105 / 5 lb / "
                     "Signature Required / $950 / Label Created / GND outbound")
    tn = "1Z5F71X90370000152"
    if tn.lower() not in answer.lower():
        judge.fail("answer_tracking_number", f"answer lacks {tn}")
    else:
        judge.ok("answer_tracking_number", tn)
    check_rows_added(judge, initial, after, "tracking_events",
                     [(None, 15, 1, "2026-09-28", "—", "Label Created",
                       "New York, NY",
                       "rx:^Shipping information received by UPS",
                       None)], "db_label_event")


if __name__ == "__main__":
    sys.exit(run_verifier("UPS--5", checks))
