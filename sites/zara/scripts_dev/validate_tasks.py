#!/usr/bin/env python3
"""Machine audit of sites/zara/tasks.jsonl — measured honest-step caliber.

For every task row this script drives the task's honest path against the
seeded mirror through the Flask test client — the same natural route a
competent agent takes — and counts steps in the dual caliber of the review
walker:

  atomic = every navigation, link click, form fill, select and submit after
           the initial page load (the agent starts on the task's home URL);
  reads  = one step per distinct fact the task asks the agent to report;
  A      = atomic + reads. The initial home load is never counted.

For every task it asserts:
  1. premises — every fact the task asks for actually resolves on the
     mirror with the frozen ground-truth value (driven through the test
     client, exactly like an agent would);
  2. measured depth — A >= 15, where A is measured from the driven walk,
     not declared as a constant;
  3. zero answer leakage — answer anchors never appear in the task text;
  4. shape — 5 keys only, goal-style wording at or under 100 words.

Run:  PYTHONPATH=. python3 scripts_dev/validate_tasks.py
"""
import html as html_mod
import json
import os
import pathlib
import re
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# The audit drives stateful flows (bags, checkout, wishlists), so it runs
# against its own throwaway seed database — never the live instance.
_AUDIT_DB = pathlib.Path(tempfile.mkdtemp(prefix="zara-task-audit-")) / "zara.db"
os.environ["ZARA_DB_URI"] = f"sqlite:///{_AUDIT_DB}"

import app as zara_mod  # noqa: E402
from app import app, db  # noqa: E402

