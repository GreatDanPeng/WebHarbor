"""Honest walkthrough SPECS transcribed from the reviewer's r2 live runs
(wh-united-airlines-rereview, site build 93a2638f, seed md5
3a04d306e9fcb436e598fa07e2740912) plus the per-task DB mutations the site
itself would write. Re-frozen values: T4's 787-8 total seat rows (32), T6's
seat band (rows 15-32), T8's before/after itinerary, T12's 3-bag calculator
run, T14's both-page thresholds + remaining PQF/PQP, T16's fleet values
(37/46, 560/557 mph, 197 ft 4 in, 115,300 lbf) and T17's source-article
titles. No LLM."""
from __future__ import annotations

BASE = "http://localhost:40167"

SPECS = {}

SPECS[0] = {
    "urls": [
        "/",
        "/flights/search?origin=ORD&destination=DEN&depart=2026-10-15&adults=1&children=0&cabin=ECO",
        "/booking/passengers",
        "/booking/payment",
        "/booking/confirmation/VRMEZ8",
    ],
    "answer": ("I compared every United Economy fare for ORD to DEN on October 15: "
               "UA 2803 $210.95, UA 2790 $202.95, UA 1974 $226.95. The cheapest "
               "Economy option was UA 2790 departing 16:12 arriving 18:13, so I booked "
               "it for guest traveler Jordan Hayes. Confirmation number VRMEZ8, "
               "flight UA 2790, total charged $202.95."),
    "conf": "VRMEZ8",
    "sql": [
        "INSERT INTO bookings (id,confirmation,user_id,contact_email,contact_phone,cabin,adults,children,award_booking,miles_redeemed,card_last4,card_type,total,status,canceled_at,refund_amount,refund_to,created_at) "
        "VALUES (5,'VRMEZ8',NULL,'jordan.hayes@example.com','+1 555 019 4433','ECO',1,0,0,0,'4242','Visa',202.95,'confirmed',NULL,0.0,'','2026-09-28 12:00:00.000000')",
        "INSERT INTO booking_legs (id,booking_id,flight_id,travel_date,cabin,amount) VALUES (5,5,10,'2026-10-15','ECO',202.95)",
        "INSERT INTO passengers (id,booking_id,first_name,last_name,title,date_of_birth,gender,mp_number,seat,checked_in,boarding_group) "
        "VALUES (5,5,'Jordan','Hayes','Mr','1990-05-10','Male','','',0,'')",
    ],
}

SPECS[1] = {
    "urls": [
        "/",
        "/flights/search?origin=CMX&destination=ORD&depart=2026-10-14&return=2026-10-21&adults=1&children=0&cabin=ECO",
        "/flights/select-return?origin=ORD&destination=CMX",
        "/booking/passengers",
        "/booking/payment",
        "/booking/confirmation/9ZEK48",
    ],
    "answer": ("Round trip Hancock (CMX) to Chicago O'Hare: the cheapest outbound was "
               "UA 5131 at $138.95 (October 14) and the cheapest return was UA 6067 at "
               "$134.95 (October 21). Booked for Dana Reyes with Mastercard "
               "...7890. Confirmation number 9ZEK48, flights UA 5131 and UA 6067, "
               "total charged $273.90."),
    "conf": "9ZEK48",
    "sql": [
        "INSERT INTO bookings (id,confirmation,user_id,contact_email,contact_phone,cabin,adults,children,award_booking,miles_redeemed,card_last4,card_type,total,status,canceled_at,refund_amount,refund_to,created_at) "
        "VALUES (5,'9ZEK48',NULL,'dana.reyes@example.com','+1 555 013 7788','ECO',1,0,0,0,'7890','Mastercard',273.9,'confirmed',NULL,0.0,'','2026-09-28 12:00:00.000000')",
        "INSERT INTO booking_legs (id,booking_id,flight_id,travel_date,cabin,amount) VALUES (5,5,3,'2026-10-14','ECO',138.95)",
        "INSERT INTO booking_legs (id,booking_id,flight_id,travel_date,cabin,amount) VALUES (6,5,28,'2026-10-21','ECO',134.95)",
        "INSERT INTO passengers (id,booking_id,first_name,last_name,title,date_of_birth,gender,mp_number,seat,checked_in,boarding_group) "
        "VALUES (5,5,'Dana','Reyes','Ms','1990-05-10','Female','','',0,'')",
    ],
}

