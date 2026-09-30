#!/usr/bin/env python3
"""Emit verify_0.py .. verify_20.py with hardcoded ground truth frozen from
the reviewer's honest live walkthroughs of wh-united-airlines-rereview (seed
md5 3a04d306e9fcb436e598fa07e2740912, re-frozen at r2 from contribution
93a2638f). The generated files are plain
deterministic verifiers committed as-is."""
from pathlib import Path

OUT = Path(__file__).resolve().parent

HEADER = '''#!/usr/bin/env python3
"""Deterministic verifier for {task_id} (united_airlines).

Ground truth below is HARDCODED (frozen from the reviewer's independent
honest walkthroughs of the rereview container wh-united-airlines-rereview,
seed md5 3a04d306e9fcb436e598fa07e2740912, site build 93a2638f) — never read
from tasks.jsonl.
Usage: python3 verify_{n}.py --run_dir DIR [--initial_db P] [--after_db P]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_lib import (
    check_answer_absent, check_answer_any, check_answer_confirmation,
    check_answer_count_at_least, check_answer_money, check_answer_number,
    check_answer_phrase, check_read_only, check_rows_added,
    check_rows_changed, check_only_tables_changed, check_screenshots,
    check_seed_contract, check_trajectory_identity, check_visited_any,
    check_visited_path, final_answer, run_verifier,
)

TASK_ID = "{task_id}"


def run_checks(judge, traj, initial, after):
    check_trajectory_identity(judge, traj, TASK_ID)
    check_screenshots(judge, traj)
    check_seed_contract(judge, initial)
    answer = final_answer(traj)
{body}
if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
'''

BODIES = {}

# ---------------------------------------------------------------- T0
BODIES[0] = '''    # navigation: home booking widget -> ORD-DEN search -> cheapest Economy -> booking chain.
    check_visited_path(judge, traj, "nav_search", r'/flights/search\?.*?origin=ORD.*?destination=DEN.*?depart=2026-10-15')
    check_visited_path(judge, traj, "nav_passengers", r'/booking/passengers')
    check_visited_path(judge, traj, "nav_payment", r'/booking/payment')
    check_visited_path(judge, traj, "nav_confirmation", r'/booking/confirmation/')
    # answer ground truth (deterministic fares from the frozen seed):
    #   UA2803 ECO $210.95 / UA2790 ECO $202.95 / UA1974 ECO $226.95.
    check_answer_phrase(judge, answer, "cheapest_flight", "2790")
    check_answer_money(judge, answer, "cheapest_eco_fare", 202.95)
    # every Economy fare compared must be reported (three fares of that day).
    check_answer_count_at_least(judge, answer, "all_eco_fares_reported",
                                ["210.95", "202.95", "226.95"], 3)
    # confirmation number must match the booking persisted by the run.
    row = after.execute(
        "SELECT confirmation FROM bookings WHERE id=5").fetchone()
    check_answer_confirmation(judge, answer, "confirmation_number",
                              row[0] if row else None)
    check_answer_money(judge, answer, "total_charged", 202.95)
    # DB after-state: exactly one new ECO booking ORD->DEN Oct 15 for Jordan Hayes.
    check_only_tables_changed(judge, initial, after,
                             {"bookings", "booking_legs", "passengers"})
    check_rows_added(judge, initial, after, "bookings",
                    [[None, "rx:^[2-9A-HJ-NP-Z]{6}$", None,
                      "jordan.hayes@example.com", None, "ECO", 1, 0, 0, 0,
                      "4242", "Visa", 202.95, "confirmed", None, None, None,
                      None]], "booking_row")
    check_rows_added(judge, initial, after, "booking_legs",
                    [[None, 5, 10, "2026-10-15", "ECO", 202.95]], "leg_row")
    check_rows_added(judge, initial, after, "passengers",
                    [[None, 5, "Jordan", "Hayes", None, None, None, None,
                      None, None, None]], "pax_row")
'''

# ---------------------------------------------------------------- T1
BODIES[1] = '''    # navigation: CMX-ORD round-trip search, both selections, booking chain.
    check_visited_path(judge, traj, "nav_search", r'/flights/search\?.*?origin=CMX.*?destination=ORD.*?depart=2026-10-14')
    check_visited_path(judge, traj, "nav_return", r'/flights/select-return\?origin=ORD&destination=CMX|/flights/search\?.*?origin=ORD.*?destination=CMX.*?depart=2026-10-21')
    check_visited_path(judge, traj, "nav_passengers", r'/booking/passengers')
    check_visited_path(judge, traj, "nav_confirmation", r'/booking/confirmation/')
    check_answer_phrase(judge, answer, "outbound_flight", "5131")
    check_answer_phrase(judge, answer, "return_flight", "6067")
    row = after.execute("SELECT confirmation FROM bookings WHERE id=5").fetchone()
    check_answer_confirmation(judge, answer, "confirmation_number",
                              row[0] if row else None)
    check_answer_money(judge, answer, "total_charged", 273.90)
    check_only_tables_changed(judge, initial, after,
                             {"bookings", "booking_legs", "passengers"})
    check_rows_added(judge, initial, after, "bookings",
                    [[None, "rx:^[2-9A-HJ-NP-Z]{6}$", None,
                      "dana.reyes@example.com", None, "ECO", 1, 0, 0, 0,
                      "7890", "Mastercard", 273.9, "confirmed", None, None,
                      None, None]], "booking_row")
    check_rows_added(judge, initial, after, "booking_legs",
                    [[None, 5, 3, "2026-10-14", "ECO", 138.95],
                     [None, 5, 28, "2026-10-21", "ECO", 134.95]], "leg_rows")
    check_rows_added(judge, initial, after, "passengers",
                    [[None, 5, "Dana", "Reyes", None, None, None, None,
                      None, None, None]], "pax_row")
'''

