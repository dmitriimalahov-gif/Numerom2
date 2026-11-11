import {useEffect,useState,useSyncExternalStore} from 'react';
import {Text,View} from 'react-native';
import type {ApiClient} from '@numerom/api-client';
import {Button,Field,Loading,s} from '../ui';
import {DraftStatus} from './DraftStatus';
import {createExerciseDraft} from '../../lib/exerciseDraft';
import {submissionId} from '../../lib/learning';
import {useSession} from '../../lib/session';

export function DiaryNote({api,path,initial,completed,locked,onEdit,onCommit}:{api:ApiClient;path:string;initial:string;completed:boolean;locked:boolean;onEdit:(note:string)=>void;onCommit:(note:string,complete:boolean)=>Promise<boolean>}){
 const {user,session}=useSession();
 const [controller]=useState(()=>{const owner=user?.id;return createExerciseDraft({read:()=>api.request(path),write:body=>api.request(path,{method:'POST',body}),initial,maxLength:4000,makeId:submissionId,isCurrent:()=>session.getSnapshot().user?.id===owner});});
 const state=useSyncExternalStore(controller.subscribe,controller.getSnapshot,controller.getSnapshot);
 useEffect(()=>{void controller.load();return()=>controller.dispose();},[controller]);
 useEffect(()=>{controller.setInitial(initial);},[controller,initial]);
 const [saving,setSaving]=useState(false);
 const save=async(complete:boolean)=>{if(saving||locked)return;setSaving(true);try{
  if(!await controller.flush())return;
  if(await onCommit(state.text,complete)){controller.setInitial(state.text.trim());await controller.clear();}
 }finally{setSaving(false);}};
 return <View style={{gap:12}}>{!state.ready&&<Loading/>}
  <Field label="Мои заметки и наблюдения" multiline value={state.text} maxLength={4000} editable={state.ready&&!locked&&!saving} onBlur={()=>void controller.flush()} onChangeText={value=>{controller.edit(value);onEdit(value);}} style={[s.input,{minHeight:150,textAlignVertical:'top'}]}/>
  <Text style={s.small}>{state.text.length} / 4000 · Черновик не отмечает задание выполненным.</Text>
  <DraftStatus state={state} retry={()=>void(state.ready?controller.flush():controller.load())} keepMine={()=>void controller.keepMine()} useServer={()=>void controller.useServer()}/>
  <Button secondary title="Сохранить заметку в дневник" disabled={!state.ready||locked||state.conflict} busy={saving} onPress={()=>void save(false)}/>
  {!completed&&<Button title="Задание выполнено — сохранить день" disabled={!state.ready||locked||saving||!state.text.trim()||state.conflict} onPress={()=>void save(true)}/>}
 </View>;
}
