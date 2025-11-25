"""
HTML генератор отчетов с полными расчетами и графиками
Заменяет PDF экспорт на более удобный HTML формат
"""
from datetime import datetime
from typing import Dict, Any, List
import base64
import json
from html_generator_helpers import (
    calculate_behavior_fractal, calculate_task_numbers,
    get_planet_color, get_planet_symbol, get_planet_name,
    get_planet_interpretation, get_missing_planet_advice
)

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
    
    # Генерируем табы и их содержимое
    tabs_html = generate_tabs_structure(user_data, all_data, vedic_data, charts_data, selected_calculations)
    
    # Генерируем HTML контент с табами
    html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NUMEROM - Персональный отчет для {user_data.get('full_name', 'Пользователь')}</title>
    <style>
        {css_styles}
        {get_tabs_css_styles(theme)}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        {generate_header(user_data)}
        {tabs_html}
    </div>
    
    <script>
        {generate_chart_scripts(charts_data) if charts_data else ''}
        
        // Функция переключения табов
        function switchTab(tabName) {{
            // Скрываем все табы
            const allTabs = document.querySelectorAll('.tab-content');
            allTabs.forEach(tab => {{
                tab.style.display = 'none';
            }});
            
            // Убираем активный класс у всех кнопок
            const allButtons = document.querySelectorAll('.tab-button');
            allButtons.forEach(btn => {{
                btn.classList.remove('active');
            }});
            
            // Показываем выбранный таб
            const selectedTab = document.getElementById('tab-' + tabName);
            if (selectedTab) {{
                selectedTab.style.display = 'block';
            }}
            
            // Добавляем активный класс к кнопке
            const selectedButton = document.querySelector('[onclick="switchTab(\\'' + tabName + '\\')"]');
            if (selectedButton) {{
                selectedButton.classList.add('active');
            }}
        }}
        
        // Инициализация: показываем первый таб
        document.addEventListener('DOMContentLoaded', function() {{
            switchTab('overview');
            {animation_script}
        }});
        
        // Функция печати
        function printReport() {{
            window.print();
        }}
        
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
        
        /* Стили для планетарных цветов и градиентов */
        .fractal-digit {{
            transition: all 0.3s ease;
        }}
        
        .fractal-digit:hover {{
            transform: scale(1.1);
            box-shadow: 0 8px 12px -2px rgba(0, 0, 0, 0.3);
        }}
        
        .task-number-card {{
            transition: all 0.3s ease;
        }}
        
        .task-number-card:hover {{
            transform: scale(1.05);
        }}
        
        .planet-card {{
            transition: all 0.3s ease;
        }}
        
        .planet-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
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

def get_tabs_css_styles(theme: str) -> str:
    """Возвращает CSS стили для табов"""
    if theme == "dark":
        bg_color = "#1f2937"
        border_color = "#374151"
        text_color = "#f3f4f6"
        active_bg = "#3b82f6"
        hover_bg = "#4b5563"
    else:
        bg_color = "#ffffff"
        border_color = "#e5e7eb"
        text_color = "#111827"
        active_bg = "#3b82f6"
        hover_bg = "#f3f4f6"
    
    return f"""
        .tabs-container {{
            margin-top: 30px;
        }}
        
        .tabs-list {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 8px;
            margin-bottom: 24px;
            padding: 4px;
            background: {bg_color};
            border-radius: 8px;
            border: 1px solid {border_color};
        }}
        
        .tab-button {{
            padding: 10px 16px;
            border: none;
            background: transparent;
            color: {text_color};
            cursor: pointer;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }}
        
        .tab-button:hover {{
            background: {hover_bg};
        }}
        
        .tab-button.active {{
            background: {active_bg};
            color: white;
        }}
        
        .tab-content {{
            display: none;
            animation: fadeIn 0.3s;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .tab-icon {{
            width: 16px;
            height: 16px;
        }}
    """

def generate_tabs_structure(user_data: Dict[str, Any], all_data: Dict[str, Any], 
                            vedic_data: Dict[str, Any] = None, charts_data: Dict[str, Any] = None,
                            selected_calculations: List[str] = None) -> str:
    """Генерирует структуру табов как на фронтенде"""
    
    # Генерируем контент для каждого таба
    overview_content = generate_overview_tab(user_data, all_data)
    charts_content = generate_charts_tab(all_data, charts_data, user_data)
    planetary_content = generate_planetary_tab(all_data)
    route_content = generate_route_tab(all_data)
    compatibility_content = generate_compatibility_tab(all_data)
    name_content = generate_name_tab(user_data, all_data)
    address_content = generate_address_tab(user_data, all_data)
    car_content = generate_car_tab(user_data, all_data)
    
    tabs_html = f"""
    <div class="tabs-container">
        <div class="tabs-list">
            <button class="tab-button active" onclick="switchTab('overview')">
                <span class="tab-icon">👤</span>
                <span>Обзор</span>
            </button>
            <button class="tab-button" onclick="switchTab('charts')">
                <span class="tab-icon">📊</span>
                <span>Графики</span>
            </button>
            <button class="tab-button" onclick="switchTab('planetary')">
                <span class="tab-icon">🪐</span>
                <span>Планеты</span>
            </button>
            <button class="tab-button" onclick="switchTab('route')">
                <span class="tab-icon">🗺️</span>
                <span>Маршрут</span>
            </button>
            <button class="tab-button" onclick="switchTab('compatibility')">
                <span class="tab-icon">👥</span>
                <span>Совместимость</span>
            </button>
            <button class="tab-button" onclick="switchTab('name')">
                <span class="tab-icon">⭐</span>
                <span>Имя</span>
            </button>
            <button class="tab-button" onclick="switchTab('address')">
                <span class="tab-icon">📍</span>
                <span>Адрес</span>
            </button>
            <button class="tab-button" onclick="switchTab('car')">
                <span class="tab-icon">🚗</span>
                <span>Авто</span>
            </button>
        </div>
        
        <div id="tab-overview" class="tab-content active">
            {overview_content}
        </div>
        
        <div id="tab-charts" class="tab-content">
            {charts_content}
        </div>
        
        <div id="tab-planetary" class="tab-content">
            {planetary_content}
        </div>
        
        <div id="tab-route" class="tab-content">
            {route_content}
        </div>
        
        <div id="tab-compatibility" class="tab-content">
            {compatibility_content}
        </div>
        
        <div id="tab-name" class="tab-content">
            {name_content}
        </div>
        
        <div id="tab-address" class="tab-content">
            {address_content}
        </div>
        
        <div id="tab-car" class="tab-content">
            {car_content}
        </div>
    </div>
    """
    
    return tabs_html