# ---------------------------------------------------------------- T2
BODIES[2] = '''    # navigation: sign-in -> award search SFO-ORD Oct 5 -> booking chain.
    check_visited_path(judge, traj, "nav_signin", r'/signin')
    check_visited_path(judge, traj, "nav_search", r'/flights/search\?.*?origin=SFO.*?destination=ORD.*?depart=2026-10-05')
    check_visited_path(judge, traj, "nav_payment", r'/booking/payment')
    check_visited_path(judge, traj, "nav_confirmation", r'/booking/confirmation/')
    # answer ground truth: 42,595 miles redeemed (flight 45 ECO, 100 miles/$).
    check_answer_number(judge, answer, "miles_redeemed", 42595)
    check_answer_number(judge, answer, "balance_after", 25855)
    row = after.execute("SELECT confirmation FROM bookings WHERE id=5").fetchone()
    check_answer_confirmation(judge, answer, "confirmation_number",
                              row[0] if row else None)
    # DB after-state: award booking on alice's account, miles deducted exactly once.
    check_only_tables_changed(judge, initial, after,
                             {"bookings", "booking_legs", "passengers",
                              "users", "activities"})
    check_rows_added(judge, initial, after, "bookings",
                    [[None, "rx:^[2-9A-HJ-NP-Z]{6}$", 1,
                      "alice.j@example.com", None, "ECO", 1, 0, 1, 42595,
                      None, None, 0.0, "confirmed", None, None, None, None]],
                    "award_booking_row")
    check_rows_added(judge, initial, after, "booking_legs",
                    [[None, 5, 45, "2026-10-05", "ECO", 421.69]], "leg_row")
    check_rows_added(judge, initial, after, "passengers",
                    [[None, 5, "Alice", "Johnson", None, None, None,
                      "8511174410", None, None, None]], "pax_row")
    check_rows_changed(judge, initial, after, "users",
                       [[1, "alice.j@example.com", None, "Alice", "Johnson",
                         "8511174410", 25855, None, None, "Premier Silver",
                         None, None, None, None]],
                       "alice_miles_deducted")
    check_rows_added(judge, initial, after, "activities",
                    [[None, 1, None, "rx:^Award travel", "MileagePlus",
                      -42595, None]],
                    "activity_row")
'''

# ---------------------------------------------------------------- T3
BODIES[3] = '''    # navigation: bob signs in, IAD-DEN Oct 8 Economy Plus search, booking chain.
    check_visited_path(judge, traj, "nav_signin", r'/signin')
    check_visited_path(judge, traj, "nav_search", r'/flights/search\?.*?origin=IAD.*?destination=DEN.*?depart=2026-10-08')
    check_visited_path(judge, traj, "nav_confirmation", r'/booking/confirmation/')
    # answer ground truth: cheapest EPU = UA599 $325.61 (Premier Gold 0.98x).
    check_answer_phrase(judge, answer, "cheapest_flight", "599")
    check_answer_money(judge, answer, "total_charged", 325.61)
    check_answer_number(judge, answer, "miles_credited", 2605)
    row = after.execute("SELECT confirmation FROM bookings WHERE id=5").fetchone()
    check_answer_confirmation(judge, answer, "confirmation_number",
                              row[0] if row else None)
    check_only_tables_changed(judge, initial, after,
                             {"bookings", "booking_legs", "passengers",
                              "users", "activities"})
    check_rows_added(judge, initial, after, "bookings",
                    [[None, "rx:^[2-9A-HJ-NP-Z]{6}$", 2,
                      "bob.m@example.com", None, "EPU", 1, 0, 0, 0,
                      "9010", "Visa", 325.61, "confirmed", None, None, None,
                      None]], "booking_row")
    check_rows_added(judge, initial, after, "booking_legs",
                    [[None, 5, 14, "2026-10-08", "EPU", 325.61]], "leg_row")
    check_rows_added(judge, initial, after, "passengers",
                    [[None, 5, "Robert", "Miller", None, None, None,
                      "5658356101", None, None, None]], "pax_row")
    check_rows_changed(judge, initial, after, "users",
                       [[2, "bob.m@example.com", None, "Bob", "Miller",
                         "5658356101", 145805, 32, 9506, "Premier Gold",
                         None, None, None, None]],
                       "bob_miles_credited")
    check_rows_added(judge, initial, after, "activities",
                    [[None, 2, None, "rx:^Flight credit", "United", 2605, 326]],
                    "activity_row")
'''

# ---------------------------------------------------------------- T4
BODIES[4] = '''    # navigation: status by number UA2855, route status SFO-ORD, 787-8 fleet page.
    check_visited_path(judge, traj, "nav_status_number", r'/flight-status/results\?.*?number=2855')
    check_visited_path(judge, traj, "nav_status_route", r'/flight-status/results\?.*?mode=route.*?origin=SFO.*?destination=ORD')
    check_visited_path(judge, traj, "nav_fleet_78h", r'/travel-info/fleet/78H')
    # answer ground truth: UA2855 SFO 15:30 -> ORD 21:53, Boeing 787-8,
    # Wi-Fi Panasonic, 7 United First/Business rows, 3 Premium Plus rows.
    check_answer_any(judge, answer, "scheduled_departure", ["15:30"])
    check_answer_any(judge, answer, "scheduled_arrival", ["21:53"])
    check_answer_phrase(judge, answer, "aircraft_type", "787-8")
    check_answer_phrase(judge, answer, "wifi_provider", "Panasonic")
    check_answer_number(judge, answer, "polaris_rows", 7)
    check_answer_number(judge, answer, "premium_plus_rows", 3)
    check_read_only(judge, initial, after)
'''

