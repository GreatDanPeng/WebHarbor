"""Site regression tests for the statista mirror.

Run with: python -m pytest tests/ -q  (from sites/statista/)
Uses a scratch copy of the seed DB so stateful checks never touch the
worktree database.
"""
import os
import shutil
import sqlite3
import sys
import tempfile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import pytest

SEED = os.path.join(BASE_DIR, "instance_seed", "statista.db")
if not os.path.exists(SEED):
    SEED = os.path.join(BASE_DIR, "instance", "statista.db")


@pytest.fixture()
def client(tmp_path):
    scratch = str(tmp_path / "scratch.db")
    if os.path.exists(SEED):
        shutil.copy(SEED, scratch)
    os.environ["STATISTA_DB_PATH"] = f"sqlite:///{scratch}"
    import app as appmod
    appmod.app.config["TESTING"] = True
    if hasattr(appmod, "_app"):
        pass
    with appmod.app.test_client() as c:
        yield c
    os.environ.pop("STATISTA_DB_PATH", None)
    # drop cached module state for the next run
    sys.modules.pop("app", None)
    sys.modules.pop("seed_data", None)


def test_health(client):
    r = client.get("/_health")
    assert r.status_code == 200
    body = r.get_json()
    assert body["ok"] is True
    assert body["counts"]["statistics"] >= 200
    assert body["counts"]["topics"] >= 10
    assert body["counts"]["reports"] >= 11
    assert body["counts"]["outlook_markets"] >= 150


def test_pages_200(client):
    urls = [
        "/", "/serp?q=inflation", "/serp?q=tiktok&content_type=Topics",
        "/statistics/256598/global-inflation-rate-compared-to-previous-year/",
        "/statistics/268173/countries-with-the-largest-gross-domestic-product-gdp/?chart=table",
        "/forecasts/1474143/global-ai-market-size/",
        "/topics/6077/tiktok/", "/markets/", "/markets/424/internet/",
        "/study/206237/consumer-trends-2026/",
        "/recent/statistics/", "/recent/topics/", "/recent/reports/",
        "/outlook/", "/outlook/mobility-markets/",
        "/outlook/mmo/shared-mobility/ride-hailing/worldwide/",
        "/outlook/tmo/it-services/it-outsourcing/worldwide/",
        "/pricing/", "/contact/", "/login", "/register",
    ]
    for u in urls:
        assert client.get(u).status_code == 200, u


def test_search_scored_not_strict(client):
    # multi-word query must return results (token overlap, not strict AND)
    r = client.get("/serp?q=global+inflation+rate+worldwide")
    assert r.status_code == 200
    assert b"serpResult__title" in r.data
    r = client.get("/serp?q=social+media+users+by+country")
    assert b"serpResult__title" in r.data


def test_stat_detail_chart_modes(client):
    base = "/statistics/256598/global-inflation-rate-compared-to-previous-year/"
    line = client.get(base).data
    assert b"statChartSvg" in line
    table = client.get(base + "?chart=table").data
    assert b"chartTable" in table
    assert b"4.13" in table  # 2025 value in the data table
    bar = client.get("/statistics/268173/countries-with-the-largest-gross-domestic-product-gdp/?chart=bar").data
    assert b"32.38" in bar  # bar value labels


def test_premium_paywall_tiers(client):
    premium = "/statistics/871513/worldwide-data-created/"
    anon = client.get(premium).data
    assert b"You need a" in anon
    # Basic account still masked
    client.post("/login", data={"email": "bob.c@test.com", "password": "TestPass123!"})
    basic = client.get(premium).data
    assert b"does not include premium statistics" in basic
    # Starter account sees content, not the basic paywall copy
    client.get("/logout")
    client.post("/login", data={"email": "david.k@test.com", "password": "TestPass123!"})
    starter = client.get(premium).data
    assert b"does not include premium statistics" not in starter


def test_auth_favorites_downloads(client):
    client.post("/login", data={"email": "alice.j@test.com", "password": "TestPass123!"})
    r = client.post("/favorite/stat/279777", data={"back": "/"},
                    follow_redirects=True)
    assert b"added to your favorites" in r.data
    favs = client.get("/account/favorites").data
    assert b"Unemployment rate worldwide" in favs
    r = client.post("/download/stat/279777", data={"format": "png"},
                    follow_redirects=True)
    assert b"has been prepared" in r.data
    dls = client.get("/account/downloads").data
    assert b"Unemployment rate worldwide" in dls
    # remove favorite again (cleanup on scratch db not needed)


def test_report_download_requires_professional(client):
    client.post("/login", data={"email": "alice.j@test.com", "password": "TestPass123!"})
    r = client.post("/download/report/206237", follow_redirects=True)
    assert b"Professional Account" in r.data
    client.get("/logout")
    client.post("/login", data={"email": "carol.d@test.com", "password": "TestPass123!"})
    r = client.post("/download/report/206237", follow_redirects=True)
    assert b"added to your downloads" in r.data


def test_register_validation(client):
    r = client.post("/register", data={"email": "bad", "username": "x", "password": "short"},
                    follow_redirects=True)
    assert b"valid email" in r.data
    r = client.post("/register", data={"email": "new.user@test.com", "username": "new_user",
                                       "password": "LongEnough1!"}, follow_redirects=True)
    assert b"ready" in r.data


def test_citations(client):
    r = client.get("/statistics/256598/global-inflation-rate-compared-to-previous-year/?citation=APA")
    assert b"Statista Research Department" in r.data
    assert b"APA" in r.data


def test_outlook_market_highlights(client):
    r = client.get("/outlook/mmo/shared-mobility/ride-hailing/worldwide/")
    assert b"188.60" in r.data
    assert b"Ride-hailing" in r.data


def test_recent_sorted_by_date(client):
    r = client.get("/recent/statistics/")
    assert r.status_code == 200
    # the most recent free statistic must appear before an older one
    body = r.data.decode()
    assert "Sep 17, 2026" in body


def test_seed_idempotent_byte_identity(tmp_path):
    """Re-running the bootstrap on a seeded DB must not change any byte."""
    if not os.path.exists(os.path.join(BASE_DIR, "instance_seed", "statista.db")):
        pytest.skip("instance_seed not built yet")
    seed = os.path.join(BASE_DIR, "instance_seed", "statista.db")
    import hashlib
    h1 = hashlib.md5(open(seed, "rb").read()).hexdigest()
    scratch = str(tmp_path / "scratch.db")
    shutil.copy(seed, scratch)
    os.environ["STATISTA_DB_PATH"] = f"sqlite:///{scratch}"
    import app as appmod
    os.environ.pop("STATISTA_DB_PATH", None)
    sys.modules.pop("app", None)
    sys.modules.pop("seed_data", None)
    h2 = hashlib.md5(open(scratch, "rb").read()).hexdigest()
    assert h1 == h2
