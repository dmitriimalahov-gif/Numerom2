// Legacy API timestamps without an offset are UTC, as are MongoDB datetimes.
function serverDate(value) {
  if (typeof value !== 'string' || !value) return null;
  const normalized = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?$/.test(value) ? `${value}Z` : value;
  const date = new Date(normalized);
  return Number.isNaN(date.getTime()) ? null : date;
}
module.exports = {serverDate};