def generate_overview_tab(user_data: Dict[str, Any], all_data: Dict[str, Any]) -> str:
    """Генерирует контент таба 'Обзор'"""
    personal_numbers = all_data.get('personal_numbers', {})
    
    # Разделяем имя и фамилию
    full_name = user_data.get('full_name', '')
    name_parts = full_name.split() if full_name else []
    first_name = name_parts[0] if name_parts else 'Не указано'
    last_name = name_parts[-1] if len(name_parts) > 1 else 'Не указано'
    
    # Генерируем секцию "Ключевые числа" с фракталом и персональными числами
    key_numbers_html = ""
    if user_data and user_data.get('birth_date'):
        fractal = calculate_behavior_fractal(user_data.get('birth_date'))
        if fractal and personal_numbers:
            d1_color = get_planet_color(fractal['digit1'])
            d2_color = get_planet_color(fractal['digit2'])
            d3_color = get_planet_color(fractal['digit3'])
            d4_color = get_planet_color(fractal['digit4'])
            
            key_numbers_html = f"""
    <div class="card">
        <h2>⭐ Ключевые числа</h2>
        <div style="margin-bottom: 24px;">
            <h4 style="font-size: 1.1em; font-weight: 600; margin-bottom: 16px; color: #374151;">Фрактал поведения</h4>
            <div style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-bottom: 20px;">
                <div style="text-align: center;">
                    <div style="width: 64px; height: 64px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: bold; border: 2px solid {d1_color}; background: {d1_color}25; color: {d1_color}; box-shadow: 0 4px 6px -1px {d1_color}40, 0 2px 4px -1px {d1_color}20;">{fractal['digit1']}</div>
                    <div style="font-size: 11px; margin-top: 6px; font-weight: 500; color: {d1_color}; background: {d1_color}15; padding: 3px 6px; border-radius: 4px; max-width: 60px; margin-left: auto; margin-right: auto;">День</div>
                </div>
                <div style="text-align: center;">
                    <div style="width: 64px; height: 64px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: bold; border: 2px solid {d2_color}; background: {d2_color}25; color: {d2_color}; box-shadow: 0 4px 6px -1px {d2_color}40, 0 2px 4px -1px {d2_color}20;">{fractal['digit2']}</div>
                    <div style="font-size: 11px; margin-top: 6px; font-weight: 500; color: {d2_color}; background: {d2_color}15; padding: 3px 6px; border-radius: 4px; max-width: 60px; margin-left: auto; margin-right: auto;">Месяц</div>
                </div>
                <div style="text-align: center;">
                    <div style="width: 64px; height: 64px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: bold; border: 2px solid {d3_color}; background: {d3_color}25; color: {d3_color}; box-shadow: 0 4px 6px -1px {d3_color}40, 0 2px 4px -1px {d3_color}20;">{fractal['digit3']}</div>
                    <div style="font-size: 11px; margin-top: 6px; font-weight: 500; color: {d3_color}; background: {d3_color}15; padding: 3px 6px; border-radius: 4px; max-width: 60px; margin-left: auto; margin-right: auto;">Год</div>
                </div>
                <div style="text-align: center;">
                    <div style="width: 64px; height: 64px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: bold; border: 2px solid {d4_color}; background: {d4_color}25; color: {d4_color}; box-shadow: 0 4px 6px -1px {d4_color}40, 0 2px 4px -1px {d4_color}20;">{fractal['digit4']}</div>
                    <div style="font-size: 11px; margin-top: 6px; font-weight: 500; color: {d4_color}; background: {d4_color}15; padding: 3px 6px; border-radius: 4px; max-width: 60px; margin-left: auto; margin-right: auto;">Сумма</div>
                </div>
            </div>
        </div>
        
        <div>
            <h4 style="font-size: 1.1em; font-weight: 600; margin-bottom: 16px; color: #374151;">Персональные числа</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px;">
"""
            # Добавляем персональные числа
            numbers_to_show = [
                ('soul_number', 'Число души (ЧД)'),
                ('mind_number', 'Число ума (ЧУ)'),
                ('destiny_number', 'Число судьбы (ЧС)'),
                ('wisdom_number', 'Число мудрости (ЧМ)'),
                ('ruling_number', 'Правящее число (ПЧ)')
            ]
            
            for key, label in numbers_to_show:
                value = personal_numbers.get(key)
                if value is not None and value != '':
                    color = get_planet_color(value)
                    key_numbers_html += f"""
                <div style="text-align: center; padding: 16px; border-radius: 8px; border: 2px solid {color}; background: {color}15; transition: all 0.3s ease;">
                    <div style="font-size: 2em; font-weight: bold; margin-bottom: 8px; color: {color};">{value}</div>
                    <div style="font-size: 0.85em; font-weight: 500; color: #374151;">{label}</div>
                </div>
"""
            
            key_numbers_html += """
            </div>
        </div>
    </div>
"""
    
    return f"""
    <div class="card">
        <h2>👤 Личная информация</h2>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Имя</div>
                <div class="info-value">{first_name}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Фамилия</div>
                <div class="info-value">{last_name}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Email</div>
                <div class="info-value">{user_data.get('email', 'Не указано')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Дата рождения</div>
                <div class="info-value">{user_data.get('birth_date', 'Не указана')}</div>
            </div>
        </div>
    </div>
    
    {key_numbers_html}
    
    <div class="card">
        <h2>📋 Краткий обзор разделов</h2>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">📊 Графики</div>
                <div class="info-value">Пифагорейский квадрат и планетарные энергии</div>
            </div>
            <div class="info-item">
                <div class="info-label">🪐 Планетарный маршрут</div>
                <div class="info-value">Ежедневные рекомендации</div>
            </div>
            <div class="info-item">
                <div class="info-label">👥 Совместимость</div>
                <div class="info-value">Личная и групповая</div>
            </div>
            <div class="info-item">
                <div class="info-label">⭐ Нумерология</div>
                <div class="info-value">Имя, адрес, автомобиль</div>
            </div>
        </div>
    </div>
    """

