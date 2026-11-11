import { useCallback, useRef } from 'react';
import { Pressable, Text, View } from 'react-native';
import { router, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import type { Lesson } from '@numerom/api-client';
import { Card, Heading, Loading, Notice, Screen, s } from '../../components/ui';
import { useSession } from '../../lib/session';
import { useResource } from '../../lib/useResource';
import { lessonProgress, LessonProgress } from '../../lib/learning';
import { colors } from '../../lib/theme';

function LessonRow({lesson,index}: {lesson:Lesson;index:number}) {
 let progress:LessonProgress|null=null;
 try { if(lesson.progress_data)progress=lessonProgress(lesson.progress_data); } catch { /* No invented progress for an unavailable summary. */ }
 return <Pressable accessibilityRole="button" accessibilityLabel={`${lesson.title}${progress?`, ${progress.completed?'Урок завершён':`Пройдено ${progress.percentage}%`}`:''}`} onPress={()=>router.push({pathname:'/lesson/[id]',params:{id:lesson.id}})}>
  <Card><View style={s.row}><Text style={s.eyebrow}>Урок {String(index+1).padStart(2,'0')}</Text><Text style={s.small}>Уровень {lesson.level || 1}</Text></View>
   <Text style={s.title}>{lesson.title}</Text>{!!lesson.description && <Text style={s.body} numberOfLines={3}>{lesson.description}</Text>}
   {progress && <><View style={{height:5,borderRadius:3,backgroundColor:colors.blue,overflow:'hidden'}}><View style={{width:`${progress.percentage}%`,height:5,backgroundColor:progress.completed?colors.green:colors.accent}}/></View><Text style={s.small}>{progress.completed?'Урок завершён':`Пройдено ${progress.percentage}%`}</Text></>}
   <View style={s.row}><Text style={s.link}>{progress && progress.percentage>0?'Продолжить урок':'Открыть урок'}</Text><Ionicons name="arrow-forward" size={20} color={colors.accent}/></View>
  </Card>
 </Pressable>;
}
export default function Learning() {
 const {api}=useSession();
 const lessons=useResource(useCallback(()=>api.lessons(),[api]));
 const focused=useRef(false);
 useFocusEffect(useCallback(()=>{if(focused.current)void lessons.reload();else focused.current=true;},[lessons.reload]));
 return <Screen refreshing={lessons.loading} onRefresh={()=>void lessons.reload()}><Heading eyebrow="Школа NumerOM" title="Знания в своём темпе" subtitle="Читайте, практикуйтесь и возвращайтесь к сохранённым результатам."/>
  {lessons.error && <Notice message={lessons.error} action="Попробовать снова" onAction={()=>void lessons.reload()}/>}
  {lessons.loading && !lessons.data?<Loading/>:lessons.data && !lessons.data.lessons?.length?<Card><Text style={s.title}>Уроков пока нет</Text><Text style={s.body}>Доступные материалы появятся здесь после публикации.</Text></Card>:lessons.data?.lessons?.map((lesson,index)=><LessonRow key={lesson.id} lesson={lesson} index={index}/>)}
 </Screen>;
}
