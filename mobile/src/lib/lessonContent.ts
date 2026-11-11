import type { Lesson } from '@numerom/api-client';
import { plainText } from './learning';
type Block = { title: string; text: string };
const record = (value:unknown):Record<string,unknown> => value && typeof value==='object' && !Array.isArray(value) ? value as Record<string,unknown> : {};
const parseList=(value:unknown):unknown[]=>{if(typeof value==='string'){try{return parseList(JSON.parse(value));}catch{return [];}}return Array.isArray(value)?value:[];};
export function lessonTextBlocks(lesson: Lesson): Block[] {
 const result:Block[]=[];
 const add=(title:unknown,text:unknown)=>{const content=plainText(text);if(content)result.push({title:plainText(title),text:content});};
 if(Array.isArray(lesson.theory))for(const item of lesson.theory){const block=record(item);add(block.title,block.content);}
 const content=record(lesson.content),theory=record(content.theory),labels=record(content.theory_labels);
 const hidden=new Set(parseList(record(content.hidden_theory_fields).fields));
 const defaults:Record<string,string>={what_is_numerology:'Что такое нумерология',cosmic_ship_story:'История',planets_and_numbers:'Планеты и числа',what_is_topic:'О теме',main_story:'Основное',key_concepts:'Ключевые понятия',practical_applications:'Применение'};
 for(const [key,value] of Object.entries(theory))if(key!=='full_text' && !hidden.has(key))add(labels[`${key}_label`] || defaults[key] || 'Теоретический материал',value);
 if(!result.length && !hidden.has('full_text'))add('',theory.full_text);
 for(const item of parseList(record(content.custom_theory_blocks).blocks)){const block=record(item);if(block.hidden!==true)add(block.title,block.content || block.text);}
 return result;
}