SPECS[2] = {
    "urls": [
        "/",
        "/signin",
        "/account",
        "/flights/search?origin=SFO&destination=ORD&depart=2026-10-05&adults=1&children=0&cabin=ECO",
        "/booking/passengers",
        "/booking/payment",
        "/booking/confirmation/WTV9G8",
    ],
    "answer": ("Signed in as Alice Johnson and booked award travel one way SFO to ORD "
               "on October 5, 2026 in United Economy: UA 2855, 15:30 to 21:53. The "
               "fare needed 42,595 miles; I redeemed 42,595 award miles. Confirmation "
               "number WTV9G8. My award miles balance afterwards is 25,855."),
    "conf": "WTV9G8",
    "sql": [
        "INSERT INTO bookings (id,confirmation,user_id,contact_email,contact_phone,cabin,adults,children,award_booking,miles_redeemed,card_last4,card_type,total,status,canceled_at,refund_amount,refund_to,created_at) "
        "VALUES (5,'WTV9G8',1,'alice.j@example.com','+1 555 010 1234','ECO',1,0,1,42595,NULL,NULL,0.0,'confirmed',NULL,0.0,'','2026-09-28 12:00:00.000000')",
        "INSERT INTO booking_legs (id,booking_id,flight_id,travel_date,cabin,amount) VALUES (5,5,45,'2026-10-05','ECO',421.69)",
        "INSERT INTO passengers (id,booking_id,first_name,last_name,title,date_of_birth,gender,mp_number,seat,checked_in,boarding_group) "
        "VALUES (5,5,'Alice','Johnson','Ms','1990-05-10','Female','8511174410','',0,'')",
        "UPDATE users SET award_miles=25855 WHERE id=1",
        "INSERT INTO activities (id,user_id,date,description,channel,miles,pqp) "
        "VALUES (1,1,'2026-09-28','Award travel — SFO–ORD','MileagePlus',-42595,NULL)",
    ],
}

SPECS[3] = {
    "urls": [
        "/",
        "/signin",
        "/account",
        "/flights/search?origin=IAD&destination=DEN&depart=2026-10-08&adults=1&children=0&cabin=EPU",
        "/booking/passengers",
        "/booking/payment",
        "/booking/confirmation/RHHYTY",
    ],
    "answer": ("Signed in as Bob Miller (Premier Gold) and booked Economy Plus one way "
               "Washington-Dulles to Denver on October 8: the cheapest Economy Plus fare "
               "was UA 599 at $325.61 (UA 395 was $328.05, UA 2667 $335.34, UA 495 "
               "$348.70). Booked for Robert Miller with his MileagePlus number "
               "5658356101 on the traveler. Confirmation number RHHYTY, total charged "
               "$325.61, and the booking credits 2,605 award miles to the account."),
    "conf": "RHHYTY",
    "sql": [
        "INSERT INTO bookings (id,confirmation,user_id,contact_email,contact_phone,cabin,adults,children,award_booking,miles_redeemed,card_last4,card_type,total,status,canceled_at,refund_amount,refund_to,created_at) "
        "VALUES (5,'RHHYTY',2,'bob.m@example.com','+1 555 010 5678','EPU',1,0,0,0,'9010','Visa',325.61,'confirmed',NULL,0.0,'','2026-09-28 12:00:00.000000')",
        "INSERT INTO booking_legs (id,booking_id,flight_id,travel_date,cabin,amount) VALUES (5,5,14,'2026-10-08','EPU',325.61)",
        "INSERT INTO passengers (id,booking_id,first_name,last_name,title,date_of_birth,gender,mp_number,seat,checked_in,boarding_group) "
        "VALUES (5,5,'Robert','Miller','Mr','1990-05-10','Male','5658356101','',0,'')",
        "UPDATE users SET award_miles=145805, pqf=32, pqp=9506 WHERE id=2",
        "INSERT INTO activities (id,user_id,date,description,channel,miles,pqp) "
        "VALUES (1,2,'2026-09-28','Flight credit — IAD–DEN','United',2605,326)",
    ],
}

