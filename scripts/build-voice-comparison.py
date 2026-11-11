"""Package the local voice experiment as a self-contained listening page."""
import base64
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/voice-natural-2026-11-07'
manifest = json.loads((OUT / 'manifest.json').read_text())
samples = {s['name']: s for s in manifest['samples']}
labels = {
    'natural': ('Новая проба', 'Спокойная, естественная подача', 'Без ускорения · сохранены тихие оттенки и окончания фраз'),
    'current': ('Для сравнения', 'Текущая обработка', 'Привычный эталон · ускорение до 1,2×'),
}
cards = []
for name in ('natural', 'current'):
    sample = samples[name]
    uri = 'data:audio/mp4;base64,' + base64.b64encode((OUT / f'{name}.m4a').read_bytes()).decode()
    eyebrow, title, detail = labels[name]
    seconds = round(sample['seconds'])
    cards.append(f'''<section class="card {name}">
      <p class="eyebrow">{eyebrow}</p><h2>{title}</h2><p class="detail">{detail}</p>
      <audio controls preload="metadata" aria-label="{title}" src="{uri}"></audio>
      <div class="bottom"><span>{seconds // 60}:{seconds % 60:02d}</span><a href="{uri}" download="Dmitrii-{name}.m4a">Скачать аудио ↓</a></div>
    </section>''')
page = '''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Голос Дмитрия — сравнение озвучки</title><style>
*{box-sizing:border-box}body{margin:0;background:#f4f7fc;color:#172e50;font:17px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
main{max-width:1040px;margin:auto;padding:54px 24px 40px}.brand{font-weight:750;letter-spacing:.12em;font-size:13px;color:#47668e}
h1{font-size:clamp(34px,6vw,54px);line-height:1.12;letter-spacing:-.04em;margin:24px 0 18px}h2{font-size:25px;line-height:1.25;margin:8px 0 16px}
.intro{max-width:710px;color:#526781;margin-bottom:28px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.card{background:white;border:1px solid #dce5f1;border-radius:24px;padding:26px;min-width:0}.natural{border:2px solid #6292d5;background:#fafdff}
.eyebrow{font-size:12px;letter-spacing:.1em;font-weight:750;text-transform:uppercase;color:#44668f;margin:0}.detail{font-size:15px;min-height:52px;color:#526781}
audio{width:100%;display:block;margin:22px 0 12px}.bottom{display:flex;justify-content:space-between;gap:16px;font-size:14px;color:#5d7190}a{color:#265da6;text-underline-offset:4px}
.transcript{margin-top:26px;padding:26px;border-radius:24px;background:#eaf0f9}.transcript p:last-child{margin-bottom:0}.foot{font-size:13px;color:#687c96;margin-top:24px}
@media(max-width:670px){main{padding:30px 18px}.grid{grid-template-columns:1fr}.detail{min-height:0}.card,.transcript{padding:22px}}
</style></head><body><main><div class="brand">NUMEROM · ГОЛОС ДМИТРИЯ</div><h1>Больше живой речи.</h1>
<p class="intro">Один текст в двух вариантах. Сравните темп, паузы и окончания фраз. Это проба синтезированного голоса на основе вашей записи.</p>
<div class="grid">''' + ''.join(cards) + '''</div><section class="transcript"><p class="eyebrow">Текст образца</p><p>''' + html.escape(manifest['text']) + '''</p></section>
<p class="foot">Оба варианта созданы локально. Страница работает без интернета. Основная озвучка проекта пока сохранена.</p></main>
<script>document.querySelectorAll('audio').forEach(player=>player.addEventListener('play',()=>document.querySelectorAll('audio').forEach(other=>{if(other!==player)other.pause()})));</script>
</body></html>'''
(OUT / 'Голос-Дмитрия-сравнение.html').write_text(page)
print(OUT / 'Голос-Дмитрия-сравнение.html')
