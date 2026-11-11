import React, {act} from 'react';
import {createRoot} from 'react-dom/client';
global.TextEncoder = require('util').TextEncoder;
const {MemoryRouter} = require('react-router-dom');
const Page = require('./PasswordRecoveryPage').default;
let root,host;
const input = async(name,value)=>act(async()=>{const element=host.querySelector(`[name="${name}"]`);Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(element,value);element.dispatchEvent(new Event('input',{bubbles:true}));});
const submit=async()=>act(async()=>host.querySelector('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
const render=async mode=>act(async()=>root.render(<MemoryRouter><Page mode={mode}/></MemoryRouter>));
beforeEach(()=>{global.IS_REACT_ACT_ENVIRONMENT=true;host=document.createElement('div');document.body.appendChild(host);root=createRoot(host);window.history.replaceState(null,'','/');localStorage.clear();global.fetch=jest.fn(async()=>({ok:true,status:202,json:async()=>({message:'Если аккаунт существует, проверьте почту.'})}));});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();window.history.replaceState(null,'','/');jest.restoreAllMocks();});
test('request submits email without an existing account token and displays generic result',async()=>{
 localStorage.setItem('token','existing-session');await render('request');await input('email','anna@example.invalid');await submit();
 expect(fetch).toHaveBeenCalledTimes(1);const [url,options]=fetch.mock.calls[0];expect(url).toContain('/auth/forgot-password');expect(options.headers.Authorization).toBeUndefined();expect(JSON.parse(options.body)).toEqual({email:'anna@example.invalid'});expect(host.textContent).toContain('Если аккаунт существует');
});
test('mismatched password confirmation does not send the token',async()=>{
 window.history.replaceState(null,'','/reset-password#token='+'x'.repeat(43));await render('reset');await input('password','long-new-password');await input('confirmation','a-different-password');await submit();expect(fetch).not.toHaveBeenCalled();expect(host.textContent).toContain('Пароли не совпадают');expect(window.location.hash).toBe('');
});
test('successful reset sends token in body and asks for normal sign-in',async()=>{
 window.history.replaceState(null,'','/reset-password#token='+'x'.repeat(43));fetch.mockResolvedValue({ok:true,status:200,json:async()=>({message:'Пароль изменён. Войдите с новым паролем.'})});await render('reset');await input('password','long-new-password');await input('confirmation','long-new-password');await submit();expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({token:'x'.repeat(43),password:'long-new-password'});expect(host.textContent).toContain('Пароль изменён');expect(host.querySelector('input[type="password"]')).toBeNull();expect(localStorage.getItem('token')).toBeNull();
});
test('missing reset token offers a new link instead of an unusable form',async()=>{
 await render('reset');expect(host.querySelector('form')).toBeNull();expect(host.querySelector('a[href="/forgot-password"]')).not.toBeNull();
});
test('mail unavailable is displayed as an error and not a successful send',async()=>{
 fetch.mockResolvedValue({ok:false,status:503,json:async()=>({detail:'Mail unavailable'})});await render('request');await input('email','anna@example.invalid');await submit();expect(host.querySelector('[role="alert"]')).not.toBeNull();expect(host.querySelector('form')).not.toBeNull();
});