# ---------------------------------------------------------------- T5
BODIES[5] = '''    # navigation: FCO-DEN Oct 19 search comparing all five cabins of UA178.
    check_visited_path(judge, traj, "nav_search", r'/flights/search\?.*?origin=FCO.*?destination=DEN.*?depart=2026-10-19')
    # answer ground truth: UA178 fares BE $538.16 / ECO $689.95 / EPU $855.54
    # / PP $1,621.38 / BUS $2,828.80; cheapest Premium Plus = UA178 on 787-9.
    check_answer_money(judge, answer, "be_fare", 538.16)
    check_answer_money(judge, answer, "eco_fare", 689.95)
    check_answer_money(judge, answer, "epu_fare", 855.54)
    check_answer_money(judge, answer, "pp_fare", 1621.38)
    check_answer_money(judge, answer, "bus_fare", 2828.80)
    check_answer_phrase(judge, answer, "cheapest_pp_flight", "178")
    check_answer_phrase(judge, answer, "aircraft", "787-9")
    check_read_only(judge, initial, after)
'''

# ---------------------------------------------------------------- T6
BODIES[6] = '''    # navigation: My Trips lookup KX42LM, add the next bag, seat map.
    check_visited_path(judge, traj, "nav_mytrips", r'/mytrips')
    check_visited_path(judge, traj, "nav_trip", r'/mytrips/KX42LM')
    check_visited_path(judge, traj, "nav_seatmap", r'/mytrips/KX42LM/seats/1')
    # answer ground truth: Premier Silver = 1 free bag on this trip; the
    # trip already carries one free bag, so the NEXT (second) bag costs $35
    # online — the task (reworded at 93a2638f) asks for "the fee charged for
    # the added bag", an unambiguous $35 anchor; the standard (non-Economy
    # Plus) window/aisle seat is any seat in the 787-8 Economy band, now
    # rows 15-32 (widened from 15-20 by the interior-spec fix).
    check_answer_number(judge, answer, "free_bags", 1)
    check_answer_money(judge, answer, "bag_fee", 35)
    import re as _re
    seat_rx = _re.compile(r'\\b(1[5-9]|2[0-9]|3[0-2])[A-K]\\b')
    if seat_rx.search(answer):
        judge.ok("seat", seat_rx.search(answer).group(0))
    else:
        judge.fail("seat", "answer lacks a standard seat 15A-32K")
    check_only_tables_changed(judge, initial, after, {"baggage_items", "passengers"})
    check_rows_added(judge, initial, after, "baggage_items",
                    [[None, 1, 1, "Checked bag 2", 0, 35.0]], "bag_row")
    check_rows_changed(judge, initial, after, "passengers",
                       [[1, 1, "Alice", "Johnson", None, None, None,
                         "8511174410", "rx:^(1[5-9]|2[0-9]|3[0-2])[A-K]$", 0, ""]],
                       "seat_row")
'''

# ---------------------------------------------------------------- T7
BODIES[7] = '''    # navigation: dave signs in, check-in flow, boarding pass.
    check_visited_path(judge, traj, "nav_signin", r'/signin')
    check_visited_path(judge, traj, "nav_checkin", r'/checkin')
    check_visited_path(judge, traj, "nav_checkin_flow", r'/checkin/HD19RK')
    check_visited_path(judge, traj, "nav_boarding_pass", r'/checkin/HD19RK/boarding-pass')
    # answer ground truth: seat 12A, boarding group Group 1 (Premier Platinum),
    # gate C12, boarding 14:50 (40 min before the 15:30 departure), Boeing 787-8.
    check_answer_phrase(judge, answer, "seat", "12A")
    check_answer_phrase(judge, answer, "boarding_group", "Group 1")
    check_answer_any(judge, answer, "gate", ["C12"])
    check_answer_any(judge, answer, "boarding_time", ["14:50"])
    check_answer_phrase(judge, answer, "aircraft", "787-8")
    check_only_tables_changed(judge, initial, after, {"passengers"})
    check_rows_changed(judge, initial, after, "passengers",
                       [[4, 4, "Dave", "Thomas", None, None, None,
                         "5153868213", "12A", 1, "Group 1"]],
                       "checked_in_row")
'''

