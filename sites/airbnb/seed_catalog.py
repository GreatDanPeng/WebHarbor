"""Deterministic seed for the Airbnb mirror.

Loaded by app.py after the models are defined. Every seed function is gated
as a whole (see AGENTS.md "Idempotent seeding"): a populated database returns
before any write, so a boot or /reset never bumps SQLite metadata.

Upstream-sourced fields (listing names, types, capacity, prices, ratings,
amenities, sleeping arrangements, house rules, host stats, photos) come from
source_data_listings.json. Fields the upstream page does not publish in a
machine-readable form (cleaning fee, stay discounts, minimum stay, Instant
Book, calendar, reviews text) are derived from a hash of the upstream room id
so every build is identical.
Guest reviews are mirror-authored templates signed with first names only;
no upstream review text or reviewer identity is reproduced.
"""
import hashlib
import json
import random
import sys
from datetime import date, datetime, timedelta


def _m():
    """The already-imported app module (works for `import app` and __main__)."""
    return sys.modules.get('app') or sys.modules['__main__']


def _h(listing_id, salt: str) -> int:
    return int(hashlib.sha256(f'airbnb-{salt}-{listing_id}'.encode()).hexdigest()[:12], 16)


# Search filter keys, matched against upstream amenity titles (lower-cased,
# first match wins). Titles that match nothing are listed but not filterable.
FILTER_RULES = (
    ('ev_charger', ('ev charger',)),
    ('hot_tub', ('hot tub',)),
    ('pool', ('pool',)),
    ('wifi', ('wifi',)),
    ('kitchen', ('kitchen',)),
    ('dryer', ('dryer',)),
    ('washer', ('washer',)),
    ('air_conditioning', ('air conditioning', 'ac - ', 'ac – ', 'portable air')),
    ('heating', ('heating', 'radiant heating', 'central heating')),
    ('workspace', ('workspace',)),
    ('free_parking', ('free parking on premises', 'free driveway parking',
                      'free carport on premises', 'free residential garage')),
    ('crib', ('crib',)),
    ('gym', ('gym',)),
    ('bbq', ('bbq grill',)),
    ('breakfast', ('breakfast',)),
    ('fireplace', ('indoor fireplace',)),
    ('balcony', ('patio or balcony', 'balcony')),
    ('elevator', ('elevator',)),
    ('waterfront', ('waterfront',)),
    ('beach_access', ('beach access',)),
    ('co_alarm', ('carbon monoxide alarm',)),
    ('smoke_alarm', ('smoke alarm',)),
    ('tv', ('tv', 'hdtv')),
)
EXCLUDE_FROM_FILTER = ('hair dryer', 'dryer – in building', 'dryer - in building',
                       'crib - available upon request', 'tv not', 'pool table',
                       'baby bath', 'dining table')


def filter_key_for(title: str):
    low = title.lower()
    if any(x in low for x in ('hair dryer', 'pool table', 'pool toys')):
        return None
    for key, needles in FILTER_RULES:
        for needle in needles:
            if needle in ('tv',):
                words = low.replace('-', ' ').replace('–', ' ').split()
                if 'tv' in words or 'hdtv' in words:
                    return key
                continue
            if needle in low:
                return key
    return None


def _property_group(room_type: str, property_type: str) -> str:
    low = property_type.lower()
    if room_type == 'Hotel room' or any(w in low for w in ('hotel', 'hostel', 'aparthotel', 'resort')):
        return 'Hotel'
    if any(w in low for w in ('guest suite', 'guesthouse', 'guest house', 'bed and breakfast',
                              'casa particular', 'farm stay', 'nature lodge')):
        return 'Guesthouse'
    if any(w in low for w in ('rental unit', 'condo', 'apartment', 'loft', 'serviced',
                              'flat', 'residential')):
        return 'Apartment'
    return 'House'


