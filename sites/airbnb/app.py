#!/usr/bin/env python3
"""Airbnb mirror — Flask application.

Mirrors https://www.airbnb.com/ (en-US, USD): the homepage listing rows, the
Where / When / Who search bar, /s/<place>/homes results with the filters
panel, /rooms/<id> listing pages (photo tour, amenities, sleeping
arrangements, availability calendar, review categories, host card, house
rules, cancellation policy and the reservation card with the full price
breakdown), Confirm and pay, Trips (itinerary, receipt, cancellation with
policy-driven refunds, reviews of past stays), Wishlists, the guest inbox,
Account settings (personal info, payment methods, login & security), host
profiles, the Help Center and site-wide scored search.

Listings, hosts, photos, ratings and amenities come from the tracked
source_data_*.json snapshots captured from www.airbnb.com on 2026-09-28; the
SQLite seed is materialized deterministically at image build time.
"""
import hashlib
import json
import os
import random
import re
import time
import unicodedata
from calendar import monthrange
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache
from urllib.parse import quote, urlencode

from flask import (Flask, abort, flash, jsonify, redirect, render_template,
                   request, url_for)
from flask_bcrypt import Bcrypt
from flask_login import (LoginManager, UserMixin, current_user,
                         login_required, login_user, logout_user)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, instance_path=os.path.join(BASE_DIR, 'instance'))
app.config["SECRET_KEY"] = os.environ.get("AIRBNB_SECRET_KEY") or "webharbor-airbnb-dev-key"
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'AIRBNB_DB_URI',
    f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'airbnb.db')}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_TIME_LIMIT'] = None

os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Log in to continue.'
csrf = CSRFProtect(app)

# The mirror is a snapshot of the upstream site taken on 2026-09-28. Every
# date-dependent rule (calendar, trip status, refund windows) reads this clock.
MIRROR_TODAY = date(2026, 9, 28)
MIRROR_NOW = datetime(2026, 9, 28, 12, 0, 0)
# check-in / checkout of the upstream search the listings were captured from
SNAPSHOT_STAY = (date(2026, 11, 12), date(2026, 11, 16))
PROCESS_START = time.monotonic()
# bcrypt hash of 'TestPass123!' (frozen so the SQLite seed is byte-reproducible
# on every build; PYTHONHASHSEED=0 keeps the rest deterministic)
BENCHMARK_PASSWORD_HASH = (
    '$2b$12$qSds4Mr9Wo7VwPWLhompEer88SuxxXFDp31P9etY6v7nfRctNO7B.')
SERVICE_FEE_RATE = Decimal('0.142')
CALENDAR_HORIZON_DAYS = 365
MAX_NIGHTS = 90
RESULTS_PER_PAGE = 18
REVIEWS_PER_PAGE = 10
POLICIES = ('Flexible', 'Moderate', 'Firm', 'Strict')
STOP_WORDS = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and',
              'or', 'is', 'it', 'by', 'with', 'near', 'place', 'places',
              'stay', 'stays', 'homes', 'home', 'airbnb', 'rentals', 'rental'}


def _load_source(name):
    with open(os.path.join(BASE_DIR, name), encoding='utf-8') as handle:
        return json.load(handle)


def money(value) -> int:
    """Round a dollar amount half-up to a whole dollar (Airbnb shows USD
    breakdowns in whole dollars)."""
    return int(Decimal(str(value)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def mirror_now() -> datetime:
    """Mirror wall clock: the snapshot noon plus time since the process
    started, so rows created at runtime keep their relative order."""
    return MIRROR_NOW + timedelta(seconds=time.monotonic() - PROCESS_START)


def fold(text: str) -> str:
    text = unicodedata.normalize('NFKD', text or '')
    return ''.join(c for c in text if not unicodedata.combining(c)).lower()


def tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r'[a-z0-9]+', fold(text))
            if t not in STOP_WORDS]


# ------------------------------------------------------------------ models --

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(60), nullable=False)
    last_name = db.Column(db.String(60), nullable=False)
    preferred_name = db.Column(db.String(60))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    phone = db.Column(db.String(40))
    street = db.Column(db.String(120))
    apt = db.Column(db.String(40))
    city = db.Column(db.String(80))
    state = db.Column(db.String(60))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(60))
    emergency_contact = db.Column(db.String(160))
    about = db.Column(db.Text)
    lives_in = db.Column(db.String(120))
    work = db.Column(db.String(120))
    languages = db.Column(db.String(160))
    joined = db.Column(db.Date, nullable=False)
    identity_verified = db.Column(db.Boolean, default=False)

    @property
    def display_name(self):
        return self.preferred_name or self.first_name

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def initial(self):
        return (self.display_name or '?')[:1].upper()

    @property
    def address_line(self):
        parts = [self.street, self.apt, self.city, self.state, self.postal_code, self.country]
        return ', '.join(p for p in parts if p)


class Host(db.Model):
    __tablename__ = 'hosts'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    is_superhost = db.Column(db.Boolean, default=False)
    years_hosting = db.Column(db.Integer, default=0)
    months_hosting = db.Column(db.Integer)          # set for hosts with under a year
    hosting_label = db.Column(db.String(40))        # upstream wording, e.g. '11 years hosting'
    rating = db.Column(db.Float)
    review_count = db.Column(db.Integer)            # None when the capture had no host stats
    response_rate = db.Column(db.Integer)          # percent
    response_time = db.Column(db.String(40))
    languages = db.Column(db.String(200))
    lives_in = db.Column(db.String(120))
    work = db.Column(db.String(120))
    about = db.Column(db.Text)
    identity_verified = db.Column(db.Boolean)

    @property
    def initial(self):
        return self.first_name[:1].upper()

    @property
    def tenure_stat(self):
        """(number, caption) for the host card's tenure stat; None for a brand-new host."""
        if self.years_hosting:
            return self.years_hosting, 'Year hosting' if self.years_hosting == 1 else 'Years hosting'
        if self.months_hosting:
            return self.months_hosting, 'Month hosting' if self.months_hosting == 1 else 'Months hosting'
        return None

    @property
    def tenure(self):
        if self.hosting_label:
            return self.hosting_label
        stat = self.tenure_stat
        return f'{stat[0]} {stat[1].lower()}' if stat else 'New Host'

    @property
    def avatar_hue(self):
        return int(hashlib.md5(f'host-{self.id}'.encode()).hexdigest()[:4], 16) % 360


class City(db.Model):
    __tablename__ = 'cities'
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), unique=True, nullable=False)   # Lisbon--Portugal
    name = db.Column(db.String(80), nullable=False)
    region = db.Column(db.String(80))
    country = db.Column(db.String(80), nullable=False)
    tax_rate = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    position = db.Column(db.Integer, nullable=False)

    @property
    def label(self):
        return f'{self.name}, {self.country}'


class Listing(db.Model):
    __tablename__ = 'listings'
    id = db.Column(db.Integer, primary_key=True)            # upstream room id
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)
    host_id = db.Column(db.Integer, db.ForeignKey('hosts.id'), nullable=False)
    rank = db.Column(db.Integer, nullable=False)            # upstream result order
    name = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(160), nullable=False)       # "Apartment in Lisbon"
    headline = db.Column(db.String(200), nullable=False)    # "Entire rental unit in Lisbon, Portugal"
    room_type = db.Column(db.String(40), nullable=False)    # Entire home / Private room / ...
    property_type = db.Column(db.String(60), nullable=False)
    property_group = db.Column(db.String(40), nullable=False)  # House / Apartment / Guesthouse / Hotel
    neighborhood = db.Column(db.String(120))
    guests = db.Column(db.Integer, nullable=False)
    bedrooms = db.Column(db.Integer, nullable=False)
    beds = db.Column(db.Integer, nullable=False)
    baths = db.Column(db.Float, nullable=False)
    baths_label = db.Column(db.String(40), nullable=False)
    is_studio = db.Column(db.Boolean, default=False)
    nightly_price = db.Column(db.Integer, nullable=False)
    cleaning_fee = db.Column(db.Integer, nullable=False)
    weekly_discount = db.Column(db.Integer, default=0)      # percent
    monthly_discount = db.Column(db.Integer, default=0)     # percent
    min_nights = db.Column(db.Integer, default=1)
    rating = db.Column(db.Float)
    review_count = db.Column(db.Integer, default=0)
    r_cleanliness = db.Column(db.Float)
    r_accuracy = db.Column(db.Float)
    r_checkin = db.Column(db.Float)
    r_communication = db.Column(db.Float)
    r_location = db.Column(db.Float)
    r_value = db.Column(db.Float)
    is_guest_favorite = db.Column(db.Boolean, default=False)
    instant_book = db.Column(db.Boolean, default=False)
    self_checkin = db.Column(db.Boolean, default=False)
    pets_allowed = db.Column(db.Boolean, default=False)
    smoking_allowed = db.Column(db.Boolean, default=False)
    events_allowed = db.Column(db.Boolean, default=False)
    quiet_hours = db.Column(db.String(60))
    cancellation_policy = db.Column(db.String(20), nullable=False)
    checkin_time = db.Column(db.String(40), nullable=False)
    checkout_time = db.Column(db.String(40), nullable=False)
    description = db.Column(db.Text, nullable=False)
    space = db.Column(db.Text)
    location_blurb = db.Column(db.Text)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    source_url = db.Column(db.String(200), nullable=False)

    city = db.relationship('City', backref='listings')
    host = db.relationship('Host', backref='listings')

    @property
    def photos(self):
        return (ListingPhoto.query.filter_by(listing_id=self.id)
                .order_by(ListingPhoto.position).all())

    @property
    def cover(self):
        return (ListingPhoto.query.filter_by(listing_id=self.id)
                .order_by(ListingPhoto.position).first())

    @property
    def overview(self):
        bits = [f"{self.guests} guest{'s' if self.guests != 1 else ''}"]
        if self.is_studio:
            bits.append('Studio')
        else:
            bits.append(f"{self.bedrooms} bedroom{'s' if self.bedrooms != 1 else ''}")
        bits.append(f"{self.beds} bed{'s' if self.beds != 1 else ''}")
        bits.append(self.baths_label)
        return bits

    @property
    def rating_label(self):
        if not self.review_count or self.rating is None:
            return 'New'
        text = f'{self.rating:.2f}'
        return text[:-1] if text.endswith('0') else text

    @property
    def category_ratings(self):
        return [('Cleanliness', self.r_cleanliness), ('Accuracy', self.r_accuracy),
                ('Check-in', self.r_checkin), ('Communication', self.r_communication),
                ('Location', self.r_location), ('Value', self.r_value)]


