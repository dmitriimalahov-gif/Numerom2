"""
PDF генерация отчетов с полными расчетами и графиками
"""
import io
import base64
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import Color, HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.lib import colors
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Headless backend for server

# Функции генерации табов определены в конце файла


def create_numerology_report_pdf(user_data: Dict[str, Any], all_data: Dict[str, Any] = None,
                                vedic_data: Dict[str, Any] = None, charts_data: Dict[str, Any] = None,
                                selected_calculations: List[str] = None) -> bytes:
    """
    Создает многостраничный PDF отчет с табами, как в персональном отчете
    Каждая страница соответствует табу из персонального отчета
    """
    # Для обратной совместимости
    if all_data is None:
        calculations = user_data if isinstance(user_data, dict) and 'personal_numbers' in user_data else {}
        all_data = {
            'personal_numbers': calculations.get('personal_numbers', calculations) if isinstance(calculations, dict) else {},
            'pythagorean_square': calculations.get('pythagorean_square', calculations.get('enhanced_square', {}))
        }
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=18)
    
    # Стили
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        textColor=HexColor('#4a90a4'),
        alignment=TA_CENTER
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle', 
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=20,
        textColor=HexColor('#2c5f2d'),
        alignment=TA_LEFT
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        textColor=HexColor('#333333')
    )
    
    # Если не указаны выбранные расчёты, включаем все доступные
    if selected_calculations is None:
        selected_calculations = ['personal_numbers', 'pythagorean_square', 'vedic_times', 'planetary_route']
    
    # Определяем, какие табы включать
    tabs_to_include = []
    if all_data.get('personal_numbers'):
        tabs_to_include.append('overview')
    if all_data.get('pythagorean_square') or charts_data:
        tabs_to_include.append('charts')
        tabs_to_include.append('planetary')
    if all_data.get('planetary_route') or all_data.get('vedic_times'):
        tabs_to_include.append('route')
    if all_data.get('compatibility') or all_data.get('group_compatibility'):
        tabs_to_include.append('compatibility')
    if user_data.get('full_name'):
        tabs_to_include.append('name')
    if user_data.get('street') or user_data.get('house_number'):
        tabs_to_include.append('address')
    if user_data.get('car_number'):
        tabs_to_include.append('car')
    
    # Если нет табов, добавляем хотя бы обзор
    if not tabs_to_include:
        tabs_to_include = ['overview']
    
    # Контент документа - создаем страницу для каждого таба
    story = []
    
    # Генерируем страницы для каждого таба
    for tab_idx, tab_name in enumerate(tabs_to_include):
        # Добавляем разрыв страницы для всех табов кроме первого
        if tab_idx > 0:
            story.append(Spacer(1, 0.1))  # Минимальный спейсер для принудительного разрыва страницы
        
        # Заголовок страницы с названием таба
        tab_titles = {
            'overview': '👤 Обзор',
            'charts': '📊 Графики',
            'planetary': '🪐 Планеты',
            'route': '🗺️ Маршрут',
            'compatibility': '👥 Совместимость',
            'name': '⭐ Имя',
            'address': '📍 Адрес',
            'car': '🚗 Авто'
        }
        
        story.append(Paragraph(f"🔢 NUMEROM - Персональный Нумерологический Отчет", title_style))
        story.append(Paragraph(f"{tab_titles.get(tab_name, tab_name)}", 
                              ParagraphStyle('TabTitle', parent=subtitle_style, fontSize=18, 
                                           textColor=HexColor('#3b82f6'), alignment=TA_CENTER)))
        story.append(Spacer(1, 20))
        
        # Генерируем контент для каждого таба
        if tab_name == 'overview':
            story.extend(generate_pdf_overview_tab(user_data, all_data, styles, subtitle_style, body_style))
        elif tab_name == 'charts':
            story.extend(generate_pdf_charts_tab(user_data, all_data, charts_data, styles, subtitle_style, body_style))
        elif tab_name == 'planetary':
            story.extend(generate_pdf_planetary_tab(all_data, styles, subtitle_style, body_style))
        elif tab_name == 'route':
            story.extend(generate_pdf_route_tab(all_data, styles, subtitle_style, body_style))
        elif tab_name == 'compatibility':
            story.extend(generate_pdf_compatibility_tab(all_data, styles, subtitle_style, body_style))
        elif tab_name == 'name':
            story.extend(generate_pdf_name_tab(user_data, all_data, styles, subtitle_style, body_style))
        elif tab_name == 'address':
            story.extend(generate_pdf_address_tab(user_data, all_data, styles, subtitle_style, body_style))
        elif tab_name == 'car':
            story.extend(generate_pdf_car_tab(user_data, all_data, styles, subtitle_style, body_style))
        
        # Футер на каждой странице
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Страница {tab_idx + 1} из {len(tabs_to_include)}", 
                              ParagraphStyle('PageNumber', parent=body_style, fontSize=8, 
                                           textColor=HexColor('#666666'), alignment=TA_CENTER)))
    
    # Генерируем PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer.getvalue()


