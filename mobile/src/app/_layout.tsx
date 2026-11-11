import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { SessionProvider } from '../lib/session';
import {AppNavigation} from '../components/AppNavigation';
import {CreditNotice} from '../components/CreditNotice';
import {MediaDock} from '../components/media/MediaDock';
import {ReportReady} from '../components/media/ReportReady';
export default function RootLayout() {
 return <SafeAreaProvider><SessionProvider><StatusBar style="dark"/><CreditNotice><AppNavigation><Stack screenOptions={{headerShown:false}}/></AppNavigation><ReportReady/><MediaDock/></CreditNotice></SessionProvider></SafeAreaProvider>;
}
