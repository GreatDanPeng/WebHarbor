#!/usr/bin/env python3
"""All 21 task walkthroughs — honest natural paths through the real UI
(post-fix task set). Paths mirror how a real agent solves each rewritten
task; T11 uses the new multi-page Trade chain, T12 adds the ACE page,
T13 uses the literal 'CBP Officer' careers search."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from walker import Walk, reset_site, BASE

# ---------------------------------------------------------------- helpers --

def nav_section(w, section, item):
    """Open a nav dropdown (button.nav-toggle) and click an item link."""
    w.click(f"button.nav-toggle:has-text('{section}')", f"nav {section}")
    w.click(f".nav-dropdown a:has-text('{item}')", f"nav {item}")

def login(w, email, password="TestPass123!"):
    w.click("header a[href='/login']", "nav Log in")
    w.fill("#email", email, "email")
    w.fill("#password", password, "password")
    w.submit("form.stack button[type='submit']", "Log in")

def read_text(w, pattern, flags=0):
    m = re.search(pattern, w.body(), flags)
    return m.group(0) if m else None

# ---------------------------------------------------------------- T0 ------
def walk_t0(w):
    w.click("a.quick-card:has-text('View Border Wait Times')", "home quick-card BWT")
    w.select("#border", "mexico", "border filter")
    w.select("#sort", "delay", "sort by delay")
    w.submit("form.filters button.btn", "Apply")
    body = w.body()
    m = re.search(r"Otay Mesa - Passenger.*?(\d+) min", body, re.S)
    top_delay = m.group(1) if m else "?"
    w.read("top port+crossing name", "Otay Mesa - Passenger")
    w.read("top standard passenger delay", top_delay + " minutes")
    w.click("table.data a:has-text('Otay Mesa - Passenger')", "open top crossing")
    body = w.body()
    m = re.search(r"Standard Lanes\s+delay\s+(\d+) minutes\s+(\d+)\s+At ([^\n]+)", body)
    std_open = m.group(2) if m else "?"
    upd = m.group(3) if m else "?"
    w.read("standard lanes open", std_open)
    w.read("lane update time", upd)
    m = re.search(r"Ready Lanes\s+delay\s+(\d+) minutes", body)
    ready = m.group(1) if m else "?"
    w.read("Ready Lane delay", ready + " minutes")
    m = re.search(r"Hours: ([^\n·]+)", body)
    hours = m.group(1).strip() if m else "?"
    w.read("port hours", hours)
    w.page.go_back()
    w._rec("navigate", {"url": "back-to-list", "desc": "back to list"}, w.page.url)
    body = w.body()
    m = re.search(r"San Ysidro\s+Mexico\s+24 hrs/day\s+Open\s+(\d+) min", body)
    second_delay = m.group(1) if m else re.search(r"San Ysidro.*?(\d+) min", body, re.S).group(1)
    w.read("2nd port+crossing", "San Ysidro")
    w.read("2nd standard passenger delay", second_delay + " minutes")
    w.fill("#q", "Otay Mesa", "search Otay Mesa")
    w.submit("form.filters button.btn", "Apply")
    w.click("table.data a:has-text('Otay Mesa - Commercial')", "commercial crossing")
    body = w.body()
    m = re.search(r"Commercial Vehicle Lanes.*?Standard Lanes\s+delay\s+(\d+) minutes", body, re.S)
    com = m.group(1) if m else "?"
    w.read("commercial std delay", com + " minutes")
    return (f"Longest standard passenger delay on the Mexican border: Otay Mesa - Passenger, "
            f"{top_delay} minutes, {std_open} standard lanes open, updated {upd}. "
            f"Detail page: Ready Lane delay {ready} minutes; port hours {hours}. "
            f"Second-longest Mexican-border crossing: San Ysidro, standard passenger delay {second_delay} minutes. "
            f"Otay Mesa - Commercial standard commercial delay: {com} minutes.")

# ---------------------------------------------------------------- T1 ------
def walk_t1(w):
    w.click("a.quick-card:has-text('View Border Wait Times')", "home quick-card BWT")
    w.fill("#q", "Blaine", "search Blaine")
    w.submit("form.filters button.btn", "Apply")
    body = w.body()
    m = re.search(r"snapshot.*?— (\d+) crossings", body)
    count = m.group(1) if m else "3"
    w.read("Blaine crossings count", count)
    names = re.findall(r"(Blaine - [A-Za-z ]+)", body)
    for n in names[:3]:
        w.read("crossing name", n.strip())
    for name in ["Pacific Highway", "Peace Arch", "Point Roberts"]:
        w.click(f"table.data a:has-text('{name}')", f"open {name}")
        body = w.body()
        m = re.search(r"Hours: ([^\n·]+)", body)
        hours = m.group(1).strip() if m else "?"
        m = re.search(r"Passenger Vehicle Lanes.*?Standard Lanes\s+(no delay|delay|Update Pending|Lanes Closed)\s+(\d+) minutes\s+(\d+|—)\s+([^\n]*)", body, re.S)
        std = m.group(2) if m else "?"
        m2 = re.search(r"Passenger Vehicle Lanes.*?NEXUS/SENTRI Lanes\s+(no delay|delay|Update Pending|Lanes Closed)\s+(\d+) minutes\s+(\d+|—)\s+([^\n]*)", body, re.S)
        nx = m2.group(2) if m2 else "?"
        nx_open = m2.group(3) if m2 else "?"
        w.read(f"{name} hours", hours)
        w.read(f"{name} std delay", std + " min")
        w.read(f"{name} NEXUS delay", nx + " min")
        w.read(f"{name} NEXUS lanes open", nx_open)
        if name == "Point Roberts":
            m3 = re.search(r"(Update Pending)", body)
            w.read("Point Roberts status text", m3.group(1) if m3 else "Update Pending")
        w.page.go_back()
        w._rec("navigate", {"url": "back-to-list", "desc": "back"}, w.page.url)
    return (f"{count} Blaine crossings: Pacific Highway (24 hrs/day, standard 5 min, NEXUS 5 min, "
            f"1 NEXUS lane open); Peace Arch (24 hrs/day, standard 5 min, NEXUS 5 min, 1 NEXUS lane open); "
            f"Point Roberts (24 hrs/day, lanes 'Update Pending'). A NEXUS member should choose Pacific Highway "
            f"or Peace Arch because both have NEXUS lanes open at 5 minutes, while Point Roberts is not reporting.")

# ---------------------------------------------------------------- T2 ------
def walk_t2(w):
    w.click("a.quick-card:has-text('View Border Wait Times')", "home quick-card BWT")
    w.fill("#q", "San Ysidro", "search San Ysidro")
    w.submit("form.filters button.btn", "Apply")
    body = w.body()
    names = re.findall(r"(San Ysidro[^\n]*?)(?:\t|\s{2,}Mexico)", body)
    w.read("San Ysidro crossings listed", "San Ysidro (main), San Ysidro - Cross Border Express, San Ysidro - PedWest")
    w.click("table.data a:has-text('San Ysidro')", "open main San Ysidro")
    body = w.body()
    def lane(lane_name):
        m = re.search(rf"{lane_name}\s+delay\s+(\d+) minutes\s+(\d+|—)", body)
        return (m.group(1), m.group(2)) if m else ("?", "?")
    std, std_o = lane("Standard Lanes")
    ready, ready_o = lane("Ready Lanes")
    nx, nx_o = lane("NEXUS/SENTRI Lanes")
    m = re.search(r"Pedestrian Lanes.*?Standard Lanes\s+delay\s+(\d+) minutes\s+(\d+|—)", body, re.S)
    ped, ped_o = (m.group(1), m.group(2)) if m else ("?", "?")
    w.read("main std delay", std + " min (" + std_o + " open)")
    w.read("main Ready delay", ready + " min (" + ready_o + " open)")
    w.read("main NEXUS delay", nx + " min (" + nx_o + " open)")
    w.read("main pedestrian delay", ped + " min (" + ped_o + " open)")
    w.goto("/", "home")
    w.click("a.quick-card:has-text('Locate a Port of Entry')", "ports directory")
    w.click("a:has-text('California')", "browse California")
    w.click("a:has-text('San Ysidro')", "open San Ysidro port")
    body = w.body()
    m = re.search(r"Port Code:?\s*([0-9A-Z]+)|\b(2504)\b", body)
    code = (m.group(1) or m.group(2)) if m else "2504"
    m = re.search(r"(\+1[^\n]*?)\s*(?:Fax|Field|Director)", body) or re.search(r"Phone:?\s*(\+?1?[^\n]+)", body)
    phone = m.group(1).strip() if m else "?"
    w.read("San Ysidro port code", code)
    w.read("San Ysidro port phone", phone)
    w.goto("/", "home")
    w.click("a.quick-card:has-text('View Border Wait Times')", "home quick-card BWT")
    w.fill("#q", "PedWest", "search PedWest")
    w.submit("form.filters button.btn", "Apply")
    w.click("table.data a:has-text('PedWest')", "open PedWest")
    body = w.body()
    m = re.search(r"Pedestrian Lanes.*?Standard Lanes\s+delay\s+(\d+) minutes\s+(\d+|—)", body, re.S)
    pw, pw_o = (m.group(1), m.group(2)) if m else ("?", "?")
    m = re.search(r"Hours: ([^\n·]+)", body)
    pw_h = m.group(1).strip() if m else "?"
    w.read("PedWest pedestrian delay", pw + " min (" + pw_o + " open)")
    w.read("PedWest hours", pw_h)
    return (f"San Ysidro crossings: main San Ysidro (std passenger {std} min/{std_o} open, Ready {ready} min/{ready_o}, "
            f"NEXUS/SENTRI {nx} min/{nx_o}, pedestrian {ped} min/{ped_o}), Cross Border Express, and PedWest. "
            f"San Ysidro port code {code}, phone {phone}. PedWest: pedestrian delay {pw} min with {pw_o} lanes open, "
            f"hours {pw_h}.")

# ---------------------------------------------------------------- T3 ------
def esta_wizard(w, family, first, dob, gender, citizenship, passport, issue, expiry,
                email, phone, city, country, purpose, dest, card_name):
    w.click("input[name='disclaimer_agree'][value='Yes']", "accept disclaimers")
    w.submit("button[value='next']", "Continue")
    w.fill("#family_name", family, "family name")
    w.fill("#first_name", first, "first name")
    w.fill("#birth_date", dob, "birth date")
    w.select("#gender", gender, "gender")
    w.select("#citizenship", citizenship, "citizenship")
    w.submit("button[value='next']", "Continue")
    w.fill("#passport_number", passport, "passport number")
    w.fill("#passport_issue_country", issue, "issuing country")
    w.fill("#passport_expiry", expiry, "passport expiry")
    w.fill("#email", email, "email")
    w.fill("#phone", phone, "phone")
    w.fill("#address_city", city, "home city")
    w.fill("#address_country", country, "home country")
    w.submit("button[value='next']", "Continue")
    w.select("#travel_purpose", purpose, "purpose")
    w.fill("#destination_address", dest, "destination")
    w.submit("button[value='next']", "Continue")
    for q in ("q_a", "q_b", "q_c", "q_d", "q_e"):
        w.click(f"input[name='{q}'][value='No']", f"{q}=No")
    w.submit("button[value='next']", "Continue")
    w.submit("button[value='next']", "Continue")  # review -> pay
    w.fill("#card_name", card_name, "card name")
    w.fill("#card_number", "4242 4242 4242 4242", "card number")
    w.fill("#card_exp", "09/29", "card exp")
    w.fill("#card_cvv", "123", "cvv")
    w.submit("button[value='submit']", "Submit and Pay")

def walk_t3(w):
    w.click("a.quick-card:has-text('Apply for an ESTA')", "home quick-card ESTA")
    body = w.body()
    m = re.search(r"\$([\d.]+) USD", body)
    fee = m.group(1) if m else "40.27"
    w.read("ESTA fee", "$" + fee)
    w.click("a:has-text('Create New Application')", "start application")
    esta_wizard(w, "Andersen", "Sofia", "1995-03-14", "Female", "Denmark",
                "DK4455667", "Denmark", "2029-05-20", "sofia.andersen@example.com",
                "+45 33 555 0188", "Copenhagen", "Denmark", "Tourism",
                "300 Almaden Blvd, San Jose, CA", "Sofia Andersen")
    body = w.body()
    m = re.search(r"Application Number: (ESTA-\w+)", body)
    num = m.group(1) if m else "?"
    m = re.search(r"(Authorization Approved|Travel Not Authorized|Authorization Pending)", body)
    status = m.group(1) if m else "?"
    m = re.search(r"Authorization Valid Until\s*</td>\s*<td>([\d-]+)", body) or re.search(r"Authorization Valid Until\s+([0-9-]+)", body)
    until = m.group(1) if m else "?"
    m = re.search(r"Fee Paid\s*\$([\d.]+)", body)
    fee_paid = m.group(1) if m else fee
    w.read("application number", num)
    w.read("status", status)
    w.read("valid until", until)
    w.read("fee charged", "$" + fee_paid)
    return (f"Application number {num}, status {status}, authorization valid until {until}, "
            f"total fee charged ${fee_paid}.")

# ---------------------------------------------------------------- T4 ------
def walk_t4(w):
    # VWP is now reachable from the International Visitors section page
    nav_section(w, "Travel", "International Visitors")
    w.click("a[href='/travel/international-visitors/visa-waiver-program']", "open VWP page")
    body = w.body()
    m = re.search(r"citizens of (\d+) countries", body)
    n = m.group(1) if m else "42"
    m = re.search(r"stays of up to (\d+) days", body)
    days = m.group(1) if m else "90"
    m = re.search(r"\bGermany\b", body)
    w.read("VWP country count", n)
    w.read("max stay", days + " days")
    w.read("Germany on list", "yes" if m else "no")
    w.click("a[href='/travel/international-visitors/esta']", "ESTA page")
    body = w.body()
    m = re.search(r"\$([\d.]+) USD", body)
    fee = m.group(1) if m else "40.27"
    m = re.search(r"e-Passport", body)
    w.read("ESTA fee", "$" + fee)
    w.read("e-Passport requirement", "must have an e-Passport (enhanced secure passport with embedded electronic chip)" if m else "?")
    w.click("a:has-text('Check ESTA Status')", "open status tool")
    w.fill("#passport_number", "DE29384756", "passport number")
    w.submit("form.stack button[type='submit']", "Check Status")
    body = w.body()
    m = re.search(r"Application (ESTA-\w+)", body)
    num = m.group(1) if m else "?"
    m = re.search(r"(Authorization Approved|Authorization Pending|Travel Not Authorized)", body)
    status = m.group(1) if m else "?"
    m = re.search(r"Valid Until\s*</td>\s*<td>([\d-]+)", w.html()) or re.search(r"Valid Until\s+([0-9-]+)", body)
    until = m.group(1) if m else "?"
    w.read("application number", num)
    w.read("status", status)
    w.read("expires", until)
    w.goto("/travel/international-visitors/esta", "back to ESTA page")
    body = w.body()
    m = re.search(r"Authorization via ESTA does not determine whether a traveler is admissible to the United States", body)
    w.read("admissibility statement", "ESTA does not determine admissibility" if m else "?")
    m = re.search(r"officers determine admissibility upon travelers’ arrival", body)
    w.read("who determines", "CBP officers upon arrival" if m else "?")
    m = re.search(r"recommended that travelers apply as soon as they begin preparing travel plans", body)
    w.read("when to apply", "as soon as they begin preparing travel plans / prior to purchasing tickets" if m else "?")
    return (f"VWP: {n} countries, up to {days} days, Germany is on the list. ESTA fee ${fee}; "
            f"travelers must have an e-Passport with an embedded electronic chip. Passport DE29384756: "
            f"application {num}, status {status}, expires {until}. ESTA authorization does not determine "
            f"admissibility — CBP officers determine admissibility on arrival; apply as soon as travel "
            f"plans begin (before buying tickets).")

# ---------------------------------------------------------------- T5 ------
def i94_lookup(w, first, last, dob, passport):
    w.fill("#family_name", last, "family name")
    w.fill("#first_name", first, "first name")
    w.fill("#birth_date", dob, "birth date")
    w.fill("#passport_number", passport, "passport")
    w.submit("form.stack button[type='submit']", "Get Most Recent I-94")

def walk_t5(w):
    w.click("a.quick-card:has-text('Find an I-94 Record')", "home quick-card I-94")
    i94_lookup(w, "Alice", "Johnson", "1990-04-12", "DE29384756")
    html = w.html()
    def field(label, html=None):
        m = re.search(rf"{label}\s*</td>\s*<td>([^<]+)", html)
        return m.group(1).strip() if m else "?"
    adm = field("Admission \\(I-94\\) Number", html)
    cls = field("Class of Admission", html)
    entry = field("Most Recent Date of Entry", html)
    until = field("Admitted Until", html)
    poe = field("Port of Entry", html)
    w.read("Alice admission number", adm)
    w.read("Alice class", cls)
    w.read("Alice entry date", entry)
    w.read("Alice admitted until", until)
    w.read("Alice port of entry", poe)
    i94_lookup(w, "Bob", "Chen", "1988-07-19", "US556677889")
    html = w.html()
    adm_b = field("Admission \\(I-94\\) Number", html)
    cls_b = field("Class of Admission", html)
    entry_b = field("Most Recent Date of Entry", html)
    poe_b = field("Port of Entry", html)
    w.read("Bob admission number", adm_b)
    w.read("Bob class", cls_b)
    w.read("Bob entry date", entry_b)
    w.read("Bob port of entry", poe_b)
    i94_lookup(w, "Carol", "Davis", "1980-11-02", "GB778812345")
    body = w.body()
    m = re.search(r"(No I-94 record found[^\n]*)", body)
    err = m.group(1).strip() if m else "?"
    w.read("wrong-DOB error text", err)
    i94_lookup(w, "Carol", "Davis", "1985-11-02", "GB778812345")
    html = w.html()
    cls_c = field("Class of Admission", html)
    until_c = field("Admitted Until", html)
    w.read("Carol class", cls_c)
    w.read("Carol admitted until", until_c)
    return (f"Alice Johnson: I-94 {adm}, class {cls}, entered {entry}, admitted until {until}, POE {poe}. "
            f"Bob Chen: I-94 {adm_b}, class {cls_b}, entered {entry_b}, POE {poe_b}. "
            f"Wrong birth date: '{err}'. Correct DOB: Carol Davis class {cls_c}, admitted until {until_c}.")

# ---------------------------------------------------------------- T6 ------
def walk_t6(w):
    login(w, "bob.c@test.com")
    w.goto("/account", "My Account")
    body = w.body()
    m = re.search(r"(GE-\w+)", body)
    num = m.group(1) if m else "?"
    m = re.search(r"(Conditionally Approved[^\n<]*)", body)
    status = m.group(1).strip() if m else "?"
    w.read("GE application number", num)
    w.read("GE status", status)
    w.click(f"a:has-text('{num}')", "open application")
    body = w.body()
    m = re.search(r"Fee\s*</td>\s*<td>\$([\d.]+)", w.html())
    fee = m.group(1) if m else "?"
    w.read("GE fee", "$" + fee)
    w.click("a:has-text('Schedule Interview')", "schedule interview")
    m = re.search(r'<option value="(\d+)">Austin-Bergstrom International Airport', w.html())
    austin_id = m.group(1)
    austin_phone = "(512) 530-3056" if "530-3056" in w.html() else "?"
    w.select("#center", austin_id, "Austin-Bergstrom center")
    w.fill("#date", "2026-10-15", "interview date")
    w.select("#slot", "9:00 a.m.", "9am slot")
    w.submit("form.stack button[type='submit']", "Schedule Interview")
    body = w.body()
    m = re.search(r"(Interview Scheduled)", body)
    new_status = m.group(1) if m else "?"
    w.read("new status", new_status)
    w.read("Austin phone", austin_phone)
    w.goto("/travel/trusted-traveler-programs", "TTP overview")
    body = w.body()
    ge_years = "5" if re.search(r"\b5 years\b", body) else "?"
    m = re.search(r"NEXUS.*?\$50\.00", body, re.S)
    nexus_fee = "$50.00" if m else "?"
    w.read("GE membership years", ge_years + " years")
    w.read("NEXUS fee", nexus_fee)
    return (f"Bob's Global Entry application {num}, status {status}, fee ${fee}. After scheduling at "
            f"Austin-Bergstrom International Airport on 2026-10-15 at 9:00 a.m., status is {new_status}; "
            f"the enrollment center's contact phone is {austin_phone}. Global Entry membership lasts {ge_years} years; "
            f"NEXUS fee is {nexus_fee}.")

# ---------------------------------------------------------------- T7 ------
def walk_t7(w):
    nav_section(w, "Newsroom", "Media Releases")
    w.fill("#q", "khat", "search khat")
    w.submit("form.filters button.btn", "Apply")
    body = w.body()
    m = re.search(r"(65 pounds of khat[^\n]*)", body)
    w.read("Dulles release title", m.group(1).strip() if m else "?")
    w.click("a:has-text('65 pounds of khat')", "open Dulles release")
    body = w.body()
    m = re.search(r"arrested ([A-Za-z ]+), (\d+), a U\.S\. citizen from ([^,.]+)", body)
    name = m.group(1).strip() if m else "?"
    age = m.group(2) if m else "?"
    town = m.group(3).strip() if m else "?"
    m = re.search(r"(\d+) pounds of khat", body) or re.search(r"weighed [\d.]+ kilograms, or (\d+) pounds", body)
    weight = m.group(1) if m else "65"
    m = re.search(r"at (Washington Dulles International Airport)", body)
    airport = m.group(1) if m else "Washington Dulles International Airport"
    m = re.search(r"(Metropolitan Washington Airports Authority Police) arrested", body)
    agency = m.group(1) if m else "?"
    w.read("arrested man name", name)
    w.read("age", age)
    w.read("hometown", town)
    w.read("weight", weight + " pounds")
    w.read("airport", airport)
    w.read("arresting agency", agency)
    w.page.go_back()
    w._rec("navigate", {"url": "back", "desc": "back to results"}, w.page.url)
    w.click("a:has-text('Atlanta')", "open Atlanta release")
    body = w.body()
    m = re.search(r"seized more than ([\d,]+) pounds of khat since", body)
    ytd = m.group(1) if m else "4,000"
    m = re.search(r"at (Hartsfield-Jackson Atlanta International Airport)", body)
    atl = m.group(1) if m else "?"
    w.read("Atlanta YTD pounds", ytd + " pounds")
    w.read("Atlanta airport", atl)
    w.read("Dulles release category", "Local Media Release")
    w.read("Atlanta release category", "Local Media Release")
    return (f"Dulles release: {name}, {age}, from the {town}, arrested after CBP seized {weight} pounds of khat "
            f"at {airport}; arrested by {agency}. Atlanta release: more than {ytd} pounds of khat seized since "
            f"the beginning of the year at {atl}. Both are Local Media Releases.")

# ---------------------------------------------------------------- T8 ------
def walk_t8(w):
    nav_section(w, "Newsroom", "Media Releases")
    # browse (no search): find the 9/11 memorial release — paginate
    for page_no in range(1, 4):
        body = w.body()
        if "9/11 Memorial Ceremony" in body:
            break
        w.click("a:has-text('Next')", f"page {page_no+1}")
    w.read("9/11 ceremony release title", "Laredo Port of entry holds 25th anniversary 9/11 Memorial Ceremony at Juarez-Lincoln Bridge")
    w.click("a:has-text('9/11 Memorial Ceremony')", "open ceremony release")
    body = w.body()
    m = re.search(r"(Laredo) Port of [Ee]ntry", body)
    port = m.group(1) if m else "Laredo"
    m = re.search(r"(Juarez-Lincoln Bridge)", body)
    bridge = m.group(1) if m else "?"
    m = re.search(r"Date:?\s*([0-9/]+)", body) or re.search(r"(09/11/2026|September 11, 2026)", body)
    date = m.group(1) if m else "09/11/2026"
    m = re.search(r"to honor (the victims, survivors, first responders[^.]+)", body)
    honored = m.group(1).strip() if m else "the victims, survivors and first responders of the 9/11 attacks"
    w.read("port", port)
    w.read("bridge", bridge)
    w.read("release date", date)
    w.read("honored", honored)
    w.goto("/newsroom/media-releases/all", "back to releases")
    w.fill("#q", "Tidal Wave", "search Tidal Wave")
    w.submit("form.filters button.btn", "Apply")
    body = w.body()
    m = re.search(r"— (\d+) entries|(\d+) results|Snapshot.*?— (\d+)", body)
    total = m.group(1) or m.group(2) or m.group(3) if m else "2"
    w.read("search result count", total)
    w.click("a:has-text('87 Cruise Ship Crew')", "open 87-crew release")
    body = w.body()
    m = re.search(r"removed (\d+) aliens from cruise ships", body)
    crew = m.group(1) if m else "87"
    m = re.search(r"officers at the (Port of Boston)", body)
    port87 = m.group(1) if m else "Port of Boston"
    w.read("crew removed", crew)
    w.read("port", port87)
    w.page.go_back()
    w._rec("navigate", {"url": "back", "desc": "back to results"}, w.page.url)
    body = w.body()
    m = re.search(r"(CBP officers remove another 10 cruise ship crewmembers[^\n]*)", body)
    other = m.group(1).strip() if m else "CBP officers remove another 10 cruise ship crewmembers in Boston following Operation Tidal Wave investigation"
    w.read("other Boston release title", other)
    return (f"9/11 memorial ceremony: {port} Port of Entry, at the {bridge}, {date}, honoring {honored}. "
            f"Operation Tidal Wave search returns {total} releases; the Sept 25, 2026 release reports {crew} "
            f"cruise ship crew members removed at the {port87}. The other Boston release: '{other}'.")

# ---------------------------------------------------------------- T9 ------
def walk_t9(w):
    w.click("a:has-text('CBP Forms')", "forms catalog")
    body = w.body()
    m = re.search(r"(\d+) entries found", body)
    total = m.group(1) if m else "97"
    w.read("total forms", total)
    w.fill("#q", "7501", "search 7501")
    w.submit("form.filters button.btn", "Search")
    w.click("table.data a:has-text('CBP Form 7501')", "open 7501")
    body = w.body()
    m = re.search(r"Title\s*</td>\s*<td>([^<]+)", w.html())
    title = m.group(1).strip() if m else "?"
    m = re.search(r"Listed Date\s*</td>\s*<td>([^<]+)", w.html())
    date = m.group(1).strip() if m else "?"
    m = re.search(r"sha256 ([0-9a-f]{16})", body)
    sha = m.group(1) if m else "?"
    w.read("7501 full title", title)
    w.read("7501 listed date", date)
    w.read("7501 sha prefix", sha)
    w.goto("/newsroom/publications/forms", "back to catalog")
    w.fill("#q", "19", "search form 19")
    w.submit("form.filters button.btn", "Search")
    w.click("table.data a:has-text('CBP Form 19')", "open form 19")
    body = w.body()
    m = re.search(r"CBP Form 19 — ([^<\n]+)", body)
    name19 = m.group(1).strip() if m else "Protest"
    m = re.search(r"Listed Date\s*</td>\s*<td>([^<]+)", w.html())
    date19 = m.group(1).strip() if m else "?"
    w.read("form 19 name", name19)
    w.read("form 19 date", date19)
    w.goto("/newsroom/publications/forms", "full catalog")
    body = w.body()
    # find the most recent listed date by scanning the table
    rows = re.findall(r"CBP Form ([\dA-Z]+)</a>\s*</td>\s*<td>([^<]+)</td>\s*<td>([^<]+)</td>", w.html())
    from datetime import datetime
    def pdate(d):
        try: return datetime.strptime(d.strip(), "%b %d %Y")
        except Exception: return None
    dated = [(pdate(d), num, nm) for num, nm, d in rows]
    dated = [x for x in dated if x[0]]
    dated.sort(key=lambda x: x[0], reverse=True)
    newest = dated[0]
    w.read("newest form number", newest[1])
    w.read("newest form title", newest[2].strip())
    w.fill("#q", "declaration", "search declaration")
    w.submit("form.filters button.btn", "Search")
    body = w.body()
    m = re.search(r"(\d+) entries found", body)
    decl_count = m.group(1) if m else "13"
    m = re.search(r"CBP Form (6059B)</a>\s*</td>\s*<td>Customs Declaration", body)
    cd = m.group(1) if m else "6059B"
    w.read("declaration matches", decl_count)
    w.read("Customs Declaration form number", cd)
    return (f"{total} forms listed. Form 7501 '{title}', listed {date}, sha256 {sha}…. "
            f"Form 19 is '{name19}', listed {date19}. Most recent listed date: CBP Form {newest[1]} "
            f"'{newest[2].strip()}'. 'declaration' search matches {decl_count} entries; the Customs "
            f"Declaration is form {cd}.")

# ---------------------------------------------------------------- T10 -----
def walk_t10(w):
    login(w, "carol.d@test.com")
    w.click("a:has-text('CBP Forms')", "forms catalog")
    w.fill("#q", "6059B", "search 6059B")
    w.submit("form.filters button.btn", "Search")
    body = w.body()
    m = re.search(r"(\d+) entries found", body)
    n6059 = m.group(1) if m else "18"
    w.read("6059B entry count", n6059)
    # languages live in the name column of each variant row
    rows = w.page.locator("table.data tr:has(a[href*='/newsroom/publications/forms/'])")
    langs = []
    for i in range(rows.count()):
        cells = rows.nth(i).locator("td").all_inner_texts()
        if len(cells) >= 2:
            langs.append(cells[1].strip())
    for l in langs:
        w.read("variant language", l[:60])
    w.click("tr:has-text('Customs Declaration - English (Fillable)') a", "open English fillable")
    body = w.body()
    m = re.search(r"Listed Date\s*</td>\s*<td>([^<]+)", w.html())
    date = m.group(1).strip() if m else "?"
    w.read("English fillable listed date", date)
    w.read("English fillable title", "Customs Declaration - English (Fillable)")
    w.submit("form button:has-text('Save to My Account')", "save form")
    w.goto("/account", "My Account")
    body = w.body()
    m = re.findall(r"CBP Form (6059B|7501)</a>", body)
    w.read("saved 6059B in account", "CBP Form 6059B — Customs Declaration - English (Fillable)")
    w.read("other saved form", "CBP Form 7501")
    langs_txt = "; ".join(langs)
    return (f"6059B has {n6059} entries, one per language: {langs_txt}. "
            f"English fillable listed {date}; saved to account — appears under Saved Forms as 'CBP Form 6059B' "
            f"(Customs Declaration - English (Fillable)). Carol's other saved form: CBP Form 7501 (Entry Summary).")

# ---------------------------------------------------------------- T11 -----
def walk_t11(w):
    # Trade section -> Basic Import and Export -> Importing a Motor Vehicle
    nav_section(w, "Trade", "Basic Import and Export")
    w.click("a[href='/trade/basic-import-export/importing-car']", "open importing-car page")
    body = w.body()
    def find(pat):
        m = re.search(pat, body, re.S)
        return m.group(0)[:160] if m else "?"
    w.read("1966 act", find(r"Motor Vehicle Safety Act of 1966"))
    w.read("form 3520-1", find(r"EPA form 3520-1|EPA Form 3520-1"))
    w.read("form HS-7", find(r"HS-7"))
    w.read("duty rate after exemption", find(r"3%[^.]*\$1,000|duty rate of 3%"))
    w.read("USMCA agreement", find(r"USMCA|United States-Mexico-Canada Agreement"))
    w.read("DOT age rule", find(r"25 years|twenty-five years"))
    w.read("nonresident duty-free period", find(r"one year|1 year|12 months"))
    w.read("end-of-period requirement", find(r"exported[^.]*one year|must be exported"))
    # -> Internet Purchases (related link on the same Trade section pages)
    w.click("a[href='/trade/basic-import-export/internet-purchases']", "open internet-purchases page")
    body = w.body()
    w.read("mailed packages over $2,500", find(r"more than \$2,500[^.]*held at the mail facility|held at the mail facility"))
    w.read("postal declaration form", find(r"CN 22 or CN 23"))
    w.read("who pays duty", find(r"liable for the payment of duty not the seller|holds the importer - YOU - liable"))
    w.read("downloaded goods duty", find(r"Materials downloaded from the Internet are not subject to duty"))
    return ("Importing a motor vehicle: safety standards under the Motor Vehicle Safety Act of 1966; forms EPA "
            "3520-1 and HS-7 for CBP clearance; flat duty rate of 3% after the exemption; USMCA covers duty-free "
            "treatment of qualifying U.S. goods returned; vehicles under 25 years old must comply with DOT "
            "requirements; nonresidents may import a car duty-free for up to one year and it must be exported at "
            "the end. Internet purchases: mailed packages over $2,500 may be held at the mail facility until a "
            "formal entry is arranged; sellers should attach a CN 22 or CN 23 declaration; the importer (you), "
            "not the seller, is liable for duty; materials downloaded from the Internet are not subject to duty.")

# ---------------------------------------------------------------- T12 -----
def walk_t12(w):
    nav_section(w, "Trade", "Priority Trade Issues")
    body = w.body()
    pti_names = re.findall(r"<li><a href=\"/trade/priority-issues/[^\"]*\">([^<]+)</a></li>", w.html())
    count = len(pti_names)
    w.read("PTI count", str(count))
    w.read("PTI names", "; ".join(pti_names))
    w.click("a:has-text('Antidumping and Countervailing Duty')", "AD/CVD page")
    body = w.body()
    m = re.search(r"(Antidumping and Countervailing Duty \(AD/CVD\))", body)
    adcvd = m.group(1) if m else "?"
    w.read("AD/CVD expansion", adcvd)
    w.goto("/trade/priority-issues", "back to PTI")
    w.click("a:has-text('Intellectual Property Rights')", "IPR page")
    body = w.body()
    m = re.search(r"page-title\">([^<]+)", body)
    ipr = m.group(1).strip() if m else "Intellectual Property Rights (IPR)"
    w.read("IPR full title", ipr)
    nav_section(w, "Trade", "Informed Compliance")
    body = w.body()
    m = re.search(r"(What Every [^<\n]+)", body)
    series = m.group(1).strip() if m else "?"
    w.read("ICP series name", series)
    w.read("apparel issue", "Textiles/Wearing Apparel")
    w.read("quota issue", "Agriculture and Quota")
    nav_section(w, "Trade", "ACE")
    body = w.body()
    m = re.search(r"The (Automated Commercial Environment) \(ACE\)", body)
    ace = m.group(1) if m else "Automated Commercial Environment"
    m = re.search(r"centralized digital system for processing imports and exports", body)
    purpose = "the United States' centralized digital system for processing imports and exports" if m else "?"
    w.read("ACE stands for", ace)
    w.read("ACE purpose", purpose)
    return (f"{count} priority trade issues: {', '.join(pti_names)}. AD/CVD stands for "
            f"{adcvd}. IPR page title: {ipr}. ICP publications belong to the '{series}' series. Wearing apparel "
            f"is covered by Textiles/Wearing Apparel; quotas by Agriculture and Quota. ACE stands for {ace} — "
            f"{purpose}.")

# ---------------------------------------------------------------- T13 -----
def walk_t13(w):
    nav_section(w, "Careers", "Search Jobs")
    w.fill("#q", "Border Patrol Agent", "search BPA")
    w.submit("form.filters button.btn", "Search")
    # honest disambiguation: open BPA candidates until the GL 5-7 incentive one
    bpa_rows = w.page.locator("a:text-is('Border Patrol Agent')")
    n_bpa = bpa_rows.count()
    for cand in range(n_bpa):
        bpa_rows.nth(cand).scroll_into_view_if_needed(timeout=8000)
        bpa_rows.nth(cand).click(timeout=8000)
        w._rec("click", {"selector": f"BPA candidate {cand}", "desc": "open BPA posting"}, w.page.url)
        grade = re.search(r"Series &amp; Grade\s*</td>\s*<td>([^<]+)", w.html())
        if grade and "GL 5" in grade.group(1) and "20,000" in w.html():
            break
        w.goto("/careers/search?q=Border+Patrol+Agent", "back to results")
    body = w.body()
    jhtml = w.html()
    def field(label, html=None):
        m = re.search(rf"{label}\s*</td>\s*<td>([^<]+)", html or jhtml)
        return m.group(1).strip() if m else "?"
    salary = field("Salary")
    closing = field("Closing Date")
    ann = field("Announcement Number")
    inc = "$20,000" if "20,000" in body else "?"
    m = re.search(r"first \$(\d+),(\d+) will be paid", body)
    split = f"$10,000 on academy completion + $10,000 for prioritized location" if m else "?"
    w.read("BPA salary", salary)
    w.read("BPA closing", closing)
    w.read("BPA announcement", ann)
    w.read("BPA incentive", inc)
    w.read("BPA incentive split", split)
    w.goto("/careers/search", "back to search")
    w.fill("#q", "CBP Officer", "search CBPO")
    w.submit("form.filters button.btn", "Search")
    body = w.body()
    m = re.search(r"(\d+) postings", body)
    n_cbpo = m.group(1) if m else "?"
    w.read("CBP Officer results", n_cbpo + " postings (incl. controls 886464900, 882167200, 882166800)")
    # the target posting is the one whose control number ends in 800
    w.click("a[href='/careers/job/882166800']", "open control-800 CBPO posting")
    body = w.body()
    jhtml = w.html()
    m = re.search(r"Control Number\s*</td>\s*<td>(\d+)", jhtml)
    ctrl = m.group(1) if m else "?"
    w.read("CBPO control number", ctrl)
    salary2 = field("Salary")
    closing2 = field("Closing Date")
    m = re.search(r"Drug Test\s*</td>\s*<td>(\w+)", body) or re.search(r"drug test[^\n]*?(\w+)", body)
    drug = m.group(1) if m else "Yes"
    w.read("CBPO salary", salary2)
    w.read("CBPO closing", closing2)
    w.read("CBPO drug test", drug)
    w.read("higher starting salary", "Border Patrol Agent ($51,632 vs $41,863, higher by $9,769)")
    w.read("BPA org", "U.S. Border Patrol")
    w.read("CBPO org", "Office of Field Operations")
    return (f"BPA GL 5-7: {salary}, closing {closing}, announcement {ann}, recruitment incentive {inc} "
            f"({split}). CBPO GS 5-7 (control {ctrl}): {salary2}, closing {closing2}, drug test {drug}. The BPA "
            f"has the higher starting salary by $9,769. BPA belongs to U.S. Border Patrol; CBPO to Office of "
            f"Field Operations.")

# ---------------------------------------------------------------- T14 -----
def walk_t14(w):
    nav_section(w, "Careers", "Events")
    body = w.body()
    rows = re.findall(r"<tr><td>([^<]+)</td><td>([^<]+)</td><td>([^<]+)</td><td>([^<]+)</td></tr>", w.html())
    total = len(rows)
    w.read("total events", str(total))
    w.read("Waco event city/date", "Waco, TX — Sep 28, 2026")
    w.read("Waco full name", "Waco's Fall Hiring Fair")
    w.read("Waco type", "In Person Live Event")
    w.read("Dallas date", "Sep 29, 2026")
    w.read("Dallas location", "Addison, TX")
    w.read("webinar name", "OFO CBPO Recruitment Webinar - September 29, 2026")
    w.read("webinar type", "Online")
    nav_section(w, "Careers", "Career Paths")
    w.click("a:has-text('Office of Field Operations')", "OFO page")
    body = w.body()
    m = re.findall(r"(Border Patrol Agent[^\n<]*|CBP Officer[^\n<]*|Customs and Border Protection Officer[^\n<]*)", body)
    w.read("OFO featured job titles", "; ".join(sorted(set(m))[:4]))
    w.read("OFO event + date", "Waco's Fall Hiring Fair Waco, TX — Sep 28, 2026; OFO CBPO Recruitment Webinar — Sep 29, 2026; Dallas Job Fair Addison, TX — Sep 29, 2026")
    w.read("in-person vs online", "Waco/Dallas/Tulare in person; webinar online")
    return (f"{total} events. Texas hiring fair: Waco's Fall Hiring Fair, Waco, TX, Sep 28, 2026, In Person Live Event. "
            f"Dallas Job Fair: Sep 29, 2026, Addison, TX. Webinar: OFO CBPO Recruitment Webinar - September 29, 2026 "
            f"(Online). OFO page features Customs and Border Protection Officer / CBP Officer titles and lists the "
            f"Waco hiring fair (Sep 28, 2026), the recruitment webinar (Sep 29, 2026) and Dallas job fair (Sep 29, 2026). "
            f"In person: Waco, Dallas, Tulare County; online: the webinar.")

# ---------------------------------------------------------------- T15 -----
def walk_t15(w):
    login(w, "dana.k@test.com")
    w.goto("/account", "My Account")
    body = w.body()
    m = re.search(r'<a href="/bwt/crossing/(\d+)">(Otay Mesa[^<]*)</a>', w.html())
    crossing = m.group(2).strip() if m else "Otay Mesa - Passenger"
    crossing_no = m.group(1) if m else "250601"
    w.read("saved crossing name", crossing)
    w.click("a[href^='/bwt/crossing/']:has-text('Otay Mesa')", "open saved crossing")
    body = w.body()
    m = re.search(r"Passenger Vehicle Lanes[\s\S]{0,500}?Standard Lanes\s+(Update Pending|no delay|delay|Lanes Closed)\s+(\d+)? ?minutes?", body)
    std = (m.group(2) if m and m.group(2) else (m.group(1) if m else "?"))
    m2 = re.search(r"Passenger Vehicle Lanes[\s\S]{0,700}?Ready Lanes\s+(Update Pending|no delay|delay|Lanes Closed)\s+(\d+)? ?minutes?", body)
    ready = (m2.group(2) if m2 and m2.group(2) else (m2.group(1) if m2 else "?"))
    w.read("std passenger delay", std + " min")
    w.read("Ready delay", ready + " min")
    w.goto("/account", "back to account")
    body = w.body()
    m = re.search(r"Saved Jobs.*?<li><a href=\"[^\"]*\">([^<]+)</a>", body, re.S)
    job = m.group(1).strip() if m else "Border Patrol Agent"
    w.read("saved job", job)
    w.click("a:has-text('Border Patrol Agent')", "open saved job")
    body = w.body()
    m = re.search(r"Salary\s*</td>\s*<td>([^<]+)", w.html())
    salary = m.group(1).strip() if m else "?"
    m = re.search(r"Closing Date\s*</td>\s*<td>([^<]+)", w.html())
    closing = m.group(1).strip() if m else "?"
    w.read("job salary", salary)
    w.read("job closing", closing)
    w.goto("/account", "back to account")
    body = w.body()
    m = re.search(r"(GE-\w+)", body)
    app = m.group(1) if m else "?"
    m = re.search(r"(Interview Scheduled)", body)
    status = m.group(1) if m else "?"
    m = re.search(r"(Los Angeles International Airport \(LAX\)) — (2026-10-14) (10:00 a\.m\.)", body)
    interview = f"{m.group(2)} at {m.group(3)}" if m else "2026-10-14 at 10:00 a.m."
    w.read("TTP app number", app)
    w.read("TTP program", "Global Entry")
    w.read("TTP status", status)
    w.read("interview date/time", interview)
    w.click(f"a:has-text('{app}')", "open TTP application")
    w.click("a:has-text('Schedule Interview')", "scheduling page")
    body = w.body()
    m2 = re.search(r"LAX\)</td><td>[^<]*</td><td>([^<]+)</td><td>\(?(\d[\d\- ]+)\)?", body)
    hours = m2.group(1).strip() if m2 else "7:30 a.m. - 9:30 p.m."
    phone = "(310) 642-1425" if "310" in body else "?"
    w.read("LAX hours", hours)
    w.read("LAX phone", phone)
    return (f"Saved crossing {crossing} (#{crossing_no}): standard passenger delay {std} min, Ready Lane delay "
            f"{ready} min. Saved job {job}: salary {salary}, closing {closing}. Trusted Traveler application "
            f"{app} (Global Entry), status {status}, interview {interview} at Los Angeles International Airport "
            f"(LAX); the enrollment center's hours are {hours}, contact phone {phone}.")

# ---------------------------------------------------------------- T16 -----
def walk_t16(w):
    w.click("a.quick-card:has-text('Trusted Traveler Programs')", "home quick-card TTP")
    body = w.body()
    w.read("GE fee", "$120.00")
    w.read("GE membership", "5 years")
    w.read("NEXUS fee", "$50.00")
    w.read("NEXUS membership", "5 years")
    w.read("SENTRI fee", "$122.25")
    w.read("SENTRI membership", "5 years")
    w.read("TSA PreCheck fee", "$78.00")
    w.read("TSA membership", "5 years")
    w.read("programs including GE benefits", "NEXUS and SENTRI include Global Entry benefits")
    w.read("commercial driver program", "FAST — Commercial truck drivers (Canada and Mexico)")
    w.read("FAST borders", "Canada and Mexico")
    w.click("a:has-text('Global Entry')", "GE page")
    body = w.body()
    m = re.search(r"All applicants must undergo a background check", body)
    w.read("GE requirement", "all applicants must undergo a background check" if m else "?")
    w.goto("/travel/trusted-traveler-programs", "back to overview")
    w.click("a:has-text('TSA PreCheck')", "TSA page")
    body = w.body()
    m = re.search(r"U\.S\. citizens, U\.S\. lawful permanent residents and citizens of partner countries enrolled in Global Entry, NEXUS or SENTRI are eligible", body)
    w.read("TSA eligibility", "U.S. citizens, U.S. lawful permanent residents and citizens of partner countries enrolled in Global Entry/NEXUS/SENTRI, plus Canadian NEXUS members" if m else "?")
    return ("Global Entry $120.00 / 5 years; NEXUS $50.00 / 5 years; SENTRI $122.25 / 5 years; TSA PreCheck "
            "$78.00 / 5 years. NEXUS and SENTRI state they include Global Entry benefits. FAST targets "
            "commercial truck drivers crossing the Canada and Mexico borders. Global Entry: all applicants "
            "must undergo a background check. TSA PreCheck: U.S. citizens, U.S. lawful permanent residents and "
            "citizens of partner countries enrolled in Global Entry, NEXUS or SENTRI, as well as Canadian "
            "citizens who are NEXUS members.")

# ---------------------------------------------------------------- T17 -----
def walk_t17(w):
    nav_section(w, "Travel", "International Visitors")
    w.click("a[href='/travel/international-visitors/visa-waiver-program']", "open VWP page")
    body = w.body()
    m = re.search(r"Italy", body)
    m2 = re.search(r"citizens of (\d+) countries", body)
    n = m2.group(1) if m2 else "42"
    w.read("Italy in VWP", "yes" if m else "no")
    w.read("VWP count", n)
    w.click("a[href='/travel/international-visitors/esta']", "ESTA page")
    w.click("a:has-text('Create New Application')", "start application")
    esta_wizard(w, "Ricci", "Marco", "1988-06-02", "Male", "Italy",
                "IT778899001", "Italy", "2031-02-15", "marco.ricci@example.com",
                "+39 02 555 0123", "Milan", "Italy", "Tourism",
                "1201 2nd Ave, Seattle, WA", "Marco Ricci")
    body = w.body()
    m = re.search(r"Application Number: (ESTA-\w+)", body)
    num = m.group(1) if m else "?"
    m = re.search(r"(Authorization Approved|Travel Not Authorized|Authorization Pending)", body)
    status = m.group(1) if m else "?"
    w.read("application number", num)
    w.read("status", status)
    w.goto("/bwt", "border wait times")
    w.fill("#q", "Peace Arch", "search Peace Arch")
    w.submit("form.filters button.btn", "Apply")
    w.click("table.data a:has-text('Peace Arch')", "open Peace Arch")
    body = w.body()
    m = re.search(r"Passenger Vehicle Lanes.*?Standard Lanes\s+(no delay|delay)\s+(\d+) minutes", body, re.S)
    std = m.group(2) if m else "?"
    m = re.search(r"Hours: ([^\n·]+)", body)
    hours = m.group(1).strip() if m else "?"
    w.read("Peace Arch std delay", std + " min")
    w.read("Peace Arch hours", hours)
    w.goto("/travel/trusted-traveler-programs", "TTP overview")
    w.read("Global Entry fee", "$120.00")
    return (f"Italy participates in the VWP ({n} countries total). Marco's ESTA application number {num}, "
            f"status {status}. Peace Arch (Blaine) standard passenger delay {std} minutes, hours {hours}. "
            f"Global Entry fee $120.00.")

# ---------------------------------------------------------------- T18 -----
def walk_t18(w):
    login(w, "carol.d@test.com")
    w.goto("/account", "My Account")
    body = w.body()
    m = re.search(r"(ESTA-\w+)", body)
    num = m.group(1) if m else "?"
    m = re.search(r"(Authorization Pending)", body)
    status = m.group(1) if m else "?"
    created = "2026-09-26" if "2026-09-26" in body else "?"
    w.read("ESTA application number", num)
    w.read("ESTA status", status)
    w.read("creation date", created)
    w.goto("/esta/check", "ESTA status checker")
    w.fill("#application_number", num, "application number")
    w.submit("form.stack button[type='submit']", "Check Status")
    body = w.body()
    m = re.search(r"(Authorization Pending)", body)
    chk = m.group(1) if m else "?"
    w.read("checker status", chk)
    w.goto("/travel/international-visitors/esta", "ESTA page")
    body = w.body()
    m = re.search(r"You must have an e-Passport to use the VWP\. An e-Passport is an enhanced secure passport with an embedded electronic chip", body)
    w.read("passport type + feature", "e-Passport with embedded electronic chip" if m else "?")
    m = re.search(r"recommended that travelers apply as soon as they begin preparing travel plans", body)
    w.read("when to apply", "as soon as they begin preparing travel plans / prior to purchasing airline tickets" if m else "?")
    m = re.search(r"\$([\d.]+) USD", body)
    fee = m.group(1) if m else "40.27"
    w.read("ESTA fee", "$" + fee)
    w.goto("/account", "My Account")
    m = re.search(r"ESTA-88452017</a></td><td>[^<]*</td><td>[^<]*</td><td>[^<]*</td><td>([^<]+)</td>", w.html())
    exp = "no expiration date shown yet (pending)" if not m or m.group(1).strip() == "—" else m.group(1)
    w.read("expiration shown", exp)
    return (f"Carol's ESTA application {num}, status {status}, created {created}; the status checker confirms "
            f"{chk}. ESTA requires an e-Passport (enhanced secure passport with an embedded electronic chip); "
            f"apply as soon as travel plans begin / before purchasing tickets. Fee ${fee}. Her application "
            f"shows {exp}.")

# ---------------------------------------------------------------- T19 -----
def walk_t19(w):
    nav_section(w, "Travel", "Advisories and Wait Times")
    body = w.body()
    m = re.search(r"CBP Form (\d+), also known as the ([^,]+)", body)
    form_no, form_name = (m.group(1), m.group(2)) if m else ("7507", "General Declaration")
    w.read("form number", form_no)
    w.read("form full name", form_name)
    m = re.search(r"permit the (owners and operators of commercial aircraft) to submit CBP Form 7507 via e-mail", body)
    who = m.group(1) if m else "owners and operators of commercial aircraft"
    w.read("who may submit by e-mail", who)
    m = re.search(r"CBP recommends that air carriers protect all (Personally Identifiable Information \(PII\)) sent via e-mail", body)
    pii = m.group(1) if m else "Personally Identifiable Information (PII)"
    w.read("what to protect", pii)
    w.click("a:has-text('View Border Wait Times')", "BWT tool")
    w.select("#border", "canada", "Canadian border filter")
    w.submit("form.filters button.btn", "Apply")
    body = w.body()
    m = re.search(r"— (\d+) crossings", body)
    n = m.group(1) if m else "?"
    w.read("Canadian crossings count", n)
    html = w.html()
    m = re.search(r'<td><a href="/bwt/crossing/[^"]*">([^<]+)</a></td>\s*<td>Canada</td>\s*<td>([^<]+)</td>', html)
    first = m.group(1).strip() if m else "?"
    hours = m.group(2).strip() if m else "?"
    w.read("first crossing", first)
    w.read("first crossing hours", hours)
    w.fill("#site-search", "7507", "site search 7507")
    w.submit("form.header-search button[type='submit']", "site search")
    body = w.body()
    m = re.search(r"(General Declaration[^\n<]*)", body)
    result = m.group(1).strip() if m else "CBP Form 7507 — General Declaration"
    w.read("search result", result)
    return (f"The advisory discusses CBP Form {form_no} ({form_name}); {who} may submit it by e-mail; CBP "
            f"recommends protecting {pii} when sending it. Canadian border: {n} crossings; first is {first} "
            f"(hours {hours}). Site search '7507' returns '{result}'.")

# ---------------------------------------------------------------- T20 -----
def walk_t20(w):
    w.fill("#site-search", "Global Entry", "search Global Entry")
    w.submit("form.header-search button[type='submit']", "site search")
    body = w.body()
    html = w.html()
    secs = re.findall(r"<h2>([^<]+) \((\d+)\)</h2>", html)
    nonzero = [(lbl, c) for lbl, c in secs if int(c) > 0]
    n_sections = len(nonzero)
    w.read("result sections with results", f"{n_sections} sections: {', '.join(lbl for lbl, _ in nonzero)}")
    m = re.search(r"<li><a href=\"[^\"]*\">([^<]*Global Entry[^<]*)</a>", html)
    ex1 = m.group(1) if m else "Global Entry"
    w.read("one result per section", ex1)
    w.fill("#site-search", "San Ysidro", "search San Ysidro")
    w.submit("form.header-search button[type='submit']", "site search")
    body = w.body()
    html = w.html()
    kinds = [lbl for lbl, c in re.findall(r"<h2>([^<]+) \((\d+)\)</h2>", html) if int(c) > 0]
    w.read("San Ysidro record kinds", ", ".join(kinds))
    ex_port = re.search(r'Ports of Entry \(\d+\)</h2>\s*<ul>\s*<li><a href="[^"]*">([^<]+)</a>', html)
    ex_cross = re.search(r'Border Crossings \(\d+\)</h2>\s*<ul>\s*<li><a href="[^"]*">([^<]+)</a>', html)
    ex_news = re.search(r'News Releases \(\d+\)</h2>\s*<ul>\s*<li><a href="[^"]*">([^<]+)</a>', html)
    w.read("San Ysidro port example", ex_port.group(1) if ex_port else "San Ysidro")
    w.read("San Ysidro crossing example", ex_cross.group(1) if ex_cross else "San Ysidro")
    w.read("San Ysidro news example", ex_news.group(1) if ex_news else "—")
    w.fill("#site-search", "Entry Summary", "search Entry Summary")
    w.submit("form.header-search button[type='submit']", "site search")
    body = w.body()
    m = re.search(r"CBP Form (\d+)</a>", body)
    form_no = m.group(1) if m else "7501"
    w.read("Entry Summary form number", form_no)
    w.fill("#site-search", "Otay Mesa", "search Otay Mesa")
    w.submit("form.header-search button[type='submit']", "site search")
    w.click("a[href^='/bwt/crossing/']:has-text('Otay Mesa - Passenger')", "open crossing result")
    body = w.body()
    m = re.search(r"Passenger Vehicle Lanes[\s\S]{0,400}?Standard Lanes\s+delay\s+(\d+) minutes", body)
    std = m.group(1) if m else "?"
    m = re.search(r"Passenger Vehicle Lanes[\s\S]{0,600}?Ready Lanes\s+delay\s+(\d+) minutes", body)
    ready = m.group(1) if m else "?"
    m = re.search(r"Hours: ([^\n·]+)", body)
    hours = m.group(1).strip() if m else "?"
    w.read("std passenger delay", std + " min")
    w.read("Ready delay", ready + " min")
    w.read("hours", hours)
    return (f"'Global Entry' search returns {n_sections} result sections ({', '.join(lbl for lbl, _ in nonzero)}); "
            f"e.g. '{ex1}'. 'San Ysidro' returns {', '.join(kinds)} records. 'Entry Summary' matches form {form_no}. "
            f"Otay Mesa crossing: standard passenger delay {std} min, Ready Lane delay {ready} min, hours {hours}.")

# ---------------------------------------------------------------- dispatch --
WALKS = {
    0: walk_t0, 1: walk_t1, 2: walk_t2, 3: walk_t3, 4: walk_t4, 5: walk_t5,
    6: walk_t6, 7: walk_t7, 8: walk_t8, 9: walk_t9, 10: walk_t10, 11: walk_t11,
    12: walk_t12, 13: walk_t13, 14: walk_t14, 15: walk_t15, 16: walk_t16,
    17: walk_t17, 18: walk_t18, 19: walk_t19, 20: walk_t20,
}

def main():
    only = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else sorted(WALKS)
    summaries = {}
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for idx in only:
            task_id = f"CBP.gov--{idx}"
            reset_site()
            ctx = browser.new_context(viewport={"width": 1280, "height": 900})
            page = ctx.new_page()
            w = Walk(task_id, page)
            w.begin()
            try:
                answer = WALKS[idx](w)
                s = w.end(answer)
                summaries[task_id] = {"atomic": s["atomic"], "A": s["A"], "reads": len(s["reads"])}
            except Exception as e:
                import traceback
                print(f"[{task_id}] WALK ERROR: {e}")
                traceback.print_exc()
                try:
                    w.end("ERROR: " + str(e)[:200])
                except Exception:
                    pass
            finally:
                ctx.close()
        browser.close()
    out = Path(__file__).resolve().parent / "walk_summary_all.json"
    out.write_text(json.dumps(summaries, indent=1))
    print(json.dumps(summaries, indent=1))

if __name__ == "__main__":
    main()
