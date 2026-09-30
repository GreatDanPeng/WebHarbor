"""Regression tests for the Airbnb mirror.

Run from the repository root once the site assets are in place:

    python3 -m pytest sites/airbnb/tests -q

The app is imported against a temporary SQLite file (AIRBNB_DB_URI), which
the import seeds exactly like a container boot. Each test that uses the
`client` fixture starts from a pristine copy of that seed.
"""
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
from datetime import date, timedelta

import pytest
from werkzeug.datastructures import MultiDict

SITE = pathlib.Path(__file__).resolve().parents[1]
_TMP = tempfile.mkdtemp(prefix='airbnb-tests-')
DB_PATH = os.path.join(_TMP, 'airbnb.db')
PRISTINE = os.path.join(_TMP, 'pristine.db')
os.environ['AIRBNB_DB_URI'] = f'sqlite:///{DB_PATH}'
sys.path.insert(0, str(SITE))

import app as site  # noqa: E402  (importing the app seeds the temporary database)
import seed_catalog  # noqa: E402

site.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
with site.app.app_context():
    site.db.session.remove()
    site.db.engine.dispose()
shutil.copyfile(DB_PATH, PRISTINE)

PASSWORD = 'TestPass123!'


def _md5(path):
    return hashlib.md5(pathlib.Path(path).read_bytes()).hexdigest()


@pytest.fixture()
def client():
    with site.app.app_context():
        site.db.session.remove()
        site.db.engine.dispose()
    shutil.copyfile(PRISTINE, DB_PATH)
    return site.app.test_client()


def login(client, email='alice.j@test.com', password=PASSWORD):
    resp = client.post('/login', data={'email': email, 'password': password})
    assert resp.status_code == 302, resp.get_data(as_text=True)[:500]
    return client


def free_stay(listing, nights, start=date(2026, 10, 12), adults=2):
    """First bookable stay of `nights` nights on or after `start`."""
    d = start
    for _ in range(300):
        if site.stay_problem(listing, d, d + timedelta(days=nights), adults) is None:
            return d, d + timedelta(days=nights)
        d += timedelta(days=1)
    raise AssertionError(f'no free stay for {listing.id}')


def reservation(email, **filters):
    user = site.User.query.filter_by(email=email).one()
    return site.Reservation.query.filter_by(user_id=user.id, **filters)


def city_reservation(email, slug):
    user = site.User.query.filter_by(email=email).one()
    city = site.City.query.filter_by(slug=slug).one()
    return (site.Reservation.query.join(site.Listing, site.Listing.id == site.Reservation.listing_id)
            .filter(site.Reservation.user_id == user.id, site.Listing.city_id == city.id).one())


# ------------------------------------------------------------------ seed ---

def test_health(client):
    resp = client.get('/_health')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['ok'] is True
    assert body['counts']['listings'] >= 100
    assert body['counts']['users'] == 4


def test_seed_is_idempotent_and_byte_stable():
    before = _md5(PRISTINE)
    shutil.copyfile(PRISTINE, DB_PATH)
    with site.app.app_context():
        site.create_schema()
        site.seed_database()
        site.seed_benchmark_users()
        site.db.session.remove()
        site.db.engine.dispose()
    assert _md5(DB_PATH) == before


def test_catalog_breadth_and_photos():
    with site.app.app_context():
        cities = site.City.query.order_by(site.City.position).all()
        assert len(cities) == 12
        for city in cities:
            assert site.Listing.query.filter_by(city_id=city.id).count() >= 6, city.slug
        for listing in site.Listing.query.all():
            photos = listing.photos
            assert len(photos) >= 5, listing.id
            for photo in photos:
                assert (SITE / 'static' / 'images' / photo.path).is_file(), photo.path
        room_types = {r[0] for r in site.db.session.query(site.Listing.room_type).distinct()}
        assert {'Entire home', 'Private room'} <= room_types
        policies = {r[0] for r in site.db.session.query(site.Listing.cancellation_policy).distinct()}
        assert policies == set(site.POLICIES)


def test_host_privacy():
    with site.app.app_context():
        for host in site.Host.query.all():
            assert host.about is None and host.work is None and host.lives_in is None


