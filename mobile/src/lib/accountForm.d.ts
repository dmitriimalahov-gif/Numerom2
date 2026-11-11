import type {UserProfile} from '@numerom/api-client';

export interface ProfileDraft {
  full_name: string;
  name: string;
  surname: string;
  birth_date: string;
  city: string;
  birth_city:string; birth_city_id:string; phone_number:string; car_number:string;
  house_number:string; apartment_number:string; postal_code:string; street:string;
}
export function profileDraft(user: UserProfile | null): ProfileDraft;
export function profilePatch(draft: ProfileDraft, baseline: ProfileDraft): Partial<ProfileDraft>;
export function profileError(draft: ProfileDraft): string;
export function registrationError(data: {email: string; password: string; confirmation: string; full_name: string; birth_date: string}): string;