def _derive_cleaning(src, h):
    if src.get('cleaning_fee') is not None:
        return int(src['cleaning_fee'])
    if h % 7 == 0:
        return 0
    nightly = int(src['nightly_price'])
    if src['room_type'] in ('Private room', 'Shared room', 'Hotel room'):
        fee = 10 + (h // 7 % 5) * 5
    else:
        fee = 35 + 15 * max(1, int(src.get('bedrooms') or 1)) + (h // 7 % 6) * 5
    return int(min(fee, max(10, round(nightly * 0.8 / 5) * 5)))


def _derive_policy(src, h):
    if src.get('cancellation') in ('Flexible', 'Moderate', 'Firm', 'Strict'):
        return src['cancellation']
    return ('Flexible', 'Moderate', 'Moderate', 'Firm', 'Strict', 'Moderate', 'Flexible', 'Firm')[h % 8]


def _percent(value):
    """'100%' / 98 / None -> int percent or None (host response rate)."""
    if value is None:
        return None
    digits = ''.join(c for c in str(value) if c.isdigit())
    return int(digits) if digits else None


def _response_time(value):
    """'Responds within an hour' -> 'within an hour' (the template adds the verb)."""
    text = (value or '').strip()
    if text.lower().startswith('responds '):
        text = text[len('responds '):]
    return text or None


def _load():
    m = _m()
    return m._load_source('source_data_listings.json'), m._load_source('source_data_content.json')


# ---------------------------------------------------------------- reviews --

REVIEW_NAMES = (
    'Aaron', 'Abigail', 'Adrian', 'Aisha', 'Alejandro', 'Amelia', 'Ana', 'Andre', 'Anika',
    'Ben', 'Bianca', 'Caleb', 'Camille', 'Carlos', 'Chloe', 'Chris', 'Daniel', 'Daniela',
    'Deepa', 'Diego', 'Elena', 'Eli', 'Emma', 'Ethan', 'Fatima', 'Felix', 'Freya', 'Gabriel',
    'Grace', 'Hannah', 'Hiro', 'Ingrid', 'Isaac', 'Isabel', 'Jack', 'Jana', 'Javier', 'Jin',
    'Jonas', 'Julia', 'Kai', 'Karan', 'Katie', 'Leah', 'Leo', 'Lina', 'Lucas', 'Lucia',
    'Maya', 'Mateo', 'Mei', 'Mia', 'Nadia', 'Nathan', 'Nina', 'Noah', 'Olivia', 'Omar',
    'Paula', 'Pedro', 'Priya', 'Rafael', 'Rachel', 'Ravi', 'Rosa', 'Sam', 'Sara', 'Sofia',
    'Stefan', 'Tariq', 'Tessa', 'Theo', 'Tom', 'Valentina', 'Victor', 'Yara', 'Yuki', 'Zoe',
)
REVIEW_PLACES = (
    'Toronto, Canada', 'Chicago, Illinois', 'Austin, Texas', 'Seattle, Washington',
    'Denver, Colorado', 'Boston, Massachusetts', 'Berlin, Germany', 'Munich, Germany',
    'Amsterdam, Netherlands', 'Madrid, Spain', 'Milan, Italy', 'Lyon, France',
    'Dublin, Ireland', 'Edinburgh, United Kingdom', 'Stockholm, Sweden', 'Oslo, Norway',
    'Copenhagen, Denmark', 'Zurich, Switzerland', 'Vienna, Austria', 'Prague, Czechia',
    'Warsaw, Poland', 'Melbourne, Australia', 'Auckland, New Zealand', 'Singapore',
    'Seoul, South Korea', 'Taipei, Taiwan', 'São Paulo, Brazil', 'Buenos Aires, Argentina',
    'Bogotá, Colombia', 'Vancouver, Canada', 'San Diego, California', 'Atlanta, Georgia',
    'Miami, Florida', 'Philadelphia, Pennsylvania', 'Minneapolis, Minnesota',
    'Nashville, Tennessee', 'Montreal, Canada', 'Brussels, Belgium', 'Helsinki, Finland',
    'Cape Town, South Africa',
)
STAY_NOTES = ('Stayed a few nights', 'Stayed a few nights', 'Stayed about a week',
              'Stayed one night', 'Group trip', 'Stayed with kids', 'Stayed a few nights',
              'Stayed over a week')

OPENERS_5 = (
    'We loved our stay at {host}’s place.',
    'Everything was exactly as described.',
    'Fantastic stay from start to finish.',
    'One of the best Airbnbs we have stayed in.',
    '{host} was a wonderful host.',
    'Great place in a great spot.',
    'Such a comfortable and well-kept home.',
    'Would absolutely stay here again.',
)
DETAILS_5 = (
    'The location in {area} made it easy to explore on foot.',
    'Check-in was simple and {host} answered every question quickly.',
    'The space was spotless and the beds were really comfortable.',
    'It had everything we needed, including {amenity}.',
    'The photos don’t do it justice — it is even nicer in person.',
    'Quiet at night, which we really appreciated after long days out.',
    'Lots of cafés and restaurants within a few minutes’ walk.',
    '{host} left great recommendations for {city}.',
    'The {amenity} came in handy more than once.',
    'Perfect for our {purpose}.',
)
CLOSERS_5 = (
    'Highly recommend!', 'Thank you, {host}!', 'We’ll be back.', 'Five stars.',
    'Can’t wait to return to {city}.', '', '',
)
OPENERS_4 = (
    'Nice place overall.', 'Good stay with a couple of small issues.',
    'Solid choice for {city}.', 'Pleasant stay.',
)
DETAILS_4 = (
    'The location in {area} was convenient, though the street could be noisy in the evening.',
    'The space was clean, but a few kitchen basics were missing.',
    'Check-in took a little longer than expected, but {host} sorted it out.',
    'The beds were fine, although the second bedroom is on the small side.',
    'Wifi was a bit slow at times, otherwise everything worked well.',
    'The stairs are steep, so pack light.',
)
CLOSERS_4 = ('Would stay again.', 'Good value for the price.', 'Recommended.', '')
OPENERS_3 = ('The stay was okay.', 'Mixed experience.', 'Not quite what we expected.')
DETAILS_3 = (
    'The apartment needed a better clean when we arrived.',
    'It was noisier than the listing suggests.',
    'Some things in the photos were not there anymore.',
    'Hot water ran out quickly in the mornings.',
)
CLOSERS_3 = ('{host} was responsive when we reported the issues.', 'The location is still great.')
PURPOSES = ('family trip', 'work trip', 'weekend away', 'city break', 'first visit', 'long weekend')


def _review_ratings(rng, n, rating):
    deficit = max(0, round((5 - (rating or 5)) * n))
    ratings = [5] * n
    i = 0
    order = list(range(n))
    rng.shuffle(order)
    while deficit > 0 and i < n:
        drop = 2 if deficit >= 2 and rng.random() < 0.2 else 1
        ratings[order[i]] = 5 - drop
        deficit -= drop
        i += 1
    return ratings


def _review_body(rng, stars, ctx):
    if stars >= 5:
        parts = [rng.choice(OPENERS_5)] + rng.sample(DETAILS_5, 2) + [rng.choice(CLOSERS_5)]
    elif stars == 4:
        parts = [rng.choice(OPENERS_4), rng.choice(DETAILS_4), rng.choice(DETAILS_5),
                 rng.choice(CLOSERS_4)]
    else:
        parts = [rng.choice(OPENERS_3), rng.choice(DETAILS_3), rng.choice(CLOSERS_3)]
    return ' '.join(p for p in parts if p).format(**ctx)


def _seed_reviews(listing, amenity_titles):
    m = _m()
    if not listing.review_count:
        return
    rng = random.Random(f'airbnb-reviews-{listing.id}')
    n = min(listing.review_count, 6 + _h(listing.id, 'review-n') % 15)
    ratings = _review_ratings(rng, n, listing.rating)
    good_amenities = [a for a in amenity_titles if len(a) < 28] or ['kitchen']
    day = m.MIRROR_TODAY - timedelta(days=rng.randint(3, 12))
    for i in range(n):
        stars = ratings[i]
        ctx = {'host': listing.host.first_name,
               'area': listing.neighborhood or listing.city.name,
               'city': listing.city.name,
               'amenity': rng.choice(good_amenities).lower(),
               'purpose': rng.choice(PURPOSES)}
        cats = {}
        for field in ('cleanliness', 'accuracy', 'checkin', 'communication', 'location', 'value'):
            cats[field] = stars if rng.random() < 0.8 else max(3, min(5, stars + rng.choice((-1, 1))))
        m.db.session.add(m.Review(
            listing_id=listing.id, author_name=rng.choice(REVIEW_NAMES),
            author_location=rng.choice(REVIEW_PLACES), created=day, rating=stars,
            stay_note=rng.choice(STAY_NOTES), body=_review_body(rng, stars, ctx), **cats))
        day -= timedelta(days=rng.randint(4, 38))


# --------------------------------------------------------------- catalog ---

def seed_database():
    m = _m()
    if m.Listing.query.count() > 0:
        return
    data, content = _load()

    for pos, c in enumerate(data['cities']):
        m.db.session.add(m.City(id=pos + 1, slug=c['slug'], name=c['name'], region=c.get('region'),
                                country=c['country'], tax_rate=c['tax_rate'],
                                latitude=c.get('lat'), longitude=c.get('lng'), position=pos))
    m.db.session.flush()
    city_ids = {c.slug: c.id for c in m.City.query.all()}

    for h in data['hosts']:
        m.db.session.add(m.Host(
            id=int(h['id']), first_name=h['first_name'], is_superhost=bool(h.get('is_superhost')),
            years_hosting=int(h.get('years_hosting') or 0), months_hosting=h.get('months_hosting'),
            hosting_label=h.get('hosting_label'), rating=h.get('rating'),
            review_count=None if h.get('review_count') is None else int(h['review_count']),
            response_rate=_percent(h.get('response_rate')),
            response_time=_response_time(h.get('response_time')), languages=', '.join(h.get('languages') or []) or None,
            lives_in=h.get('lives_in'), work=h.get('work'), about=h.get('about'),
            identity_verified=None if h.get('identity_verified') is None else bool(h['identity_verified'])))
    m.db.session.flush()

    amenity_ids = {}
    for spec in content['amenity_catalog']:
        am = m.Amenity(name=spec['title'], category=spec['group'], filter_key=filter_key_for(spec['title']))
        m.db.session.add(am)
        m.db.session.flush()
        amenity_ids[spec['title']] = am.id

    for src in data['listings']:
        lid = int(src['id'])
        h = _h(lid, 'derive')
        rules = src.get('house_rules') or {}
        amenity_titles = [a['title'] for a in src.get('amenities', []) if a.get('available', True)]
        low_titles = ' | '.join(amenity_titles).lower()
        highlight_titles = ' | '.join(x['title'] for x in src.get('highlights', [])).lower()
        weekly = src.get('weekly_discount')
        if weekly is None:
            weekly = (0, 5, 10, 10, 15, 0, 8, 12)[h % 8]
        monthly = src.get('monthly_discount')
        if monthly is None:
            monthly = 0 if not weekly and h % 3 == 0 else max(weekly, (10, 15, 20, 25, 30)[(h // 8) % 5])
        pets = rules.get('pets_allowed')
        if pets is None:
            pets = 'pets allowed' in low_titles
        self_checkin = rules.get('self_checkin')
        if self_checkin is None:
            self_checkin = 'self check-in' in highlight_titles or 'self check-in' in low_titles
        instant = src.get('instant_book')
        if instant is None:
            instant = h % 10 < 6
        listing = m.Listing(
            id=lid, city_id=city_ids[src['city']], host_id=int(src['host_id']), rank=int(src['rank']),
            name=src['name'], title=src['title'], headline=src['headline'],
            room_type=src['room_type'], property_type=src['property_type'],
            property_group=src.get('property_group') or _property_group(src['room_type'], src['property_type']),
            neighborhood=src.get('neighborhood'), guests=int(src['guests']),
            bedrooms=int(src.get('bedrooms') or 0), beds=int(src.get('beds') or 1),
            baths=float(src.get('baths') or 1), baths_label=src['baths_label'],
            is_studio=bool(src.get('is_studio')), nightly_price=int(src['nightly_price']),
            cleaning_fee=_derive_cleaning(src, h), weekly_discount=int(weekly),
            monthly_discount=int(monthly),
            min_nights=int(src.get('min_nights') or (1, 1, 2, 2, 3, 1, 2)[(h // 3) % 7]),
            rating=src.get('rating'), review_count=int(src.get('review_count') or 0),
            r_cleanliness=(src.get('category_ratings') or {}).get('cleanliness'),
            r_accuracy=(src.get('category_ratings') or {}).get('accuracy'),
            r_checkin=(src.get('category_ratings') or {}).get('checkin'),
            r_communication=(src.get('category_ratings') or {}).get('communication'),
            r_location=(src.get('category_ratings') or {}).get('location'),
            r_value=(src.get('category_ratings') or {}).get('value'),
            is_guest_favorite=bool(src.get('guest_favorite')), instant_book=bool(instant),
            self_checkin=bool(self_checkin), pets_allowed=bool(pets),
            smoking_allowed=bool(rules.get('smoking_allowed', False)),
            events_allowed=bool(rules.get('events_allowed', False)),
            quiet_hours=rules.get('quiet_hours'),
            cancellation_policy=_derive_policy(src, h),
            checkin_time=rules.get('checkin') or ('Check-in after 3:00 PM', 'Check-in after 4:00 PM',
                                                  'Check-in: 3:00 PM - 10:00 PM')[h % 3],
            checkout_time=rules.get('checkout') or ('Checkout before 11:00 AM', 'Checkout before 10:00 AM',
                                                    'Checkout before 12:00 PM')[(h // 3) % 3],
            description=src['description'], space=src.get('space'),
            location_blurb=src.get('location_blurb'), latitude=src.get('lat'), longitude=src.get('lng'),
            source_url=f'https://www.airbnb.com/rooms/{lid}')
        m.db.session.add(listing)
        m.db.session.flush()
        for pos, photo in enumerate(src.get('photos', [])):
            m.db.session.add(m.ListingPhoto(listing_id=lid, position=pos, path=photo['path'],
                                            caption=photo.get('caption')))
        for pos, hl in enumerate(src.get('highlights', [])):
            m.db.session.add(m.Highlight(listing_id=lid, position=pos, title=hl['title'],
                                         subtitle=hl.get('subtitle')))
        for pos, sa in enumerate(src.get('sleeping', [])):
            m.db.session.add(m.SleepingArrangement(listing_id=lid, position=pos, room=sa['room'],
                                                   beds=sa['beds']))
        for pos, am in enumerate(src.get('amenities', [])):
            m.db.session.add(m.ListingAmenity(listing_id=lid, amenity_id=amenity_ids[am['title']],
                                              position=pos, detail=am.get('subtitle'),
                                              available=bool(am.get('available', True))))
        _seed_reviews(listing, amenity_titles)

    for pos, art in enumerate(content['help_articles']):
        m.db.session.add(m.HelpArticle(id=int(art['id']), title=art['title'], category=art['category'],
                                       audience=art['audience'], summary=art.get('summary'),
                                       body=json.dumps(art['blocks'], ensure_ascii=False),
                                       position=pos))
    m.db.session.commit()


# ------------------------------------------------------------- fixtures ---

BENCHMARK_USERS = (
    dict(first_name='Alice', last_name='Johnson', email='alice.j@test.com', phone='+1 (415) 555-0142',
         street='1458 Hayes Street', apt='Apt 3', city='San Francisco', state='CA', postal_code='94117',
         country='United States', lives_in='San Francisco, CA', work='Product designer',
         languages='English, French', about='Weekend explorer, coffee snob, always hunting for a place with a view.',
         joined=date(2019, 4, 2), identity_verified=True),
    dict(first_name='Robert', last_name='Chen', preferred_name='Bob', email='bob.c@test.com',
         phone='+1 (206) 555-0178', street='2210 Eastlake Avenue E', apt='Unit 5', city='Seattle',
         state='WA', postal_code='98102', country='United States', lives_in='Seattle, WA',
         work='Software engineer', languages='English, Mandarin', joined=date(2021, 1, 15),
         identity_verified=True),
    dict(first_name='Carol', last_name='Davis', email='carol.d@test.com', phone='+1 (312) 555-0119',
         street='740 N Rush Street', city='Chicago', state='IL', postal_code='60611',
         country='United States', lives_in='Chicago, IL', languages='English, Spanish',
         joined=date(2017, 9, 8), identity_verified=True),
    dict(first_name='David', last_name='Kim', email='david.k@test.com', phone='+1 (617) 555-0163',
         street='88 Beacon Street', city='Boston', state='MA', postal_code='02108',
         country='United States', joined=date(2024, 6, 20)),
)

CARDS = {
    'alice.j@test.com': (('Visa', '4242', 8, 2028, True), ('Mastercard', '5454', 3, 2027, False)),
    'bob.c@test.com': (('American Express', '1005', 11, 2029, True),),
    'carol.d@test.com': (('Visa', '1881', 5, 2028, True), ('Discover', '6011', 1, 2027, False)),
    'david.k@test.com': (('Mastercard', '4444', 9, 2030, True),),
}


def _pick(city_slug, rank_from=1, **need):
    """First listing in a city (by upstream rank >= rank_from) meeting `need`."""
    m = _m()
    city = m.City.query.filter_by(slug=city_slug).first()
    q = m.Listing.query.filter(m.Listing.city_id == city.id, m.Listing.rank >= rank_from)
    for listing in q.order_by(m.Listing.rank).all():
        if need.get('instant') is not None and listing.instant_book != need['instant']:
            continue
        if need.get('policy') and listing.cancellation_policy != need['policy']:
            continue
        if need.get('min_guests') and listing.guests < need['min_guests']:
            continue
        if need.get('entire') and listing.room_type != 'Entire home':
            continue
        if need.get('max_min_nights') and listing.min_nights > need['max_min_nights']:
            continue
        if need.get('reviewed') and not listing.review_count:
            continue
        return listing
    raise RuntimeError(f'no fixture listing in {city_slug} for {need}')


def _first_free_window(listing, start: date, nights: int) -> date:
    m = _m()
    blocked = m.booked_nights(listing.id)
    d = start
    for _ in range(200):
        if all((d + timedelta(days=i)) not in blocked for i in range(nights)):
            return d
        d += timedelta(days=1)
    raise RuntimeError(f'no free window for {listing.id}')


def _reserve(user, listing, checkin, nights, status, card, created_at, adults=2, children=0,
             message=None, purpose=None, cancelled_at=None, cancel_reason=None, future=True):
    m = _m()
    if future:
        checkin = _first_free_window(listing, checkin, nights)
    checkout = checkin + timedelta(days=nights)
    q = m.price_quote(listing, checkin, checkout)
    res = m.Reservation(
        code='PENDING', user_id=user.id, listing_id=listing.id, checkin=checkin, checkout=checkout,
        adults=adults, children=children, nights=q['nights'], nightly_price=q['nightly_price'],
        subtotal=q['subtotal'], discount=q['discount'], discount_label=q['discount_label'],
        cleaning_fee=q['cleaning_fee'], service_fee=q['service_fee'], taxes=q['taxes'],
        total=q['total'], cancellation_policy=listing.cancellation_policy, status=status,
        payment_method_id=card.id, payment_label=card.label, message_to_host=message,
        trip_purpose=purpose, created_at=created_at, cancelled_at=cancelled_at,
        cancel_reason=cancel_reason)
    m.db.session.add(res)
    m.db.session.flush()
    res.code = m.reservation_code(res.id)
    if status == 'cancelled':
        res.refund_amount = res.total
    return res


def _thread(user, listing, res, messages, updated_at, unread=False):
    m = _m()
    th = m.MessageThread(user_id=user.id, host_id=listing.host_id, listing_id=listing.id,
                         reservation_id=res.id if res else None, updated_at=updated_at, unread=unread)
    m.db.session.add(th)
    m.db.session.flush()
    for sender, body, sent_at in messages:
        m.db.session.add(m.Message(thread_id=th.id, sender=sender, body=body, sent_at=sent_at))
    return th


def seed_benchmark_users():
    m = _m()
    if m.User.query.filter_by(email='alice.j@test.com').first():
        return
    users = {}
    for spec in BENCHMARK_USERS:
        user = m.User(password_hash=m.BENCHMARK_PASSWORD_HASH, **spec)
        m.db.session.add(user)
        m.db.session.flush()
        users[spec['email']] = user
    cards = {}
    for email, specs in CARDS.items():
        user = users[email]
        for i, (brand, last4, mm, yy, default) in enumerate(specs):
            card = m.PaymentMethod(user_id=user.id, brand=brand, last4=last4, exp_month=mm, exp_year=yy,
                                   holder_name=user.full_name, postal_code=user.postal_code,
                                   country=user.country, is_default=default,
                                   created_at=datetime(2025, 1 + i, 10, 9, 30))
            m.db.session.add(card)
            m.db.session.flush()
            cards.setdefault(email, []).append(card)

    today, now = m.MIRROR_TODAY, m.MIRROR_NOW
    alice, bob, carol = users['alice.j@test.com'], users['bob.c@test.com'], users['carol.d@test.com']
    visa_a = cards['alice.j@test.com'][0]

    # Alice — upcoming Paris trip, a completed (still reviewable) Lisbon stay,
    # a canceled Rome trip, two wishlists and a conversation with her Paris host.
    paris = _pick('Paris--France', instant=True, min_guests=2, entire=True, max_min_nights=4)
    r_paris = _reserve(alice, paris, date(2026, 10, 21), 4, 'confirmed', visa_a,
                       now - timedelta(days=23, hours=3), message='Hi! We are visiting for a design '
                       'conference and would love any café recommendations nearby.', purpose='Work')
    lisbon = _pick('Lisbon--Portugal', min_guests=2, reviewed=True)
    r_lisbon = _reserve(alice, lisbon, today - timedelta(days=12), 5, 'confirmed', visa_a,
                        now - timedelta(days=70), future=False)
    rome = _pick('Rome--Italy', min_guests=2)
    _reserve(alice, rome, date(2026, 8, 14), 3, 'cancelled', cards['alice.j@test.com'][1],
             now - timedelta(days=120), future=False, cancelled_at=now - timedelta(days=96),
             cancel_reason='My travel dates changed')
    _thread(alice, paris, r_paris, [
        ('guest', r_paris.message_to_host, r_paris.created_at),
        ('host', f'Bonjour Alice! Thanks for booking. I will send the door code and my list of '
                 f'favorite cafés a few days before you arrive.', r_paris.created_at + timedelta(hours=2)),
        ('guest', 'Perfect, thank you! Is there a hair dryer in the apartment?',
         r_paris.created_at + timedelta(hours=5)),
        ('host', 'Yes, there is one in the bathroom cabinet. See you in October!',
         r_paris.created_at + timedelta(hours=7)),
    ], r_paris.created_at + timedelta(hours=7), unread=True)
    _thread(alice, lisbon, r_lisbon, [
        ('host', 'Welcome to Lisbon! Let me know if you need anything during your stay.',
         datetime.combine(r_lisbon.checkin, datetime.min.time()) + timedelta(hours=15)),
        ('guest', 'Thanks for a lovely stay — we left the keys in the lockbox.',
         datetime.combine(r_lisbon.checkout, datetime.min.time()) + timedelta(hours=10)),
    ], datetime.combine(r_lisbon.checkout, datetime.min.time()) + timedelta(hours=10))

    wl1 = m.Wishlist(user_id=alice.id, name='Paris getaway', created_at=now - timedelta(days=60))
    wl2 = m.Wishlist(user_id=alice.id, name='Someday', created_at=now - timedelta(days=15))
    m.db.session.add_all([wl1, wl2])
    m.db.session.flush()
    paris_city = m.City.query.filter_by(slug='Paris--France').first()
    paris_saves = (m.Listing.query.filter(m.Listing.city_id == paris_city.id, m.Listing.id != paris.id)
                   .order_by(m.Listing.rank).limit(3).all())
    for i, listing in enumerate(paris_saves):
        m.db.session.add(m.WishlistItem(wishlist_id=wl1.id, listing_id=listing.id,
                                        added_at=now - timedelta(days=59 - i)))
    for i, slug in enumerate(('Tokyo--Japan', 'Asheville--North-Carolina--United-States')):
        city = m.City.query.filter_by(slug=slug).first()
        listing = m.Listing.query.filter_by(city_id=city.id).order_by(m.Listing.rank.desc()).first()
        m.db.session.add(m.WishlistItem(wishlist_id=wl2.id, listing_id=listing.id,
                                        added_at=now - timedelta(days=14 - i)))

    # Bob — two upcoming trips under different policies and a completed stay
    # whose review window has closed.
    amex = cards['bob.c@test.com'][0]
    london = _pick('London--United-Kingdom', policy='Firm', min_guests=2)
    r_london = _reserve(bob, london, date(2026, 10, 16), 4, 'confirmed', amex,
                        now - timedelta(days=41), purpose='Leisure')
    tokyo = _pick('Tokyo--Japan', policy='Flexible', min_guests=2)
    _reserve(bob, tokyo, date(2026, 11, 19), 6, 'confirmed', amex, now - timedelta(days=9),
             adults=2, children=1, purpose='Leisure')
    barcelona = _pick('Barcelona--Spain', min_guests=2, reviewed=True)
    _reserve(bob, barcelona, date(2026, 6, 8), 5, 'confirmed', amex, now - timedelta(days=150),
             future=False)
    _thread(bob, london, r_london, [
        ('host', 'Hi Bob, thanks for your booking! Check-in instructions will arrive 3 days before.',
         r_london.created_at + timedelta(hours=1)),
    ], r_london.created_at + timedelta(hours=1))

    # Carol — a pending request to book, a reviewed past stay, one wishlist.
    visa_c = cards['carol.d@test.com'][0]
    ny = _pick('New-York--New-York--United-States', instant=False, min_guests=2)
    r_ny = _reserve(carol, ny, date(2026, 11, 5), 3, 'pending', visa_c, now - timedelta(hours=20),
                    message='Hello! I am in town for a friend’s wedding and would love to stay at your place.',
                    purpose='Leisure')
    _thread(carol, ny, r_ny, [('guest', r_ny.message_to_host, r_ny.created_at)], r_ny.created_at)
    mexico = _pick('Mexico-City--Mexico', min_guests=1, reviewed=True)
    r_mx = _reserve(carol, mexico, today - timedelta(days=9), 4, 'confirmed', visa_c,
                    now - timedelta(days=45), adults=1, future=False)
    m.db.session.add(m.Review(
        listing_id=mexico.id, user_id=carol.id, reservation_id=r_mx.id, author_name='Carol',
        author_location='Chicago, Illinois', created=r_mx.checkout + timedelta(days=2), rating=5,
        cleanliness=5, accuracy=5, checkin=5, communication=5, location=5, value=4,
        stay_note='Stayed a few nights',
        body=f'Beautiful, bright place and {mexico.host.first_name} was incredibly helpful. '
             f'Walking distance to great tacos and coffee.'))
    wl_c = m.Wishlist(user_id=carol.id, name='Beach trips', created_at=now - timedelta(days=30))
    m.db.session.add(wl_c)
    m.db.session.flush()
    bcn_city = m.City.query.filter_by(slug='Barcelona--Spain').first()
    for i, listing in enumerate(m.Listing.query.filter_by(city_id=bcn_city.id)
                                .order_by(m.Listing.rank).limit(2).all()):
        m.db.session.add(m.WishlistItem(wishlist_id=wl_c.id, listing_id=listing.id,
                                        added_at=now - timedelta(days=29 - i)))
    m.db.session.commit()