class ListingPhoto(db.Model):
    __tablename__ = 'listing_photos'
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    path = db.Column(db.String(200), nullable=False)
    caption = db.Column(db.String(200))


class Amenity(db.Model):
    __tablename__ = 'amenities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    category = db.Column(db.String(80), nullable=False)
    filter_key = db.Column(db.String(40))   # set for amenities offered as search filters


class ListingAmenity(db.Model):
    __tablename__ = 'listing_amenities'
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    amenity_id = db.Column(db.Integer, db.ForeignKey('amenities.id'), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    detail = db.Column(db.String(200))
    available = db.Column(db.Boolean, default=True)

    amenity = db.relationship('Amenity')


class Highlight(db.Model):
    __tablename__ = 'listing_highlights'
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(120), nullable=False)
    subtitle = db.Column(db.String(240))


class SleepingArrangement(db.Model):
    __tablename__ = 'sleeping_arrangements'
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    room = db.Column(db.String(80), nullable=False)
    beds = db.Column(db.String(160), nullable=False)


class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.id'))
    author_name = db.Column(db.String(80), nullable=False)
    author_location = db.Column(db.String(120))
    created = db.Column(db.Date, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    cleanliness = db.Column(db.Integer)
    accuracy = db.Column(db.Integer)
    checkin = db.Column(db.Integer)
    communication = db.Column(db.Integer)
    location = db.Column(db.Integer)
    value = db.Column(db.Integer)
    stay_note = db.Column(db.String(80))
    body = db.Column(db.Text, nullable=False)
    private_note = db.Column(db.Text)
    host_response = db.Column(db.Text)

    listing = db.relationship('Listing', backref='reviews')

    @property
    def initial(self):
        return self.author_name[:1].upper()

    @property
    def avatar_hue(self):
        return int(hashlib.md5(f'rev-{self.id}'.encode()).hexdigest()[:4], 16) % 360


class Wishlist(db.Model):
    __tablename__ = 'wishlists'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

    items = db.relationship('WishlistItem', backref='wishlist',
                            cascade='all, delete-orphan',
                            order_by='WishlistItem.added_at.desc()')


class WishlistItem(db.Model):
    __tablename__ = 'wishlist_items'
    id = db.Column(db.Integer, primary_key=True)
    wishlist_id = db.Column(db.Integer, db.ForeignKey('wishlists.id'), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    added_at = db.Column(db.DateTime, nullable=False)
    note = db.Column(db.String(250))

    listing = db.relationship('Listing')

    __table_args__ = (db.UniqueConstraint('wishlist_id', 'listing_id'),)


class PaymentMethod(db.Model):
    __tablename__ = 'payment_methods'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    brand = db.Column(db.String(30), nullable=False)
    last4 = db.Column(db.String(4), nullable=False)
    exp_month = db.Column(db.Integer, nullable=False)
    exp_year = db.Column(db.Integer, nullable=False)
    holder_name = db.Column(db.String(120), nullable=False)
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(60))
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False)

    @property
    def label(self):
        return f'{self.brand} •••• {self.last4}'

    @property
    def expiry(self):
        return f'{self.exp_month:02d}/{self.exp_year % 100:02d}'


class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(12), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    checkin = db.Column(db.Date, nullable=False)
    checkout = db.Column(db.Date, nullable=False)
    adults = db.Column(db.Integer, nullable=False, default=1)
    children = db.Column(db.Integer, nullable=False, default=0)
    infants = db.Column(db.Integer, nullable=False, default=0)
    pets = db.Column(db.Integer, nullable=False, default=0)
    nights = db.Column(db.Integer, nullable=False)
    nightly_price = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Integer, nullable=False)
    discount = db.Column(db.Integer, nullable=False, default=0)
    discount_label = db.Column(db.String(40))
    cleaning_fee = db.Column(db.Integer, nullable=False)
    service_fee = db.Column(db.Integer, nullable=False)
    taxes = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    cancellation_policy = db.Column(db.String(20), nullable=False)
    # confirmed / pending (request to book) / cancelled / declined
    status = db.Column(db.String(20), nullable=False)
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_methods.id'))
    payment_label = db.Column(db.String(60))
    message_to_host = db.Column(db.Text)
    trip_purpose = db.Column(db.String(40))
    created_at = db.Column(db.DateTime, nullable=False)
    cancelled_at = db.Column(db.DateTime)
    cancel_reason = db.Column(db.String(120))
    refund_amount = db.Column(db.Integer)

    listing = db.relationship('Listing')
    user = db.relationship('User', backref='reservations')

    @property
    def guest_count(self):
        return self.adults + self.children

    @property
    def guests_label(self):
        return guests_label(self.adults, self.children, self.infants, self.pets)

    @property
    def is_past(self):
        return self.checkout <= MIRROR_TODAY

    @property
    def is_upcoming(self):
        return self.status in ('confirmed', 'pending') and self.checkout > MIRROR_TODAY

    @property
    def status_label(self):
        if self.status == 'cancelled':
            return 'Canceled'
        if self.status == 'declined':
            return 'Declined'
        if self.status == 'pending':
            return 'Request pending'
        if self.checkout <= MIRROR_TODAY:
            return 'Completed'
        if self.checkin <= MIRROR_TODAY:
            return 'Currently hosting you'
        return 'Confirmed'

    @property
    def review(self):
        return Review.query.filter_by(reservation_id=self.id).first()

    @property
    def can_review(self):
        return (self.status == 'confirmed' and self.checkout <= MIRROR_TODAY
                and (MIRROR_TODAY - self.checkout).days <= 14 and self.review is None)


class MessageThread(db.Model):
    __tablename__ = 'message_threads'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    host_id = db.Column(db.Integer, db.ForeignKey('hosts.id'), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.id'))
    updated_at = db.Column(db.DateTime, nullable=False)
    archived = db.Column(db.Boolean, default=False)
    unread = db.Column(db.Boolean, default=False)

    host = db.relationship('Host')
    listing = db.relationship('Listing')
    reservation = db.relationship('Reservation')
    messages = db.relationship('Message', backref='thread', order_by='Message.sent_at',
                               cascade='all, delete-orphan')

    @property
    def last_message(self):
        return self.messages[-1] if self.messages else None


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('message_threads.id'), nullable=False)
    sender = db.Column(db.String(10), nullable=False)   # guest / host / airbnb
    body = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, nullable=False)


class HelpArticle(db.Model):
    __tablename__ = 'help_articles'
    id = db.Column(db.Integer, primary_key=True)          # /help/article/<id>
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    audience = db.Column(db.String(20), nullable=False)   # guest / host / all
    summary = db.Column(db.String(300))
    body = db.Column(db.Text, nullable=False)             # JSON list of blocks
    position = db.Column(db.Integer, nullable=False)

    @property
    def blocks(self):
        return json.loads(self.body)


INDEX_STATEMENTS = (
    "CREATE INDEX IF NOT EXISTS ix_listings_city ON listings (city_id, rank)",
    "CREATE INDEX IF NOT EXISTS ix_listings_host ON listings (host_id)",
    "CREATE INDEX IF NOT EXISTS ix_listing_amenities_listing ON listing_amenities (listing_id, position)",
    "CREATE INDEX IF NOT EXISTS ix_listing_highlights_listing ON listing_highlights (listing_id, position)",
    "CREATE INDEX IF NOT EXISTS ix_listing_photos_listing ON listing_photos (listing_id, position)",
    "CREATE INDEX IF NOT EXISTS ix_message_threads_user ON message_threads (user_id, updated_at)",
    "CREATE INDEX IF NOT EXISTS ix_messages_thread ON messages (thread_id, sent_at)",
    "CREATE INDEX IF NOT EXISTS ix_reservations_listing ON reservations (listing_id, checkin)",
    "CREATE INDEX IF NOT EXISTS ix_reservations_user ON reservations (user_id, checkin)",
    "CREATE INDEX IF NOT EXISTS ix_reviews_listing ON reviews (listing_id, created)",
    "CREATE INDEX IF NOT EXISTS ix_sleeping_listing ON sleeping_arrangements (listing_id, position)",
    "CREATE INDEX IF NOT EXISTS ix_wishlist_items_wishlist ON wishlist_items (wishlist_id, added_at)",
    "CREATE INDEX IF NOT EXISTS ix_wishlists_user ON wishlists (user_id, created_at)",
)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# --------------------------------------------------------------- pricing ---

def guests_label(adults, children=0, infants=0, pets=0):
    guests = adults + children
    parts = [f"{guests} guest{'s' if guests != 1 else ''}"]
    if infants:
        parts.append(f"{infants} infant{'s' if infants != 1 else ''}")
    if pets:
        parts.append(f"{pets} pet{'s' if pets != 1 else ''}")
    return ', '.join(parts)


