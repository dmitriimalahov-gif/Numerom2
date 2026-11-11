"""Morning letters: at 8:00 in the profile's city, the personal day number with a short word for it.

Runs as md.numerom.app.daily-email (scripts/numerom_services.py); services/daily_email.py has the rules.
"""
import asyncio
import logging
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from dotenv import load_dotenv
load_dotenv(ROOT / 'backend/.env')
from motor.motor_asyncio import AsyncIOMotorClient
from services.daily_email import DailyEmail


async def main():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    await DailyEmail(client[os.environ.get('MONGODB_DATABASE')]).run()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    asyncio.run(main())
