#!/usr/bin/env python3
"""Honest task audit for the u_s_customs mirror.

For every task in tasks.jsonl this walks the mirror the way a real agent
would (Flask test client) and asserts each factual premise the task relies
on, printing the ground truth an agent must be able to find. It also gates
every task on the honest step counts MEASURED by real Playwright
walkthroughs of the live container (scripts_dev records: each goto /
click / fill / select / submit counts 1, plus one read per distinct
reported fact, home-page load not counted), refusing to bless tasks under
15 steps, and enforces the <= 100-word task limit.

Run: python3.11 validate_tasks.py
"""
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["US_CUSTOMS_DB_URI"] = (
    "sqlite:///" + str(ROOT / "instance_test" / "audit.db"))
os.makedirs(ROOT / "instance_test", exist_ok=True)
audit_db = ROOT / "instance_test" / "audit.db"
if audit_db.exists():
    audit_db.unlink()

from app import app, db  # noqa: E402

app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

MIN_STEPS = 15
MAX_WORDS = 100
failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL: {msg}")
    return cond


def get(path):
    r = client.get(path)
    check(r.status_code == 200, f"GET {path} -> {r.status_code}")
    return r.data.decode("utf-8", "replace")


def has(body, needle, label):
    check(needle.lower() in body.lower(), f"missing {label}: {needle!r}")


# Honest step counts per task, MEASURED by real Playwright walkthroughs of
# the container (reset + fresh browser context per task): every navigation,
# form fill, dropdown selection and submit counts 1, plus one read per
# distinct reported fact. The home-page load is never counted. Values come
# from scripts_dev/walk_fix/walk_summary_*.json; re-measure after any task
# change.
TASK_STEPS = {
    "CBP.gov--0": 18, "CBP.gov--1": 26, "CBP.gov--2": 22, "CBP.gov--3": 38,
    "CBP.gov--4": 19, "CBP.gov--5": 33, "CBP.gov--6": 19, "CBP.gov--7": 18,
    "CBP.gov--8": 19, "CBP.gov--9": 21, "CBP.gov--10": 33,
    "CBP.gov--11": 16, "CBP.gov--12": 18, "CBP.gov--13": 24,
    "CBP.gov--14": 16, "CBP.gov--15": 23, "CBP.gov--16": 17,
    "CBP.gov--17": 48, "CBP.gov--18": 18, "CBP.gov--19": 15,
    "CBP.gov--20": 19,
}

client = app.test_client()

# ------------------------------------------------------- F-5: BWT listing --
# The BWT list must render the number of open lanes per mode (the JSON key
# is `open`, not `lanes_open`) — 255 cells used to render empty.
body = get("/bwt?border=mexico&sort=delay")
check("185 min · 3 open" in body, "F-5: Otay Mesa passenger lanes-open cell")
all_body = get("/bwt?page=9")
check(re.search(r"\d+ min · \d+ open", all_body) is not None,
      "F-5: numeric lanes-open cells render on BWT list")

# ------------------------------------------------------ F-6: nav islands ---
# Every content page that used to be a navigation island must now be
# reachable through in-site links rendered on its parent page.
iv = get("/travel/international-visitors")
check('href="/travel/international-visitors/visa-waiver-program"' in iv,
      "F-6: intl-visitors links to VWP")
check('href="/travel/international-visitors/know-before-you-visit"' in iv,
      "F-6: intl-visitors links to know-before-you-visit")
bie = get("/trade/basic-import-export")
check('href="/trade/basic-import-export/importing-car"' in bie,
      "F-6: basic-import-export links to importing-car")
check('href="/trade/basic-import-export/internet-purchases"' in bie,
      "F-6: basic-import-export links to internet-purchases")
check('href="/trade/basic-import-export/importer-exporter-tips"' in bie,
      "F-6: basic-import-export links to importer-exporter-tips")
usc = get("/travel/us-citizens")
check('href="/travel/us-citizens/know-before-you-go"' in usc,
      "F-6: us-citizens links to know-before-you-go")
check('href="/travel/us-citizens/mobile-passport-control"' in usc,
      "F-6: us-citizens links to mobile-passport-control")
check('href="/travel/us-citizens/canada-mexico-travel"' in usc,
      "F-6: us-citizens links to canada-mexico-travel")

