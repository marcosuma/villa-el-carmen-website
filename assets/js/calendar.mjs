// Availability calendar in the booking section. Booked nights come from /api/availability/;
// choosing dates updates the Airbnb button so the guest lands on the listing with the stay filled in.

import {
  airbnbStayUrl, compareMonths, dayState, firstArrivalDate, monthCells, monthOf, nights, normaliseRanges, plural,
  selectDate, shiftMonth,
} from './calendar-core.mjs';
import { addDays, isISODate } from './dates.mjs';

const TWO_MONTHS = window.matchMedia('(min-width: 768px)');

function localToday() {
  const now = new Date();
  const pad = (value) => String(value).padStart(2, '0');
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

function formatter(lang, options) {
  return new Intl.DateTimeFormat(lang, { timeZone: 'UTC', ...options });
}

async function loadAvailability(endpoint) {
  const response = await fetch(endpoint, { headers: { Accept: 'application/json' } });
  if (!response.ok) throw new Error(`availability endpoint returned HTTP ${response.status}`);
  const data = await response.json();
  if (!isISODate(data.until)) throw new Error('availability response has no "until" date');
  return { ranges: normaliseRanges(data.booked), until: data.until };
}

function setupCalendar(root) {
  const strings = JSON.parse(root.querySelector('[data-cal-strings]').textContent);
  const lang = root.dataset.lang;
  const listingUrl = root.dataset.airbnb;
  const find = (name) => root.querySelector(`[data-cal-${name}]`);
  const ui = find('ui');
  const months = find('months');
  const hint = find('hint');
  const status = find('status');
  const cta = find('cta');
  const clear = find('clear');
  const guests = find('guests');
  const defaultCta = cta.textContent;

  const monthTitle = formatter(lang, { month: 'long', year: 'numeric' });
  const fullDate = formatter(lang, { dateStyle: 'full' });
  const shortDate = formatter(lang, { day: 'numeric', month: 'short', year: 'numeric' });
  const weekdayName = formatter(lang, { weekday: 'short' });
  const weekdays = Array.from({ length: 7 }, (_, index) => weekdayName.format(new Date(Date.UTC(2024, 0, 1 + index))));

  const today = localToday();
  let context = { ranges: [], today, until: today };
  let selection = { arrival: null, departure: null };
  let view = monthOf(today);
  let lastView = view;

  function monthsShown() {
    return TWO_MONTHS.matches ? 2 : 1;
  }

  function dayButton(iso) {
    const state = dayState(iso, selection, context);
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'calendar-day';
    button.dataset.date = iso;
    button.textContent = String(Number(iso.slice(8)));
    button.disabled = state.disabled;
    button.setAttribute('aria-pressed', String(state.selected));
    button.setAttribute('aria-label', `${fullDate.format(new Date(`${iso}T00:00:00Z`))}, ${state.booked ? strings.booked : strings.available}`);
    if (state.booked) button.dataset.booked = '';
    if (state.inRange) button.dataset.inRange = '';
    return button;
  }

  function monthElement(month) {
    const wrapper = document.createElement('div');
    wrapper.className = 'calendar-month';
    const title = document.createElement('h4');
    title.textContent = monthTitle.format(new Date(Date.UTC(month.year, month.month, 1)));
    const grid = document.createElement('div');
    grid.className = 'calendar-grid';
    weekdays.forEach((name) => {
      const cell = document.createElement('span');
      cell.className = 'weekday';
      cell.setAttribute('aria-hidden', 'true');
      cell.textContent = name;
      grid.append(cell);
    });
    monthCells(month.year, month.month).forEach((iso) => {
      grid.append(iso ? dayButton(iso) : document.createElement('span'));
    });
    wrapper.append(title, grid);
    return wrapper;
  }

  function renderMonths() {
    const shown = monthsShown();
    const firstAllowed = monthOf(today);
    const lastStart = shiftMonth(lastView, 1 - shown);
    if (compareMonths(view, lastStart) > 0) view = lastStart;
    if (compareMonths(view, firstAllowed) < 0) view = firstAllowed;
    const focused = document.activeElement?.dataset?.date;
    months.replaceChildren(...Array.from({ length: shown }, (_, index) => monthElement(shiftMonth(view, index))));
    find('prev').disabled = compareMonths(view, firstAllowed) <= 0;
    find('next').disabled = compareMonths(view, lastStart) >= 0;
    if (focused) months.querySelector(`[data-date="${focused}"]`)?.focus();
  }

  function renderSummary() {
    const { arrival, departure } = selection;
    const format = (iso) => (iso ? shortDate.format(new Date(`${iso}T00:00:00Z`)) : '—');
    find('arrival').textContent = format(arrival);
    find('departure').textContent = format(departure);
    const count = nights(selection);
    find('nights').textContent = count ? plural(strings.nights, count, lang) : '';
    hint.textContent = !arrival ? strings.select_arrival : !departure ? strings.select_departure : plural(strings.nights, count, lang);
    clear.hidden = !arrival;
  }

  function renderCta() {
    cta.href = airbnbStayUrl(listingUrl, selection, Number(guests.value));
    cta.textContent = selection.departure ? strings.cta_dates : defaultCta;
  }

  function render() {
    renderMonths();
    renderSummary();
    renderCta();
  }

  months.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-date]');
    if (!button || button.disabled) return;
    selection = selectDate(selection, button.dataset.date, context);
    render();
  });
  find('prev').addEventListener('click', () => { view = shiftMonth(view, -1); renderMonths(); });
  find('next').addEventListener('click', () => { view = shiftMonth(view, 1); renderMonths(); });
  clear.addEventListener('click', () => {
    selection = { arrival: null, departure: null };
    render();
    months.querySelector('button[data-date]:not(:disabled)')?.focus();
  });
  guests.addEventListener('change', renderCta);
  TWO_MONTHS.addEventListener('change', renderMonths);
  renderCta();

  status.textContent = strings.loading;
  loadAvailability(root.dataset.endpoint)
    .then(({ ranges, until }) => {
      context = { ranges, today, until };
      lastView = monthOf(addDays(until, -1));
      view = monthOf(firstArrivalDate(context) ?? today);
      status.textContent = '';
      ui.hidden = false;
      render();
    })
    .catch((error) => {
      status.textContent = strings.error;
      console.warn('Availability calendar unavailable:', error.message);
    });
}

document.querySelectorAll('[data-calendar]').forEach(setupCalendar);
