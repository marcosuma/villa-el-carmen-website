// GET /api/availability/ — booked nights for the calendar on the booking section.
// The logic lives in lib/availability.mjs so it can be tested without Vercel.

import { handleAvailability } from '../lib/availability.mjs';

export default {
  fetch(request) {
    return handleAvailability(request, { env: process.env, fetchImpl: fetch, now: new Date() });
  },
};
