import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import AdminPanelV2 from '../../../components/AdminPanelV2';
import LessonEditModal from '../../../components/LessonEditModal';
jest.mock('../../../components/AuthContext', () => ({ useAuth: () => ({ user: { id: 'admin', is_admin: true }, loading: false }) }));

let root, host, postReply, onClose;
const reply = (data, status = 200) => ({ ok: status < 400, status, json: async () => data });
const button = text => [...document.querySelectorAll('button')].find(node => node.textContent.trim() === text);
const click = async element => {
  expect(element).toBeTruthy();
  await act(async () => { element.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, button: 0 })); element.dispatchEvent(new MouseEvent('click', { bubbles: true })); });
};
const setValue = async (element, value) => {
  expect(element).toBeTruthy();
  await act(async () => {
    const type = element.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(type, 'value').set.call(element, value);
    element.dispatchEvent(new Event('input', { bubbles: true }));
  });
};
const posts = () => global.fetch.mock.calls.filter(([url,options]) => url.endsWith('/review-response/r') && options?.method === 'POST');
const comment = () => document.querySelector('textarea[placeholder="Введите комментарий для студента..."]');
const points = () => document.querySelector('input#points-r') || [...document.querySelectorAll('input[type="number"]')].find(node => node.closest('[role="tabpanel"]')?.getAttribute('data-state') === 'active');
const fetchRead = url => {
  if (url.endsWith('/admin/analytics/overview')) return reply({ pending_reviews: 1, pending_reviews_details: [{ response_id:'r',user_name:'Анна',lesson_title:'Урок',exercise_title:'Практика',response_text:'Наблюдение' }] });
  if (url.endsWith('/admin/lessons-v2')) return reply({ lessons: [] });
  if (url.includes('/admin/files?')) return reply({ files: [] });
  if (url.endsWith('/admin/analytics/lesson/lesson')) return reply({ statistics: { total_students:1,total_exercise_responses:1,pending_review:1 } });
  if (url.endsWith('/admin/analytics/student-responses/lesson')) return reply({ responses: [{ id:'r',user_name:'Анна',exercise_title:'Практика',response_text:'Наблюдение',reviewed:false }] });
  if (url.endsWith('/admin/analytics/challenge-notes/lesson')) return reply({ notes: [] });
  if (url.endsWith('/admin/lesson-files-analytics/lesson')) return reply({});
  throw new Error('Unexpected read: '+url);
};
async function renderForm(form) {
  await act(async () => root.render(form === 'dashboard' ? <AdminPanelV2 embedded /> : <LessonEditModal isOpen lesson={{id:'lesson',title:'Урок',level:1}} onClose={onClose} onSave={jest.fn()} />));
  if (form === 'lesson') { await click(button('Аналитика')); await click(button('Добавить комментарий')); }
  await setValue(comment(),'Спасибо за пример'); await setValue(points(),'30');
}
const sendButton = form => form === 'dashboard' ? button('Отправить ответ') : button('Сохранить комментарий и 30 баллов');

beforeEach(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true; localStorage.setItem('token','synthetic-admin');
  Object.defineProperty(window,'crypto',{configurable:true,value:{randomUUID:()=>require('crypto').randomUUID()}});
  host=document.createElement('div'); document.body.appendChild(host); root=createRoot(host); onClose=jest.fn();
  postReply=()=>Promise.resolve(reply({award_pending:false,points_earned:30}));
  global.fetch=jest.fn((url,options) => url.endsWith('/review-response/r') && options?.method==='POST' ? postReply() : Promise.resolve(fetchRead(url)));
});
afterEach(async () => { await act(async () => root.unmount()); host.remove(); localStorage.clear(); jest.restoreAllMocks(); });

for (const form of ['dashboard','lesson']) {
  test(`${form}: pending award keeps form and repeats the same UUID and immutable body until confirmed`, async () => {
    let resolve; postReply=()=>new Promise(yes=>{resolve=yes;});
    await renderForm(form);
    const send=sendButton(form); await click(send); await click(send);
    expect(posts()).toHaveLength(1);
    expect(comment().disabled).toBe(true); expect(points().disabled).toBe(true);
    await act(async () => resolve(reply({award_pending:true,points_earned:30})));
    expect(document.body.textContent).toContain('Проверка сохранена, начисление ожидает подтверждения');
    expect(comment().value).toBe('Спасибо за пример'); expect(button('Проверить сохранение')).toBeTruthy();
    const original=JSON.parse(posts()[0][1].body);
    expect(original.request_id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
    if (form==='lesson') {
      const cancel=[...document.querySelectorAll('button')].filter(node=>node.textContent.trim()==='Отмена');
      expect(cancel.every(node=>node.disabled)).toBe(true);
      await click(cancel[0]); expect(onClose).not.toHaveBeenCalled();
    } else expect(button('Очистить').disabled).toBe(true);
    // Even a synthetic event cannot replace the payload held by the pending attempt.
    await setValue(comment(),'Другой текст'); await setValue(points(),'90');
    postReply=()=>Promise.resolve(reply({award_pending:false,points_earned:30}));
    await click(button('Проверить сохранение'));
    expect(posts()).toHaveLength(2); expect(JSON.parse(posts()[1][1].body)).toEqual(original);
    expect(comment()).toBeNull(); expect(button('Проверить сохранение')).toBeUndefined();
  });

  test(`${form}: ambiguous network error and malformed success retain the request for retry`, async () => {
    await renderForm(form); postReply=()=>Promise.reject(new Error('network down'));
    await click(sendButton(form));
    const original=posts()[0][1].body;
    expect(document.body.textContent).toContain('Результат отправки пока не подтверждён');
    expect(comment().disabled).toBe(true);
    postReply=()=>Promise.resolve(reply({})); await click(button('Проверить сохранение'));
    expect(comment()).toBeTruthy(); expect(posts()[1][1].body).toBe(original);
    postReply=()=>Promise.resolve(reply({award_pending:false,points_earned:30})); await click(button('Проверить сохранение'));
    expect(posts()[2][1].body).toBe(original); expect(comment()).toBeNull();
  });

  test(`${form}: explicit validation rejection unlocks corrections and a new request`, async () => {
    await renderForm(form); postReply=()=>Promise.resolve(reply({detail:'Исправьте комментарий'},422));
    await click(sendButton(form)); const first=JSON.parse(posts()[0][1].body);
    expect(comment().disabled).toBe(false); expect(document.body.textContent).toContain('Исправьте комментарий');
    await setValue(comment(),'Исправленный комментарий');
    postReply=()=>Promise.resolve(reply({award_pending:false,points_earned:30})); await click(sendButton(form));
    const second=JSON.parse(posts()[1][1].body);
    expect(second.request_id).not.toBe(first.request_id); expect(second.admin_comment).toBe('Исправленный комментарий');
  });
}
