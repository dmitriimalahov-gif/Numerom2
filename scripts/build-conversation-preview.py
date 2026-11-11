"""Package the authored consultation, verified calculations and audio offline."""
import base64
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/dmitrii-reading-1982-01-10'

# Design: cool paper #f6f8fc, white #fff, ink #183d64, secondary #57738c,
# sage #4b8d7b. Georgia for the personal letter heading, system sans for speech.
# A left-aligned consultation with a working square; formulas stay in disclosure.
# The square is the distinctive visual. No decorative gradients or card grid.


def main():
    script = json.loads((OUT / 'script.json').read_text())
    report = json.loads((OUT / 'calculation.json').read_text())
    audio = json.loads((OUT / 'audio-manifest.json').read_text())
    assert audio.get('seconds') and len(audio['segments']) == len(script['segments'])
    escape = html.escape
    encoded = base64.b64encode((OUT / 'Дмитрий-первый-разбор.m4a').read_bytes()).decode()
    logo = base64.b64encode((ROOT / 'frontend/public/images/brand/numerom-logo.svg').read_bytes()).decode()
    paragraphs = ''.join(f'<div class="passage" data-id="{escape(item["id"])}"><button class="cue" data-time="{stamp["start"]}" aria-label="Слушать этот фрагмент">{int(stamp["start"]//60)}:{int(stamp["start"]%60):02d}</button><p>{escape(item["text"])}</p></div>'
        for item, stamp in zip(script['segments'], audio['segments']))
    scheme = report['raw']['scheme']
    cells = ''.join(f'<div class="cell" data-digit="{cell["digit"]}"><span>{cell["digit"]} · {escape(cell["title"])}</span><strong>{str(cell["digit"])*cell["count"] or "—"}</strong><small>{cell["count"]} в расчёте</small></div>' for cell in scheme['cells'])
    lines = ''.join(f'<button class="line" data-key="{escape(line["key"])}" aria-pressed="false"><span>{escape(line["title"])}</span><span class="bar"><i style="width:{line["value"]/8*100}%"></i></span><b>{line["value"]}</b></button>' for line in scheme['lines'])
    names = {'soul':'Душа','mind':'Ум','destiny':'Судьба','helping_mind':'Помогающий ум','ruling':'Правящее число','life_path':'Жизненный путь','problem':'Общая задача'}
    values = ''.join(f'<div><dt>{label}</dt><dd>{report["raw"]["personal"][key]}</dd></div>' for key,label in names.items())
    methods = ''.join(f'<h3>{escape(section["title"])}</h3><ul>'+''.join(f'<li>{escape(step)}</li>'for step in section['steps'])+'</ul>' for section in report['sections'] if section['id'] in ['personal','square','lines'])
    payload = json.dumps({'lines':scheme['lines'],'counts':{str(c['digit']):c['count'] for c in scheme['cells']},
                          'timing':[{'id':s['id'],'start':s['start'],'seconds':s['seconds']} for s in audio['segments']]},ensure_ascii=False).replace('<','\\u003c')
    minutes,seconds = divmod(round(audio['seconds']),60)
    document = '''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Дмитрий — личный разбор NumerOM</title>
<style>
:root{color-scheme:light;--ink:#183d64;--muted:#57738c;--line:#dce5ed;--sage:#4b8d7b}
*{box-sizing:border-box}body{margin:0;background:#f6f8fc;color:var(--ink);font:17px/1.7 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}main{max-width:1000px;margin:0 auto;padding:30px 40px 80px}header{display:flex;align-items:center;justify-content:space-between;margin-bottom:42px;font-size:14px;color:var(--muted)}.brand{display:flex;align-items:center;gap:10px;font-size:20px;color:var(--ink);font-weight:650}.brand img{width:48px;height:44px;object-fit:contain}h1{font:normal clamp(36px,6vw,60px)/1.12 Georgia,serif;letter-spacing:-1px;margin:0 0 14px}h2{font:normal 30px/1.3 Georgia,serif;margin:0 0 18px}h3{font-size:18px;margin-top:30px}.date{color:var(--muted);margin:0 0 28px}.listen{padding:24px 28px;background:var(--ink);color:white;border-radius:20px;margin:30px 0 38px}.listen strong{font-size:20px}.listen p{font-size:14px;margin:4px 0 14px;color:#dce8f4}audio{width:100%;height:44px}.numbers{display:flex;flex-wrap:wrap;gap:16px 30px;border-bottom:1px solid var(--line);padding-bottom:28px;margin-bottom:36px}.numbers div{display:flex;align-items:baseline;gap:10px}.numbers dt{font-size:14px;color:var(--muted)}.numbers dd{font-size:23px;margin:0;font-weight:650}.reading{max-width:800px}.passage{display:grid;grid-template-columns:48px 1fr;gap:12px;padding:10px 0;border-left:3px solid transparent}.passage p{margin:0;max-width:70ch}.passage.active{border-left-color:var(--sage);background:#edf4f2}.cue{align-self:start;appearance:none;border:0;background:none;color:var(--sage);font:inherit;font-size:13px;cursor:pointer;padding:6px 0}.cue:hover{text-decoration:underline}.diagrams{border-top:1px solid var(--line);padding-top:35px;margin-top:38px}.diagram-layout{display:grid;grid-template-columns:1fr 1fr;gap:34px}.square{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border:1px solid var(--line);border-radius:15px;overflow:hidden;background:white}.cell{padding:16px 8px;min-height:125px;text-align:center;border:1px solid #e9eef3;display:flex;flex-direction:column;justify-content:center}.cell span{font-size:12px;color:var(--muted)}.cell strong{font-size:clamp(19px,3vw,25px);letter-spacing:1px;overflow-wrap:anywhere;margin:6px 0}.cell small{font-size:11px;color:var(--muted)}.cell.selected{background:#dceee7;border-color:#92b8aa}.line{width:100%;display:grid;grid-template-columns:155px 1fr 20px;gap:10px;align-items:center;background:none;border:0;padding:10px 0;color:var(--ink);font:inherit;font-size:13px;text-align:left;cursor:pointer}.line[aria-pressed=true]{color:#22644d;font-weight:700}.bar{height:6px;background:#e0e7ee;border-radius:3px;overflow:hidden}.bar i{display:block;height:100%;background:#668fad}.line[aria-pressed=true] .bar i{background:var(--sage)}.help{font-size:14px;color:var(--muted)}#line-note{min-height:90px;font-size:15px;margin-top:20px}.note{color:var(--muted);font-size:13px;margin-top:24px}details{border-top:1px solid var(--line);margin-top:30px;padding-top:20px}summary{cursor:pointer;font-weight:600}details li{margin:10px 0;font-size:14px}footer{border-top:1px solid var(--line);padding-top:22px;margin-top:40px;color:var(--muted);font-size:13px}button:focus-visible,summary:focus-visible{outline:3px solid #43816d;outline-offset:4px}@media(max-width:650px){main{padding:22px 20px 55px}header{margin-bottom:28px}.listen{padding:20px}.diagram-layout{grid-template-columns:1fr;gap:15px}.passage{grid-template-columns:35px 1fr;gap:8px}.numbers{gap:12px 22px}.reading{font-size:16px}.line{grid-template-columns:165px 1fr 20px}.cell strong{font-size:23px}}@media print{body{background:white}main{padding:0}.listen,.cue{display:none}.passage{display:block}details{display:block}.diagrams{break-inside:avoid}}
</style>
<main><header><div class="brand"><img alt="" src="data:image/svg+xml;base64,__LOGO__">NumerOM</div><span>Личный разбор</span></header>
<h1>Дмитрий,<br>посмотрим на ваши числа.</h1><p class="date">Дата рождения: 10 января 1982</p>
<section class="listen" aria-label="Аудиоразбор"><strong>Инициатива, люди и большой замысел</strong><p>__DURATION__ · выбранный вами голос</p><audio id="audio" controls preload="metadata" src="data:audio/mp4;base64,__AUDIO__"></audio></section>
<dl class="numbers">__VALUES__</dl><section class="reading" aria-label="Текст разбора">__PARAGRAPHS__</section>
<section class="diagrams"><h2>Ваш квадрат и линии</h2><p class="help">Выберите линию — её ячейки подсветятся в квадрате.</p><div class="diagram-layout"><div class="square">__CELLS__</div><div>__LINES__</div></div><p id="line-note" aria-live="polite">В ячейках показаны цифры из даты и дополнительных чисел. Справа — суммы их количеств по каждой линии.</p><p class="note">Дополнительные числа: 22, 4, 20, 2. Прочерк означает, что этой цифры нет в наборе расчёта.</p></section>
<details><summary>Посмотреть расчёт по шагам</summary>__METHODS__</details><footer>Первый разбор по материалам NumerOM: личные числа, квадрат, сочетания и практики. Трактовки служат поводом для самонаблюдения. Файл содержит текст, схемы и аудио и работает без интернета.</footer></main>
<script type="application/json" id="data">__PAYLOAD__</script><script>
const data=JSON.parse(document.getElementById('data').textContent),player=document.getElementById('audio');
document.querySelectorAll('.cue').forEach(b=>b.addEventListener('click',()=>{player.currentTime=Number(b.dataset.time);player.play().catch(()=>{});}));
player.addEventListener('timeupdate',()=>{const current=data.timing.find(s=>player.currentTime>=s.start&&player.currentTime<s.start+s.seconds);document.querySelectorAll('.passage').forEach(p=>p.classList.toggle('active',p.dataset.id===current?.id));});
document.querySelectorAll('.line').forEach(b=>b.addEventListener('click',()=>{const line=data.lines.find(l=>l.key===b.dataset.key);document.querySelectorAll('.line').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));document.querySelectorAll('.cell').forEach(c=>c.classList.toggle('selected',line.digits.includes(Number(c.dataset.digit))));document.getElementById('line-note').textContent=line.title+': '+line.digits.map(d=>data.counts[d]).join(' + ')+' = '+line.value+'. '+line.meaning.replace('В символике NumerOM: ','');}));
</script></html>'''
    for key,value in {'LOGO':logo,'DURATION':f'{minutes} мин {seconds:02d} сек','AUDIO':encoded,'VALUES':values,
        'PARAGRAPHS':paragraphs,'CELLS':cells,'LINES':lines,'METHODS':methods,'PAYLOAD':payload}.items():
        document=document.replace('__'+key+'__',value)
    target=OUT/'Дмитрий-личный-разбор.html'
    target.write_text(document)
    print(target)
    print('Self-contained bytes:',target.stat().st_size)


if __name__=='__main__':main()
