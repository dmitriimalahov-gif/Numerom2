import {View,Text} from 'react-native';
import {Button,Notice,s} from '../ui';
import type {DraftState} from '../../lib/exerciseDraft';
export function DraftStatus({state,retry,keepMine,useServer}:{state:DraftState;retry:()=>void;keepMine:()=>void;useServer:()=>void}){
 return <View style={{gap:10}}><Text accessibilityLiveRegion="polite" style={s.small}>{state.saving?'Сохраняем черновик…':state.saved?'Черновик сохранён в вашем аккаунте.':state.dirty?'Изменения ещё не сохранены.':'Черновик сохраняется автоматически.'}</Text>
  {!!state.error&&<Notice message={state.error} action="Повторить" onAction={retry}/>}
  {state.conflict&&<><Button secondary title="Сохранить мой текст вместо другой версии" onPress={keepMine}/><Button secondary title="Заменить мой текст сохранённой версией" onPress={useServer}/></>}
 </View>;
}
