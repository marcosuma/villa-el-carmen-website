import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { CACHE_NONE, CACHE_OK, CALENDAR_ENV, calendarUrl, handleAvailability } from '../../lib/availability.mjs';

const SECRET_URL = 'https://www.airbnb.com/calendar/ical/1205785008353242688.ics?t=secret-token';
const NOW = new Date('2027-04-30T10:00:00Z');
const CALENDAR = [
  'BEGIN:VCALENDAR',
  'BEGIN:VEVENT',
  'DTSTART;VALUE=DATE:20270501',
  'DTEND;VALUE=DATE:20270508',
  'DESCRIPTION:Reservation URL: https://www.airbnb.com/hosting/reservations/details/HMXYZ',
  'SUMMARY:Reserved',
  'END:VEVENT',
  'END:VCALENDAR',
].join('\r\n');

function silentLog() {
  const lines = [];
  return { lines, error: (message) => lines.push(message) };
}

function fakeFetch(respond) {
  const calls = [];
  const fetchImpl = async (url, options) => {
    calls.push({ url: String(url), options });
    return respond();
  };
  return { calls, fetchImpl };
}

function call({ env = { [CALENDAR_ENV]: SECRET_URL }, respond, method = 'GET' } = {}) {
  const { calls, fetchImpl } = fakeFetch(respond ?? (() => new Response(CALENDAR)));
  const log = silentLog();
  const request = new Request('https://elcarmenpuglia.com/api/availability/', { method });
  return handleAvailability(request, { env, fetchImpl, now: NOW, log }).then((response) => ({ response, calls, log }));
}

describe('calendarUrl', () => {
  it('accepts only https URLs', () => {
    assert.equal(calendarUrl({ [CALENDAR_ENV]: ` ${SECRET_URL} ` }).href, SECRET_URL);
    assert.equal(calendarUrl({ [CALENDAR_ENV]: 'http://example.com/a.ics' }), null);
    assert.equal(calendarUrl({ [CALENDAR_ENV]: 'not a url' }), null);
    assert.equal(calendarUrl({}), null);
  });
});

describe('handleAvailability', () => {
  it('returns booked nights, the horizon and CDN cache headers', async () => {
    const { response, calls } = await call();
    assert.equal(response.status, 200);
    assert.equal(response.headers.get('Cache-Control'), CACHE_OK);
    assert.deepEqual(await response.json(), {
      booked: [['2027-05-01', '2027-05-08']],
      until: '2028-04-29',
      updated: '2027-04-30T10:00:00.000Z',
    });
    assert.equal(calls[0].url, SECRET_URL);
  });

  it('never exposes the secret URL or reservation details', async () => {
    const { response } = await call();
    const body = await response.text();
    assert.doesNotMatch(body, /secret-token|ical|HMXYZ|Reserved/);
  });

  it('answers 503 without calling Airbnb when the URL is not configured', async () => {
    const { response, calls, log } = await call({ env: {} });
    assert.equal(response.status, 503);
    assert.equal(response.headers.get('Cache-Control'), CACHE_NONE);
    assert.equal(calls.length, 0);
    assert.match(log.lines[0], new RegExp(CALENDAR_ENV));
  });

  it('answers 502 and logs without the URL when Airbnb fails', async () => {
    const { response, log } = await call({ respond: () => new Response('nope', { status: 500 }) });
    assert.equal(response.status, 502);
    assert.equal(response.headers.get('Cache-Control'), CACHE_NONE);
    assert.match(log.lines[0], /HTTP 500/);
    assert.doesNotMatch(log.lines.join('\n'), /secret-token/);
  });

  it('answers 502 when the export is not a calendar', async () => {
    const { response } = await call({ respond: () => new Response('<html>login</html>') });
    assert.equal(response.status, 502);
  });

  it('answers 502 when the request to Airbnb throws', async () => {
    const { response } = await call({ respond: () => { throw new TypeError('fetch failed'); } });
    assert.equal(response.status, 502);
  });

  it('rejects other methods', async () => {
    const { response, calls } = await call({ method: 'POST' });
    assert.equal(response.status, 405);
    assert.equal(response.headers.get('Allow'), 'GET, HEAD');
    assert.equal(calls.length, 0);
  });
});