# ---------------------------------------------------------------- T8
BODIES[8] = '''    # navigation: bob's trips, trip details, change flow for QT83NB.
    check_visited_path(judge, traj, "nav_mytrips", r'/mytrips')
    check_visited_path(judge, traj, "nav_trip", r'/mytrips/QT83NB')
    check_visited_path(judge, traj, "nav_change", r'/mytrips/QT83NB/change/2')
    # answer ground truth (deepened at 93a2638f to a before/after itinerary
    # comparison): original leg UA2803 departing 14:33 -> 16:31; latest
    # same-day ORD->DEN flight = UA1974 18:17 -> 20:22, fare difference
    # $19.84 (EPU $281.42 vs $261.58), no change fee.
    check_answer_phrase(judge, answer, "original_flight", "2803")
    check_answer_any(judge, answer, "original_departure", ["14:33"])
    check_answer_phrase(judge, answer, "new_flight", "1974")
    check_answer_any(judge, answer, "new_departure", ["18:17"])
    check_answer_money(judge, answer, "fare_difference", 19.84)
    ok_fee = ("no change fee" in answer.lower()) or ("$0" in answer) or ("0" in answer)
    if ok_fee:
        judge.ok("change_fee", "no change fee")
    else:
        judge.fail("change_fee", "answer must state no change fee / $0")
    check_only_tables_changed(judge, initial, after, {"bookings", "booking_legs"})
    check_rows_changed(judge, initial, after, "bookings",
                       [[None, "QT83NB", 2, "bob.m@example.com", None, "EPU",
                         1, 0, 0, 0, "4242", "Visa", 281.42, "confirmed",
                         None, None, None, None]],
                       "booking_total")
    check_rows_changed(judge, initial, after, "booking_legs",
                       [[2, 2, 11, "2026-09-28", "EPU", 281.42]], "leg_changed")
'''

# ---------------------------------------------------------------- T9
BODIES[9] = '''    # navigation: DEN-SLC Oct 16 booking chain, then My Trips cancel flow.
    check_visited_path(judge, traj, "nav_search", r'/flights/search\?.*?origin=DEN.*?destination=SLC.*?depart=2026-10-16')
    check_visited_path(judge, traj, "nav_confirmation", r'/booking/confirmation/')
    check_visited_path(judge, traj, "nav_trip", r'/mytrips/')
    check_visited_path(judge, traj, "nav_cancel", r'/cancel')
    # answer ground truth: ECO $131.95 charged, full refund $131.95 to the
    # original payment method (Visa ...4242).
    row = after.execute("SELECT confirmation FROM bookings WHERE id=5").fetchone()
    check_answer_confirmation(judge, answer, "confirmation_number",
                              row[0] if row else None)
    check_answer_money(judge, answer, "total_paid", 131.95)
    check_answer_money(judge, answer, "refund_amount", 131.95)
    check_answer_any(judge, answer, "refund_destination",
                    ["original payment method", "card", "visa"])
    check_only_tables_changed(judge, initial, after,
                             {"bookings", "booking_legs", "passengers"})
    check_rows_added(judge, initial, after, "bookings",
                    [[None, "rx:^[2-9A-HJ-NP-Z]{6}$", None,
                      "casey.kim@example.com", None, "ECO", 1, 0, 0, 0,
                      "4242", "Visa", 131.95, "canceled", None, 131.95,
                      "card", None]], "booking_row")
    check_rows_added(judge, initial, after, "booking_legs",
                    [[None, 5, 39, "2026-10-16", "ECO", 131.95]], "leg_row")
    check_rows_added(judge, initial, after, "passengers",
                    [[None, 5, "Casey", "Kim", None, None, None, None,
                      None, None, None]], "pax_row")
'''

# ---------------------------------------------------------------- T10
BODIES[10] = '''    # navigation: ZW57PC lookup, cancel flow, Basic Economy change policy page.
    check_visited_path(judge, traj, "nav_mytrips", r'/mytrips')
    check_visited_path(judge, traj, "nav_trip", r'/mytrips/ZW57PC')
    check_visited_path(judge, traj, "nav_cancel", r'/mytrips/ZW57PC/cancel')
    check_visited_path(judge, traj, "nav_policy", r'/travel-info/policies/flight-change')
    # answer ground truth: Basic Economy cannot be changed; the canceled value
    # stays as a future flight credit (ticket $198.08; cash refund $0).
    ok_change = ("cannot be changed" in answer.lower()) or \\
                 ("not changeable" in answer.lower()) or \\
                 ("can't be changed" in answer.lower()) or \\
                 ("cannot change" in answer.lower())
    if ok_change:
        judge.ok("be_change_rule", "Basic Economy cannot be changed")
    else:
        judge.fail("be_change_rule", "answer must state Basic Economy cannot be changed")
    check_answer_phrase(judge, answer, "value_outcome", "credit")
    check_answer_money(judge, answer, "ticket_value", 198.08)
    check_only_tables_changed(judge, initial, after, {"bookings"})
    check_rows_changed(judge, initial, after, "bookings",
                       [[None, "ZW57PC", 3, "carol.w@example.com", None, "BE",
                         1, 0, 0, 0, "4242", "Visa", 198.08, "canceled",
                         None, 0.0, "travel credit", None]],
                       "cancel_row")
'''

# ---------------------------------------------------------------- T11
BODIES[11] = '''    # navigation: the checked bag fee calculator.
    check_visited_path(judge, traj, "nav_calculator", r'/baggage/fee-calculator')
    # answer ground truth (calculator output, frozen):
    #   Member / Economy / ORD-DEN / 2 bags: $35 + $45 = $80 online,
    #   $40 + $50 = $90 at the airport; weight 50 lb.
    #   Premier Gold / United Business / LHR-DEN / 2 bags online: the
    #   calculator prices $35 + $45 = $80 with a free-bags note (Gold in
    #   Economy gets 2 free bags); weight 70 lb. Both the calculator fees
    #   and the free-allowance reading are defensible for scenario 2.
    check_answer_money(judge, answer, "s1_bag1_online", 35)
    check_answer_money(judge, answer, "s1_bag2_online", 45)
    check_answer_money(judge, answer, "s1_online_total", 80)
    check_answer_money(judge, answer, "s1_bag1_airport", 40)
    check_answer_money(judge, answer, "s1_bag2_airport", 50)
    check_answer_money(judge, answer, "s1_airport_total", 90)
    ok_s2 = ("80" in answer) or ("free" in answer.lower()) or ("$0" in answer)
    if ok_s2:
        judge.ok("s2_fees", "$80 calculator price or free-allowance reading")
    else:
        judge.fail("s2_fees", "answer lacks scenario-2 fees ($80 or free)")
    check_answer_number(judge, answer, "member_weight_limit", 50)
    check_answer_number(judge, answer, "gold_weight_limit", 70)
    check_read_only(judge, initial, after)
'''

