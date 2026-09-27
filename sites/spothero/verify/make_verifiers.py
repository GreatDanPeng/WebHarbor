#!/usr/bin/env python3
"""make_verifiers.py — generate verify_<N>.py for the 21 spothero tasks.

The centralized ground-truth table below is HARDCODED from the reviewer's
independent first-principles computation (compute_ground_truth.py /
compute_gt_gaps.py over the tracked source_data_*.json snapshots + the frozen
seed DB) and cross-checked against the reviewer's live honest walks on the
review container (wh-spothero-review @ http://localhost:46094, seed md5
482fb61d…). Ground truth lives only here and in the generated verifiers —
never in the agent-facing tasks.jsonl.

Run from sites/spothero/verify/:  python3 make_verifiers.py
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent

# --------------------------------------------------------------- ground truth
# nav: (gate_name, url_regex) — the task-named on-site surfaces.
# ans: (check_name, kind, arg[, arg2]) — kinds: phrase | number | any_number | any
# db:  callable + kwargs — the exact allowed SQLite delta.
GT = {
 0: dict(
   nav=[("search_results", r"/search\?.*search_string=Millennium"),
        ("covered_filter", r"/search\?.*covered=1"),
        ("price_sort", r"/search\?.*sort=price"),
        ("cheapest_facility_page", r"/facility/6075"),
        ("checkout", r"/purchase/hourly\?facility=6075"),
        ("confirmation", r"/purchase/confirmation/SH-")],
   ans=[("facility_named", "phrase", "475 East Huron"),
        ("star_rating", "number", "4.7"),
        ("height_restriction", "phrase", "6' 10\""),
        ("total", "number", "10.44")],
   db=("check_reservations_delta", dict(
        expect_added=dict(facility_id=6075, kind="hourly", total=10.44,
                          email="saturday.market@example.com",
                          starts="2026-10-03T12:00", ends="2026-10-03T18:00",
                          promo="", user_id=None, status="upcoming"))),
   tables=("reservations",)),
 1: dict(
   nav=[("monthly_landing", r"/parking/monthly-parking"),
        ("chicago_monthly_section", r"/city/monthly/chicago-parking"),
        ("monthly_search", r"/search\?kind=monthly"),
        ("cheapest_facility_page", r"/facility/2348"),
        ("runnerup_facility_page", r"/facility/769"),
        ("checkout", r"/purchase/hourly\?facility=2348&.*kind=monthly"),
        ("confirmation", r"/purchase/confirmation/SH-")],
   ans=[("featured_rate", "number", "13.0"),
        ("facility_named", "phrase", "Traders Garage"),
        ("monthly_rate", "any_number", ["13.0", "13.00"]),
        ("access_hours", "phrase", "24/7"),
        ("runnerup_named", "phrase", "Valet-Assist")],
   db=("check_reservations_delta", dict(
        expect_added=dict(facility_id=2348, kind="monthly", total=13.99,
                          email="new.commuter@example.com",
                          starts="2026-10-01", promo="", user_id=None,
                          status="upcoming"))),
   tables=("reservations",)),
 2: dict(
   nav=[("arena_destination", r"/destination/seattle/climate-pledge-arena-parking"),
        ("tyler_childers_event_search", r"/search\?kind=event&id=1240368"),
        ("jungle_event_search", r"/search\?kind=event&id=1307354"),
        ("event_price_sort", r"/search\?kind=event&id=1240368.*sort=price"),
        ("checkout", r"/purchase/hourly\?facility=164512"),
        ("confirmation", r"/purchase/confirmation/SH-")],
   ans=[("earlier_show", "phrase", "Tyler Childers"),
        ("earlier_window_start", "phrase", "5:30 PM"),
        ("earlier_window_end", "phrase", "11:30 PM"),
        ("jungle_window", "phrase", "6:45 PM"),
        ("garage_named", "phrase", "5 W Harrison"),
        ("walk_time", "phrase", "3 min"),
        ("total", "number", "7.49")],
   db=("check_reservations_delta", dict(
        expect_added=dict(facility_id=164512, kind="event", total=7.49,
                          email="show.night@example.com",
                          starts="2026-10-02T17:30", ends="2026-10-02T23:30",
                          promo="", user_id=None, status="upcoming"))),
   tables=("reservations",)),
 3: dict(
   nav=[("ord_airport_page", r"/airport/chicago-ord-parking|/airport-code/ORD"),
        ("ord_search", r"/search\?kind=airport.*airport=ORD"),
        ("mdw_airport_page", r"/airport/chicago-mdw-parking|/airport-code/MDW"),
        ("mdw_search", r"/search\?kind=airport.*airport=MDW"),
        ("cheaper_lot_page", r"/facility/152325"),
        ("checkout", r"/purchase/hourly\?facility=152325"),
        ("confirmation", r"/purchase/confirmation/SH-")],
   ans=[("winning_airport", "phrase", "O'Hare"),
        ("ord_lot_named", "phrase", "Courtyard by Marriott Wood Dale"),
        ("ord_per_day", "number", "12.00"),
        ("mdw_per_day", "number", "13.00"),
        ("total", "number", "40.00"),
        ("first_step", "phrase", "Enter this location at 900 N Wood Dale Rd")],
   db=("check_reservations_delta", dict(
        expect_added=dict(facility_id=152325, kind="airport", total=40.00,
                          email="ord.flyer@example.com",
                          starts="2026-10-03T12:00", ends="2026-10-06T12:00",
                          promo="", user_id=None, status="upcoming",
                          parking_pass="Monitored by License Plate"))),
   tables=("reservations",)),
 4: dict(
   nav=[("login", r"/auth/login"),
        ("account", r"/account$"),
        ("first_reservation", r"/account/reservations/SH-7K2M4Q"),
        ("second_reservation", r"/account/reservations/SH-9W5XN8"),
        ("payment_methods", r"/account/payment-methods")],
   ans=[("sooner_reservation", "phrase", "SH-7K2M4Q"),
        ("sooner_end", "phrase", "5:00 PM"),
        ("extension_charge", "number", "1.85"),
        ("refund_message", "phrase", "5-10 business days"),
        ("default_card", "phrase", "Visa ending in 4242")],
   db=("check_reservations_delta", dict(
        expect_added=None,
        expect_updated={"SH-7K2M4Q": {"ends": "2026-09-28T19:00",
                                       "subtotal": 16.58, "total": 17.57},
                        "SH-9W5XN8": {"status": "cancelled"}})),
   tables=("reservations",)),
 5: dict(
   nav=[("login", r"/auth/login"),
        ("airport_reservation", r"/account/reservations/SH-6N9WF4"),
        ("ord_airport_page", r"/airport/chicago-ord-parking|/airport-code/ORD"),
        ("ord_search", r"/search\?kind=airport.*airport=ORD"),
        ("booked_lot_page", r"/facility/152325"),
        ("checkout", r"/purchase/hourly\?facility=152325"),
        ("confirmation", r"/purchase/confirmation/SH-")],
   ans=[("refund_message", "phrase", "5-10 business days"),
        ("booked_lot_named", "phrase", "Courtyard by Marriott Wood Dale"),
        ("new_total", "number", "52.00")],
   db=("check_reservations_delta", dict(
        expect_added=dict(facility_id=152325, kind="airport", total=52.00,
                          email="david.k@test.com",
                          starts="2026-10-10T12:00", ends="2026-10-14T12:00",
                          promo="", user_id=4, status="upcoming",
                          parking_pass="Monitored by License Plate"),
        expect_updated={"SH-6N9WF4": {"status": "cancelled"}})),
   tables=("reservations",)),
 6: dict(
   nav=[("promo_advertised", r"/$|/\?"),
        ("search_results", r"/search\?.*search_string=Fenway"),
        ("price_sort", r"/search\?.*sort=price"),
        ("cheapest_facility_page", r"/facility/19224"),
        ("checkout", r"/purchase/hourly\?facility=19224"),
        ("confirmation", r"/purchase/confirmation/SH-")],
   ans=[("promo_code", "phrase", "FIRSTSPOT10"),
        ("discount", "number", "1.71"),
        ("final_total", "number", "16.42")],
   db=("check_reservations_delta", dict(
        expect_added=dict(facility_id=19224, kind="hourly", total=16.42,
                          email="first.timer@example.com",
                          starts="2026-10-03T16:00", ends="2026-10-03T20:00",
                          promo="FIRSTSPOT10", user_id=None,
                          status="upcoming"))),
   tables=("reservations",)),
 7: dict(
   nav=[("search_results", r"/search\?.*search_string=Times"),
        ("covered_filter", r"/search\?.*covered=1"),
        ("price_sort", r"/search\?.*sort=price"),
        ("fitting_garage_page", r"/facility/16130"),
        ("checkout", r"/purchase/hourly\?facility=16130"),
        ("confirmation", r"/purchase/confirmation/SH-")],
   ans=[("garage_named", "phrase", "118 W 44th"),
        ("height_fits_van", "phrase", "7' 1\""),
        ("total", "number", "36.29")],
   db=("check_reservations_delta", dict(
        expect_added=dict(facility_id=16130, kind="hourly", total=36.29,
                          email="van.driver@example.com",
                          starts="2026-10-03T19:00", ends="2026-10-04T00:00",
                          promo="", user_id=None, status="upcoming"))),
   tables=("reservations",)),
 8: dict(
   nav=[("search_results", r"/search\?.*search_string=Millennium"),
        ("first_facility_page", r"/facility/11603"),
        ("second_facility_page", r"/facility/2175"),
        ("checkout", r"/purchase/hourly\?facility=2175"),
        ("confirmation", r"/purchase/confirmation/SH-")],
   ans=[("michigan_plaza_rating", "number", "3.4"),
        ("south_loop_rating", "number", "4.8"),
        ("booked_facility", "phrase", "South Loop Garage"),
        ("total", "number", "17.81")],
   db=("check_reservations_delta", dict(
        expect_added=dict(facility_id=2175, kind="hourly", total=17.81,
                          email="jury.duty@example.com",
                          starts="2026-10-03T12:00", ends="2026-10-03T18:00",
                          promo="", user_id=None, status="upcoming"))),
   tables=("reservations",)),
 9: dict(
   nav=[("faq_page", r"/faq"),
        ("guarantee_page", r"/about/parking-guarantee"),
        ("search_results", r"/search\?.*search_string=Union"),
        ("price_sort", r"/search\?.*sort=price"),
        ("cheapest_facility_page", r"/facility/8467"),
        ("checkout", r"/purchase/hourly\?facility=8467"),
        ("confirmation", r"/purchase/confirmation/SH-")],
   ans=[("cancellation_policy", "phrase", "minute before they begin"),
        ("card_charge_timing", "phrase", "pay and reserve"),
        ("guarantee_promise", "phrase", "money back"),
        ("booked_facility", "phrase", "495 Mission Rock"),
        ("total", "number", "7.88")],
   db=("check_reservations_delta", dict(
        expect_added=dict(facility_id=8467, kind="hourly", total=7.88,
                          email="policy.check@example.com",
                          starts="2026-10-03T09:00", ends="2026-10-03T17:00",
                          promo="", user_id=None, status="upcoming"))),
   tables=("reservations",)),
 10: dict(
   nav=[("chicago_city_page", r"/city/chicago-parking"),
        ("loop_search", r"/search\?.*search_string=the%20Loop|/search\?.*search_string=the\+Loop|/search\?.*search_string=Loop"),
        ("covered_filter", r"/search\?.*covered=1"),
        ("price_sort", r"/search\?.*sort=price"),
        ("cheapest_facility_page", r"/facility/957"),
        ("checkout", r"/purchase/hourly\?facility=957"),
        ("confirmation", r"/purchase/confirmation/SH-")],
   ans=[("commuter_range", "phrase", "$13 - $22.5"),
        ("weekend_range", "phrase", "$14 - $34"),
        ("garage_named", "phrase", "1212 S Michigan"),
        ("height_restriction", "phrase", "6' 3\""),
        ("total", "number", "10.19")],
   db=("check_reservations_delta", dict(
        expect_added=dict(facility_id=957, kind="hourly", total=10.19,
                          email="weekend.fan@example.com",
                          starts="2026-10-03T17:00", ends="2026-10-03T23:00",
                          promo="", user_id=None, status="upcoming"))),
   tables=("reservations",)),
 11: dict(
   nav=[("wrigley_destination", r"/destination/chicago/wrigley-field-parking"),
        ("destination_search", r"/search\?.*search_string=Wrigley|/search\?.*latitude="),
        ("featured_first_facility_page", r"/facility/129876"),
        ("checkout", r"/purchase/hourly\?facility=129876"),
        ("confirmation", r"/purchase/confirmation/SH-")],
   ans=[("featured_first", "phrase", "1075 W Addison"),
        ("suv_height_finding", "any", ["no height restriction",
                                       "no height restriction is listed"]),
        ("first_instruction", "phrase", "Enter this location at 1075 W Addison St"),
        ("total", "number", "66.78")],
   db=("check_reservations_delta", dict(
        expect_added=dict(facility_id=129876, kind="hourly", total=66.78,
                          email="cubs.fan@example.com",
                          starts="2026-10-05T17:00", ends="2026-10-05T23:00",
                          promo="", user_id=None, status="upcoming"))),
   tables=("reservations",)),
 12: dict(
   nav=[("stadium_page", r"/parking/stadium-parking"),
        ("soldier_field_search", r"/search\?.*search_string=Soldier"),
        ("price_sort", r"/search\?.*sort=price"),
        ("cheapest_facility_page", r"/facility/957"),
        ("checkout", r"/purchase/hourly\?facility=957"),
        ("confirmation", r"/purchase/confirmation/SH-")],
   ans=[("nfl_count", "number", "30"),
        ("nhl_count", "number", "31"),
        ("facility_named", "phrase", "1212 S Michigan"),
        ("in_out_finding", "phrase", "not allow"),
        ("total", "number", "10.19")],
   db=("check_reservations_delta", dict(
        expect_added=dict(facility_id=957, kind="hourly", total=10.19,
                          email="bears.tailgate@example.com",
                          starts="2026-10-04T12:00", ends="2026-10-04T18:00",
                          promo="", user_id=None, status="upcoming"))),
   tables=("reservations",)),
 13: dict(
   nav=[("login", r"/auth/login"),
        ("payment_methods", r"/account/payment-methods"),
        ("account", r"/account$")],
   ans=[("new_card", "phrase", "4242"),
        ("card_label", "phrase", "Cubs Season"),
        ("upcoming_reservation", "phrase", "SH-8M4KD3"),
        ("remaining_card", "phrase", "1881")],
   db=("check_payment_methods_delta", dict(
        added_spec=dict(user_id=3, brand="Visa", last4="4242", exp_month=9,
                        exp_year=2029, label="Cubs Season"),
        removed_last4="6742", default_last4="4242")),
   tables=("payment_methods",)),
 14: dict(
   nav=[("login_twice", "COUNT:/auth/login:2"),
        ("profile_twice", "COUNT:/account/profile:2"),
        ("payment_methods", r"/account/payment-methods"),
        ("account", r"/account$")],
   ans=[("plate_updated", "phrase", "WI-BO1180"),
        ("vehicle_updated", "phrase", "Honda CR-V Hybrid"),
        ("default_card", "phrase", "5309"),
        ("past_count", "number", "1")],
   db=("check_profile_delta", dict(
        user_id=2, fields={"license_plate": "WI-BO1180",
                           "vehicle": "Honda CR-V Hybrid"})),
   tables=("users",)),
 15: dict(
   nav=[("login", r"/auth/login"),
        ("millennium_facility_page", r"/facility/5284"),
        ("union_square_search", r"/search\?.*search_string=Union"),
        ("covered_filter", r"/search\?.*covered=1"),
        ("riu_facility_page", r"/facility/6182"),
        ("saved_spots_list", r"/account/favorites")],
   ans=[("spot_millennium", "phrase", "Millennium Park Garage"),
        ("spot_park_millennium", "phrase", "Park Millennium Garage"),
        ("spot_grant_park", "phrase", "Grant Park North"),
        ("spot_riu", "phrase", "280 Beach St"),
        ("price_17", "number", "17.00"),
        ("price_14_97", "number", "14.97"),
        ("price_20", "number", "20.00"),
        ("price_12_07", "number", "12.07")],
   db=("check_favorites_delta", dict(
        user_id=1,
        expect_pairs=[(1, 5284), (1, 104341), (1, 5283), (1, 6182)],
        allow_readd=[(1, 5284)])),
   tables=("favorites",)),
 16: dict(
   nav=[("ord_airport_page", r"/airport/chicago-ord-parking|/airport-code/ORD"),
        ("ord_search", r"/search\?kind=airport.*airport=ORD"),
        ("covered_filter", r"/search\?.*covered=1"),
        ("cheapest_facility_page", r"/facility/106017"),
        ("checkout", r"/purchase/hourly\?facility=106017"),
        ("confirmation", r"/purchase/confirmation/SH-")],
   ans=[("pay_timing_faq", "phrase", "It depends"),
        ("accessible_faq", "phrase", "first-come, first-serve"),
        ("economy_faq", "phrase", "Economy Lots F, G, and H"),
        ("facility_named", "phrase", "Hyatt Regency"),
        ("first_instruction", "phrase", "Enter this location at 9300 W Bryn Mawr"),
        ("total", "number", "82.68"),
        ("pass_type", "phrase", "Scan In/Out")],
   db=("check_reservations_delta", dict(
        expect_added=dict(facility_id=106017, kind="airport", total=82.68,
                          email="ord.trip@example.com",
                          starts="2026-10-03T12:00", ends="2026-10-07T12:00",
                          promo="", user_id=None, status="upcoming",
                          parking_pass="Scan In/Out"))),
   tables=("reservations",)),
 17: dict(
   nav=[("signup", r"/auth/signup"),
        ("account", r"/account$"),
        ("united_center_search", r"/search\?.*search_string=United"),
        ("price_sort", r"/search\?.*sort=price"),
        ("cheapest_facility_page", r"/facility/100339"),
        ("checkout", r"/purchase/hourly\?facility=100339"),
        ("confirmation", r"/purchase/confirmation/SH-")],
   ans=[("account_created", "phrase", "Jordan Reyes"),
        ("facility_named", "phrase", "1850 - 1856 W Walnut"),
        ("total", "number", "11.49")],
   db=("signup_and_reserve", None),
   tables=("users", "reservations")),
 18: dict(
   nav=[("fenway_search", r"/search\?.*search_string=Fenway"),
        ("covered_filter_fenway", r"/search\?.*covered=1.*search_string=Fenway|/search\?.*search_string=Fenway.*covered=1"),
        ("times_square_search", r"/search\?.*search_string=Times"),
        ("covered_filter_tsq", r"/search\?.*covered=1.*search_string=Times|/search\?.*search_string=Times.*covered=1"),
        ("cheaper_facility_page", r"/facility/13153"),
        ("checkout", r"/purchase/hourly\?facility=13153"),
        ("confirmation", r"/purchase/confirmation/SH-")],
   ans=[("fenway_facility", "phrase", "32 Fullerton"),
        ("fenway_price", "number", "21.20"),
        ("tsq_price", "number", "26.59"),
        ("cheaper_city", "phrase", "Boston"),
        ("price_difference", "number", "5.39"),
        ("booked_total", "number", "22.47")],
   db=("check_reservations_delta", dict(
        expect_added=dict(facility_id=13153, kind="hourly", total=22.47,
                          email="city.hopper@example.com",
                          starts="2026-10-03T19:00", ends="2026-10-04T00:00",
                          promo="", user_id=None, status="upcoming"))),
   tables=("reservations",)),
 19: dict(
   nav=[("monthly_search", r"/search\?kind=monthly.*search_string=Denver|/search\?kind=monthly.*Denver"),
        ("cheapest_facility_page", r"/facility/15104|/facility/98430"),
        ("second_facility_page", r"/facility/15104|/facility/98430"),
        ("checkout", r"/purchase/hourly\?facility=15104&.*kind=monthly|/purchase/hourly\?facility=98430&.*kind=monthly"),
        ("confirmation", r"/purchase/confirmation/SH-")],
   ans=[("cheapest_named", "any", ["1536 Cleveland Pl", "437 13th St",
                                     "1248 Delaware St", "1442 Tremont",
                                     "1401 Court Pl", "1424 Tremont"]),
        ("tie_note_or_hours", "phrase", "5.99"),
        ("access_hours", "phrase", "24/7")],
   db=("check_any_new_reservation", dict(
        facility_ids=[15104, 98430, 133999, 161586, 161588, 161660],
        kind="monthly", total=6.98, email="denver.office@example.com",
        starts="2026-11-01")),
   tables=("reservations",)),
 20: dict(
   nav=[("arena_destination", r"/destination/seattle/climate-pledge-arena-parking"),
        ("kraken_event_search", r"/search\?kind=event&id=1391016"),
        ("covered_inout_filters", r"/search\?kind=event&id=1391016.*covered=1.*in_out=1|/search\?kind=event&id=1391016.*in_out=1.*covered=1"),
        ("cheapest_facility_page", r"/facility/22491"),
        ("fees_toggle", r"/search\?kind=event&id=1391016.*fees=1"),
        ("checkout", r"/purchase/hourly\?facility=22491"),
        ("confirmation", r"/purchase/confirmation/SH-")],
   ans=[("parking_window_start", "phrase", "4:00 PM"),
        ("parking_window_end", "phrase", "9:00 PM"),
        ("garage_named", "phrase", "465 Spring St"),
        ("height_restriction", "phrase", "6' 6\""),
        ("first_instruction", "phrase", "Enter this garage at 465 Spring St"),
        ("total_with_fees", "number", "13.11")],
   db=("check_reservations_delta", dict(
        expect_added=dict(facility_id=22491, kind="event", total=13.11,
                          email="kraken.fan@example.com",
                          starts="2026-10-04T16:00", ends="2026-10-04T21:00",
                          promo="", user_id=None, status="upcoming"))),
   tables=("reservations",)),
}

HEADER = '''#!/usr/bin/env python3
"""Deterministic verifier for task {tid} (generated by make_verifiers.py).

