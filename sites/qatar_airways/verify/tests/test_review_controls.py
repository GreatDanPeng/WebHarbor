"""Reviewer controls: copies of synthetic fixtures, not browser trajectories."""
import json
import sqlite3
from pathlib import Path
import pytest
from _support import *

def change_answer(run, fn):
    p=run/'trajectory.json';t=json.loads(p.read_text());t['final_answer']=fn(t['final_answer']);p.write_text(json.dumps(t))


def test_numeric_substring_is_not_a_total(tmp_path):
    run,_=honest_run(tmp_path,0)
    change_answer(run,lambda a:a.replace('1,490','91,490'))
    assert run_verifier(0,run)['pass'] is False


def test_no_screenshot_references_rejected(tmp_path):
    run,_=honest_run(tmp_path,0);p=run/'trajectory.json';t=json.loads(p.read_text())
    for step in t['steps']:
        for k in ['screenshot','screenshot_before','screenshot_after']:step.pop(k,None)
    p.write_text(json.dumps(t));assert run_verifier(0,run)['pass'] is False


def test_other_booking_unchanged(tmp_path):
    run,_=honest_run(tmp_path,5)
    with sqlite3.connect(run/'after.db') as c:c.execute("UPDATE bookings SET status='cancelled' WHERE pnr != 'QR92XN'")
    assert run_verifier(5,run)['pass'] is False


def test_brazil_exception_not_general_allowance(tmp_path):
    run,_=honest_run(tmp_path,15);change_answer(run,lambda a:a.replace('10kg','7kg'))
    assert run_verifier(15,run)['pass'] is False


def test_other_member_unchanged(tmp_path):
    run,_=honest_run(tmp_path,18)
    with sqlite3.connect(run/'after.db') as c:c.execute("UPDATE users SET country='Brazil' WHERE email='alice.j@test.com'")
    assert run_verifier(18,run)['pass'] is False