# ---------------------------------------------------------------- T12
BODIES[12] = '''    # navigation: checked-bags, carry-on rule pages and the fee calculator.
    check_visited_path(judge, traj, "nav_checked", r'/baggage/checked-bags')
    check_visited_path(judge, traj, "nav_carryon", r'/baggage/carry-on')
    check_visited_path(judge, traj, "nav_calculator", r'/baggage/fee-calculator')
    # answer ground truth: 62 total linear inches (30x20x12), Economy 50 lb vs
    # Premier 70 lb, a 60-lb bag is overweight (51-70 lb) at $100, carry-on
    # 23x35x56 cm (9x14x22 in), personal item 22x25x43 cm, Basic Economy
    # domestic includes only a personal item (full carry-on on international);
    # deepened at 93a2638f: three checked bags prepaid online for one United
    # Economy traveler ORD->DEN price at $35 + $45 + $150 = $230 per the fee
    # calculator (weight limit 50 lb per bag).
    check_answer_number(judge, answer, "max_linear_inches", 62)
    check_answer_number(judge, answer, "economy_weight_lb", 50)
    check_answer_number(judge, answer, "premier_weight_lb", 70)
    check_answer_money(judge, answer, "sixty_lb_fee", 100)
    ok_carry = ("23 x 35 x 56" in answer) or ("23x35x56" in answer) or \\
               ("9 x 14 x 22" in answer) or ("9x14x22" in answer) or \\
               ("35 x 56" in answer)
    if ok_carry:
        judge.ok("carryon_size", "23 x 35 x 56 cm / 9 x 14 x 22 in")
    else:
        judge.fail("carryon_size", "answer lacks carry-on size limits")
    ok_personal = ("22 x 25 x 43" in answer) or ("22x25x43" in answer) or \\
                  ("25 x 43" in answer)
    if ok_personal:
        judge.ok("personal_item_size", "22 x 25 x 43 cm")
    else:
        judge.fail("personal_item_size", "answer lacks personal item size")
    ok_be = ("personal item" in answer.lower())
    if ok_be:
        judge.ok("be_carryon", "Basic Economy includes a personal item")
    else:
        judge.fail("be_carryon", "answer lacks the Basic Economy carry-on rule")
    check_answer_money(judge, answer, "calc_bag1_fee", 35)
    check_answer_money(judge, answer, "calc_bag2_fee", 45)
    check_answer_money(judge, answer, "calc_bag3_fee", 150)
    check_answer_money(judge, answer, "calc_3bag_total", 230)
    check_read_only(judge, initial, after)
'''

# ---------------------------------------------------------------- T13
BODIES[13] = '''    # navigation: MileagePlus join, SFO-PDX Oct 9 booking chain.
    check_visited_path(judge, traj, "nav_join", r'/mileageplus/join')
    check_visited_path(judge, traj, "nav_search", r'/flights/search\?.*?origin=SFO.*?destination=PDX.*?depart=2026-10-09')
    check_visited_path(judge, traj, "nav_confirmation", r'/booking/confirmation/')
    # answer ground truth: deterministic MileagePlus number (sha256 of the
    # join email), ECO $172.95, 865 award miles credited (5 miles/$, Member).
    check_answer_number(judge, answer, "mp_number", "1759967178")
    row = after.execute("SELECT confirmation FROM bookings WHERE id=5").fetchone()
    check_answer_confirmation(judge, answer, "confirmation_number",
                              row[0] if row else None)
    check_answer_number(judge, answer, "miles_credited", 865)
    check_only_tables_changed(judge, initial, after,
                             {"users", "activities", "bookings",
                              "booking_legs", "passengers"})
    check_rows_added(judge, initial, after, "users",
                    [[5, "frank.lee@example.com", None, "Frank", "Lee",
                      "1759967178", 865, 1, 173, "Member", None, None,
                      None, None]], "user_row")
    check_rows_added(judge, initial, after, "bookings",
                    [[None, "rx:^[2-9A-HJ-NP-Z]{6}$", 5,
                      "frank.lee@example.com", None, "ECO", 1, 0, 0, 0,
                      "4242", "Visa", 172.95, "confirmed", None, None, None,
                      None]], "booking_row")
    check_rows_added(judge, initial, after, "booking_legs",
                    [[None, 5, 43, "2026-10-09", "ECO", 172.95]], "leg_row")
    check_rows_added(judge, initial, after, "passengers",
                    [[None, 5, "Frank", "Lee", None, None, None,
                      "1759967178", None, None, None]], "pax_row")
    check_rows_added(judge, initial, after, "activities",
                    [[None, 5, None, "rx:^Flight credit", "United", 865, 173]],
                    "activity_row")
'''

