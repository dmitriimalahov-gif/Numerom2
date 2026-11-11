const profileFields=['name','surname','full_name','birth_date','city','birth_city','birth_city_id','street','house_number','apartment_number','postal_code','phone_number','car_number'];
function profileRevision(user){return JSON.stringify(profileFields.map(key=>user?.[key]||''));}
function reportPreview(raw,birth,useProfile){
 if(!raw||raw.birth_date!==birth||raw.use_profile!==useProfile||!Array.isArray(raw.available)||!Array.isArray(raw.excluded)||(useProfile&&!/^[a-f0-9]{64}$/.test(raw.profile_fingerprint)))throw new Error('Обновите состав разбора перед оплатой.');
 return raw;
}
module.exports={profileRevision,reportPreview};
