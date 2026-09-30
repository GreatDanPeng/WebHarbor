#!/usr/bin/env python3
"""Build the tracked source_data/ snapshots from the gitignored scraped_data/
captures (upstream zara.com/us JSON API + SSR payloads captured 2026-09-29).

Every tracked snapshot is a deterministic trim of the real upstream capture;
the trim policy is declared in provenance.json. Re-run: nothing here talks to
the network.
"""
import json
import os
import re
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
SCRAPE = os.path.join(SITE, "scraped_data")
OUT = os.path.join(SITE, "source_data")

# The 13 mirrored categories: categorySeoId -> (category id, section, name)
CATEGORIES = OrderedDict([
    (1066, (2420896, "WOMAN", "DRESSES")),
    (1114, (2417772, "WOMAN", "JACKETS")),
    (1152, (2420306, "WOMAN", "KNITWEAR")),
    (1251, (2730527, "WOMAN", "SHOES")),
    (1024, (2417728, "WOMAN", "BAGS")),
    (737, (2431994, "MAN", "SHIRTS")),
    (659, (2432131, "MAN", "JEANS")),
    (640, (2536906, "MAN", "JACKETS")),
    (769, (2436382, "MAN", "SHOES")),
    (360, (2427552, "KIDS", "GIRL DRESSES & JUMPSUITS")),
    (231, (2426482, "KIDS", "BOY COATS & JACKETS")),
    (1415, (2419833, "BEAUTY", "PERFUMES")),
    (4414, (1881272, "BEAUTY", "MAKEUP")),
])
MAX_PER_CATEGORY = 10
GALLERY_PER_COLOR = 4


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump(name, data):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=False)
        f.write("\n")
    print(f"wrote {name} ({os.path.getsize(path)} bytes)")


def cat_products_file(cat_id):
    """Find the captured products JSON for a zara category id."""
    for fn in sorted(os.listdir(os.path.join(SCRAPE, "captures"))):
        if "category" in fn and f"_{cat_id}_" in fn and fn.endswith("products.json"):
            return os.path.join(SCRAPE, "captures", fn)
    raise FileNotFoundError(f"no products capture for category {cat_id}")


def grid_products(cat_id):
    """Upstream grid order of the category: (seo_product_id, name, ref)."""
    d = load(cat_products_file(cat_id))
    seen = set()
    out = []
    for e in d["productGroups"][0]["elements"]:
        for c in e.get("commercialComponents", []):
            if c.get("type") != "Product" or not c.get("name") or not c.get("seo"):
                continue
            seo = c["seo"]
            pid = seo.get("seoProductId")
            if not pid or pid in seen:
                continue
            seen.add(pid)
            out.append({
                "seo_product_id": pid,
                "keyword": seo["keyword"],
                "name": c["name"],
                "reference": c.get("reference"),
                "price": c.get("price"),
                "is_on_sale": bool(c.get("isOnSale")),
                "old_price": c.get("oldPrice"),
                "available_colors": c.get("availableColors") or len(
                    (c.get("detail") or {}).get("colors") or []) or 1,
                "family": c.get("familyName"),
            })
    return out