def price_quote(listing: Listing, checkin: date, checkout: date) -> dict:
    """Full Airbnb price breakdown for a stay (whole-dollar USD)."""
    nights = (checkout - checkin).days
    subtotal = listing.nightly_price * nights
    discount, discount_label = 0, None
    if nights >= 28 and listing.monthly_discount:
        discount = money(subtotal * listing.monthly_discount / 100)
        discount_label = 'Monthly stay discount'
    elif nights >= 7 and listing.weekly_discount:
        discount = money(subtotal * listing.weekly_discount / 100)
        discount_label = 'Weekly stay discount'
    base = subtotal - discount + listing.cleaning_fee
    service_fee = money(Decimal(base) * SERVICE_FEE_RATE)
    taxes = money(Decimal(base) * Decimal(str(listing.city.tax_rate)))
    return {
        'nights': nights,
        'nightly_price': listing.nightly_price,
        'subtotal': subtotal,
        'discount': discount,
        'discount_label': discount_label,
        'cleaning_fee': listing.cleaning_fee,
        'service_fee': service_fee,
        'taxes': taxes,
        'total_before_taxes': base + service_fee,
        'total': base + service_fee + taxes,
    }


POLICY_TEXT = {
    'Flexible': ('Free cancellation until 1 day before check-in. After that, the '
                 'first night, the service fee and taxes are non-refundable; the '
                 'remaining nights and the cleaning fee are refunded.'),
    'Moderate': ('Free cancellation until 5 days before check-in. After that, the '
                 'first night, the service fee and taxes are non-refundable; you get '
                 '50% of the remaining nights back, plus the full cleaning fee.'),
    'Firm': ('Free cancellation until 30 days before check-in. Cancel at least 7 '
             'days before check-in to get 50% of the nightly rate back, plus the '
             'full cleaning fee. No refund after that.'),
    'Strict': ('Free cancellation for 48 hours after booking, if check-in is at '
               'least 14 days away. Cancel at least 7 days before check-in to get '
               '50% of the nightly rate back, plus the full cleaning fee. No refund '
               'after that.'),
}


def free_cancellation_deadline(policy: str, checkin: date, booked_at: datetime | None = None):
    """Last day a guest can cancel for a full refund, or None."""
    if policy == 'Flexible':
        return checkin - timedelta(days=1)
    if policy == 'Moderate':
        return checkin - timedelta(days=5)
    if policy == 'Firm':
        return checkin - timedelta(days=30)
    if policy == 'Strict':
        booked_at = booked_at or mirror_now()
        deadline = (booked_at + timedelta(hours=48)).date()
        if (checkin - booked_at.date()).days >= 14:
            return min(deadline, checkin - timedelta(days=14))
        return None
    return None


def refund_quote(res: Reservation) -> dict:
    """Refund a guest receives if they cancel `res` on MIRROR_TODAY."""
    if res.status == 'pending':
        return {'refund': res.total, 'kept': 0, 'rule': 'Your request has not been '
                'accepted yet, so you have not been charged.', 'full': True}
    days_before = (res.checkin - MIRROR_TODAY).days
    accommodation = res.subtotal - res.discount
    full = {'refund': res.total, 'kept': 0, 'full': True,
            'rule': 'You are cancelling inside the free-cancellation window, so the '
                    'full amount is refunded.'}
    half = money(Decimal(accommodation) / 2) + res.cleaning_fee
    partial_rule = ('50% of the nightly rate is refunded, plus the full cleaning fee. '
                    'The service fee and taxes are non-refundable.')
    after_first = max(accommodation - res.nightly_price, 0)
    policy = res.cancellation_policy
    if policy == 'Flexible':
        if days_before >= 1:
            return full
        refund = after_first + res.cleaning_fee
        return {'refund': refund, 'kept': res.total - refund, 'full': False,
                'rule': 'The first night, the service fee and taxes are non-refundable. '
                        'The remaining nights and the cleaning fee are refunded.'}
    if policy == 'Moderate':
        if days_before >= 5:
            return full
        refund = money(Decimal(after_first) / 2) + res.cleaning_fee
        return {'refund': refund, 'kept': res.total - refund, 'full': False,
                'rule': 'The first night, the service fee and taxes are non-refundable. '
                        '50% of the remaining nights is refunded, plus the full cleaning fee.'}
    if policy == 'Firm':
        if days_before >= 30:
            return full
        if days_before >= 7:
            return {'refund': half, 'kept': res.total - half, 'full': False, 'rule': partial_rule}
        return {'refund': 0, 'kept': res.total, 'full': False,
                'rule': 'Check-in is less than 7 days away, so this reservation is non-refundable.'}
    if policy == 'Strict':
        hours_since = (mirror_now() - res.created_at).total_seconds() / 3600
        if hours_since <= 48 and days_before >= 14:
            return full
        if days_before >= 7:
            return {'refund': half, 'kept': res.total - half, 'full': False, 'rule': partial_rule}
        return {'refund': 0, 'kept': res.total, 'full': False,
                'rule': 'Check-in is less than 7 days away, so this reservation is non-refundable.'}
    return full


def reservation_code(reservation_id: int) -> str:
    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    digest = hashlib.sha256(f'airbnb-reservation-{reservation_id}'.encode()).digest()
    return 'HM' + ''.join(alphabet[b % len(alphabet)] for b in digest[:8])


# ------------------------------------------------------------ availability --

@lru_cache(maxsize=4096)
def seeded_blocked_nights(listing_id: int) -> frozenset:
    """Nights already booked by other guests (deterministic per listing).

    Every listing was captured from an upstream search for the snapshot stay,
    so those nights stay open everywhere.
    """
    rng = random.Random(f'airbnb-calendar-{listing_id}')
    blocked = set()
    cursor = MIRROR_TODAY + timedelta(days=rng.randint(0, 6))
    end = MIRROR_TODAY + timedelta(days=CALENDAR_HORIZON_DAYS)
    while cursor < end:
        length = rng.randint(2, 5)
        for i in range(length):
            night = cursor + timedelta(days=i)
            if not SNAPSHOT_STAY[0] <= night < SNAPSHOT_STAY[1]:
                blocked.add(night)
        cursor += timedelta(days=length + rng.randint(5, 18))
    return frozenset(blocked)


def booked_nights(listing_id: int, exclude_reservation_id=None) -> set:
    nights = set(seeded_blocked_nights(listing_id))
    q = Reservation.query.filter(Reservation.listing_id == listing_id,
                                 Reservation.status.in_(('confirmed', 'pending')),
                                 Reservation.checkout > MIRROR_TODAY)
    for res in q.all():
        if res.id == exclude_reservation_id:
            continue
        d = res.checkin
        while d < res.checkout:
            nights.add(d)
            d += timedelta(days=1)
    return nights


def stay_problem(listing: Listing, checkin: date | None, checkout: date | None,
                 adults=1, children=0, infants=0, pets=0):
    """Return a user-facing reason the stay can't be booked, or None."""
    if not checkin or not checkout:
        return 'Add your travel dates to book.'
    if checkin < MIRROR_TODAY:
        return 'Check-in date is in the past.'
    if checkout <= checkin:
        return 'Checkout must be after check-in.'
    nights = (checkout - checkin).days
    if nights > MAX_NIGHTS:
        return f'Stays are limited to {MAX_NIGHTS} nights.'
    if checkout > MIRROR_TODAY + timedelta(days=CALENDAR_HORIZON_DAYS):
        return 'Those dates are not open for booking yet.'
    if nights < listing.min_nights:
        return f'This place has a {listing.min_nights}-night minimum.'
    if adults < 1:
        return 'At least one adult is required.'
    if adults + children > listing.guests:
        return f'This place has a maximum of {listing.guests} guests, not including infants.'
    if infants > 5:
        return 'This place allows a maximum of 5 infants.'
    if pets and not listing.pets_allowed:
        return 'This place doesn’t allow pets.'
    blocked = booked_nights(listing.id)
    d = checkin
    while d < checkout:
        if d in blocked:
            return 'Those dates are not available.'
        d += timedelta(days=1)
    return None


def month_grid(listing: Listing, year: int, month: int, blocked: set):
    first = date(year, month, 1)
    days_in = monthrange(year, month)[1]
    lead = (first.weekday() + 1) % 7     # Sunday-first calendar
    cells = [None] * lead
    horizon = MIRROR_TODAY + timedelta(days=CALENDAR_HORIZON_DAYS)
    for day in range(1, days_in + 1):
        d = date(year, month, day)
        cells.append({'date': d, 'available': MIRROR_TODAY <= d < horizon and d not in blocked,
                      'past': d < MIRROR_TODAY})
    while len(cells) % 7:
        cells.append(None)
    return {'label': first.strftime('%B %Y'), 'weeks': [cells[i:i + 7] for i in range(0, len(cells), 7)],
            'year': year, 'month': month}


# ----------------------------------------------------------------- search ---

AMENITY_FILTERS = [
    ('wifi', 'Wifi'), ('kitchen', 'Kitchen'), ('washer', 'Washer'), ('dryer', 'Dryer'),
    ('air_conditioning', 'Air conditioning'), ('heating', 'Heating'),
    ('workspace', 'Dedicated workspace'), ('tv', 'TV'), ('free_parking', 'Free parking on premises'),
    ('pool', 'Pool'), ('hot_tub', 'Hot tub'), ('ev_charger', 'EV charger'), ('crib', 'Crib'),
    ('gym', 'Gym'), ('bbq', 'BBQ grill'), ('breakfast', 'Breakfast'),
    ('fireplace', 'Indoor fireplace'), ('balcony', 'Patio or balcony'),
    ('elevator', 'Elevator'), ('waterfront', 'Waterfront'), ('beach_access', 'Beach access'),
    ('smoke_alarm', 'Smoke alarm'), ('co_alarm', 'Carbon monoxide alarm'),
]
AMENITY_FILTER_LABELS = dict(AMENITY_FILTERS)
PROPERTY_GROUPS = ('House', 'Apartment', 'Guesthouse', 'Hotel')
ROOM_TYPES = ('Entire home', 'Private room', 'Shared room', 'Hotel room')