# ---------------------------------------------------------------- T14
BODIES[14] = '''    # navigation: carol's account page + MileagePlus program page.
    check_visited_path(judge, traj, "nav_signin", r'/signin')
    check_visited_path(judge, traj, "nav_account", r'/account')
    check_visited_path(judge, traj, "nav_program", r'/mileageplus')
    # answer ground truth: PQF 2 / PQP 640; Premier Silver needs 12 PQF +
    # 4,000 PQP (or 5,000 PQP only) — the account page and the program page
    # state the same thresholds; deepened at 93a2638f: she still needs
    # 10 more PQF and 3,360 more PQP for Silver; Premier 1K earns 11 miles
    # per dollar.
    check_answer_number(judge, answer, "current_pqf", 2)
    check_answer_number(judge, answer, "current_pqp", 640)
    check_answer_number(judge, answer, "silver_pqf", 12)
    check_answer_number(judge, answer, "silver_pqp", 4000)
    check_answer_number(judge, answer, "silver_pqp_only", 5000)
    check_answer_number(judge, answer, "onek_earn_rate", 11)
    check_answer_number(judge, answer, "remaining_pqf", 10)
    check_answer_number(judge, answer, "remaining_pqp", 3360)
    import re as _re
    agree_rx = _re.compile(r'\\b(agree[ds]?|the same|same on both|consistent|'
                            r'match(es|ed)?|identical)\\b', _re.I)
    if agree_rx.search(answer):
        judge.ok("thresholds_agree", agree_rx.search(answer).group(0))
    else:
        judge.fail("thresholds_agree",
                   "answer must state whether the two pages' thresholds agree")
    check_read_only(judge, initial, after)
'''

# ---------------------------------------------------------------- T15
BODIES[15] = '''    # navigation: the four cabin pages + the 787-9 fleet page (Polaris pitch).
    check_visited_path(judge, traj, "nav_be", r'/travel-info/cabins/basic-economy')
    check_visited_path(judge, traj, "nav_epu", r'/travel-info/cabins/economy-plus')
    check_visited_path(judge, traj, "nav_pp", r'/travel-info/cabins/premium-plus')
    check_visited_path(judge, traj, "nav_polaris", r'/travel-info/cabins/united-polaris')
    check_visited_path(judge, traj, "nav_fleet_78p", r'/travel-info/fleet/78P')
    # answer ground truth:
    #   Basic Economy: personal item only domestic; full carry-on on
    #     international routes; no changes permitted.
    #   Economy Plus: from $29 per flight; free at booking for Premier Gold
    #     and above; free at check-in for Premier Silver.
    #   Premium Plus: 2 free checked bags at 70 lb.
    #   Polaris pitch (787-9): 6'6" (198 cm) lie-flat sleeping space.
    ok_be_carry = ("personal item" in answer.lower()) and \\
                  (("international" in answer.lower()) or \\
                   ("canada" in answer.lower()) or \\
                   ("south america" in answer.lower()))
    if ok_be_carry:
        judge.ok("be_carryon_rules", "personal item + international carry-on")
    else:
        judge.fail("be_carryon_rules", "answer lacks the two carry-on rules")
    ok_be_change = ("no changes" in answer.lower()) or \\
                   ("cannot be changed" in answer.lower()) or \\
                   ("not changeable" in answer.lower())
    if ok_be_change:
        judge.ok("be_change_rule", "no changes permitted")
    else:
        judge.fail("be_change_rule", "answer lacks the Basic Economy change rule")
    check_answer_money(judge, answer, "epu_from_price", 29)
    ok_epu_free = ("gold" in answer.lower()) and ("silver" in answer.lower())
    if ok_epu_free:
        judge.ok("epu_free_for", "Gold+ at booking, Silver at check-in")
    else:
        judge.fail("epu_free_for", "answer lacks who gets Economy Plus free")
    check_answer_number(judge, answer, "pp_free_bags", 2)
    check_answer_number(judge, answer, "pp_bag_weight", 70)
    ok_pitch = ("6'6\\"" in answer) or ("198 cm" in answer) or ("198cm" in answer)
    if ok_pitch:
        judge.ok("polaris_pitch", "6'6\\" / 198 cm")
    else:
        judge.fail("polaris_pitch", "answer lacks the Polaris seat pitch")
    check_read_only(judge, initial, after)
'''