SPECS[4] = {
    "urls": [
        "/",
        "/flight-status",
        "/flight-status/results?mode=number&number=2855&date=2026-09-28",
        "/flight-status",
        "/flight-status/results?mode=route&origin=SFO&destination=ORD&date=2026-09-28",
        "/travel-info/fleet/78H",
    ],
    "answer": ("UA 2855 today is scheduled to depart SFO at 15:30 and arrive ORD at "
               "21:53, operated by a Boeing 787-8. The SFO to ORD route status page "
               "shows UA 2855 as the day's flight. On the 787-8 fleet page: total seat "
               "rows 32, with 7 United First/Business rows and 3 Premium Plus rows; "
               "Wi-Fi provider Panasonic."),
    "sql": [],
}

SPECS[5] = {
    "urls": [
        "/",
        "/flights/search?origin=FCO&destination=DEN&depart=2026-10-19&adults=1&children=0&cabin=ECO",
    ],
    "answer": ("For Rome (FCO) to Denver on October 19, 2026 there is one flight: UA 178. "
               "Its fares are Basic Economy $538.16, United Economy $689.95, Economy "
               "Plus $855.54, Premium Plus $1,621.38 and United Business $2,828.80. The "
               "cheapest Premium Plus flight is UA 178 itself, operated by a Boeing 787-9."),
    "sql": [],
}

SPECS[6] = {
    "urls": [
        "/",
        "/mytrips",
        "/mytrips?confirmation=KX42LM&lastname=Johnson",
        "/mytrips/KX42LM",
        "/mytrips/KX42LM/seats/1",
        "/mytrips/KX42LM",
    ],
    "answer": ("Alice Johnson's trip KX42LM (SFO to ORD, September 29): adding the next "
               "checked bag costs $35 online — Checked bag 2 added — $35 (online price); "
               "her first bag is already covered because Premier Silver gives 1 free bag on "
               "this trip. On the seat map I picked standard aisle seat 15D (a "
               "non-Economy Plus row in the standard Economy band, not marked occupied). "
               "Free bags from Premier status: 1."),
    "sql": [
        "INSERT INTO baggage_items (id,booking_id,passenger_id,description,weight_lb,fee) VALUES (3,1,1,'Checked bag 2',0,35.0)",
        "UPDATE passengers SET seat='15D' WHERE id=1",
    ],
}

SPECS[7] = {
    "urls": [
        "/",
        "/signin",
        "/account",
        "/checkin",
        "/checkin/HD19RK",
        "/checkin/HD19RK/boarding-pass",
    ],
    "answer": ("Checked in for David Thomas on trip HD19RK (SFO to ORD today). Seat "
               "12A confirmed; boarding pass shows boarding group Group 1, gate C12, "
               "boarding time 14:50, seat 12A. The aircraft flying the route is a "
               "Boeing 787-8."),
    "sql": [
        "UPDATE passengers SET seat='12A', checked_in=1, boarding_group='Group 1' WHERE id=4",
    ],
}

SPECS[8] = {
    "urls": [
        "/",
        "/signin",
        "/account",
        "/mytrips",
        "/mytrips/QT83NB",
        "/mytrips/QT83NB/change/2",
        "/mytrips/QT83NB",
    ],
    "answer": ("Bob Miller (Premier Gold, trip QT83NB, ORD to DEN today in Economy "
               "Plus) was on UA 2803 departing 14:33. I moved him to the latest United "
               "flight later today: UA 1974, departing 18:17 and arriving 20:22. The "
               "fare difference charged was $19.84 and United applied no change fee "
               "($0)."),
    "sql": [
        "UPDATE booking_legs SET flight_id=11, amount=281.42 WHERE id=2",
        "UPDATE bookings SET total=281.42 WHERE confirmation='QT83NB'",
    ],
}

