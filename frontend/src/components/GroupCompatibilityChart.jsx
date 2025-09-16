import React from 'react';
import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';

ChartJS.register(ArcElement, Tooltip, Legend);

const GroupCompatibilityChart = ({ groupResults }) => {
  if (!groupResults || !groupResults.group_analysis) {
    return null;
  }

  const { main_person, group_analysis, average_compatibility } = groupResults;

  // Данные для диаграммы совместимости
  const compatibilityData = {
    labels: group_analysis.map(person => person.name),
    datasets: [
      {
        label: 'Совместимость',
        data: group_analysis.map(person => person.compatibility_score),
        backgroundColor: [
          'rgba(255, 99, 132, 0.6)',
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 205, 86, 0.6)',
          'rgba(75, 192, 192, 0.6)',
          'rgba(153, 102, 255, 0.6)',
        ],
        borderColor: [
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 205, 86, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)',
        ],
        borderWidth: 2,
      },
    ],
  };

  // Данные для диаграммы типов отношений
  const relationshipTypes = group_analysis.reduce((acc, person) => {
    const type = person.relationship_type;
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {});

  const relationshipData = {
    labels: Object.keys(relationshipTypes),
    datasets: [
      {
        label: 'Типы отношений',
        data: Object.values(relationshipTypes),
        backgroundColor: [
          'rgba(34, 197, 94, 0.6)',
          'rgba(59, 130, 246, 0.6)',
          'rgba(239, 68, 68, 0.6)',
          'rgba(245, 158, 11, 0.6)',
          'rgba(139, 69, 19, 0.6)',
          'rgba(147, 51, 234, 0.6)',
        ],
        borderColor: [
          'rgba(34, 197, 94, 1)',
          'rgba(59, 130, 246, 1)',
          'rgba(239, 68, 68, 1)',
          'rgba(245, 158, 11, 1)',
          'rgba(139, 69, 19, 1)',
          'rgba(147, 51, 234, 1)',
        ],
        borderWidth: 2,
      },
    ],
  };

  // Данные для диаграммы чисел жизненного пути
  const lifePathCounts = group_analysis.reduce((acc, person) => {
    const path = person.life_path;
    acc[path] = (acc[path] || 0) + 1;
    return acc;
  }, {});

  const lifePathData = {
    labels: Object.keys(lifePathCounts).map(path => `Путь ${path}`),
    datasets: [
      {
        label: 'Числа жизненного пути',
        data: Object.values(lifePathCounts),
        backgroundColor: [
          'rgba(168, 85, 247, 0.6)',
          'rgba(236, 72, 153, 0.6)',
          'rgba(14, 165, 233, 0.6)',
          'rgba(34, 197, 94, 0.6)',
          'rgba(251, 191, 36, 0.6)',
          'rgba(239, 68, 68, 0.6)',
          'rgba(156, 163, 175, 0.6)',
          'rgba(99, 102, 241, 0.6)',
          'rgba(245, 158, 11, 0.6)',
        ],
        borderColor: [
          'rgba(168, 85, 247, 1)',
          'rgba(236, 72, 153, 1)',
          'rgba(14, 165, 233, 1)',
          'rgba(34, 197, 94, 1)',
          'rgba(251, 191, 36, 1)',
          'rgba(239, 68, 68, 1)',
          'rgba(156, 163, 175, 1)',
          'rgba(99, 102, 241, 1)',
          'rgba(245, 158, 11, 1)',
        ],
        borderWidth: 2,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'bottom',
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const label = context.label || '';
            const value = context.parsed || 0;
            return `${label}: ${value}${context.datasetIndex === 0 && context.chart.data.datasets[0].label === 'Совместимость' ? '/10' : ''}`;
          }
        }
      }
    },
    maintainAspectRatio: false,
  };

  const getCompatibilityColor = (score) => {
    if (score >= 8) return 'bg-green-100 border-green-300 text-green-800';
    if (score >= 6) return 'bg-yellow-100 border-yellow-300 text-yellow-800';
    return 'bg-red-100 border-red-300 text-red-800';
  };

  const getRelationshipColor = (type) => {
    const colors = {
      'Зеркальные души': 'bg-purple-100 border-purple-300 text-purple-800',
      'Гармоничные партнеры': 'bg-green-100 border-green-300 text-green-800',
      'Взаимодополняющие': 'bg-blue-100 border-blue-300 text-blue-800',
      'Стимулирующие': 'bg-orange-100 border-orange-300 text-orange-800',
      'Вызывающие': 'bg-red-100 border-red-300 text-red-800',
      'Кармические': 'bg-gray-100 border-gray-300 text-gray-800',
    };
    return colors[type] || 'bg-gray-100 border-gray-300 text-gray-800';
  };

  return (
    <div className="space-y-6">
      {/* Общая информация */}
      <Card>
        <CardHeader>
          <CardTitle>Анализ групповой совместимости</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-muted-foreground">Ваш жизненный путь</p>
              <p className="text-2xl font-bold text-blue-600">{main_person.life_path}</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-sm text-muted-foreground">Средняя совместимость</p>
              <p className="text-2xl font-bold text-green-600">{average_compatibility.toFixed(1)}/10</p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <p className="text-sm text-muted-foreground">Людей в анализе</p>
              <p className="text-2xl font-bold text-purple-600">{group_analysis.length}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Диаграммы */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Совместимость по людям</CardTitle>
          </CardHeader>
          <CardContent>
            <div style={{ height: '300px', position: 'relative' }}>
              <Doughnut data={compatibilityData} options={chartOptions} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Типы отношений</CardTitle>
          </CardHeader>
          <CardContent>
            <div style={{ height: '300px', position: 'relative' }}>
              <Doughnut data={relationshipData} options={chartOptions} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Жизненные пути</CardTitle>
          </CardHeader>
          <CardContent>
            <div style={{ height: '300px', position: 'relative' }}>
              <Doughnut data={lifePathData} options={chartOptions} />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Детальный анализ каждого человека */}
      <Card>
        <CardHeader>
          <CardTitle>Детальный анализ отношений</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {group_analysis.map((person, index) => (
              <div key={index} className="p-4 border rounded-lg">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg">{person.name}</h3>
                    <p className="text-sm text-muted-foreground">
                      Дата рождения: {person.birth_date} • Жизненный путь: {person.life_path}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Badge className={getCompatibilityColor(person.compatibility_score)}>
                      {person.compatibility_score}/10
                    </Badge>
                    <Badge className={getRelationshipColor(person.relationship_type)}>
                      {person.relationship_type}
                    </Badge>
                  </div>
                </div>
                <div className="mt-3 p-3 bg-gray-50 rounded">
                  <p className="text-sm"><strong>Совет:</strong> {person.advice}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default GroupCompatibilityChart;