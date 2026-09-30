# Mirror notice — airbnb (www.airbnb.com)

This directory contains a functional mirror of https://www.airbnb.com/ (en-US,
USD) built for the WebHarbor offline benchmark environment. It is a benchmark
fixture, not an official Airbnb product, and it is not affiliated with or
endorsed by Airbnb, Inc.

## What is mirrored

- The home page with category browsing by destination, and the search bar
  (destination, check-in/check-out dates, guests).
- Search results with scored destination matching (including disambiguation of
  places that share a name, such as Portland, Oregon and Portland, Maine),
  listing cards with total-before-taxes prices, and the filter panel:
  type of place, nightly price range, bedrooms/beds/bathrooms, amenities,
  booking options (Instant Book, Self check-in, Free cancellation, Allows
  pets), standout stays (Guest favorite, Superhost) and property type.
- Listing pages with the photo tour, highlights, description, sleeping
  arrangements, the full amenity list, reviews with category ratings, the
  location section, house rules, safety and the cancellation policy, and a
  public host card.
- The reservation flow: price breakdown (nightly subtotal, weekly/monthly
  discounts, cleaning fee, service fee and taxes), Instant Book and
  request-to-book with a required message to the Host, saved or new cards,
  confirmation, receipts.
- Trips: upcoming, pending, past and canceled reservations; cancellation with
  a policy-based refund quote; reviews within the 14-day review window.
- Wishlists (create, save, rename, delete, notes), Messages with Hosts, account
  settings (personal info, payments & payouts, login & security), the
  "Airbnb your home" earnings estimate, and a help centre with scored search.

## Data provenance

Listing names, titles, descriptions, room/property types, capacities, bedroom,
bed and bathroom counts, nightly prices for the captured search dates, ratings
and review counts, amenity lists, highlights, sleeping arrangements,
neighbourhoods and approximate coordinates were captured from public
www.airbnb.com search-result and listing pages for 12 destinations on
2026-09-28 (see provenance.json). Listing photos are the real upstream images
fetched from the a0.muscache.com URLs referenced by those pages; every file's
source URL, byte length and SHA-256 are recorded in asset_inventory.json;
four photos the CDN served as PNG were re-encoded to JPEG (listed in the
inventory notes). Line breaks and no-break spaces in listing titles and house
rules are normalized to single spaces, as the upstream page renders them. The
Airbnb logo and favicon were taken from the upstream page header (the logo's
fill is set to the brand colour #FF385C because the inline upstream SVG
inherits its colour from the page).

## Host privacy

Only a Host's first name, public hosting statistics (Superhost status, years
hosting, rating, review count, response rate and time, identity verification)
and spoken languages are kept. Host "about", work and home-town text and Host
profile photos are not included; Hosts are shown with letter avatars.

## Mirror-authored elements

- Guest reviews are written for the mirror (upstream review text and reviewer
  names are not copied). Listing-level rating and review-count values are the
  captured upstream values, so the number of review cards shown on a listing
  can be smaller than its review count.
- Cleaning fees, weekly/monthly discounts, minimum stays and Instant Book
  flags are not published on the captured pages; they are derived
  deterministically from the listing id. Pet and self check-in flags come from
  the captured house rules, highlights and amenities. The availability
  calendar (other guests' bookings) is derived from the listing id and keeps
  the captured search dates (November 12-16, 2026) open; the service-fee and
  tax rates are mirror constants.
- Cancellation policies are mapped from the free-cancellation deadline shown
  on the captured listing page onto the mirror's four policies (Flexible,
  Moderate, Firm, Strict). Upstream non-refundable and 24-hour-only
  cancellation terms are represented as Strict. The 14 listings whose captured
  page shows no cancellation terms get a policy derived from the listing id.
- The help-centre articles are written for the mirror to document the
  mirror's own rules (fees, refunds, review window, payment methods).
- The benchmark users (alice.j@test.com, bob.c@test.com, carol.d@test.com,
  david.k@test.com), their cards, reservations, conversations, wishlists and
  reviews are benchmark fixtures.
- Reservations, messages, wishlists and account changes made at runtime are
  stored in the mirror's SQLite instance directory and reset by the control
  plane.

## Removal

Anyone whose content appears in this mirror (for example a Host who wants a
listing or its photos removed) can open an issue in the WebHarbor repository
naming the listing id; the listing rows and its photo files will be removed
from the tracked source data and the asset archive.
