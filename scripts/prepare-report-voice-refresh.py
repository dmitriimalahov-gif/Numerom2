"""Queue the selected voice for existing paid snapshots, without payments or notifications.

The current validated interpretation pipeline produces the replacement chapters
and Remotion jobs. Original report documents, revisions and old files stay intact.
Default is an inventory; --apply explicitly queues all saved paid snapshots.
"""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import sys

from numerom_services import service_root
ROOT = service_root()
sys.path.insert(0, str(ROOT/'backend'))
from domain.consultation import VOICE
from services.report_files import digest
from services.report_insights import ReportInsights, VERSION
from services.narration import NarrationService
from services.report_video import ReportVideo


def prepare(reports, insights, voice, video):
    counts = Counter(); seen = set()
    for report in reports:
        key = digest(VERSION, report)
        if key in seen: continue
        seen.add(key)
        enriched, state = insights.enrich(report)
        counts['snapshots'] += 1
        if state != 'ready':
            counts['analysis_'+state] += 1
            continue  # The insight worker queues audio/video only after validation.
        clips = enriched.get('narration', [])
        if not clips or any(item.get('voice') != VOICE for item in clips):
            raise ValueError('Report refresh did not select the approved voice')
        for item in clips:
            voice.enqueue(item, 'full-report', 'paid-report')
            counts['audio_'+voice.state(item)['status']] += 1
        video.enqueue(enriched)
        counts['video_'+video.state(enriched)['status']] += 1
    return dict(counts)


def main():
    from dotenv import load_dotenv
    from pymongo import MongoClient
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(); load_dotenv(ROOT/'backend/.env')
    with MongoClient(os.environ['MONGO_URL'], serverSelectionTimeoutMS=5000) as client:
        orders = list(client[os.environ['MONGODB_DATABASE']].full_report_orders.find(
            {'state': 'paid'}, {'report': 1, 'revisions.report': 1}))
    reports = [report for order in orders for report in
        [order.get('report'), *[r.get('report') for r in order.get('revisions', [])]] if isinstance(report, dict)]
    result = {'paid_orders': len(orders), 'saved_snapshots': len(reports), 'voice': VOICE, 'applied': args.apply}
    if args.apply:
        result.update(prepare(reports, ReportInsights(), NarrationService(None), ReportVideo(None)))
        output = ROOT/'artifacts/narration-consultation-v1/report-refresh.json'
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__': main()