def test_host_cards_show_only_captured_stats(client):
    with site.app.app_context():
        hosts = site.Host.query.all()
        assert all(h.first_name != 'Host' for h in hosts)
        compact = [h for h in hosts if h.review_count is None]
        assert compact and all(h.identity_verified is None and h.rating is None for h in compact)
        new_host = next(h for h in hosts if h.hosting_label == 'New Host')
        months = next(h for h in hosts if not h.years_hosting and h.months_hosting)
        assert new_host.tenure_stat is None and new_host.tenure == 'New Host'
        assert months.tenure_stat == (months.months_hosting,
                                      'Month hosting' if months.months_hosting == 1 else 'Months hosting')
        compact_id, new_id = compact[0].id, new_host.id
    page = client.get(f'/users/show/{compact_id}').get_data(as_text=True)
    assert 'Reviews</span>' not in page and 'confirmed information' not in page
    page = client.get(f'/users/show/{new_id}').get_data(as_text=True)
    assert 'Years hosting' not in page and 'Year hosting' not in page


def test_amenity_filter_keys_do_not_match_lookalikes():
    assert seed_catalog.filter_key_for('Hair dryer') is None
    assert seed_catalog.filter_key_for('Pool table') is None
    assert seed_catalog.filter_key_for('Wifi') == 'wifi'
    assert seed_catalog.filter_key_for('Free parking on premises') == 'free_parking'
    assert seed_catalog.filter_key_for('55 inch HDTV with Netflix') == 'tv'


# ----------------------------------------------------------------- pages ---

def test_public_pages_render(client):
    with site.app.app_context():
        listing = site.Listing.query.order_by(site.Listing.city_id, site.Listing.rank).first()
        lid, host_id = listing.id, listing.host_id
    for path in ('/', '/s/Lisbon--Portugal/homes', '/s/homes?query=Paris',
                 '/s/homes?query=Portland&adults=2', f'/rooms/{lid}', f'/rooms/{lid}/photos',
                 f'/rooms/{lid}/amenities', f'/rooms/{lid}/reviews', f'/users/show/{host_id}',
                 '/help', '/help?audience=host', '/help/article/101', '/help/search?q=refund',
                 '/search?q=Tokyo', '/host/homes', '/host/homes?city=Rome--Italy&bedrooms=2&nights=10',
                 '/login', '/register',
                 f'/rooms/{lid}?check_in=2026-11-12&check_out=2026-11-16&adults=2'):
        resp = client.get(path)
        assert resp.status_code == 200, path
    assert client.get('/rooms/1').status_code == 404
    assert client.get('/help/article/9999').status_code == 404


def test_protected_pages_redirect_to_login(client):
    for path in ('/trips', '/wishlists', '/guest/inbox', '/account-settings',
                 '/account-settings/payments/payment-methods'):
        resp = client.get(path)
        assert resp.status_code == 302 and '/login' in resp.headers['Location'], path


@pytest.mark.parametrize('email', ['alice.j@test.com', 'bob.c@test.com', 'carol.d@test.com',
                                   'david.k@test.com'])
def test_account_pages_render(client, email):
    login(client, email)
    for path in ('/trips', '/trips?tab=past', '/trips?tab=cancelled', '/wishlists', '/guest/inbox',
                 '/guest/inbox?filter=unread', '/account-settings', '/account-settings/personal-info',
                 '/account-settings/payments/payment-methods',
                 '/account-settings/login-and-security', '/users/profile'):
        assert client.get(path).status_code == 200, path
    with site.app.app_context():
        codes = [r.code for r in reservation(email).all()]
        wishlist_ids = [w.id for w in site.Wishlist.query.join(site.User).filter(site.User.email == email)]
        thread_ids = [t.id for t in site.MessageThread.query.join(site.User).filter(site.User.email == email)]
    for code in codes:
        assert client.get(f'/trips/v1/{code}').status_code == 200
        assert client.get(f'/trips/v1/{code}/receipt').status_code == 200
    for wid in wishlist_ids:
        assert client.get(f'/wishlists/{wid}').status_code == 200
        assert client.get(f'/wishlists/{wid}/settings').status_code == 200
    for tid in thread_ids:
        assert client.get(f'/guest/messages/{tid}').status_code == 200


