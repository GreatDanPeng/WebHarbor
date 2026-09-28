"""Frozen honest-run fixtures for the speedo verifier tests.

Extracted from the reviewer's live 21/21 honest walkthroughs
(2026-09-26, review container wh-speedo-review): per task the
visited URL trail, the final answer (DB-derived totals), and the
exact SQL that reproduces the observed after-DB from the
deterministic seed. No LLM.
"""

BASE = "http://localhost:40136/"

SPECS = {
    0: {
        'urls': [
            "/pages/swimsuit-quiz",
            "/pages/swimsuit-quiz?step=1",
            "/pages/swimsuit-quiz?step=2",
            "/pages/swimsuit-quiz/results",
            "/products/womens-fastskin-lzr-ignite-kneeskin-black-grey-81343719224",
            "/cart",
            "/checkout",
            "/order/confirmation/SP100008",
        ],
        'answer': "Cheapest recommended kneeskin: Women's Fastskin LZR Ignite Kneeskin Black/Grey \u00a3114.00 (on sale), size 26. Order SP100008, Express Delivery, total charged \u00a3122.99.",
        'sql': [
            "INSERT INTO \"orders\" (\"id\", \"order_number\", \"user_id\", \"email\", \"status\", \"subtotal\", \"discount\", \"shipping_method\", \"shipping\", \"total\", \"discount_code\", \"ship_name\", \"ship_line1\", \"ship_line2\", \"ship_city\", \"ship_postcode\", \"ship_country\", \"card_brand\", \"card_last4\", \"tracking_number\", \"placed_on\") VALUES (8, 'SP100008', NULL, 'maya.torres@example.com', 'Processing', 114.0, 0.0, 'Express Delivery', 8.99, 122.99, '', 'Maya Torres', '22 Harbour Reach', '', 'Portsmouth', 'PO1 3XY', 'United Kingdom', 'Visa', '4242', '', '2026-09-26')",
            "INSERT INTO \"order_items\" (\"id\", \"order_id\", \"product_id\", \"product_name\", \"product_slug\", \"size\", \"qty\", \"unit_price\") VALUES (12, 8, 985, 'Women''s Fastskin LZR Ignite Kneeskin Black/Grey', 'womens-fastskin-lzr-ignite-kneeskin-black-grey-81343719224', '26', 1, 114.0)",
        ],
    },
    1: {
        'urls': [
            "/login",
            "/account",
            "/account/wishlist",
            "/search?q=Men%27s+Fastskin+LZR+Pure+Valor+2.0+Jammer",
            "/products/mens-fastskin-lzr-pure-valor-2-0-jammer-blue-815861040",
            "/account/wishlist",
        ],
        'answer': ("Removed jammer (not Fastskin LZR): Men's Hyperboom Jammer Black/Red. "
                   "Items remaining on the wishlist: Men's Fastskin LZR Pure Intent 2.0 "
                   "Jammer Red/Black, Speedo iQ Vanquisher 3.0 Mirror Track Purple, 25L "
                   "Flex Bag White/Black, Women's Endurance+ Logo Thinstrap Bikini Set "
                   "Red, plus the added Men's Fastskin LZR Pure Valor 2.0 Jammer Blue. "
                   "New wishlist count: 5."),
        'sql': [
            "DELETE FROM \"wishlist_items\" WHERE \"id\" = 7",
            "INSERT INTO \"wishlist_items\" (\"id\", \"user_id\", \"product_id\", \"added_at\") VALUES (19, 2, 540, '')",
        ],
    },
    2: {
        'urls': [
            "/login",
            "/account",
            "/cart",
            "/search?q=Women%27s+Endurance%2B+Medalist+Swimsuit",
            "/products/womens-endurance-medalist-swimsuit-black-8134710001",
            "/cart",
            "/search?q=Women%27s+Endurance%2B+Medalist+Swimsuit+Navy",
            "/products/womens-endurance-medalist-swimsuit-navy-813471d740",
            "/cart",
            "/checkout",
            "/order/confirmation/SP100008",
        ],
        'answer': "Basket cleared (Endurance+ Medalist Black 28, Biofuse 2.0 Goggles Black). Added Women's Endurance+ Medalist Swimsuit Black \u00a331.00 and Navy \u00a323.25, both size 34. WELCOME15 applied (-\u00a38.14). Order SP100008, Standard Delivery, total \u00a352.10.",
        'sql': [
            "DELETE FROM \"cart_items\" WHERE \"id\" = 1",
            "DELETE FROM \"cart_items\" WHERE \"id\" = 2",
            "INSERT INTO \"orders\" (\"id\", \"order_number\", \"user_id\", \"email\", \"status\", \"subtotal\", \"discount\", \"shipping_method\", \"shipping\", \"total\", \"discount_code\", \"ship_name\", \"ship_line1\", \"ship_line2\", \"ship_city\", \"ship_postcode\", \"ship_country\", \"card_brand\", \"card_last4\", \"tracking_number\", \"placed_on\") VALUES (8, 'SP100008', 1, 'alice.j@test.com', 'Processing', 54.25, 8.14, 'Standard Delivery', 5.99, 52.1, 'WELCOME15', 'Alice Johnson', '12 Marina Way', 'Flat 3', 'Brighton', 'BN1 1AA', 'United Kingdom', 'Visa', '4242', '', '2026-09-26')",
            "INSERT INTO \"order_items\" (\"id\", \"order_id\", \"product_id\", \"product_name\", \"product_slug\", \"size\", \"qty\", \"unit_price\") VALUES (12, 8, 957, 'Women''s Endurance+ Medalist Swimsuit Black', 'womens-endurance-medalist-swimsuit-black-8134710001', '34', 1, 31.0)",
            "INSERT INTO \"order_items\" (\"id\", \"order_id\", \"product_id\", \"product_name\", \"product_slug\", \"size\", \"qty\", \"unit_price\") VALUES (13, 8, 961, 'Women''s Endurance+ Medalist Swimsuit Navy', 'womens-endurance-medalist-swimsuit-navy-813471d740', '34', 1, 23.25)",
        ],
    },
    3: {
        'urls': [
            "/pages/size-guides",
            "/search?q=Women%27s+Sculpture+Boom+Back+Swimsuit",
            "/products/womens-sculpture-boom-back-swimsuit-black-8a000165002",
            "/cart",
            "/checkout",
            "/order/confirmation/SP100008",
        ],
        'answer': "Women's cm size guide: bust 91 / waist 77 / hips 102 -> Speedo size 36 (UK 14). Women's Sculpture Boom Back Swimsuit Black, size 36. Order SP100008, Standard Delivery free over \u00a350, total \u00a372.00.",
        'sql': [
            "INSERT INTO \"orders\" (\"id\", \"order_number\", \"user_id\", \"email\", \"status\", \"subtotal\", \"discount\", \"shipping_method\", \"shipping\", \"total\", \"discount_code\", \"ship_name\", \"ship_line1\", \"ship_line2\", \"ship_city\", \"ship_postcode\", \"ship_country\", \"card_brand\", \"card_last4\", \"tracking_number\", \"placed_on\") VALUES (8, 'SP100008', NULL, 'carol.davis@example.com', 'Processing', 72.0, 0.0, 'Standard Delivery', 0.0, 72.0, '', 'Carol Davis', '5 Lido Terrace', '', 'Bristol', 'BS1 4TR', 'United Kingdom', 'Mastercard', '9183', '', '2026-09-26')",
            "INSERT INTO \"order_items\" (\"id\", \"order_id\", \"product_id\", \"product_name\", \"product_slug\", \"size\", \"qty\", \"unit_price\") VALUES (12, 8, 1154, 'Women''s Sculpture Boom Back Swimsuit Black', 'womens-sculpture-boom-back-swimsuit-black-8a000165002', '36', 1, 72.0)",
        ],
    },
    4: {
        'urls': [
            "/login",
            "/account",
            "/account/orders/SP100007",
            "/pages/contact",
        ],
        'answer': "Most recent jammer order: SP100007, status Dispatched, tracking SDRM100522663GB, charged to Visa ending 9902. Contact case opened (Orders & Delivery / Where is my order, quoting SP100007): case reference CAS100001.",
        'sql': [
            "INSERT INTO \"contact_messages\" (\"id\", \"case_ref\", \"user_id\", \"first_name\", \"last_name\", \"email\", \"category\", \"subcategory\", \"order_number\", \"address_line\", \"postcode\", \"message\", \"submitted_on\", \"status\") VALUES (1, 'CAS100001', 4, 'David', 'Kim', 'david.k@test.com', 'Orders & Delivery', 'Where is my order', 'SP100007', '', '', 'Please update me on the delivery of my order SP100007.', '2026-09-26', 'Open')",
        ],
    },
    5: {
        'urls': [
            "/",
            "/collections/men-fitness",
            "/collections/men-fitness?page=2",
            "/products/mens-hyperboom-splice-mid-jammer-navy-8a000254002",
            "/products/mens-hyperboom-splice-mid-jammer-navy-green-8a000254004",
            "/cart",
            "/checkout",
            "/order/confirmation/SP100008",
        ],
        'answer': "Most expensive in-stock men's fitness jammer under \u00a350 with size 34: Men's Hyperboom Splice Mid Jammer Navy/Green \u00a335.00 (Navy colourway sold out in 34). Order SP100008, Express Delivery, total \u00a343.99.",
        'sql': [
            "INSERT INTO \"orders\" (\"id\", \"order_number\", \"user_id\", \"email\", \"status\", \"subtotal\", \"discount\", \"shipping_method\", \"shipping\", \"total\", \"discount_code\", \"ship_name\", \"ship_line1\", \"ship_line2\", \"ship_city\", \"ship_postcode\", \"ship_country\", \"card_brand\", \"card_last4\", \"tracking_number\", \"placed_on\") VALUES (8, 'SP100008', NULL, 'sam.whitfield@example.com', 'Processing', 35.0, 0.0, 'Express Delivery', 8.99, 43.99, '', 'Sam Whitfield', '7 Quay Street', '', 'Southampton', 'SO14 2AB', 'United Kingdom', 'Visa', '1111', '', '2026-09-26')",
            "INSERT INTO \"order_items\" (\"id\", \"order_id\", \"product_id\", \"product_name\", \"product_slug\", \"size\", \"qty\", \"unit_price\") VALUES (12, 8, 586, 'Men''s Hyperboom Splice Mid Jammer Navy/Green', 'mens-hyperboom-splice-mid-jammer-navy-green-8a000254004', '34', 1, 35.0)",
        ],
    },
    6: {
        'urls': [
            "/pages/goggles",
            "/collections/goggles-all",
            "/collections/goggles-all?lens_type=Prescription",
            "/products/adult-hydropure-optical-goggles-black-812670f808",
            "/products/adult-mariner-pro-optical-kit-black-silver-8135317485",
            "/products/adult-vanquisher-3-0-optical-goggles-black-grey-8e000041002",
            "/products/adult-biofuse-2-0-optical-goggles-grey-black-8e000412002",
            "/products/adult-vanquisher-3-0-optical-goggles-white-clear-8e000041003",
            "/products/adult-biofuse-2-0-optical-goggles-clear-blue-8e000412003",
            "/products/adult-hydropure-optical-goggles-black-812670f808",
            "/cart",
            "/checkout",
            "/order/confirmation/SP100008",
        ],
        'answer': "Lens-type facet = Prescription. Cheapest in-stock -4.5 prescription goggles under \u00a325: Adult Hydropure Optical Goggles Black \u00a321.75, lens -4.5. Order SP100008, Standard Delivery, total \u00a327.74.",
        'sql': [
            "INSERT INTO \"orders\" (\"id\", \"order_number\", \"user_id\", \"email\", \"status\", \"subtotal\", \"discount\", \"shipping_method\", \"shipping\", \"total\", \"discount_code\", \"ship_name\", \"ship_line1\", \"ship_line2\", \"ship_city\", \"ship_postcode\", \"ship_country\", \"card_brand\", \"card_last4\", \"tracking_number\", \"placed_on\") VALUES (8, 'SP100008', NULL, 'nina.petrova@example.com', 'Processing', 21.75, 0.0, 'Standard Delivery', 5.99, 27.74, '', 'Nina Petrova', '15 Riverside Court', '', 'London', 'SE1 9RE', 'United Kingdom', 'Visa', '8812', '', '2026-09-26')",
            "INSERT INTO \"order_items\" (\"id\", \"order_id\", \"product_id\", \"product_name\", \"product_slug\", \"size\", \"qty\", \"unit_price\") VALUES (12, 8, 68, 'Adult Hydropure Optical Goggles Black', 'adult-hydropure-optical-goggles-black-812670f808', '-4.5', 1, 21.75)",
        ],
    },
    7: {
        'urls': [
            "/login",
            "/account",
            "/account/profile",
            "/account/addresses",
        ],
        'answer': "Profile phone updated to +44 1632 960111. Added default address: Home, 3 Cliffside Road, Newquay, TR7 1AA; removed the old Plymouth address. 2 addresses saved; the Newquay Home address is the default.",
        'sql': [
            "UPDATE \"users\" SET \"id\" = 3, \"email\" = 'carol.d@test.com', \"password_hash\" = '$2b$12$WtOBgikyE24OU/kuhls4Fuy1s2Kuz/osD0cproGZjpkL713kWy58q', \"name\" = 'Carol Davis', \"phone\" = '+44 1632 960111', \"created_at\" = '2026-01-15 00:00:00.000000', \"accepts_marketing\" = 1 WHERE \"id\" = 3",
            "DELETE FROM \"addresses\" WHERE \"id\" = 5",
            "INSERT INTO \"addresses\" (\"id\", \"user_id\", \"label\", \"first_name\", \"last_name\", \"line1\", \"line2\", \"city\", \"postcode\", \"country\", \"phone\", \"is_default\") VALUES (7, 3, 'Home', 'Carol', 'Davis', '3 Cliffside Road', '', 'Newquay', 'TR7 1AA', 'United Kingdom', '', 1)",
            "UPDATE \"addresses\" SET \"id\" = 4, \"user_id\" = 3, \"label\" = 'Home', \"first_name\" = 'Carol', \"last_name\" = 'Davis', \"line1\" = '5 Lido Terrace', \"line2\" = '', \"city\" = 'Bristol', \"postcode\" = 'BS1 4TR', \"country\" = 'United Kingdom', \"phone\" = '', \"is_default\" = 0 WHERE \"id\" = 4",
        ],
    },
    8: {
        'urls': [
            "/login",
            "/account",
            "/account/wishlist",
            "/search?q=Sculpture+Boom+Back+Swimsuit",
            "/products/womens-sculpture-boom-back-swimsuit-black-8a000165002",
            "/account/wishlist",
        ],
        'answer': ("Removed the non-swimsuit items: Men's Endurance+ Jammer Black and Adult "
                   "Fastskin Hyper Elite Mirrored Goggles Smoke/Red. Items remaining on the "
                   "wishlist: Women's Fastskin LZR Pure Valor 2.0 Openback Kneeskin Red/Black, "
                   "Women's Hyperboom Printed Medalist Swimsuit Blue/Pink, plus the added "
                   "Women's Sculpture Boom Back Swimsuit Black. Final wishlist count: 3."),
        'sql': [
            "DELETE FROM \"wishlist_items\" WHERE \"id\" = 2",
            "DELETE FROM \"wishlist_items\" WHERE \"id\" = 3",
            "INSERT INTO \"wishlist_items\" (\"id\", \"user_id\", \"product_id\", \"added_at\") VALUES (19, 1, 1154, '')",
        ],
    },
    9: {
        'urls': [
            "/login",
            "/account",
            "/cart",
            "/search?q=swim+cap+purple",
            "/products/adult-long-hair-pace-cap-purple-812806a791",
            "/cart",
            "/products/adult-bubble-cap-pink-870929d669",
            "/cart",
            "/products/adult-silicone-cap-purple-870984014",
            "/cart",
            "/products/plain-moulded-silicone-junior-purple-870990d438",
            "/products/unisex-long-hair-silicone-cap-blue-purple-80616816681",
            "/cart",
            "/checkout",
            "/order/confirmation/SP100008",
        ],
        'answer': "Basket subtotal was \u00a333.88, so \u00a316.12 more was needed for free UK delivery. Added every in-stock adult purple swim cap: Adult Bubble Cap Pink \u00a315.00, Adult Long Hair Pace Cap Purple \u00a311.25 and Adult Silicone Cap Purple \u00a36.75. Order SP100008, Standard Delivery, final total \u00a366.88 \u2014 delivery was free (over \u00a350).",
        'sql': [
            "DELETE FROM \"cart_items\" WHERE \"id\" = 6",
            "DELETE FROM \"cart_items\" WHERE \"id\" = 7",
            "INSERT INTO \"orders\" (\"id\", \"order_number\", \"user_id\", \"email\", \"status\", \"subtotal\", \"discount\", \"shipping_method\", \"shipping\", \"total\", \"discount_code\", \"ship_name\", \"ship_line1\", \"ship_line2\", \"ship_city\", \"ship_postcode\", \"ship_country\", \"card_brand\", \"card_last4\", \"tracking_number\", \"placed_on\") VALUES (8, 'SP100008', 3, 'carol.d@test.com', 'Processing', 66.88, 0.0, 'Standard Delivery', 0.0, 66.88, '', 'Carol Davis', '9 Seacombe Esplanade', '', 'Plymouth', 'PL1 3AA', 'United Kingdom', 'Mastercard', '9183', '', '2026-09-26')",
            "INSERT INTO \"order_items\" (\"id\", \"order_id\", \"product_id\", \"product_name\", \"product_slug\", \"size\", \"qty\", \"unit_price\") VALUES (12, 8, 206, 'Girls'' Endurance+ Medalist Swimsuit Navy', 'girls-endurance-medalist-swimsuit-navy-813457d740', '4', 1, 13.88)",
            "INSERT INTO \"order_items\" (\"id\", \"order_id\", \"product_id\", \"product_name\", \"product_slug\", \"size\", \"qty\", \"unit_price\") VALUES (13, 8, 117, 'Biofuse 2.0 Junior Goggles Clear/Blue', 'biofuse-2-0-junior-goggles-clear-blue-800336315947', 'One Size', 1, 20.0)",
            "INSERT INTO \"order_items\" (\"id\", \"order_id\", \"product_id\", \"product_name\", \"product_slug\", \"size\", \"qty\", \"unit_price\") VALUES (14, 8, 75, 'Adult Long Hair Pace Cap Purple', 'adult-long-hair-pace-cap-purple-812806a791', 'One Size', 1, 11.25)",
            "INSERT INTO \"order_items\" (\"id\", \"order_id\", \"product_id\", \"product_name\", \"product_slug\", \"size\", \"qty\", \"unit_price\") VALUES (15, 8, 88, 'Adult Silicone Cap Purple', 'adult-silicone-cap-purple-870984014', 'One Size', 1, 6.75)",
            "INSERT INTO \"order_items\" (\"id\", \"order_id\", \"product_id\", \"product_name\", \"product_slug\", \"size\", \"qty\", \"unit_price\") VALUES (16, 8, 38, 'Adult Bubble Cap Pink', 'adult-bubble-cap-pink-870929d669', 'One Size', 1, 15.0)",
        ],
    },
    10: {
        'urls': [
            "/",
            "/search?q=Women%27s+Hyperboom+Printed+Medalist+Swimsuit",
            "/products/womens-hyperboom-printed-medalist-swimsuit-blue-8a000244006",
            "/products/womens-hyperboom-printed-medalist-swimsuit-blue-green-8a000244003",
            "/products/womens-hyperboom-printed-medalist-swimsuit-blue-pink-8a000244002",
            "/products/girls-hyperboom-printed-medalist-swimsuit-black-8a000260004",
            "/products/girls-hyperboom-printed-medalist-swimsuit-blue-8a000260005",
            "/products/girls-hyperboom-printed-medalist-swimsuit-blue-green-8a000260003",
            "/products/girls-hyperboom-printed-medalist-swimsuit-blue-pink-8a000260002",
            "/products/girls-hyperboom-printed-medalist-swimsuit-pink-8a000260006",
            "/products/womens-hyberboom-allover-medalist-swimsuit-darkteal-green-81219916009",
            "/products/womens-hyperboom-printed-medalist-swimsuit-blue-8a000244006",
            "/cart",
            "/checkout",
            "/order/confirmation/SP100008",
        ],
        'answer': "Women's Hyperboom Printed Medalist Swimsuit colourways: Blue \u00a333.00 (size 38 in stock), Blue/Green \u00a326.40 (sold out in 38), Blue/Pink \u00a344.00 (sold out in 38). Bought the cheapest available in 38: Blue, size 38. Order SP100008, Standard Delivery, total \u00a338.99.",
        'sql': [
            "INSERT INTO \"orders\" (\"id\", \"order_number\", \"user_id\", \"email\", \"status\", \"subtotal\", \"discount\", \"shipping_method\", \"shipping\", \"total\", \"discount_code\", \"ship_name\", \"ship_line1\", \"ship_line2\", \"ship_city\", \"ship_postcode\", \"ship_country\", \"card_brand\", \"card_last4\", \"tracking_number\", \"placed_on\") VALUES (8, 'SP100008', NULL, 'freya.lindqvist@example.com', 'Processing', 33.0, 0.0, 'Standard Delivery', 5.99, 38.99, '', 'Freya Lindqvist', '30 Mill Pond Way', '', 'Bristol', 'BS3 4QN', 'United Kingdom', 'Visa', '4242', '', '2026-09-26')",
            "INSERT INTO \"order_items\" (\"id\", \"order_id\", \"product_id\", \"product_name\", \"product_slug\", \"size\", \"qty\", \"unit_price\") VALUES (12, 8, 1050, 'Women''s Hyperboom Printed Medalist Swimsuit Blue', 'womens-hyperboom-printed-medalist-swimsuit-blue-8a000244006', '38', 1, 33.0)",
        ],
    },
    11: {
        'urls': [
            "/",
            "/search?q=Women%27s+Endurance%2B+Medalist+Swimsuit",
            "/products/womens-endurance-medalist-swimsuit-black-8134710001",
            "/products/womens-endurance-medalist-swimsuit-blue-813471005",
            "/products/womens-endurance-medalist-swimsuit-blue-813471a369",
            "/products/womens-endurance-medalist-swimsuit-green-813471004",
            "/products/womens-endurance-medalist-swimsuit-navy-813471d740",
            "/products/womens-endurance-medalist-swimsuit-red-8134716446",
            "/products/womens-endurance-printed-medalist-swimsuit-black-800305300334",
            "/products/womens-endurance-printed-medalist-swimsuit-dark-pink-8003053003",
            "/products/womens-plus-size-endurance-medalist-swimsuit-black-80039330001",
            "/products/girls-endurance-medalist-swimsuit-black-8134570001",
            "/products/girls-endurance-medalist-swimsuit-blue-813457a369",
            "/products/girls-endurance-medalist-swimsuit-navy-813457d740",
            "/products/girls-endurance-medalist-swimsuit-pink-813457b495",
            "/products/girls-endurance-medalist-swimsuit-red-8134576446",
            "/login",
            "/account",
            "/products/womens-endurance-medalist-swimsuit-navy-813471d740",
        ],
        'answer': "Women's Endurance+ Medalist Swimsuit colourways: Black \u00a331.00, Blue \u00a323.25, Blue \u00a323.25, Green \u00a323.25, Navy \u00a323.25, Red \u00a331.00, Printed Black \u00a322.80, Printed Dark Pink \u00a328.50, Plus Size Black \u00a333.00. The Plus Size Black is the most expensive. Navy size 34 added to Alice's wishlist.",
        'sql': [
            "INSERT INTO \"wishlist_items\" (\"id\", \"user_id\", \"product_id\", \"added_at\") VALUES (19, 1, 961, '')",
        ],
    },
    12: {
        'urls': [
            "/blogs/news/",
            "/blogs/news/4-easy-ways-to-care-for-your-swimming-goggles",
            "/pages/faqs",
            "/pages/contact",
        ],
        'answer': "Goggle-care blog rules: rinse goggles in fresh water after each swim, air-dry away from direct sunlight, never wipe or rub the lenses, store in their case. FAQ swimsuit rinse advice: rinse in cold water after every use. Contact case opened (Product Enquiry / Goggles): case reference CAS100001.",
        'sql': [
            "INSERT INTO \"contact_messages\" (\"id\", \"case_ref\", \"user_id\", \"first_name\", \"last_name\", \"email\", \"category\", \"subcategory\", \"order_number\", \"address_line\", \"postcode\", \"message\", \"submitted_on\", \"status\") VALUES (1, 'CAS100001', NULL, 'Kit', 'Owner', 'kit.owner@example.com', 'Product Enquiry', 'Goggles', '', '', '', 'Which goggles suit a chlorinated pool best?', '2026-09-26', 'Open')",
        ],
    },
    13: {
        'urls': [
            "/",
            "/search?q=Biofuse+2.0+Goggles",
            "/products/biofuse-2-0-goggles-black-800233214501",
            "/cart",
            "/checkout",
            "/order/confirmation/SP100008",
        ],
        'answer': "Biofuse 2.0 Goggles Black, One Size. Guest checkout with jamie.okafor@example.com. Order SP100008, Express Delivery (next working day), total \u00a333.99.",
        'sql': [
            "INSERT INTO \"orders\" (\"id\", \"order_number\", \"user_id\", \"email\", \"status\", \"subtotal\", \"discount\", \"shipping_method\", \"shipping\", \"total\", \"discount_code\", \"ship_name\", \"ship_line1\", \"ship_line2\", \"ship_city\", \"ship_postcode\", \"ship_country\", \"card_brand\", \"card_last4\", \"tracking_number\", \"placed_on\") VALUES (8, 'SP100008', NULL, 'jamie.okafor@example.com', 'Processing', 25.0, 0.0, 'Express Delivery', 8.99, 33.99, '', 'Jamie Okafor', '9 Old Wharf Lane', '', 'Plymouth', 'PL1 3LQ', 'United Kingdom', 'Visa', '5556', '', '2026-09-26')",
            "INSERT INTO \"order_items\" (\"id\", \"order_id\", \"product_id\", \"product_name\", \"product_slug\", \"size\", \"qty\", \"unit_price\") VALUES (12, 8, 112, 'Biofuse 2.0 Goggles Black', 'biofuse-2-0-goggles-black-800233214501', 'One Size', 1, 25.0)",
        ],
    },
    14: {
        'urls': [
            "/login",
            "/register",
            "/account",
            "/search?q=Kids+Sunny+G+goggles",
            "/products/kids-sunny-g-pop-sea-shells-goggles-pink-blue-8775070515063",
            "/products/kids-sunny-g-pop-seasiders-goggles-blue-green-8775070415036",
            "/products/kids-sunny-g-sea-shells-goggles-blue-8775050515064",
            "/products/kids-sunny-g-sea-shells-goggles-pink-8775050515096",
            "/products/kids-sunny-g-seasiders-goggles-blue-8775049115066",
            "/products/kids-sunny-g-seasiders-goggles-red-87750491618",
            "/products/kids-sunny-g-seasiders-goggles-white-8775049115057",
            "/products/kids-sunny-g-mariner-mirrored-800413214938",
            "/products/kids-sunny-g-mariner-mirrored-silver-gold-800413214474",
            "/products/minions-monsters-kids-sunny-g-goggle-8e101029002",
            "/products/minions-monsters-adult-sunny-g-goggle-8e101028002",
            "/products/kids-sunny-g-seasiders-goggles-white-8775049115057",
            "/account",
            "/account/profile",
            "/account/wishlist",
        ],
        'answer': "Cheapest in-stock Kids Sunny G goggles: Kids Sunny G Seasiders Goggles White \u00a38.00 \u2014 saved to the wishlist (count 1). Profile phone updated to +44 7700 900123.",
        'sql': [
            "INSERT INTO \"users\" (\"id\", \"email\", \"password_hash\", \"name\", \"phone\", \"created_at\", \"accepts_marketing\") VALUES (5, 'priya.sharma@example.com', '$2b$12$oJ4vxxx6JKJaBV2QKUgKL.QQUUzNRXh2ylgXKr6R8bHoNsOBS2chS', 'Priya Sharma', '+44 7700 900123', NULL, 0)",
            "INSERT INTO \"wishlist_items\" (\"id\", \"user_id\", \"product_id\", \"added_at\") VALUES (19, 5, 388, '')",
        ],
    },
    15: {
        'urls': [
            "/",
            "/search?q=Adult+Bubble+Active%2B+Cap+White",
            "/products/adult-bubble-active-cap-white-8139540003",
            "/cart",
            "/checkout",
            "/order/confirmation/SP100008",
        ],
        'answer': "Newsletter welcome code: WELCOME15. Adult Bubble Active+ Cap White \u00a315.00, code applied (-\u00a32.25). Order SP100008, Standard Delivery, total \u00a318.74.",
        'sql': [
            "INSERT INTO \"newsletter_signups\" (\"id\", \"email\", \"signed_up_on\") VALUES (1, 'alex.novak@example.com', '2026-09-26')",
            "INSERT INTO \"orders\" (\"id\", \"order_number\", \"user_id\", \"email\", \"status\", \"subtotal\", \"discount\", \"shipping_method\", \"shipping\", \"total\", \"discount_code\", \"ship_name\", \"ship_line1\", \"ship_line2\", \"ship_city\", \"ship_postcode\", \"ship_country\", \"card_brand\", \"card_last4\", \"tracking_number\", \"placed_on\") VALUES (8, 'SP100008', NULL, 'alex.novak@example.com', 'Processing', 15.0, 2.25, 'Standard Delivery', 5.99, 18.74, 'WELCOME15', 'Alex Novak', '118 Sefton Park Road', '', 'Liverpool', 'L17 1BQ', 'United Kingdom', 'Visa', '4242', '', '2026-09-26')",
            "INSERT INTO \"order_items\" (\"id\", \"order_id\", \"product_id\", \"product_name\", \"product_slug\", \"size\", \"qty\", \"unit_price\") VALUES (12, 8, 36, 'Adult Bubble Active+ Cap White', 'adult-bubble-active-cap-white-8139540003', 'One Size', 1, 15.0)",
        ],
    },
    16: {
        'urls': [
            "/pages/size-guides",
            "/search?q=Boys%27+Endurance%2B+Jammer",
            "/products/boys-endurance-jammer-black-8134600001",
            "/products/boys-endurance-jammer-navy-813460d740",
            "/products/boys-endurance-logo-jammer-black-8a000187003",
            "/products/boys-endurance-logo-jammer-blue-8a000187006",
            "/products/boys-endurance-logo-jammer-navy-8a000187002",
            "/products/boys-endurance-logo-jammer-red-8a000187008",
            "/products/boys-endurance-jammer-black-8134600001",
            "/cart",
            "/checkout",
            "/order/confirmation/SP100008",
        ],
        'answer': "Kids' size guide: 9-year-old with 66cm waist -> Speedo size 28, age band 9-10 Yrs. Cheapest in-stock Boys' Endurance+ Jammer in that band: Boys' Endurance+ Jammer Black \u00a314.63, size 9-10. Order SP100008, Standard Delivery, total \u00a320.62.",
        'sql': [
            "INSERT INTO \"orders\" (\"id\", \"order_number\", \"user_id\", \"email\", \"status\", \"subtotal\", \"discount\", \"shipping_method\", \"shipping\", \"total\", \"discount_code\", \"ship_name\", \"ship_line1\", \"ship_line2\", \"ship_city\", \"ship_postcode\", \"ship_country\", \"card_brand\", \"card_last4\", \"tracking_number\", \"placed_on\") VALUES (8, 'SP100008', NULL, 'hannah.cole@example.com', 'Processing', 14.63, 0.0, 'Standard Delivery', 5.99, 20.62, '', 'Hannah Cole', '44 Bramble Road', '', 'Exeter', 'EX2 5TA', 'United Kingdom', 'Mastercard', '7890', '', '2026-09-26')",
            "INSERT INTO \"order_items\" (\"id\", \"order_id\", \"product_id\", \"product_name\", \"product_slug\", \"size\", \"qty\", \"unit_price\") VALUES (12, 8, 142, 'Boys'' Endurance+ Jammer Black', 'boys-endurance-jammer-black-8134600001', '9-10', 1, 14.63)",
        ],
    },
    17: {
        'urls': [
            "/pages/team-speedo",
            "/pages/team-speedo-leon-marchand",
            "/search?q=Women%27s+Fastskin+LZR+Ignite+Kneeskin",
            "/products/womens-fastskin-lzr-ignite-kneeskin-black-8134370001",
            "/products/womens-fastskin-lzr-ignite-kneeskin-black-grey-81343719224",
            "/products/womens-fastskin-lzr-ignite-kneeskin-blue-81343719223",
            "/products/womens-fastskin-lzr-ignite-kneeskin-blue-pink-81343715334",
            "/products/womens-fastskin-lzr-ignite-kneeskin-blue-purple-81343718475",
            "/products/womens-fastskin-lzr-ignite-kneeskin-green-black-813437h819",
            "/products/womens-fastskin-lzr-ignite-kneeskin-navy-purple-813437003",
        ],
        'answer': "The four Team GB athletes: Adam Ramsay-Peaty, Alice Tai, Duncan Scott, Matt Richards. The motto 'Never fear failure' belongs to L\u00e9on Marchand; he wore the Speedo Fastskin Valor at the Paris 2024 Olympics. Cheapest in-stock Women's Fastskin LZR Ignite Kneeskin colourway: \u00a3114.00.",
        'sql': [],
    },
    18: {
        'urls': [
            "/",
            "/pages/goggles-quiz",
            "/pages/goggles-quiz?step=1",
            "/pages/goggles-quiz?step=2",
            "/pages/goggles-quiz/results",
            "/products/adult-hydrosity-2-0-goggles-teal-clear-8004460002",
            "/cart",
            "/checkout",
            "/order/confirmation/SP100008",
        ],
        'answer': "Goggles quiz (Adults -> Fitness -> Clear) recommends Biofuse 2.0 Optical Clear/Blue \u00a330.00, Hydrosity 2.0 Teal/Clear \u00a318.00 and Biofuse 2.0 Red \u00a325.00. Cheapest in stock: Adult Hydrosity 2.0 Goggles Teal/Clear \u00a318.00. Order SP100008, Standard Delivery, total \u00a323.99.",
        'sql': [
            "INSERT INTO \"orders\" (\"id\", \"order_number\", \"user_id\", \"email\", \"status\", \"subtotal\", \"discount\", \"shipping_method\", \"shipping\", \"total\", \"discount_code\", \"ship_name\", \"ship_line1\", \"ship_line2\", \"ship_city\", \"ship_postcode\", \"ship_country\", \"card_brand\", \"card_last4\", \"tracking_number\", \"placed_on\") VALUES (8, 'SP100008', NULL, 'marta.nowak@example.com', 'Processing', 18.0, 0.0, 'Standard Delivery', 5.99, 23.99, '', 'Marta Nowak', '61 Castle View', '', 'Edinburgh', 'EH1 2NB', 'United Kingdom', 'Visa', '9012', '', '2026-09-26')",
            "INSERT INTO \"order_items\" (\"id\", \"order_id\", \"product_id\", \"product_name\", \"product_slug\", \"size\", \"qty\", \"unit_price\") VALUES (12, 8, 70, 'Adult Hydrosity 2.0 Goggles Teal/Clear', 'adult-hydrosity-2-0-goggles-teal-clear-8004460002', 'One Size', 1, 18.0)",
        ],
    },
    19: {
        'urls': [
            "/login",
            "/account",
            "/account/payment",
            "/account/wishlist",
        ],
        'answer': "Removed the existing Visa ****9902 and added the new default Visa ****5678 (Club, exp 03/29). 1 card saved; the Visa ****5678 is the default. Removed the two pairs of goggles from the wishlist; remaining wishlist count: 4.",
        'sql': [
            "UPDATE \"payment_cards\" SET \"id\" = 5, \"user_id\" = 4, \"label\" = 'Club', \"brand\" = 'Visa', \"last4\" = '5678', \"exp_month\" = 3, \"exp_year\" = 29, \"is_default\" = 1 WHERE \"id\" = 5",
            "DELETE FROM \"wishlist_items\" WHERE \"id\" = 14",
            "DELETE FROM \"wishlist_items\" WHERE \"id\" = 17",
        ],
    },
    20: {
        'urls': [
            "/",
            "/search?q=Adult+Silicone+Cap+Purple",
            "/products/adult-silicone-cap-purple-870984014",
            "/cart",
            "/checkout",
            "/order/confirmation/SP100008",
        ],
        'answer': "Adult Silicone Cap Purple \u00a36.75, One Size, Standard Delivery \u00a35.99 (under \u00a310). Guest checkout with casey.morgan@example.com. Order SP100008, total \u00a312.74.",
        'sql': [
            "INSERT INTO \"orders\" (\"id\", \"order_number\", \"user_id\", \"email\", \"status\", \"subtotal\", \"discount\", \"shipping_method\", \"shipping\", \"total\", \"discount_code\", \"ship_name\", \"ship_line1\", \"ship_line2\", \"ship_city\", \"ship_postcode\", \"ship_country\", \"card_brand\", \"card_last4\", \"tracking_number\", \"placed_on\") VALUES (8, 'SP100008', NULL, 'casey.morgan@example.com', 'Processing', 6.75, 0.0, 'Standard Delivery', 5.99, 12.74, '', 'Casey Morgan', '2 Windmill Lane', '', 'Leeds', 'LS6 1QR', 'United Kingdom', 'Visa', '4242', '', '2026-09-26')",
            "INSERT INTO \"order_items\" (\"id\", \"order_id\", \"product_id\", \"product_name\", \"product_slug\", \"size\", \"qty\", \"unit_price\") VALUES (12, 8, 88, 'Adult Silicone Cap Purple', 'adult-silicone-cap-purple-870984014', 'One Size', 1, 6.75)",
        ],
    },
}
