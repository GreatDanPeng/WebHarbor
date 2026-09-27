#!/usr/bin/env python3
"""Append reviewer grading keys (verifier_path + judge_rubric) to tasks.jsonl.

Contract: the five contributor keys (web_name, id, ques, web, upstream_url) are
preserved BYTE-IDENTICALLY — each original line is split on the closing brace
of the 5-key object and the two new keys are appended before it. No `answer`
key is ever written. Idempotent: rows that already carry verifier_path are
left untouched.
"""
import json
import sys
from pathlib import Path

TASKS = Path(__file__).resolve().parents[1] / "tasks.jsonl"

RUBRICS = {
    0: "FACT CHECKPOINTS: (1) The trajectory MUST complete the swimwear quiz (Women's -> Racing -> Fastskin Valor), open the quiz results, open the recommended kneeskin product page, and reach the order confirmation. (2) The final answer MUST report order SP100008 and the total charged 122.99 (the cheapest recommended kneeskin, size 26, Express Delivery). (3) DB: exactly one new order with one order_item line for the cheapest recommended kneeskin in size 26; nothing else may change.",
    1: "FACT CHECKPOINTS: (1) The trajectory MUST sign in as bob.c@test.com, open his wishlist, and open the Men's Fastskin LZR Pure Valor 2.0 Jammer Blue product page. (2) The final answer MUST name the removed non-Fastskin-LZR jammer (the Hyperboom Jammer), every item remaining on the wishlist (Fastskin LZR Pure Intent 2.0 Jammer, iQ Vanquisher 3.0 goggles, 25L Flex Bag, Endurance+ Logo Thinstrap Bikini Set, plus the added Valor Blue jammer), and the new wishlist count 5. (3) DB: exactly one wishlist row removed for Bob (the Hyperboom Jammer) and exactly one added (the Fastskin LZR Pure Valor 2.0 Jammer Blue); nothing else may change.",
    2: "FACT CHECKPOINTS: (1) The trajectory MUST sign in as alice.j@test.com, open her basket, open both Endurance+ Medalist Swimsuit colourway product pages (Black and Navy), apply the newsletter welcome code in the basket, and reach the order confirmation. (2) The final answer MUST report order SP100008 and the total 52.10. (3) DB: Alice's two seed basket rows cleared, exactly one new order with two order_items (Black size 34 and Navy size 34) carrying the WELCOME15 discount; nothing else may change.",
    3: "FACT CHECKPOINTS: (1) The trajectory MUST open the size guides page (women's table), open the Sculpture Boom Back Swimsuit Black product page, and reach the order confirmation. (2) The final answer MUST report the size derived from the women's cm table for bust 91 / waist 77 / hips 102 (36), order SP100008 and the total 72.00 (Standard Delivery free over £50). (3) DB: exactly one new order with one order_item (Sculpture Boom Back Swimsuit Black, size 36); nothing else may change.",
    4: "FACT CHECKPOINTS: (1) The trajectory MUST sign in as david.k@test.com, open the account order history and the detail page of his jammer order, then submit the contact form. (2) The final answer MUST report order SP100007 with status Dispatched, tracking SDRM100522663GB, the Visa card ending 9902, and the case reference CAS100001. (3) DB: exactly one new contact case (category Orders & Delivery, sub-category Where is my order, quoting SP100007); nothing else may change.",
    5: "FACT CHECKPOINTS: (1) The trajectory MUST browse the men's fitness collection (both result pages) and open the product page of the most expensive in-stock men's fitness jammer under £50 with size 34 available (the Hyperboom Splice Mid Jammer; the Navy colourway is sold out in 34 so the Navy/Green colourway is the buy). (2) The final answer MUST report that product, order SP100008 and the total 43.99 (Express Delivery). (3) DB: exactly one new order with one order_item (size 34); nothing else may change.",
    6: "FACT CHECKPOINTS: (1) The trajectory MUST open the All Goggles catalogue, use its lens-type facet (Prescription), open the chosen optical goggles product page, and reach the order confirmation. (2) The final answer MUST report the cheapest in-stock prescription goggles offered in a -4.5 lens under £25 (the Hydropure Optical Goggles), order SP100008 and the total 27.74. (3) DB: exactly one new order with one order_item (Hydropure, lens size -4.5); nothing else may change.",
    7: "FACT CHECKPOINTS: (1) The trajectory MUST sign in as carol.d@test.com, open the profile page and the addresses page. (2) The final answer MUST report 2 saved addresses with the Newquay Home address as the default. (3) DB: Carol's phone updated to the given number, exactly one address added (Home, 3 Cliffside Road, Newquay, TR7 1AA, default), the Plymouth address removed, and the previous default un-flagged; nothing else may change.",
    8: "FACT CHECKPOINTS: (1) The trajectory MUST sign in as alice.j@test.com, open her wishlist, and open the Women's Sculpture Boom Back Swimsuit Black product page. (2) The final answer MUST name both removed non-swimsuit items (the Men's Endurance+ Jammer and the Fastskin Hyper Elite Mirrored Goggles), the items remaining on the wishlist (the Fastskin LZR Pure Valor 2.0 Openback Kneeskin and the Hyperboom Printed Medalist Swimsuit, plus the added Sculpture Boom Back Swimsuit), and the final wishlist count 3. (3) DB: exactly two wishlist rows removed for Alice (the jammer and the goggles) and exactly one added (the Sculpture Boom Back Swimsuit Black); nothing else may change.",
    9: "FACT CHECKPOINTS: (1) The trajectory MUST sign in as carol.d@test.com, open her basket, add every in-stock adult swim cap in purple (two caps), and reach the order confirmation. (2) The final answer MUST report the final total 51.88 and that delivery was free (Standard Delivery free over £50). (3) DB: exactly one new order containing her two pre-existing basket items plus the two adult purple caps, Standard Delivery at £0.00; nothing else may change.",
    10: "FACT CHECKPOINTS: (1) The trajectory MUST open every colourway product page of the Women's Hyperboom Printed Medalist Swimsuit and reach the order confirmation. (2) The final answer MUST report each colourway's current price and which are sold out in size 38, then order SP100008 and the total 38.99 (the cheapest colourway still available in size 38). (3) DB: exactly one new order with one order_item (size 38); nothing else may change.",
    11: "FACT CHECKPOINTS: (1) The trajectory MUST open every colourway product page of the Women's Endurance+ Medalist Swimsuit and sign in as alice.j@test.com. (2) The final answer MUST report each colourway's current price, which are on sale and the savings, and the most expensive colourway. (3) DB: exactly one wishlist row added for Alice (the Navy colourway); nothing else may change.",
    12: "FACT CHECKPOINTS: (1) The trajectory MUST open the blog index and the goggle-care article, the FAQs page, and submit the contact form. (2) The final answer MUST report the goggle-care rules, the swimsuit rinse advice from the FAQ, and the case reference CAS100001. (3) DB: exactly one new contact case (category Product Enquiry, sub-category Goggles); nothing else may change.",
    13: "FACT CHECKPOINTS: (1) The trajectory MUST open the Biofuse 2.0 Goggles Black product page and reach the order confirmation as a guest (no account creation). (2) The final answer MUST report order SP100008 and the Express Delivery time quoted. (3) DB: exactly one new order with one order_item (One Size, Express Delivery); no user row may be created and nothing else may change.",
    14: "FACT CHECKPOINTS: (1) The trajectory MUST register the new account, open the cheapest in-stock Kids Sunny G goggles product page, add it to the wishlist, and open the profile page. (2) The final answer MUST report the saved goggles (the cheapest in-stock Kids Sunny G goggles) and the wishlist count 1. (3) DB: exactly one new user (name, email, phone as given) and exactly one wishlist row for that user; nothing else may change.",
    15: "FACT CHECKPOINTS: (1) The trajectory MUST sign up for the newsletter, open the Bubble Active+ Cap White product page, apply the revealed welcome code in the basket, and reach the order confirmation. (2) The final answer MUST report the full code, the discount amount 2.25 and the order total 18.74. (3) DB: exactly one newsletter signup, exactly one new order carrying the WELCOME15 discount; nothing else may change.",
    16: "FACT CHECKPOINTS: (1) The trajectory MUST open the size guides page (kids' table), open the Boys' Endurance+ Jammer product page, and reach the order confirmation. (2) The final answer MUST report the size/age band derived from the kids' table for a 9-year-old with a 66cm waist (9-10 Yrs), order SP100008 and the total 20.62. (3) DB: exactly one new order with one order_item in the 9-10 band; nothing else may change.",
    17: "FACT CHECKPOINTS: (1) The trajectory MUST open the Team Speedo page, the athlete pages needed to find the motto 'Never fear failure', and the Fastskin LZR Ignite Kneeskin product pages. (2) The final answer MUST list the four GB athletes, name the motto athlete and the Speedo suit he wore at Paris 2024, and report the price of the cheapest in-stock Women's Fastskin LZR Ignite Kneeskin colourway (114.00). (3) No DB rows may change.",
    18: "FACT CHECKPOINTS: (1) The trajectory MUST complete the goggles quiz (Adults -> Fitness -> Clear), open the quiz results, open the cheapest in-stock recommended pair's product page, and reach the order confirmation. (2) The final answer MUST report that product, order SP100008 and the total 23.99. (3) DB: exactly one new order with one order_item; nothing else may change.",
    19: "FACT CHECKPOINTS: (1) The trajectory MUST sign in as david.k@test.com, open the payment methods page and the wishlist. (2) The final answer MUST report 1 saved card with the new Visa as the default, and the remaining wishlist count 4. (3) DB: David's card row replaced by the new default Visa (given number/expiry, Club label) and exactly the two pairs of goggles removed from his wishlist; nothing else may change.",
    20: "FACT CHECKPOINTS: (1) The trajectory MUST open the Adult Silicone Cap Purple product page and reach the order confirmation as a guest. (2) The final answer MUST report order SP100008 and the total 12.74 (Standard Delivery under £10). (3) DB: exactly one new order with one order_item; no user row may be created and nothing else may change.",
}


def main():
    lines = TASKS.read_text(encoding="utf-8").splitlines(keepends=False)
    out = []
    appended = skipped = 0
    for line in lines:
        row = json.loads(line)
        n = int(row["id"].split("--")[1])
        if "verifier_path" in row:
            skipped += 1
            out.append(line)
            continue
        # byte-preserving append: find the closing brace of the original object
        obj = line.rstrip()
        assert obj.endswith("}")
        body = obj[:-1].rstrip()
        sep = "," if (body and not body.endswith(",")) else ""
        new_line = (body + sep
                    + f' "verifier_path": "sites/speedo/verify/verify_{n}.py",'
                    + f' "judge_rubric": {json.dumps(RUBRICS[n])}'
                    + "}")
        # sanity: original 5 keys byte-identical
        before = json.loads(line)
        after = json.loads(new_line)
        assert all(after[k] == before[k] for k in before), n
        assert set(after) == set(before) | {"verifier_path", "judge_rubric"}, n
        assert "answer" not in after
        out.append(new_line)
        appended += 1
    TASKS.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"appended={appended} skipped={skipped} -> {TASKS}")


if __name__ == "__main__":
    main()