def generate_charts_tab(all_data: Dict[str, Any], charts_data: Dict[str, Any] = None, user_data: Dict[str, Any] = None) -> str:
    """Генерирует контент таба 'Графики'"""
    content = ""
    
    # Фрактал поведения с полной интерпретацией
    if user_data and user_data.get('birth_date'):
        fractal = calculate_behavior_fractal(user_data.get('birth_date'))
        if fractal:
            d1_color = get_planet_color(fractal['digit1'])
            d2_color = get_planet_color(fractal['digit2'])
            d3_color = get_planet_color(fractal['digit3'])
            d4_color = get_planet_color(fractal['digit4'])
            
            content += f"""
            <div class="card">
                <h2>🔢 Фрактал поведения</h2>
                <p style="margin-bottom: 20px; color: #666;">Четырёхзначный код вашего характера и поведения</p>
                
                <div style="display: flex; gap: 16px; justify-content: center; margin: 20px 0; flex-wrap: wrap;">
                    <div style="text-align: center;">
                        <div style="width: 80px; height: 80px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 36px; font-weight: bold; border: 2px solid {d1_color}; background: {d1_color}25; color: {d1_color}; box-shadow: 0 4px 6px -1px {d1_color}40, 0 2px 4px -1px {d1_color}20;">{fractal['digit1']}</div>
                        <div style="font-size: 12px; margin-top: 8px; font-weight: 500; color: {d1_color}; background: {d1_color}15; padding: 4px 8px; border-radius: 4px;">День</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="width: 80px; height: 80px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 36px; font-weight: bold; border: 2px solid {d2_color}; background: {d2_color}25; color: {d2_color}; box-shadow: 0 4px 6px -1px {d2_color}40, 0 2px 4px -1px {d2_color}20;">{fractal['digit2']}</div>
                        <div style="font-size: 12px; margin-top: 8px; font-weight: 500; color: {d2_color}; background: {d2_color}15; padding: 4px 8px; border-radius: 4px;">Месяц</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="width: 80px; height: 80px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 36px; font-weight: bold; border: 2px solid {d3_color}; background: {d3_color}25; color: {d3_color}; box-shadow: 0 4px 6px -1px {d3_color}40, 0 2px 4px -1px {d3_color}20;">{fractal['digit3']}</div>
                        <div style="font-size: 12px; margin-top: 8px; font-weight: 500; color: {d3_color}; background: {d3_color}15; padding: 4px 8px; border-radius: 4px;">Год</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="width: 80px; height: 80px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 36px; font-weight: bold; border: 2px solid {d4_color}; background: {d4_color}25; color: {d4_color}; box-shadow: 0 4px 6px -1px {d4_color}40, 0 2px 4px -1px {d4_color}20;">{fractal['digit4']}</div>
                        <div style="font-size: 12px; margin-top: 8px; font-weight: 500; color: {d4_color}; background: {d4_color}15; padding: 4px 8px; border-radius: 4px;">Сумма</div>
                    </div>
                </div>
                
                <div style="background: #f9fafb; border-radius: 8px; padding: 16px; margin-top: 24px; border: 1px solid #e5e7eb;">
                    <h4 style="font-size: 1.1em; margin-bottom: 12px; font-weight: 600;">Алгоритм расчёта</h4>
                    <div style="font-size: 0.9em; line-height: 1.8; color: #4b5563;">
                        <div style="margin-bottom: 8px;"><strong>1-я цифра:</strong> День рождения {fractal['day']} → <span style="color: {d1_color}; font-weight: bold;">{fractal['digit1']}</span> (основная жизненная позиция)</div>
                        <div style="margin-bottom: 8px;"><strong>2-я цифра:</strong> Месяц рождения {fractal['month']} → <span style="color: {d2_color}; font-weight: bold;">{fractal['digit2']}</span> (взаимодействие с окружающими)</div>
                        <div style="margin-bottom: 8px;"><strong>3-я цифра:</strong> Год рождения {fractal['year']} → <span style="color: {d3_color}; font-weight: bold;">{fractal['digit3']}</span> (внутренние убеждения)</div>
                        <div><strong>4-я цифра:</strong> Сумма ({fractal['day']} + {fractal['month']} + {fractal['year']}) → <span style="color: {d4_color}; font-weight: bold;">{fractal['digit4']}</span> (жизненный путь)</div>
                    </div>
                </div>
                
                <div style="background: #eff6ff; border-radius: 8px; padding: 16px; margin-top: 16px; border: 1px solid #bfdbfe;">
                    <h4 style="font-size: 1.1em; margin-bottom: 12px; font-weight: 600; color: #1e40af;">Общая интерпретация</h4>
                    <div style="font-size: 0.95em; line-height: 1.8; color: #1e3a8a; white-space: pre-line;">{fractal['general_interpretation']}</div>
                </div>
            </div>
            """
    
    # Числа задач (ЧП)
    personal_numbers = all_data.get('personal_numbers', {})
    if user_data and user_data.get('birth_date') and personal_numbers:
        try:
            from numerology import parse_birth_date
            d, m, y = parse_birth_date(user_data.get('birth_date', ''))
            
            soul_number = personal_numbers.get('soul_number')
            mind_number = personal_numbers.get('mind_number')
            destiny_number = personal_numbers.get('destiny_number')
            
            # Вычисляем число целого года рождения
            year_digits = [int(d) for d in str(y)]
            year_number = sum(year_digits)
            while year_number > 9:
                year_number = sum(int(d) for d in str(year_number))
            
            if soul_number and mind_number and destiny_number:
                task_numbers = calculate_task_numbers(soul_number, mind_number, destiny_number, year_number)
                if task_numbers:
                    p1_color = get_planet_color(task_numbers['problem1'])
                    p2_color = get_planet_color(task_numbers['problem2'])
                    p3_color = get_planet_color(task_numbers['problem3'])
                    p4_color = get_planet_color(task_numbers['problem4'])
                    
                    content += f"""
                    <div class="card">
                        <h2>🔢 Числа задач (ЧП)</h2>
                        <p style="margin-bottom: 20px; color: #666;">Четыре числа проблемы, определяющие жизненные задачи в разные периоды</p>
                        
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px; margin: 20px 0;">
                            <div style="text-align: center;">
                                <div style="width: 80px; height: 80px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 36px; font-weight: bold; border: 2px solid {p1_color}; background: {p1_color}25; color: {p1_color}; box-shadow: 0 4px 6px -1px {p1_color}40, 0 2px 4px -1px {p1_color}20; margin: 0 auto;">{task_numbers['problem1']}</div>
                                <div style="font-size: 12px; margin-top: 8px; font-weight: 600; color: {p1_color}; background: {p1_color}15; padding: 4px 8px; border-radius: 4px;">ЧП1</div>
                                <div style="font-size: 11px; margin-top: 4px; color: #666;">{task_numbers['period1']['start']}-{task_numbers['period1']['end']} лет</div>
                            </div>
                            <div style="text-align: center;">
                                <div style="width: 80px; height: 80px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 36px; font-weight: bold; border: 2px solid {p2_color}; background: {p2_color}25; color: {p2_color}; box-shadow: 0 4px 6px -1px {p2_color}40, 0 2px 4px -1px {p2_color}20; margin: 0 auto;">{task_numbers['problem2']}</div>
                                <div style="font-size: 12px; margin-top: 8px; font-weight: 600; color: {p2_color}; background: {p2_color}15; padding: 4px 8px; border-radius: 4px;">ЧП2</div>
                                <div style="font-size: 11px; margin-top: 4px; color: #666;">{task_numbers['period2']['start']}-{task_numbers['period2']['end']} лет</div>
                            </div>
                            <div style="text-align: center;">
                                <div style="width: 80px; height: 80px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 36px; font-weight: bold; border: 2px solid {p3_color}; background: {p3_color}25; color: {p3_color}; box-shadow: 0 4px 6px -1px {p3_color}40, 0 2px 4px -1px {p3_color}20; margin: 0 auto;">{task_numbers['problem3']}</div>
                                <div style="font-size: 12px; margin-top: 8px; font-weight: 600; color: {p3_color}; background: {p3_color}15; padding: 4px 8px; border-radius: 4px;">ЧП3</div>
                                <div style="font-size: 11px; margin-top: 4px; color: #666;">Всю жизнь</div>
                            </div>
                            <div style="text-align: center;">
                                <div style="width: 80px; height: 80px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 36px; font-weight: bold; border: 2px solid {p4_color}; background: {p4_color}25; color: {p4_color}; box-shadow: 0 4px 6px -1px {p4_color}40, 0 2px 4px -1px {p4_color}20; margin: 0 auto;">{task_numbers['problem4']}</div>
                                <div style="font-size: 12px; margin-top: 8px; font-weight: 600; color: {p4_color}; background: {p4_color}15; padding: 4px 8px; border-radius: 4px;">ЧП4</div>
                                <div style="font-size: 11px; margin-top: 4px; color: #666;">С {task_numbers['period4']['start']} лет</div>
                            </div>
                        </div>
                        
                        <div style="background: #f9fafb; border-radius: 8px; padding: 16px; margin-top: 24px; border: 1px solid #e5e7eb;">
                            <h4 style="font-size: 1.1em; margin-bottom: 12px; font-weight: 600;">Алгоритм расчёта</h4>
                            <div style="font-size: 0.9em; line-height: 1.8; color: #4b5563;">
                                <div style="margin-bottom: 8px;"><strong>1-е число проблемы (ЧП1):</strong> Число Души <span style="color: {get_planet_color(soul_number)}; font-weight: bold;">{soul_number}</span> - Число Ума <span style="color: {get_planet_color(mind_number)}; font-weight: bold;">{mind_number}</span> = {task_numbers['calculations']['problem1Raw']} → <span style="color: {p1_color}; font-weight: bold;">{task_numbers['problem1']}</span></div>
                                <div style="margin-bottom: 8px; padding-left: 16px; color: #6b7280; font-size: 0.85em;">Период: с {task_numbers['period1']['start']} до {task_numbers['period1']['end']} лет (начинается с 36 - число судьбы {destiny_number} = {task_numbers['period1']['start']}, заканчивается {task_numbers['period1']['start']} + 9 = {task_numbers['period1']['end']})</div>
                                
                                <div style="margin-bottom: 8px; margin-top: 12px;"><strong>2-е число проблемы (ЧП2):</strong> Число Души <span style="color: {get_planet_color(soul_number)}; font-weight: bold;">{soul_number}</span> - Число целого года рождения <span style="color: {get_planet_color(year_number)}; font-weight: bold;">{year_number}</span> = {task_numbers['calculations']['problem2Raw']} → <span style="color: {p2_color}; font-weight: bold;">{task_numbers['problem2']}</span></div>
                                <div style="margin-bottom: 8px; padding-left: 16px; color: #6b7280; font-size: 0.85em;">Период: с {task_numbers['period2']['start']} до {task_numbers['period2']['end']} лет (начинается после окончания ЧП1, длится 9 лет)</div>
                                
                                <div style="margin-bottom: 8px; margin-top: 12px;"><strong>3-е число проблемы (ЧП3):</strong> ЧП1 <span style="color: {p1_color}; font-weight: bold;">{task_numbers['problem1']}</span> - ЧП2 <span style="color: {p2_color}; font-weight: bold;">{task_numbers['problem2']}</span> = {task_numbers['calculations']['problem3Raw']} → <span style="color: {p3_color}; font-weight: bold;">{task_numbers['problem3']}</span></div>
                                <div style="margin-bottom: 8px; padding-left: 16px; color: #6b7280; font-size: 0.85em;">Период: всю жизнь</div>
                                
                                <div style="margin-bottom: 8px; margin-top: 12px;"><strong>4-е число проблемы (ЧП4):</strong> Месяц рождения <span style="color: {get_planet_color(mind_number)}; font-weight: bold;">{mind_number}</span> - Число целого года рождения <span style="color: {get_planet_color(year_number)}; font-weight: bold;">{year_number}</span> = {task_numbers['calculations']['problem4Raw']} → <span style="color: {p4_color}; font-weight: bold;">{task_numbers['problem4']}</span></div>
                                <div style="padding-left: 16px; color: #6b7280; font-size: 0.85em;">Период: с {task_numbers['period4']['start']} лет до конца жизни</div>
                            </div>
                        </div>
                    </div>
                    """
        except Exception as e:
            print(f"Ошибка расчета чисел задач: {e}")
            pass
    
    # Квадрат Пифагора
    pythagorean_square = all_data.get('pythagorean_square', {})
    if pythagorean_square:
        content += generate_pythagorean_square(pythagorean_square)
    
    # Графики планетарных энергий
    if charts_data and charts_data.get('planetary_energy'):
        content += f"""
        <div class="card">
            <h2>📈 Динамика энергий планет</h2>
            <div class="chart-container">
                <canvas id="planetaryEnergyChart"></canvas>
            </div>
        </div>
        """
    
    return content if content else "<div class='card'><p>Данные графиков не доступны</p></div>"