# ---------------------------------------------------------------- T16
BODIES[16] = '''    # navigation: both fleet pages.
    check_visited_path(judge, traj, "nav_78p", r'/travel-info/fleet/78P')
    check_visited_path(judge, traj, "nav_77x", r'/travel-info/fleet/77X')
    # answer ground truth (re-frozen at r2 from the 93a2638f site, seed md5
    # 3a04d306...; fleet data):
    #   787-9: total seat rows 37 (12 Polaris / 3 Premium Plus / 5 Economy
    #     Plus / 17 Economy), seats 48 / 21 / 39 / 149, Wi-Fi Panasonic,
    #     cruise 560 mph, wingspan 197 ft 4 in,
    #     engines General Electric GEnx-1B76 x2, thrust 76,100 lbf.
    #   777-300ER: total seat rows 46 (15 / 3 / 7 / 21), seats 60 / 24 / 62 /
    #     204, Wi-Fi Panasonic, cruise 557 mph, wingspan 212 ft 7 in,
    #     engines General Electric GE90-115B x2, thrust 115,300 lbf.
    check_answer_number(judge, answer, "ua789_seat_rows", 37)
    check_answer_number(judge, answer, "ua789_polaris_rows", 12)
    check_answer_number(judge, answer, "ua789_pp_rows", 3)
    check_answer_number(judge, answer, "ua789_epu_rows", 5)
    check_answer_count_at_least(judge, answer, "ua789_seats",
                                ["48", "21", "39", "149"], 4)
    check_answer_phrase(judge, answer, "ua789_wifi", "Panasonic")
    check_answer_number(judge, answer, "ua789_cruise", 560)
    ok_789_wing = ("197 ft 4 in" in answer) or ("197ft4in" in answer.replace(" ", ""))
    if ok_789_wing:
        judge.ok("ua789_wingspan", "197 ft 4 in")
    else:
        judge.fail("ua789_wingspan", "answer lacks the 787-9 wingspan")
    ok_789_eng = ("GEnx" in answer)
    if ok_789_eng:
        judge.ok("ua789_engine", "General Electric GEnx-1B76")
    else:
        judge.fail("ua789_engine", "answer lacks the 787-9 engine")
    check_answer_number(judge, answer, "b77w_seat_rows", 46)
    check_answer_number(judge, answer, "b77w_polaris_rows", 15)
    check_answer_number(judge, answer, "b77w_pp_rows", 3)
    check_answer_number(judge, answer, "b77w_epu_rows", 7)
    check_answer_count_at_least(judge, answer, "b77w_seats",
                                ["60", "24", "62", "204"], 4)
    check_answer_phrase(judge, answer, "b77w_wifi", "Panasonic")
    check_answer_number(judge, answer, "b77w_cruise", 557)
    ok_77w_wing = ("212 ft 7 in" in answer) or ("212ft7in" in answer.replace(" ", ""))
    if ok_77w_wing:
        judge.ok("b77w_wingspan", "212 ft 7 in")
    else:
        judge.fail("b77w_wingspan", "answer lacks the 777-300ER wingspan")
    ok_77w_eng = ("GE90" in answer)
    if ok_77w_eng:
        judge.ok("b77w_engine", "General Electric GE90-115B")
    else:
        judge.fail("b77w_engine", "answer lacks the 777-300ER engine")
    check_answer_number(judge, answer, "b77w_thrust", 115300)
    check_read_only(judge, initial, after)
'''

# ---------------------------------------------------------------- T17
BODIES[17] = '''    # navigation: the four Help Center articles.
    check_visited_path(judge, traj, "nav_checkin_article", r'/help/check-in-online')
    check_visited_path(judge, traj, "nav_sameday_article", r'/help/same-day-change')
    check_visited_path(judge, traj, "nav_award_article", r'/help/change-award')
    check_visited_path(judge, traj, "nav_epu_article", r'/help/economy-plus')
    # answer ground truth: online check-in opens 24 hours before and closes
    # 60 minutes before departure; same-day change up to $75 (free on
    # standby for Premier members); award redeposit after canceling is free
    # (no fee), no-show costs a nonrefundable $125 service fee; the lowest
    # Economy Plus price is $29 per flight. Deepened at 93a2638f: each of
    # the four answers must cite the exact title of its source article.
    check_answer_number(judge, answer, "checkin_open_hours", 24)
    check_answer_number(judge, answer, "checkin_close_minutes", 60)
    check_answer_money(judge, answer, "sameday_fee", 75)
    ok_standby = ("standby" in answer.lower()) and ("premier" in answer.lower())
    if ok_standby:
        judge.ok("standby_free", "free standby for Premier members")
    else:
        judge.fail("standby_free", "answer lacks the free-standby rule")
    ok_redeposit = ("redeposit" in answer.lower() or "deposit" in answer.lower()) and \\
                   (("no fee" in answer.lower()) or ("free" in answer.lower()) or \\
                    ("waived" in answer.lower()))
    if ok_redeposit:
        judge.ok("award_redeposit", "no redeposit fee after canceling")
    else:
        judge.fail("award_redeposit", "answer lacks the redeposit-fee answer")
    check_answer_money(judge, answer, "noshow_fee", 125)
    check_answer_money(judge, answer, "epu_lowest_price", 29)
    check_answer_phrase(judge, answer, "source_article_checkin",
                        "How early can I check in for my flight?")
    check_answer_phrase(judge, answer, "source_article_sameday",
                        "What is the same-day change option?")
    check_answer_phrase(judge, answer, "source_article_award",
                        "Can I get my miles back if I cancel an award flight?")
    check_answer_phrase(judge, answer, "source_article_epu",
                        "What is Economy Plus?")
    check_read_only(judge, initial, after)
'''

# ---------------------------------------------------------------- T18
BODIES[18] = '''    # navigation: EWR-DEN route status, the earliest-arrival fleet page, DEN guide.
    check_visited_path(judge, traj, "nav_status", r'/flight-status/results\?.*?mode=route.*?origin=EWR.*?destination=DEN')
    check_visited_path(judge, traj, "nav_fleet", r'/travel-info/fleet/21N')
    check_visited_path(judge, traj, "nav_airport", r'/travel-info/airports/DEN')
    # answer ground truth: UA1197 16:59->19:34, UA407 18:49->21:18,
    # UA1792 20:59->23:26; earliest arrival UA1197 at 19:34. The duration the
    # status page actually lists for UA 1197 is 3h 01m (the frozen
    # great-circle block time; the naive schedule difference 19:34-16:59 =
    # 2h 35m is also accepted as an honest arithmetic reading),
    # Wi-Fi provider Viasat (A321neo); Denver is a United hub.
    check_answer_count_at_least(judge, answer, "all_three_flights",
                                ["1197", "407", "1792"], 3)
    check_answer_any(judge, answer, "ua1197_times", ["16:59"])
    check_answer_any(judge, answer, "ua1197_arrival", ["19:34"])
    check_answer_any(judge, answer, "ua407_times", ["18:49"])
    check_answer_any(judge, answer, "ua1792_times", ["20:59"])
    ok_aircraft = ("A321neo" in answer) or ("321neo" in answer)
    if ok_aircraft:
        judge.ok("aircraft_of_earliest", "Airbus A321neo")
    else:
        judge.fail("aircraft_of_earliest", "answer lacks the aircraft")
    check_answer_phrase(judge, answer, "earliest_arrival", "1197")
    check_answer_any(judge, answer, "duration", ["3h 01m", "3 hours 1", "2h 35m", "2 hours 35"])
    check_answer_phrase(judge, answer, "wifi_provider", "Viasat")
    ok_hub = ("hub" in answer.lower())
    if ok_hub:
        judge.ok("denver_hub", "Denver is a United hub")
    else:
        judge.fail("denver_hub", "answer must state Denver is a United hub")
    check_read_only(judge, initial, after)
'''

