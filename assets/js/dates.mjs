// Calendar dates as ISO strings ("2027-05-01"), computed in UTC so that daylight-saving
// changes never shift a day. Shared by the page (calendar.mjs) and the availability function.

const DAY_MS = 86_400_000;
const ISO_DATE = /^(\d{4})-(\d{2})-(\d{2})$/;

export function fromISODate(iso) {
  const match = ISO_DATE.exec(iso);
  if (!match) throw new RangeError(`not an ISO date: ${iso}`);
  const [year, month, day] = match.slice(1).map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  if (date.getUTCMonth() !== month - 1 || date.getUTCDate() !== day) {
    throw new RangeError(`not a calendar date: ${iso}`);
  }
  return date;
}

export function toISODate(date) {
  return date.toISOString().slice(0, 10);
}

export function isISODate(value) {
  if (typeof value !== 'string') return false;
  try {
    fromISODate(value);
    return true;
  } catch {
    return false;
  }
}

export function addDays(iso, days) {
  return toISODate(new Date(fromISODate(iso).getTime() + days * DAY_MS));
}

export function nightsBetween(start, end) {
  return Math.round((fromISODate(end) - fromISODate(start)) / DAY_MS);
}

/** Today's date in a given IANA time zone, e.g. todayIn('Europe/Rome'). */
export function todayIn(timeZone, now = new Date()) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone, year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(now);
  const value = (type) => parts.find((part) => part.type === type).value;
  return `${value('year')}-${value('month')}-${value('day')}`;
}
