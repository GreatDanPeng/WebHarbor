"""Entity-specific ticket comparisons; prices derive from the frozen seed."""
import re
from verify_lib import check_visited_path, check_answer_number

def endpoints(db):
    return db.execute("SELECT * FROM events WHERE performer_id=(SELECT id FROM performers WHERE slug='seattle-kraken') ORDER BY starts_at").fetchall()

def check_endpoints(judge, traj, db):
    answer=traj.get("final_answer", "")
    events=endpoints(db)
    for e in [events[0], events[-1]]:
        check_visited_path(judge, traj, "event_"+str(e["upstream_id"]), r"/event/"+str(e["upstream_id"]))
        rows=db.execute("SELECT * FROM listings WHERE event_id=? AND is_sold=0 ORDER BY price,id",(e["id"],)).fetchall()
        best=rows[0]
        judge.check("cheapest_seat_"+str(e["id"]), str(best["section"]).casefold() in answer.casefold() and str(best["row"] or "").casefold() in answer.casefold())

def check_explore(judge, traj, db):
    answer=traj.get("final_answer", "")
    events=db.execute("SELECT * FROM events WHERE listing_count>0 ORDER BY starts_at,id LIMIT 3").fetchall()
    for e in events:
        check_visited_path(judge, traj, "event_"+str(e["upstream_id"]),r"/event/"+str(e["upstream_id"]))
        check_answer_number(judge, answer, "getin_"+str(e["id"]),e["min_price"])
        check_answer_number(judge, answer, "listings_"+str(e["id"]),e["listing_count"])
        judge.check("event_name_"+str(e["id"]),e["name"].casefold() in answer.casefold())
    prices=sorted(e["min_price"] for e in events)
    for price in prices[1:]:check_answer_number(judge,answer,"saving_"+str(price),price-prices[0])
