import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { parseEvents, toBookedRanges, unfoldLines } from '../../lib/ical.mjs';

const AIRBNB_EXPORT = [
  'BEGIN:VCALENDAR',
  'PRODID;X-RICAL-TZSOURCE=TZINFO:-//Airbnb Inc//Hosting Calendar 1.0//EN',
  'VERSION:2.0',
  'BEGIN:VEVENT',
  'DTEND;VALUE=DATE:20270508',
  'DTSTART;VALUE=DATE:20270501',
  'UID:1418fb94e984-0b2a1c7e@airbnb.com',
  'DESCRIPTION:Reservation URL: https://www.airbnb.com/hosting/reservations/details/HMABCDEFGH\\nPhone',
  '  Number (Last 4 Digits): 1234',
  'SUMMARY:Reserved',
  'END:VEVENT',
  'BEGIN:VEVENT',
  'DTEND;VALUE=DATE:20270601',
  'DTSTART;VALUE=DATE:20270520',
  'UID:7f3b2c1d-blocked@airbnb.com',
  'SUMMARY:Airbnb (Not available)',
  'END:VEVENT',
  'END:VCALENDAR',
].join('\r\n');

describe('unfoldLines', () => {
  it('joins folded continuation lines', () => {
    assert.deepEqual(unfoldLines('DESCRIPTION:Phone\r\n  Number\r\nSUMMARY:x'), ['DESCRIPTION:Phone Number', 'SUMMARY:x']);
  });
});

describe('parseEvents', () => {
  it('keeps only the dates of each event', () => {
    assert.deepEqual(parseEvents(AIRBNB_EXPORT), [
      { start: '2027-05-01', end: '2027-05-08' },
      { start: '2027-05-20', end: '2027-06-01' },
    ]);
  });

  it('reads date-time values and events without DTEND', () => {
    const text = 'BEGIN:VEVENT\nDTSTART:20270701T150000Z\nEND:VEVENT\nBEGIN:VEVENT\nSUMMARY:no dates\nEND:VEVENT';
    assert.deepEqual(parseEvents(text), [{ start: '2027-07-01', end: null }]);
  });

  it('ignores properties outside events and lines without a value', () => {
    assert.deepEqual(parseEvents('DTSTART;VALUE=DATE:20270101\nBEGIN:VEVENT\nGARBAGE\nEND:VEVENT'), []);
  });
});

describe('toBookedRanges', () => {
  const window = { today: '2027-05-03', horizonEnd: '2028-11-01' };

  it('clips past nights and merges overlapping or back-to-back stays', () => {
    const events = [
      { start: '2027-05-01', end: '2027-05-08' },
      { start: '2027-05-08', end: '2027-05-10' },
      { start: '2027-05-09', end: '2027-05-12' },
      { start: '2027-06-01', end: '2027-06-03' },
    ];
    assert.deepEqual(toBookedRanges(events, window), [['2027-05-03', '2027-05-12'], ['2027-06-01', '2027-06-03']]);
  });

  it('drops stays that ended before today and clips at the horizon', () => {
    const events = [
      { start: '2027-04-01', end: '2027-04-05' },
      { start: '2028-10-25', end: '2028-11-20' },
    ];
    assert.deepEqual(toBookedRanges(events, window), [['2028-10-25', '2028-11-01']]);
  });

  it('treats a missing or backwards end as a single night', () => {
    const events = [
      { start: '2027-07-01', end: null },
      { start: '2027-08-10', end: '2027-08-01' },
    ];
    assert.deepEqual(toBookedRanges(events, window), [['2027-07-01', '2027-07-02'], ['2027-08-10', '2027-08-11']]);
  });

  it('never leaks anything but dates', () => {
    const output = JSON.stringify(toBookedRanges(parseEvents(AIRBNB_EXPORT), { today: '2027-01-01', horizonEnd: '2028-01-01' }));
    assert.doesNotMatch(output, /airbnb|Reserved|1234|HMABC/i);
  });
});
