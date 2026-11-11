import {router} from 'expo-router';
import {Button,Heading,Loading,Screen} from '../components/ui';
import {useSession} from '../lib/session';
import Relationships from '../features/Relationships';
import {NarrationProvider} from '../components/audio/Narration';

export default function RelationshipsRoute(){
 const {user,status}=useSession();
 if(status==='loading')return <Screen><Loading/></Screen>;
 if(status!=='signedIn')return <Screen><Heading title="Совместимость" subtitle="Войдите, чтобы рассчитать совместимость и открыть свои результаты."/><Button title="Войти" onPress={()=>router.replace('/')}/></Screen>;
 return <NarrationProvider key={user!.id} path="/narration/project"><Relationships/></NarrationProvider>;
}
