# Функции генерации контента для каждого таба PDF

from typing import Dict, Any, List
from reportlab.platypus import Spacer, Table, TableStyle, Paragraph, Image
from reportlab.lib.colors import HexColor, colors
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle


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
        from pdf_generator import create_planetary_chart
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