def product_from_pdp(payload):
    p = payload["product"]
    det = p.get("detail") or {}
    colors = []
    for c in det.get("colors") or []:
        gallery = []
        seen_names = set()
        for x in c.get("xmedia") or []:
            du = (x.get("extraInfo") or {}).get("deliveryUrl")
            nm = x.get("name")
            if du and x.get("type") == "image" and nm not in seen_names:
                seen_names.add(nm)
                gallery.append(du)
            if len(gallery) >= GALLERY_PER_COLOR:
                break
        if not gallery:  # mainImgs fallback
            for x in c.get("mainImgs") or []:
                du = (x.get("extraInfo") or {}).get("deliveryUrl")
                if du:
                    gallery.append(du)
                if len(gallery) >= GALLERY_PER_COLOR:
                    break
        thumb = None
        for x in c.get("colorSelectorMedias") or []:
            du = (x.get("extraInfo") or {}).get("deliveryUrl")
            if du:
                thumb = du
                break
        if thumb is None and gallery:
            thumb = gallery[0]
        sizes = []
        for s in c.get("sizes") or []:
            sizes.append({
                "id": s.get("id"),
                "name": s.get("name"),
                "availability": s.get("availability"),
                "price": s.get("price"),
                "sku": s.get("sku"),
                "equivalent_size_id": s.get("equivalentSizeId"),
                "reference": s.get("reference"),
            })
        colors.append({
            "id": c.get("id"),
            "name": c.get("name"),
            "hex": c.get("hexCode"),
            "price": c.get("price"),
            "reference": c.get("reference"),
            "description": c.get("description"),
            "tags": [t.get("displayName") for t in (c.get("tagTypes") or [])
                     if t.get("displayName")],
            "sizes": sizes,
            "gallery": gallery,
            "thumb": thumb,
        })
    seo = p.get("seo") or {}
    return {
        "id": p.get("id"),
        "reference": p.get("reference") or det.get("reference"),
        "display_reference": det.get("displayReference"),
        "name": p.get("name"),
        "kind": p.get("kind"),
        "section_name": p.get("sectionName"),
        "family": p.get("familyName"),
        "subfamily": p.get("subfamilyName"),
        "seo_keyword": seo.get("keyword"),
        "seo_product_id": seo.get("seoProductId"),
        "first_visible_date": p.get("firstVisibleDate"),
        "size_guide_enabled": bool((p.get("sizeGuide") or {}).get("enabled")),
        "colors": colors,
    }


def build_categories():
    tree = load(os.path.join(SCRAPE, "captures",
                             "005_www.zara.com_us_en_categories.json"))
    keep_sections = {"I2024-MUJER": "WOMAN", "I2024-HOMBRE": "MAN",
                     "I2024-NINOS": "KIDS", "I2024-BEAUTY": "BEAUTY"}

    def trim_node(node, depth):
        subs = node.get("subcategories") or []
        picked = []
        for s in subs:
            name = (s.get("name") or "").strip()
            if not name:
                continue
            if s.get("hasSubcategories"):
                sub = trim_node(s, depth + 1)
                if sub:
                    picked.append(sub)
            else:
                seo = (s.get("seo") or {}).get("seoCategoryId")
                # keep only catalog leaf categories mirrored by some product
                picked.append({
                    "id": s.get("id"), "name": name,
                    "seo_id": seo,
                    "mirrored": seo in CATEGORIES,
                })
        return {"id": node.get("id"), "name": (node.get("name") or "").strip(),
                "seo_id": (node.get("seo") or {}).get("seoCategoryId"),
                "children": picked}

    sections = []
    for top in tree["categories"]:
        if top["key"] not in keep_sections:
            continue
        sections.append({
            "name": keep_sections[top["key"]],
            "id": top["id"],
            "children": [trim_node(s, 1) for s in (top.get("subcategories") or [])
                         if (s.get("name") or "").strip()][:10],
        })
    return sections


