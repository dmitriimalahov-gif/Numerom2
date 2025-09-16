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


def create_numerology_report_pdf(user_data: Dict[str, Any], calculations: Dict[str, Any], 
                                vedic_data: Dict[str, Any] = None, charts_data: Dict[str, Any] = None) -> bytes:
    """
    Создает PDF отчет с полными нумерологическими расчетами
    """
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
    
    # Контент документа
    story = []
    
    # Заголовок
    story.append(Paragraph("🔢 NUMEROM - Персональный Нумерологический Отчет", title_style))
    story.append(Spacer(1, 20))
    
    # Информация о пользователе
    story.append(Paragraph("📋 Персональные данные", subtitle_style))
    
    user_info_data = [
        ['Имя:', user_data.get('full_name', 'Не указано')],
        ['Email:', user_data.get('email', 'Не указано')],
        ['Дата рождения:', user_data.get('birth_date', 'Не указано')],
        ['Дата создания отчета:', datetime.now().strftime("%d.%m.%Y %H:%M")]
    ]
    
    user_info_table = Table(user_info_data, colWidths=[2*inch, 4*inch])
    user_info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), HexColor('#f0f8f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.gray),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(user_info_table)
    story.append(Spacer(1, 30))
    
    # Основные числа личности
    if 'personal_numbers' in calculations:
        personal = calculations['personal_numbers']
        story.append(Paragraph("✨ Основные числа личности", subtitle_style))
        
        personal_data = [
            ['Показатель', 'Значение', 'Описание'],
            ['Число жизненного пути', str(personal.get('life_path', '')), 'Ваша главная жизненная миссия'],
            ['Число судьбы', str(personal.get('destiny', '')), 'К чему вы стремитесь'],
            ['Число души', str(personal.get('soul', '')), 'Ваша внутренняя сущность'],
            ['Число ума', str(personal.get('mind', '')), 'Способ мышления и восприятия'],
            ['Число личности', str(personal.get('personality', '')), 'Как вас видят окружающие']
        ]
        
        personal_table = Table(personal_data, colWidths=[2*inch, 1*inch, 3*inch])
        personal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#4a90a4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.gray),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(personal_table)
        story.append(Spacer(1, 20))
    
    # Квадрат Пифагора
    if 'enhanced_square' in calculations:
        square = calculations['enhanced_square']
        story.append(Paragraph("⭐ Квадрат Пифагора - Матрица энергий", subtitle_style))
        
        # Создаем таблицу квадрата 3x3
        square_matrix = square.get('square', [['', '', ''], ['', '', ''], ['', '', '']])
        planet_names = [
            ['Солнце', 'Луна', 'Юпитер'],
            ['Раху', 'Центр', 'Венера'], 
            ['Кету', 'Сатурн', 'Марс']
        ]
        
        # Создаем данные для таблицы квадрата
        square_data = []
        for i in range(3):
            row = []
            for j in range(3):
                cell_value = square_matrix[i][j] if square_matrix[i][j] else 'пусто'
                cell_text = f"{planet_names[i][j]}\n{cell_value}"
                row.append(cell_text)
            square_data.append(row)
        
        square_table = Table(square_data, colWidths=[2*inch, 2*inch, 2*inch])
        square_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#fafafa')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 2, HexColor('#4a90a4')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [HexColor('#e8f5e8'), HexColor('#f0f8f0')])
        ]))
        
        story.append(square_table)
        story.append(Spacer(1, 15))
        
        # Суммы по линиям
        if 'horizontal_sums' in square:
            story.append(Paragraph("📊 Анализ линий квадрата", ParagraphStyle('SubHeader', parent=body_style, fontSize=12, textColor=HexColor('#2c5f2d'))))
            
            sums_data = [
                ['Направление', 'Значение', 'Интерпретация'],
                ['Горизонтальные суммы', f"{square.get('horizontal_sums', [])}", 'Материальная сфера, практичность'],
                ['Вертикальные суммы', f"{square.get('vertical_sums', [])}", 'Духовная сфера, интуиция'],
                ['Диагональные суммы', f"{square.get('diagonal_sums', [])}", 'Баланс между материальным и духовным']
            ]
            
            sums_table = Table(sums_data, colWidths=[2*inch, 2*inch, 2*inch])
            sums_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c5f2d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.gray),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            story.append(sums_table)
        
        story.append(Spacer(1, 30))
    
    # Ведическая нумерология  
    if vedic_data:
        story.append(Paragraph("🕉️ Ведическая нумерология", subtitle_style))
        
        vedic_info = [
            ['Параметр', 'Санскрит', 'Значение', 'Описание'],
            ['Число рождения (Джанма)', vedic_data.get('janma_ank_sanskrit', ''), 
             str(vedic_data.get('janma_ank', '')), 'Ваша природная сущность'],
            ['Число имени (Нама)', vedic_data.get('nama_ank_sanskrit', ''), 
             str(vedic_data.get('nama_ank', '')), 'Социальная личность'],
            ['Число удачи (Бхагья)', vedic_data.get('bhagya_ank_sanskrit', ''),
             str(vedic_data.get('bhagya_ank', '')), 'Путь к успеху'],
            ['Число души (Атма)', vedic_data.get('atma_ank_sanskrit', ''),
             str(vedic_data.get('atma_ank', '')), 'Духовная сущность']
        ]
        
        vedic_table = Table(vedic_info, colWidths=[1.5*inch, 1.5*inch, 1*inch, 2*inch])
        vedic_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#ff9933')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.gray),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(vedic_table)
        story.append(Spacer(1, 20))
    
    # Планетарные влияния
    if charts_data and 'planetary_energy' in charts_data:
        story.append(Paragraph("📈 Планетарные энергии (График за неделю)", subtitle_style))
        
        # Создаем график планетарных энергий 
        chart_image = create_planetary_chart(charts_data['planetary_energy'])
        if chart_image:
            story.append(Image(chart_image, width=6*inch, height=3*inch))
        
        story.append(Spacer(1, 20))
    
    # Рекомендации
    story.append(Paragraph("💡 Персональные рекомендации", subtitle_style))
    
    recommendations_text = """
    <b>Сильные стороны:</b><br/>
    • Используйте свои природные таланты для достижения целей<br/>
    • Развивайте качества своего числа жизненного пути<br/>
    • Следуйте интуиции в принятии важных решений<br/><br/>
    
    <b>Области для развития:</b><br/>
    • Работайте над балансом материального и духовного<br/>
    • Укрепляйте слабые позиции в квадрате Пифагора<br/>
    • Используйте ведические практики для гармонизации энергий<br/><br/>
    
    <b>Благоприятные направления:</b><br/>
    • Следуйте планетарным часам для важных дел<br/>
    • Избегайте неблагоприятных периодов (Раху Кала)<br/>
    • Практикуйте медитацию в период Абхиджит Мухурта
    """
    
    story.append(Paragraph(recommendations_text, body_style))
    story.append(Spacer(1, 30))
    
    # Подпись
    story.append(Paragraph("Создано с помощью NUMEROM - Древняя мудрость для современной жизни", 
                          ParagraphStyle('Footer', parent=body_style, fontSize=8, 
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
    
    return buffer.getvalue()