SPECS[9] = {
    "urls": [
        "/",
        "/flights/search?origin=DEN&destination=SLC&depart=2026-10-16&adults=1&children=0&cabin=ECO",
        "/booking/passengers",
        "/booking/payment",
        "/booking/confirmation/AKGGFG",
        "/mytrips",
        "/mytrips?confirmation=AKGGFG&lastname=Kim",
        "/mytrips/AKGGFG/cancel",
    ],
    "answer": ("Booked the cheapest United Economy flight Denver to Salt Lake City on "
               "October 16 for guest traveler Casey Kim: confirmation number AKGGFG, "
               "total paid $131.95. I then canceled the trip from My trips; the refund "
               "amount is $131.95 and it went back to the original payment method (the "
               "Visa card)."),
    "conf": "AKGGFG",
    "sql": [
        "INSERT INTO bookings (id,confirmation,user_id,contact_email,contact_phone,cabin,adults,children,award_booking,miles_redeemed,card_last4,card_type,total,status,canceled_at,refund_amount,refund_to,created_at) "
        "VALUES (5,'AKGGFG',NULL,'casey.kim@example.com','+1 555 017 2200','ECO',1,0,0,0,'4242','Visa',131.95,'canceled','2026-09-28 12:00:00.000000',131.95,'card','2026-09-28 12:00:00.000000')",
        "INSERT INTO booking_legs (id,booking_id,flight_id,travel_date,cabin,amount) VALUES (5,5,39,'2026-10-16','ECO',131.95)",
        "INSERT INTO passengers (id,booking_id,first_name,last_name,title,date_of_birth,gender,mp_number,seat,checked_in,boarding_group) "
        "VALUES (5,5,'Casey','Kim','Ms','1990-05-10','Female','','',0,'')",
    ],
}

SPECS[10] = {
    "urls": [
        "/",
        "/mytrips",
        "/mytrips?confirmation=ZW57PC&lastname=Williams",
        "/mytrips/ZW57PC",
        "/mytrips/ZW57PC/cancel",
        "/travel-info/policies/flight-change",
    ],
    "answer": ("Carol Williams' Basic Economy trip ZW57PC (IAH to LAX, October 12): "
               "Basic Economy tickets cannot be changed, so the change attempt is not "
               "offered on the trip page. After canceling, the ticket value was saved as "
               "a future flight credit — the full $198.08 stays as a travel credit "
               "(cash refund $0). The flight-change policy page confirms United charges "
               "no change fee on standard United Economy and premium cabin fares — you "
               "only pay the fare difference — while Basic Economy is not changeable."),
    "sql": [
        "UPDATE bookings SET status='canceled', canceled_at='2026-09-28 12:00:00.000000', refund_amount=0.0, refund_to='travel credit' WHERE confirmation='ZW57PC'",
    ],
}

SPECS[11] = {
    "urls": [
        "/",
        "/baggage",
        "/baggage/fee-calculator",
        "/baggage/fee-calculator",
        "/baggage/fee-calculator",
    ],
    "answer": ("Checked bag fee calculator. (1) Member in United Economy flying ORD to "
               "DEN with 2 bags: prepaid online $35 for the first bag and $45 for the "
               "second, $80 total; at the airport $40 and $50, $90 total. Weight limit "
               "50 lb per bag (23 kg). (2) Premier Gold member in United Business flying "
               "London Heathrow to DEN with 2 bags online: the calculator prices $35 + "
               "$45 = $80 (note: Gold members in Economy get free checked bags — 1 for "
               "Silver, 2 for Gold, 3 for Platinum/1K — so bags on the reservation may "
               "be free). Weight limit 70 lb (32 kg) per bag."),
    "sql": [],
}