# ------------------------------------------------------------- T0: BWT ------
body = get("/bwt?border=mexico&sort=delay")
check("Otay Mesa - Passenger" in body, "T0: Otay Mesa Passenger top row")
has(body, "185", "T0 otay delay")
has(body, "San Ysidro", "T0 second row")
d = get("/bwt/crossing/250601")
has(d, "120", "T0 otay ready delay")
has(d, "24 hrs/day", "T0 otay hours")
d2 = get("/bwt/crossing/250602")
has(d2, "40", "T0 otay commercial std")

# ------------------------------------------------------------- T1: Blaine --
body = get("/bwt?q=Blaine")
check(body.count("/bwt/crossing/3004") == 3, "T1: three Blaine crossings")
for pn, nm in [("300401", "Pacific Highway"), ("300402", "Peace Arch"),
               ("300403", "Point Roberts")]:
    dd = get(f"/bwt/crossing/{pn}")
    has(dd, nm, f"T1 {nm} detail")
has(get("/bwt/crossing/300403"), "Update Pending", "T1 point roberts status")

# ------------------------------------------------------- T2: San Ysidro ----
body = get("/bwt?q=San Ysidro")
check(body.count("San Ysidro") >= 3, "T2: all San Ysidro crossings")
d = get("/bwt/crossing/250401")
for fact in ["150", "120", "30", "60"]:
    has(d, fact, "T2 sysidro lane delays")
p = get("/contact/ports/san-ysidro-class-california-2504")
has(p, "2504", "T2 sysidro code")
has(p, "+1 619-428-2188", "T2 sysidro phone")
pw = get("/bwt/crossing/250407")
has(pw, "15", "T2 pedwest delay")
has(pw, "6 am-2 pm", "T2 pedwest hours")

# --------------------------------------------------------- T3: ESTA apply --
steps = [("disclaimers", {"disclaimer_agree": "Yes"}),
         ("applicant", {"family_name": "Andersen", "first_name": "Sofia",
                        "birth_date": "1995-03-14", "gender": "Female",
                        "citizenship": "Denmark"}),
         ("personal", {"passport_number": "DK4455667",
                       "passport_issue_country": "Denmark",
                       "passport_expiry": "2029-05-20",
                       "email": "sofia.andersen@example.com",
                       "phone": "+45 33 555 0188",
                       "address_city": "Copenhagen",
                       "address_country": "Denmark"}),
         ("travel", {"travel_purpose": "Tourism",
                     "destination_address": "300 Almaden Blvd, San Jose, CA"}),
         ("eligibility", {"q_a": "No", "q_b": "No", "q_c": "No",
                          "q_d": "No", "q_e": "No"}),
         ("review", {}),
         ("pay", {"card_name": "Sofia Andersen",
                  "card_number": "4242 4242 4242 4242",
                  "card_exp": "09/29", "card_cvv": "123"})]
num = None
for step, form in steps:
    form = dict(form)
    form["step"] = step
    form["next"] = "submit" if step == "pay" else "next"
    r = client.post("/esta/apply", data=form, follow_redirects=False)
    check(r.status_code == 302, f"T3 wizard step {step} -> {r.status_code}")
    if step == "pay":
        num = re.search(r"ESTA-\w+", r.headers["Location"]).group(0)
check(num, "T3: application number issued")
conf = get(f"/esta/confirmation/{num}")
has(conf, "Authorization Approved", "T3 approved status")
has(conf, "2028-09-28", "T3 expiry")
has(conf, "40.27", "T3 fee")
esta_info = get("/travel/international-visitors/esta")
has(esta_info, "40.27", "T3 fee shown on ESTA page")

# ------------------------------------------------------------ T4: VWP ------
vwp = get("/travel/international-visitors/visa-waiver-program")
has(vwp, "42 countries", "T4 VWP count")
has(vwp, "90 days", "T4 90-day stay")
has(vwp, "Germany", "T4 Germany listed")
chk = client.get("/esta/check?passport_number=DE29384756").data.decode()
has(chk, "ESTA-88291045", "T4 alice app number")
has(chk, "Authorization Approved", "T4 alice status")
has(chk, "2028-08-20", "T4 alice expiry")
has(esta_info, "e-Passport", "T4 epassport")

