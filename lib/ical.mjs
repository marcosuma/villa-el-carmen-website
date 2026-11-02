// Minimal iCalendar (RFC 5545) reading for Airbnb's calendar export: only the dates of each
// event are kept. Summaries and descriptions (reservation links, phone digits) are ignored.

import { addDays } from '../assets/js/dates.mjs';

const DATE_PREFIX = /^(\d{4})(\d{2})(\d{2})/;

/** Undo RFC 5545 line folding: a line break followed by a space or tab continues the line. */
export function unfoldLines(text) {
  return text.replace(/\r?\n[ \t]/g, '').split(/\r?\n/);
}

function toISO(value) {
  const match = DATE_PREFIX.exec(value.trim());
  return match ? `${match[1]}-${match[2]}-${match[3]}` : null;
}

/** [{ start, end }] for every VEVENT; end is null when the event has no usable DTEND. */
export function parseEvents(text) {
  const events = [];
  let current = null;
  for (const line of unfoldLines(text)) {
    if (line === 'BEGIN:VEVENT') {
      current = { start: null, end: null };
      continue;
    }
    if (line === 'END:VEVENT') {
      if (current?.start) events.push(current);
      current = null;
      continue;
    }
    if (!current) continue;
    const colon = line.indexOf(':');
    if (colon < 0) continue;
    const name = line.slice(0, colon).split(';')[0].toUpperCase();
    if (name === 'DTSTART') current.start = toISO(line.slice(colon + 1));
    if (name === 'DTEND') current.end = toISO(line.slice(colon + 1));
  }
  return events;
}

/**
 * Booked nights as merged [start, end) pairs between today and horizonEnd.
 * DTEND is the check-out day (exclusive); an event without one blocks a single night.
 */
export function toBookedRanges(events, { today, horizonEnd }) {
  const clipped = events
    .map(({ start, end }) => ({ start, end: end && end > start ? end : addDays(start, 1) }))
    .map(({ start, end }) => ({ start: start < today ? today : start, end: end > horizonEnd ? horizonEnd : end }))
    .filter(({ start, end }) => start < end)
    .sort((a, b) => (a.start < b.start ? -1 : a.start > b.start ? 1 : 0));

  const merged = [];
  for (const range of clipped) {
    const last = merged.at(-1);
    if (last && range.start <= last.end) {
      if (range.end > last.end) last.end = range.end;
    } else {
      merged.push({ ...range });
    }
  }
  return merged.map(({ start, end }) => [start, end]);
}