SPECS[12] = {
    "urls": [
        "/",
        "/baggage",
        "/baggage/checked-bags",
        "/baggage",
        "/baggage/carry-on",
        "/baggage/fee-calculator",
    ],
    "answer": ("Baggage rules: the maximum size of a checked bag is 30 in x 20 in x 12 in "
               "(76 cm x 52 cm x 30 cm) or 62 total linear inches including handles and "
               "wheels. Weight limit for United Economy is 50 lb (23 kg); Premier members "
               "get 70 lb (32 kg). A 60-pound bag falls in the 51-70 lb overweight band: "
               "$100. Carry-on size limit 23 x 35 x 56 cm (9 x 14 x 22 in); personal item "
               "22 x 25 x 43 cm. Basic Economy includes a personal item on all flights, "
               "with a full-size carry-on also included when flying to Canada, South "
               "America, across the Atlantic or on an international Pacific route. "
               "Pricing three checked bags prepaid online for one United Economy "
               "traveler from Chicago O'Hare to Denver with the fee calculator: bag 1 "
               "$35, bag 2 $45, bag 3 $150, total $230.00 (weight limit 50 lb per bag)."),
    "sql": [],
}

SPECS[13] = {
    "urls": [
        "/",
        "/mileageplus",
        "/mileageplus/join",
        "/account",
        "/flights/search?origin=SFO&destination=PDX&depart=2026-10-09&adults=1&children=0&cabin=ECO",
        "/booking/passengers",
        "/booking/payment",
        "/booking/confirmation/XSZ2SB",
    ],
    "answer": ("Frank Lee joined MileagePlus: his new MileagePlus number is 1759967178. "
               "I booked the cheapest United Economy flight San Francisco to Portland on "
               "October 9 for Frank Lee with his new number on the traveler: UA 2624, "
               "confirmation number XSZ2SB, and the flight credits 865 award miles."),
    "conf": "XSZ2SB",
    "sql": [
        "INSERT INTO users (id,email,password_hash,first_name,last_name,mp_number,award_miles,pqf,pqp,tier,plus_points,phone,country,created_at) "
        "VALUES (5,'frank.lee@example.com','x','Frank','Lee','1759967178',865,1,173,'Member',0,NULL,NULL,'2026-09-28 12:00:00.000000')",
        "INSERT INTO bookings (id,confirmation,user_id,contact_email,contact_phone,cabin,adults,children,award_booking,miles_redeemed,card_last4,card_type,total,status,canceled_at,refund_amount,refund_to,created_at) "
        "VALUES (5,'XSZ2SB',5,'frank.lee@example.com','+1 555 018 7755','ECO',1,0,0,0,'4242','Visa',172.95,'confirmed',NULL,0.0,'','2026-09-28 12:00:00.000000')",
        "INSERT INTO booking_legs (id,booking_id,flight_id,travel_date,cabin,amount) VALUES (5,5,43,'2026-10-09','ECO',172.95)",
        "INSERT INTO passengers (id,booking_id,first_name,last_name,title,date_of_birth,gender,mp_number,seat,checked_in,boarding_group) "
        "VALUES (5,5,'Frank','Lee','Mr','1990-05-10','Male','1759967178','',0,'')",
        "INSERT INTO activities (id,user_id,date,description,channel,miles,pqp) "
        "VALUES (1,5,'2026-09-28','Flight credit — SFO–PDX','United',865,173)",
    ],
}

SPECS[14] = {
    "urls": [
        "/",
        "/signin",
        "/account",
        "/mileageplus",
    ],
    "answer": ("Carol Williams' Premier qualification progress: she currently has 2 PQF "
               "and 640 PQP (the account page shows 2 PQF — need 12 — and 640 PQP — "
               "need 4,000). For Premier Silver the program page requires 12 PQF and "
               "4,000 PQP — the same thresholds the account page states, so the two "
               "pages agree — or the PQP-only alternative of 5,000 PQP. She still "
               "needs 10 more PQF and 3,360 more PQP for Premier Silver. Premier 1K "
               "members earn 11 award miles per dollar (11x)."),
    "sql": [],
}