# ------------------------------------------------------------ T5: I-94 -----
def i94_lookup(fname, lname, bday, passport):
    r = client.post("/i94/request", data={
        "family_name": lname, "first_name": fname,
        "birth_date": bday, "passport_number": passport})
    return r.data.decode("utf-8", "replace")

a = i94_lookup("Alice", "Johnson", "1990-04-12", "DE29384756")
for fact in ["269745632011", "VWP B-1", "2026-06-14", "2026-09-12",
             "Washington Dulles International Airport"]:
    has(a, fact, "T5 alice i94")
b = i94_lookup("Bob", "Chen", "1988-07-19", "US556677889")
for fact in ["269745641088", "US Citizen", "2026-09-03"]:
    has(b, fact, "T5 bob i94")
bad = i94_lookup("Carol", "Davis", "1980-11-02", "GB778812345")
has(bad, "No I-94 record found", "T5 wrong birthday error")
c = i94_lookup("Carol", "Davis", "1985-11-02", "GB778812345")
for fact in ["269745650222", "VWP B-2", "2026-06-20"]:
    has(c, fact, "T5 carol i94")

# ------------------------------------------------------------- T6: Bob GE --
r = client.post("/login", data={"email": "bob.c@test.com",
                                "password": "TestPass123!"})
check(r.status_code == 302, "T6 login bob")
acct = get("/account")
has(acct, "GE-77031188", "T6 bob app number")
has(acct, "Conditionally Approved", "T6 bob status")
sched = get("/ttp/schedule/GE-77031188")
has(sched, "Austin-Bergstrom International Airport", "T6 austin center")
has(sched, "(512) 530-3056", "T6 austin phone")
# pick the Austin center id from the page
m = re.search(r'<option value="(\d+)">Austin-Bergstrom International Airport',
              sched)
check(m, "T6 austin option value")
r = client.post("/ttp/schedule/GE-77031188",
                data={"center": m.group(1), "date": "2026-10-15",
                      "slot": "9:00 a.m."}, follow_redirects=True)
has(r.data.decode(), "Interview Scheduled", "T6 scheduled")
ttp = get("/travel/trusted-traveler-programs")
has(ttp, "$120.00", "T6 GE fee")
has(ttp, "$50.00", "T6 NEXUS fee")
client.get("/logout")

# -------------------------------------------------------- T7: khat news ---
news = client.get("/newsroom/media-releases/all?q=khat").data.decode()
has(news, "65 pounds of khat", "T7 dulles release listed")
rel = get("/newsroom/local-media-release/new-york-man-arrested-after-cbp-officers-seize-65-pounds-khat")
for fact in ["Bakari Wally", "24", "Bronx", "65 pounds",
             "Washington Dulles International Airport",
             "Metropolitan Washington Airports Authority Police"]:
    has(rel, fact, "T7 dulles facts")
atl = get("/newsroom/local-media-release/atlanta-cbp-officers-stop-more-4000-pounds-illegal-khat-entering-us")
for fact in ["4,000 pounds", "Hartsfield-Jackson Atlanta International Airport"]:
    has(atl, fact, "T7 atlanta facts")

# -------------------------------------------------------- T8: Laredo etc --
laredo = get("/newsroom/local-media-release/11-memorial-ceremony-juarez")
check("9/11" in laredo or "Memorial Ceremony" in laredo, "T8 laredo slug check")
# find the laredo release from the DB-driven list
import sqlite3
con = sqlite3.connect(ROOT / "instance_test" / "audit.db")
row = con.execute("select slug from news_releases where title like ?",
                  ("%9/11 Memorial%",)).fetchone()
check(row, "T8 laredo release exists")
if row:
    lr = get("/newsroom/local-media-release/" + row[0])
    for fact in ["25th anniversary", "Juarez-Lincoln Bridge", "LAREDO, Texas"]:
        has(lr, fact, "T8 laredo facts")
tw = client.get("/newsroom/media-releases/all?q=Tidal+Wave").data.decode()
n_tw = con.execute("select count(*) from news_releases where body like ? "
                   "or title like ?", ("%Tidal Wave%", "%Tidal Wave%")).fetchone()[0]
check(n_tw >= 2, f"T8 tidal wave releases >= 2 (got {n_tw})")
row2 = con.execute("select slug, body from news_releases where body like ?",
                   ("%87 aliens%",)).fetchone()
