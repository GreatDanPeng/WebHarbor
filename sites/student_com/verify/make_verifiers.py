#!/usr/bin/env python3
"""make_verifiers.py — generate sites/student_com/verify/verify_<N>.py from the
frozen per-task spec table (deterministic regeneration; byte-stable output).

Reviewer contract for the 21 student_com tasks (orch/review/student_com).
Ground truth is HARDCODED here and in the generated verifiers — never in
tasks.jsonl. Three tasks (16, 18, 20) are BLOCKED by site defects found during
the review (18 property pages crash with HTTP 500 because upstream room_details
maps room type -> price int and property.html:140 calls .get() on it; the
contact email is never rendered anywhere in the UI). Their verifiers encode the
task's full ground truth and therefore FAIL every run until the contributor
fixes the site — documented in verify/README.md.
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent

RIVE = "the-rive-atlanta-vbqacu"
LITTLEFIELD = "littlefield-hall-kutkl0"
FREEMAN = "freeman-ford-lofts-5bc863"
EIGHTH = "eighth-street-apartments-z0rz15"
KENNY = "kenny-road-apartments-d68a14"
HUB = "hub-on-campus-orlando-4df3abc0"
PARKSIDE = "parkside-dwellings-fex58u"
PARK100 = "100-park-554186"
VILLAS = "villas-on-rio-8639e0"
SOUTHGATE = "southgate-campus-centre-13694141"
BUTLER = "the-butler-olmq6o"
MOONTOWER = "moontower-69d81c"
RETREAT = "the-retreat-at-tampa"
CATALYST = "catalyst-s7m7fb"
STANGEL = "stangel-hall-3-zooq"
MURRAY = "murray-hall-gcf4nm"
MURDOUGH = "murdough-hall-mvhqyi"

RIVE_AMENITIES = ["Games Room", "Gas", "Co-working Spaces", "Dishwasher",
                  "Microwave", "Oven", "Shared Refrigerator", "Furnishing Option",
                  "BBQ Area", "Cinema Room", "Gym", "Rooftop Terrace",
                  "Swimming Pool", "Wifi", "Pet Friendly", "Controlled Access Gate",
                  "Maintenance Team", "Library / Study Area", "Post / Parcel Collection",
                  "Entertainment Area / Lounge", "Smart Home Technology",
                  "Private Balcony / Patio", "Walk-in Closet", "Washer / Dryer"]

# ---------------------------------------------------------------- per-task specs
SPECS = {
0: dict(
  summary="Find the highest-rated Student Community near Georgia Tech under "
          "$1,200, open its page, report name/distance/two amenities, then save "
          "it to alice's saved properties.",
  gates=[("visited_gt_srp_filtered",
          r"/us/ga/atlanta/u/georgia-institute-of-technology\?.*max_price=1200.*type=Student"),
         ("visited_rive_property", rf"/us/ga/atlanta/p/{RIVE}")],
  answer=[("phrase", "answer_name", "The Rive Atlanta"),
          ("any", "answer_distance", ["0.7", "0.69"]),
          ("count_at_least", "answer_amenities", (RIVE_AMENITIES, 2))],
  db="stateful",
  db_code=f'''
    check_only_tables_changed(judge, initial_db, after_db,
                               {{"bookmarks", "property_views"}})
    check_bookmark_delta(judge, initial_db, after_db, "alice.j@test.com", "{RIVE}", None)
    check_views_added(judge, initial_db, after_db, ["{RIVE}"])''',
),
1: dict(

  summary="Budget calculator 4-step flow: income $1,500 aid + $600 job, expenses" "350/90/70/280/100/120; report the safety buffer, rent target, the" "$800-rent leftover with the calculator's verdict, and the property count" "of the college search from the last step.",
  gates=[("visited_budget_calculator", r"/budget-calculator"),
         ("visited_college_search", r"/search\?q=Georgia"),],
  answer=[("number", "answer_buffer", 420),
          ("number", "answer_target", 670),
          ("number", "answer_leftover", 290),
          ("phrase", "answer_verdict", "Tight but doable"),
          ("number", "answer_search_properties", 1),],
  db="read_only",
  db_code='''
    check_read_only(judge, initial_db, after_db)''',
),
2: dict(

  summary="Cheapest dorm-style housing near UT Austin (8 dorms listed); sign in as" "bob, send a fall-availability inquiry, then report from My Inquiries the" "new inquiry's date and Bob's inquiry total.",
  gates=[("visited_ut_srp",
          r"/us/tx/austin/u/the-university-of-texas-at-austin"),
         ("visited_littlefield", rf"/us/tx/austin/p/{LITTLEFIELD}"),
         ("visited_ut_srp_dorm_filtered", r"/us/tx/austin/u/the-university-of-texas-at-austin\?.*type=Dorm"),
         ("visited_my_inquiries", r"/profile/inquiries"),],
  answer=[("phrase", "answer_name", "Littlefield Hall"),
          ("phrase", "answer_address", "2503 Whitis Ave"),
          ("phrase", "answer_reference", "INQ-000005"),
          ("number", "answer_dorm_count", 8),
          ("number", "answer_price", 935),
          ("count_at_least", "answer_amenity",
           (['Air Conditioning', 'Entertainment Area / Lounge'], 1)),
          ("phrase", "answer_inquiry_date", "September 26, 2026"),
          ("number", "answer_total_inquiries", 2),],
  db="stateful",
  db_code=f'''
    check_only_tables_changed(judge, initial_db, after_db,
                               {{"enquiries", "property_views"}})
    check_enquiry_created(judge, initial_db, after_db, "bob.c@test.com", "{LITTLEFIELD}", "INQ-000005")
    check_views_added(judge, initial_db, after_db, ["{LITTLEFIELD}"])''',
),
3: dict(
  summary="Two homes closest to Georgia Tech and two closest to Georgia State "
          "(default distance ordering); report names+prices; open the most "
          "expensive of the four and report its Google rating and review count.",
  gates=[("visited_gt_srp", r"/us/ga/atlanta/u/georgia-institute-of-technology"),
         ("visited_gsu_srp", r"/us/ga/atlanta/u/georgia-state-university"),
         ("visited_freeman", rf"/us/ga/atlanta/p/{FREEMAN}")],
  answer=[("phrase", "answer_gt1_name", "International House"),
          ("number", "answer_gt1_price", 950),
          ("phrase", "answer_gt2_name", "Eighth Street Apartments"),
          ("number", "answer_gt2_price", 1411),
          ("phrase", "answer_gsu1_name", "Piedmont Pad Apartments"),
          ("number", "answer_gsu1_price", 500),
          ("phrase", "answer_gsu2_name", "Freeman Ford Lofts"),
          ("number", "answer_gsu2_price", 1850),
          ("number", "answer_rating", "4.7"),
          ("number", "answer_reviews", 36)],
  db="views_only",
  db_code=f'''
    check_views_only(judge, initial_db, after_db, ["{FREEMAN}"])''',
),
4: dict(

  summary="Carol's recently viewed Midtown Atlanta property costing roughly" "$1,400-1,500 rated 4.2; full history audit (count + all names), its" "street address and rating, the navbar Recently Viewed cross-check, and" "her saved-properties total.",
  gates=[("visited_history", r"/profile/history"),
         ("visited_eighth", rf"/us/ga/atlanta/p/{EIGHTH}"),
         ("visited_bookmarks", r"/profile/bookmarks"),],
  answer=[("phrase", "answer_name", "Eighth Street Apartments"),
          ("number", "answer_price", 1411),
          ("number", "answer_reviews", 36),
          ("number", "answer_history_count", 3),
          ("phrase", "answer_history_name_2", "University House Midtown"),
          ("phrase", "answer_history_name_3", "Linea Midtown"),
          ("phrase", "answer_street_address", "555 8th St NW"),
          ("number", "answer_rating", "4.2"),
          ("number", "answer_saved_count", 2),],
  db="views_only",
  db_code=f'''
    check_views_only(judge, initial_db, after_db, ["{EIGHTH}"])''',
),
5: dict(

  summary="Gainesville internship listings: total count, newest posting, part-time" "and fellowship tag counts, the Part-Time filter's job, the footer Jobs" "page's newest Austin listing, and the Gainesville city page property" "count.",
  gates=[("visited_gainesville_jobs", r"/us/fl/gainesville/internships"),
         ("visited_jobs_parttime_filter", r"/us/fl/gainesville/internships\?type=part-time"),
         ("visited_jobs_home", r"/jobs"),
         ("visited_gainesville_city", r"/us/fl/gainesville"),],
  answer=[("number", "answer_total", 5),
          ("phrase", "answer_newest_title", "Medical Assistant"),
          ("phrase", "answer_newest_company", "Theoriamedical"),
          ("number", "answer_parttime", 1),
          ("number", "answer_fellowship", 3),
          ("phrase", "answer_filtered_title", "Part-Time Assistant Manager - Level 2"),
          ("phrase", "answer_filtered_company", "Boxlunch"),
          ("phrase", "answer_austin_newest", "Operations Associate (Part-Time) - Domain Austin"),
          ("phrase", "answer_austin_company", "Aloyoga"),
          ("number", "answer_gainesville_properties", 15),],
  db="read_only",
  db_code='''
    check_read_only(judge, initial_db, after_db)''',
),
6: dict(

  summary="Austin city page: visa FAQ, rental range, properties listed, popular" "college, average student budget excluding tuition, the free museum and" "the free-tours government building; then the UT Austin homes page's" "results total and, after sorting by rating, the highest-rated home's" "name, price and rating.",
  gates=[("visited_austin_city", r"/us/tx/austin"),
         ("visited_ut_srp", r"/us/tx/austin/u/the-university-of-texas-at-austin"),],
  answer=[("phrase", "answer_visa", "F-1 visa"),
          ("number", "answer_range_low", 1000),
          ("number", "answer_range_high", 1600),
          ("number", "answer_properties", 30),
          ("phrase", "answer_popular_college", "The University of Texas at Austin"),
          ("number", "answer_budget_low", 1500),
          ("number", "answer_budget_high", 2500),
          ("phrase", "answer_museum", "Blanton Museum of Art"),
          ("phrase", "answer_capitol", "Texas State Capitol"),
          ("number", "answer_srp_total", 592),
          ("phrase", "answer_top_rated_name", "Carothers Residence Hall"),
          ("number", "answer_top_rated_price", 1560),
          ("number", "answer_top_rated_rating", "4.7"),],
  db="read_only",
  db_code='''
    check_read_only(judge, initial_db, after_db)''',
),
7: dict(
  summary="David: remove the Atlanta property from his saved properties, add "
          "the only 5.0-rated property near Ohio State under $600, report the "
          "final saved count and the added property's name.",
  gates=[("visited_bookmarks", r"/profile/bookmarks"),
         ("visited_osu_srp", r"/us/oh/columbus/u/the-ohio-state-university"),
         ("visited_kenny", rf"/us/oh/columbus/p/{KENNY}")],
  answer=[("number", "answer_saved_count", 3),
          ("phrase", "answer_added_name", "Kenny Road Apartments")],
  db="stateful",
  db_code=f'''
    check_only_tables_changed(judge, initial_db, after_db,
                               {{"bookmarks", "property_views"}})
    check_bookmark_delta(judge, initial_db, after_db, "david.k@test.com", "{KENNY}", "the-standard-at-atlanta-vesb8v")
    check_views_added(judge, initial_db, after_db, ["{KENNY}"])''',
),
8: dict(

  summary="AI Search on the UCF homes page for an apartment up to $800/month;" "report the pre-filter and post-filter result counts, what the AI search" "filtered by, and the cheapest apartment's name, rating, address," "starting price, Google review count and campus distance.",
  gates=[("visited_ucf_srp_ai_filtered",
          r"/us/fl/orlando/u/university-of-central-florida\?.*max_price=800.*type=Apartment"),
         ("visited_hub", rf"/us/fl/orlando/p/{HUB}")],
  answer=[("number", "answer_result_count", 5),
          ("phrase", "answer_name", "Hub On Campus Orlando"),
          ("number", "answer_rating", "4.0"),
          ("phrase", "answer_address", "11012 Hub Plz"),
          ("number", "answer_pre_total", 177),
          ("phrase", "answer_ai_filter_type", "Apartment"),
          ("number", "answer_ai_filter_max", 800),
          ("number", "answer_price", 500),
          ("number", "answer_reviews", 1034),
          ("any", "answer_distance", ["2.4", "2.3786"]),],
  db="views_only",
  db_code=f'''
    check_views_only(judge, initial_db, after_db, ["{HUB}"])''',
),
9: dict(

  summary="Case Western Reserve homes page: use the map view, identify the property" "closest to the campus marker, report the page's results total, the" "property's name, price, rating, review count, address and two amenities," "and the second-closest property's name and price.",
  gates=[("visited_cwru_srp", r"/us/oh/cleveland/u/case-western-reserve-university"),
         ("visited_parkside", rf"/us/oh/cleveland/p/{PARKSIDE}")],
  answer=[("phrase", "answer_name", "Parkside Dwellings"),
          ("number", "answer_price", 1360),
          ("number", "answer_rating", "4.3"),
          ("phrase", "answer_address", "2040 Stearns Rd"),
          ("number", "answer_srp_total", 316),
          ("number", "answer_reviews", 15),
          ("count_at_least", "answer_amenities",
           (['Gym', 'Swimming Pool', 'Pet Friendly', 'Furnishing Option', 'Washer / Dryer', 'Air Conditioning', 'Rooftop Terrace', 'Entertainment Area / Lounge', 'Library / Study Area'], 2)),
          ("phrase", "answer_second_name", "Skyline on Stokes"),
          ("number", "answer_second_price", 1380),],
  db="views_only",
  db_code=f'''
    check_views_only(judge, initial_db, after_db, ["{PARKSIDE}"])''',
),
10: dict(

  summary="From the Texas college finder, locate 'TAMU', report the most expensive" "property within one mile (name, price, distance, gym, rating, review" "count), the campus page's results total, and the cheapest home on it.",
  gates=[("visited_tx_finder_tamu", r"/us/tx/u\?q=TAMU"),
         ("visited_tamu_srp", r"/us/tx/college-station/u/texas-am-university"),
         ("visited_100park", rf"/us/tx/college-station/p/{PARK100}")],
  answer=[("phrase", "answer_university", "Texas A&M University"),
          ("phrase", "answer_name", "100 Park"),
          ("number", "answer_price", 1539),
          ("any", "answer_distance", ["0.3", "0.26"]),
          ("phrase", "answer_gym", "Gym"),
          ("number", "answer_rating", "4.1"),
          ("number", "answer_reviews", 63),
          ("number", "answer_srp_total", 141),
          ("phrase", "answer_cheapest_name", "The Gardens Apartments"),
          ("number", "answer_cheapest_price", 125),],
  db="views_only",
  db_code=f'''
    check_views_only(judge, initial_db, after_db, ["{PARK100}"])''',
),
11: dict(
  summary="Villas on Rio as alice: submit an inquiry with an invalid email and "
          "empty phone, report the exact validation errors, then correct and "
          "send; report the reference.",
  gates=[("visited_villas", rf"/us/tx/austin/p/{VILLAS}")],
  answer=[("phrase", "answer_email_error", "Invalid email address"),
          ("phrase", "answer_phone_error", "Phone number is required"),
          ("phrase", "answer_reference", "INQ-000005")],
  db="stateful",
  db_code=f'''
    check_only_tables_changed(judge, initial_db, after_db,
                               {{"enquiries", "property_views"}})
    check_enquiry_created(judge, initial_db, after_db, "alice.j@test.com", "{VILLAS}", "INQ-000005")
    check_views_added(judge, initial_db, after_db, ["{VILLAS}"])''',
),
12: dict(

  summary="Search 'Seminoles', identify the university and its city, find the" "cheapest property near that campus (name, price, rating, distance," "address, amenity), the campus page's results total, and the most" "expensive home on it.",
  gates=[("visited_seminoles_search", r"/search\?q=Seminoles"),
         ("visited_fsu_srp", r"/us/fl/tallahassee/u/florida-state-university"),
         ("visited_southgate", rf"/us/fl/tallahassee/p/{SOUTHGATE}")],
  answer=[("phrase", "answer_university", "Florida State University"),
          ("phrase", "answer_city", "Tallahassee"),
          ("phrase", "answer_name", "Southgate Campus Centre"),
          ("number", "answer_price", 455),
          ("number", "answer_rating", "4.3"),
          ("any", "answer_distance", ["0.3", "0.32"]),
          ("phrase", "answer_address", "675 W Jefferson St"),
          ("count_at_least", "answer_amenity",
           (['Pet Friendly', 'Entertainment Area / Lounge', 'Furnishing Option', 'Elevators', 'Gym', 'Swimming Pool', 'Air Conditioning'], 1)),
          ("number", "answer_srp_total", 182),
          ("phrase", "answer_most_expensive_name", "TLH Rent, LLC"),
          ("number", "answer_most_expensive_price", 2200),],
  db="views_only",
  db_code=f'''
    check_views_only(judge, initial_db, after_db, ["{SOUTHGATE}"])''',
),
13: dict(

  summary="Scams guide: the two red flags matching a wire-transfer landlord 'away" "on vacation', the first three emergency-protocol steps, the reporting" "phone and email (cross-checked on the Contact page), and the cheapest" "home near UT Austin vs the Austin price range.",
  gates=[("visited_scams_guide", r"/guides/avoid-scams-and-fraud"),
         ("visited_contact_page", r"/contact"),
         ("visited_ut_srp", r"/us/tx/austin/u/the-university-of-texas-at-austin"),],
  answer=[("phrase", "answer_redflag_wire", "Off-Platform Payments"),
          ("phrase", "answer_redflag_ghost_1", "Ghost"),
          ("phrase", "answer_redflag_ghost_2", "Landlord"),
          ("phrase", "answer_step1", "Report anything suspicious"),
          ("phrase", "answer_step2", "Trace the Paperwork"),
          ("phrase", "answer_step3", "External Authorities"),
          ("phrase", "answer_phone", "+44 800 316 2918"),
          ("phrase", "answer_email", "contact@student.com"),
          ("phrase", "answer_cheapest_name", "College House Nueces"),
          ("number", "answer_cheapest_price", 532),],
  db="read_only",
  db_code='''
    check_read_only(judge, initial_db, after_db)''',
),
14: dict(
  summary="Register Mia Torres, find homes near the University of Georgia, "
          "save the most expensive 5.0-rated property, send it a spring "
          "availability inquiry; report the saved property and reference.",
  gates=[("visited_uga_srp", r"/us/ga/athens/u/university-of-georgia"),
         ("visited_butler", rf"/us/ga/athens/p/{BUTLER}")],
  answer=[("phrase", "answer_name", "The Butler"),
          ("phrase", "answer_reference", "INQ-000005")],
  db="stateful",
  db_code=f'''
    check_only_tables_changed(judge, initial_db, after_db,
                               {{"users", "bookmarks", "enquiries", "property_views"}})
    check_user_created(judge, initial_db, after_db, "mia.torres@test.com", "Mia", "Torres")
    check_bookmark_delta(judge, initial_db, after_db, "mia.torres@test.com", "{BUTLER}", None)
    check_enquiry_created(judge, initial_db, after_db, "mia.torres@test.com", "{BUTLER}", "INQ-000005")
    check_views_added(judge, initial_db, after_db, ["{BUTLER}"])''',
),
15: dict(

  summary="Moontower's price range, gallery photo count, Google rating and review" "count, street address and an amenity; Villas on Rio's rating, review" "count, starting price and an amenity; which is cheaper to start with and" "which sits closer to campus.",
  gates=[("visited_moontower", rf"/us/tx/austin/p/{MOONTOWER}"),
         ("visited_villas", rf"/us/tx/austin/p/{VILLAS}")],
  answer=[("number", "answer_min_price", 700),
          ("number", "answer_max_price", 6475),
          ("number", "answer_photos", 10),
          ("number", "answer_rating", "3.5"),
          ("number", "answer_reviews", 178),
          ("number", "answer_villas_min", 989),
          ("number", "answer_villas_rating", "4.3"),
          ("phrase", "answer_cheaper", "Moontower"),
          ("phrase", "answer_moontower_address", "2204 San Antonio St"),
          ("count_at_least", "answer_moontower_amenity",
           (['Gym', 'Rooftop Terrace', 'Entertainment Area / Lounge', 'Yoga Studio'], 1)),
          ("number", "answer_villas_reviews", 456),
          ("count_at_least", "answer_villas_amenity",
           (['Washer / Dryer', 'Yoga Studio', 'Gym', 'Library / Study Area', 'Rooftop Terrace'], 1)),
          ("number", "answer_villas_distance", "0.1"),
          ("number", "answer_moontower_distance", "0.4"),],
  db="views_only",
  db_code=f'''
    check_views_only(judge, initial_db, after_db, ["{MOONTOWER}", "{VILLAS}"])''',
),
16: dict(
  summary="BLOCKED (site defect): Student Communities near USF priced "
          "$900-$1,000 sorted price-ascending; report the match count, its "
          "street address and every neighbourhood vibe label. The only match's "
          "property page returns HTTP 500 (room_details int), so the address "
          "and vibe labels are unobtainable until the contributor fixes it.",
  gates=[("visited_usf_srp_filtered",
          r"/us/fl/tampa/u/university-of-south-florida\?.*min_price=900.*max_price=1000.*type=Student"),
         ("visited_retreat", rf"/us/fl/miami/p/{RETREAT}")],
  answer=[("number", "answer_match_count", 1),
          ("phrase", "answer_name", "The Retreat at Tampa"),
          ("number", "answer_price", 940),
          ("phrase", "answer_address", "11326 N 46th St"),
          ("count_at_least", "answer_vibes",
           (["Coffee & food", "Music & nightlife", "Artsy & cultural"], 3))],
  db="views_only",
  db_code=f'''
    check_views_only(judge, initial_db, after_db, ["{RETREAT}"])''',
),
17: dict(
  summary="Browse three different Texas Tech properties anonymously, report the "
          "Recently Viewed dropdown's names, then check as carol whether they "
          "appear on her Recently Viewed Properties page.",
  gates=[("visited_ttu_srp", r"/us/tx/lubbock/u/texas-tech-university"),
         ("visited_stangel", rf"/us/tx/lubbock/p/{STANGEL}"),
         ("visited_murray", rf"/us/tx/lubbock/p/{MURRAY}"),
         ("visited_murdough", rf"/us/tx/lubbock/p/{MURDOUGH}"),
         ("visited_history", r"/profile/history")],
  answer=[("phrase", "answer_item1", "Stangel Hall"),
          ("phrase", "answer_item2", "Murray Hall"),
          ("phrase", "answer_item3", "Murdough Hall"),
          ("phrase", "answer_appear", "appear"),
          ("absent", "answer_appear_not_negated",
           ["not appear", "do not appear", "don't appear", "didn't appear",
            "did not appear", "no longer appear"])],
  db="views_only",
  db_code=f'''
    check_views_only(judge, initial_db, after_db, ["{STANGEL}", "{MURRAY}", "{MURDOUGH}"])''',
),
18: dict(
  summary="BLOCKED (site defect): Catalyst's contact email/phone/website, then "
          "the budget calculator for $2,300 income / $1,180 expenses — rent "
          "target and affordability conclusion. The contact email is never "
          "rendered anywhere in the mirror's UI (upstream's page contains it), "
          "so the email sub-goal is unobtainable until the contributor fixes it.",
  gates=[("visited_catalyst", rf"/us/ga/atlanta/p/{CATALYST}"),
         ("visited_budget_calculator", r"/budget-calculator")],
  answer=[("phrase", "answer_contact_email", "catalystmidtown@crm-living.com"),
          ("phrase", "answer_phone", "677-3286"),
          ("phrase", "answer_website", "catalystmidtown.com"),
          ("number", "answer_rent_target", 660),
          ("number", "answer_cheapest_room", 1099),
          ("phrase", "answer_conclusion", "not")],
  db="views_only",
  db_code=f'''
    check_views_only(judge, initial_db, after_db, ["{CATALYST}"])''',
),
19: dict(

  summary="Alice's full account audit: the older inquiry (reference, property," "date, message), the other inquiry's reference and property, all" "saved-property names and the total, and the Recently Viewed count.",
  gates=[("visited_inquiries", r"/profile/inquiries"),
         ("visited_bookmarks", r"/profile/bookmarks"),
         ("visited_history", r"/profile/history"),],
  answer=[("phrase", "answer_reference", "INQ-000001"),
          ("phrase", "answer_property", "Moontower"),
          ("any", "answer_date", ["September 20, 2026", "September 20", "2026-09-20"]),
          ("phrase", "answer_message", "studio with a private bathroom"),
          ("number", "answer_saved_count", 3),
          ("phrase", "answer_other_reference", "INQ-000002"),
          ("phrase", "answer_other_property", "Villas on Rio"),
          ("phrase", "answer_saved_name_3", "International House"),
          ("number", "answer_viewed_count", 4),],
  db="read_only",
  db_code='''
    check_read_only(judge, initial_db, after_db)''',
),
20: dict(
  summary="BLOCKED (site defect): the only suburban-feel Student Community "
          "near USF priced $900-$1,000 — name, price, rating, 'Key things to "
          "know' labels — then save it as bob. The property page returns HTTP "
          "500, so the labels are unobtainable and the save button (on the "
          "broken page) is unreachable.",
  gates=[("visited_usf_srp_filtered",
          r"/us/fl/tampa/u/university-of-south-florida\?.*min_price=900.*max_price=1000.*type=Student"),
         ("visited_retreat", rf"/us/fl/miami/p/{RETREAT}")],
  answer=[("phrase", "answer_name", "The Retreat at Tampa"),
          ("number", "answer_price", 940),
          ("number", "answer_rating", "4.0"),
          ("count_at_least", "answer_ktk",
           (["Quiet area", "Suburban", "Good shopping & grocery"], 3))],
  db="stateful",
  db_code=f'''
    check_only_tables_changed(judge, initial_db, after_db,
                               {{"bookmarks", "property_views"}})
    check_bookmark_delta(judge, initial_db, after_db, "bob.c@test.com", "{RETREAT}", None)
    check_views_added(judge, initial_db, after_db, ["{RETREAT}"])''',
),
}

TEMPLATE = '''#!/usr/bin/env python3
"""Verify Student.com--{n}.