def create_planetary_chart(planetary_data: List[Dict]) -> io.BytesIO:
    """
    Создает график планетарных энергий с помощью matplotlib
    """
    try:
        # Настройка matplotlib для красивого графика
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('white')
        
        # Данные для графика
        days = [entry.get('day_name', f"День {i+1}") for i, entry in enumerate(planetary_data)]
        
        # Планеты и их цвета
        planets = ['surya', 'chandra', 'mangal', 'budha', 'guru', 'shukra', 'shani', 'rahu', 'ketu']
        planet_colors = {
            'surya': '#FF6B35',     # Оранжевый для Солнца
            'chandra': '#87CEEB',   # Голубой для Луны  
            'mangal': '#DC143C',    # Красный для Марса
            'budha': '#32CD32',     # Зеленый для Меркурия
            'guru': '#FFD700',      # Золотой для Юпитера
            'shukra': '#FF69B4',    # Розовый для Венеры
            'shani': '#4169E1',     # Синий для Сатурна
            'rahu': '#8B4513',      # Коричневый для Раху
            'ketu': '#9370DB'       # Фиолетовый для Кету
        }
        
        planet_names = {
            'surya': 'Сурья (Солнце)',
            'chandra': 'Чандра (Луна)',
            'mangal': 'Мангал (Марс)', 
            'budha': 'Будха (Меркурий)',
            'guru': 'Гуру (Юпитер)',
            'shukra': 'Шукра (Венера)',
            'shani': 'Шани (Сатурн)',
            'rahu': 'Раху',
            'ketu': 'Кету'
        }
        
        # Строим линии для каждой планеты
        for planet in planets[:7]:  # Показываем первые 7 планет для читабельности
            values = []
            for entry in planetary_data:
                energies = entry.get('planetary_energies', {})
                values.append(energies.get(planet, 50))
            
            ax.plot(days, values, 
                   color=planet_colors[planet], 
                   linewidth=2, 
                   marker='o', 
                   markersize=4,
                   label=planet_names[planet])
        
        # Настройка графика
        ax.set_title('Планетарные энергии по дням', fontsize=14, fontweight='bold', color='#2c5f2d')
        ax.set_xlabel('Дни', fontsize=12)
        ax.set_ylabel('Уровень энергии', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.set_ylim(0, 100)
        
        # Поворачиваем подписи дней для лучшей читабельности
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Сохраняем в буфер
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plt.close(fig)
        
        return buffer
        
    except Exception as e:
        print(f"Ошибка создания графика: {e}")
        return None


def create_compatibility_pdf(user1_data: Dict, user2_data: Dict, compatibility_result: Dict) -> bytes:
    """
    Создает PDF отчет о совместимости двух людей
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        textColor=HexColor('#d63384'),
        alignment=TA_CENTER
    )
    
    story = []
    
    # Заголовок
    story.append(Paragraph("💕 NUMEROM - Анализ совместимости", title_style))
    story.append(Spacer(1, 20))
    
    # Данные партнеров
    partners_data = [
        ['Партнер 1', 'Партнер 2'],
        [f"Дата рождения: {user1_data.get('birth_date', 'Не указано')}", 
         f"Дата рождения: {user2_data.get('birth_date', 'Не указано')}"],
        [f"Число жизни: {compatibility_result.get('person1_life_path', 'Не рассчитано')}", 
         f"Число жизни: {compatibility_result.get('person2_life_path', 'Не рассчитано')}"]
    ]
    
    partners_table = Table(partners_data, colWidths=[3*inch, 3*inch])
    partners_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#d63384')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.gray),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(partners_table)
    story.append(Spacer(1, 20))
    
    # Результат совместимости
    compatibility_score = compatibility_result.get('compatibility_score', 0)
    score_color = HexColor('#28a745') if compatibility_score > 70 else HexColor('#ffc107') if compatibility_score > 40 else HexColor('#dc3545')
    
    story.append(Paragraph(f"Общий уровень совместимости: <font color='{score_color}'>{compatibility_score}%</font>", 
                          ParagraphStyle('Score', parent=styles['Normal'], fontSize=16, alignment=TA_CENTER)))
    
    story.append(Spacer(1, 20))
    story.append(Paragraph(compatibility_result.get('description', 'Описание недоступно'), styles['Normal']))
    
    # Генерируем PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer.getvalue()# Функции генерации контента для каждого таба PDF

from typing import Dict, Any, List
from reportlab.platypus import Spacer, Table, TableStyle, Paragraph, Image
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
# colors и HexColor уже импортированы в начале файла


def generate_pdf_overview_tab(user_data: Dict[str, Any], all_data: Dict[str, Any], 
                              styles, subtitle_style, body_style) -> List:
    """Генерирует контент таба 'Обзор' для PDF"""
    story = []
    
    # Личная информация
    story.append(Paragraph("👤 Личная информация", subtitle_style))
    
    # Разделяем имя и фамилию
    full_name = user_data.get('full_name', '')
    name_parts = full_name.split() if full_name else []
    first_name = name_parts[0] if name_parts else 'Не указано'
    last_name = name_parts[-1] if len(name_parts) > 1 else 'Не указано'
    
    user_info_data = [
        ['Имя:', first_name],
        ['Фамилия:', last_name],
        ['Email:', user_data.get('email', 'Не указано')],
        ['Дата рождения:', user_data.get('birth_date', 'Не указана')]
    ]
    
    user_info_table = Table(user_info_data, colWidths=[2*inch, 4*inch])
    user_info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), HexColor('#e3f2fd')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.gray),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(user_info_table)
    story.append(Spacer(1, 20))
    
    # Ключевые числа
    personal_numbers = all_data.get('personal_numbers', {})
    if personal_numbers:
        story.append(Paragraph("✨ Ключевые числа", subtitle_style))
        
        numbers_data = [
            ['Число', 'Значение', 'Описание'],
            ['Число души (ЧД)', str(personal_numbers.get('soul_number', '?')), 'Ваша внутренняя сущность'],
            ['Число ума (ЧУ)', str(personal_numbers.get('mind_number', '?')), 'Способ мышления'],
            ['Число судьбы (ЧС)', str(personal_numbers.get('destiny_number', '?')), 'Ваш жизненный путь'],
            ['Помогающее число ума (ЧУ*)', str(personal_numbers.get('helping_mind_number', '?')), 'Дополнительная поддержка'],
            ['Число мудрости (ЧМ)', str(personal_numbers.get('wisdom_number', '?')), 'Духовная мудрость'],
            ['Правящее число (ПЧ)', str(personal_numbers.get('ruling_number', '?')), 'Главное число']
        ]
        
        numbers_table = Table(numbers_data, colWidths=[2*inch, 1*inch, 3*inch])
        numbers_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.gray),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(numbers_table)
        story.append(Spacer(1, 20))
    
    return story


def generate_pdf_charts_tab(user_data: Dict[str, Any], all_data: Dict[str, Any], 
                            charts_data: Dict[str, Any], styles, subtitle_style, body_style) -> List:
    """Генерирует контент таба 'Графики' для PDF"""
    story = []
    
    # Фрактал поведения
    if user_data.get('birth_date'):
        try:
            from numerology import parse_birth_date, reduce_to_single_digit
            d, m, y = parse_birth_date(user_data.get('birth_date', ''))
            day_reduced = reduce_to_single_digit(d)
            month_reduced = reduce_to_single_digit(m)
            year_reduced = reduce_to_single_digit(y)
            year_sum = reduce_to_single_digit(d + m + y)
            
            story.append(Paragraph("🔢 Фрактал поведения", subtitle_style))
            
            fractal_data = [
                ['Позиция', 'Значение', 'Расчет'],
                ['1-я цифра (День)', str(day_reduced), f'День рождения {d} → {day_reduced}'],
                ['2-я цифра (Месяц)', str(month_reduced), f'Месяц рождения {m} → {month_reduced}'],
                ['3-я цифра (Год)', str(year_reduced), f'Год рождения {y} → {year_reduced}'],
                ['4-я цифра (Сумма)', str(year_sum), f'Сумма ({d} + {m} + {y} = {d+m+y}) → {year_sum}']
            ]
            
            fractal_table = Table(fractal_data, colWidths=[2*inch, 1*inch, 3*inch])
            fractal_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f59e0b')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.gray),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(fractal_table)
            story.append(Spacer(1, 20))
        except:
            pass
    
    # Квадрат Пифагора
    pythagorean_square = all_data.get('pythagorean_square', {})
    if pythagorean_square:
        story.append(Paragraph("⭐ Квадрат Пифагора", subtitle_style))
        
        square_matrix = pythagorean_square.get('square', [['', '', ''], ['', '', ''], ['', '', '']])
        planet_names = [
            ['Солнце', 'Луна', 'Юпитер'],
            ['Раху', 'Центр', 'Венера'],
            ['Кету', 'Сатурн', 'Марс']
        ]
        
        square_data = []
        for i in range(3):
            row = []
            for j in range(3):
                cell_value = square_matrix[i][j] if square_matrix[i][j] else ''
                cell_text = f"{planet_names[i][j]}\n{cell_value}"
                row.append(cell_text)
            square_data.append(row)
        
        square_table = Table(square_data, colWidths=[2*inch, 2*inch, 2*inch])
        square_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#fafafa')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 2, HexColor('#3b82f6')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(square_table)
        story.append(Spacer(1, 20))
    
    # График планетарных энергий
    if charts_data and charts_data.get('planetary_energy'):
        story.append(Paragraph("📈 Динамика энергий планет", subtitle_style))
        chart_image = create_planetary_chart(charts_data['planetary_energy'])
        if chart_image:
            story.append(Image(chart_image, width=6*inch, height=3*inch))
        story.append(Spacer(1, 20))
    
    return story


def generate_pdf_planetary_tab(all_data: Dict[str, Any], styles, subtitle_style, body_style) -> List:
    """Генерирует контент таба 'Планеты' для PDF"""
    story = []
    
    pythagorean_square = all_data.get('pythagorean_square', {})
    if not pythagorean_square:
        story.append(Paragraph("Данные о планетах не доступны", body_style))
        return story
    
    story.append(Paragraph("🪐 Интерпретация планет в вашей карте", subtitle_style))
    
    square_matrix = pythagorean_square.get('square', [['', '', ''], ['', '', ''], ['', '', '']])
    planet_names = ['Солнце', 'Луна', 'Юпитер', 'Раху', 'Центр', 'Венера', 'Кету', 'Сатурн', 'Марс']
    planet_numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    
    for idx, (planet_name, planet_num) in enumerate(zip(planet_names, planet_numbers)):
        row_idx = idx // 3
        col_idx = idx % 3
        cell = square_matrix[row_idx][col_idx] if row_idx < len(square_matrix) and col_idx < len(square_matrix[row_idx]) else ''
        count = len(cell) if isinstance(cell, str) else (len(cell) if isinstance(cell, list) else 0)
        
        strength = 'сильная' if count >= 3 else ('средняя' if count == 2 else ('слабая' if count == 1 else 'отсутствует'))
        
        planet_data = [
            ['Планета', 'Количество цифр', 'Состояние'],
            [f"{planet_name} ({planet_num})", str(count), strength]
        ]
        
        planet_table = Table(planet_data, colWidths=[2*inch, 2*inch, 2*inch])
        planet_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.gray),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(planet_table)
        story.append(Spacer(1, 10))
    
    return story


def generate_pdf_route_tab(all_data: Dict[str, Any], styles, subtitle_style, body_style) -> List:
    """Генерирует контент таба 'Маршрут' для PDF"""
    story = []
    
    planetary_route = all_data.get('planetary_route', {})
    if not planetary_route:
        story.append(Paragraph("Данные планетарного маршрута не доступны", body_style))
        return story
    
    story.append(Paragraph("🗺️ Планетарный маршрут на день", subtitle_style))
    
    route_data = [
        ['Параметр', 'Значение'],
        ['Дата', planetary_route.get('date', 'Не указана')],
        ['Город', planetary_route.get('city', 'Не указан')],
        ['Планета дня', planetary_route.get('daily_ruling_planet', 'Не указана')]
    ]
    
    route_table = Table(route_data, colWidths=[2*inch, 4*inch])
    route_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.gray),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(route_table)
    story.append(Spacer(1, 20))
    
    return story


def generate_pdf_compatibility_tab(all_data: Dict[str, Any], styles, subtitle_style, body_style) -> List:
    """Генерирует контент таба 'Совместимость' для PDF"""
    story = []
    
    compatibility = all_data.get('compatibility', {})
    if not compatibility:
        story.append(Paragraph("Данные совместимости не доступны", body_style))
        return story
    
    story.append(Paragraph("👥 Анализ совместимости", subtitle_style))
    
    compat_data = [
        ['Параметр', 'Значение'],
        ['Оценка совместимости', f"{compatibility.get('compatibility_score', 'Не определено')}/10"],
        ['Описание', compatibility.get('description', 'Не доступно')]
    ]
    
    compat_table = Table(compat_data, colWidths=[2*inch, 4*inch])
    compat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#d63384')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.gray),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(compat_table)
    story.append(Spacer(1, 20))
    
    return story


def generate_pdf_name_tab(user_data: Dict[str, Any], all_data: Dict[str, Any], 
                         styles, subtitle_style, body_style) -> List:
    """Генерирует контент таба 'Имя' для PDF"""
    story = []
    
    if not user_data.get('full_name'):
        story.append(Paragraph("Имя не указано", body_style))
        return story
    
    story.append(Paragraph("⭐ Нумерология имени", subtitle_style))
    story.append(Paragraph(f"Полное имя: {user_data.get('full_name', 'Не указано')}", body_style))
    story.append(Spacer(1, 20))
    
    return story


def generate_pdf_address_tab(user_data: Dict[str, Any], all_data: Dict[str, Any], 
                             styles, subtitle_style, body_style) -> List:
    """Генерирует контент таба 'Адрес' для PDF"""
    story = []
    
    if not (user_data.get('street') or user_data.get('house_number')):
        story.append(Paragraph("Адрес не указан", body_style))
        return story
    
    story.append(Paragraph("📍 Нумерология адреса", subtitle_style))
    
    address_parts = []
    if user_data.get('street'):
        address_parts.append(user_data.get('street'))
    if user_data.get('house_number'):
        address_parts.append(f"д. {user_data.get('house_number')}")
    if user_data.get('apartment_number'):
        address_parts.append(f"кв. {user_data.get('apartment_number')}")
    
    story.append(Paragraph(f"Адрес: {' '.join(address_parts) if address_parts else 'Не указан'}", body_style))
    story.append(Spacer(1, 20))
    
    return story


def generate_pdf_car_tab(user_data: Dict[str, Any], all_data: Dict[str, Any], 
                        styles, subtitle_style, body_style) -> List:
    """Генерирует контент таба 'Авто' для PDF"""
    story = []
    
    if not user_data.get('car_number'):
        story.append(Paragraph("Номер автомобиля не указан", body_style))
        return story
    
    story.append(Paragraph("🚗 Нумерология автомобиля", subtitle_style))
    story.append(Paragraph(f"Номер автомобиля: {user_data.get('car_number', 'Не указан')}", body_style))
    story.append(Spacer(1, 20))
    
    return story

