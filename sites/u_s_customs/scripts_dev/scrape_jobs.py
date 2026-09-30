#!/usr/bin/env python3
"""Phase 7: USAJOBS detail scrape for the CBP featured job postings.

The careers.cbp.gov pages feature real CBP job postings hosted on
usajobs.gov; this fetches each posting's public page and extracts the
structured announcement (title, org, series/grade, salary, locations,
closing date, duties, requirements).

Run: python3.11 scrape_jobs.py
Writes scraped_data/jobs/<control>.json
"""
import json
import pathlib
import random
import re
import time

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "scraped_data" / "jobs"
OUT.mkdir(parents=True, exist_ok=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def load_job_urls():
    careers = ROOT / "scraped_data" / "careers"
    urls = {}
    for f in sorted(careers.glob("*.json")):
        d = json.load(open(f))
        for j in d.get("jobs", []):
            urls[j["url"]] = j["title"]
    return urls


def extract_job(html, url):
    soup = BeautifulSoup(html, "lxml")
    for t in soup.select("script,style,noscript"):
        t.decompose()
    text = " ".join(soup.get_text(" ").split())
    title = ""
    h1 = soup.select_one("h1")
    if h1:
        title = " ".join(h1.get_text().split())

    facts = {}
    for dt in soup.select("dt"):
        key = " ".join(dt.get_text().split())
        dd = dt.find_next_sibling("dd")
        if dd is not None:
            facts[key] = " ".join(dd.get_text(" ").split())

    def fact(name, maxlen=160):
        for k, v in facts.items():
            if k.lower() == name.lower():
                return v[:maxlen]
        return ""

    salary = fact("Salary", 200)
    m = re.search(r"\$[\d,]+\s*[-\u2013]\s*\$?[\d,]+", salary)
    salary = m.group(0) if m else salary[:60]
    grade = fact("Pay scale & grade", 80) or fact("Pay scale &amp; grade", 80)
    m = re.match(r"(GL|GS)\s*\d+\s*[-\u2013]", grade)
    series_grade = grade[:40] if m else grade[:40]
    announcement = fact("Announcement number", 40)
    control = fact("Control number", 20)
    telework = fact("Telework eligible", 30)
    drug_test = fact("Drug test", 20)
    appointment = fact("Appointment type", 30)
    schedule = fact("Work schedule", 40)
    promotion = fact("Promotion potential", 12)
    dates = re.findall(r"\b(\d{2})/(\d{2})/(\d{4})\b", text)
    closing = ""
    if dates:
        best = max(dates, key=lambda d: (d[2], d[0], d[1]))
        closing = f"{int(best[0]):02d}/{int(best[1]):02d}/{best[2]}"

    def section(name, limit=3500):
        h = soup.find(lambda t: t.name in ("h2", "h3")
                      and t.get_text().strip() == name)
        if not h:
            return ""
        # the announcement sections live in a .page-section wrapper around
        # the heading; the heading row itself carries only a Help link.
        node = h
        for _ in range(6):
            node = node.parent
            if node is None:
                break
            cls = node.get("class") or []
            if "page-section" in cls:
                txt = " ".join(node.get_text(" ").split())
                # drop the leading "Duties Help" / "Summary Help" chrome
                txt = re.sub(r"^" + re.escape(name) + r"\s*Help\s*", "", txt)
                txt = txt.replace("  ", " ")
                return txt[:limit]
        parts = []
        for sib in h.find_next_siblings():
            if sib.name in ("h2", "h3"):
                break
            parts.append(" ".join(sib.get_text(" ").split()))
        return " ".join(parts)[:limit]

    summary = section("Summary", 2200)
    duties = section("Duties", 4000)
    requirements = section("Requirements", 3000)
    qualifications = section("Qualifications", 3000)
    open_to = section("This job is open to", 400)
    dept = ""
    if "Department of Homeland Security" in text:
        dept = ("Department of Homeland Security \u2014 Customs and "
                "Border Protection")
    org = ""
    m = re.search(r"(U\.S\. Border Patrol|Air and Marine Operations|"
                   r"Office of Field Operations|Office of Trade|"
                   r"Office of Professional Responsibility|"
                   r"Office of Chief Counsel)", text)
    if m:
        org = m.group(1)
    location = ""
    m = re.search(r"Many locations\s*[:\u2014]?\s*([A-Za-z ,.\u2014-]{5,120}?)(?:\s{2,}|\s+Salary|\s+Duties|$)", text)
    if not m:
        m = re.search(r"\bLocation\b\s*([A-Z][A-Za-z ,.\u2014-]{5,120}?)(?:\s+Salary|\s+Duties|\s+Overview|\s{2,})", text)
    if m:
        location = " ".join(m.group(1).split())[:120]
    return {"url": url, "title": title, "org": org, "department": dept,
            "series_grade": series_grade, "salary": salary,
            "grade_raw": grade, "announcement_number": announcement,
            "promotion_potential": promotion, "telework": telework,
            "drug_test": drug_test, "appointment_type": appointment,
            "work_schedule": schedule, "location": location,
            "closing": closing, "summary": summary, "duties": duties,
            "requirements": requirements,
            "qualifications": qualifications, "open_to": open_to,
            "control": control or url.rstrip("/").split("/")[-1]}


def main():
    urls = load_job_urls()
    print(f"[jobs] {len(urls)} postings")
    done = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(user_agent=UA,
                                  viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        for url, title in urls.items():
            control = url.rstrip("/").split("/")[-1]
            out = OUT / f"{control}.json"
            if out.exists():
                done += 1
                continue
            ok = False
            for attempt in range(4):
                try:
                    r = page.goto(url, wait_until="domcontentloaded",
                                   timeout=45000)
                    page.wait_for_timeout(2500)
                    html = page.content()
                    if (r.status if r else 0) == 200 and len(html) > 50000:
                        rec = extract_job(html, url)
                        rec["control"] = control
                        rec["careers_title"] = title
                        out.write_text(json.dumps(rec, indent=1))
                        done += 1
                        print(f"[job] {control} {rec['title'][:50]}")
                        ok = True
                        break
                except Exception as e:
                    print(f"[retry {control}.{attempt}] {str(e)[:60]}")
                time.sleep(4 + attempt * 4)
            if not ok:
                print(f"[FAIL job] {control}")
            time.sleep(random.uniform(0.8, 1.6))
        browser.close()
    print(f"[jobs] done: {done}")


if __name__ == "__main__":
    main()
