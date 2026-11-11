"""Create a clearly named, free rendering fixture in disposable Mongo27039 only."""
import asyncio,os
from datetime import datetime
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorClient
from services.personal_calculations import PersonalRequest,prepare_personal
async def main():
 if os.environ.get('NUMEROM_TOOLS_QA')!='1':raise RuntimeError('Only isolated preview data')
 client=AsyncIOMotorClient('mongodb://127.0.0.1:27039',serverSelectionTimeoutMS=4000)
 db=client['numerom_tools_browser_qa']
 assert await db.users.find_one({'id':'tools-qa','email':'tools@example.invalid'})
 result=prepare_personal(PersonalRequest(birth_date='10.01.1982',request_id=uuid4(),expected_cost=0),{'name':'Anna','surname':'Marinova','birth_date':'10.01.1982'})
 await db.numerology_calculations.update_one({'id':'qa-comprehensive-rendering-fixture'},{'$setOnInsert':{'id':'qa-comprehensive-rendering-fixture','user_id':'tools-qa','calculation_type':'personal_numbers','birth_date':'10.01.1982','created_at':datetime.utcnow(),'cost':0,'results':result['legacy'],'fixture_only':True}},upsert=True)
 client.close();print('Free rendering fixture saved in disposable Mongo27039; no debit and no account changes.')
if __name__=='__main__':asyncio.run(main())
