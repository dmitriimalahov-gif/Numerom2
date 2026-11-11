import React, { useState } from 'react';
import { ArrowUpRight, Image as ImageIcon } from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';

export const Illustration = ({ name, alt, className = '', ...props }) => <picture className={`nm-illustration ${className}`}>
  <img className="nm-image-light" src={`${process.env.PUBLIC_URL}/images/numerom/${name}W.png`} alt={alt} loading="lazy" decoding="async" {...props} />
  <img className="nm-image-dark" src={`${process.env.PUBLIC_URL}/images/numerom/${name}B.png`} alt={alt} loading="lazy" decoding="async" {...props} />
</picture>;

const illustrations = [
  { name: 'KVADRAT', title: 'Квадрат чисел', group: 'Квадрат и даты' },
  ...['1101928', '2112029', '3122130', '4132231', '51423', '61524', '71625', '81726', '91827'].map((name, i) => ({ name, title: `Число ${i + 1} и даты рождения`, group: 'Квадрат и даты' })),
  ...['123', '456', '159', '357'].map(name => ({ name, title: `Сочетание ${name.split('').join('–')}`, group: 'Сочетания' })),
  ...['4D', '4M', '4S', '4U', '4UZ', 'P4'].map(name => ({ name, title: `Схема ${name}`, group: 'Сочетания' })),
  ...[['SU', 'Солнце'], ['CHA', 'Луна'], ['GU', 'Юпитер'], ['RA', 'Раху'], ['BU', 'Меркурий'], ['SHA', 'Сатурн'], ['MA', 'Марс'], ['KE', 'Кету'], ['HSU', 'Дополнительная схема']].map(([name, title]) => ({ name, title, group: 'Примеры расчётов' })),
];
const groups = ['Квадрат и даты', 'Сочетания', 'Примеры расчётов'];

const NumerologyIllustrations = ({ embedded = false }) => {
  const [group, setGroup] = useState(groups[0]);
  const [selected, setSelected] = useState(null);
  return <section className={`nm-illustration-library ${embedded ? 'nm-illustration-library-embedded' : ''}`}>
    <div className="nm-row-heading"><div><span className="nm-section-label"><ImageIcon size={16} aria-hidden="true" /> Наглядная нумерология</span>{embedded ? <h2>От схемы к пониманию</h2> : <h1>Схемы и примеры</h1>}<p>Иллюстрации NumerOM для знакомства с числами. Это учебные примеры, а не ваши персональные результаты.</p></div></div>
    <div className="nm-filter-buttons" role="group" aria-label="Категория иллюстраций">{groups.map(item => <button key={item} aria-pressed={group === item} onClick={() => setGroup(item)}>{item}</button>)}</div>
    <div className="nm-illustration-grid">{illustrations.filter(item => item.group === group).map(item => <button className="nm-illustration-card" key={item.name} onClick={() => setSelected(item)} aria-label={`Увеличить: ${item.title}`}><Illustration name={item.name} alt={item.title} /><span>{item.title}<ArrowUpRight size={16} aria-hidden="true" /></span></button>)}</div>
    <Dialog open={!!selected} onOpenChange={open => { if (!open) setSelected(null); }}><DialogContent className="nm-illustration-dialog">{selected && <><DialogHeader><DialogTitle>{selected.title}</DialogTitle><DialogDescription>Учебная иллюстрация NumerOM. Пример для изучения, не персональный расчёт.</DialogDescription></DialogHeader><Illustration name={selected.name} alt={selected.title} /></>}</DialogContent></Dialog>
  </section>;
};
export default NumerologyIllustrations;
