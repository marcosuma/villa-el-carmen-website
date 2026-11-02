// Pure logic behind the availability calendar: no DOM, so it can be unit tested with node --test.
//
// Booked ranges are [start, end) pairs of nights, as returned by /api/availability/: a range
// ["2027-05-01", "2027-05-08"] means the nights of 1-7 May are taken and 8 May is the check-out
// day, which is free for a new arrival and valid as a departure for a stay that ends there.

import { addDays, isISODate, nightsBetween } from './dates.mjs';

/** Validate and sort the ranges from the API, dropping anything malformed. */
export function normaliseRanges(raw) {
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((pair) => Array.isArray(pair) && pair.length === 2 && pair.every(isISODate) && pair[0] < pair[1])
    .map(([start, end]) => ({ start, end }))
    .sort((a, b) => (a.start < b.start ? -1 : a.start > b.start ? 1 : 0));
}

export function isNightBooked(ranges, iso) {
  return ranges.some((range) => range.start <= iso && iso < range.end);
}

/** The first booked night after a free night, or null when the calendar is open from there on. */
export function nextBookedNight(ranges, iso) {
  const later = ranges.filter((range) => range.start > iso).map((range) => range.start);
  return later.length ? later.reduce((a, b) => (a < b ? a : b)) : null;
}

/** context: { ranges, today, until } — until is the first date the calendar knows nothing about. */
export function canArrive(context, iso) {
  return iso >= context.today && iso < context.until && !isNightBooked(context.ranges, iso);
}

export function canDepart(context, arrival, iso) {
  if (iso <= arrival || iso > context.until) return false;
  const limit = nextBookedNight(context.ranges, arrival);
  return limit === null || iso <= limit;
}

/** The selection after a click: complete the stay when possible, otherwise start a new one. */
export function selectDate(selection, iso, context) {
  const { arrival, departure } = selection;
  if (arrival && !departure && canDepart(context, arrival, iso)) return { arrival, departure: iso };
  if (canArrive(context, iso)) return { arrival: iso, departure: null };
  return selection;
}

/** The first date a guest can arrive, so the calendar opens on a month with free nights. */
export function firstArrivalDate(context) {
  for (let iso = context.today; iso < context.until; iso = addDays(iso, 1)) {
    if (canArrive(context, iso)) return iso;
  }
  return null;
}

export function dayState(iso, selection, context) {
  const { arrival, departure } = selection;
  const choosingDeparture = Boolean(arrival && !departure);
  const selectable = canArrive(context, iso) || (choosingDeparture && canDepart(context, arrival, iso));
  return {
    booked: isNightBooked(context.ranges, iso),
    disabled: !selectable,
    selected: iso === arrival || iso === departure,
    inRange: Boolean(arrival && departure && iso > arrival && iso < departure),
  };
}

export function nights(selection) {
  return selection.arrival && selection.departure ? nightsBetween(selection.arrival, selection.departure) : 0;
}

/** Days of a month laid out Monday-first, with null for the blanks before the 1st. */
export function monthCells(year, monthIndex) {
  const first = new Date(Date.UTC(year, monthIndex, 1));
  const leadingBlanks = (first.getUTCDay() + 6) % 7;
  const daysInMonth = new Date(Date.UTC(year, monthIndex + 1, 0)).getUTCDate();
  const firstIso = first.toISOString().slice(0, 10);
  const days = Array.from({ length: daysInMonth }, (_, index) => addDays(firstIso, index));
  return [...Array(leadingBlanks).fill(null), ...days];
}

export function shiftMonth({ year, month }, offset) {
  const total = year * 12 + month + offset;
  return { year: Math.floor(total / 12), month: ((total % 12) + 12) % 12 };
}

export function monthOf(iso) {
  return { year: Number(iso.slice(0, 4)), month: Number(iso.slice(5, 7)) - 1 };
}

export function compareMonths(a, b) {
  return a.year * 12 + a.month - (b.year * 12 + b.month);
}

/** Link to the listing with the stay filled in; Airbnb shows the price and enforces the minimum stay. */
export function airbnbStayUrl(listingUrl, selection, adults) {
  const url = new URL(listingUrl);
  if (selection.arrival && selection.departure) {
    url.searchParams.set('check_in', selection.arrival);
    url.searchParams.set('check_out', selection.departure);
  }
  if (adults) url.searchParams.set('adults', String(adults));
  return url.toString();
}

/** forms = { one, other } with {n} for the number; categories come from Intl.PluralRules. */
export function plural(forms, count, lang) {
  const category = new Intl.PluralRules(lang).select(count);
  return (category === 'one' ? forms.one : forms.other).replace('{n}', String(count));
}
