import React,{act} from 'react';
import {createRoot} from 'react-dom/client';
global.TextEncoder=require('util').TextEncoder;
const {MemoryRouter}=require('react-router-dom');
const Preview=require('../ReportProfilePreview').default;
const {api}=require('../../../services/api');
jest.mock('../../../services/api',()=>({api:{request:jest.fn()}}));
let root,host;
beforeEach(()=>{global.IS_REACT_ACT_ENVIRONMENT=true;host=document.createElement('div');document.body.append(host);root=createRoot(host);api.request.mockReset();});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();});
test('late old preview cannot replace a changed birth date and profile is disabled for another person',async()=>{
 let oldResolve;const onPreview=jest.fn();
 api.request.mockImplementation((path,{body})=>body.birth_date==='12.03.1990'?new Promise(resolve=>{oldResolve=resolve;}):Promise.resolve({...body,profile_fingerprint:null,available:[{id:'new',title:'New date'}],excluded:[]}));
 const render=birth=>act(async()=>root.render(<MemoryRouter><Preview user={{id:'owner',birth_date:'12.03.1990'}} birth={birth} useProfile onUseProfile={()=>{}} onPreview={onPreview}/></MemoryRouter>));
 await render('12.03.1990');await render('13.03.1990');
 expect(api.request.mock.calls[1][1].body.use_profile).toBe(false);expect(host.textContent).toContain('New date');
 await act(async()=>oldResolve({birth_date:'12.03.1990',use_profile:true,profile_fingerprint:'a'.repeat(64),available:[{id:'old',title:'Old profile'}],excluded:[]}));
 expect(host.textContent).not.toContain('Old profile');expect(onPreview.mock.calls.at(-1)[0].birth_date).toBe('13.03.1990');
});
test('profile changes invalidate the preview fingerprint without making a payment',async()=>{
 const onPreview=jest.fn();let stamp='a';api.request.mockImplementation((path,{body})=>Promise.resolve({...body,profile_fingerprint:stamp.repeat(64),available:[],excluded:[{title:'Дом',reason:'Укажите номер дома'}]}));
 const render=house=>act(async()=>root.render(<MemoryRouter><Preview user={{id:'owner',birth_date:'12.03.1990',house_number:house}} birth="12.03.1990" useProfile onUseProfile={()=>{}} onPreview={onPreview}/></MemoryRouter>));
 await render('');expect(host.textContent).toContain('Укажите номер дома');stamp='b';await render('12');
 expect(onPreview.mock.calls.at(-1)[0].profile_fingerprint).toBe('b'.repeat(64));expect(api.request.mock.calls.every(([path])=>path==='/full-reports/preview')).toBe(true);
});