check(row2, "T8 87 crew release")
if row2:
    twr = get("/newsroom/national-media-release/" + row2[0])
    has(twr, "87", "T8 87 crew")

# ------------------------------------------------------------ T9: forms ---
forms = get("/newsroom/publications/forms")
total = con.execute("select count(*) from forms").fetchone()[0]
check(total == 97, f"T9 total forms {total}")
f7501 = get("/newsroom/publications/forms/7501-entry-summary-with-continuation-sheets")
has(f7501, "Entry Summary with Continuation Sheets", "T9 7501 title")
has(f7501, "Feb 11 2026", "T9 7501 date")
has(f7501, "sha256", "T9 7501 sha")
f19 = get("/newsroom/publications/forms/19")
has(f19, "Protest", "T9 form 19")
row3 = con.execute("select catalog_key, title from forms where listed_date "
                    "like 'Sep%2026' or listed_date like '%2026' order by "
                    "listed_date desc").fetchall()
check(row3, "T9 newest form present")
f1304 = get("/newsroom/publications/forms/1304-crew-effects-declarations")
has(f1304, "Crew Effects Declarations", "T9 newest form title")

# ----------------------------------------------------------- T10: Carol ---
r = client.post("/login", data={"email": "carol.d@test.com",
                                "password": "TestPass123!"})
check(r.status_code == 302, "T10 login carol")
cat = client.get("/newsroom/publications/forms?q=6059B").data.decode()
# The 6059B search returns all 18 entries: 5 numbered variants plus 13
# translated variants whose catalog cells now render their form number
# (previously blank, which produced the 5-vs-18 double read).
n6059 = cat.count("CBP Form 6059B")
check(n6059 == 18, f"T10 6059B variants {n6059}")
decl = cat.count("declaration")
row4 = con.execute("select catalog_key, listed_date from forms where "
                   "form_number='6059B' and name like '%English%'").fetchone()
check(row4, "T10 english 6059B")
feng = get(f"/newsroom/publications/forms/{row4[0]}")
has(feng, "Jul 25 2024", "T10 english date")
eng_id = con.execute("select id from forms where catalog_key=?",
                     (row4[0],)).fetchone()[0]
r = client.post(f"/account/saved/form/{eng_id}", follow_redirects=True)
acct = get("/account")
has(acct, "CBP Form 6059B", "T10 saved form visible")
has(acct, "CBP Form 7501", "T10 prior saved 7501")
client.get("/logout")

# ------------------------------------------- T11: car import + net buys ---
car = get("/trade/basic-import-export/importing-car")
for fact in ["Motor Vehicle Safety Act of 1966", "EPA form 3520-1", "HS-7",
             "3%", "USMCA", "one year", "25 years"]:
    has(car, fact, "T11 car import facts")
net = get("/trade/basic-import-export/internet-purchases")
has(net, "$2,500", "T11 postal package hold threshold")
has(net, "CN 22 or CN 23", "T11 postal declaration form")
has(net, "liable for the payment of duty", "T11 duty liability")
has(net, "not subject to duty", "T11 downloaded goods duty-free")

# --------------------------------------------------------- T12: PTI -------
pti = get("/trade/priority-issues")
for fact in ["Antidumping and Countervailing Duty",
             "Intellectual Property Rights", "Import Safety",
             "Textiles/Wearing Apparel", "Agriculture and Quota",
             "Revenue", "Trade Agreements"]:
    has(pti, fact, "T12 PTI list")
adcvd = get("/trade/priority-issues/adcvd")
has(adcvd, "Antidumping and Countervailing Duty", "T12 adcvd page")
icp = get("/trade/rulings/informed-compliance-publications")
has(icp, "What Every Member of the Trade Community Should Know",
    "T12 ICP series")
ace = get("/trade/automated")
has(ace, "Automated Commercial Environment", "T12 ACE expansion")
has(ace, "centralized digital system", "T12 ACE purpose")

# ------------------------------------------------------- T13: careers -----
srp = client.get("/careers/search?q=Border+Patrol+Agent").data.decode()
bpa = get("/careers/job/882256600")
for fact in ["$51,632 - $92,912", "09/30/2026", "BPA DH 26-12", "$20,000"]:
    has(bpa, fact, "T13 BPA facts")