def generate_planetary_tab(all_data: Dict[str, Any]) -> str:
    """Генерирует контент таба 'Планеты'"""
    pythagorean_square = all_data.get('pythagorean_square', {})
    if not pythagorean_square:
        return "<div class='card'><p>Данные о планетах не доступны</p></div>"
    
    # Генерируем интерпретацию планет
    square_matrix = pythagorean_square.get('square', [['', '', ''], ['', '', ''], ['', '', '']])
    # Индексы планет в квадрате: [1, 4, 7], [2, 5, 8], [3, 6, 9]
    INDEX_BY_NUMBER = {
        1: [0, 0], 4: [0, 1], 7: [0, 2],
        2: [1, 0], 5: [1, 1], 8: [1, 2],
        3: [2, 0], 6: [2, 1], 9: [2, 2]
    }
    
    planets_html = ""
    for planet_num in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
        row_idx, col_idx = INDEX_BY_NUMBER[planet_num]
        cell = square_matrix[row_idx][col_idx] if row_idx < len(square_matrix) and col_idx < len(square_matrix[row_idx]) else ''
        count = len(cell) if isinstance(cell, str) else (len(cell) if isinstance(cell, list) else 0)
        
        planet_name = get_planet_name(planet_num)
        planet_symbol = get_planet_symbol(planet_num)
        planet_color = get_planet_color(planet_num)
        planet_interpretation = get_planet_interpretation(planet_num)
        
        strength = 'сильная' if count >= 3 else ('средняя' if count == 2 else ('слабая' if count == 1 else 'отсутствует'))
        strength_color = '#10b981' if count >= 3 else ('#f59e0b' if count == 2 else ('#6b7280' if count == 1 else '#9ca3af'))
        
        # Определяем ведическое название
        vedic_names = {
            1: 'Surya', 2: 'Chandra', 3: 'Guru', 4: 'Rahu', 5: 'Budha',
            6: 'Shukra', 7: 'Ketu', 8: 'Shani', 9: 'Mangala'
        }
        vedic_name = vedic_names.get(planet_num, '')
        
        # Добавляем рекомендации для отсутствующих планет
        missing_advice = ""
        if count == 0:
            missing_advice = get_missing_planet_advice(planet_num)
        
        planets_html += f"""
        <div class="card" style="margin-bottom: 24px; border: 2px solid {planet_color}; border-radius: 12px; background: linear-gradient(to bottom right, {planet_color}15, {planet_color}05);">
            <div style="display: flex; align-items: start; justify-content: space-between; margin-bottom: 16px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="font-size: 48px; color: {planet_color}; opacity: {0.6 if count == 0 else 1.0};">{planet_symbol}</div>
                    <div>
                        <h3 style="font-size: 1.5em; font-weight: bold; color: {planet_color}; margin: 0;">
                            {planet_name} / {vedic_name} ({planet_num})
                        </h3>
                        <div style="display: flex; align-items: center; gap: 16px; margin-top: 8px;">
                            <span style="font-weight: 600; color: {planet_color};">
                                Количество цифр: <span style="font-size: 1.2em; font-weight: bold;">{count}</span>
                            </span>
                            <span style="color: {strength_color}; font-weight: 600;">
                                Состояние: <span style="text-transform: capitalize; font-weight: bold;">{strength}</span>
                            </span>
                        </div>
                    </div>
                </div>
                <div style="padding: 8px 16px; border-radius: 8px; background: {planet_color}20; border: 2px solid {planet_color};">
                    <span style="font-size: 1.5em; font-weight: bold; color: {planet_color};">{count}</span>
                </div>
            </div>
            
            <div style="background: white; border-radius: 8px; padding: 16px; margin-top: 16px; border: 1px solid #e5e7eb;">
                <div style="font-size: 0.95em; line-height: 1.8; color: #374151; white-space: pre-line;">{planet_interpretation}</div>
            </div>
            
            {f'<div style="background: #fef3c7; border-radius: 8px; padding: 16px; margin-top: 16px; border: 1px solid #fbbf24;"><div style="font-size: 0.95em; line-height: 1.8; color: #92400e; white-space: pre-line;">{missing_advice}</div></div>' if missing_advice else ''}
        </div>
        """
    
    return f"""
    <div class="card">
        <h2>🪐 Интерпретация планет в вашей карте</h2>
        <p style="margin-bottom: 20px; color: #666;">Анализ планетарных энергий на основе квадрата Пифагора. Показаны все планеты с их состоянием и рекомендациями по развитию.</p>
        {planets_html}
    </div>
    """

