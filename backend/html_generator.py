"""
HTML генератор отчетов с полными расчетами и графиками
Заменяет PDF экспорт на более удобный HTML формат
"""
from datetime import datetime
from typing import Dict, Any, List
import base64
import json

def create_numerology_report_html(user_data: Dict[str, Any], all_data: Dict[str, Any], 
                                 vedic_data: Dict[str, Any] = None, charts_data: Dict[str, Any] = None,
                                 theme: str = "default", selected_calculations: List[str] = None) -> str:
    """
    Создает HTML отчет с полными нумерологическими расчетами из всех разделов
    """
    
    # CSS стили для разных тем
    css_styles = get_css_styles(theme)
    
    # JavaScript для базовой функциональности
    animation_script = """
        // Базовая функциональность без анимаций, которые могут сломать отображение
        function initializeReport() {
            // Убеждаемся что все карточки видимы
            const cards = document.querySelectorAll('.card');
            cards.forEach((card) => {
                // Принудительно убеждаемся в видимости
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
                card.style.visibility = 'visible';
            });
            
            console.log('NUMEROM отчёт загружен. Карточек:', cards.length);
        }
        
        // Запускаем немедленно и при загрузке DOM
        initializeReport();
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initializeReport);
        }
    """
    
    # Если не указаны выбранные расчёты, включаем все доступные
    if selected_calculations is None:
        selected_calculations = ['personal_numbers', 'pythagorean_square', 'vedic_times', 'planetary_route']
    
    # Генерируем разделы на основе выбранных расчётов
    content_sections = []
    
    # Всегда включаем заголовок и основную информацию
    content_sections.extend([
        generate_header(user_data),
        generate_personal_info(user_data)
    ])
    
    # Добавляем выбранные разделы
    if 'personal_numbers' in selected_calculations:
        content_sections.extend([
            generate_main_numbers(all_data.get('personal_numbers', {})),
            generate_planetary_strength(all_data.get('personal_numbers', {}))
        ])
    
    if 'name_numerology' in selected_calculations and user_data.get('full_name'):
        content_sections.append(generate_name_numerology_section(user_data))
    
    if 'car_numerology' in selected_calculations and user_data.get('car_number'):
        content_sections.append(generate_car_numerology_section(user_data))
    
    if 'address_numerology' in selected_calculations and (user_data.get('street') or user_data.get('house_number')):
        content_sections.append(generate_address_numerology_section(user_data))
    
    if 'pythagorean_square' in selected_calculations:
        content_sections.append(generate_pythagorean_square(all_data.get('pythagorean_square', {})))
    
    if 'vedic_times' in selected_calculations and all_data.get('vedic_times'):
        content_sections.append(generate_vedic_times_section(all_data.get('vedic_times', {})))
    
    if 'planetary_route' in selected_calculations and all_data.get('planetary_route'):
        content_sections.append(generate_planetary_route_section(all_data.get('planetary_route', {})))
    
    if 'compatibility' in selected_calculations or 'group_compatibility' in selected_calculations:
        content_sections.append(generate_compatibility_section(all_data))
    
    # Всегда включаем рекомендации и футер
    content_sections.extend([
        generate_recommendations(),
        generate_footer()
    ])
    
    # Генерируем HTML контент
    html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NUMEROM - Персональный отчет для {user_data.get('full_name', 'Пользователь')}</title>
    <style>
        {css_styles}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        {''.join(content_sections)}
    </div>
    
    <script>
        {generate_chart_scripts(charts_data) if charts_data else ''}
        
        // Функция печати
        function printReport() {{
            window.print();
        }}
        
        {animation_script}
        
        // Функция сохранения как PDF
        function saveAsPDF() {{
            window.print();
        }}
        
    </script>