{summary}

Generated by make_verifiers.py (deterministic regeneration; do not edit by hand).
"""
from verify_lib import (check_answer_absent, check_answer_any,
                        check_answer_count_at_least, check_answer_number,
                        check_answer_phrase, check_bookmark_delta, check_enquiry_created,
                        check_only_tables_changed, check_read_only,
                        check_trajectory_identity, check_user_created,
                        check_views_added, check_views_only, check_visited_path,
                        final_answer, run_verifier)

TASK_ID = "Student.com--{n}"


def run_checks(judge, traj, initial_db, after_db):
    answer = final_answer(traj)
    check_trajectory_identity(judge, traj, TASK_ID)
{gates}
{answers}
{db_code}


if __name__ == "__main__":
    raise SystemExit(run_verifier(TASK_ID, run_checks))
'''

GATE_FMT = '''    check_visited_path(judge, traj, "{name}", r"{pattern}")'''
ANSWER_FMT = {
    "phrase": '    check_answer_phrase(judge, answer, "{name}", {expr!r})',
    "absent": '    check_answer_absent(judge, answer, "{name}", {expr!r})',
    "number": '    check_answer_number(judge, answer, "{name}", {expr!r})',
    "any": '    check_answer_any(judge, answer, "{name}", {expr!r})',
    "count_at_least": '    check_answer_count_at_least(judge, answer, "{name}", {expr[0]!r}, {expr[1]!r})',
}


def main():
    for n, spec in SPECS.items():
        gates = "\n".join(GATE_FMT.format(name=name, pattern=pattern)
                          for name, pattern in spec["gates"])
        answers = []
        for kind, name, expr in spec["answer"]:
            if kind == "count_at_least":
                answers.append(ANSWER_FMT[kind].format(name=name, expr=expr))
            else:
                answers.append(ANSWER_FMT[kind].format(name=name, expr=expr))
        body = TEMPLATE.format(n=n, summary=spec["summary"],
                               gates=gates, answers="\n".join(answers),
                               db_code=spec["db_code"])
        (OUT / f"verify_{n}.py").write_text(body, encoding="utf-8")
    print(f"generated {len(SPECS)} verifiers")


if __name__ == "__main__":
    main()