def generate_route_tab(all_data: Dict[str, Any]) -> str:
    """Генерирует контент таба 'Маршрут'"""
    planetary_route = all_data.get('planetary_route', {})
    if not planetary_route:
        return "<div class='card'><p>Данные планетарного маршрута не доступны</p></div>"
    
    route_html = f"""
    <div class="card">
        <h2>🗺️ Планетарный маршрут на день</h2>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Дата</div>
                <div class="info-value">{planetary_route.get('date', 'Не указана')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Город</div>
                <div class="info-value">{planetary_route.get('city', 'Не указан')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Планета дня</div>
                <div class="info-value">{planetary_route.get('daily_ruling_planet', 'Не указана')}</div>
            </div>
        </div>
    </div>
    """
    
    # Благоприятные периоды
    if planetary_route.get('favorable_period'):
        fav = planetary_route['favorable_period']
        route_html += f"""
        <div class="card" style="border-left: 4px solid #10b981;">
            <h3>✅ Благоприятный период</h3>
            <div class="info-item">
                <div class="info-label">Абхиджит мухурта</div>
                <div class="info-value">{fav.get('start', '')} - {fav.get('end', '')}</div>
            </div>
        </div>
        """
    
    # Периоды, которых следует избегать
    if planetary_route.get('avoid_periods'):
        avoid = planetary_route['avoid_periods']
        route_html += f"""
        <div class="card" style="border-left: 4px solid #ef4444;">
            <h3>⚠️ Периоды, которых следует избегать</h3>
            {f"<div class='info-item'><div class='info-label'>Раху кала</div><div class='info-value'>{avoid.get('rahu_kaal', {}).get('start', '')} - {avoid.get('rahu_kaal', {}).get('end', '')}</div></div>" if avoid.get('rahu_kaal') else ''}
            {f"<div class='info-item'><div class='info-label'>Гулика кала</div><div class='info-value'>{avoid.get('gulika_kaal', {}).get('start', '')} - {avoid.get('gulika_kaal', {}).get('end', '')}</div></div>" if avoid.get('gulika_kaal') else ''}
            {f"<div class='info-item'><div class='info-label'>Ямагханта</div><div class='info-value'>{avoid.get('yamaghanta', {}).get('start', '')} - {avoid.get('yamaghanta', {}).get('end', '')}</div></div>" if avoid.get('yamaghanta') else ''}
        </div>
        """
    
    # Почасовой гид
    if planetary_route.get('hourly_guide'):
        hours = planetary_route['hourly_guide']
        hours_html = ""
        for hour in hours[:12]:  # Показываем первые 12 часов
            start_time = hour.get('start_time', '')
            end_time = hour.get('end_time', '')
            # Извлекаем только время из ISO строки
            if 'T' in start_time:
                start_time = start_time.split('T')[1][:5]
            if 'T' in end_time:
                end_time = end_time.split('T')[1][:5]
            
            hours_html += f"""
            <div class="info-item" style="margin-bottom: 10px;">
                <div class="info-label">{start_time} - {end_time}</div>
                <div class="info-value">{hour.get('planet', '')} {'✅' if hour.get('favorable') else '⚠️'}</div>
            </div>
            """
        route_html += f"""
        <div class="card">
            <h3>🕐 Почасовой гид</h3>
            <div class="info-grid">
                {hours_html}
            </div>
        </div>
        """
    
    return route_html

