import {useState} from 'react';
import {Pressable,Text,View} from 'react-native';
import {router} from 'expo-router';
import {Button,Heading,Loading,Notice,Screen,s} from '../components/ui';
import {useSession} from '../lib/session';
import {colors} from '../lib/theme';
import Users from '../features/admin/Users';
import {Lessons,Consultations} from '../features/admin/Content';
import Reviews from '../features/admin/Reviews';
import Settings from '../features/admin/Settings';
import Overview from '../features/admin/Overview';
import Reports from '../features/admin/Reports';
import {Analytics,ChallengeNotes} from '../features/admin/Analytics';
const sections=['Обзор','Пользователи','Уроки','Ответы','Дневники','Аналитика','Консультации','Озвучка и видео','Настройки'] as const;
export default function Admin(){const {user,status,error,session}=useSession();if(status==='loading')return <Screen><Loading/></Screen>;if(status==='unavailable')return <Screen><Heading title="Проверяем доступ"/><Notice message={error||'Не удалось связаться с сервером.'} action="Повторить" onAction={()=>void session.restore()}/></Screen>;return status==='signedIn'&&(user?.is_admin||user?.is_super_admin)?<AdminWorkspace key={user.id}/>:<Screen><Heading title="Кабинет управления" subtitle="Этот раздел доступен администраторам NumerOM."/><Button title="К профилю" onPress={()=>router.replace('/profile')}/></Screen>;}
function AdminWorkspace(){const [section,setSection]=useState<typeof sections[number]>('Обзор'),[menu,setMenu]=useState(false);return <Screen><Button secondary title="К профилю" onPress={()=>router.push('/profile')}/><Heading eyebrow="NumerOM · управление" title="Кабинет администратора" subtitle="Ученики, содержание и настройки платформы."/><Button secondary title={menu?'Скрыть разделы управления':`Разделы управления · ${section}`} onPress={()=>setMenu(v=>!v)}/>{menu&&<View style={{flexDirection:'row',flexWrap:'wrap',gap:8}}>{sections.map(item=><Pressable key={item} accessibilityRole="tab" accessibilityState={{selected:section===item}} onPress={()=>{setSection(item);setMenu(false);}} style={{padding:14,minHeight:50,minWidth:'45%',flexGrow:1,borderRadius:16,backgroundColor:section===item?colors.navy:colors.surface,borderWidth:1,borderColor:colors.line}}><Text style={{fontWeight:'600',color:section===item?'#fff':colors.navy}}>{item}</Text></Pressable>)}</View>}<Text accessibilityRole="header" style={s.title}>{section}</Text>{section==='Обзор'?<Overview/>:section==='Пользователи'?<Users/>:section==='Уроки'?<Lessons/>:section==='Ответы'?<Reviews/>:section==='Дневники'?<ChallengeNotes/>:section==='Аналитика'?<Analytics/>:section==='Консультации'?<Consultations/>:section==='Озвучка и видео'?<Reports/>:<Settings/>}</Screen>;}