</body>
</html>"""
    
    return html_content

def get_css_styles(theme: str) -> str:
    """Возвращает CSS стили для выбранной темы"""
    
    # Базовые стили
    if theme == "dark":
        theme_vars = {
            'body_bg': '#1a202c',
            'body_color': '#e2e8f0',
            'card_bg': '#2d3748',
            'border_color': '#4a5568',
            'header_color': '#f7fafc',
            'value_color': '#cbd5e0',
            'label_color': '#a0aec0',
            'info_item_bg': '#2d3748'
        }
    else:  # default theme
        theme_vars = {
            'body_bg': '#f7fafc',
            'body_color': '#333',
            'card_bg': 'white',
            'border_color': '#e2e8f0',
            'header_color': '#2d3748',
            'value_color': '#2d3748',
            'label_color': '#4a5568',
            'info_item_bg': '#f7fafc'
        }
    
    # Генерируем CSS с подстановкой переменных
    css_template = f"""
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: {theme_vars['body_color']};
            background-color: {theme_vars['body_bg']};
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .card {{
            background: {theme_vars['card_bg']};
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border: 1px solid {theme_vars['border_color']};
            opacity: 1;
            transform: translateY(0);
            transition: all 0.3s ease;
        }}
        
        .header {{
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            padding: 40px 20px;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        h2 {{
            color: {theme_vars['header_color']};
            font-size: 1.8em;
            margin-bottom: 16px;
            border-bottom: 3px solid {theme_vars['border_color']};
            padding-bottom: 8px;
        }}
        
        h3 {{
            color: {theme_vars['header_color']};
            font-size: 1.3em;
            margin-bottom: 12px;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }}
        
        .info-item {{
            background: {theme_vars['info_item_bg']};
            padding: 16px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        
        .info-label {{
            font-weight: 600;
            color: {theme_vars['label_color']};
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .info-value {{
            font-size: 1.1em;
            font-weight: 500;
            color: {theme_vars['value_color']};
            margin-top: 4px;
        }}
        
        .numbers-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }}
        
        .number-card {{
            text-align: center;
            padding: 20px;
            border-radius: 10px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            transition: transform 0.3s ease;
        }}
        
        .number-card:hover {{
            transform: translateY(-2px);
        }}
        
        .number-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 8px;
        }}
        
        .number-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        
        .pythagorean-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            max-width: 300px;
            margin: 0 auto 20px;
        }}
        
        .pythagorean-cell {{
            aspect-ratio: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            background: #f7fafc;
            font-weight: 600;
            position: relative;
            transition: all 0.3s ease;
        }}
        
        .pythagorean-cell:hover {{
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }}
        
        .planet-name {{
            font-size: 0.7em;
            color: #666;
            margin-bottom: 4px;
        }}
        
        .planet-numbers {{
            font-size: 1.4em;
            color: #2d3748;
        }}
        
        .energy-count {{
            font-size: 0.6em;
            color: #888;
            margin-top: 2px;
        }}
        
        .strength-indicator {{
            position: absolute;
            top: 4px;
            right: 4px;
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }}
        
        .strength-strong {{ background: #48bb78; }}
        .strength-normal {{ background: #ed8936; }}
        .strength-weak {{ background: #f56565; }}
        .strength-absent {{ background: #a0aec0; }}
        
        .chart-container {{
            position: relative;
            height: 400px;
            margin: 20px 0;
        }}
        
        .recommendations {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border-radius: 12px;
            padding: 30px;
        }}
        
        .recommendations h3 {{
            color: white;
            margin-bottom: 16px;
        }}
        
        .recommendation-section {{
            margin-bottom: 20px;
        }}
        
        .recommendation-section h4 {{
            color: #e2e8f0;
            font-size: 1.1em;
            margin-bottom: 8px;
        }}
        
        .recommendation-list {{
            list-style: none;
            padding: 0;
        }}
        
        .recommendation-list li {{
            padding: 6px 0;
            padding-left: 20px;
            position: relative;
        }}
        
        .recommendation-list li:before {{
            content: "✨";
            position: absolute;
            left: 0;
        }}
        
        .actions {{
            text-align: center;
            margin: 30px 0;
        }}
        
        .btn {{
            display: inline-block;
            padding: 12px 24px;
            margin: 0 8px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
            font-size: 1em;
        }}
        
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }}
        
        .footer {{
            text-align: center;
            color: #666;
            font-size: 0.9em;
            padding: 20px;
            border-top: 1px solid #e2e8f0;
            margin-top: 40px;
        }}
        
        @media print {{
            .actions {{
                display: none;
            }}
            
            .card {{
                box-shadow: none;
                border: 1px solid #ddd;
                break-inside: avoid;
                margin-bottom: 20px;
            }}
            
            .header {{
                background: #667eea !important;
                -webkit-print-color-adjust: exact;
            }}
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
            
            .header p {{
                font-size: 1em;
            }}
            
            .numbers-grid {{
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
            }}
            
            .info-grid {{
                grid-template-columns: 1fr;
                gap: 12px;
            }}
            
            .pythagorean-grid {{
                max-width: 250px;
                margin: 0 auto;
            }}
            
            .pythagorean-cell {{
                min-height: 60px;
                padding: 8px;
            }}
            
            .planet-name {{
                font-size: 0.6em;
            }}
            
            .planet-numbers {{
                font-size: 1.2em;
            }}
            
            .card {{
                padding: 16px;
                margin-bottom: 16px;
            }}
            
            h2 {{
                font-size: 1.5em;
            }}
            
            h3 {{
                font-size: 1.2em;
            }}
            
            .actions {{
                flex-direction: column;
            }}
            
            .btn {{
                width: 100%;
                margin: 4px 0;
            }}
        }}
        
        @media (max-width: 480px) {{
            .header h1 {{
                font-size: 1.8em;
            }}
            
            .numbers-grid {{
                grid-template-columns: 1fr;
                gap: 8px;
            }}
            
            .pythagorean-grid {{
                max-width: 200px;
            }}
            
            .pythagorean-cell {{
                min-height: 50px;
                padding: 6px;
            }}
            
            .card {{
                padding: 12px;
            }}
        }}
    """
    
    # For dark theme, add additional overrides directly to css_template
    if theme == "dark":
        css_template += """
            body {
                background: #1a202c !important;
                color: #e2e8f0 !important;
            }
            
            .card {
                background: #2d3748 !important;
                color: #e2e8f0 !important;
            }
            
            .info-item {
                background: #374151 !important;
            }
            
            .pythagorean-cell {
                background: #374151 !important;
                border-color: #4a5568 !important;
                color: #e2e8f0 !important;
            }
        """
    
    return css_template

def generate_header(user_data: Dict[str, Any]) -> str:
    """Генерирует заголовок отчета"""
    return f"""
    <div class="header">
        <h1>🔢 NUMEROM</h1>
        <p>Персональный нумерологический отчет</p>
        <p>для {user_data.get('full_name', 'Пользователь')}</p>
    </div>
    """

def generate_personal_info(user_data: Dict[str, Any]) -> str:
    """Генерирует секцию с персональной информацией"""
    return f"""
    <div class="card">
        <h2>📋 Персональные данные</h2>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Имя</div>
                <div class="info-value">{user_data.get('full_name', 'Не указано')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Email</div>
                <div class="info-value">{user_data.get('email', 'Не указано')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Дата рождения</div>
                <div class="info-value">{user_data.get('birth_date', 'Не указано')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Город</div>
                <div class="info-value">{user_data.get('city', 'Не указано')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Дата создания отчета</div>
                <div class="info-value">{datetime.now().strftime('%d.%m.%Y %H:%M')}</div>
            </div>
        </div>
    </div>
    """

def generate_main_numbers(calculations: Dict[str, Any]) -> str:
    """Генерирует секцию с основными числами"""
    if not calculations:
        return ""
    
    return f"""
    <div class="card">
        <h2>✨ Основные числа личности</h2>
        <div class="numbers-grid">
            <div class="number-card" style="background: linear-gradient(135deg, #ff6b35, #f7931e);">
                <div class="number-value">{calculations.get('soul_number', '?')}</div>
                <div class="number-label">Число души (ЧД)</div>
            </div>
            <div class="number-card" style="background: linear-gradient(135deg, #667eea, #764ba2);">
                <div class="number-value">{calculations.get('mind_number', '?')}</div>
                <div class="number-label">Число ума (ЧУ)</div>
            </div>
            <div class="number-card" style="background: linear-gradient(135deg, #f093fb, #f5576c);">
                <div class="number-value">{calculations.get('destiny_number', '?')}</div>
                <div class="number-label">Число судьбы (ЧС)</div>
            </div>
            <div class="number-card" style="background: linear-gradient(135deg, #4facfe, #00f2fe);">
                <div class="number-value">{calculations.get('helping_mind_number', '?')}</div>
                <div class="number-label">Помогающее число ума (ЧУ*)</div>
            </div>
            <div class="number-card" style="background: linear-gradient(135deg, #43e97b, #38f9d7);">
                <div class="number-value">{calculations.get('wisdom_number', '?')}</div>
                <div class="number-label">Число мудрости (ЧМ)</div>
            </div>
            <div class="number-card" style="background: linear-gradient(135deg, #fa709a, #fee140);">
                <div class="number-value">{calculations.get('ruling_number', '?')}</div>
                <div class="number-label">Правящее число (ПЧ)</div>
            </div>
        </div>
    </div>
    """

def generate_pythagorean_square(calculations: Dict[str, Any]) -> str:
    """Генерирует визуализацию квадрата Пифагора"""
    if not calculations:
        return ""
    
    square_matrix = calculations.get('square', [['', '', ''], ['', '', ''], ['', '', '']])
    additional_numbers = calculations.get('additional_numbers', [])
    horizontal_sums = calculations.get('horizontal_sums', [])
    vertical_sums = calculations.get('vertical_sums', [])
    diagonal_sums = calculations.get('diagonal_sums', [])
    
    planet_names = [
        ['Солнце', 'Луна', 'Юпитер'],
        ['Раху', 'Центр', 'Венера'],
        ['Кету', 'Сатурн', 'Марс']
    ]
    
    colors = [
        ['#ff6b35', '#87ceeb', '#ffd700'],
        ['#8b4513', '#90ee90', '#ff69b4'],
        ['#9370db', '#4169e1', '#dc143c']
    ]
    
    cells_html = ""
    for i in range(3):
        for j in range(3):
            cell_content = square_matrix[i][j] if square_matrix[i][j] else '—'
            color = colors[i][j]
            
            cells_html += f"""
            <div class="pythagorean-cell" style="border-color: {color};">
                <div class="planet-name">{planet_names[i][j]}</div>
                <div class="planet-numbers" style="color: {color};">{cell_content}</div>
            </div>
            """
    
    additional_numbers_html = ""
    if additional_numbers:
        additional_numbers_html = f"""
        <div class="additional-numbers">
            <h4>Дополнительные числа:</h4>
            <div class="numbers-row">
                <span>А1: {additional_numbers[0] if len(additional_numbers) > 0 else '?'}</span>
                <span>А2: {additional_numbers[1] if len(additional_numbers) > 1 else '?'}</span>
                <span>А3: {additional_numbers[2] if len(additional_numbers) > 2 else '?'}</span>
                <span>А4: {additional_numbers[3] if len(additional_numbers) > 3 else '?'}</span>
            </div>
        </div>
        """
    
    return f"""
    <div class="card">
        <h2>⭐ Квадрат Пифагора - Матрица энергий</h2>
        <div class="pythagorean-grid">
            {cells_html}
        </div>
        {additional_numbers_html}
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Горизонтальные суммы</div>
                <div class="info-value">{horizontal_sums}</div>
                <p style="font-size: 0.85em; margin-top: 4px; color: #666;">Материальная сфера</p>
            </div>
            <div class="info-item">
                <div class="info-label">Вертикальные суммы</div>
                <div class="info-value">{vertical_sums}</div>
                <p style="font-size: 0.85em; margin-top: 4px; color: #666;">Духовная сфера</p>
            </div>
            <div class="info-item">
                <div class="info-label">Диагональные суммы</div>
                <div class="info-value">{diagonal_sums}</div>
                <p style="font-size: 0.85em; margin-top: 4px; color: #666;">Баланс</p>
            </div>
        </div>
    </div>
    """

def generate_vedic_section(vedic_data: Dict[str, Any]) -> str:
    """Генерирует секцию ведической нумерологии"""
    if not vedic_data:
        return ""
    
    return f"""
    <div class="card">
        <h2>🕉️ Ведическая нумерология</h2>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Число рождения (Джанма)</div>
                <div class="info-value">{vedic_data.get('janma_ank', '?')} - {vedic_data.get('janma_ank_sanskrit', '')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Число имени (Нама)</div>
                <div class="info-value">{vedic_data.get('nama_ank', '?')} - {vedic_data.get('nama_ank_sanskrit', '')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Число удачи (Бхагья)</div>
                <div class="info-value">{vedic_data.get('bhagya_ank', '?')} - {vedic_data.get('bhagya_ank_sanskrit', '')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Число души (Атма)</div>
                <div class="info-value">{vedic_data.get('atma_ank', '?')} - {vedic_data.get('atma_ank_sanskrit', '')}</div>
            </div>
        </div>
    </div>
    """

def generate_charts_section(charts_data: Dict[str, Any]) -> str:
    """Генерирует секцию с графиками"""
    if not charts_data:
        return ""
    
    return f"""
    <div class="card">
        <h2>📈 Планетарные энергии</h2>
        <div class="chart-container">
            <canvas id="planetaryChart"></canvas>
        </div>
    </div>
    """

def generate_chart_scripts(charts_data: Dict[str, Any]) -> str:
    """Генерирует JavaScript для графиков"""
    if not charts_data or 'planetary_energy' not in charts_data:
        return ""
    
    # Преобразуем данные для Chart.js
    planetary_energy = charts_data['planetary_energy']
    days = [entry.get('day_name', f"День {i+1}") for i, entry in enumerate(planetary_energy)]
    
    datasets = []
    colors = ['#FF6B35', '#87CEEB', '#DC143C', '#32CD32', '#FFD700', '#FF69B4', '#4169E1']
    planets = ['surya', 'chandra', 'mangal', 'budha', 'guru', 'shukra', 'shani']
    planet_names = ['Сурья', 'Чандра', 'Мангал', 'Будха', 'Гуру', 'Шукра', 'Шани']
    
    for i, planet in enumerate(planets[:7]):
        values = [entry.get('planetary_energies', {}).get(planet, 50) for entry in planetary_energy]
        datasets.append({
            'label': planet_names[i],
            'data': values,
            'borderColor': colors[i],
            'backgroundColor': colors[i] + '20',
            'tension': 0.4
        })
    
    return f"""
        const ctx = document.getElementById('planetaryChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(days)},
                datasets: {json.dumps(datasets)}
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Планетарные энергии по дням'
                    }},
                    legend: {{
                        display: true,
                        position: 'bottom'
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        title: {{
                            display: true,
                            text: 'Уровень энергии'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'Дни'
                        }}
                    }}
                }}
            }}
        }});
    """

def generate_recommendations() -> str:
    """Генерирует секцию с рекомендациями"""
    return f"""
    <div class="recommendations">
        <h3>💡 Персональные рекомендации</h3>
        
        <div class="recommendation-section">
            <h4>🌟 Сильные стороны:</h4>
            <ul class="recommendation-list">
                <li>Используйте свои природные таланты для достижения целей</li>
                <li>Развивайте качества своего числа жизненного пути</li>
                <li>Следуйте интуиции в принятии важных решений</li>
            </ul>
        </div>
        
        <div class="recommendation-section">
            <h4>🔧 Области для развития:</h4>
            <ul class="recommendation-list">
                <li>Работайте над балансом материального и духовного</li>
                <li>Укрепляйте слабые позиции в квадрате Пифагора</li>
                <li>Используйте ведические практики для гармонизации энергий</li>
            </ul>
        </div>
        
        <div class="recommendation-section">
            <h4>🎯 Благоприятные направления:</h4>
            <ul class="recommendation-list">
                <li>Следуйте планетарным часам для важных дел</li>
                <li>Избегайте неблагоприятных периодов (Раху Кала)</li>
                <li>Практикуйте медитацию в период Абхиджит Мухурта</li>
            </ul>
        </div>
    </div>
    """

def generate_footer() -> str:
    """Генерирует подвал отчета"""
    return f"""
    <div class="actions">
        <button class="btn" onclick="printReport()">🖨️ Печать</button>
        <button class="btn" onclick="exportToPDF()">📄 Сохранить как PDF</button>
        <button class="btn" onclick="window.location.reload()">🔄 Обновить</button>
    </div>
    
    <div class="footer">
        <p>Создано с помощью <strong>NUMEROM</strong> - Древняя мудрость для современной жизни</p>
        <p>Дата создания: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
        <p>© 2024 NUMEROM. Все права защищены.</p>
    </div>
    """

def create_compatibility_html(user1_data: Dict, user2_data: Dict, compatibility_result: Dict, theme: str = "default") -> str:
    """Создает HTML отчет о совместимости"""
    css_styles = get_css_styles(theme)
    
    compatibility_score = compatibility_result.get('compatibility_score', 0)
    score_color = "#28a745" if compatibility_score > 70 else "#ffc107" if compatibility_score > 40 else "#dc3545"
    
    html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NUMEROM - Анализ совместимости</title>
    <style>{css_styles}</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💕 NUMEROM</h1>
            <p>Анализ совместимости</p>
        </div>
        
        <div class="card">
            <h2>👫 Партнеры</h2>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Партнер 1</div>
                    <div class="info-value">Дата: {user1_data.get('birth_date', 'Не указано')}</div>
                    <div class="info-value">Число жизни: {compatibility_result.get('person1_life_path', '?')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Партнер 2</div>
                    <div class="info-value">Дата: {user2_data.get('birth_date', 'Не указано')}</div>
                    <div class="info-value">Число жизни: {compatibility_result.get('person2_life_path', '?')}</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>📊 Результат совместимости</h2>
            <div style="text-align: center; margin: 30px 0;">
                <div style="font-size: 4em; font-weight: bold; color: {score_color}; margin-bottom: 10px;">
                    {compatibility_score}%
                </div>
                <p style="font-size: 1.2em; color: #666;">Общий уровень совместимости</p>
            </div>
            <div class="info-item">
                <p style="font-size: 1.1em; line-height: 1.8;">
                    {compatibility_result.get('description', 'Описание недоступно')}
                </p>
            </div>
        </div>
        
        {generate_footer()}
    </div>
</body>
</html>
    """
    
    return html_content

def generate_planetary_strength(personal_numbers: Dict[str, Any]) -> str:
    """Генерирует секцию с планетарными силами"""
    if not personal_numbers or not personal_numbers.get('planetary_strength'):
        return ""
    
    strength_data = personal_numbers.get('planetary_strength', {})
    
    return f"""
    <div class="card">
        <h2>🪐 Сила планет по дням недели</h2>
        <p>День недели рождения: <strong>{personal_numbers.get('birth_weekday', 'Не определено')}</strong></p>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Солнце</div>
                <div class="info-value">{strength_data.get('Солнце', 0)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Луна</div>
                <div class="info-value">{strength_data.get('Луна', 0)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Марс</div>
                <div class="info-value">{strength_data.get('Марс', 0)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Меркурий</div>
                <div class="info-value">{strength_data.get('Меркурий', 0)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Юпитер</div>
                <div class="info-value">{strength_data.get('Юпитер', 0)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Венера</div>
                <div class="info-value">{strength_data.get('Венера', 0)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Сатурн</div>
                <div class="info-value">{strength_data.get('Сатурн', 0)}</div>
            </div>
        </div>
    </div>
    """

def generate_vedic_times_section(vedic_times: Dict[str, Any]) -> str:
    """Генерирует секцию с ведическими временами"""
    if not vedic_times:
        return ""
    
    return f"""
    <div class="card">
        <h2>⏰ Ведические времена</h2>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Раху Кала (неблагоприятное время)</div>
                <div class="info-value">{vedic_times.get('rahu_kala', 'Не определено')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Абхиджит Мухурта (благоприятное время)</div>
                <div class="info-value">{vedic_times.get('abhijit_muhurta', 'Не определено')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Планетарный час</div>
                <div class="info-value">{vedic_times.get('planetary_hour', 'Не определено')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Текущая планета</div>
                <div class="info-value">{vedic_times.get('current_planet', 'Не определено')}</div>
            </div>
        </div>
    </div>
    """

def generate_planetary_route_section(planetary_route: Dict[str, Any]) -> str:
    """Генерирует секцию с планетарным маршрутом"""
    if not planetary_route:
        return ""
    
    # Handle both 'route' and 'daily_route' formats
    route_data = planetary_route.get('route', [])
    daily_route = planetary_route.get('daily_route', [])
    
    if not route_data and not daily_route:
        return ""
    
    route_html = ""
    
    # Handle daily_route format (simple list of strings)
    if daily_route:
        for i, period in enumerate(daily_route):
            route_html += f"""
            <div class="info-item">
                <div class="info-label">Период {i+1}</div>
                <div class="info-value">{period}</div>
            </div>
            """
    
    # Handle route format (list of dictionaries)
    if route_data:
        for i, period in enumerate(route_data):
            route_html += f"""
            <div class="info-item">
                <div class="info-label">Период {i+1} ({period.get('age_range', 'Не определено')})</div>
                <div class="info-value">Планета: {period.get('planet', 'Не определено')}</div>
                <div class="info-value">Влияние: {period.get('influence', 'Не определено')}</div>
            </div>
            """
    
    return f"""
    <div class="card">
        <h2>🛤️ Планетарный маршрут жизни</h2>
        <p>Дата: <strong>{planetary_route.get('date', 'Не определено')}</strong></p>
        <p>Город: <strong>{planetary_route.get('city', 'Не определено')}</strong></p>
        <div class="info-grid">
            {route_html}
        </div>
        <div class="info-item">
            <div class="info-label">Общее описание</div>
            <div class="info-value">{planetary_route.get('description', 'Планетарный маршрут показывает влияние различных планет на разные периоды жизни')}</div>
        </div>
    </div>
    """

def generate_name_numerology_section(user_data: Dict[str, Any]) -> str:
    """Генерирует секцию нумерологии имени"""
    if not user_data.get('full_name'):
        return ""
    
    from numerology import calculate_name_numerology
    
    try:
        name_data = calculate_name_numerology(user_data['full_name'])
        
        return f"""
        <div class="card">
            <h2>📝 Нумерология имени и фамилии</h2>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Полное имя</div>
                    <div class="info-value">{user_data['full_name']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Число имени</div>
                    <div class="info-value">{name_data.get('name_number', 'Не определено')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Интерпретация</div>
                    <div class="info-value">{name_data.get('interpretation', 'Интерпретация недоступна')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Совместимость с датой рождения</div>
                    <div class="info-value">{name_data.get('compatibility', 'Не определено')}</div>
                </div>
            </div>
        </div>
        """
    except:
        return f"""
        <div class="card">
            <h2>📝 Нумерология имени и фамилии</h2>
            <div class="info-item">
                <div class="info-label">Имя</div>
                <div class="info-value">{user_data['full_name']}</div>
                <p>Нумерологический анализ имени временно недоступен</p>
            </div>
        </div>
        """

def generate_car_numerology_section(user_data: Dict[str, Any]) -> str:
    """Генерирует секцию нумерологии автомобиля"""
    if not user_data.get('car_number'):
        return ""
    
    from numerology import calculate_car_number_numerology
    
    try:
        car_data = calculate_car_number_numerology(user_data['car_number'])
        
        return f"""
        <div class="card">
            <h2>🚗 Нумерология автомобиля</h2>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Номер автомобиля</div>
                    <div class="info-value">{car_data.get('car_number', 'Не определено')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Нумерологическое значение</div>
                    <div class="info-value">{car_data.get('numerology_value', 'Не определено')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Общая сумма</div>
                    <div class="info-value">{car_data.get('total_sum', 'Не определено')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Интерпретация</div>
                    <div class="info-value">{car_data.get('interpretation', 'Интерпретация недоступна')}</div>
                </div>
            </div>
        </div>
        """
    except:
        return f"""
        <div class="card">
            <h2>🚗 Нумерология автомобиля</h2>
            <div class="info-item">
                <div class="info-label">Номер</div>
                <div class="info-value">{user_data['car_number']}</div>
                <p>Нумерологический анализ автомобиля временно недоступен</p>
            </div>
        </div>
        """

def generate_address_numerology_section(user_data: Dict[str, Any]) -> str:
    """Генерирует секцию нумерологии адреса"""
    from numerology import calculate_address_numerology
    
    try:
        address_data = calculate_address_numerology(
            street=user_data.get('street'),
            house_number=user_data.get('house_number'),
            apartment_number=user_data.get('apartment_number'),
            postal_code=user_data.get('postal_code')
        )
        
        address_html = ""
        
        if user_data.get('street'):
            address_html += f"""
            <div class="info-item">
                <div class="info-label">Улица</div>
                <div class="info-value">{user_data['street']}</div>
            </div>"""
        
        if address_data.get('house_numerology'):
            house_data = address_data['house_numerology']
            address_html += f"""
            <div class="info-item">
                <div class="info-label">Дом № {user_data.get('house_number', '')}</div>
                <div class="info-value">Значение: {house_data.get('value', 'Не определено')}</div>
                <p style="font-size: 0.9em; margin-top: 5px;">{house_data.get('interpretation', '')}</p>
            </div>"""
        
        if address_data.get('apartment_numerology'):
            apt_data = address_data['apartment_numerology']
            address_html += f"""
            <div class="info-item">
                <div class="info-label">Квартира № {user_data.get('apartment_number', '')}</div>
                <div class="info-value">Значение: {apt_data.get('value', 'Не определено')}</div>
                <p style="font-size: 0.9em; margin-top: 5px;">{apt_data.get('interpretation', '')}</p>
            </div>"""
        
        if address_data.get('postal_code_numerology'):
            postal_data = address_data['postal_code_numerology']
            address_html += f"""
            <div class="info-item">
                <div class="info-label">Индекс {user_data.get('postal_code', '')}</div>
                <div class="info-value">Значение: {postal_data.get('value', 'Не определено')}</div>
                <p style="font-size: 0.9em; margin-top: 5px;">{postal_data.get('interpretation', '')}</p>
            </div>"""
        
        return f"""
        <div class="card">
            <h2>🏠 Нумерология адреса проживания</h2>
            <div class="info-grid">
                {address_html}
            </div>
        </div>
        """
    except:
        return f"""
        <div class="card">
            <h2>🏠 Нумерология адреса проживания</h2>
            <div class="info-item">
                <div class="info-label">Адрес</div>
                <div class="info-value">
                    {user_data.get('street', '')} 
                    {user_data.get('house_number', '')} 
                    {user_data.get('apartment_number', '')}
                </div>
                <p>Нумерологический анализ адреса временно недоступен</p>
            </div>
        </div>
        """

def generate_compatibility_section(all_data: Dict[str, Any]) -> str:
    """Генерирует секцию совместимости"""
    compatibility_html = ""
    
    # Парная совместимость
    if all_data.get('compatibility'):
        compatibility_data = all_data['compatibility']
        compatibility_html += f"""
        <div class="info-item">
            <div class="info-label">Парная совместимость</div>
            <div class="info-value">Оценка: {compatibility_data.get('compatibility_score', 'Не определено')}/10</div>
            <p style="font-size: 0.9em; margin-top: 5px;">{compatibility_data.get('description', '')}</p>
        </div>"""
    
    # Групповая совместимость
    if all_data.get('group_compatibility'):
        group_data = all_data['group_compatibility']
        compatibility_html += f"""
        <div class="info-item">
            <div class="info-label">Групповая совместимость</div>
            <div class="info-value">Средняя оценка: {group_data.get('average_compatibility', 'Не определено')}/10</div>
            <div class="info-value">Анализируемых людей: {len(group_data.get('group_analysis', []))}</div>
        </div>"""
    
    if compatibility_html:
        return f"""
        <div class="card">
            <h2>❤️ Анализ совместимости</h2>
            <div class="info-grid">
                {compatibility_html}
            </div>
        </div>
        """
    
    return ""