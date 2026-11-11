export interface NavigationItem {id:string;label:string;path:string;icon:string}
export interface NavigationSection {title:string;items:NavigationItem[]}
export function navigationSections(options:{signedIn:boolean;isAdmin?:boolean}):NavigationSection[];
export function activeSection(pathname:string,signedIn:boolean):string;
export function screenNavigation(pathname:string,signedIn:boolean):{title:string;parent:string|null};