@lru_cache(maxsize=1)
def _city_index():
    rows = []
    for city in City.query.order_by(City.position).all():
        tokens = set(tokenize(f'{city.name} {city.region or ""} {city.country}'))
        rows.append((city.id, frozenset(tokens), frozenset(tokenize(city.name))))
    return rows


@lru_cache(maxsize=1)
def _listing_index():
    rows = {}
    for listing in Listing.query.order_by(Listing.id).all():
        rows[listing.id] = {
            'place': frozenset(tokenize(f'{listing.neighborhood or ""}')),
            'text': frozenset(tokenize(f'{listing.name} {listing.title} {listing.property_type} '
                                       f'{listing.room_type}')),
        }
    return rows


def resolve_location(query: str):
    """Map a free-text destination to (cities, extra_tokens).

    Token-overlap scoring against city / region / country names: every city
    sharing the best overlap is returned; tokens that did not match a place
    name are handed back for neighborhood / title scoring.
    """
    tokens = tokenize(query)
    if not tokens:
        return [], []
    best, matched = 0, []
    for city_id, place_tokens, name_tokens in _city_index():
        score = sum(2 if t in name_tokens else 1 for t in tokens if t in place_tokens)
        if score > best:
            best, matched = score, [city_id]
        elif score == best and score > 0:
            matched.append(city_id)
    if not best:
        return [], tokens
    used = set()
    for city_id, place_tokens, _ in _city_index():
        if city_id in matched:
            used |= place_tokens
    return matched, [t for t in tokens if t not in used]


def score_listings(tokens, candidates):
    """Scored token overlap (not strict AND) on neighborhood + listing text."""
    index = _listing_index()
    scored = []
    for listing in candidates:
        row = index.get(listing.id, {'place': frozenset(), 'text': frozenset()})
        score = sum(3 if t in row['place'] else (1 if t in row['text'] else 0) for t in tokens)
        scored.append((score, listing))
    return scored


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


def parse_int(value, default=0, lo=0, hi=99):
    try:
        v = int(value)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, v))


def search_state(args, location=None):
    """Normalize search query-string parameters (Airbnb naming)."""
    query = (args.get('query') or '').strip()
    if not query and location:
        query = location.replace('--', ', ').replace('-', ' ')
    return {
        'query': query,
        'checkin': parse_date(args.get('checkin')),
        'checkout': parse_date(args.get('checkout')),
        'adults': parse_int(args.get('adults'), 0, 0, 16),
        'children': parse_int(args.get('children'), 0, 0, 15),
        'infants': parse_int(args.get('infants'), 0, 0, 5),
        'pets': parse_int(args.get('pets'), 0, 0, 5),
        'price_min': parse_int(args.get('price_min'), 0, 0, 100000) or None,
        'price_max': parse_int(args.get('price_max'), 0, 0, 100000) or None,
        'room_types': [r for r in args.getlist('room_types[]') if r in ROOM_TYPES],
        'property_types': [p for p in args.getlist('property_type[]') if p in PROPERTY_GROUPS],
        'min_bedrooms': parse_int(args.get('min_bedrooms'), 0, 0, 8),
        'min_beds': parse_int(args.get('min_beds'), 0, 0, 8),
        'min_bathrooms': parse_int(args.get('min_bathrooms'), 0, 0, 8),
        'amenities': [a for a in args.getlist('amenities[]') if a in AMENITY_FILTER_LABELS],
        'instant_book': args.get('ib') == 'true',
        'self_checkin': args.get('self_check_in') == 'true',
        'guest_favorite': args.get('guest_favorite') == 'true',
        'superhost': args.get('superhost') == 'true',
        'free_cancellation': args.get('flexible_cancellation') == 'true',
        'page': parse_int(args.get('page'), 1, 1, 50),
    }


def listing_amenity_keys(listing_id):
    rows = (db.session.query(Amenity.filter_key)
            .join(ListingAmenity, ListingAmenity.amenity_id == Amenity.id)
            .filter(ListingAmenity.listing_id == listing_id, ListingAmenity.available.is_(True),
                    Amenity.filter_key.isnot(None)).all())
    return {r[0] for r in rows}


def run_search(state):
    cities, extra = resolve_location(state['query'])
    q = Listing.query
    if cities:
        q = q.filter(Listing.city_id.in_(cities))
    candidates = q.order_by(Listing.city_id, Listing.rank).all()
    if state['query'] and not cities:
        scored = [(s, l) for s, l in score_listings(extra, candidates) if s > 0]
    else:
        scored = score_listings(extra, candidates) if extra else [(0, l) for l in candidates]
    # Stable relevance: token score, then the upstream result order.
    scored.sort(key=lambda sl: (-sl[0], sl[1].city.position, sl[1].rank))
    listings = [l for _, l in scored]

    guests = state['adults'] + state['children']
    stay = state['checkin'] and state['checkout'] and state['checkout'] > state['checkin']
    out = []
    for listing in listings:
        if guests and listing.guests < guests:
            continue
        if state['pets'] and not listing.pets_allowed:
            continue
        if state['room_types'] and listing.room_type not in state['room_types']:
            continue
        if state['property_types'] and listing.property_group not in state['property_types']:
            continue
        if listing.bedrooms < state['min_bedrooms'] or listing.beds < state['min_beds']:
            continue
        if listing.baths < state['min_bathrooms']:
            continue
        if state['instant_book'] and not listing.instant_book:
            continue
        if state['self_checkin'] and not listing.self_checkin:
            continue
        if state['guest_favorite'] and not listing.is_guest_favorite:
            continue
        if state['superhost'] and not listing.host.is_superhost:
            continue
        if state['free_cancellation'] and listing.cancellation_policy not in ('Flexible', 'Moderate'):
            continue
        if state['price_min'] and listing.nightly_price < state['price_min']:
            continue
        if state['price_max'] and listing.nightly_price > state['price_max']:
            continue
        if state['amenities'] and not set(state['amenities']) <= listing_amenity_keys(listing.id):
            continue
        if stay and stay_problem(listing, state['checkin'], state['checkout'],
                                 max(state['adults'], 1), state['children'],
                                 state['infants'], state['pets']):
            continue
        out.append(listing)
    return cities, out


def search_url(location_slug=None, **params):
    clean = {}
    for key, value in params.items():
        if value in (None, '', 0, False, []):
            continue
        clean[key] = value
    path = f"/s/{quote(location_slug or 'homes', safe='-')}/homes" if location_slug else '/s/homes'
    return path + ('?' + urlencode(clean, doseq=True) if clean else '')


def state_params(state, **overrides):
    params = {
        'query': state['query'],
        'checkin': state['checkin'].isoformat() if state['checkin'] else None,
        'checkout': state['checkout'].isoformat() if state['checkout'] else None,
        'adults': state['adults'], 'children': state['children'],
        'infants': state['infants'], 'pets': state['pets'],
        'price_min': state['price_min'], 'price_max': state['price_max'],
        'room_types[]': state['room_types'], 'property_type[]': state['property_types'],
        'min_bedrooms': state['min_bedrooms'], 'min_beds': state['min_beds'],
        'min_bathrooms': state['min_bathrooms'], 'amenities[]': state['amenities'],
        'ib': 'true' if state['instant_book'] else None,
        'self_check_in': 'true' if state['self_checkin'] else None,
        'guest_favorite': 'true' if state['guest_favorite'] else None,
        'superhost': 'true' if state['superhost'] else None,
        'flexible_cancellation': 'true' if state['free_cancellation'] else None,
    }
    params.update(overrides)
    return {k: v for k, v in params.items() if v not in (None, '', 0, False, [])}


def room_url(listing, state=None):
    params = {}
    if state:
        if state.get('checkin') and state.get('checkout'):
            params['check_in'] = state['checkin'].isoformat()
            params['check_out'] = state['checkout'].isoformat()
        for key in ('adults', 'children', 'infants', 'pets'):
            if state.get(key):
                params[key] = state[key]
    return f'/rooms/{listing.id}' + ('?' + urlencode(params) if params else '')


# ------------------------------------------------------------ template ctx --

def fmt_money(value):
    return f'${value:,.0f}'


def fmt_range(checkin, checkout):
    if not checkin or not checkout:
        return ''
    if checkin.year == checkout.year and checkin.month == checkout.month:
        return f"{checkin.strftime('%b')} {checkin.day} – {checkout.day}"
    if checkin.year == checkout.year:
        return f"{checkin.strftime('%b')} {checkin.day} – {checkout.strftime('%b')} {checkout.day}"
    return f"{checkin.strftime('%b')} {checkin.day}, {checkin.year} – {checkout.strftime('%b')} {checkout.day}, {checkout.year}"


def fmt_long_date(d):
    return f"{d.strftime('%a, %b')} {d.day}, {d.year}" if d else ''


app.jinja_env.filters['money'] = fmt_money
app.jinja_env.filters['long_date'] = fmt_long_date
app.jinja_env.globals.update(fmt_range=fmt_range, room_url=room_url, search_url=search_url,
                             guests_label=guests_label,
                             MIRROR_TODAY=MIRROR_TODAY, POLICY_TEXT=POLICY_TEXT,
                             AMENITY_FILTERS=AMENITY_FILTERS, PROPERTY_GROUPS=PROPERTY_GROUPS,
                             free_cancellation_deadline=free_cancellation_deadline)


