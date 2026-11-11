import React, {act} from 'react';
import {createRoot} from 'react-dom/client';
import axios from 'axios';
import PersonalNumbers from '../PersonalNumbers';

jest.mock('axios', () => ({post:jest.fn()}));
jest.mock('../AuthContext', () => ({useAuth:()=>({user:{birth_date:'10.11.1982',credits_remaining:12}})}));
let root, container, previousFetch;
beforeEach(()=>{
  global.IS_REACT_ACT_ENVIRONMENT=true;
  previousFetch=global.fetch;
  global.fetch=jest.fn().mockResolvedValue({ok:true,json:async()=>({personal_numbers:1})});
  axios.post.mockResolvedValue({data:{soul_number:1,mind_number:11,destiny_number:5,
    helping_mind_number:3,wisdom_number:null,ruling_number:5,report:{numbers:[{
      key:'mind_number',title:'Число ума',steps:['Месяц рождения: 11','Итог: 11 — мастер-число, сохраняется'],
      method:'Сводим месяц рождения, сохраняя мастер-число.',meaning:'Способ мышления.',interpretation:'Текст из серверного отчёта.',note:null,
    }]}}});
  container=document.createElement('div');document.body.appendChild(container);root=createRoot(container);
});
afterEach(async()=>{await act(async()=>root.unmount());container.remove();global.fetch=previousFetch;});
test('web uses server report formula and displays unavailable wisdom explicitly',async()=>{
  await act(async()=>root.render(<PersonalNumbers theme="light"/>));
  const calculate=[...container.querySelectorAll('button')].find(button=>button.textContent.includes('Рассчитать числа'));
  await act(async()=>calculate.click());
  expect(container.textContent).toContain('Для расчёта укажите имя и фамилию латиницей в профиле.');
  const label=[...container.querySelectorAll('div')].find(node=>node.textContent==='ЧУ (Число Ума)');
  await act(async()=>label.parentElement.querySelector('button').click());
  expect(container.textContent).toContain('Месяц рождения: 11');
  expect(container.textContent).toContain('Сводим месяц рождения, сохраняя мастер-число.');
  expect(container.textContent).toContain('Текст из серверного отчёта.');
  expect(axios.post).toHaveBeenCalledTimes(1);
});
