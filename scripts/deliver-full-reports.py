"""Background delivery of paid full reports: queue interpretation, audio and video, then email the owner.

Runs as md.numerom.app.report-delivery (scripts/numerom_services.py); services/report_delivery.py has the rules.
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
from push_notifications import PushNotificationManager
from services.report_delivery import ReportDelivery


async def main():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ.get('MONGODB_DATABASE')]
    await ReportDelivery(db, push=PushNotificationManager(db)).run()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    asyncio.run(main())