Ground truth is frozen from the reviewer's independent computation and live
honest walks on the review container (seed md5 482fb61d…). See
verify/README.md for the contract and task-specific caveats.
"""
import sys

from verify_lib import (Judge, check_package, check_seed_contract,
                        check_visited_path, check_visited_path_count,
                        check_answer_phrase,
                        check_answer_number, check_answer_any_number,
                        check_answer_any, check_only_tables_changed,
                        check_reservations_delta, check_any_new_reservation,
                        check_payment_methods_delta, check_profile_delta,
                        check_favorites_delta, check_new_user, final_answer,
                        run_verifier)

TASK_ID = "{tid}"


def main(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_package(judge, traj, TASK_ID)
    check_seed_contract(judge, initial_db)
{body}
    return judge


if __name__ == "__main__":
    sys.exit(run_verifier(TASK_ID, main))
'''

DB_CALLS = {
    "check_reservations_delta":
        '    check_reservations_delta(judge, initial_db, after_db, answer,\n'
        '                             expect_added={EA!r},\n'
        '                             expect_updated={EU!r})',
    "check_any_new_reservation":
        '    check_any_new_reservation(judge, initial_db, after_db, answer,\n'
        '                              facility_ids={FIDS!r}, kind={KIND!r},\n'
        '                              total={TOTAL!r}, email={EMAIL!r},\n'
        '                              starts={STARTS!r})',
    "check_payment_methods_delta":
        '    check_payment_methods_delta(judge, initial_db, after_db,\n'
        '                                added_spec={ADDED!r},\n'
        '                                removed_last4={REMOVED!r},\n'
        '                                default_last4={DEFAULT!r})',
    "check_profile_delta":
        '    check_profile_delta(judge, initial_db, after_db, user_id={UID!r},\n'
        '                        fields={FIELDS!r})',
    "check_favorites_delta":
        '    check_favorites_delta(judge, initial_db, after_db, user_id={UID!r},\n'
        '                          expect_pairs={PAIRS!r},\n'
        '                          allow_readd={ALLOW!r})',
    "signup_and_reserve":
        '    uid = check_new_user(judge, initial_db, after_db,\n'
        '                        email="jordan.reyes@example.com",\n'
        '                        username="jordan_reyes", first_name="Jordan",\n'
        '                        last_name="Reyes")\n'
        '    check_reservations_delta(judge, initial_db, after_db, answer,\n'
        '                             expect_added=dict(\n'
        '                                 facility_id=100339, kind="hourly",\n'
        '                                 total=11.49,\n'
        '                                 email="jordan.reyes@example.com",\n'
        '                                 starts="2026-10-03T17:00",\n'
        '                                 ends="2026-10-03T23:00", promo="",\n'
        '                                 user_id=uid, status="upcoming"),\n'
        '                             expect_updated=None)',
}


def answer_check_lines(spec):
    lines = []
    for item in spec:
        name, kind = item[0], item[1]
        if kind == "phrase":
            lines.append(f'    check_answer_phrase(judge, answer, "{name}", '
                         f'{item[2]!r})')
        elif kind == "number":
            lines.append(f'    check_answer_number(judge, answer, "{name}", '
                         f'{item[2]!r})')
        elif kind == "any_number":
            lines.append(f'    check_answer_any_number(judge, answer, "{name}", '
                         f'{item[2]!r})')
        elif kind == "any":
            lines.append(f'    check_answer_any(judge, answer, "{name}", '
                         f'{item[2]!r})')
        else:
            raise ValueError(kind)
    return "\n".join(lines)


def db_call(spec):
    kind, kwargs = spec
    if kind == "check_reservations_delta":
        return DB_CALLS[kind].format(EA=kwargs.get("expect_added"),
                                     EU=kwargs.get("expect_updated"))
    if kind == "check_any_new_reservation":
        return DB_CALLS[kind].format(FIDS=kwargs["facility_ids"],
                                     KIND=kwargs["kind"],
                                     TOTAL=kwargs["total"],
                                     EMAIL=kwargs["email"],
                                     STARTS=kwargs["starts"])
    if kind == "check_payment_methods_delta":
        return DB_CALLS[kind].format(ADDED=kwargs["added_spec"],
                                     REMOVED=kwargs["removed_last4"],
                                     DEFAULT=kwargs["default_last4"])
    if kind == "check_profile_delta":
        return DB_CALLS[kind].format(UID=kwargs["user_id"],
                                     FIELDS=kwargs["fields"])
    if kind == "check_favorites_delta":
        return DB_CALLS[kind].format(UID=kwargs["user_id"],
                                     PAIRS=kwargs["expect_pairs"],
                                     ALLOW=kwargs["allow_readd"])
    if kind == "signup_and_reserve":
        return DB_CALLS[kind]
    raise ValueError(kind)


def main():
    for n, spec in sorted(GT.items()):
        tid = f"SpotHero--{n}"
        body_lines = []
        for gate, pattern in spec["nav"]:
            if isinstance(pattern, str) and pattern.startswith("COUNT:"):
                _, pat, cnt = pattern.split(":")
                body_lines.append(f'    check_visited_path_count(judge, traj, "{gate}", '
                                  f'r"{pat}", {cnt})')
            else:
                body_lines.append(f'    check_visited_path(judge, traj, "{gate}", '
                                  f'r"{pattern}")')
        body_lines.append(answer_check_lines(spec["ans"]))
        body_lines.append(db_call(spec["db"]))
        body_lines.append(f'    check_only_tables_changed(judge, initial_db, '
                          f'after_db, {spec["tables"]!r})')
        body = "\n".join(body_lines)
        out = HEADER.format(tid=tid, body=body)
        (OUT / f"verify_{n}.py").write_text(out)
        print(f"wrote verify_{n}.py ({tid})")


if __name__ == "__main__":
    main()
