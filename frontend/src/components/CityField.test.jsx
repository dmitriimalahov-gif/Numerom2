import React,{act,useState} from 'react';
import {createRoot} from 'react-dom/client';
import CityField from './CityField';
import {api} from '../services/api';
jest.mock('../services/api',()=>({api:{request:jest.fn()}}));
let root,host,chosen;
function Form(){const [value,setValue]=useState('');return <CityField value={value} onChange={(text,id)=>{setValue(text);chosen=id;}}/>;}
beforeEach(()=>{global.IS_REACT_ACT_ENVIRONMENT=true;jest.useFakeTimers();host=document.createElement('div');document.body.append(host);root=createRoot(host);api.request.mockReset();chosen='';});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();jest.useRealTimers();});
async function input(value){await act(async()=>{const el=host.querySelector('input');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(el,value);el.dispatchEvent(new Event('input',{bubbles:true}));jest.advanceTimersByTime(301);});}
test('keyboard selection preserves region and country and manual edit clears city id',async()=>{
 api.request.mockResolvedValue({items:[{id:'1',name:'Springfield',country:'United States',region:'Illinois',label:'Springfield, Illinois, United States'}]});
 await act(async()=>root.render(<Form/>));await input('Spring');
 expect(host.textContent).toContain('Illinois, United States');
 await act(async()=>host.querySelector('input').dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowDown',bubbles:true})));
 await act(async()=>host.querySelector('input').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true})));
 expect(chosen).toBe('1');expect(host.querySelector('input').value).toBe('Springfield, Illinois, United States');expect(host.querySelector('[role=listbox]')).toBeNull();
 await input('My village');expect(chosen).toBe('');
});