def generate_compatibility_tab(all_data: Dict[str, Any]) -> str:
    """Генерирует контент таба 'Совместимость'"""
    compatibility = all_data.get('compatibility', {})
    group_compatibility = all_data.get('group_compatibility', {})
    
    if not compatibility and not group_compatibility:
        return "<div class='card'><p>Данные совместимости не доступны. Перейдите в раздел 'Совместимость' для расчёта.</p></div>"
    
    content = ""
    
    # Парная совместимость
    if compatibility:
        score = compatibility.get('compatibility_score', 0)
        score_color = '#10b981' if score >= 8 else ('#f59e0b' if score >= 6 else '#ef4444')
        
        content += f"""
        <div class="card">
            <h2>👥 Парная совместимость</h2>
            <div style="display: flex; justify-content: center; align-items: center; gap: 32px; margin: 24px 0;">
                <div style="text-align: center;">
                    <div style="width: 64px; height: 64px; border-radius: 50%; background: linear-gradient(135deg, #667eea, #764ba2); display: flex; align-items: center; justify-content: center; margin: 0 auto 8px;">
                        <span style="font-size: 24px; font-weight: bold; color: white;">{compatibility.get('person1_life_path', '?')}</span>
                    </div>
                    <p style="font-size: 0.9em; color: #666;">Число судьбы 1</p>
                </div>
                <div style="text-align: center;">
                    <div style="padding: 16px 24px; border-radius: 12px; border: 2px solid {score_color}; background: {score_color}15;">
                        <span style="font-size: 32px; font-weight: bold; color: {score_color};">{score}/10</span>
                    </div>
                    <p style="font-size: 0.9em; color: #666; margin-top: 8px;">Совместимость</p>
                </div>
                <div style="text-align: center;">
                    <div style="width: 64px; height: 64px; border-radius: 50%; background: linear-gradient(135deg, #f093fb, #f5576c); display: flex; align-items: center; justify-content: center; margin: 0 auto 8px;">
                        <span style="font-size: 24px; font-weight: bold; color: white;">{compatibility.get('person2_life_path', '?')}</span>
                    </div>
                    <p style="font-size: 0.9em; color: #666;">Число судьбы 2</p>
                </div>
            </div>
            <div style="background: #f9fafb; border-radius: 8px; padding: 16px; margin-top: 16px;">
                <p style="color: #374151; line-height: 1.6;">{compatibility.get('description', 'Описание совместимости')}</p>
            </div>
        </div>
        """
    
    # Групповая совместимость
    if group_compatibility:
        content += f"""
        <div class="card">
            <h2>👥👥 Групповая совместимость</h2>
            <p style="color: #666; margin-bottom: 16px;">Анализ совместимости с группой людей</p>
            <div style="background: #f9fafb; border-radius: 8px; padding: 16px;">
                <p style="color: #374151;">Данные групповой совместимости доступны в разделе 'Совместимость'.</p>
            </div>
        </div>
        """
    
    return content if content else "<div class='card'><p>Данные совместимости не доступны</p></div>"

