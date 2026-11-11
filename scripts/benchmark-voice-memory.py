"""Run the actual voice worker in isolated queues against the same public script.

No production jobs, voice choices, or caches are changed. The existing shared
GPU slot is held for the comparison; production synthesis resumes afterwards.
"""
import argparse
from contextlib import nullcontext
import importlib.util
import json
from pathlib import Path
import sys
import time

SOURCE = Path(__file__).resolve().parents[1]
RUNTIME = Path.home() / 'Library/Application Support/NumerOM/runtime'
sys.path.insert(0, str(SOURCE / 'scripts'))
sys.path.insert(0, str(SOURCE / 'backend'))
from domain.narration import clip
from domain.report_audio import ready_audio
from report_generation_slot import report_generation_slot

TEXT = '\n\n'.join([
    'Начнём с того, что вам легко даётся. Вспомните недавнюю задачу, которую вы решили спокойно и уверенно. Обратите внимание, какие действия помогли вам получить результат.',
    'Теперь посмотрите на привычный способ общения. Умеете ли вы слушать собеседника и ясно объяснять свою мысль? Попробуйте сначала уточнить вопрос, а затем предложить решение.',
    'Для практики выберите одно небольшое действие на сегодня. Запишите, что именно вы хотите сделать и как поймёте, что получилось. Вечером вернитесь к записи и отметьте результат.',
    'Если задача кажется слишком большой, разделите её на понятные шаги. Сначала завершите один шаг и только потом переходите к следующему. Такой подход помогает сохранять внимание.'
])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    spec = importlib.util.spec_from_file_location('voice_benchmark_worker', SOURCE/'scripts/generate-project-voices.py')
    worker = importlib.util.module_from_spec(spec); spec.loader.exec_module(worker)
    worker.ROOT = RUNTIME
    reference = worker.reference('dmitrii-conversation-v1')
    worker.reference = lambda name: reference
    worker.russian_pronunciation.RESOURCE = RUNTIME/'backend/private/pronunciation'/worker.russian_pronunciation.VERSION
    worker.secrets.randbits = lambda bits: 20261108
    worker.report_generation_slot = nullcontext
    job = clip('voice-performance-sample', 'guide', 'Проверка скорости', TEXT)
    job.update(voice='dmitrii-conversation-v1', pronunciation=worker.russian_pronunciation.VERSION)
    summary = {'voice': job['voice'], 'pronunciation': job['pronunciation'], 'seed': 20261108, 'samples': []}
    print('WAIT shared generation slot', flush=True)
    with report_generation_slot(RUNTIME/'backend/private/runtime/report-generation.lock'):
        # Warm both paths before the measured pair; imports, accent models and
        # initial Metal kernel compilation must not inflate the claimed gain.
        modes=[('warmup-low','--low-memory'),('warmup-reuse','--reuse-models'),
               ('low','--low-memory'),('reuse','--reuse-models')]
        for mode, flag in modes:
            worker.ROOT = output/mode
            queue = worker.ROOT/'backend/private/narration'
            (queue/'jobs').mkdir(parents=True)
            (queue/'jobs'/f"{job['hash']}.json").write_text(json.dumps(job, ensure_ascii=False))
            sys.argv = ['generate-project-voices.py', '--limit', '1', flag]
            started = time.monotonic()
            worker.main()
            elapsed = time.monotonic()-started
            cache = queue/'clips'/job['hash']
            ready = ready_audio(cache, job['hash'])
            if not ready:raise RuntimeError(f'Benchmark {mode} did not pass the production quality gate')
            meta = json.loads((cache/'ready.json').read_text())
            generation = json.loads((cache/'generation.json').read_text())
            row = {'mode':mode, 'wall_seconds':round(elapsed, 3), 'audio_seconds':meta['seconds'],
                'max_word_difference':max(s['difference'] for s in meta['segments']),
                'segments':len(meta['segments']), 'sha256':meta['sha256'],
                'performance':generation['performance']}
            summary['samples'].append(row)
            (output/'result.json').write_text(json.dumps(summary, indent=2))
            print(json.dumps(row), flush=True)
    old, new = summary['samples'][-2:]
    summary['comparison']='Final pair after both modes were warmed; identical script and seeds.'
    summary['speedup'] = round(old['wall_seconds']/new['wall_seconds'], 3)
    summary['duration_reduction_percent'] = round((1-new['wall_seconds']/old['wall_seconds'])*100, 1)
    (output/'result.json').write_text(json.dumps(summary, indent=2))
    print('RESULT', json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
