import {telegramApp} from '../../lib/telegram';
import { useRef, useState } from 'react';
import { Text, View, Pressable } from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Brand, Button, Card, Heading, Notice, Screen, s } from '../../components/ui';
import { colors } from '../../lib/theme';
import { useSession } from '../../lib/session';
import { AuthorWord } from '../../components/AuthorWord';
export default function Home() {
 const {user,session} = useSession(); const [busy,setBusy]=useState(false);const [error,setError]=useState('');
 const refreshLock=useRef(false);
 async function refresh() {if(refreshLock.current)return;refreshLock.current=true;setBusy(true);setError('');try{await session.refresh();}catch(e){setError(e instanceof Error?e.message:'Не удалось обновить');}finally{refreshLock.current=false;setBusy(false);}}
 return <Screen refreshing={busy} onRefresh={()=>void refresh()}><Brand/><Heading eyebrow="Ваш личный кабинет" title={`Здравствуйте, ${user?.name || user?.full_name?.split(' ')[0] || 'друг'}!`} subtitle="Немного внимания к себе — каждый день."/>
 {error && <Notice message={error} action="Повторить" onAction={()=>void refresh()}/>}
 <Card tinted><Text style={s.eyebrow}>Ваш следующий шаг</Text><Text style={[s.title,{fontSize:26,lineHeight:32}]}>Узнайте свои{ '\n'}персональные числа</Text><Text style={s.body}>Начните с даты рождения и познакомьтесь с основными числами вашего профиля.</Text><Button title="Подробный расчёт" onPress={()=>router.push('/numbers')}/></Card>
 <View style={s.row}><View style={{flex:1}}><Card><Text style={s.small}>Баланс</Text><Text style={[s.heading,{fontSize:28}]}>{user?.credits_remaining ?? '—'}</Text><Text style={s.small}>баллов для расчётов</Text></Card></View><View style={{flex:1}}><Card><Text style={s.small}>Обучение</Text><Text style={[s.heading,{fontSize:28}]}>{user?.level ?? '—'}</Text><Text style={s.small}>текущий уровень</Text></Card></View></View>
 <Button title="Пополнить баллы" onPress={()=>router.push('/top-up')}/>
 <Card><Text style={s.title}>Полный разбор по дате рождения</Text><Text style={s.body}>Все расчёты, схемы, персональные пояснения и аудиоглавы в одном сохранённом отчёте.</Text><Button title={telegramApp()?'Полный разбор':'Полный разбор · 6,66 €'} onPress={()=>router.push('/full-report')}/><Text style={s.small}>Отдельная разовая покупка. Баллы не списываются.</Text></Card>
 <Text style={s.title}>Продолжайте исследовать</Text>
 <Pressable accessibilityRole="button" onPress={()=>router.push('/learning')}><Card><View style={s.row}><Ionicons name="book-outline" size={28} color={colors.accent}/><View style={{flex:1,gap:4}}><Text style={s.title}>Обучение NumerOM</Text><Text style={s.small}>Материалы, которые доступны вам</Text></View><Ionicons name="chevron-forward" size={20} color={colors.muted}/></View></Card></Pressable>
 <AuthorWord/>
 <Pressable accessibilityRole="button" onPress={()=>router.push('/library')}><Card><View style={s.row}><Ionicons name="shapes-outline" size={28} color={colors.accent}/><View style={{flex:1,gap:4}}><Text style={s.title}>Наглядные схемы</Text><Text style={s.small}>Авторские иллюстрации и примеры</Text></View><Ionicons name="chevron-forward" size={20} color={colors.muted}/></View></Card></Pressable>
 </Screen>;
}
