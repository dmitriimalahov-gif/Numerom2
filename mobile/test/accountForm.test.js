const {test} = require('node:test');
const assert = require('node:assert/strict');
const {profileDraft, profilePatch, profileError, registrationError} = require('../src/lib/accountForm');

test('editing city preserves full and separate multi-part names', () => {
  const original = profileDraft({full_name: 'Анна Мария де ла Крус', name: 'Anna Maria', surname: 'de la Cruz', birth_date: '29.02.2000', city: 'Москва'});
  assert.deepEqual(profilePatch({...original, city: ' Кишинёв '}, original), {city: 'Кишинёв'});
  assert.deepEqual(profilePatch({...original, name: 'Ana Maria'}, original), {name: 'Ana Maria'});
});

test('legacy full-name-only profiles are never split or silently written to other fields', () => {
  const original = profileDraft({full_name: 'Иван Петрович Иванов', birth_date: '01.01.1990'});
  assert.equal(original.name, '');
  assert.equal(original.surname, '');
  assert.deepEqual(profilePatch(original, original), {});
  assert.deepEqual(profilePatch({...original, birth_date: '02.01.1990'}, original), {birth_date: '02.01.1990'});
  assert.equal(profileError(original), '');
});

test('profile validation keeps native-script names and rejects impossible or future dates', () => {
  const original = profileDraft({full_name: 'Иван Иванов', name: 'Иван', surname: 'Иванов', birth_date: '29.02.2000'});
  assert.equal(profileError(original), '');
  assert.ok(profileError({...original, birth_date: '29.02.2001'}));
  assert.ok(profileError({...original, birth_date: '01.01.2999'}));
  assert.ok(profileError({...original, full_name: ' ', name: ''}));
});

test('profile changes trim fields and allow an explicit optional-field clear', () => {
  const original = profileDraft({full_name: 'Jane Doe', name: 'Jane', surname: 'Doe', city: 'Paris'});
  assert.deepEqual(profilePatch({...original, name: ' Jane ', surname: ' '}, original), {surname: ''});
});

const signup = {email: ' person@example.com ', full_name: 'Иван Иванов', birth_date: '29.02.2000', password: 'password', confirmation: 'password'};
test('signup validates confirmation and UTF-8 bcrypt boundaries without rejecting legacy 8-character minimum', () => {
  assert.equal(registrationError(signup), '');
  assert.ok(registrationError({...signup, confirmation: 'different'}));
  assert.ok(registrationError({...signup, password: 'short', confirmation: 'short'}));
  for (const password of ['a'.repeat(72), 'я'.repeat(36), '😀'.repeat(18)]) {
    assert.equal(registrationError({...signup, password, confirmation: password}), '');
  }
  for (const password of ['a'.repeat(73), 'я'.repeat(37), '😀'.repeat(19), 'long\ud800password']) {
    assert.ok(registrationError({...signup, password, confirmation: password}));
  }
});

test('signup requires email, complete display name and a real birth date', () => {
  assert.ok(registrationError({...signup, email: 'not-an-email'}));
  assert.ok(registrationError({...signup, full_name: ' '}));
  assert.ok(registrationError({...signup, birth_date: '31.04.2000'}));
  assert.equal(registrationError({...signup, birth_date: ' 29.02.2000 '}), '');
});


test('report extras and birth city are optional independent profile fields',()=>{
 const original=profileDraft({full_name:'Jane Doe',birth_date:'01.01.1990',city:'Paris',birth_city:'London',birth_city_id:'123',phone_number:'+123456789'});
 assert.deepEqual(profilePatch({...original,birth_city:'Village',birth_city_id:'',phone_number:'',house_number:' 12 ',car_number:' AB123 '},original),{birth_city:'Village',birth_city_id:'',phone_number:'',house_number:'12',car_number:'AB123'});
 assert.equal(profileError(original),'');
});
