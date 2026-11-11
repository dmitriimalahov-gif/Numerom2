import {createContext} from 'react';
// Standalone screens such as biometric unlock still own their top safe area.
export const NavigationChromeContext=createContext(false);
