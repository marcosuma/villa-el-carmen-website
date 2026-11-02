import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { addDays, fromISODate, isISODate, nightsBetween, todayIn } from '../../assets/js/dates.mjs';

describe('dates', () => {
  it('adds days across month, year and daylight-saving boundaries', () => {
    assert.equal(addDays('2027-01-31', 1), '2027-02-01');
    assert.equal(addDays('2026-12-31', 1), '2027-01-01');
    assert.equal(addDays('2027-03-27', 2), '2027-03-29');
    assert.equal(addDays('2027-03-01', -1), '2027-02-28');
  });

  it('counts nights between dates', () => {
    assert.equal(nightsBetween('2027-05-01', '2027-05-08'), 7);
    assert.equal(nightsBetween('2027-10-30', '2027-11-01'), 2);
  });

  it('rejects malformed and impossible dates', () => {
    assert.throws(() => fromISODate('2027-02-30'), RangeError);
    assert.throws(() => fromISODate('20270201'), RangeError);
    assert.equal(isISODate('2027-02-28'), true);
    assert.equal(isISODate('2027-13-01'), false);
    assert.equal(isISODate(20270201), false);
  });

  it("gives today's date in Rome, not in UTC", () => {
    const lateEveningUtc = new Date('2027-06-30T22:30:00Z');
    assert.equal(todayIn('Europe/Rome', lateEveningUtc), '2027-07-01');
    assert.equal(todayIn('UTC', lateEveningUtc), '2027-06-30');
  });
});