def generate_name_tab(user_data: Dict[str, Any], all_data: Dict[str, Any]) -> str:
    """Генерирует контент таба 'Имя'"""
    name_numerology = all_data.get('name_numerology', {})
    
    if not name_numerology:
        if not user_data.get('full_name'):
            return "<div class='card'><p>Имя не указано</p></div>"
        return "<div class='card'><p>Нумерология имени не рассчитана. Перейдите в раздел 'Нумерология' для расчёта.</p></div>"
    
    first_name_color = get_planet_color(name_numerology.get('first_name_number', 1))
    last_name_color = get_planet_color(name_numerology.get('last_name_number', 1)) if name_numerology.get('last_name_number') else None
    total_name_color = get_planet_color(name_numerology.get('total_name_number', 1))
    
    content = f"""
    <div class="card">
        <h2>⭐ Нумерология имени</h2>
        <p style="margin-bottom: 20px; color: #666;">Числовой анализ вашего имени</p>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin: 20px 0;">
            <div style="text-align: center; padding: 20px; border-radius: 12px; border: 2px solid {first_name_color}; background: {first_name_color}15;">
                <div style="font-size: 2.5em; font-weight: bold; color: {first_name_color}; margin-bottom: 8px;">{name_numerology.get('first_name_number', '?')}</div>
                <div style="font-weight: 600; color: #374151; margin-bottom: 4px;">Число имени</div>
                <div style="font-size: 0.9em; color: #666;">{name_numerology.get('first_name', '')}</div>
            </div>
"""
    
    if name_numerology.get('last_name_number'):
        content += f"""
            <div style="text-align: center; padding: 20px; border-radius: 12px; border: 2px solid {last_name_color}; background: {last_name_color}15;">
                <div style="font-size: 2.5em; font-weight: bold; color: {last_name_color}; margin-bottom: 8px;">{name_numerology.get('last_name_number')}</div>
                <div style="font-weight: 600; color: #374151; margin-bottom: 4px;">Число фамилии</div>
                <div style="font-size: 0.9em; color: #666;">{name_numerology.get('last_name', '')}</div>
            </div>
"""
    
    content += f"""
            <div style="text-align: center; padding: 20px; border-radius: 12px; border: 2px solid {total_name_color}; background: {total_name_color}15;">
                <div style="font-size: 2.5em; font-weight: bold; color: {total_name_color}; margin-bottom: 8px;">{name_numerology.get('total_name_number', '?')}</div>
                <div style="font-weight: 600; color: #374151; margin-bottom: 4px;">Общее число имени</div>
                <div style="font-size: 0.9em; color: #666;">{name_numerology.get('full_name', '')}</div>
            </div>
        </div>
        
        <div style="background: #eff6ff; border-radius: 8px; padding: 16px; margin-top: 16px; border: 1px solid #bfdbfe;">
            <h4 style="font-size: 1.1em; margin-bottom: 12px; font-weight: 600; color: #1e40af;">Интерпретация</h4>
            <p style="color: #1e3a8a; line-height: 1.6;">{name_numerology.get('total_interpretation', 'Интерпретация не доступна')}</p>
        </div>
    </div>
    """
    
    return content