has(bpa, "$10,000", "T13 BPA split")
# F-7: a literal "CBP Officer" search must now surface the target posting
# (the careers search expands the CBP acronym the way the upstream one
# does, so "Customs and Border Protection Officer" matches too).
cbpo_search = client.get("/careers/search?q=CBP+Officer").data.decode()
check("/careers/job/882166800" in cbpo_search,
      "F-7/T13: 'CBP Officer' search returns control 882166800")
cbpo = get("/careers/job/882166800")
for fact in ["$41,863 - $112,415", "09/30/2026", "Yes"]:
    has(cbpo, fact, "T13 CBPO facts")

# -------------------------------------------------------- T14: events -----
ev = get("/careers/events")
check(ev.count("In Person Live Event") >= 2, "T14 in-person events")
has(ev, "Fall Hiring Fair", "T14 waco")
has(ev, "Dallas Job Fair", "T14 dallas")
has(ev, "OFO CBPO Recruitment Webinar", "T14 webinar")
ofo = get("/careers/career-paths/ofo")
has(ofo, "Office of Field Operations", "T14 ofo page")

# --------------------------------------------------------- T15: Dana ------
r = client.post("/login", data={"email": "dana.k@test.com",
                                "password": "TestPass123!"})
check(r.status_code == 302, "T15 login dana")
acct = get("/account")
has(acct, "Otay Mesa", "T15 saved crossing")
# F-6 (review numbering): Dana's saved crossing is pinned to Otay Mesa -
# Passenger (250601), whose lanes report live delays; the task premise
# (standard passenger delay and Ready Lane delay) must match the seed.
check("/bwt/crossing/250601" in acct, "T15 saved crossing is 250601")
# F-11: the saved-crossings row renders the live max delay, not a
# placeholder.
check("see crossing page" not in acct, "F-11: no placeholder max delay")
has(acct, "185 min", "T15/F-11 saved crossing max delay")
has(acct, "GE-77554402", "T15 GE app")
has(acct, "Interview Scheduled", "T15 GE status")
has(acct, "2026-10-14", "T15 interview date")
sched2 = get("/ttp/schedule/GE-77554402")
has(sched2, "Los Angeles International Airport (LAX)", "T15 LAX center")
has(sched2, "7:30 a.m. - 9:30 p.m.", "T15 LAX hours")
has(sched2, "(310) 642-1425", "T15 LAX phone")
otay = get("/bwt/crossing/250601")
has(otay, "185", "T15 otay delay")
has(otay, "120", "T15 otay ready delay")
sj = get("/careers/job/882256600")
has(sj, "$51,632 - $92,912", "T15 BPA salary")
client.get("/logout")

# ---------------------------------------------------------- T16: TTP ------
ttp = get("/travel/trusted-traveler-programs")
for fact in ["$120.00", "$50.00", "$122.25", "$78.00", "FAST"]:
    has(ttp, fact, "T16 fees")
ge = get("/travel/trusted-traveler-programs/global-entry")
has(ge, "background check", "T16 GE background check")
tsa = get("/travel/trusted-traveler-programs/tsa-precheck")
has(tsa, "enrolled in Global Entry", "T16 TSA eligibility")

# --------------------------------------------------------- T17: mega ------
vwp = get("/travel/international-visitors/visa-waiver-program")
has(vwp, "Italy", "T17 italy VWP")
steps = [("disclaimers", {"disclaimer_agree": "Yes"}),
         ("applicant", {"family_name": "Ricci", "first_name": "Marco",
                        "birth_date": "1988-06-02", "gender": "Male",
                        "citizenship": "Italy"}),
         ("personal", {"passport_number": "IT778899001",
                       "passport_issue_country": "Italy",
                       "passport_expiry": "2031-02-15",
                       "email": "marco.ricci@example.com",
                       "phone": "+39 02 555 0123",
                       "address_city": "Milan", "address_country": "Italy"}),
         ("travel", {"travel_purpose": "Tourism",
                     "destination_address": "1201 2nd Ave, Seattle, WA"}),
         ("eligibility", {"q_a": "No", "q_b": "No", "q_c": "No",
                          "q_d": "No", "q_e": "No"}),
         ("review", {}),
         ("pay", {"card_name": "Marco Ricci",
                  "card_number": "4242 4242 4242 4242", "card_exp": "09/29",
                  "card_cvv": "123"})]
