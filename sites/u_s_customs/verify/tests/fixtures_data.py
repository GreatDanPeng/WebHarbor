"""Frozen honest fixtures for the u_s_customs verifier tests.

Transcribed from the reviewer's real Chromium walkthroughs of the
review container (seed md5 26b00e5808a42028cc0c3019eb3912f5): the
paths list is the distinct-URL visit order of the live session and
the answer is the honest final answer read off the pages.
"""

BASE = "http://localhost:40162"

SPECS = {
    0: {
        # paths visited (in order) by the honest walkthrough
        "paths": [
            "/bwt",
            "/bwt?border=mexico&q=&sort=delay",
            "/bwt/crossing/250601",
            "/bwt?border=mexico&q=Otay+Mesa&sort=delay",
            "/bwt/crossing/250602",
        ],
        "answer": "Longest standard passenger delay on the Mexican border: Otay Mesa - Passenger, 185 minutes, 3 standard lanes open, updated 10:00 am PDT. Detail page: Ready Lane delay 120 minutes; port hours 24 hrs/day. Second-longest Mexican-border crossing: San Ysidro, standard passenger delay 150 minutes. Otay Mesa - Commercial standard commercial delay: 40 minutes.",
        "mutations": [],
    },
    1: {
        # paths visited (in order) by the honest walkthrough
        "paths": [
            "/bwt",
            "/bwt?border=all&q=Blaine&sort=name",
            "/bwt/crossing/300401",
            "/bwt/crossing/300402",
            "/bwt/crossing/300403",
        ],
        "answer": "3 Blaine crossings: Pacific Highway (24 hrs/day, standard 5 min, NEXUS 5 min, 1 NEXUS lane open); Peace Arch (24 hrs/day, standard 5 min, NEXUS 5 min, 1 NEXUS lane open); Point Roberts (24 hrs/day, lanes 'Update Pending'). A NEXUS member should choose Pacific Highway or Peace Arch because both have NEXUS lanes open at 5 minutes, while Point Roberts is not reporting.",
        "mutations": [],
    },
    2: {
        # paths visited (in order) by the honest walkthrough
        "paths": [
            "/bwt",
            "/bwt?border=all&q=San+Ysidro&sort=name",
            "/bwt/crossing/250401",
            "/",
            "/contact/ports",
            "/about/contact/ports/CA",
            "/about/contact/ports/port/san-ysidro-class-california-2504",
            "/bwt?border=all&q=PedWest&sort=name",
            "/bwt/crossing/250407",
        ],
        "answer": "San Ysidro crossings: main San Ysidro (std passenger 150 min/6 open, Ready 120 min/11, NEXUS/SENTRI 30 min/11, pedestrian 60 min/16), Cross Border Express, and PedWest. San Ysidro port code 2504, phone +1 619-428-2188. PedWest: pedestrian delay 15 min with 4 lanes open, hours 6 am-2 pm.",
        "mutations": [],
    },
    3: {
        # paths visited (in order) by the honest walkthrough
        "paths": [
            "/travel/international-visitors/esta",
            "/esta/apply",
            "/esta/apply?step=applicant",
            "/esta/apply?step=personal",
            "/esta/apply?step=travel",
            "/esta/apply?step=eligibility",
            "/esta/apply?step=review",
            "/esta/apply?step=pay",
            "/esta/confirmation/ESTA-86C8DC4",
        ],
        "answer": "Application number ESTA-86C8DC4, status Authorization Approved, authorization valid until 2028-09-28, total fee charged $40.27.",
        "mutations": [
            ("esta_applications", "INSERT INTO esta_applications (application_number, user_id, family_name, first_name, birth_date, gender, citizenship, passport_number, passport_issue_country, passport_expiry, email, phone, address_city, address_country, travel_purpose, destination_address, status, fee_usd, created_at, expires_on) VALUES ('ESTA-86C8DC4', NULL, 'Andersen', 'Sofia', '1995-03-14', 'Female', 'Denmark', 'DK4455667', 'Denmark', '2029-05-20', 'sofia.andersen@example.com', '+45 33 555 0188', 'Copenhagen', 'Denmark', 'Tourism', '300 Almaden Blvd, San Jose, CA', 'Authorization Approved', 40.27, '2026-09-28', '2028-09-28')"),
        ],
    },
    4: {
        # paths visited (in order) by the honest walkthrough
        "paths": [
            "/",
            "/search?q=Visa+Waiver",
            "/travel/international-visitors/visa-waiver-program",
            "/travel/international-visitors/esta",
            "/esta/check",
        ],
        "answer": "VWP: 42 countries, up to 90 days, Germany is on the list. ESTA fee $40.27; travelers must have an e-Passport with an embedded electronic chip. Passport DE29384756: application ESTA-88291045, status Authorization Approved, expires 2028-08-20. ESTA authorization does not determine admissibility \u2014 CBP officers determine admissibility on arrival; apply as soon as travel plans begin (before buying tickets).",
        "mutations": [],
    },
    5: {
        # paths visited (in order) by the honest walkthrough
        "paths": [
            "/i94/request",
        ],
        "answer": "Alice Johnson: I-94 269745632011, class VWP B-1, entered 2026-06-14, admitted until 2026-09-12, POE Washington Dulles International Airport. Bob Chen: I-94 269745641088, class US Citizen, entered 2026-09-03, POE San Ysidro, California - Pedestrian. Wrong birth date: 'No I-94 record found. Verify that your name, date of birth and passport number match your passport exactly, then try again.'. Correct DOB: Carol Davis class VWP B-2, admitted until 2026-06-20.",
        "mutations": [],
    },
    6: {
        # paths visited (in order) by the honest walkthrough
        "paths": [
            "/login",
            "/account",
            "/ttp/status/GE-77031188",
            "/ttp/schedule/GE-77031188",
            "/travel/trusted-traveler-programs",
        ],
        "answer": "Bob's Global Entry application GE-77031188, status Conditionally Approved \u2014 Schedule Interview\t\u2014, fee $120.00. After scheduling at Austin-Bergstrom International Airport on 2026-10-15 at 9:00 a.m., status is Interview Scheduled; the enrollment center's contact phone is (512) 530-3056. Global Entry membership lasts 5 years; NEXUS fee is $50.00.",
        "mutations": [
            ("ttp_applications", "UPDATE ttp_applications SET interview_center_id=24, interview_date='2026-10-15', interview_slot='9:00 a.m.', status='Interview Scheduled' WHERE application_number='GE-77031188'"),
        ],
    },
    7: {
        # paths visited (in order) by the honest walkthrough
        "paths": [
            "/",
            "/newsroom/media-releases/all",
            "/newsroom/media-releases/all?q=khat&category=all",
            "/newsroom/local-media-release/new-york-man-arrested-after-cbp-officers-seize-65-pounds-khat",
            "/newsroom/local-media-release/atlanta-cbp-officers-stop-more-4000-pounds-illegal-khat-entering-us",
        ],
        "answer": "Dulles release: Bakari Wally, 24, from the the Bronx, arrested after CBP seized 65 pounds of khat at Washington Dulles International Airport; arrested by Metropolitan Washington Airports Authority Police. Atlanta release: more than 4,000 pounds of khat seized since the beginning of the year at Hartsfield-Jackson Atlanta International Airport. Both are Local Media Releases.",
        "mutations": [],
    },
    8: {
        # paths visited (in order) by the honest walkthrough
        "paths": [
            "/",
            "/newsroom/media-releases/all",
            "/newsroom/media-releases/all?q=&category=all&page=2",
            "/newsroom/media-releases/all?q=&category=all&page=3",
            "/newsroom/local-media-release/11-memorial-ceremony-juarez",
            "/newsroom/media-releases/all?q=Tidal+Wave&category=all",
            "/newsroom/national-media-release/operation-tidal-wave-boston-leads-87-cruise-ship-crew-removals-cbp",
        ],
        "answer": "9/11 memorial ceremony: Laredo Port of Entry, at the Juarez-Lincoln Bridge, 2026-09-11, honoring the victims, survivors, first responders and all those affected by the terrorist attacks of Sept. Operation Tidal Wave search returns 2 releases; the Sept 25, 2026 release reports 87 cruise ship crew members removed at the Port of Boston. The other Boston release: 'CBP officers remove another 10 cruise ship crewmembers in Boston following Operation Tidal Wave investigation'.",
        "mutations": [],
    },
    9: {
        # paths visited (in order) by the honest walkthrough
        "paths": [
            "/newsroom/publications/forms",
            "/newsroom/publications/forms?q=7501",
            "/newsroom/publications/forms/7501-entry-summary-with-continuation-sheets",
            "/newsroom/publications/forms?q=19",
            "/newsroom/publications/forms/19",
            "/newsroom/publications/forms?q=declaration",
        ],
        "answer": "97 forms listed. Form 7501 'CBP Form 7501 - Entry Summary with Continuation Sheets', listed Feb 11 2026, sha256 87046018fbd6ca62\u2026. Form 19 is 'Protest', listed May 1 2024. Most recent listed date: CBP Form 1304 'Crew Effects Declarations'. 'declaration' search matches 13 entries; the Customs Declaration is form 6059B.",
        "mutations": [],
    },
    10: {
        # paths visited (in order) by the honest walkthrough
        "paths": [
            "/login",
            "/account",
            "/newsroom/publications/forms",
            "/newsroom/publications/forms?q=6059B",
            "/newsroom/publications/forms/6059b-4",
        ],
        "answer": "6059B has 18 entries, one per language: Arabic (\u0642\u0627\u0628\u0644 \u0644\u0644\u062a\u0639\u0628\u0626\u0629), Farsi, English (Fillable), Italian, Vietnamese, German (Deutsch), Dutch (Nederlands), Japanese (\u65e5\u672c\u8a9e), Punjabi, Chinese Simplified, Chinese Traditional, Korean (\ud55c\uad6d\uc5b4), Spanish (Espa\u00f1ol), French, Polish (Polski), Portuguese (Portugu\u00eas), Russian (\u0440\u0443\u0441\u0441\u043a\u0438\u0439), Hebrew (\u05e2\u05d1\u05e8\u05d9\u05ea). English fillable listed Jul 25 2024; saved to account \u2014 appears under Saved Forms as 'CBP Form 6059B' (Customs Declaration - English (Fillable)). Carol's other saved form: CBP Form 7501 (Entry Summary).",
        "mutations": [
            ("saved_forms", "INSERT INTO saved_forms (user_id, form_id, created_at) VALUES (3, 63, '2026-09-28')"),
        ],
    },
    11: {
        # paths visited (in order) by the honest walkthrough (F-1 redesign:
        # multi-page Trade chain — car import + internet purchases)
        "paths": [
            "/trade/basic-import-export",
            "/trade/basic-import-export/importing-car",
            "/trade/basic-import-export/internet-purchases",
        ],
        "answer": "Car import: safety standards under the Motor Vehicle Safety Act of 1966; CBP clearance requires EPA form 3520-1 and DOT form HS-7; after the exemption a flat duty rate of 3% applies toward the next $1,000 of value; USMCA (United States-Mexico-Canada Agreement) provides duty-free treatment for qualifying U.S. goods returned; vehicles less than 25 years old must comply with FMVSS; nonresidents may import a car duty-free for personal use up to one year, after which it must be exported within one year and may not be sold in the U.S. Internet purchases: mailed packages over $2,500 may be held at the mail facility until a formal entry is arranged; sellers should attach a completed CN 22 or CN 23 (CBP Declaration Form) to the outside of the package; the importer (the buyer, YOU) pays the duty \u2014 CBP holds the importer liable, not the seller; items downloaded from the Internet are not subject to duty.",
        "mutations": [],
    },
    12: {
        # paths visited (in order) by the honest walkthrough (F-2: adds the
        # ACE page cross-question)
        "paths": [
            "/trade/priority-issues",
            "/trade/priority-issues/adcvd",
            "/trade/priority-issues/ipr",
            "/trade/rulings/informed-compliance-publications",
            "/trade/automated",
        ],
        "answer": "7 priority trade issues: Antidumping and Countervailing Duty (AD/CVD), Intellectual Property Rights (IPR), Import Safety, Textiles/Wearing Apparel, Agriculture and Quota, Revenue, Trade Agreements. AD/CVD stands for Antidumping and Countervailing Duty (AD/CVD). IPR page title: Intellectual Property Rights (IPR). ICP publications belong to the 'What Every Member of the Trade Community Should Know' series. Wearing apparel is covered by Textiles/Wearing Apparel; quotas by Agriculture and Quota. ACE stands for the Automated Commercial Environment \u2014 the U.S. centralized digital 'Single Window' system for processing imports and exports.",
        "mutations": [],
    },
    13: {
        # paths visited (in order) by the honest walkthrough
        "paths": [
            "/",
            "/careers/search",
            "/careers/search?q=Border+Patrol+Agent&org=&category=",
            "/careers/job/882257900",
            "/careers/search?q=Border+Patrol+Agent",
            "/careers/job/882256600",
            "/careers/search?q=CBP+Officer&org=&category=",
            "/careers/job/886464900",
            "/careers/search?q=Officer",
            "/careers/job/882167200",
            "/careers/job/882166800",
        ],
        "answer": "BPA GL 5-7: $51,632 - $92,912, closing 09/30/2026, announcement BPA DH 26-12, recruitment incentive $20,000 ($10,000 on academy completion + $10,000 for prioritized location). CBPO GS 5-7: $41,863 - $112,415, closing 09/30/2026, drug test Yes. The BPA has the higher starting salary by $9,769. BPA belongs to U.S. Border Patrol; CBPO to Office of Field Operations.",
        "mutations": [],
    },
    14: {
        # paths visited (in order) by the honest walkthrough
        "paths": [
            "/",
            "/careers/events",
            "/careers/career-paths",
            "/careers/career-paths/ofo",
        ],
        "answer": "4 events. Texas hiring fair: Waco's Fall Hiring Fair, Waco, TX, Sep 28, 2026, In Person Live Event. Dallas Job Fair: Sep 29, 2026, Addison, TX. Webinar: OFO CBPO Recruitment Webinar - September 29, 2026 (Online). OFO page features Customs and Border Protection Officer / CBP Officer titles and lists the Waco hiring fair (Sep 28, 2026), the recruitment webinar (Sep 29, 2026) and Dallas job fair (Sep 29, 2026). In person: Waco, Dallas, Tulare County; online: the webinar.",
        "mutations": [],
    },
    15: {
        # paths visited (in order) by the honest walkthrough (F-6 fix: Dana's
        # saved crossing is now pinned to 250601 Otay Mesa - Passenger, live
        # 185/120 delays — matches the task premise)
        "paths": [
            "/login",
            "/account",
            "/bwt/crossing/250601",
            "/careers/job/882256600",
            "/ttp/status/GE-77554402",
            "/ttp/schedule/GE-77554402",
        ],
        "answer": "Saved crossing Otay Mesa - Passenger (250601): standard passenger delay 185 min, Ready Lane delay 120 min. Saved job Border Patrol Agent: salary $51,632 - $92,912, closing 09/30/2026. Trusted Traveler application GE-77554402 (Global Entry), status Interview Scheduled, interview 2026-10-14 at 10:00 a.m. at Los Angeles International Airport (LAX); the enrollment center's hours are 7:30 a.m. - 9:30 p.m., contact phone (310) 642-1425.",
        "mutations": [],
    },
    16: {
        # paths visited (in order) by the honest walkthrough
        "paths": [
            "/travel/trusted-traveler-programs",
            "/travel/trusted-traveler-programs/global-entry",
            "/travel/trusted-traveler-programs/tsa-precheck",
        ],
        "answer": "Global Entry $120.00 / 5 years; NEXUS $50.00 / 5 years; SENTRI $122.25 / 5 years; TSA PreCheck $78.00 / 5 years. NEXUS and SENTRI state they include Global Entry benefits. FAST targets commercial truck drivers crossing the Canada and Mexico borders. Global Entry: all applicants must undergo a background check. TSA PreCheck: U.S. citizens, U.S. lawful permanent residents and citizens of partner countries enrolled in Global Entry, NEXUS or SENTRI, as well as Canadian citizens who are NEXUS members.",
        "mutations": [],
    },
    17: {
        # paths visited (in order) by the honest walkthrough
        "paths": [
            "/",
            "/search?q=Visa+Waiver",
            "/travel/international-visitors/visa-waiver-program",
            "/travel/international-visitors/esta",
            "/esta/apply",
            "/esta/apply?step=applicant",
            "/esta/apply?step=personal",
            "/esta/apply?step=travel",
            "/esta/apply?step=eligibility",
            "/esta/apply?step=review",
            "/esta/apply?step=pay",
            "/esta/confirmation/ESTA-A505B32",
            "/bwt",
            "/bwt?border=all&q=Peace+Arch&sort=name",
            "/bwt/crossing/300402",
            "/travel/trusted-traveler-programs",
        ],
        "answer": "Italy participates in the VWP (42 countries total). Marco's ESTA application number ESTA-A505B32, status Authorization Approved. Peace Arch (Blaine) standard passenger delay 5 minutes, hours 24 hrs/day. Global Entry fee $120.00.",
        "mutations": [
            ("esta_applications", "INSERT INTO esta_applications (application_number, user_id, family_name, first_name, birth_date, gender, citizenship, passport_number, passport_issue_country, passport_expiry, email, phone, address_city, address_country, travel_purpose, destination_address, status, fee_usd, created_at, expires_on) VALUES ('ESTA-A505B32', NULL, 'Ricci', 'Marco', '1988-06-02', 'Male', 'Italy', 'IT778899001', 'Italy', '2031-02-15', 'marco.ricci@example.com', '+39 02 555 0123', 'Milan', 'Italy', 'Tourism', '1201 2nd Ave, Seattle, WA', 'Authorization Approved', 40.27, '2026-09-28', '2028-09-28')"),
        ],
    },
    18: {
        # paths visited (in order) by the honest walkthrough
        "paths": [
            "/login",
            "/account",
            "/esta/check",
            "/travel/international-visitors/esta",
        ],
        "answer": "Carol's ESTA application ESTA-88452017, status Authorization Pending, created 2026-09-26; the status checker confirms Authorization Pending. ESTA requires an e-Passport (enhanced secure passport with an embedded electronic chip); apply as soon as travel plans begin / before purchasing tickets. Fee $40.27. Her application shows no expiration date shown yet (pending).",
        "mutations": [],
    },
    19: {
        # paths visited (in order) by the honest walkthrough
        "paths": [
            "/",
            "/travel/advisories-wait-times",
            "/bwt",
            "/bwt?border=canada&q=&sort=name",
            "/search?q=7507",
        ],
        "answer": "The advisory discusses CBP Form 7507 (General Declaration); owners and operators of commercial aircraft may submit it by e-mail; CBP recommends protecting Personally Identifiable Information (PII) when sending it. Canadian border: 30 crossings; first is Alexandria Bay - Thousand Islands Bridge (hours 24 hrs/day). Site search '7507' returns 'General Declaration Agriculture, Customs, Immigration and Public Health'.",
        "mutations": [],
    },
    20: {
        # paths visited (in order) by the honest walkthrough
        "paths": [
            "/",
            "/search?q=Global+Entry",
            "/search?q=San+Ysidro",
            "/search?q=Entry+Summary",
            "/search?q=Otay+Mesa",
            "/bwt/crossing/250601",
        ],
        "answer": "'Global Entry' search returns 2 result sections (Pages, News Releases); e.g. 'Global Entry'. 'San Ysidro' returns News Releases, Ports of Entry, Border Crossings records. 'Entry Summary' matches form 7501. Otay Mesa crossing: standard passenger delay 185 min, Ready Lane 120 min, hours 24 hrs/day.",
        "mutations": [],
    },
}