SPECS[15] = {
    "urls": [
        "/",
        "/travel-info/cabins",
        "/travel-info/cabins/basic-economy",
        "/travel-info/cabins",
        "/travel-info/cabins/economy-plus",
        "/travel-info/cabins",
        "/travel-info/cabins/premium-plus",
        "/travel-info/cabins",
        "/travel-info/cabins/united-polaris",
        "/travel-info/fleet/78P",
    ],
    "answer": ("Cabin comparison. Basic Economy: a personal item that fits under the "
               "seat is included; a full-size carry-on is only included on international "
               "routes (Canada, South America, transatlantic, transpacific); no changes "
               "permitted. Economy Plus: extra legroom toward the front of the Economy "
               "cabin, from $29 per flight; free at booking for Premier Gold and above, "
               "free at check-in for Premier Silver. Premium Plus: 2 free checked bags "
               "at 70 lb. United Polaris on the 787-9 fleet page: lie-flat seat, 6'6\" "
               "(198 cm) sleeping space."),
    "sql": [],
}

SPECS[16] = {
    "urls": [
        "/",
        "/travel-info/fleet",
        "/travel-info/fleet/78P",
        "/travel-info/fleet/77X",
    ],
    "answer": ("Boeing 787-9: total seat rows 37 — 12 United Polaris rows, 3 Premium "
               "Plus rows, 5 Economy Plus rows; interior specifications seats 48 Polaris "
               "/ 21 Premium Plus / 39 Economy Plus / 149 Economy; Wi-Fi provider "
               "Panasonic; cruise speed 560 mph; wingspan 197 ft 4 in; engine General "
               "Electric GEnx-1B76 (two engines, thrust 76,100 lbf). Boeing 777-300ER: "
               "total seat rows 46 — 15 Polaris rows, 3 Premium Plus, 7 Economy Plus; "
               "seats 60 / 24 / 62 / 204; Wi-Fi Panasonic; cruise speed 557 mph; "
               "wingspan 212 ft 7 in; engine General Electric GE90-115B (two engines, "
               "thrust 115,300 lbf)."),
    "sql": [],
}

SPECS[17] = {
    "urls": [
        "/",
        "/help",
        "/help?q=check-in",
        "/help/check-in-online",
        "/help",
        "/help/same-day-change",
        "/help",
        "/help/change-award",
        "/help",
        "/help/economy-plus",
    ],
    "answer": ("Help Center answers. (1) Online check-in opens 24 hours before departure "
               "and closes 60 minutes before departure (source: 'How early can I check in "
               "for my flight?'). (2) The same-day flight change fee is up to $75, and "
               "standby is free if you are a Premier member (source: 'What is the "
               "same-day change option?'). (3) After canceling an award flight there is "
               "no redeposit fee — miles return to your account with the fee waived; if "
               "you no-show, a $125 service fee applies and it is nonrefundable (source: "
               "'Can I get my miles back if I cancel an award flight?'). (4) The lowest "
               "Economy Plus price is $29 per flight (source: 'What is Economy Plus?')."),
    "sql": [],
}

SPECS[18] = {
    "urls": [
        "/",
        "/flight-status",
        "/flight-status/results?mode=route&origin=EWR&destination=DEN&date=2026-09-28",
        "/travel-info/fleet/21N",
        "/travel-info/airports",
        "/travel-info/airports/DEN",
    ],
    "answer": ("Newark to Denver today: three United flights listed — UA 1197 departs "
               "16:59 arrives 19:34 (Airbus A321neo), UA 407 departs 18:49 arrives 21:18 "
               "(Airbus A321neo), UA 1792 departs 20:59 arrives 23:26 (Boeing 737 MAX 9). "
               "UA 1197 arrives earliest at 19:34; its duration as listed on the status "
               "page is 3h 01m (scheduled 16:59 to 19:34) and its aircraft's Wi-Fi "
               "provider (from the fleet page) is Viasat. The Denver airport guide "
               "confirms Denver is a United hub (Yes — United hub)."),
    "sql": [],
}

