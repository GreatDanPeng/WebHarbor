"""Honest fixture data: per-task navigation URLs + final answers, frozen from
the reviewer's independent live walkthroughs (wh-ups-review-evidence/runs/)."""
from __future__ import annotations

BASE = "http://localhost:40107"

SPECS = {
    0: {
        "urls": ["/track",
                 "/track?tracknum=1Z58F0E70312456012%0A1Z58F0E71248779034",
                 "/track/detail/1Z58F0E70312456012",
                 "/track?tracknums=1Z58F0E71248779034",
                 "/track/detail/1Z58F0E71248779034",
                 "/locations?zip=10001",
                 "/locations/255850"],
        "answer": (
            "Shipment 1Z58F0E70312456012: latest scan Out for Delivery at Maspeth, NY "
            "on 2026-09-28 at 8:52 A.M. After leaving the Seattle area it made 4 "
            "facility stops (Spokane WA, Commerce City CO, Hodgkins IL, Maspeth NY). "
            "Shipment 1Z58F0E71248779034 is awaiting customer pickup at The UPS Store, "
            "337 10th Ave, New York, NY 10001; it must be picked up by 2026-10-05. In "
            "the ZIP 10001 locator that location's latest ground drop-off is Mon-Fri: "
            "6:30pm; Sat: 3:30pm; Sun: No Pickup."),
    },
    1: {
        "urls": ["/track?tracknum=1Z58F0E70291534227",
                 "/track/detail/1Z58F0E70291534227",
                 "/support/article/understanding-tracking-status",
                 "/track/detail/1Z58F0E70291534227/change-delivery",
                 "/support?q=intercept",
                 "/support/article/ups-delivery-intercept",
                 "/track?tracknums=1Z58F0E70291534227",
                 "/track/detail/1Z58F0E70291534227"],
        "answer": (
            "Status: Exception. Full exception reason: The address information "
            "provided by the sender is incorrect. The sender has been notified. "
            "Delivery is pending corrected address information. Scheduled delivery "
            "date: 2026-09-25. The article says an Exception means the shipment is in "
            "the UPS network but there was an unexpected error that may result in a "
            "change in the scheduled delivery date; the reason is noted in the "
            "Shipment Progress section of the Tracking Detail page. Change options: "
            "Hold for Pickup at a UPS Location, Deliver to Another Address, Reschedule "
            "Delivery. UPS Delivery Intercept: $18.00 web request, $21.00 phone "
            "request. Shipper: Harbor Lane Apparel, Portland, OR."),
    },
    2: {
        "urls": ["/track?tracknum=1Z58F0E70312456012",
                 "/track/detail/1Z58F0E70312456012",
                 "/track/detail/1Z58F0E70312456012/change-delivery",
                 "/track/detail/1Z58F0E70312456012",
                 "/locations?zip=10001&type=The%20UPS%20Store",
                 "/locations/255850"],
        "answer": (
            "Held at the closest UPS Access Point network location for ZIP 10001: The "
            "UPS Store, 337 10th Ave — distance shown when selected 0.2 miles. New "
            "activity entry: 'Delivery changed: the package will be held for pickup "
            "at The Ups Store, 337 10Th Ave, New York, NY 10001.' The location's city "
            "is New York, NY and its latest ground drop-off is Mon-Fri: 6:30pm; Sat: "
            "3:30pm; Sun: No Pickup."),
    },
    3: {
        "urls": ["/ctc", "/ctc"],
        "answer": (
            "Residential 5 lb 12x10x8 from 10001 to 60601: 6 services quoted. Cheapest "
            "UPS Ground at $21.40; most expensive UPS Next Day Air Early at $243.57. "
            "With the residential box unchecked the cheapest service's price does "
            "not change — UPS Ground is still $21.40."),
    },
    4: {
        "urls": ["/services/compare", "/ctc", "/services/1DA"],
        "answer": (
            "Guaranteed services delivering by 10:30 a.m. next business day: UPS Next "
            "Day Air Early and UPS Next Day Air. Cheapest of those for 1 lb 10001 to "
            "60601: UPS Next Day Air at $134.98, delivered by 10:30 A.M. Tuesday "
            "September 29, 2026. Service page: latest pickup time 9:00 P.M. (schedule "
            "by 7:00 P.M.), maximum weight per package up to 150 lbs and 108\" long."),
    },
    5: {
        "urls": ["/ship", "/ship/confirm/1Z5F71X90370000152",
                 "/track?tracknum=1Z5F71X90370000152"],
        "answer": (
            "Tracking number 1Z5F71X90370000152. Scheduled delivery date 2026-10-01. "
            "Declared value charge shown $17.00. The tracking number resolves on the "
            "Track page with status Label Created."),
    },
    6: {
        "urls": ["/login", "/account", "/pickup", "/pickup/confirm/PK1000001"],
        "answer": (
            "The Label Created shipment is 1Z7R4T920199330245, UPS Next Day Air "
            "Saver, scheduled delivery 2026-09-29. Future-day pickup scheduled: "
            "confirmation number PK1000001, fee $9.65."),
    },
    7: {
        "urls": ["/locations?zip=10001", "/locations?zip=10001&type=UPS%20Access%20Point",
                 "/locations?zip=10001&type=UPS%20Drop%20Box",
                 "/locations?zip=10001&type=all",
                 "/locations/235041",
                 "/locations?zip=10001&type=The%20UPS%20Store",
                 "/locations/255850", "/locations/152025"],
        "answer": (
            "20 total locations within 15 miles of ZIP 10001; 2 UPS Access Points and "
            "8 UPS Drop Boxes. Nearest drop box: Tishman Speyer, 66 Hudson Blvd E, "
            "latest ground drop-off Mon-Fri: 1:30pm; Sat, Sun: No Pickup. Closest "
            "The UPS Store: phone 2124577300. Closest UPS Access Point: Deepchhaya "
            "Deli & Grocery, 334 W 37th St — no phone number is listed on its detail "
            "page."),
    },
    8: {
        "urls": ["/login", "/account",
                 "/track/detail/1Z7R4T920399120014",
                 "/track?tracknums=1Z7R4T920399120014",
                 "/track/detail/1Z7R4T920399120014"],
        "answer": (
            "3 packages: 1 delivered, 2 in transit. Delivered package signed for by "
            "T. OLSEN on 2026-09-26. Package 2's latest scan: Departed from Facility "
            "at Commerce City, CO. On the Track page: current status In Transit, "
            "latest scan facility Commerce City, CO."),
    },
    9: {
        "urls": ["/login", "/claims/new", "/claims/status/CLM4000001"],
        "answer": (
            "Claim number CLM4000001, status Claim Review in Progress. The resolution "
            "note says you can typically expect a resolution to your claim in 8 to 10 "
            "business days."),
    },
    10: {
        "urls": ["/track?tracknum=1ZF5R8210372885301",
                 "/track/detail/1ZF5R8210372885301",
                 "/support/article/understanding-tracking-status",
                 "/claims",
                 "/locations", "/locations?zip=10001&type=UPS%20Access%20Point"],
        "answer": (
            "Status Transferred to Post Office. Last scan description: The sender "
            "requested the shipment be transferred to the local post office to "
            "finish the delivery. The article says to be safe, allow for an extra "
            "day or two for final delivery. The claims FAQ says Ground Saver claims "
            "are accepted until the exception scan that indicates the package has "
            "been handed over to the Post Office is recorded. Closest UPS Access "
            "Point to ZIP 10001: Deepchhaya Deli & Grocery, 334 W 37th St."),
    },
    11: {
        "urls": ["/login", "/account", "/business/daily-pickup",
                 "/business/smart-pickup", "/business/day-specific-pickup",
                 "/business/pickup-dropoff-options", "/business/weekend-pickup"],
        "answer": (
            "Carol Diaz's account lists 3 shipments. Weekly fees: UPS Daily Pickup "
            "$39.00, UPS Smart Pickup $18.50, Day-Specific Pickup on 3 days $23.25 — "
            "the cheapest is UPS Smart Pickup at $18.50/week. On-Call Pickup: $9.65 "
            "future-day, $15.75 same-day. UPS Smart Pickup Saturday fee $8.00."),
    },
    12: {
        "urls": ["/track?tracknum=1ZW362F70355812012",
                 "/track/detail/1ZW362F70355812012",
                 "/track/detail/1ZW362F70355812012/change-delivery",
                 "/support?q=intercept",
                 "/support/article/ups-delivery-intercept",
                 "/locations?zip=30301&type=UPS%20Access%20Point"],
        "answer": (
            "Change options: Hold for Pickup at a UPS Location, Deliver to Another "
            "Address, Reschedule Delivery. UPS Delivery Intercept: $18.00 web "
            "request, $21.00 phone request; intercept actions include Return to "
            "Sender, Deliver to Another Address, Reschedule Delivery, and Will Call. "
            "Closest UPS Access Point to ZIP 30301: CVS Store # 10043, 235 Peachtree "
            "St NE. Current status In Transit, latest scan location Louisville, KY."),
    },
    13: {
        "urls": ["/support?q=status",
                 "/support/article/understanding-tracking-status",
                 "/track?tracknum=1Z99624Y0371728890",
                 "/track/detail/1Z99624Y0371728890",
                 "/locations?zip=10001&type=UPS%20Drop%20Box",
                 "/locations/235041"],
        "answer": (
            "Label Created means we've received the shipment details and billing "
            "information from the sender; the status updates once UPS has possession "
            "and the package is moving. Long distances: shipments traveling long "
            "distances likely won't be scanned again until they reach their "
            "destination hub. Shipment 1Z99624Y0371728890: second-to-last scan "
            "Departed from Facility at Louisville, KY on 2026-09-27; scheduled "
            "delivery 2026-10-02; service UPS Ground. Nearest UPS Drop Box to ZIP "
            "10001: Tishman Speyer, latest ground drop-off Mon-Fri: 1:30pm; Sat, "
            "Sun: No Pickup."),
    },
    14: {
        "urls": ["/business/weekend-pickup", "/pickup",
                 "/pickup/confirm/PK1000001"],
        "answer": (
            "Saturday pickup with UPS Smart Pickup: $8.00. Saturday stop charge for a "
            "scheduled Saturday pickup: $12.00. Scheduled the Saturday pickup for "
            "October 3, 2026: total fee on the review step $16.60, confirmation "
            "number PK1000001."),
    },
    15: {
        "urls": ["/locations", "/locations?zip=60601",
                 "/locations?zip=60601&type=The%20UPS%20Store",
                 "/locations/94892",
                 "/locations?zip=60601&type=UPS%20Access%20Point",
                 "/store/pack-and-ship"],
        "answer": (
            "The UPS Store closest to ZIP 60601: 323 E Wacker Dr, phone 3122688290. "
            "Hours: Monday 9:00 AM - 3:00 PM, Tuesday 8:00 AM - 6:00 PM. Latest air "
            "drop-off Mon-Fri: 3:00pm; Sat, Sun: No Pickup; latest ground drop-off "
            "the same. Nearest UPS Access Point to 60601: CVS Store # 8910, 205 N "
            "Columbus Dr — the Access Point is closer (0.1 mi vs 0.3 mi). The Pack "
            "and Ship page says our team of certified packing experts specializes in "
            "properly packing fragile and high-value items, including cherished "
            "antiques and collectibles."),
    },
    16: {
        "urls": ["/services", "/services/2DM", "/ctc", "/services/GND"],
        "answer": (
            "Domestic air services offering Saturday delivery: UPS Next Day Air "
            "Early, UPS Next Day Air, UPS 2nd Day Air, UPS 3 Day Select. UPS 2nd Day "
            "Air A.M.: guaranteed on-time delivery by 10:30 a.m. or 12:00 p.m. on "
            "the second business day; guaranteed; latest pickup 9:00 P.M. For 5 lb "
            "from San Francisco 94105 to Seattle 98101 it costs $79.99, delivered by "
            "10:30 A.M. Wednesday September 30, 2026. UPS Ground: up to 150 lbs per "
            "package; delivered by default within one to five business days."),
    },
    17: {
        "urls": ["/login", "/account",
                 "/track/detail/1Z58F0E70312456012",
                 "/track/detail/1Z58F0E70312456012/change-delivery",
                 "/track/detail/1Z58F0E70312456012",
                 "/support?q=intercept",
                 "/support/article/ups-delivery-intercept"],
        "answer": (
            "Alice Johnson's account lists 4 shipments: Delivered, Exception, "
            "Awaiting Customer Pickup, and Out for Delivery (1Z58F0E70312456012). "
            "The out-for-delivery shipment's scheduled delivery date is 2026-09-28; "
            "it went out for delivery at the Maspeth, NY facility; change options: "
            "Hold for Pickup at a UPS Location, Deliver to Another Address, "
            "Reschedule Delivery. Changed to hold at the UPS Access Point closest "
            "to ZIP 10001; confirmation: 'Delivery changed: the package will be "
            "held for pickup at The Ups Store, 337 10Th Ave, New York, NY 10001.' "
            "The web-request UPS Delivery Intercept fee is $18.00."),
    },
    18: {
        "urls": ["/store/services", "/store/mailboxes", "/store/pack-and-ship",
                 "/locations", "/locations?zip=10001",
                 "/locations?zip=10001&type=The%20UPS%20Store"],
        "answer": (
            "In-store services: Notarize Without Leaving the Neighborhood, Passport "
            "Photos, Shredding Services. Mailbox customers get: We Sign for "
            "Packages, We Accept All Carriers, Receive Delivery Text Alerts, "
            "Prevent Porch Pirates, and 24-hour access at participating locations. "
            "The Pack and Ship page says our team of certified packing experts "
            "specializes in properly packing fragile and high-value items, including "
            "cherished antiques and collectibles; it does not state a carrier choice "
            "— carrier acceptance (We Accept All Carriers) is a Mailboxes-page "
            "perk. 5 The UPS Store locations are within 15 miles of ZIP 10001; the "
            "closest is The UPS Store at 337 10th Ave."),
    },
    19: {
        "urls": ["/ctc", "/support?q=intercept",
                 "/support/article/ups-delivery-intercept"],
        "answer": (
            "UPS Ground price for a 15 lb package (16x12x10) from 10001 to 60601: "
            "$32.80, delivered by By End of Day Wednesday September 30, 2026; "
            "billable weight shown 15.0 lbs. Next Day Air Early breakdown: "
            "Transportation $246.68, Delivery Area Surcharge $4.50, Fuel Surcharge "
            "$84.15. UPS Delivery Intercept web-request fee $18.00."),
    },
}