def main():
    os.makedirs(OUT, exist_ok=True)

    # ---------------------------------------------------------------- nav --
    dump("categories.json", {
        "captured_from": "https://www.zara.com/us/en/categories?ajax=true",
        "sections": build_categories(),
    })

    # ----------------------------------------------------------- pdp sets --
    pdps = {}
    for fn in os.listdir(os.path.join(SCRAPE, "pdp_payloads")):
        if not fn.endswith(".json"):
            continue
        d = load(os.path.join(SCRAPE, "pdp_payloads", fn))
        p = d.get("product") or {}
        if not p.get("name") or not p.get("seo"):
            continue
        pdps[p["seo"]["seoProductId"]] = d

    # ------------------------------------------------- products + catalog --
    catalog = []
    by_pid = {}
    categories_meta = []
    for seo_id, (cat_id, section, name) in CATEGORIES.items():
        grid = grid_products(cat_id)
        in_cat = [g for g in grid if g["seo_product_id"] in pdps][:MAX_PER_CATEGORY]
        keep = []
        for g in in_cat:
            row = product_from_pdp(pdps[g["seo_product_id"]])
            if row["id"] not in by_pid:
                by_pid[row["id"]] = row
                catalog.append(row)
            keep.append(g["seo_product_id"])
        categories_meta.append({
            "seo_id": seo_id, "id": cat_id, "section": section, "name": name,
            "slug": re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"),
            "upstream_grid_count": len(grid),
            "products": keep,
        })
    dump("category_products.json", {
        "captured_from": "https://www.zara.com/us/en/category/<id>/products?ajax=true",
        "categories": categories_meta,
    })
    dump("products.json", {
        "captured_from": "https://www.zara.com/us/en/<keyword>-p<seoProductId>.html (SSR viewPayload)",
        "products": catalog,
    })

    # ------------------------------------------------- category filters --
    filters = {}
    for seo_id, (cat_id, section, name) in CATEGORIES.items():
        fn = None
        for f in sorted(os.listdir(os.path.join(SCRAPE, "captures"))):
            if "category" in f and f"_{cat_id}_" in f and f.endswith("filters.json"):
                fn = os.path.join(SCRAPE, "captures", f)
                break
        if not fn:
            continue
        d = load(fn)
        colors = sizes = price_sort = None
        for flt in d.get("filters") or []:
            if flt.get("id") == "color":
                colors = [{"value": v.get("value"), "hex": v.get("colorHexCode"),
                           "count": len(v.get("catentries") or [])}
                          for v in flt.get("value") or []]
            elif flt.get("id") == "size":
                sizes = [{"value": v.get("value"),
                          "count": len(v.get("catentries") or [])}
                         for v in flt.get("value") or []]
        sorting = d.get("sorting") or {}
        options = [{"id": v.get("id"), "value": v.get("value")}
                   for v in sorting.get("value") or []][:6]
        filters[str(seo_id)] = {"colors": colors, "sizes": sizes,
                                "sort_options": options}
    dump("category_filters.json", {
        "captured_from": "https://www.zara.com/us/en/category/<id>/filters?ajax=true",
        "filters": filters,
    })

    # ------------------------------------------------------------ searches --
    search_files = {
        "dress": ("019_www.zara.com_itxrest_1_search_store_11719_query.json", "dress"),
        "jeans": ("r2_041_www.zara.com_itxrest_1_search_store_11719_query.json", "jeans"),
        "coat": ("r2_043_www.zara.com_itxrest_1_search_store_11719_query.json", "coat"),
        "bag": ("r2_045_www.zara.com_itxrest_1_search_store_11719_query.json", "bag"),
        "perfume": ("r2_047_www.zara.com_itxrest_1_search_store_11719_query.json", "perfume"),
        "sweater": ("r5_053_www.zara.com_itxrest_1_search_store_11719_query.json", "sweater"),
        "heels": ("r5_055_www.zara.com_itxrest_1_search_store_11719_query.json", "heels"),
        "t-shirt": ("r5_057_www.zara.com_itxrest_1_search_store_11719_query.json", "t-shirt"),
        "trench coat": ("r5_059_www.zara.com_itxrest_1_search_store_11719_query.json", "trench coat"),
    }
    searches = []
    for term, (fn, q) in search_files.items():
        d = load(os.path.join(SCRAPE, "captures", fn))
        results = []
        for r in d.get("results") or []:
            c = r.get("content") or {}
            seo = c.get("seo") or {}
            if not seo.get("seoProductId"):
                continue
            results.append(seo["seoProductId"])
        facets = []
        for f in d.get("facets") or []:
            if f.get("key") == "color_facet":
                facets.append({
                    "key": "color_facet",
                    "values": [{"id": v["id"], "value": v["value"],
                                "count": v["count"],
                                "hex": ((v.get("extraInfo") or {}).get("color") or {}).get("hexCode")}
                               for v in f.get("values") or []],
                })
            elif f.get("key") == "size_facet":
                facets.append({
                    "key": "size_facet",
                    "values": [{"id": v["id"], "value": v["value"],
                                "count": v["count"]} for v in f.get("values") or []],
                })
        price_f = next((f for f in (d.get("filtersV2") or [])
                        if f.get("key") == "price_facet"), None)
        searches.append({
            "term": q,
            "total_results": d.get("totalResults"),
            "facets": facets,
            "price_range": ({"min": price_f.get("minValue"), "max": price_f.get("maxValue")}
                            if price_f else None),
            "sortings": [{"property": s.get("property"),
                          "orders": s.get("availableOrders")}
                         for s in d.get("sortings") or []],
            "results": results,
        })
    dump("searches.json", {
        "captured_from": "https://www.zara.com/itxrest/1/search/store/11719/query?query=<term>",
        "searches": searches,
    })

    # --------------------------------------------------------------- stores --
    stores = []
    groups = []
    z = load(os.path.join(SCRAPE, "payloads", "10_z-stores.json"))
    upstream_urls = {}
    for grp in z.get("physicalStoresList") or []:
        g = {"state": grp["cityName"],
             "stores": [{"id": s["id"], "name": s["name"]} for s in grp["stores"]]}
        groups.append(g)
        for s in grp["stores"]:
            upstream_urls[s["id"]] = s["url"]
    for fn in sorted(os.listdir(os.path.join(SCRAPE, "payloads"))):
        m = re.match(r".*store-s(\d+)(?:-store)?\.json$", fn)
        if not m or fn == "10_z-stores.json":
            continue
        d = load(os.path.join(SCRAPE, "payloads", fn))
        st = d.get("physicalStoreExtendedDetails")
        if st is None and isinstance(d, dict) and d.get("address") and d.get("openingHours"):
            st = d
        if not st or not st.get("address"):
            continue
        hours = {}
        for s in (st.get("openingHours") or {}).get("schedule") or []:
            hours[str(s["weekDay"])] = {
                "open": s.get("open"),
                "hours": s.get("hours") or [],
            }
        upcoming = []
        for u in (st.get("upcomingSchedule") or [])[:7]:
            intervals = [{"open": iv.get("openTime"), "close": iv.get("closeTime")}
                         for iv in u.get("openingHoursInterval") or []]
            upcoming.append({"date": u.get("date"), "week_day": u.get("weekDay"),
                             "open": u.get("open"), "intervals": intervals})
        stores.append({
            "id": st["id"], "name": st["name"],
            "commercial_name": st.get("commercialName"),
            "address": st.get("address"), "city": st.get("city"),
            "province": st.get("province"), "zip": st.get("zipCode"),
            "phone": st.get("phone"), "type": st.get("type"),
            "status": st.get("status"), "timezone": st.get("timeZone"),
            "hours": hours, "upcoming": upcoming,
            "url": upstream_urls.get(st["id"]),
        })
    dump("stores.json", {
        "captured_from": "https://www.zara.com/us/en/z-stores-st1404.html + stores-locator detail pages",
        "upstream_us_store_count": 102,
        "state_groups": groups,
        "stores": stores,
    })

    # ----------------------------------------------------------------- home --
    home = load(os.path.join(SCRAPE, "payloads", "00_home.json"))
    sections_slides = []
    for block in (home.get("sliderSpot") or {}).get("content", {}).get("slides") or []:
        title = block.get("slideTitle")
        inner = ((block.get("spot") or {}).get("content") or {}).get("slides") or []
        posters = []
        for s in inner:
            poster = None
            for xms in (s.get("xmedias") or []):
                if isinstance(xms, dict) and xms.get("posterUrl"):
                    poster = xms["posterUrl"]
                    break
            if poster is None:
                for xm in (s.get("xmedia") or []):
                    if isinstance(xm, dict) and xm.get("type") == "image":
                        du = (xm.get("extraInfo") or {}).get("deliveryUrl")
                        if du:
                            poster = du
                            break
            if poster:
                posters.append({
                    "collection": s.get("collectionName"),
                    "category_id": s.get("categoryId"),
                    "section_name": s.get("sectionName"),
                    "poster": poster,
                })
        if posters:
            sections_slides.append({"title": title, "slides": posters[:6]})
    footer = None
    spots = (home.get("mkSpots") or {}).get("ESpot_Footer_Links") or {}
    footer = (spots.get("content") or {}).get("content")
    dump("home.json", {
        "captured_from": "https://www.zara.com/us/ (SSR viewPayload)",
        "campaigns": sections_slides,
        "footer_html": footer,
    })

    # -------------------------------------------------------- user fixtures --
    # (authored; the upstream account area requires live accounts)
    users = load(os.path.join(SCRAPE, "benchmark_users.json")) \
        if os.path.exists(os.path.join(SCRAPE, "benchmark_users.json")) else None
    if users:
        dump("benchmark_users.json", users)

    print(f"catalog products: {len(catalog)}; stores: {len(stores)}; "
          f"searches: {len(searches)}")


if __name__ == "__main__":
    main()
