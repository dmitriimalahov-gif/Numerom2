const {validateBirthDate} = require('@numerom/api-client');

const profileFields = ['full_name', 'name', 'surname', 'birth_date', 'city', 'birth_city', 'birth_city_id', 'phone_number', 'car_number', 'house_number', 'apartment_number', 'postal_code', 'street'];

function profileDraft(user) {
  return Object.fromEntries(profileFields.map(field => [field, typeof user?.[field] === 'string' ? user[field] : '']));
}

function profilePatch(draft, baseline) {
  return Object.fromEntries(profileFields
    .filter(field => (draft[field]||'').trim() !== (baseline[field]||'').trim())
    .map(field => [field, (draft[field]||'').trim()]));
}

function profileError(draft) {
  if (!draft.full_name.trim() && !draft.name.trim()) return 'Укажите полное имя или имя в профиле.';
  if (!validateBirthDate(draft.birth_date.trim())) return 'Укажите существующую дату рождения: ДД.ММ.ГГГГ.';
  return '';
}

function registrationError({email, password, confirmation, full_name, birth_date}) {
  if (!/^\S+@\S+\.\S+$/.test(email.trim())) return 'Введите адрес электронной почты.';
  if (!full_name.trim()) return 'Укажите имя и фамилию.';
  if (!validateBirthDate(birth_date.trim())) return 'Укажите существующую дату рождения: ДД.ММ.ГГГГ.';
  if (password.length < 8) return 'Пароль должен содержать не менее 8 символов.';
  let bytes;
  try { bytes = encodeURIComponent(password).replace(/%[A-F\d]{2}/gi, 'x').length; }
  catch { return 'Пароль содержит недопустимый символ.'; }
  if (bytes > 72) return 'Пароль слишком длинный. Используйте не более 72 латинских или 36 кириллических букв.';
  if (password !== confirmation) return 'Пароли не совпадают.';
  return '';
}

module.exports = {profileDraft, profilePatch, profileError, registrationError};
