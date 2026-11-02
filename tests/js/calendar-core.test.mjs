import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import {
  airbnbStayUrl, canArrive, canDepart, compareMonths, dayState, firstArrivalDate, monthCells, nextBookedNight, nights,
  normaliseRanges, plural, selectDate, shiftMonth,
} from '../../assets/js/calendar-core.mjs';

// Booked: nights of 10-14 May (check-out 15th) and 20-24 May (check-out 25th).
const context = {
  ranges: normaliseRanges([['2027-05-20', '2027-05-25'], ['2027-05-10', '2027-05-15']]),
  today: '2027-05-05',
  until: '2028-11-01',
};
const empty = { arrival: null, departure: null };

describe('normaliseRanges', () => {
  it('sorts valid pairs and drops malformed ones', () => {
    const ranges = normaliseRanges([['2027-06-01', '2027-06-03'], ['2027-05-01', '2027-05-02'], ['bad', '2027-01-01'], ['2027-07-02', '2027-07-01'], 'x']);
    assert.deepEqual(ranges, [{ start: '2027-05-01', end: '2027-05-02' }, { start: '2027-06-01', end: '2027-06-03' }]);
    assert.deepEqual(normaliseRanges(null), []);
  });
});

describe('arrival and departure rules', () => {
  it('allows arriving on a free night from today until the horizon', () => {
    assert.equal(canArrive(context, '2027-05-04'), false, 'past');
    assert.equal(canArrive(context, '2027-05-05'), true, 'today');
    assert.equal(canArrive(context, '2027-05-12'), false, 'booked night');
    assert.equal(canArrive(context, '2027-05-15'), true, 'check-out day of a stay');
    assert.equal(canArrive(context, '2028-11-01'), false, 'beyond the known calendar');
  });

  it('allows departing on the next check-in day but not past it', () => {
    assert.equal(nextBookedNight(context.ranges, '2027-05-06'), '2027-05-10');
    assert.equal(canDepart(context, '2027-05-06', '2027-05-10'), true);
    assert.equal(canDepart(context, '2027-05-06', '2027-05-11'), false);
    assert.equal(canDepart(context, '2027-05-06', '2027-05-06'), false);
    assert.equal(canDepart(context, '2027-05-25', '2027-07-01'), true);
    assert.equal(canDepart(context, '2028-10-25', '2028-11-02'), false);
  });
});

describe('firstArrivalDate', () => {
  it('skips a closed season to the first free night', () => {
    const winter = { ranges: normaliseRanges([['2026-11-02', '2027-04-10']]), today: '2026-11-02', until: '2028-05-01' };
    assert.equal(firstArrivalDate(winter), '2027-04-10');
    assert.equal(firstArrivalDate(context), '2027-05-05');
  });

  it('returns null when nothing is free before the horizon', () => {
    const full = { ranges: normaliseRanges([['2027-01-01', '2027-03-01']]), today: '2027-01-01', until: '2027-03-01' };
    assert.equal(firstArrivalDate(full), null);
  });
});

describe('selectDate', () => {
  it('picks arrival, then departure, then starts over', () => {
    const arrived = selectDate(empty, '2027-05-15', context);
    assert.deepEqual(arrived, { arrival: '2027-05-15', departure: null });
    const stay = selectDate(arrived, '2027-05-20', context);
    assert.deepEqual(stay, { arrival: '2027-05-15', departure: '2027-05-20' });
    assert.deepEqual(selectDate(stay, '2027-06-01', context), { arrival: '2027-06-01', departure: null });
  });

  it('moves the arrival when an earlier or unreachable free date is clicked', () => {
    const arrived = { arrival: '2027-05-07', departure: null };
    assert.deepEqual(selectDate(arrived, '2027-05-06', context), { arrival: '2027-05-06', departure: null });
    assert.deepEqual(selectDate(arrived, '2027-05-16', context), { arrival: '2027-05-16', departure: null });
  });

  it('ignores clicks on booked nights that cannot end the stay', () => {
    const arrived = { arrival: '2027-05-07', departure: null };
    assert.equal(selectDate(arrived, '2027-05-12', context), arrived);
    assert.equal(selectDate(empty, '2027-05-12', context), empty);
  });
});

describe('dayState', () => {
  it('enables the check-in day of the next stay only as a departure', () => {
    assert.equal(dayState('2027-05-10', empty, context).disabled, true);
    const choosing = { arrival: '2027-05-07', departure: null };
    assert.deepEqual(dayState('2027-05-10', choosing, context), { booked: true, disabled: false, selected: false, inRange: false });
    assert.equal(dayState('2027-05-11', choosing, context).disabled, true);
  });

  it('marks the selected stay', () => {
    const stay = { arrival: '2027-05-15', departure: '2027-05-18' };
    assert.equal(dayState('2027-05-15', stay, context).selected, true);
    assert.equal(dayState('2027-05-16', stay, context).inRange, true);
    assert.equal(dayState('2027-05-18', stay, context).inRange, false);
    assert.equal(nights(stay), 3);
  });
});

describe('month helpers', () => {
  it('lays out a month Monday-first', () => {
    const may2027 = monthCells(2027, 4);
    assert.equal(may2027.indexOf('2027-05-01'), 5, '1 May 2027 is a Saturday');
    assert.equal(may2027.at(-1), '2027-05-31');
    assert.equal(monthCells(2027, 1).filter(Boolean).length, 28);
    assert.equal(monthCells(2028, 1).filter(Boolean).length, 29);
  });

  it('shifts months across years', () => {
    assert.deepEqual(shiftMonth({ year: 2027, month: 11 }, 1), { year: 2028, month: 0 });
    assert.deepEqual(shiftMonth({ year: 2027, month: 0 }, -1), { year: 2026, month: 11 });
    assert.equal(compareMonths({ year: 2027, month: 0 }, { year: 2026, month: 11 }) > 0, true);
  });
});

describe('airbnbStayUrl', () => {
  const listing = 'https://www.airbnb.it/rooms/1205785008353242688';

  it('adds the stay and guests to the listing link', () => {
    const url = new URL(airbnbStayUrl(listing, { arrival: '2027-05-15', departure: '2027-05-20' }, 4));
    assert.equal(url.origin + url.pathname, listing);
    assert.equal(url.searchParams.get('check_in'), '2027-05-15');
    assert.equal(url.searchParams.get('check_out'), '2027-05-20');
    assert.equal(url.searchParams.get('adults'), '4');
  });

  it('leaves the dates out until the stay is complete', () => {
    const url = new URL(airbnbStayUrl(listing, { arrival: '2027-05-15', departure: null }, 2));
    assert.equal(url.searchParams.has('check_in'), false);
    assert.equal(url.searchParams.get('adults'), '2');
  });
});

describe('plural', () => {
  const forms = { one: '{n} night', other: '{n} nights' };

  it('uses the language plural rules', () => {
    assert.equal(plural(forms, 1, 'en'), '1 night');
    assert.equal(plural(forms, 7, 'en'), '7 nights');
    assert.equal(plural({ one: '{n} nuit', other: '{n} nuits' }, 1, 'fr'), '1 nuit');
  });
});
