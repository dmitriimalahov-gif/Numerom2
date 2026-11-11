import { Tabs, Redirect } from 'expo-router';
import { useSession } from '../../lib/session';
import { Loading, Screen } from '../../components/ui';
export default function TabsLayout() {
 const {status} = useSession();
 if(status==='loading') return <Screen><Loading/></Screen>;
 if(status!=='signedIn') return <Redirect href="/"/>;
 // Keep the existing screen lifecycle and drafts; navigation is in the shared drawer.
 return <Tabs backBehavior="history" tabBar={()=>null} screenOptions={{headerShown:false}}>
 <Tabs.Screen name="home" options={{title:'Главная'}}/><Tabs.Screen name="numbers" options={{title:'Числа'}}/><Tabs.Screen name="learning" options={{title:'Уроки'}}/><Tabs.Screen name="library" options={{title:'Схемы'}}/><Tabs.Screen name="profile" options={{title:'Профиль'}}/>
 </Tabs>;
}