def generate_address_tab(user_data: Dict[str, Any], all_data: Dict[str, Any]) -> str:
    """Генерирует контент таба 'Адрес'"""
    address_numerology = all_data.get('address_numerology', {})
    
    if not address_numerology:
        if not (user_data.get('street') or user_data.get('house_number')):
            return "<div class='card'><p>Адрес не указан</p></div>"
        return "<div class='card'><p>Нумерология адреса не рассчитана. Перейдите в раздел 'Нумерология' для расчёта.</p></div>"
    
    content = f"""
    <div class="card">
        <h2>🏠 Нумерология адреса</h2>
        <p style="margin-bottom: 20px; color: #666;">Энергетика вашего места проживания</p>
        
        <div style="display: grid; grid-cols-1 sm:grid-cols-2 gap-4; margin-bottom: 20px;">
            <div style="padding: 16px; background: #f9fafb; border-radius: 8px;">
                <label style="font-size: 0.9em; font-weight: 600; color: #666;">Улица</label>
                <p style="font-size: 1.1em; font-weight: 600; margin-top: 4px;">{user_data.get('street', 'Не указана')}</p>
            </div>
            <div style="padding: 16px; background: #f9fafb; border-radius: 8px;">
                <label style="font-size: 0.9em; font-weight: 600; color: #666;">Номер дома</label>
                <p style="font-size: 1.1em; font-weight: 600; margin-top: 4px;">{user_data.get('house_number', 'Не указан')}</p>
            </div>
        </div>
"""
    
    if address_numerology.get('house_numerology'):
        house_value = address_numerology['house_numerology'].get('value')
        house_color = get_planet_color(house_value)
        content += f"""
        <div style="padding: 16px; background: {house_color}15; border-radius: 8px; border: 2px solid {house_color}; margin-bottom: 16px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <h4 style="font-weight: 600; color: #374151;">Номер дома</h4>
                <div style="font-size: 2em; font-weight: bold; color: {house_color};">{house_value}</div>
            </div>
            <p style="color: #374151; line-height: 1.6;">{address_numerology['house_numerology'].get('interpretation', '')}</p>
        </div>
"""
    
    if address_numerology.get('apartment_numerology'):
        apt_value = address_numerology['apartment_numerology'].get('value')
        apt_color = get_planet_color(apt_value)
        content += f"""
        <div style="padding: 16px; background: {apt_color}15; border-radius: 8px; border: 2px solid {apt_color}; margin-bottom: 16px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <h4 style="font-weight: 600; color: #374151;">Номер квартиры</h4>
                <div style="font-size: 2em; font-weight: bold; color: {apt_color};">{apt_value}</div>
            </div>
            <p style="color: #374151; line-height: 1.6;">{address_numerology['apartment_numerology'].get('interpretation', '')}</p>
        </div>
"""
    
    if address_numerology.get('postal_code_numerology'):
        postal_value = address_numerology['postal_code_numerology'].get('value')
        postal_color = get_planet_color(postal_value)
        content += f"""
        <div style="padding: 16px; background: {postal_color}15; border-radius: 8px; border: 2px solid {postal_color};">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <h4 style="font-weight: 600; color: #374151;">Почтовый индекс</h4>
                <div style="font-size: 2em; font-weight: bold; color: {postal_color};">{postal_value}</div>
            </div>
            <p style="color: #374151; line-height: 1.6;">{address_numerology['postal_code_numerology'].get('interpretation', '')}</p>
        </div>
"""
    
    content += "</div>"
    
    return content

def generate_car_tab(user_data: Dict[str, Any], all_data: Dict[str, Any]) -> str:
    """Генерирует контент таба 'Авто'"""
    car_numerology = all_data.get('car_numerology', {})
    car_number = user_data.get('car_number') or car_numerology.get('car_number', '')
    
    if not car_numerology:
        if not car_number:
            return "<div class='card'><p>Номер автомобиля не указан</p></div>"
        return "<div class='card'><p>Нумерология автомобиля не рассчитана. Перейдите в раздел 'Нумерология' для расчёта.</p></div>"
    
    car_value = car_numerology.get('numerology_value', 1)
    car_color = get_planet_color(car_value)
    
    return f"""
    <div class="card">
        <h2>🚗 Нумерология автомобиля</h2>
        <p style="margin-bottom: 20px; color: #666;">Энергетика вашего транспортного средства</p>
        
        <div style="padding: 16px; background: #f9fafb; border-radius: 8px; margin-bottom: 20px;">
            <label style="font-size: 0.9em; font-weight: 600; color: #666;">Номер автомобиля</label>
            <p style="font-size: 1.2em; font-weight: 600; margin-top: 4px;">{car_number}</p>
        </div>
        
        <div style="padding: 20px; background: {car_color}15; border-radius: 12px; border: 2px solid {car_color};">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
                <h4 style="font-size: 1.2em; font-weight: 600; color: #374151;">Числовой анализ автомобиля</h4>
                <div style="font-size: 3em; font-weight: bold; color: {car_color};">{car_value}</div>
            </div>
            <p style="color: #374151; line-height: 1.6; font-size: 1em;">{car_numerology.get('interpretation', 'Интерпретация не доступна')}</p>
        </div>
    </div>
    """