SPECS[19] = {
    "urls": [
        "/",
        "/deals",
        "/deals/sfo-to-syd",
        "/flights/search?origin=SFO&destination=SYD&depart=2026-10-26&adults=1&children=0&cabin=ECO",
        "/booking/passengers",
        "/booking/payment",
        "/booking/confirmation/HJSCAX",
    ],
    "answer": ("The San Francisco to Sydney deal starts from $799 one way; the route's "
               "flight is UA 863. I booked the cheapest United Economy seat departing "
               "October 26, 2026 for guest traveler Priya Nair: confirmation number "
               "HJSCAX, flight UA 863, total charged $739.95 (deal starting price $799)."),
    "conf": "HJSCAX",
    "sql": [
        "INSERT INTO bookings (id,confirmation,user_id,contact_email,contact_phone,cabin,adults,children,award_booking,miles_redeemed,card_last4,card_type,total,status,canceled_at,refund_amount,refund_to,created_at) "
        "VALUES (5,'HJSCAX',NULL,'priya.nair@example.com','+1 555 015 9911','ECO',1,0,0,0,'4242','Visa',739.95,'confirmed',NULL,0.0,'','2026-09-28 12:00:00.000000')",
        "INSERT INTO booking_legs (id,booking_id,flight_id,travel_date,cabin,amount) VALUES (5,5,54,'2026-10-26','ECO',739.95)",
        "INSERT INTO passengers (id,booking_id,first_name,last_name,title,date_of_birth,gender,mp_number,seat,checked_in,boarding_group) "
        "VALUES (5,5,'Priya','Nair','Ms','1990-05-10','Female','','',0,'')",
    ],
}

SPECS[20] = {
    "urls": [
        "/travel-info/policies",
        "/travel-info/policies/flight-change",
        "/",
        "/flights/search?origin=ORD&destination=AUS&depart=2026-10-21&adults=1&children=0&cabin=ECO",
        "/booking/passengers",
        "/booking/payment",
        "/booking/confirmation/VV8N4V",
        "/mytrips",
        "/mytrips?confirmation=VV8N4V&lastname=Ortiz",
        "/mytrips/VV8N4V/cancel",
    ],
    "answer": ("United's change rules: change your flight any time before departure — "
               "United charges no change fee on standard United Economy and premium cabin "
               "fares, you only pay the fare difference; Basic Economy tickets are not "
               "changeable. I booked the cheapest Economy flight Chicago O'Hare to Austin "
               "on October 21 for guest Sam Ortiz: confirmation VV8N4V, total charged "
               "$234.95. After canceling from My trips, the refund was $234.95 to the "
               "original payment method."),
    "conf": "VV8N4V",
    "sql": [
        "INSERT INTO bookings (id,confirmation,user_id,contact_email,contact_phone,cabin,adults,children,award_booking,miles_redeemed,card_last4,card_type,total,status,canceled_at,refund_amount,refund_to,created_at) "
        "VALUES (5,'VV8N4V',NULL,'sam.ortiz@example.com','+1 555 016 3344','ECO',1,0,0,0,'4242','Visa',234.95,'canceled','2026-09-28 12:00:00.000000',234.95,'card','2026-09-28 12:00:00.000000')",
        "INSERT INTO booking_legs (id,booking_id,flight_id,travel_date,cabin,amount) VALUES (5,5,48,'2026-10-21','ECO',234.95)",
        "INSERT INTO passengers (id,booking_id,first_name,last_name,title,date_of_birth,gender,mp_number,seat,checked_in,boarding_group) "
        "VALUES (5,5,'Sam','Ortiz','Mr','1990-05-10','Male','','',0,'')",
    ],
}
