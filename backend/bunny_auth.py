"""Authorization shared by Bunny administration routes."""
from fastapi import Depends, HTTPException
from auth import get_current_user


async def require_bunny_admin(current_user: dict = Depends(get_current_user)):
    # get_current_user derives this role from the current database is_admin /
    # is_super_admin flags and rejects disabled accounts, never trusting JWT roles.
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail='Требуются права администратора')
    return current_user
