// Booked nights for the website calendar, read from the private Airbnb calendar export.
// The export URL is a secret (it opens the host's calendar), so it lives in an environment
// variable and is never logged or sent to the browser; only date ranges leave this function.

import { addDays, todayIn } from '../assets/js/dates.mjs';
import { parseEvents, toBookedRanges } from './ical.mjs';

export const CALENDAR_ENV = 'AIRBNB_ICAL_URI';
export const TIME_ZONE = 'Europe/Rome';
export const HORIZON_DAYS = 550;
const TIMEOUT_MS = 8000;
const MAX_CHARACTERS = 2_000_000;

// Vercel's CDN keeps a good answer for an hour, then serves it while refreshing in the
// background, and keeps serving it for a day if Airbnb is down.
export const CACHE_OK = 'public, s-maxage=3600, stale-while-revalidate=86400, stale-if-error=86400';
export const CACHE_NONE = 'no-store';

export class UpstreamError extends Error {}

/** The configured calendar URL, or null when it is missing or not an https URL. */
export function calendarUrl(env) {
  const raw = env[CALENDAR_ENV]?.trim();
  if (!raw) return null;
  try {
    const url = new URL(raw);
    return url.protocol === 'https:' ? url : null;
  } catch {
    return null;
  }
}

export async function fetchCalendar(url, fetchImpl) {
  const response = await fetchImpl(url, {
    headers: { Accept: 'text/calendar' },
    signal: AbortSignal.timeout(TIMEOUT_MS),
  });
  if (!response.ok) throw new UpstreamError(`calendar export answered HTTP ${response.status}`);
  const text = await response.text();
  if (text.length > MAX_CHARACTERS) throw new UpstreamError('calendar export is unexpectedly large');
  if (!text.includes('BEGIN:VCALENDAR')) throw new UpstreamError('calendar export is not an iCalendar file');
  return text;
}

export function availability(calendarText, now) {
  const today = todayIn(TIME_ZONE, now);
  const until = addDays(today, HORIZON_DAYS);
  return {
    booked: toBookedRanges(parseEvents(calendarText), { today, horizonEnd: until }),
    until,
    updated: now.toISOString(),
  };
}

function jsonResponse(body, status, cacheControl, headers = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': cacheControl, ...headers },
  });
}

export async function handleAvailability(request, { env, fetchImpl, now, log = console }) {
  if (request.method !== 'GET' && request.method !== 'HEAD') {
    return jsonResponse({ error: 'method_not_allowed' }, 405, CACHE_NONE, { Allow: 'GET, HEAD' });
  }
  const url = calendarUrl(env);
  if (!url) {
    log.error(`availability: ${CALENDAR_ENV} is missing or is not an https URL`);
    return jsonResponse({ error: 'not_configured' }, 503, CACHE_NONE);
  }
  try {
    const text = await fetchCalendar(url, fetchImpl);
    return jsonResponse(availability(text, now), 200, CACHE_OK);
  } catch (error) {
    // The message only: a fetch error can carry the request, and the URL is a secret.
    log.error(`availability: could not read the Airbnb calendar (${error.name}: ${error.message})`);
    return jsonResponse({ error: 'upstream_unavailable' }, 502, CACHE_NONE);
  }
}
