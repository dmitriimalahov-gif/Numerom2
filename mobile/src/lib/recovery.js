function recoveryToken(url) {
  if (typeof url !== 'string') return '';
  const hash = url.indexOf('#');
  if (hash < 0) return '';
  const value = new URLSearchParams(url.slice(hash + 1)).get('token') || '';
  return /^[A-Za-z0-9_-]{43}$/.test(value) ? value : '';
}

function passwordError(password, confirmation) {
  if (password !== confirmation) return 'Пароли не совпадают';
  let bytes;
  try { bytes = encodeURIComponent(password).replace(/%[A-F\d]{2}/gi, 'x').length; }
  catch { return 'Пароль содержит недопустимый символ'; }
  if (password.length < 12 || bytes > 72) return 'Используйте от 12 символов, не более 72 байт.';
  return '';
}

module.exports = {recoveryToken, passwordError};