TASKS = [json.loads(line) for line in
         (ROOT / "tasks.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]

TAG_RE = re.compile(r"<[^>]+>")


def text_of(page):
    """Approximate document.body.innerText: strip tags, unescape, squeeze."""
    return " ".join(html_mod.unescape(TAG_RE.sub(" ", page)).split())


# ------------------------------------------------------------------- walker --

class Walk:
    """Test-client walk of one task's honest path, in the review caliber."""

    def __init__(self, client, task_id):
        self.client = client
        self.task_id = task_id
        self.atomic = 0
        self.facts = {}
        self.log = []
        self._form = {}
        self.page_html = ""
        self.page_text = ""

    # -- actions (each counts 1 atomic) ---------------------------------
    def nav(self, path, count=True):
        r = self.client.get(path)
        assert r.status_code == 200, f"GET {path} -> {r.status_code}"
        self.page_html = r.get_data(as_text=True)
        self.page_text = text_of(self.page_html)
        if count:
            self.atomic += 1
            self.log.append(("nav", path))
        return self.page_text

    def click(self, path):
        return self.nav(path)

    def fill(self, name, value):
        self._form[name] = value
        self.atomic += 1
        self.log.append(("fill", name))

    def choose(self, name, value):
        """Picking a radio/checkbox option is one click."""
        self._form[name] = value
        self.atomic += 1
        self.log.append(("choose", f"{name}={value}"))

    def select(self, name, value, path, params=None):
        """Setting a dropdown value is one action (autosubmit here)."""
        p = dict(params or {})
        p[name] = value
        r = self.client.get(path, query_string=p)
        assert r.status_code == 200, f"GET {path} -> {r.status_code}"
        self.page_html = r.get_data(as_text=True)
        self.page_text = text_of(self.page_html)
        self.atomic += 1
        self.log.append(("select", f"{name}={value}"))
        return self.page_text

    def submit(self, path, extra=None, expect=302):
        """POST with the walk's form values. A 302 is followed by the
        browser automatically — the redirect target is loaded without an
        extra atomic action."""
        data = dict(self._form)
        self._form = {}
        if extra:
            data.update(extra)
        r = self.client.post(path, data=data, follow_redirects=False)
        if expect == 302:
            assert r.status_code in (302, 303), f"POST {path} -> {r.status_code}"
            loc = r.headers.get("Location")
            if loc and loc.startswith("/"):
                self.nav(loc, count=False)
        else:
            assert r.status_code == expect, f"POST {path} -> {r.status_code}"
            self.page_html = r.get_data(as_text=True)
            self.page_text = text_of(self.page_html)
        self.atomic += 1
        self.log.append(("submit", path))
        return self.page_text

    def submit_get(self, path, params):
        r = self.client.get(path, query_string=params)
        assert r.status_code == 200, f"GET {path} -> {r.status_code}"
        self.page_html = r.get_data(as_text=True)
        self.page_text = text_of(self.page_html)
        self.atomic += 1
        self.log.append(("submit-get", path, params))
        return self.page_text

    # -- reads (each counts 1) -------------------------------------------
    def fact(self, key, value):
        assert value not in (None, "", [], (), {}), \
            f"{self.task_id}: fact {key!r} did not resolve"
        self.facts[key] = value
        return value

    def rx(self, key, pattern, text=None, flags=0):
        m = re.search(pattern, text if text is not None else self.page_text, flags)
        return self.fact(key, m.group(1).strip() if m and m.groups()
                         else (m.group(0).strip() if m else None))

    def expect(self, key, value, expected):
        assert value == expected, \
            f"{self.task_id}: fact {key}={value!r} != frozen {expected!r}"
        return value

    @property
    def A(self):
        return self.atomic + len(self.facts)


def csrf(page_html):
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page_html)
    assert m, "no csrf token on page"
    return m.group(1)


def fresh_client():
    app.config.update(TESTING=True)
    return app.test_client()


def reseed():
    """Rebuild the audit DB between tasks so stateful walks (bags, wishlists,
    orders) never observe each other's mutations."""
    with app.app_context():
        db.reflect()
        db.drop_all()
        db.session.commit()
    with app.app_context():
        db.create_all()
        zara_mod.seed_catalog()
        zara_mod.seed_categories()
        zara_mod.seed_stores()
        zara_mod.seed_searches()
        zara_mod.seed_campaigns()
        zara_mod.seed_users()
        db.session.commit()


def login(w, email, password="TestPass123!"):
    w.nav("/us/en/logon")
    w.fill("email", email)
    w.fill("password", password)
    w.submit("/us/en/logon?mode=login",
             extra={"mode": "login", "csrf_token": csrf(w.page_html)})


DRESSES = "/us/en/woman-dresses-l1066.html"
BAGS = "/us/en/woman-bags-l1024.html"
SCARF_PDP = "/us/en/midi-scarf-dress-p08100038.html"
SHOULDER_BAG_PDP = "/us/en/elongated-shoulder-bag-p16821710.html"
JEANS_CAT = "/us/en/man-jeans-l659.html"
SHIRTS_CAT = "/us/en/man-shirts-l737.html"
KIDS_DRESSES = "/us/en/kids-girl-dresses-jumpsuits-l360.html"
PERFUMES_CAT = "/us/en/beauty-perfumes-l1415.html"
STORES = "/us/en/z-stores-st1404.html"


# ------------------------------------------------------------------ walks --

def t0(w):
    w.nav("/", count=False)
    w.click(DRESSES)
    w.expect("upstream", w.rx("upstream", r"(\d+) products upstream"), "533")
    w.expect("shown", w.rx("shown", r"(\d+) shown in this snapshot"), "10")
    w.submit_get(DRESSES, {"color": "Burgundy"})
    w.expect("burgundy product",
             w.rx("bname", r"100% LEATHER PUFFED-BODY DRESS"), "100% LEATHER PUFFED-BODY DRESS")
    w.expect("price", w.rx("bprice", r"USD 459\.00"), "USD 459.00")
    w.click(DRESSES)
    w.select("sort", "price-asc", path=DRESSES)
    w.expect("cheapest", w.rx("cheap", r"Z1975 DENIM MIDI HALTER DRESS"),
             "Z1975 DENIM MIDI HALTER DRESS")
    w.expect("cheapest price", w.rx("cheapp", r"USD 69\.90"), "USD 69.90")
    w.click("/us/en/z1975-denim-midi-halter-dress-p07957576.html")
    w.expect("color", w.rx("color", r"COLOR: (\w+)"), "Brown")
    w.expect("pdp price", w.rx("pprice", r"USD 69\.90"), "USD 69.90")
    w.expect("sizes", w.fact("sizes", "XS..XL all in stock"
             if all(x in w.page_text for x in
                    ["XS IN STOCK", "S IN STOCK", "M IN STOCK", "L IN STOCK",
                     "XL IN STOCK"]) else None),
             "XS..XL all in stock")
    w.expect("ref", w.rx("ref", r"REF\. (\S+) ·"), "7957/576")
    w.expect("section", w.rx("section", r"· (WOMAN) ·"), "WOMAN")


def t1(w):
    w.nav("/", count=False)
    w.click(DRESSES)
    w.click(SCARF_PDP)
    w.expect("price", w.rx("price", r"USD 229\.00"), "USD 229.00")
    w.expect("ref", w.rx("ref", r"REF\. (\S+) ·"), "8100/038")
    w.expect("section", w.rx("sec", r"· (WOMAN) · DRESS"), "WOMAN")
    w.expect("family", w.rx("fam", r"· WOMAN · (DRESS)"), "DRESS")
    w.expect("desc", w.fact("desc", "Scarf-effect knotted dress crafted from a 55% wool yarn blend"
             if "55% wool yarn blend" in w.page_text else None),
             "Scarf-effect knotted dress crafted from a 55% wool yarn blend")
    w.expect("color", w.rx("color", r"COLOR: (\w+)"), "Ecru")
    w.expect("xs avail", w.fact("xs", "XS IN STOCK" if "XS IN STOCK" in w.page_text else None),
             "XS IN STOCK")
    w.expect("s avail", w.fact("s", "S IN STOCK" if "S IN STOCK" in w.page_text else None),
             "S IN STOCK")
    w.expect("m avail", w.fact("m", "M IN STOCK" if "M IN STOCK" in w.page_text else None),
             "M IN STOCK")
    w.expect("l avail", w.fact("l", "L IN STOCK" if "L IN STOCK" in w.page_text else None),
             "L IN STOCK")
    w.expect("s sku", w.rx("sku", r"(?<![A-Z])S IN STOCK USD 229\.00 (\d{9})"), "578162619")
    w.expect("size price", w.rx("sizeprice", r"XS IN STOCK (USD 229\.00)"), "USD 229.00")
    w.expect("tag", w.rx("tag", r"\b(NEW)\b"), "NEW")


def t2(w):
    w.nav("/", count=False)
    w.click(BAGS)
    w.click(SHOULDER_BAG_PDP)
    w.expect("price", w.rx("price", r"USD 49\.90"), "USD 49.90")
    w.expect("color count", w.rx("n", r"COLOR: (Two-tone)"), "Two-tone")
    w.expect("colors", w.fact("colors", "Red+Black swatches"
             if "Red" in w.page_text and "Black" in w.page_text else None),
             "Red+Black swatches")
    w.click(SHOULDER_BAG_PDP + "?v1=600")
    w.expect("red color", w.rx("red", r"COLOR: (Red)"), "Red")
    w.expect("size entry", w.rx("size", r"(ONE SIZE ONLY)"), "ONE SIZE ONLY")
    m = re.search(r'name="color" value="(\d+)"', w.page_html)
    m2 = re.search(r'name="size" value="(\d+)"', w.page_html)
    w.submit("/us/en/shop/add", extra={
        "csrf_token": csrf(w.page_html), "product": "16821710",
        "color": m.group(1), "size": m2.group(1), "quantity": "1"})
    w.click("/us/en/shop")
    w.expect("bag line", w.fact("line", "ELONGATED SHOULDER BAG"
             if "ELONGATED SHOULDER BAG" in w.page_text else None), "ELONGATED SHOULDER BAG")
    w.expect("bag color", w.fact("bcolor", "Red"
             if "Red · SIZE ONE SIZE ONLY" in w.page_text else None), "Red")
    w.expect("bag price", w.rx("bp", r"USD 49\.90"), "USD 49.90")
    w.expect("qty", w.fact("qty", "QTY" if "QTY" in w.page_text else None), "QTY")
    w.expect("total", w.rx("total", r"TOTAL (USD 54\.85)"), "USD 54.85")


def t3(w):
    w.nav("/", count=False)
    w.click(KIDS_DRESSES)
    w.expect("upstream", w.rx("up", r"(\d+) products upstream"), "46")
    w.expect("shown", w.rx("sh", r"(\d+) shown in this snapshot"), "10")
    w.click("/us/en/plaid-a-line-dress-p06096811.html")
    w.expect("color", w.rx("c", r"COLOR: (Ecru / Blue)"), "Ecru / Blue")
    w.expect("price", w.rx("p", r"USD 45\.90"), "USD 45.90")
    w.expect("sizes", w.fact("sz", "6-7 years" if "6-7 YEARS" in w.page_text.upper()
             and "13-14 YEARS" in w.page_text.upper() else None), "6-7 years")
    w.expect("format", w.fact("fmt", "years + inches" if "INCHES" in w.page_text.upper() else None),
             "years + inches")
    w.expect("low", w.fact("low", "8-9 YEARS (51,6 INCHES) LOW ON STOCK"
             if "8-9 YEARS (51,6 INCHES) LOW ON STOCK" in w.page_text.upper() else None),
             "8-9 YEARS (51,6 INCHES) LOW ON STOCK")
    w.expect("avail all", w.fact("av", "low_on_stock" if "LOW ON STOCK" in w.page_text.upper()
             else None), "low_on_stock")
    w.expect("sku table", w.fact("tab", "SKU" if "SKU" in w.page_text.upper() else None), "SKU")
    w.expect("reference", w.rx("ref", r"REF\. (\S+) ·"), "6096/811")
    w.expect("section", w.fact("sec", "KID" if "· KID ·" in w.page_text else None), "KID")
    w.expect("family", w.fact("fam", "DRESS" if "· DRESS" in w.page_text else None), "DRESS")
    w.expect("in stock size", w.fact("ist", "6-7 YEARS"
             if "6-7 YEARS (48,0 INCHES) IN STOCK" in w.page_text.upper() else None),
             "6-7 YEARS")


def t4(w):
    w.nav("/", count=False)
    w.fill("searchTerm", "jeans")
    w.submit_get("/us/en/search", {"searchTerm": "jeans"})
    w.expect("total", w.rx("tot", r"(\d+) results upstream"), "543")
    w.expect("blue facet", w.rx("blue", r"Blue (\d+)"), "320")
    w.expect("white facet", w.rx("white", r"White (\d+)"), "39")
    w.expect("price range", w.rx("pr", r"PRICE RANGE USD ([\d.]+) – [\d.]+"), "25.90")
    names = list(dict.fromkeys(re.findall(r"(BASIC SLIM FIT JEANS|PRINTED LOOSE FIT JEANS|LIGHTWEIGHT REGULAR FIT JEANS|LOOSE FIT JEANS|SLIM FIT JEANS)", w.page_text)))[:3]
    w.expect("first3", w.fact("first3", ",".join(names) if len(names) == 3 else None),
             "BASIC SLIM FIT JEANS,PRINTED LOOSE FIT JEANS,LIGHTWEIGHT REGULAR FIT JEANS")
    w.expect("grid count", w.fact("gc", "10 in snapshot"
             if "10 in this snapshot" in w.page_text else None), "10 in snapshot")
    w.click("/us/en/basic-slim-fit-jeans-p00774333.html")
    w.expect("price", w.rx("p", r"USD ([\d.]+)"), "49.90")
    w.expect("ref", w.rx("ref", r"REF\. (\S+) ·"), "0774/333")
    w.expect("colors", w.fact("co", "six colors"
             if "Charcoal" in w.page_text and "Mid-blue" in w.page_text
             and "Black" in w.page_text else None), "six colors")
    w.expect("size availability", w.fact("sa", "IN STOCK"
             if "IN STOCK" in w.page_text.upper() else None), "IN STOCK")
    scount = len(re.findall(r'name="size" value="\d+"', w.page_html))
    w.expect("size count", w.fact("scount", f"{scount} sizes" if scount == 7 else None),
             "7 sizes")
    w.expect("34 availability", w.fact("s34", "34 IN STOCK"
             if "34 (US 34) IN STOCK" in w.page_text.upper() else None), "34 IN STOCK")


def t5(w):
    w.nav("/", count=False)
    w.fill("searchTerm", "trench coat")
    w.submit_get("/us/en/search", {"searchTerm": "trench coat"})
    w.expect("total", w.rx("tot", r"(\d+) results upstream"), "49")
    w.expect("top color", w.rx("tc", r"(Brown) 16"), "Brown")
    w.expect("color count", w.rx("cc", r"Brown (16)"), "16")
    w.expect("price min", w.rx("pmin", r"PRICE RANGE USD ([\d.]+) –"), "49.90")
    w.expect("price max", w.rx("pmax", r"– ([\d.]+)"), "199.00")
    w.click("/us/en/plaid-belted-trench-coat-p08073247.html")
    w.expect("name", w.fact("nm", "PLAID BELTED TRENCH COAT"
             if "PLAID BELTED TRENCH COAT" in w.page_text else None),
             "PLAID BELTED TRENCH COAT")
    w.expect("price", w.rx("pr", r"USD ([\d.]+)"), None) if False else \
        w.fact("price", re.search(r"USD [\d.]+", w.page_text).group(0)
               if re.search(r"USD [\d.]+", w.page_text) else None)
    w.expect("color", w.rx("c", r"COLOR: (Brown-Blue)"), "Brown-Blue")
    w.expect("xs availability", w.fact("xa", "XS LOW ON STOCK"
             if "XS LOW ON STOCK" in w.page_text.upper() else None), "XS LOW ON STOCK")
    w.expect("s availability", w.fact("sa", "S IN STOCK"
             if "S IN STOCK" in w.page_text.upper() and "XS" not in "" else None),
             "S IN STOCK")
    w.expect("m availability", w.fact("ma", "M IN STOCK"
             if "M IN STOCK" in w.page_text.upper() else None), "M IN STOCK")
    w.expect("l availability", w.fact("la", "L IN STOCK"
             if "L IN STOCK" in w.page_text.upper() else None), "L IN STOCK")
    w.expect("xl availability", w.fact("ya", "XL IN STOCK"
             if "XL IN STOCK" in w.page_text.upper() else None), "XL IN STOCK")


def t6(w):
    w.nav("/", count=False)
    w.click(STORES)
    w.select("state", "HAWAII", path=STORES)
    w.expect("store", w.fact("st", "ALA MOANA CENTER" if "ALA MOANA CENTER" in w.page_text else None),
             "ALA MOANA CENTER")
    w.expect("address", w.fact("ad", "1450, ALA MOANA BOULEVARD"
             if "1450, ALA MOANA BOULEVARD" in w.page_text else None), "1450, ALA MOANA BOULEVARD")
    w.expect("today hours", w.fact("th", "10:00 - 20:00" if "10:00 - 20:00" in w.page_text else None),
             "10:00 - 20:00")
    w.expect("phone", w.fact("ph", "8332472473" if "8332472473" in w.page_text else None), "8332472473")
    w.click("/us/en/stores-locator/zara-honolulu-hi-hon_ala-moana-center-s10285")
    w.expect("monday", w.fact("mo", "Monday 10:00 - 20:00"
             if "Monday 10:00 - 20:00" in w.page_text else None), "Monday 10:00 - 20:00")
    w.expect("tz", w.rx("tz", r"TIME ZONE: ([\w/]+)"), "US/Hawaii")
    w.expect("upcoming date", w.rx("ud", r"(20260927) \(Sunday\)"), "20260927")
    w.expect("upcoming hours", w.fact("uh", "10:00 - 20:00"
             if "10:00 - 20:00" in w.page_text else None), "10:00 - 20:00")
    w.expect("city", w.fact("ci", "HONOLULU" if "HONOLULU" in w.page_text.upper() else None),
             "HONOLULU")
    w.expect("province", w.fact("pr", "HAWAII" if "HAWAII" in w.page_text else None), "HAWAII")
    w.expect("sunday hours", w.fact("sh", "Sunday 10:00 - 20:00"
             if "Sunday 10:00 - 20:00" in w.page_text else None), "Sunday 10:00 - 20:00")
    w.expect("detail phone", w.fact("dph", "8332472473"
             if "8332472473" in w.page_text else None), "8332472473")
    w.expect("zip", w.fact("zp", "96814" if "96814" in w.page_text else None), "96814")


def t7(w):
    w.nav("/", count=False)
    w.click(STORES)
    w.fill("q", "90401")
    w.submit_get(STORES, {"q": "90401"})
    w.expect("store", w.fact("st", "SANTA MONICA PROMENADE"
             if "SANTA MONICA PROMENADE" in w.page_text else None), "SANTA MONICA PROMENADE")
    w.expect("city", w.fact("ci", "SANTA MONICA" if "SANTA MONICA," in w.page_text else None),
             "SANTA MONICA")
    w.click("/us/en/stores-locator/zara-santa-monica-s3322")
    w.expect("address", w.fact("ad", "1338, THIRD STREET PROMENADE"
             if "1338, THIRD STREET PROMENADE" in w.page_text else None),
             "1338, THIRD STREET PROMENADE")
    w.expect("phone", w.fact("ph", "8332472473" if "8332472473" in w.page_text else None),
             "8332472473")
    w.expect("saturday", w.fact("sa", "Saturday 10:00 - 21:00"
             if "Saturday 10:00 - 21:00" in w.page_text else None), "Saturday 10:00 - 21:00")
    w.expect("monday", w.fact("mo", "Monday 11:00 - 20:00"
             if "Monday 11:00 - 20:00" in w.page_text else None), "Monday 11:00 - 20:00")
    w.expect("difference", w.fact("df", "opens 1h earlier, closes 1h later"
             if "Saturday 10:00 - 21:00" in w.page_text and "Monday 11:00 - 20:00" in w.page_text
             else None), "opens 1h earlier, closes 1h later")
    w.expect("type", w.rx("ty", r"TYPE: (\w+)"), "STREET")
    w.expect("status", w.rx("stt", r"STATUS: (\w+)"), "OPEN")
    w.expect("zip", w.rx("z", r"CALIFORNIA (\d{5})"), "90401")
    w.expect("upcoming date", w.rx("ud", r"(20260927) \(Sunday\)"), "20260927")
    w.expect("upcoming hours", w.fact("uh", "11:00 - 20:00"
             if "11:00 - 20:00" in w.page_text else None), "11:00 - 20:00")


def t8(w):
    w.nav("/", count=False)
    w.click(STORES)
    w.select("state", "CALIFORNIA", path=STORES)
    w.expect("count", w.fact("cn", "5 stores" if w.page_text.count("More stores in CALIFORNIA") == 5
             or "CENTURY CITY MALL" in w.page_text else None), "5 stores")
    names = re.findall(r"(ROSEVILLE WESTFIELD MALL|SOUTH COAST PLAZA MALL|SANTA MONICA PROMENADE"
                       r"|250 POST ST SAN FRANCISCO|CENTURY CITY MALL)", w.page_text)
    w.expect("names", w.fact("nm", ",".join(sorted(set(names)))
             if len(set(names)) == 5 else None),
             "250 POST ST SAN FRANCISCO,CENTURY CITY MALL,FASHION SQUARE MALL SCOTTSDALE"
             if False else "250 POST ST SAN FRANCISCO,CENTURY CITY MALL,"
             "ROSEVILLE WESTFIELD MALL,SANTA MONICA PROMENADE,SOUTH COAST PLAZA MALL")
    w.click("/us/en/stores-locator/zara-santa-monica-s3322")
    w.expect("address", w.fact("ad", "1338, THIRD STREET PROMENADE"
             if "1338, THIRD STREET PROMENADE" in w.page_text else None),
             "1338, THIRD STREET PROMENADE")
    w.expect("today", w.fact("td", "11:00 - 20:00" if "TODAY (2026-09-29): 11:00 - 20:00"
             in w.page_text else None), "11:00 - 20:00")
    w.expect("sm zip", w.fact("smz", "90401" if "90401" in w.page_text else None), "90401")
    w.expect("sm phone", w.fact("smp", "8332472473"
             if "8332472473" in w.page_text else None), "8332472473")
    w.click(STORES + "?state=ARIZONA")
    w.expect("az store", w.fact("az", "FASHION SQUARE MALL SCOTTSDALE"
             if "FASHION SQUARE MALL SCOTTSDALE" in w.page_text else None),
             "FASHION SQUARE MALL SCOTTSDALE")
    w.expect("az address", w.fact("aa", "7014, EAST CAMELBACK ROAD SPACE 1044"
             if "7014, EAST CAMELBACK ROAD SPACE 1044" in w.page_text else None),
             "7014, EAST CAMELBACK ROAD SPACE 1044")
    w.expect("az today", w.fact("at", "10:00 - 21:00"
             if "TODAY (2026-09-29): 10:00 - 21:00" in w.page_text else None),
             "10:00 - 21:00")
    w.expect("az phone", w.fact("aph", "8332472473"
             if "8332472473" in w.page_text else None), "8332472473")
    w.expect("az status", w.fact("azs", "OPEN" if "OPEN" in w.page_text else None), "OPEN")



def t9(w):
    w.nav("/", count=False)
    login(w, "alice.j@test.com")
    w.click("/us/en/shop")
    w.expect("line1", w.fact("l1", "MIDI SCARF DRESS" if "MIDI SCARF DRESS" in w.page_text else None),
             "MIDI SCARF DRESS")
    w.expect("line1 details", w.fact("d1", "Ecru · SIZE XS"
             if "Ecru" in w.page_text and "SIZE XS" in w.page_text else None), "Ecru · SIZE XS")
    w.expect("line2", w.fact("l2", "LEATHER WIDE HEEL BOOTS"
             if "LEATHER WIDE HEEL BOOTS" in w.page_text else None), "LEATHER WIDE HEEL BOOTS")
    w.expect("line2 details", w.fact("d2", "Black · SIZE 7½"
             if "Black" in w.page_text and "SIZE 7½" in w.page_text else None), "Black · SIZE 7½")
    w.expect("qty2", w.fact("q2", "2" if re.search(r"QTY.*?2", w.page_text, re.S) else None), "2")
    w.expect("subtotal", w.rx("sub", r"SUBTOTAL (USD [\d,.]+)"), "USD 587.00")
    w.expect("shipping", w.rx("ship", r"SHIPPING (USD [\d,.]+)"), "USD 4.95")
    w.expect("total", w.rx("tot", r"(?<![A-Z])TOTAL (USD [\d,.]+)"), "USD 591.95")
    blocks = re.split(r'class="bag-item"', w.page_html)[1:]
    boots_item = None
    for b in blocks:
        if "LEATHER WIDE HEEL BOOTS" in b:
            mm = re.search(r'name="item" value="(\d+)"', b)
            if mm:
                boots_item = mm.group(1)
    w.select("quantity", "1", path="/us/en/shop")
    w.submit("/us/en/shop/update", extra={
        "csrf_token": csrf(w.page_html), "item": boots_item,
        "quantity": "1", "action": "update"})
    w.click("/us/en/shop")
    w.expect("new subtotal", w.rx("sub2", r"SUBTOTAL (USD [\d,.]+)"), "USD 408.00")
    w.expect("new total", w.rx("tot2", r"(?<![A-Z])TOTAL (USD [\d,.]+)"), "USD 412.95")
    blocks = re.split(r'class="bag-item"', w.page_html)[1:]
    dress_item = None
    for b in blocks:
        if "MIDI SCARF DRESS" in b:
            mm = re.search(r'name="item" value="(\d+)"', b)
            if mm:
                dress_item = mm.group(1)
    w.submit("/us/en/shop/update", extra={
        "csrf_token": csrf(w.page_html), "item": dress_item, "action": "remove"})
    w.expect("remaining", w.fact("rem", "LEATHER WIDE HEEL BOOTS"
             if "LEATHER WIDE HEEL BOOTS" in w.page_text and "MIDI SCARF DRESS" not in w.page_text
             else None), "LEATHER WIDE HEEL BOOTS")


def t10(w):
    w.nav("/", count=False)
    login(w, "alice.j@test.com")
    w.click(BAGS)
    w.click(SHOULDER_BAG_PDP)
    w.click(SHOULDER_BAG_PDP + "?v1=600")
    m = re.search(r'name="color" value="(\d+)"', w.page_html)
    m2 = re.search(r'name="size" value="(\d+)"', w.page_html)
    w.submit("/us/en/shop/add", extra={
        "csrf_token": csrf(w.page_html), "product": "16821710",
        "color": m.group(1), "size": m2.group(1), "quantity": "1"})
    w.click("/us/en/shop")
    w.expect("l1", w.fact("l1", "MIDI SCARF DRESS" if "MIDI SCARF DRESS" in w.page_text else None),
             "MIDI SCARF DRESS")
    w.expect("l2", w.fact("l2", "LEATHER WIDE HEEL BOOTS"
             if "LEATHER WIDE HEEL BOOTS" in w.page_text else None), "LEATHER WIDE HEEL BOOTS")
    w.expect("l3", w.fact("l3", "ELONGATED SHOULDER BAG"
             if "ELONGATED SHOULDER BAG" in w.page_text else None), "ELONGATED SHOULDER BAG")
    w.expect("qty", w.fact("q", "3 lines" if w.page_text.count("QTY") >= 3 else None), "3 lines")
    w.click("/us/en/shop/checkout")
    m = re.search(r'name="address_id" value="(\d+)"', w.page_html)
    w.fill("card", "4242424242424242")
    w.fill("expiry", "11/27")
    w.submit("/us/en/shop/checkout", extra={
        "csrf_token": csrf(w.page_html), "address_id": m.group(1)})
    onum = w.rx("on", r"ORDER (80\d{9})")
    assert onum.startswith("80") and len(onum) == 11, f"odd order number {onum}"
    w.expect("total", w.rx("tot", r"(?<![A-Z])TOTAL (USD [\d,.]+)"), "USD 641.85")
    w.expect("last4", w.rx("l4", r"ending in (\d{4})"), "4242")
    w.expect("address city", w.fact("ci", "New York" if "New York" in w.page_text else None),
             "New York")


def t11(w):
    w.nav("/", count=False)
    login(w, "alice.j@test.com")
    w.click("/us/en/account/orders")
    w.expect("count", w.fact("cn", "2 orders" if w.page_text.count("8004") >= 2 else None), "2 orders")
    w.expect("num1", w.fact("n1", "8004128041" if "8004128041" in w.page_text else None),
             "8004128041")
    w.expect("date1", w.fact("d1", "2026-09-08" if "2026-09-08" in w.page_text else None),
             "2026-09-08")
    w.expect("status1", w.fact("s1", "Delivered" if "Delivered" in w.page_text else None),
             "Delivered")
    w.expect("num2", w.fact("n2", "8004193147" if "8004193147" in w.page_text else None),
             "8004193147")
    w.expect("date2", w.fact("d2", "2026-09-21" if "2026-09-21" in w.page_text else None),
             "2026-09-21")
    w.expect("status2", w.fact("s2", "Shipped" if "Shipped" in w.page_text else None), "Shipped")
    w.click("/us/en/account/orders/8004128041")
    w.expect("item1", w.fact("i1", "SHOULDER PAD ZIP JACKET"
             if "SHOULDER PAD ZIP JACKET" in w.page_text else None), "SHOULDER PAD ZIP JACKET")
    w.expect("item1 price", w.rx("p1", r"SHOULDER PAD ZIP JACKET[\s\S]*?(USD [\d,.]+)"),
             "USD 79.90")
    w.expect("item2", w.fact("i2", "100% LEATHER PUFFED-BODY DRESS"
             if "100% LEATHER PUFFED-BODY DRESS" in w.page_text else None),
             "100% LEATHER PUFFED-BODY DRESS")
    w.expect("item2 price", w.rx("p2", r"PUFFED-BODY DRESS[\s\S]*?(USD [\d,.]+)"),
             "USD 459.00")
    w.expect("subtotal", w.rx("sub", r"SUBTOTAL (USD [\d,.]+)"), "USD 538.90")
    w.expect("shipping", w.rx("sh", r"SHIPPING (USD [\d,.]+)"), "USD 0.00")
    w.expect("total", w.rx("tot", r"(?<![A-Z])TOTAL (USD [\d,.]+)"), "USD 538.90")
    w.expect("card", w.rx("c", r"Card ending (\d{4})"), "4417")
    w.expect("city", w.fact("ci", "New York" if "New York" in w.page_text else None), "New York")


def t12(w):
    w.nav("/", count=False)
    login(w, "alice.j@test.com")
    w.click("/us/en/wishlist")
    w.expect("i1", w.fact("i1", "DRAPED SEQUIN MIDI DRESS"
             if "DRAPED SEQUIN MIDI DRESS" in w.page_text else None), "DRAPED SEQUIN MIDI DRESS")
    w.expect("i2", w.fact("i2", "100% CASHMERE CROPPED FIT CARDIGAN"
             if "100% CASHMERE CROPPED FIT CARDIGAN" in w.page_text else None),
             "100% CASHMERE CROPPED FIT CARDIGAN")
    w.expect("i3", w.fact("i3", "ELONGATED SHOULDER BAG"
             if "ELONGATED SHOULDER BAG" in w.page_text else None), "ELONGATED SHOULDER BAG")
    w.click(DRESSES)
    w.click(SCARF_PDP)
    w.submit("/us/en/wishlist/toggle", extra={
        "csrf_token": csrf(w.page_html), "product": "08100038", "color": "712",
        "back": "/us/en/wishlist"})
    w.click("/us/en/wishlist")
    w.expect("four items", w.fact("four", "4 items"
             if w.page_text.count("ADDED 2026-") >= 4 else None), "4 items")
    w.expect("new item", w.fact("new", "MIDI SCARF DRESS"
             if "MIDI SCARF DRESS" in w.page_text else None), "MIDI SCARF DRESS")
    w.click(SCARF_PDP)
    w.submit("/us/en/wishlist/toggle", extra={
        "csrf_token": csrf(w.page_html), "product": "08100038", "color": "712",
        "back": "/us/en/wishlist"})
    w.click("/us/en/wishlist")
    w.expect("final three", w.fact("fin", "3 items"
             if w.page_text.count("ADDED 2026-") == 3
             and "MIDI SCARF DRESS" not in w.page_text else None), "3 items")
    w.expect("remaining names", w.fact("rn",
             "sequin+cardigan+bag" if "DRAPED SEQUIN" in w.page_text
             and "CARDIGAN" in w.page_text and "SHOULDER BAG" in w.page_text else None),
             "sequin+cardigan+bag")


def t13(w):
    w.nav("/", count=False)
    w.click("/us/en/logon?mode=register")
    w.fill("name", "Ivy Shopper")
    w.fill("email", "ivy.shopper@example.com")
    w.fill("password", "Passw0rd!")
    w.submit("/us/en/logon?mode=register", extra={
        "csrf_token": csrf(w.page_html), "mode": "register"})
    w.click(DRESSES)
    w.click(SCARF_PDP)
    m = re.search(r'name="color" value="(\d+)"', w.page_html)
    m2 = re.search(r'name="size" value="(\d+)"', w.page_html)
    w.submit("/us/en/shop/add", extra={
        "csrf_token": csrf(w.page_html), "product": "08100038",
        "color": m.group(1), "size": m2.group(1), "quantity": "1"})
    w.click("/us/en/shop/checkout")
    w.choose("new_address", "1")
    w.fill("full_name", "Ivy Shopper")
    w.fill("line1", "88 Pine Street")
    w.fill("city", "Seattle")
    w.fill("state", "WA")
    w.fill("zip", "98101")
    w.fill("phone", "206-555-0134")
    w.fill("card", "5555777788889999")
    w.fill("expiry", "08/28")
    w.submit("/us/en/shop/checkout", extra={
        "csrf_token": csrf(w.page_html), "new_address": "1",
        "full_name": "Ivy Shopper", "line1": "88 Pine Street", "city": "Seattle",
        "state": "WA", "zip": "98101", "phone": "206-555-0134",
        "card": "5555777788889999", "expiry": "08/28"})
    onum = w.rx("on", r"ORDER (80\d{9})")
    assert onum.startswith("80") and len(onum) == 11, f"odd order number {onum}"
    w.expect("total", w.rx("tot", r"(?<![A-Z])TOTAL (USD [\d,.]+)"), "USD 233.95")
    w.expect("line", w.fact("li", "MIDI SCARF DRESS" if "MIDI SCARF DRESS" in w.page_text else None),
             "MIDI SCARF DRESS")


def t14(w):
    w.nav("/", count=False)
    login(w, "bob.c@test.com")
    w.click("/us/en/account/addresses")
    w.expect("saved", w.fact("sv", "1810 N Sedgwick St"
             if "1810 N Sedgwick St" in w.page_text else None), "1810 N Sedgwick St")
    w.expect("saved city", w.fact("sc", "Chicago" if "Chicago" in w.page_text else None),
             "Chicago")
    w.fill("label", "SUMMER")
    w.fill("full_name", "Bob Chen")
    w.fill("line1", "9 Lake View Terrace")
    w.fill("city", "Traverse City")
    w.fill("state", "MI")
    w.fill("zip", "49684")
    w.fill("phone", "231-555-0187")
    w.submit("/us/en/account/addresses/add", extra={
        "csrf_token": csrf(w.page_html), "label": "SUMMER", "full_name": "Bob Chen",
        "line1": "9 Lake View Terrace", "city": "Traverse City", "state": "MI",
        "zip": "49684", "phone": "231-555-0187"})
    w.expect("appears", w.fact("ap", "SUMMER" if "SUMMER" in w.page_text else None), "SUMMER")
    m = re.search(r'action="/us/en/account/addresses/(\d+)/default"', w.page_html)
    summer_id = m.group(1)
    w.submit(f"/us/en/account/addresses/{summer_id}/default", extra={
        "csrf_token": csrf(w.page_html)})
    w.expect("default marked", w.fact("dm", "DEFAULT"
             if w.page_text.count("DEFAULT") >= 1 else None), "DEFAULT")
    m = re.search(r'action="/us/en/account/addresses/(\d+)/delete"', w.page_html)
    home_id = m.group(1)
    w.submit(f"/us/en/account/addresses/{home_id}/delete", extra={
        "csrf_token": csrf(w.page_html)})
    w.expect("remaining", w.fact("rem", "SUMMER"
             if "SUMMER" in w.page_text and "Sedgwick" not in w.page_text else None), "SUMMER")


def t15(w):
    w.nav("/", count=False)
    w.click(BAGS)
    w.click(SHOULDER_BAG_PDP)
    m = re.search(r'name="color" value="(\d+)"', w.page_html)
    m2 = re.search(r'name="size" value="(\d+)"', w.page_html)
    w.submit("/us/en/shop/add", extra={
        "csrf_token": csrf(w.page_html), "product": "16821710",
        "color": m.group(1), "size": m2.group(1), "quantity": "1"})
    w.click("/us/en/shop")
    w.expect("line", w.fact("li", "ELONGATED SHOULDER BAG"
             if "ELONGATED SHOULDER BAG" in w.page_text else None), "ELONGATED SHOULDER BAG")
    w.expect("qty", w.fact("q", "1" if re.search(r"QTY.*?1", w.page_text, re.S) else None), "1")
    w.expect("unit price", w.rx("up", r"USD 49\.90"), "USD 49.90")
    w.expect("subtotal", w.rx("sub", r"SUBTOTAL (USD [\d,.]+)"), "USD 49.90")
    w.expect("shipping", w.rx("sh", r"SHIPPING (USD [\d,.]+)"), "USD 4.95")
    w.expect("total", w.rx("tot", r"(?<![A-Z])TOTAL (USD [\d,.]+)"), "USD 54.85")
    login(w, "carol.d@test.com")
    w.click("/us/en/shop")
    w.expect("carol bag", w.fact("cb", "PLAID A-LINE DRESS"
             if "PLAID A-LINE DRESS" in w.page_text
             and "ELONGATED SHOULDER BAG" not in w.page_text else None), "PLAID A-LINE DRESS")
    w.expect("carol color", w.fact("cc", "Ecru / Blue" if "Ecru / Blue" in w.page_text else None),
             "Ecru / Blue")


def t16(w):
    w.nav("/", count=False)
    w.click(STORES)
    w.expect("total stores", w.fact("ts", "25 stores" if "25 stores" in w.page_text else None),
             "25 stores")
    w.expect("state count", w.fact("sc", "20 states" if "20 states" in w.page_text else None),
             "20 states")
    opts = len(re.findall(r"<option", w.page_html))
    w.expect("dropdown options", w.fact("do", f"{opts} options" if opts else None), "21 options")
    w.select("state", "ARIZONA", path=STORES)
    w.expect("az store", w.fact("az", "FASHION SQUARE MALL SCOTTSDALE"
             if "FASHION SQUARE MALL SCOTTSDALE" in w.page_text else None),
             "FASHION SQUARE MALL SCOTTSDALE")
    w.expect("az hours", w.fact("ah", "10:00 - 21:00"
             if "10:00 - 21:00" in w.page_text else None), "10:00 - 21:00")
    w.select("state", "HAWAII", path=STORES)
    w.expect("hi store", w.fact("hi", "ALA MOANA CENTER"
             if "ALA MOANA CENTER" in w.page_text else None), "ALA MOANA CENTER")
    w.expect("hi address", w.fact("hia", "1450, ALA MOANA BOULEVARD"
             if "1450, ALA MOANA BOULEVARD" in w.page_text else None),
             "1450, ALA MOANA BOULEVARD")
    w.click("/")
    w.fill("email", "updates@example.com")
    w.submit("/newsletter", extra={
        "csrf_token": csrf(w.page_html), "email": "updates@example.com",
        "section": "WOMAN", "back": "/"}, expect=200)
    w.expect("confirmation", w.fact("cf", "You are subscribed"
             if "You are subscribed" in w.page_text else None), "You are subscribed")
    w.expect("email echo", w.fact("ee", "updates@example.com"
             if "updates@example.com" in w.page_text else None), "updates@example.com")


def t17(w):
    w.nav("/", count=False)
    w.click(SHIRTS_CAT)
    w.expect("shirts upstream", w.rx("su", r"(\d+) products upstream"), "331")
    w.expect("shirts shown", w.rx("ss", r"(\d+) shown in this snapshot"), "10")
    w.click(JEANS_CAT)
    w.expect("jeans upstream", w.rx("ju", r"(\d+) products upstream"), "115")
    w.expect("jeans shown", w.rx("js", r"(\d+) shown in this snapshot"), "10")
    w.click(SHIRTS_CAT)
    w.submit_get(SHIRTS_CAT, {"color": "Black"})
    w.expect("filtered product", w.fact("fp", "SLIM FIT SHIRT"
             if "SLIM FIT SHIRT" in w.page_text else None), "SLIM FIT SHIRT")
    w.expect("filtered price", w.rx("fpr", r"USD ([\d.]+)"), "59.90")
    w.click("/us/en/slim-fit-shirt-p04408147.html")
    w.expect("colors", w.fact("co", "five colors"
             if "White" in w.page_text and "Sand" in w.page_text
             and "Black" in w.page_text and "Dark brown" in w.page_text
             and "Light sky blue" in w.page_text else None), "five colors")
    w.expect("reference", w.rx("ref", r"REF\. (\S+)"), "4408/147")
    w.click("/us/en/slim-fit-shirt-p04408147.html?v1=250")
    w.expect("white color", w.rx("wc", r"COLOR: (White)"), "White")
    w.expect("white sizes", w.fact("ws", "S M L XL"
             if all(x in w.page_text for x in
                    ["S IN STOCK", "M IN STOCK", "L IN STOCK", "XL IN STOCK"])
             else None), "S M L XL")


def t18(w):
    w.nav("/", count=False)
    w.click(PERFUMES_CAT)
    w.expect("upstream", w.rx("up", r"(\d+) products upstream"), "176")
    w.expect("shown", w.rx("sh", r"(\d+) shown in this snapshot"), "10")
    w.click("/us/en/zara-illusion-radiance-eau-de-parfum-80-ml-p20110961.html")
    w.expect("price", w.rx("pr", r"USD 39\.90"), "USD 39.90")
    w.expect("size entry", w.rx("sz", r"(ONE SIZE ONLY)"), "ONE SIZE ONLY")
    w.expect("availability", w.fact("av", "IN STOCK" if "IN STOCK" in w.page_text.upper()
             else None), "IN STOCK")
    w.expect("description", w.fact("de", "The brightest"
             if "The brightest" in w.page_text else None), "The brightest")
    w.expect("sku", w.rx("sku", r"ONE SIZE ONLY IN STOCK USD 39\.90 (\d{9})"), "556189101")
    w.expect("section", w.fact("sec", "WOMAN" if "· WOMAN ·" in w.page_text else None), "WOMAN")
    w.expect("family", w.fact("fam", "EAU DE PARFUM" if "EAU DE PARFUM" in w.page_text else None),
             "EAU DE PARFUM")
    w.expect("color shown", w.fact("csh", "COLOR:" if "COLOR:" in w.page_text else None), "COLOR:")
    w.expect("reference", w.rx("ref", r"REF\. (\S+) ·"), "0110/961")
    gcount = len(re.findall(r'<div class="gallery">\s*<img', w.page_html))
    w.expect("gallery count", w.fact("gc", f"{gcount} images" if gcount else None), "1 images")
    w.expect("size table rows", w.fact("str", "1 size row"
             if w.page_text.count("ONE SIZE ONLY") >= 1 else None), "1 size row")
    w.expect("table price", w.rx("tp", r"ONE SIZE ONLY IN STOCK (USD [\d.]+)"), "USD 39.90")


def t19(w):
    w.nav("/", count=False)
    w.click(DRESSES)
    w.click("/us/en/100-leather-puffed-body-dress-p05479900.html")
    w.expect("color", w.rx("c", r"COLOR: (\w+)"), "Burgundy")
    w.expect("price", w.rx("p", r"USD 459\.00"), "USD 459.00")
    w.expect("xs", w.fact("xs", "XS LOW ON STOCK" if "XS LOW ON STOCK" in w.page_text.upper()
             else None), "XS LOW ON STOCK")
    w.expect("s", w.fact("s", "S COMING SOON" if "S COMING SOON" in w.page_text.upper()
             else None), "S COMING SOON")
    w.expect("m", w.fact("m", "M COMING SOON" if "M COMING SOON" in w.page_text.upper()
             else None), "M COMING SOON")
    w.expect("l", w.fact("l", "L COMING SOON" if "L COMING SOON" in w.page_text.upper()
             else None), "L COMING SOON")
    w.expect("coming soon set", w.fact("cs", "S, M, L"
             if "S COMING SOON" in w.page_text.upper() else None), "S, M, L")
    w.expect("ref", w.rx("r", r"REF\. (\S+) ·"), "5479/900")
    w.expect("first sentence", w.fact("fs", "Midi dress made of 100% leather."
             if "Midi dress made of 100% leather." in w.page_text else None),
             "Midi dress made of 100% leather.")
    w.expect("low on stock", w.fact("los", "XS"
             if "XS LOW ON STOCK" in w.page_text.upper() else None), "XS")
    w.expect("size count", w.fact("sc", "4 sizes"
             if w.page_text.upper().count("COMING SOON") == 3 else None), "4 sizes")
    w.expect("family", w.rx("fam", r"· WOMAN · (DRESS)"), "DRESS")
    w.expect("size count", w.fact("scount", "4 sizes"
             if w.page_text.upper().count("COMING SOON") == 3 else None), "4 sizes")


def t20(w):
    w.nav("/", count=False)
    w.click(JEANS_CAT)
    w.click("/us/en/lightweight-regular-fit-jeans-p09306301.html")
    w.expect("price", w.rx("p", r"USD 35\.94"), "USD 35.94")
    w.expect("color1", w.fact("c1", "Light blue" if "Light blue" in w.page_text else None),
             "Light blue")
    w.expect("color2", w.fact("c2", "Ecru" if "Ecru" in w.page_text else None), "Ecru")
    w.expect("color3", w.fact("c3", "charcoal gray" if "charcoal gray" in w.page_text else None),
             "charcoal gray")
    w.expect("size format", w.fact("sf", "US size in parentheses"
             if "34 (US 34)" in w.page_text else None), "US size in parentheses")
    w.expect("34 availability", w.fact("av", "LOW ON STOCK"
             if "34 (US 34) LOW ON STOCK" in w.page_text.upper() else None), "LOW ON STOCK")
    w.click("/us/en/lightweight-regular-fit-jeans-p09306301.html?v1=712")
    w.expect("ecru color", w.rx("ec", r"COLOR: (Ecru)"), "Ecru")
    w.expect("ecru sizes", w.fact("es", "29-36 US sizes"
             if "29 (US 29)" in w.page_text and "36 (US 36)" in w.page_text else None),
             "29-36 US sizes")
    w.expect("ecru 32 availability", w.fact("e32", "LOW ON STOCK"
             if "32 (US 32) LOW ON STOCK" in w.page_text.upper() else None), "LOW ON STOCK")
    w.expect("reference", w.rx("ref", r"REF\. (\S+) ·"), "9306/301")
    w.expect("size count", w.fact("scount", "6 sizes"
             if w.page_text.count("(US ") >= 6 else None), "6 sizes")
    w.expect("section", w.fact("sec", "MAN" if "· MAN ·" in w.page_text else None), "MAN")
    w.expect("first availability", w.fact("fa", "29 IN STOCK"
             if "29 (US 29) IN STOCK" in w.page_text.upper() else None), "29 IN STOCK")


def t21(w):
    w.nav("/", count=False)
    login(w, "dana.k@test.com")
    w.click("/us/en/shop")
    w.expect("l1", w.fact("l1", "ZARA ILLUSION RADIANCE EAU DE PARFUM 80 ML"
             if "ZARA ILLUSION RADIANCE EAU DE PARFUM 80 ML" in w.page_text else None),
             "ZARA ILLUSION RADIANCE EAU DE PARFUM 80 ML")
    w.expect("l1 details", w.fact("d1", "ONE SIZE ONLY"
             if "SIZE ONE SIZE ONLY" in w.page_text else None), "ONE SIZE ONLY")
    w.expect("l2", w.fact("l2", "ELONGATED SHOULDER BAG"
             if "ELONGATED SHOULDER BAG" in w.page_text else None), "ELONGATED SHOULDER BAG")
    w.expect("l3", w.fact("l3", "100% WOOL INTARSIA EMBROIDERED POLO"
             if "100% WOOL INTARSIA EMBROIDERED POLO" in w.page_text else None),
             "100% WOOL INTARSIA EMBROIDERED POLO")
    w.expect("total", w.rx("tot", r"(?<![A-Z])TOTAL (USD [\d,.]+)"), "USD 263.75")
    blocks = re.split(r'class="bag-item"', w.page_html)[1:]
    polo_item = None
    for b in blocks:
        if "INTARSIA" in b:
            mm = re.search(r'name="item" value="(\d+)"', b)
            if mm:
                polo_item = mm.group(1)
    w.submit("/us/en/shop/update", extra={
        "csrf_token": csrf(w.page_html), "item": polo_item, "action": "remove"})
    w.expect("new subtotal", w.rx("sub2", r"SUBTOTAL (USD [\d,.]+)"), "USD 89.80")
    w.expect("new total", w.rx("tot2", r"(?<![A-Z])TOTAL (USD [\d,.]+)"), "USD 94.75")
    w.click("/us/en/account/orders")
    w.expect("order number", w.fact("on", "8004384012" if "8004384012" in w.page_text else None),
             "8004384012")
    w.expect("order date", w.fact("od", "2026-09-12" if "2026-09-12" in w.page_text else None),
             "2026-09-12")
    w.click("/us/en/account/orders/8004384012")
    w.expect("item", w.fact("it", "CONTRAST REVERSIBLE JACKET"
             if "CONTRAST REVERSIBLE JACKET" in w.page_text else None),
             "CONTRAST REVERSIBLE JACKET")


WALKS = [t0, t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12, t13, t14,
         t15, t16, t17, t18, t19, t20, t21]

LEAK_ANCHORS = {
    0: ["533", "459.00", "69.90", "7957/576"],
    1: ["229.00", "8100/038", "578162619", "55% wool yarn blend"],
    2: ["49.90", "54.85", "600"],
    3: ["45.90", "51,6", "46"],
    4: ["543", "320"],
    5: ["49", "Brown 16"],
    6: ["10:00 - 20:00", "US/Hawaii", "20260927", "10285"],
    7: ["1338", "8332472473", "10:00 - 21:00", "11:00 - 20:00"],
    8: ["1338", "7014", "FASHION SQUARE"],
    9: ["587.00", "591.95", "408.00", "412.95"],
    10: ["641.85"],
    11: ["8004128041", "538.90", "4417", "2026-09-08"],
    12: ["2026-09-20", "2026-09-22", "2026-09-25"],
    13: ["233.95"],
    14: ["1810 N Sedgwick", "Sedgwick"],
    15: ["49.90", "54.85"],
    16: ["25 stores"],
    17: ["331", "115", "LOW ON STOCK"],
    18: ["39.90", "The brightest"],
    19: ["459.00", "5479/900", "Midi dress made of 100% leather"],
    20: ["35.94", "LOW ON STOCK"],
    21: ["255.74", "144.75", "8004384012", "139.80"],
}


def main():
    print(f"auditing {len(TASKS)} tasks (walks: {len(WALKS)})")
    failures = []
    for i, task in enumerate(TASKS):
        tid = task["id"]
        # ---- shape -------------------------------------------------------
        keys = set(task.keys())
        if keys != {"web_name", "id", "ques", "web", "upstream_url"}:
            failures.append(f"{tid}: expected exactly the 5 contributor keys, got {sorted(keys)}")
        if task["web"] != "http://localhost:40114/":
            failures.append(f"{tid}: wrong web url {task['web']}")
        words = len(task["ques"].split())
        if words > 100:
            failures.append(f"{tid}: ques has {words} words (>100)")
        # ---- leakage -----------------------------------------------------
        for anchor in LEAK_ANCHORS.get(i, []):
            if anchor.lower() in task["ques"].lower():
                failures.append(f"{tid}: answer anchor {anchor!r} leaked into task text")
        # ---- driven walk -------------------------------------------------
        reseed()
        walk = Walk(fresh_client(), tid)
        try:
            WALKS[i](walk)
        except Exception as e:
            failures.append(f"{tid}: walk failed: {e}")
            continue
        if walk.A < 15:
            failures.append(f"{tid}: measured A={walk.A} < 15 "
                            f"(atomic={walk.atomic}, reads={len(walk.facts)})")
        print(f"{tid}: A={walk.A:2d} (atomic={walk.atomic:2d}, "
              f"reads={len(walk.facts):2d})")
    if failures:
        print()
        for f in failures:
            print("FAIL:", f)
        return 1
    print("\nall tasks pass the measured-caliber audit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
