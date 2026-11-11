"""Account use cases shared by the existing web and native API clients."""
from datetime import datetime
from fastapi import HTTPException
from models import User, UserProfileUpdate, TokenResponse
from auth import verify_password, create_access_token, create_user_response
from domain.name_numbers import calculate_full_name_number


def public_profile(user):
    """Explicit projection: database additions are private unless listed here."""
    fields = ('id', 'email', 'full_name', 'surname', 'birth_date', 'phone_number',
              'city', 'birth_city', 'birth_city_id', 'car_number', 'street', 'house_number', 'apartment_number', 'postal_code')
    result = {key: user.get(key, '') for key in fields}
    result.update(name=user.get('name', user.get('full_name', 'Пользователь')),
                  full_name_number=user.get('full_name_number'),
                  is_admin=user.get('is_admin', False),
                  is_super_admin=user.get('is_super_admin', False),
                  credits_remaining=user.get('credits_remaining', 0),
                  level=user.get('level', 1))
    return result


class AccountService:
    def __init__(self, db):
        self.users = db.users

    async def login(self, credentials):
        document = await self.users.find_one({'email': credentials.email})
        if not document or document.get('is_disabled'):
            raise HTTPException(status_code=401, detail='Invalid credentials')
        user = User(**document)
        if not verify_password(credentials.password, user.password_hash):
            raise HTTPException(status_code=401, detail='Invalid credentials')
        if user.subscription_expires_at and user.subscription_expires_at < datetime.utcnow():
            await self.users.update_one({'id': user.id}, {'$set': {
                'is_premium': False, 'subscription_type': None, 'subscription_expires_at': None,
            }})
            user.is_premium = False
            user.subscription_type = None
            user.subscription_expires_at = None
        role = 'admin' if user.is_super_admin or user.is_admin else 'user'
        token = create_access_token({'sub': user.id, 'role': role, 'auth_version': document.get('auth_version', 0)})
        return TokenResponse(access_token=token, user=create_user_response(user))

    async def _find(self, user_id):
        if not user_id:
            raise HTTPException(status_code=401, detail='Invalid token')
        user = await self.users.find_one({'id': user_id})
        if not user:
            raise HTTPException(status_code=404, detail='User not found')
        return user

    async def profile(self, user_id):
        return public_profile(await self._find(user_id))

    async def update_profile(self, user_id, data: UserProfileUpdate):
        user = await self._find(user_id)
        updates = data.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(status_code=400, detail='No valid fields provided for update')
        updates = {key: value.strip() if isinstance(value, str) else value for key, value in updates.items()}
        if updates.get('birth_city_id'):
            from services.geography import city_index
            city = city_index.lookup(updates['birth_city_id'])
            if not city:
                raise HTTPException(422, 'Выберите город рождения ещё раз или введите его вручную.')
            updates['birth_city'] = city['label']
        elif 'birth_city' in updates:
            # A manual edit must not keep the previous selected city's identifier.
            updates['birth_city_id'] = ''
        updates['updated_at'] = datetime.utcnow()
        if 'name' in updates or 'surname' in updates:
            updates['full_name_number'] = calculate_full_name_number(
                updates.get('name', user.get('name')), updates.get('surname', user.get('surname')))
        await self.users.update_one({'id': user_id}, {'$set': updates})
        return await self.profile(user_id)