def test_other_users_trips_are_hidden(client):
    with site.app.app_context():
        code = city_reservation('bob.c@test.com', 'London--United-Kingdom').code
    login(client)
    assert client.get(f'/trips/v1/{code}').status_code == 404


# ---------------------------------------------------------------- search ---

def test_portland_disambiguation():
    with site.app.app_context():
        slugs = lambda q: sorted(site.db.session.get(site.City, c).slug for c in site.resolve_location(q)[0])  # noqa: E731
        assert slugs('Portland') == ['Portland--Maine--United-States', 'Portland--Oregon--United-States']
        assert slugs('Portland, Oregon') == ['Portland--Oregon--United-States']
        assert slugs('portland maine') == ['Portland--Maine--United-States']
        assert slugs('Lisbon, Portugal') == ['Lisbon--Portugal']
        assert slugs('Mexico City') == ['Mexico-City--Mexico']


def test_search_filters_apply():
    with site.app.app_context():
        base = site.search_state(MultiDict({'query': 'Lisbon'}))
        _, everything = site.run_search(base)
        assert everything and all(l.city.slug == 'Lisbon--Portugal' for l in everything)

        state = site.search_state(MultiDict({'query': 'Lisbon', 'ib': 'true',
                                             'flexible_cancellation': 'true'}))
        _, rows = site.run_search(state)
        assert all(l.instant_book and l.cancellation_policy in ('Flexible', 'Moderate') for l in rows)
        assert len(rows) < len(everything)

        prices = sorted(l.nightly_price for l in everything)
        cap = prices[len(prices) // 2]
        _, cheap = site.run_search(site.search_state(MultiDict({'query': 'Lisbon', 'price_max': str(cap)})))
        assert cheap and all(l.nightly_price <= cap for l in cheap)

        _, wifi = site.run_search(site.search_state(MultiDict([('query', 'Lisbon'), ('amenities[]', 'wifi')])))
        assert all('wifi' in site.listing_amenity_keys(l.id) for l in wifi)

        _, entire = site.run_search(site.search_state(MultiDict([('query', 'Paris'),
                                                                 ('room_types[]', 'Entire home')])))
        assert entire and all(l.room_type == 'Entire home' for l in entire)


def test_search_dates_exclude_unavailable_listings():
    with site.app.app_context():
        state = site.search_state(MultiDict({'query': 'Rome', 'checkin': '2026-11-12',
                                             'checkout': '2026-11-16', 'adults': '2'}))
        _, rows = site.run_search(state)
        for listing in rows:
            assert site.stay_problem(listing, date(2026, 11, 12), date(2026, 11, 16), 2) is None


def test_help_search_is_scored_and_indexes_list_items():
    with site.app.app_context():
        assert site.help_search_results('cancel refund')[0].id == 102
        assert site.help_search_results('service fee')[0].id == 104
        # "agents" only appears inside a bullet list of the AirCover article
        assert [a.id for a in site.help_search_results('safety agents')][:1] == [103]
        assert site.help_search_results('zzzz') == []


def test_site_search(client):
    resp = client.get('/search?q=Barcelona')
    assert resp.status_code == 200
    with site.app.app_context():
        city = site.City.query.filter_by(slug='Barcelona--Spain').one()
        first = site.Listing.query.filter_by(city_id=city.id).order_by(site.Listing.rank).first()
        name = first.name
    assert name.replace('&', '&amp;').replace("'", '&#39;') in resp.get_data(as_text=True)


# --------------------------------------------------------------- pricing ---

def test_price_quote_math():
    with site.app.app_context():
        listing = (site.Listing.query.filter(site.Listing.weekly_discount > 0)
                   .order_by(site.Listing.id).first())
        q = site.price_quote(listing, date(2026, 11, 2), date(2026, 11, 9))
        assert q['nights'] == 7
        assert q['subtotal'] == listing.nightly_price * 7
        assert q['discount'] == site.money(q['subtotal'] * listing.weekly_discount / 100)
        base = q['subtotal'] - q['discount'] + listing.cleaning_fee
        assert q['service_fee'] == site.money(base * 0.142)
        assert q['taxes'] == site.money(base * listing.city.tax_rate)
        assert q['total'] == base + q['service_fee'] + q['taxes']
        short = site.price_quote(listing, date(2026, 11, 2), date(2026, 11, 8))
        assert short['discount'] == 0


def test_host_earnings_estimate_uses_median(client):
    with site.app.app_context():
        city = site.City.query.filter_by(slug='Paris--France').one()
        prices = sorted(l.nightly_price for l in site.Listing.query.filter_by(
            city_id=city.id, room_type='Entire home') if max(l.bedrooms, 1) == 1)
    assert prices
    mid = len(prices) // 2
    nightly = prices[mid] if len(prices) % 2 else site.money((prices[mid - 1] + prices[mid]) / 2)
    resp = client.get('/host/homes?city=Paris--France&bedrooms=1&nights=10')
    assert site.fmt_money(nightly * 10) in resp.get_data(as_text=True)


# --------------------------------------------------------------- booking ---

def test_instant_book_flow(client):
    login(client)
    with site.app.app_context():
        listing = (site.Listing.query.filter_by(instant_book=True)
                   .filter(site.Listing.guests >= 2, site.Listing.min_nights <= 3)
                   .order_by(site.Listing.city_id, site.Listing.rank).first())
        checkin, checkout = free_stay(listing, 3)
        expected = site.price_quote(listing, checkin, checkout)['total']
        card = (site.PaymentMethod.query.join(site.User)
                .filter(site.User.email == 'alice.j@test.com', site.PaymentMethod.last4 == '5454').one())
        lid, card_id = listing.id, card.id
    resp = client.post(f'/book/stays/{lid}', data={
        'checkin': checkin.isoformat(), 'checkout': checkout.isoformat(), 'numberOfAdults': '2',
        'payment_method': str(card_id)})
    assert resp.status_code == 302 and '/trips/v1/HM' in resp.headers['Location']
    with site.app.app_context():
        res = reservation('alice.j@test.com', listing_id=lid, checkin=checkin).one()
        assert res.status == 'confirmed' and res.total == expected and res.payment_label.endswith('5454')
    # The same nights are no longer available.
    again = client.post(f'/book/stays/{lid}', data={
        'checkin': checkin.isoformat(), 'checkout': checkout.isoformat(), 'numberOfAdults': '2',
        'payment_method': str(card_id)})
    assert again.status_code == 302 and f'/rooms/{lid}' in again.headers['Location']


def test_request_to_book_requires_message(client):
    login(client, 'david.k@test.com')
    with site.app.app_context():
        listing = (site.Listing.query.filter_by(instant_book=False)
                   .filter(site.Listing.guests >= 2, site.Listing.min_nights <= 3)
                   .order_by(site.Listing.city_id, site.Listing.rank).first())
        checkin, checkout = free_stay(listing, 3)
        card_id = site.PaymentMethod.query.join(site.User).filter(site.User.email == 'david.k@test.com').one().id
        lid = listing.id
    form = {'checkin': checkin.isoformat(), 'checkout': checkout.isoformat(), 'numberOfAdults': '2',
            'payment_method': str(card_id)}
    resp = client.post(f'/book/stays/{lid}', data=form)
    assert resp.status_code == 200
    assert 'Write a message to the host' in resp.get_data(as_text=True)
    with site.app.app_context():
        assert reservation('david.k@test.com', listing_id=lid).count() == 0
    resp = client.post(f'/book/stays/{lid}', data=dict(form, message='Hi! Two of us visiting for a week.'))
    assert resp.status_code == 302
    with site.app.app_context():
        res = reservation('david.k@test.com', listing_id=lid).one()
        assert res.status == 'pending'
        thread = site.MessageThread.query.filter_by(user_id=res.user_id, listing_id=lid).one()
        assert thread.messages[-1].body.startswith('Hi! Two of us')


def test_booking_with_new_card_validates_luhn(client):
    login(client, 'bob.c@test.com')
    with site.app.app_context():
        listing = (site.Listing.query.filter_by(instant_book=True)
                   .filter(site.Listing.guests >= 2, site.Listing.min_nights <= 2)
                   .order_by(site.Listing.city_id.desc(), site.Listing.rank).first())
        checkin, checkout = free_stay(listing, 2)
        lid = listing.id
    form = {'checkin': checkin.isoformat(), 'checkout': checkout.isoformat(), 'numberOfAdults': '2',
            'payment_method': 'new', 'card_number': '4242 4242 4242 4241', 'expiration': '12/29',
            'cvv': '123', 'postal_code': '98102'}
    resp = client.post(f'/book/stays/{lid}', data=form)
    assert resp.status_code == 200 and 'Check your card number' in resp.get_data(as_text=True)
    resp = client.post(f'/book/stays/{lid}', data=dict(form, card_number='5555 5555 5555 4444'))
    assert resp.status_code == 302
    with site.app.app_context():
        assert reservation('bob.c@test.com', listing_id=lid).one().payment_label == 'Mastercard •••• 4444'


# ----------------------------------------------------------- cancellation ---

def test_firm_policy_partial_refund(client):
    with site.app.app_context():
        res = city_reservation('bob.c@test.com', 'London--United-Kingdom')
        assert res.cancellation_policy == 'Firm'
        days_before = (res.checkin - site.MIRROR_TODAY).days
        assert 7 <= days_before < 30
        expected = site.money((res.subtotal - res.discount) / 2) + res.cleaning_fee
        assert site.refund_quote(res)['refund'] == expected
        code = res.code
    login(client, 'bob.c@test.com')
    page = client.get(f'/trips/v1/{code}/cancel').get_data(as_text=True)
    assert site.fmt_money(expected) in page
    assert client.post(f'/trips/v1/{code}/cancel', data={}).status_code == 302
    resp = client.post(f'/trips/v1/{code}/cancel', data={'reason': 'My travel dates changed'})
    assert resp.status_code == 302
    with site.app.app_context():
        res = site.Reservation.query.filter_by(code=code).one()
        assert res.status == 'cancelled' and res.refund_amount == expected


def test_flexible_and_pending_cancellations_refund_in_full(client):
    with site.app.app_context():
        tokyo = city_reservation('bob.c@test.com', 'Tokyo--Japan')
        assert tokyo.cancellation_policy == 'Flexible'
        assert site.refund_quote(tokyo)['refund'] == tokyo.total
        pending = reservation('carol.d@test.com', status='pending').one()
        assert site.refund_quote(pending)['refund'] == pending.total
        code = pending.code
    login(client, 'carol.d@test.com')
    client.post(f'/trips/v1/{code}/cancel', data={'reason': 'Other'})
    with site.app.app_context():
        res = site.Reservation.query.filter_by(code=code).one()
        assert res.status == 'cancelled' and res.refund_amount == res.total


def test_refund_rules_by_days_before_checkin():
    def fake(policy, days, created_hours_ago=24 * 30):
        return site.Reservation(
            status='confirmed', cancellation_policy=policy, nightly_price=100, nights=4, subtotal=400,
            discount=0, cleaning_fee=60, service_fee=65, taxes=20, total=545,
            checkin=site.MIRROR_TODAY + timedelta(days=days),
            created_at=site.mirror_now() - timedelta(hours=created_hours_ago))
    assert site.refund_quote(fake('Flexible', 1))['refund'] == 545
    assert site.refund_quote(fake('Flexible', 0))['refund'] == 300 + 60
    assert site.refund_quote(fake('Moderate', 5))['refund'] == 545
    assert site.refund_quote(fake('Moderate', 4))['refund'] == 150 + 60
    assert site.refund_quote(fake('Firm', 30))['refund'] == 545
    assert site.refund_quote(fake('Firm', 29))['refund'] == 200 + 60
    assert site.refund_quote(fake('Firm', 6))['refund'] == 0
    assert site.refund_quote(fake('Strict', 20, created_hours_ago=10))['refund'] == 545
    assert site.refund_quote(fake('Strict', 20))['refund'] == 200 + 60
    assert site.refund_quote(fake('Strict', 3))['refund'] == 0


def test_past_trips_cannot_be_cancelled(client):
    with site.app.app_context():
        code = city_reservation('bob.c@test.com', 'Barcelona--Spain').code
    login(client, 'bob.c@test.com')
    client.post(f'/trips/v1/{code}/cancel', data={'reason': 'Other'})
    with site.app.app_context():
        assert site.Reservation.query.filter_by(code=code).one().status == 'confirmed'


# ---------------------------------------------------------------- reviews ---

def test_review_window(client):
    with site.app.app_context():
        lisbon = city_reservation('alice.j@test.com', 'Lisbon--Portugal')
        assert lisbon.can_review
        code, lid = lisbon.code, lisbon.listing_id
        before = site.Review.query.filter_by(listing_id=lid).count()
        barcelona = city_reservation('bob.c@test.com', 'Barcelona--Spain')
        assert not barcelona.can_review
        bcn_code = barcelona.code
    login(client)
    form = {'rating': '4', 'body': 'Lovely flat with a view of the river.',
            **{f: '4' for f in site.REVIEW_FIELDS}}
    assert client.post(f'/trips/v1/{code}/review', data=dict(form, cleanliness='0')).status_code == 200
    assert client.post(f'/trips/v1/{code}/review', data=form).status_code == 302
    with site.app.app_context():
        assert site.Review.query.filter_by(listing_id=lid).count() == before + 1
    client.get('/logout')
    login(client, 'bob.c@test.com')
    resp = client.get(f'/trips/v1/{bcn_code}/review')
    assert resp.status_code == 302 and resp.headers['Location'].endswith(f'/trips/v1/{bcn_code}')


# -------------------------------------------------------------- wishlists ---

def test_wishlist_lifecycle(client):
    login(client, 'david.k@test.com')
    with site.app.app_context():
        lid = site.Listing.query.order_by(site.Listing.id).first().id
    assert client.post('/wishlists/save', data={'listing_id': lid, 'new_name': 'x' * 51}).status_code == 302
    with site.app.app_context():
        assert site.Wishlist.query.join(site.User).filter(site.User.email == 'david.k@test.com').count() == 0
    client.post('/wishlists/save', data={'listing_id': lid, 'new_name': 'Winter ideas'})
    with site.app.app_context():
        wl = site.Wishlist.query.filter_by(name='Winter ideas').one()
        wid = wl.id
        assert [i.listing_id for i in wl.items] == [lid]
    client.post(f'/wishlists/{wid}/note', data={'listing_id': lid, 'note': 'Near the station'})
    client.post(f'/wishlists/{wid}/settings', data={'name': 'Winter 2026'})
    with site.app.app_context():
        wl = site.db.session.get(site.Wishlist, wid)
        assert wl.name == 'Winter 2026' and wl.items[0].note == 'Near the station'
    client.post(f'/wishlists/{wid}/settings', data={'action': 'delete'})
    with site.app.app_context():
        assert site.db.session.get(site.Wishlist, wid) is None


# --------------------------------------------------------------- payments ---

def test_card_used_by_upcoming_trip_cannot_be_removed(client):
    login(client)
    with site.app.app_context():
        cards = {c.last4: c.id for c in site.PaymentMethod.query.join(site.User)
                 .filter(site.User.email == 'alice.j@test.com')}
    client.post('/account-settings/payments/payment-methods', data={'action': 'remove', 'card_id': cards['4242']})
    client.post('/account-settings/payments/payment-methods', data={'action': 'remove', 'card_id': cards['5454']})
    with site.app.app_context():
        assert site.db.session.get(site.PaymentMethod, cards['4242']) is not None
        assert site.db.session.get(site.PaymentMethod, cards['5454']) is None
    client.post('/account-settings/payments/payment-methods', data={
        'action': 'add', 'card_number': '4000 0566 5566 5556', 'expiration': '04/30', 'cvv': '321',
        'postal_code': '94117', 'make_default': 'on'})
    with site.app.app_context():
        default = (site.PaymentMethod.query.join(site.User)
                   .filter(site.User.email == 'alice.j@test.com', site.PaymentMethod.is_default.is_(True)).one())
        assert default.last4 == '5556'


# ------------------------------------------------------------------ auth ---

def test_login_rejects_bad_password(client):
    resp = client.post('/login', data={'email': 'alice.j@test.com', 'password': 'wrong-password'})
    assert resp.status_code == 200 and 'Invalid email or password' in resp.get_data(as_text=True)


def test_password_change_rules(client):
    login(client)
    url = '/account-settings/login-and-security'
    client.post(url, data={'current_password': PASSWORD, 'new_password': 'short',
                           'confirm_password': 'short'})
    client.post(url, data={'current_password': PASSWORD, 'new_password': 'NewPass2026!',
                           'confirm_password': 'NewPass2026!'})
    client.get('/logout')
    assert client.post('/login', data={'email': 'alice.j@test.com', 'password': PASSWORD}).status_code == 200
    login(client, password='NewPass2026!')


def test_register(client):
    form = {'first_name': 'Eve', 'last_name': 'Moss', 'email': 'eve.m@test.com',
            'password': 'Password123', 'confirm_password': 'Password123'}
    assert client.post('/register', data=dict(form, email='alice.j@test.com')).status_code == 400
    assert client.post('/register', data=form).status_code == 302
    assert client.get('/trips').status_code == 200


def test_personal_info_update(client):
    login(client, 'carol.d@test.com')
    resp = client.post('/account-settings/personal-info', data={
        'first_name': 'Carol', 'last_name': 'Davis', 'preferred_name': 'Caz',
        'email': 'carol.d@test.com', 'phone': '+1 (312) 555-0100', 'city': 'Chicago'})
    assert resp.status_code == 302
    with site.app.app_context():
        user = site.User.query.filter_by(email='carol.d@test.com').one()
        assert user.display_name == 'Caz' and user.phone == '+1 (312) 555-0100'
    resp = client.post('/account-settings/personal-info', data={
        'first_name': 'Carol', 'last_name': 'Davis', 'email': 'bob.c@test.com'})
    assert resp.status_code == 400


# ----------------------------------------------------------------- tasks ---

def test_tasks_file_uses_basic_keys_only():
    path = SITE / 'tasks.jsonl'
    if not path.exists():
        pytest.skip('tasks.jsonl not written yet')
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    assert 15 <= len(rows) <= 20
    for row in rows:
        assert set(row) == {'web_name', 'id', 'ques', 'web', 'upstream_url'}
        assert row['web'] == 'http://localhost:40099/'


# Every data-dependent task must have exactly one correct answer on the
# seeded catalog: a non-empty candidate set and no tie for the winner.

def _results(**params):
    args = MultiDict()
    for key, value in params.items():
        for v in (value if isinstance(value, list) else [value]):
            args.add(key, v)
    return site.run_search(site.search_state(args))[1]


def _unique_best(rows, key):
    assert rows
    ranked = sorted(rows, key=key)
    assert len(ranked) == 1 or key(ranked[0]) != key(ranked[1])
    return ranked[0]


def _total_before_taxes(checkin, checkout):
    return lambda l: site.price_quote(l, checkin, checkout)['total_before_taxes']


def test_task_candidates_are_unambiguous():
    with site.app.app_context():
        # Portland, Oregon: best rating among well-reviewed available stays.
        rows = _results(query='Portland, Oregon', checkin='2026-12-04', checkout='2026-12-07', adults='2')
        assert rows and all(l.city.slug == 'Portland--Oregon--United-States' for l in rows)
        best = _unique_best([l for l in rows if l.review_count >= 100], lambda l: -l.rating)
        assert best.r_cleanliness is not None

        # Tokyo with Instant Book + Self check-in under $200 a night; the cheapest nightly
        # price is not the cheapest total once cleaning fees are added.
        stay = (date(2026, 11, 12), date(2026, 11, 16))
        rows = _results(query='Tokyo', checkin=stay[0].isoformat(), checkout=stay[1].isoformat(),
                        adults='2', ib='true', self_check_in='true', price_max='200')
        assert len(rows) >= 3
        best = _unique_best(rows, _total_before_taxes(*stay))
        assert best != min(rows, key=lambda l: l.nightly_price)

        # First results without dates.
        for query, slug in (('Asheville, North Carolina', 'Asheville--North-Carolina--United-States'),
                            ('New York', 'New-York--New-York--United-States'),
                            ('Mexico City', 'Mexico-City--Mexico')):
            rows = _results(query=query)
            assert len(rows) >= 2 and all(l.city.slug == slug for l in rows[:2]), query
        # New York's first listing has several reviews at its lowest star rating, on distinct days.
        ny_reviews = site.Review.query.filter_by(listing_id=_results(query='New York')[0].id).all()
        lowest = min(r.rating for r in ny_reviews)
        low_days = [r.created for r in ny_reviews if r.rating == lowest]
        assert lowest < 5 and len(low_days) >= 2 and len(set(low_days)) == len(low_days)
        assert _results(query='Mexico City')[1].host.response_rate is not None

        # Earnings estimate: 2-bedroom entire homes exist in Lisbon.
        lisbon = site.City.query.filter_by(slug='Lisbon--Portugal').one()
        assert any(l.bedrooms == 2 for l in site.Listing.query.filter_by(
            city_id=lisbon.id, room_type='Entire home'))

        # Rome: cheapest Instant Book entire home for Nov 3-6.
        stay = (date(2026, 11, 3), date(2026, 11, 6))
        rows = _results(query='Rome', checkin=stay[0].isoformat(), checkout=stay[1].isoformat(),
                        adults='2', ib='true', **{'room_types[]': 'Entire home'})
        _unique_best(rows, _total_before_taxes(*stay))

        # Asheville, Jan 27-31 with a pet: the top-rated pet-friendly listing is booked, so the
        # answer is the best open one, a request to book behind a lower-rated first result.
        stay = (date(2027, 1, 27), date(2027, 1, 31))
        avl = site.City.query.filter_by(slug='Asheville--North-Carolina--United-States').one()
        pet_ok = [l for l in site.Listing.query.filter_by(city_id=avl.id, pets_allowed=True)
                  if l.guests >= 2 and l.review_count]
        top = _unique_best(pet_ok, lambda l: -l.rating)
        assert site.stay_problem(top, *stay, 2, pets=1) is not None
        rows = _results(query='Asheville, North Carolina', checkin=stay[0].isoformat(),
                        checkout=stay[1].isoformat(), adults='2', pets='1')
        assert len(rows) >= 3 and top not in rows
        best = _unique_best(rows, lambda l: -l.rating)
        assert best != rows[0] and not best.instant_book

        # Mexico City: two Guest favorites with the most reviews; a non-favorite outranks them.
        mx = site.City.query.filter_by(slug='Mexico-City--Mexico').one()
        mx_listings = site.Listing.query.filter_by(city_id=mx.id).all()
        favs = sorted((l.review_count for l in mx_listings if l.is_guest_favorite), reverse=True)
        assert len(favs) >= 3 and favs[1] != favs[2]
        assert any(not l.is_guest_favorite and l.review_count > favs[0] for l in mx_listings)

        # Alice's 'Paris getaway' wishlist for Dec 15-19: the cheapest saved home is booked.
        stay = (date(2026, 12, 15), date(2026, 12, 19))
        wl = (site.Wishlist.query.join(site.User)
              .filter(site.User.email == 'alice.j@test.com', site.Wishlist.name == 'Paris getaway').one())
        saved = [site.db.session.get(site.Listing, i.listing_id)
                 for i in site.WishlistItem.query.filter_by(wishlist_id=wl.id)]
        free = [l for l in saved if site.stay_problem(l, *stay, 2) is None]
        assert len(free) >= 2
        best = _unique_best(free, lambda l: site.price_quote(l, *stay)['total'])
        cheapest = _unique_best(saved, lambda l: site.price_quote(l, *stay)['total'])
        assert cheapest != best and cheapest not in free

        # Porto: waterfront entire home with free cancellation, Dec 11-14; a cheaper
        # free-cancellation home without waterfront is the near miss.
        stay = (date(2026, 12, 11), date(2026, 12, 14))
        common = dict(query='Porto, Portugal', checkin=stay[0].isoformat(), checkout=stay[1].isoformat(),
                      adults='2', flexible_cancellation='true')
        rows = _results(**common, **{'room_types[]': 'Entire home', 'amenities[]': 'waterfront'})
        best = _unique_best(rows, _total_before_taxes(*stay))
        looser = _results(**common, **{'room_types[]': 'Entire home'})
        assert min(_total_before_taxes(*stay)(l) for l in looser) < _total_before_taxes(*stay)(best)

        # The two Portlands for Mar 5-8, 2027.
        stay = (date(2027, 3, 5), date(2027, 3, 8))
        totals = []
        for query in ('Portland, Oregon', 'Portland, Maine'):
            rows = _results(query=query, checkin=stay[0].isoformat(), checkout=stay[1].isoformat(),
                            adults='2', **{'room_types[]': 'Entire home'})
            best = _unique_best(rows, _total_before_taxes(*stay))
            totals.append(site.price_quote(best, *stay)['total'])
        assert totals[0] != totals[1]