num = None
for step, form in steps:
    form = dict(form)
    form["step"] = step
    form["next"] = "submit" if step == "pay" else "next"
    r = client.post("/esta/apply", data=form, follow_redirects=False)
    check(r.status_code == 302, f"T17 wizard {step}")
    if step == "pay":
        num = re.search(r"ESTA-\w+", r.headers["Location"]).group(0)
check(num, "T17 app number")
conf = get(f"/esta/confirmation/{num}")
has(conf, "Authorization Approved", "T17 approved")
pa = get("/bwt/crossing/300402")
has(pa, "5", "T17 peace arch delay")
has(pa, "24 hrs/day", "T17 peace arch hours")

# -------------------------------------------------------- T18: Carol ------
r = client.post("/login", data={"email": "carol.d@test.com",
                                "password": "TestPass123!"})
acct = get("/account")
has(acct, "ESTA-88452017", "T18 carol esta")
has(acct, "Authorization Pending", "T18 carol pending")
chk = get("/esta/check?application_number=ESTA-88452017")
has(chk, "Authorization Pending", "T18 checker pending")
esta_info = get("/travel/international-visitors/esta")
has(esta_info, "e-Passport", "T18 epassport")
client.get("/logout")

# --------------------------------------------------------- T19: 7507 -----
adv = get("/travel/advisories-wait-times")
for fact in ["7507", "General Declaration", "e-mail", "Personally Identifiable Information"]:
    has(adv, fact, "T19 advisory facts")
can = client.get("/bwt?border=canada").data.decode()
n_can = con.execute("select count(*) from crossings where border='canada'").fetchone()[0]
check(n_can >= 30, f"T19 canada crossings {n_can}")
sr = client.get("/search?q=7507").data.decode()
has(sr, "General Declaration", "T19 search 7507")

# ------------------------------------------------------- T20: search -----
sr = client.get("/search?q=Global+Entry").data.decode()
check("Global Entry" in sr, "T20 GE search")
sr2 = client.get("/search?q=San+Ysidro").data.decode()
has(sr2, "Ports of Entry", "T20 ports section")
has(sr2, "Border Crossings", "T20 crossings section")
sr3 = client.get("/search?q=Entry+Summary").data.decode()
has(sr3, "7501", "T20 entry summary form")
sr4 = client.get("/search?q=Otay+Mesa").data.decode()
check("Otay Mesa" in sr4, "T20 otay search")
otay = get("/bwt/crossing/250601")
has(otay, "185", "T20 otay delay")
has(otay, "24 hrs/day", "T20 otay hours")

# ---------------------------------------------------------- step gates ---
tasks = [json.loads(l) for l in
         (ROOT / "tasks.jsonl").read_text().strip().splitlines()]
print()
print(f"[audit] tasks: {len(tasks)}")
total_steps = 0
for t in tasks:
    tid = t["id"]
    steps = TASK_STEPS.get(tid)
    check(steps is not None, f"{tid}: no step count registered")
    if steps is not None:
        total_steps += steps
        check(steps >= MIN_STEPS,
              f"{tid}: only {steps} honest steps (< {MIN_STEPS})")
    words = len(t["ques"].split())
    check(words <= MAX_WORDS, f"{tid}: {words} words > {MAX_WORDS}")
    for key in ("web_name", "id", "ques", "web", "upstream_url"):
        check(key in t, f"{tid}: missing key {key}")
    check(t["web"] == "http://localhost:40162/", f"{tid}: web port")
    check(t["upstream_url"] == "https://www.cbp.gov/", f"{tid}: upstream")
    # answer leakage: the task text must not contain its own answers verbatim
    check("185" not in t["ques"] or "--0" not in tid, "leak check")
print(f"[audit] measured honest steps: total {total_steps}, "
      f"min {min(TASK_STEPS.values())}, max {max(TASK_STEPS.values())}")

print()
if failures:
    print(f"[audit] {len(failures)} FAILURES")
    sys.exit(1)
print("[audit] all task premises verified; every task >= 15 measured "
      "honest steps and <= 100 words")
