const {validateBirthDate} = require('@numerom/api-client');
const layout = [1,4,7,2,5,8,3,6,9];
const lineDigits = {
  'row-0':[1,4,7], 'row-1':[2,5,8], 'row-2':[3,6,9],
  'col-0':[1,2,3], 'col-1':[4,5,6], 'col-2':[7,8,9],
  'diag-0':[1,5,9], 'diag-1':[3,5,7],
};
const text = value => typeof value === 'string' && !!value.trim();
const count = value => Number.isSafeInteger(value) && value >= 0 && value <= 64;

// Validate server display data. Never reconstruct a missing square on the device.
function personalScheme(value, birthDate) {
  if (!value || value.version !== 1 || !validateBirthDate(value.birth_date) || value.birth_date !== birthDate
    || !text(value.method) || typeof value.note !== 'string'
    || !Array.isArray(value.additional_numbers) || value.additional_numbers.length !== 4
    || !value.additional_numbers.every(count)
    || !Array.isArray(value.cells) || value.cells.length !== 9
    || !Array.isArray(value.lines) || value.lines.length !== 8) return null;
  const cells = layout.map(digit => value.cells.filter(cell => cell && cell.digit === digit));
  if (cells.some(matches => matches.length !== 1)) return null;
  const ordered = cells.map(matches => matches[0]);
  if (!ordered.every(cell => count(cell.count) && cell.digits === String(cell.digit).repeat(cell.count)
    && text(cell.title) && text(cell.meaning))) return null;
  const lines = Object.entries(lineDigits).map(([key,digits]) => {
    const matches = value.lines.filter(line => line && line.key === key);
    const line = matches[0];
    if (matches.length !== 1 || !Array.isArray(line.digits) || line.digits.join(',') !== digits.join(',')
      || !count(line.value) || !text(line.title) || !text(line.meaning)) return null;
    // Reject contradictory display data without substituting a client result.
    const expected = digits.reduce((sum,digit) => sum + ordered.find(cell => cell.digit === digit).count,0);
    return line.value === expected ? {...line,digits:[...line.digits]} : null;
  });
  if (lines.some(line => !line)) return null;
  return {version:1,birthDate:value.birth_date,method:value.method,note:value.note,
    additionalNumbers:[...value.additional_numbers],cells:ordered.map(cell => ({...cell})),lines};
}
module.exports = {personalScheme};
