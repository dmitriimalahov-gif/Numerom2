import React, {useEffect,useId,useState,useSyncExternalStore} from 'react';
import {createCitySearch} from '../../../packages/api-client/cities';
import {api} from '../services/api';
import './city-field.css';

export default function CityField({value,onChange,disabled=false,label='Город рождения'}) {
 const id=useId(),[controller]=useState(()=>createCitySearch({request:(...args)=>api.request(...args)}));
 const state=useSyncExternalStore(controller.subscribe,controller.getSnapshot,controller.getSnapshot),[active,setActive]=useState(-1),[searched,setSearched]=useState(false);
 useEffect(()=>()=>controller.dispose(),[controller]);
 useEffect(()=>{if(disabled)controller.clear();},[disabled,controller]);
 function choose(item){controller.clear();setSearched(false);setActive(-1);onChange(item.label,item.id);}
 function keyDown(event){
  if(event.key==='Escape'){controller.clear();setSearched(false);setActive(-1);}
  if(state.items.length&&['ArrowDown','ArrowUp'].includes(event.key)){event.preventDefault();setActive(index=>(index+(event.key==='ArrowDown'?1:-1)+state.items.length)%state.items.length);}
  if(event.key==='Enter'&&active>=0&&state.items[active]){event.preventDefault();choose(state.items[active]);}
 }
 return <div className="nm-city-field"><label htmlFor={id}>{label}</label><input id={id} role="combobox" aria-autocomplete="list" aria-expanded={state.items.length>0} aria-controls={`${id}-results`} aria-activedescendant={active>=0?`${id}-${active}`:undefined} autoComplete="off" value={value||''} maxLength={300} disabled={disabled} onKeyDown={keyDown} onBlur={event=>{if(!event.currentTarget.parentElement.contains(event.relatedTarget)){controller.clear();setSearched(false);setActive(-1);}}} onChange={event=>{onChange(event.target.value,'');setActive(-1);setSearched(event.target.value.trim().length>=2);controller.search(event.target.value);}} placeholder="Начните вводить название города"/>
  {state.busy&&<p role="status">Ищем города…</p>}
  {state.items.length>0&&<ul id={`${id}-results`} role="listbox" aria-label="Подходящие города">{state.items.map((item,index)=><li key={item.id} id={`${id}-${index}`} role="option" aria-selected={active===index}><button type="button" onMouseDown={event=>event.preventDefault()} onClick={()=>choose(item)}><strong>{item.name}</strong><span>{[item.region,item.country].filter(Boolean).join(', ')}</span></button></li>)}</ul>}
  {state.error&&<p role="status">{state.error}</p>}
  {searched&&!state.busy&&!state.error&&!state.items.length&&<p role="status">Нет совпадений. Попробуйте другое написание или оставьте город, регион и страну вручную.</p>}
  <small>Город рождения и текущий город сохраняются отдельно. <a href="https://www.geonames.org/" target="_blank" rel="noreferrer">Геоданные GeoNames</a>, CC BY 4.0.</small>
 </div>;
}