@app.context_processor
def inject_globals():
    saved_ids = set()
    if current_user.is_authenticated:
        rows = (db.session.query(WishlistItem.listing_id)
                .join(Wishlist, Wishlist.id == WishlistItem.wishlist_id)
                .filter(Wishlist.user_id == current_user.id).all())
        saved_ids = {r[0] for r in rows}
    return {'saved_ids': saved_ids, 'nav_cities': City.query.order_by(City.position).all()}


def safe_next(target):
    if target and target.startswith('/') and not target.startswith('//'):
        return target
    return None


# ------------------------------------------------------------------ pages ---

@app.route('/')
def index():
    rows = []
    for city in City.query.order_by(City.position).all():
        listings = (Listing.query.filter_by(city_id=city.id)
                    .order_by(Listing.rank).limit(8).all())
        if listings:
            rows.append({'city': city, 'listings': listings,
                         'heading': f'Popular homes in {city.name}'})
    return render_template('index.html', rows=rows, state=search_state(request.args))


@app.route('/s/homes')
@app.route('/s/<path:location>/homes')
def search(location=None):
    state = search_state(request.args, location)
    if not state['query'] and location is None and not request.args:
        return redirect(url_for('index'))
    cities, results = run_search(state)
    total = len(results)
    pages = max(1, (total + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE)
    page = min(state['page'], pages)
    start = (page - 1) * RESULTS_PER_PAGE
    page_results = results[start:start + RESULTS_PER_PAGE]
    quotes = {}
    stay = state['checkin'] and state['checkout'] and state['checkout'] > state['checkin']
    if stay:
        for listing in page_results:
            quotes[listing.id] = price_quote(listing, state['checkin'], state['checkout'])
    city_objs = [db.session.get(City, c) for c in cities]
    place = city_objs[0].name if len(city_objs) == 1 else (state['query'] or 'your search')
    filter_count = sum([
        bool(state['price_min'] or state['price_max']), len(state['room_types']),
        len(state['property_types']), bool(state['min_bedrooms']), bool(state['min_beds']),
        bool(state['min_bathrooms']), len(state['amenities']), state['instant_book'],
        state['self_checkin'], state['guest_favorite'], state['superhost'],
        state['free_cancellation']])
    slug = city_objs[0].slug if len(city_objs) == 1 else (location or None)
    return render_template(
        'search.html', state=state, results=page_results, total=total, page=page,
        pages=pages, quotes=quotes, place=place, cities=city_objs, stay=stay,
        filter_count=filter_count, slug=slug,
        page_url=lambda n: search_url(slug, **state_params(state, page=n)),
        clear_url=search_url(slug, **state_params(
            state, price_min=None, price_max=None, **{'room_types[]': [], 'property_type[]': [],
                                                      'amenities[]': []},
            min_bedrooms=0, min_beds=0, min_bathrooms=0, ib=None, self_check_in=None,
            guest_favorite=None, superhost=None, flexible_cancellation=None)))


def _room_state(args):
    return {
        'checkin': parse_date(args.get('check_in')),
        'checkout': parse_date(args.get('check_out')),
        'adults': parse_int(args.get('adults'), 1, 1, 16),
        'children': parse_int(args.get('children'), 0, 0, 15),
        'infants': parse_int(args.get('infants'), 0, 0, 5),
        'pets': parse_int(args.get('pets'), 0, 0, 5),
    }


@app.route('/rooms/<int:listing_id>')
def room(listing_id):
    listing = db.session.get(Listing, listing_id) or abort(404)
    state = _room_state(request.args)
    quote_ = problem = None
    if state['checkin'] and state['checkout']:
        problem = stay_problem(listing, state['checkin'], state['checkout'], state['adults'],
                               state['children'], state['infants'], state['pets'])
        if state['checkout'] > state['checkin']:
            quote_ = price_quote(listing, state['checkin'], state['checkout'])
    blocked = booked_nights(listing.id)
    year = parse_int(request.args.get('cal_year'), MIRROR_TODAY.year, MIRROR_TODAY.year,
                     MIRROR_TODAY.year + 1)
    month = parse_int(request.args.get('cal_month'), (state['checkin'] or MIRROR_TODAY).month, 1, 12)
    if not request.args.get('cal_year') and state['checkin']:
        year = state['checkin'].year
    first = date(year, month, 1)
    if first < MIRROR_TODAY.replace(day=1):
        first = MIRROR_TODAY.replace(day=1)
    second = (first + timedelta(days=32)).replace(day=1)
    months = [month_grid(listing, first.year, first.month, blocked),
              month_grid(listing, second.year, second.month, blocked)]
    prev_month = (first - timedelta(days=1)).replace(day=1)
    next_month = second
    amenities = (ListingAmenity.query.filter_by(listing_id=listing.id)
                 .order_by(ListingAmenity.position).all())
    reviews = (Review.query.filter_by(listing_id=listing.id)
               .order_by(Review.created.desc(), Review.id.desc()).limit(6).all())
    return render_template(
        'room.html', listing=listing, state=state, quote=quote_, problem=problem,
        months=months, prev_month=prev_month if prev_month >= MIRROR_TODAY.replace(day=1) else None,
        next_month=next_month, amenities=amenities,
        highlights=Highlight.query.filter_by(listing_id=listing.id).order_by(Highlight.position).all(),
        sleeping=SleepingArrangement.query.filter_by(listing_id=listing.id)
        .order_by(SleepingArrangement.position).all(),
        reviews=reviews,
        review_total=Review.query.filter_by(listing_id=listing.id).count(),
        deadline=(free_cancellation_deadline(listing.cancellation_policy, state['checkin'])
                  if state['checkin'] else None))


@app.route('/rooms/<int:listing_id>/photos')
def room_photos(listing_id):
    listing = db.session.get(Listing, listing_id) or abort(404)
    return render_template('room_photos.html', listing=listing, photos=listing.photos)


@app.route('/rooms/<int:listing_id>/amenities')
def room_amenities(listing_id):
    listing = db.session.get(Listing, listing_id) or abort(404)
    rows = (ListingAmenity.query.filter_by(listing_id=listing.id)
            .order_by(ListingAmenity.position).all())
    groups, missing = {}, []
    for row in rows:
        if not row.available:
            missing.append(row)
            continue
        groups.setdefault(row.amenity.category, []).append(row)
    return render_template('room_amenities.html', listing=listing, groups=groups, missing=missing)


@app.route('/rooms/<int:listing_id>/reviews')
def room_reviews(listing_id):
    listing = db.session.get(Listing, listing_id) or abort(404)
    q = (request.args.get('q') or '').strip()
    sort = request.args.get('sort', 'recent')
    query = Review.query.filter_by(listing_id=listing.id)
    reviews = query.all()
    if q:
        tokens = tokenize(q)
        reviews = [r for r in reviews if any(t in set(tokenize(r.body)) for t in tokens)]
    if sort == 'highest':
        reviews.sort(key=lambda r: (-r.rating, -r.created.toordinal(), -r.id))
    elif sort == 'lowest':
        reviews.sort(key=lambda r: (r.rating, -r.created.toordinal(), -r.id))
    else:
        sort = 'recent'
        reviews.sort(key=lambda r: (-r.created.toordinal(), -r.id))
    page = parse_int(request.args.get('page'), 1, 1, 100)
    pages = max(1, (len(reviews) + REVIEWS_PER_PAGE - 1) // REVIEWS_PER_PAGE)
    page = min(page, pages)
    shown = reviews[(page - 1) * REVIEWS_PER_PAGE: page * REVIEWS_PER_PAGE]
    return render_template('room_reviews.html', listing=listing, reviews=shown, q=q, sort=sort,
                           page=page, pages=pages, matched=len(reviews))


@app.route('/users/show/<int:host_id>')
def host_profile(host_id):
    host = db.session.get(Host, host_id) or abort(404)
    listings = Listing.query.filter_by(host_id=host.id).order_by(Listing.city_id, Listing.rank).all()
    ids = [l.id for l in listings]
    reviews = (Review.query.filter(Review.listing_id.in_(ids))
               .order_by(Review.created.desc(), Review.id.desc()).limit(8).all()) if ids else []
    return render_template('host_profile.html', host=host, listings=listings, reviews=reviews)


# ---------------------------------------------------------------- booking ---

def _book_state(listing_id, source):
    return {
        'checkin': parse_date(source.get('checkin')),
        'checkout': parse_date(source.get('checkout')),
        'adults': parse_int(source.get('numberOfAdults'), 1, 1, 16),
        'children': parse_int(source.get('numberOfChildren'), 0, 0, 15),
        'infants': parse_int(source.get('numberOfInfants'), 0, 0, 5),
        'pets': parse_int(source.get('numberOfPets'), 0, 0, 5),
    }


def book_url(listing, state):
    params = {'checkin': state['checkin'].isoformat(), 'checkout': state['checkout'].isoformat(),
              'numberOfAdults': state['adults'], 'numberOfChildren': state['children'],
              'numberOfInfants': state['infants'], 'numberOfPets': state['pets']}
    return f'/book/stays/{listing.id}?' + urlencode(params)


app.jinja_env.globals['book_url'] = book_url


def _card_brand(number):
    if number.startswith('4'):
        return 'Visa'
    if number[:2] in ('51', '52', '53', '54', '55') or number[:4].isdigit() and 2221 <= int(number[:4]) <= 2720:
        return 'Mastercard'
    if number[:2] in ('34', '37'):
        return 'American Express'
    if number.startswith('6011') or number.startswith('65'):
        return 'Discover'
    return None


def _luhn_ok(number):
    total = 0
    for i, ch in enumerate(reversed(number)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def add_card_from_form(user, form):
    """Validate + store a card; returns (PaymentMethod|None, error|None)."""
    number = re.sub(r'\D', '', form.get('card_number', ''))
    expiry = (form.get('expiration') or '').strip()
    cvv = re.sub(r'\D', '', form.get('cvv', ''))
    postal = (form.get('postal_code') or '').strip()
    holder = (form.get('holder_name') or '').strip() or user.full_name
    brand = _card_brand(number) if number else None
    if not (13 <= len(number) <= 19) or not brand or not _luhn_ok(number):
        return None, 'Check your card number.'
    m = re.fullmatch(r'(\d{1,2})\s*/\s*(\d{2}|\d{4})', expiry)
    if not m:
        return None, 'Check the expiration date (MM/YY).'
    exp_month, exp_year = int(m.group(1)), int(m.group(2))
    if exp_year < 100:
        exp_year += 2000
    if not 1 <= exp_month <= 12 or (exp_year, exp_month) < (MIRROR_TODAY.year, MIRROR_TODAY.month):
        return None, 'This card has expired.'
    if len(cvv) not in (3, 4):
        return None, 'Check the CVV.'
    if not postal:
        return None, 'ZIP code is required.'
    has_default = PaymentMethod.query.filter_by(user_id=user.id, is_default=True).first()
    card = PaymentMethod(user_id=user.id, brand=brand, last4=number[-4:], exp_month=exp_month,
                         exp_year=exp_year, holder_name=holder, postal_code=postal,
                         country=(form.get('country') or 'United States'),
                         is_default=not has_default, created_at=mirror_now())
    db.session.add(card)
    db.session.flush()
    return card, None


@app.route('/book/stays/<int:listing_id>', methods=['GET', 'POST'])
@login_required
def book(listing_id):
    listing = db.session.get(Listing, listing_id) or abort(404)
    source = request.form if request.method == 'POST' else request.args
    state = _book_state(listing_id, source)
    problem = stay_problem(listing, state['checkin'], state['checkout'], state['adults'],
                           state['children'], state['infants'], state['pets'])
    cards = (PaymentMethod.query.filter_by(user_id=current_user.id)
             .order_by(PaymentMethod.is_default.desc(), PaymentMethod.id).all())
    if problem:
        flash(problem, 'error')
        return redirect(room_url(listing, state))
    quote_ = price_quote(listing, state['checkin'], state['checkout'])
    error = None
    if request.method == 'POST':
        message = (request.form.get('message') or '').strip()
        card_choice = request.form.get('payment_method', '')
        card = None
        if card_choice == 'new':
            card, error = add_card_from_form(current_user, request.form)
        else:
            card = PaymentMethod.query.filter_by(id=parse_int(card_choice, 0, 0, 10 ** 9),
                                                 user_id=current_user.id).first()
            if not card:
                error = 'Choose a payment method.'
        if not error and not listing.instant_book and not message:
            error = 'Write a message to the host to send your request.'
        if not error:
            res = Reservation(
                code='PENDING', user_id=current_user.id, listing_id=listing.id,
                checkin=state['checkin'], checkout=state['checkout'], adults=state['adults'],
                children=state['children'], infants=state['infants'], pets=state['pets'],
                nights=quote_['nights'], nightly_price=quote_['nightly_price'],
                subtotal=quote_['subtotal'], discount=quote_['discount'],
                discount_label=quote_['discount_label'], cleaning_fee=quote_['cleaning_fee'],
                service_fee=quote_['service_fee'], taxes=quote_['taxes'], total=quote_['total'],
                cancellation_policy=listing.cancellation_policy,
                status='confirmed' if listing.instant_book else 'pending',
                payment_method_id=card.id, payment_label=card.label,
                message_to_host=message or None,
                trip_purpose=(request.form.get('trip_purpose') or None),
                created_at=mirror_now())
            db.session.add(res)
            db.session.flush()
            res.code = reservation_code(res.id)
            if message:
                thread = MessageThread.query.filter_by(user_id=current_user.id,
                                                       listing_id=listing.id).first()
                if not thread:
                    thread = MessageThread(user_id=current_user.id, host_id=listing.host_id,
                                           listing_id=listing.id, updated_at=mirror_now())
                    db.session.add(thread)
                    db.session.flush()
                thread.reservation_id = res.id
                thread.updated_at = mirror_now()
                db.session.add(Message(thread_id=thread.id, sender='guest', body=message,
                                       sent_at=mirror_now()))
            db.session.commit()
            if listing.instant_book:
                flash('Your reservation is confirmed.', 'success')
            else:
                flash(f'Request sent. {listing.host.first_name} usually responds '
                      f'{listing.host.response_time or "within a day"}.', 'success')
            return redirect(url_for('trip_detail', code=res.code))
        db.session.rollback()
        cards = (PaymentMethod.query.filter_by(user_id=current_user.id)
                 .order_by(PaymentMethod.is_default.desc(), PaymentMethod.id).all())
    return render_template('book.html', listing=listing, state=state, quote=quote_, cards=cards,
                           error=error, form=request.form if request.method == 'POST' else {},
                           deadline=free_cancellation_deadline(listing.cancellation_policy,
                                                               state['checkin']))


# ------------------------------------------------------------------ trips ---

@app.route('/trips')
@app.route('/trips/v1')
@login_required
def trips():
    tab = request.args.get('tab', 'upcoming')
    rows = Reservation.query.filter_by(user_id=current_user.id).all()
    upcoming = sorted([r for r in rows if r.is_upcoming], key=lambda r: (r.checkin, r.id))
    past = sorted([r for r in rows if r.status == 'confirmed' and r.checkout <= MIRROR_TODAY],
                  key=lambda r: (r.checkin, r.id), reverse=True)
    cancelled = sorted([r for r in rows if r.status in ('cancelled', 'declined')],
                       key=lambda r: (r.checkin, r.id), reverse=True)
    if tab not in ('upcoming', 'past', 'cancelled'):
        tab = 'upcoming'
    return render_template('trips.html', tab=tab, upcoming=upcoming, past=past, cancelled=cancelled)


def _own_reservation(code):
    res = Reservation.query.filter_by(code=code).first()
    if not res or res.user_id != current_user.id:
        abort(404)
    return res


@app.route('/trips/v1/<code>')
@login_required
def trip_detail(code):
    res = _own_reservation(code)
    thread = MessageThread.query.filter_by(user_id=current_user.id,
                                           listing_id=res.listing_id).first()
    return render_template('trip_detail.html', res=res, thread=thread,
                           review_deadline=res.checkout + timedelta(days=14),
                           deadline=free_cancellation_deadline(res.cancellation_policy,
                                                               res.checkin, res.created_at))


@app.route('/trips/v1/<code>/receipt')
@login_required
def trip_receipt(code):
    res = _own_reservation(code)
    return render_template('receipt.html', res=res)


CANCEL_REASONS = ('My travel dates changed', 'I found a different place to stay',
                  'I no longer need a place to stay', 'The host asked me to cancel',
                  'Travel restrictions', 'Other')


@app.route('/trips/v1/<code>/cancel', methods=['GET', 'POST'])
@login_required
def trip_cancel(code):
    res = _own_reservation(code)
    if not res.is_upcoming:
        flash('This reservation can no longer be canceled.', 'error')
        return redirect(url_for('trip_detail', code=code))
    quote_ = refund_quote(res)
    if request.method == 'POST':
        reason = request.form.get('reason')
        if reason not in CANCEL_REASONS:
            flash('Tell us why you need to cancel.', 'error')
            return redirect(url_for('trip_cancel', code=code))
        res.status = 'cancelled'
        res.cancelled_at = mirror_now()
        res.cancel_reason = reason
        res.refund_amount = quote_['refund']
        db.session.commit()
        flash(f'Your reservation was canceled. Refund: {fmt_money(quote_["refund"])}.', 'success')
        return redirect(url_for('trip_detail', code=code))
    return render_template('trip_cancel.html', res=res, quote=quote_, reasons=CANCEL_REASONS)


REVIEW_FIELDS = ('cleanliness', 'accuracy', 'checkin', 'communication', 'location', 'value')


@app.route('/trips/v1/<code>/review', methods=['GET', 'POST'])
@login_required
def trip_review(code):
    res = _own_reservation(code)
    if res.review:
        flash('You already reviewed this stay.', 'info')
        return redirect(url_for('trip_detail', code=code))
    if not res.can_review:
        flash('Reviews can be written within 14 days after checkout.', 'error')
        return redirect(url_for('trip_detail', code=code))
    error = None
    if request.method == 'POST':
        overall = parse_int(request.form.get('rating'), 0, 0, 5)
        cats = {f: parse_int(request.form.get(f), 0, 0, 5) for f in REVIEW_FIELDS}
        body = (request.form.get('body') or '').strip()
        if not overall:
            error = 'Choose an overall rating.'
        elif not all(cats.values()):
            error = 'Rate every category.'
        elif len(body) < 10:
            error = 'Write at least a sentence about your stay.'
        else:
            review = Review(listing_id=res.listing_id, user_id=current_user.id,
                            reservation_id=res.id, author_name=current_user.display_name,
                            author_location=current_user.lives_in, created=MIRROR_TODAY,
                            rating=overall, body=body,
                            private_note=(request.form.get('private_note') or '').strip() or None,
                            stay_note=f'Stayed {res.nights} night{"s" if res.nights != 1 else ""}',
                            **cats)
            db.session.add(review)
            db.session.commit()
            flash('Thanks! Your review was submitted.', 'success')
            return redirect(url_for('trip_detail', code=code))
    return render_template('trip_review.html', res=res, error=error, fields=REVIEW_FIELDS,
                           form=request.form)


# -------------------------------------------------------------- wishlists ---

@app.route('/wishlists')
@login_required
def wishlists():
    lists = (Wishlist.query.filter_by(user_id=current_user.id)
             .order_by(Wishlist.created_at.desc(), Wishlist.id.desc()).all())
    return render_template('wishlists.html', lists=lists)


@app.route('/wishlists/<int:wishlist_id>')
@login_required
def wishlist_detail(wishlist_id):
    wl = Wishlist.query.filter_by(id=wishlist_id, user_id=current_user.id).first() or abort(404)
    return render_template('wishlist_detail.html', wl=wl)


@app.route('/wishlists/save', methods=['GET', 'POST'])
@login_required
def wishlist_save():
    listing_id = parse_int(request.values.get('listing_id'), 0, 0, 10 ** 19)
    listing = db.session.get(Listing, listing_id) or abort(404)
    lists = (Wishlist.query.filter_by(user_id=current_user.id)
             .order_by(Wishlist.created_at.desc(), Wishlist.id.desc()).all())
    back = safe_next(request.values.get('next')) or f'/rooms/{listing.id}'
    if request.method == 'POST':
        name = (request.form.get('new_name') or '').strip()
        if name:
            if len(name) > 50:
                flash('Wishlist names can be up to 50 characters.', 'error')
                return redirect(url_for('wishlist_save', listing_id=listing.id, next=back))
            wl = Wishlist(user_id=current_user.id, name=name, created_at=mirror_now())
            db.session.add(wl)
            db.session.flush()
        else:
            wl = Wishlist.query.filter_by(id=parse_int(request.form.get('wishlist_id'), 0, 0, 10 ** 9),
                                          user_id=current_user.id).first()
            if not wl:
                flash('Choose a wishlist or create a new one.', 'error')
                return redirect(url_for('wishlist_save', listing_id=listing.id, next=back))
        if not WishlistItem.query.filter_by(wishlist_id=wl.id, listing_id=listing.id).first():
            db.session.add(WishlistItem(wishlist_id=wl.id, listing_id=listing.id,
                                        added_at=mirror_now()))
        db.session.commit()
        flash(f'Saved to {wl.name}', 'success')
        return redirect(back)
    return render_template('wishlist_save.html', listing=listing, lists=lists, back=back)


@app.route('/wishlists/<int:wishlist_id>/remove', methods=['POST'])
@login_required
def wishlist_remove(wishlist_id):
    wl = Wishlist.query.filter_by(id=wishlist_id, user_id=current_user.id).first() or abort(404)
    listing_id = parse_int(request.form.get('listing_id'), 0, 0, 10 ** 19)
    item = WishlistItem.query.filter_by(wishlist_id=wl.id, listing_id=listing_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash(f'Removed from {wl.name}', 'success')
    return redirect(safe_next(request.form.get('next')) or url_for('wishlist_detail', wishlist_id=wl.id))


@app.route('/wishlists/unsave', methods=['POST'])
@login_required
def wishlist_unsave():
    """Heart toggle: remove a listing from every wishlist of the user."""
    listing_id = parse_int(request.form.get('listing_id'), 0, 0, 10 ** 19)
    items = (WishlistItem.query.join(Wishlist, Wishlist.id == WishlistItem.wishlist_id)
             .filter(Wishlist.user_id == current_user.id, WishlistItem.listing_id == listing_id).all())
    for item in items:
        db.session.delete(item)
    if items:
        db.session.commit()
        flash('Removed from wishlist', 'success')
    return redirect(safe_next(request.form.get('next')) or url_for('wishlists'))


@app.route('/wishlists/<int:wishlist_id>/note', methods=['POST'])
@login_required
def wishlist_note(wishlist_id):
    wl = Wishlist.query.filter_by(id=wishlist_id, user_id=current_user.id).first() or abort(404)
    listing_id = parse_int(request.form.get('listing_id'), 0, 0, 10 ** 19)
    item = WishlistItem.query.filter_by(wishlist_id=wl.id, listing_id=listing_id).first() or abort(404)
    item.note = (request.form.get('note') or '').strip()[:250] or None
    db.session.commit()
    flash('Note saved', 'success')
    return redirect(url_for('wishlist_detail', wishlist_id=wl.id))


@app.route('/wishlists/<int:wishlist_id>/settings', methods=['GET', 'POST'])
@login_required
def wishlist_settings(wishlist_id):
    wl = Wishlist.query.filter_by(id=wishlist_id, user_id=current_user.id).first() or abort(404)
    if request.method == 'POST':
        if request.form.get('action') == 'delete':
            name = wl.name
            db.session.delete(wl)
            db.session.commit()
            flash(f'Deleted {name}', 'success')
            return redirect(url_for('wishlists'))
        name = (request.form.get('name') or '').strip()
        if not name or len(name) > 50:
            flash('Wishlist names must be 1–50 characters.', 'error')
        else:
            wl.name = name
            db.session.commit()
            flash('Wishlist renamed', 'success')
            return redirect(url_for('wishlist_detail', wishlist_id=wl.id))
    return render_template('wishlist_settings.html', wl=wl)


# --------------------------------------------------------------- messages ---

@app.route('/guest/inbox')
@login_required
def inbox():
    view = request.args.get('filter', 'all')
    q = MessageThread.query.filter_by(user_id=current_user.id)
    if view == 'archived':
        q = q.filter_by(archived=True)
    else:
        q = q.filter_by(archived=False)
        if view == 'unread':
            q = q.filter_by(unread=True)
    threads = q.order_by(MessageThread.updated_at.desc(), MessageThread.id.desc()).all()
    return render_template('inbox.html', threads=threads, view=view, active=None)


@app.route('/guest/messages/<int:thread_id>', methods=['GET', 'POST'])
@login_required
def thread(thread_id):
    th = MessageThread.query.filter_by(id=thread_id, user_id=current_user.id).first() or abort(404)
    if request.method == 'POST':
        action = request.form.get('action', 'send')
        if action == 'archive':
            th.archived = not th.archived
            db.session.commit()
            flash('Conversation archived' if th.archived else 'Conversation restored', 'success')
            return redirect(url_for('inbox'))
        body = (request.form.get('body') or '').strip()
        if not body:
            flash('Type a message first.', 'error')
        else:
            db.session.add(Message(thread_id=th.id, sender='guest', body=body[:4000],
                                   sent_at=mirror_now()))
            th.updated_at = mirror_now()
            db.session.commit()
        return redirect(url_for('thread', thread_id=th.id))
    if th.unread:
        th.unread = False
        db.session.commit()
    threads = (MessageThread.query.filter_by(user_id=current_user.id, archived=th.archived)
               .order_by(MessageThread.updated_at.desc(), MessageThread.id.desc()).all())
    return render_template('inbox.html', threads=threads, view='archived' if th.archived else 'all',
                           active=th)


@app.route('/contact_host/<int:listing_id>/send_message', methods=['GET', 'POST'])
@login_required
def contact_host(listing_id):
    listing = db.session.get(Listing, listing_id) or abort(404)
    existing = MessageThread.query.filter_by(user_id=current_user.id, listing_id=listing.id).first()
    if request.method == 'POST':
        body = (request.form.get('body') or '').strip()
        if len(body) < 2:
            flash('Write a message to the host.', 'error')
            return redirect(url_for('contact_host', listing_id=listing.id))
        th = existing
        if not th:
            th = MessageThread(user_id=current_user.id, host_id=listing.host_id,
                               listing_id=listing.id, updated_at=mirror_now())
            db.session.add(th)
            db.session.flush()
        db.session.add(Message(thread_id=th.id, sender='guest', body=body[:4000], sent_at=mirror_now()))
        th.updated_at = mirror_now()
        th.archived = False
        db.session.commit()
        flash(f'Message sent to {listing.host.first_name}', 'success')
        return redirect(url_for('thread', thread_id=th.id))
    return render_template('contact_host.html', listing=listing, existing=existing)


# ---------------------------------------------------------------- account ---

@app.route('/account-settings')
@login_required
def account_settings():
    return render_template('account_settings.html')


@app.route('/account')
@login_required
def account():
    return redirect(url_for('account_settings'))


@app.route('/account/edit')
@login_required
def account_edit():
    return redirect(url_for('personal_info'))


PERSONAL_FIELDS = ('first_name', 'last_name', 'preferred_name', 'phone', 'street', 'apt', 'city',
                   'state', 'postal_code', 'country', 'emergency_contact')


@app.route('/account-settings/personal-info', methods=['GET', 'POST'])
@login_required
def personal_info():
    if request.method == 'POST':
        data = {f: (request.form.get(f) or '').strip() for f in PERSONAL_FIELDS}
        email = (request.form.get('email') or '').strip().lower()
        if not data['first_name'] or not data['last_name']:
            flash('Legal first and last name are required.', 'error')
            return render_template('personal_info.html', form=request.form), 400
        if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
            flash('Enter a valid email address.', 'error')
            return render_template('personal_info.html', form=request.form), 400
        clash = User.query.filter(db.func.lower(User.email) == email, User.id != current_user.id).first()
        if clash:
            flash('That email is already used by another account.', 'error')
            return render_template('personal_info.html', form=request.form), 400
        for key, value in data.items():
            setattr(current_user, key, value or None if key not in ('first_name', 'last_name') else value)
        current_user.email = email
        db.session.commit()
        flash('Personal info saved', 'success')
        return redirect(url_for('personal_info'))
    return render_template('personal_info.html', form=None)


@app.route('/account-settings/payments/payment-methods', methods=['GET', 'POST'])
@login_required
def payments():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            card, error = add_card_from_form(current_user, request.form)
            if error:
                db.session.rollback()
                flash(error, 'error')
            else:
                if request.form.get('make_default') == 'on':
                    for c in PaymentMethod.query.filter_by(user_id=current_user.id).all():
                        c.is_default = c.id == card.id
                db.session.commit()
                flash(f'{card.label} added', 'success')
        else:
            card = PaymentMethod.query.filter_by(id=parse_int(request.form.get('card_id'), 0, 0, 10 ** 9),
                                                 user_id=current_user.id).first() or abort(404)
            if action == 'default':
                for c in PaymentMethod.query.filter_by(user_id=current_user.id).all():
                    c.is_default = c.id == card.id
                db.session.commit()
                flash(f'{card.label} is now your default payment method', 'success')
            elif action == 'remove':
                upcoming = Reservation.query.filter(
                    Reservation.payment_method_id == card.id, Reservation.status.in_(('confirmed', 'pending')),
                    Reservation.checkout > MIRROR_TODAY).count()
                if upcoming:
                    flash('This card is used for an upcoming reservation and can’t be removed.', 'error')
                else:
                    was_default = card.is_default
                    label = card.label
                    db.session.delete(card)
                    db.session.flush()
                    if was_default:
                        nxt = (PaymentMethod.query.filter_by(user_id=current_user.id)
                               .order_by(PaymentMethod.id).first())
                        if nxt:
                            nxt.is_default = True
                    db.session.commit()
                    flash(f'{label} removed', 'success')
        return redirect(url_for('payments'))
    cards = (PaymentMethod.query.filter_by(user_id=current_user.id)
             .order_by(PaymentMethod.is_default.desc(), PaymentMethod.id).all())
    history = (Reservation.query.filter_by(user_id=current_user.id)
               .order_by(Reservation.created_at.desc(), Reservation.id.desc()).all())
    return render_template('payments.html', cards=cards, history=history)


@app.route('/account-settings/login-and-security', methods=['GET', 'POST'])
@login_required
def login_security():
    if request.method == 'POST':
        current = request.form.get('current_password', '')
        new = request.form.get('new_password', '')
        confirm = request.form.get('confirm_password', '')
        if not bcrypt.check_password_hash(current_user.password_hash, current):
            flash('Current password is incorrect.', 'error')
        elif len(new) < 8:
            flash('Password must be at least 8 characters.', 'error')
        elif new != confirm:
            flash('Passwords don’t match.', 'error')
        elif new == current:
            flash('Choose a password you haven’t used before.', 'error')
        else:
            current_user.password_hash = bcrypt.generate_password_hash(new).decode()
            db.session.commit()
            flash('Password updated', 'success')
        return redirect(url_for('login_security'))
    return render_template('login_security.html')


@app.route('/users/profile', methods=['GET', 'POST'])
@login_required
def my_profile():
    if request.method == 'POST':
        current_user.about = (request.form.get('about') or '').strip()[:1000] or None
        current_user.lives_in = (request.form.get('lives_in') or '').strip()[:120] or None
        current_user.work = (request.form.get('work') or '').strip()[:120] or None
        current_user.languages = (request.form.get('languages') or '').strip()[:160] or None
        db.session.commit()
        flash('Profile updated', 'success')
        return redirect(url_for('my_profile'))
    my_reviews = (Review.query.filter_by(user_id=current_user.id)
                  .order_by(Review.created.desc(), Review.id.desc()).all())
    trips_done = Reservation.query.filter(Reservation.user_id == current_user.id,
                                          Reservation.status == 'confirmed',
                                          Reservation.checkout <= MIRROR_TODAY).count()
    return render_template('my_profile.html', my_reviews=my_reviews, trips_done=trips_done)


# ------------------------------------------------------------------- auth ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter(db.func.lower(User.email) == email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=request.form.get('remember') == 'on')
            return redirect(safe_next(request.args.get('next')) or url_for('index'))
        flash('Invalid email or password.', 'error')
    return render_template('login.html')


@app.route('/signup_login')
def signup_login():
    return redirect(url_for('login', next=request.args.get('next')))


@app.route('/register', methods=['GET', 'POST'])
@app.route('/signup', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        first = (request.form.get('first_name') or '').strip()
        last = (request.form.get('last_name') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        error = None
        if not first or not last:
            error = 'Enter your first and last name as they appear on your ID.'
        elif not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
            error = 'Enter a valid email.'
        elif User.query.filter(db.func.lower(User.email) == email).first():
            error = 'An account with this email already exists. Log in instead.'
        elif len(password) < 8:
            error = 'Password must be at least 8 characters.'
        elif password != confirm:
            error = 'Passwords don’t match.'
        if error:
            flash(error, 'error')
            return render_template('register.html', form=request.form), 400
        user = User(first_name=first, last_name=last, email=email,
                    password_hash=bcrypt.generate_password_hash(password).decode(),
                    joined=MIRROR_TODAY)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(f'Welcome to Airbnb, {first}!', 'success')
        return redirect(url_for('index'))
    return render_template('register.html', form={})


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# ------------------------------------------------------------------- help ---

@app.route('/help')
def help_home():
    audience = request.args.get('audience', 'guest')
    if audience not in ('guest', 'host'):
        audience = 'guest'
    articles = (HelpArticle.query.filter(HelpArticle.audience.in_((audience, 'all')))
                .order_by(HelpArticle.position).all())
    groups = {}
    for a in articles:
        groups.setdefault(a.category, []).append(a)
    return render_template('help_home.html', groups=groups, audience=audience)


@app.route('/help/article/<int:article_id>')
def help_article(article_id):
    article = db.session.get(HelpArticle, article_id) or abort(404)
    related = (HelpArticle.query.filter(HelpArticle.category == article.category,
                                        HelpArticle.id != article.id)
               .order_by(HelpArticle.position).limit(5).all())
    return render_template('help_article.html', article=article, related=related)


def help_search_results(q):
    tokens = tokenize(q)
    if not tokens:
        return []
    scored = []
    for a in HelpArticle.query.order_by(HelpArticle.position).all():
        title = set(tokenize(a.title))
        body = set(tokenize(a.summary or '') + tokenize(' '.join(
            ' '.join([b.get('text', '')] + list(b.get('items') or [])) if isinstance(b, dict) else str(b)
            for b in a.blocks)))
        score = sum(3 if t in title else (1 if t in body else 0) for t in tokens)
        if score:
            scored.append((score, a))
    scored.sort(key=lambda sa: (-sa[0], sa[1].position))
    return [a for _, a in scored]


@app.route('/help/search')
def help_search():
    q = (request.args.get('q') or '').strip()
    return render_template('help_search.html', q=q, results=help_search_results(q) if q else [])


@app.route('/search')
def site_search():
    """Site-wide scored search across stays, hosts and Help Center articles."""
    q = (request.args.get('q') or '').strip()
    listings, hosts, articles = [], [], []
    if q:
        state = search_state(request.args)
        state['query'] = q
        _, listings = run_search(state)
        tokens = set(tokenize(q))
        for h in Host.query.order_by(Host.id).all():
            if tokens & set(tokenize(h.first_name)):
                hosts.append(h)
        articles = help_search_results(q)
    return render_template('site_search.html', q=q, listings=listings[:24],
                           listing_total=len(listings), hosts=hosts[:12], articles=articles[:10])


# ---------------------------------------------------------- content pages ---

@app.route('/host/homes')
def host_homes():
    """'Airbnb it' earnings estimate: median nightly rate of comparable
    entire-home listings in the chosen city times the nights hosted."""
    cities = City.query.order_by(City.position).all()
    city = next((c for c in cities if c.slug == request.args.get('city')), cities[0] if cities else None)
    nights = parse_int(request.args.get('nights'), 7, 1, 30)
    bedrooms = parse_int(request.args.get('bedrooms'), 1, 1, 6)
    estimate = nightly = sample = None
    if city:
        prices = sorted(l.nightly_price for l in Listing.query.filter_by(
            city_id=city.id, room_type='Entire home').all() if max(l.bedrooms, 1) == bedrooms)
        if not prices:
            prices = sorted(l.nightly_price for l in Listing.query.filter_by(
                city_id=city.id, room_type='Entire home').all())
        if prices:
            mid = len(prices) // 2
            nightly = prices[mid] if len(prices) % 2 else money(Decimal(prices[mid - 1] + prices[mid]) / 2)
            estimate = nightly * nights
            sample = len(prices)
    return render_template('host_homes.html', cities=cities, city=city, nights=nights,
                           bedrooms=bedrooms, estimate=estimate, nightly=nightly, sample=sample)


@app.errorhandler(404)
def not_found(_):
    return render_template('404.html'), 404


@app.route('/_health')
def health():
    try:
        counts = {
            'listings': Listing.query.count(),
            'hosts': Host.query.count(),
            'photos': ListingPhoto.query.count(),
            'reviews': Review.query.count(),
            'users': User.query.count(),
            'help_articles': HelpArticle.query.count(),
        }
        ok = counts['listings'] >= 100 and counts['users'] >= 4 and counts['help_articles'] >= 10
        return jsonify({'ok': ok, 'site': 'airbnb', 'counts': counts}), (200 if ok else 500)
    except Exception as exc:  # pragma: no cover - surfaced to the control plane
        return jsonify({'ok': False, 'site': 'airbnb', 'error': str(exc)}), 500


# ------------------------------------------------------------------- seed ---

from seed_catalog import seed_benchmark_users, seed_database  # noqa: E402


def create_schema() -> None:
    db.create_all()
    with db.engine.begin() as conn:
        for stmt in INDEX_STATEMENTS:
            conn.execute(db.text(stmt))


with app.app_context():
    create_schema()
    seed_database()
    seed_benchmark_users()


def main() -> None:
    with app.app_context():
        create_schema()
        seed_database()
        seed_benchmark_users()
    print('seeded')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