# ---------------------------------------------------------------- T19
BODIES[19] = '''    # navigation: deals page, the SFO-SYD deal, booking chain for Oct 26.
    check_visited_path(judge, traj, "nav_deals", r'/deals')
    check_visited_path(judge, traj, "nav_deal_syd", r'/deals/sfo-to-syd')
    check_visited_path(judge, traj, "nav_search", r'/flights/search\?.*?origin=SFO.*?destination=SYD.*?depart=2026-10-26')
    check_visited_path(judge, traj, "nav_confirmation", r'/booking/confirmation/')
    # answer ground truth: deal from $799, flight UA863, ECO $739.95 charged.
    check_answer_money(judge, answer, "deal_from_price", 799)
    check_answer_phrase(judge, answer, "flight_booked", "863")
    row = after.execute("SELECT confirmation FROM bookings WHERE id=5").fetchone()
    check_answer_confirmation(judge, answer, "confirmation_number",
                              row[0] if row else None)
    check_answer_money(judge, answer, "total_charged", 739.95)
    check_only_tables_changed(judge, initial, after,
                             {"bookings", "booking_legs", "passengers"})
    check_rows_added(judge, initial, after, "bookings",
                    [[None, "rx:^[2-9A-HJ-NP-Z]{6}$", None,
                      "priya.nair@example.com", None, "ECO", 1, 0, 0, 0,
                      "4242", "Visa", 739.95, "confirmed", None, None, None,
                      None]], "booking_row")
    check_rows_added(judge, initial, after, "booking_legs",
                    [[None, 5, 54, "2026-10-26", "ECO", 739.95]], "leg_row")
    check_rows_added(judge, initial, after, "passengers",
                    [[None, 5, "Priya", "Nair", None, None, None, None,
                      None, None, None]], "pax_row")
'''

# ---------------------------------------------------------------- T20
BODIES[20] = '''    # navigation: change policy page, ORD-AUS booking chain, cancel flow.
    check_visited_path(judge, traj, "nav_policy", r'/travel-info/policies/flight-change')
    check_visited_path(judge, traj, "nav_search", r'/flights/search\?.*?origin=ORD.*?destination=AUS.*?depart=2026-10-21')
    check_visited_path(judge, traj, "nav_confirmation", r'/booking/confirmation/')
    check_visited_path(judge, traj, "nav_cancel", r'/cancel')
    # answer ground truth: no change fee on standard United Economy (fare
    # difference only); Basic Economy is not changeable; ORD-AUS ECO $234.95
    # charged then fully refunded to the original payment method.
    ok_fee = ("no change fee" in answer.lower()) or ("$0" in answer) or \\
             ("0 change fee" in answer)
    if ok_fee:
        judge.ok("standard_change_fee", "no change fee")
    else:
        judge.fail("standard_change_fee", "answer must state the no-change-fee rule")
    ok_be = ("basic economy" in answer.lower()) and \\
            (("not changeable" in answer.lower()) or \\
             ("cannot be changed" in answer.lower()) or \\
             ("can't be changed" in answer.lower()))
    if ok_be:
        judge.ok("be_rule", "Basic Economy not changeable")
    else:
        judge.fail("be_rule", "answer lacks the Basic Economy rule")
    row = after.execute("SELECT confirmation FROM bookings WHERE id=5").fetchone()
    check_answer_confirmation(judge, answer, "confirmation_number",
                              row[0] if row else None)
    check_answer_money(judge, answer, "total_charged", 234.95)
    check_answer_money(judge, answer, "refund_amount", 234.95)
    check_answer_any(judge, answer, "refund_destination",
                    ["original payment method", "card", "visa"])
    check_only_tables_changed(judge, initial, after,
                             {"bookings", "booking_legs", "passengers"})
    check_rows_added(judge, initial, after, "bookings",
                    [[None, "rx:^[2-9A-HJ-NP-Z]{6}$", None,
                      "sam.ortiz@example.com", None, "ECO", 1, 0, 0, 0,
                      "4242", "Visa", 234.95, "canceled", None, 234.95,
                      "card", None]], "booking_row")
    check_rows_added(judge, initial, after, "booking_legs",
                    [[None, 5, 48, "2026-10-21", "ECO", 234.95]], "leg_row")
    check_rows_added(judge, initial, after, "passengers",
                    [[None, 5, "Sam", "Ortiz", None, None, None, None,
                      None, None, None]], "pax_row")
'''

for n, body in BODIES.items():
    path = OUT / f"verify_{n}.py"
    path.write_text(HEADER.format(task_id=f"United Airlines--{n}", n=n, body=body),
                    encoding="utf-8")
    print("wrote", path.name)
