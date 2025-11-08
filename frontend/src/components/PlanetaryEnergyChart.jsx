import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Loader, BarChart3 } from 'lucide-react';
import { PLANET_COLORS, PLANET_SHORT_NAMES } from '../constants/colors';
import { useAuth } from '../AuthContext';
import clsx from 'clsx';
import { getBackendUrl } from '../utils/backendUrl';

const PlanetaryEnergyChart = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const backendUrl = getBackendUrl();

  const loadData = async () => {
    setLoading(true); setError('');
    try {
      const res = await fetch(`${backendUrl}/api/charts/planetary-energy/7`, { headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` } });
      if (!res.ok) throw new Error('Ошибка получения графиков энергий');
      const json = await res.json();
      setData(json);
    } catch (e) { setError(e.message); } finally { setLoading(false); }
  };

  useEffect(() => { loadData(); }, []);

  if (loading) return (<Card><CardContent className="py-10 text-center"><Loader className="w-5 h-5 animate-spin mx-auto mb-2" />Загрузка…</CardContent></Card>);
  if (error) return (<Card><CardContent className="py-10 text-center text-red-600">{error}</CardContent></Card>);
  if (!data) return null;

  const day = data.chart_data?.[0];
  if (!day) return null;

  const entries = Object.entries(day.energies || day).filter(([k]) => !['date', 'day_name'].includes(k));

  return (
    <div className="space-y-4">
      <Card className="numerology-gradient"><CardHeader className="text-white"><CardTitle className="text-2xl">Планетарные Энергии</CardTitle><CardDescription className="text-white/90">Анализ на 7 дней</CardDescription></CardHeader></Card>
      <Card>
        <CardHeader><CardTitle className="flex items-center"><BarChart3 className="w-5 h-5 mr-2" />Сегодня</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {entries.map(([planet, value]) => (
              <div key={planet} className="p-3 rounded-lg bg-white shadow flex items-center justify-between">
                <div className="text-sm font-medium" style={{ color: PLANET_COLORS[PLANET_SHORT_NAMES[planet]] }}>{planet}</div>
                <div className="text-xl font-bold">{value}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PlanetaryEnergyChart;