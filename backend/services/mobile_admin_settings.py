"""Typed, bounded configuration shared by mobile admin editors."""
import math
from fastapi import HTTPException
from models import (LearningPointsConfig, CreditsDeductionConfig,
                    PlanetaryEnergyModifiersConfig, MonthlyRouteConfig)

MODELS = {
    'learning': ('learning_points_config', LearningPointsConfig),
    'costs': ('credits_deduction_config', CreditsDeductionConfig),
    'planetary-energy': ('planetary_energy_modifiers_config', PlanetaryEnergyModifiersConfig),
    'monthly-route': ('monthly_route_config', MonthlyRouteConfig),
}
LABELS = {
    'video_points_per_minute':'Видео: баллов за минуту', 'pdf_points_per_view':'PDF: баллов за просмотр',
    'media_points_per_view':'Материалы: баллов за просмотр', 'time_points_per_minute':'Обучение: баллов за минуту',
    'challenge_points_per_day':'Челлендж: баллов за день', 'challenge_bonus_points':'Челлендж: награда за завершение',
    'quiz_points_per_attempt':'Тест: награда за прохождение', 'exercise_points_per_submission':'Упражнение: награда за отправку',
    'name_numerology':'Число имени', 'address_numerology':'Адрес', 'car_numerology':'Автомобиль',
    'personal_numbers':'Персональные числа', 'pythagorean_square':'Квадрат Пифагора', 'compatibility_pair':'Совместимость пары',
    'group_compatibility':'Групповая совместимость', 'vedic_daily':'Ведическое время на день',
    'planetary_daily':'Маршрут на день', 'planetary_weekly':'Маршрут на неделю', 'planetary_monthly':'Маршрут на месяц',
    'planetary_quarterly':'Маршрут на квартал', 'planetary_energy_weekly':'Энергия планет на неделю',
    'planetary_energy_monthly':'Энергия планет на месяц', 'planetary_energy_quarterly':'Энергия планет на квартал',
    'personality_test':'Тест личности', 'quiz_completion':'Прохождение теста', 'lesson_viewing':'Просмотр урока',
    'material_viewing':'Просмотр материала', 'pdf_report_numerology':'Нумерология: PDF',
    'html_report_numerology':'Нумерология: HTML', 'pdf_report_compatibility':'Совместимость: PDF',
    'html_report_compatibility':'Совместимость: HTML',
    'friend_planet_bonus':'Дружественные планеты: прибавка', 'enemy_planet_penalty':'Враждебные планеты: снижение',
    'fractal_present_bonus':'Присутствие во фрактале: прибавка', 'fractal_absent_penalty':'Отсутствие во фрактале: снижение',
    'problem_number_penalty':'Числа проблем: снижение', 'individual_year_bonus':'Индивидуальный год: прибавка',
    'individual_month_bonus':'Индивидуальный месяц: прибавка', 'individual_day_bonus':'Индивидуальный день: прибавка',
    'pythagorean_digit_bonus':'Цифра в квадрате: прибавка', 'soul_number_bonus':'Число души: прибавка',
    'mind_number_bonus':'Число ума: прибавка', 'destiny_number_bonus':'Число судьбы: прибавка',
    'wisdom_number_bonus':'Число мудрости: прибавка', 'ruling_number_bonus':'Правящее число: прибавка',
    'line_sum_bonus':'Сумма линии: прибавка', 'name_number_bonus':'Число имени: прибавка',
    'surname_number_bonus':'Число фамилии: прибавка', 'total_name_bonus':'Полное имя: прибавка',
    'weekday_multiplier':'Множитель дня недели', 'personal_day_match_bonus':'Совпадение личного дня: прибавка',
    'personal_month_match_bonus':'Совпадение личного месяца: прибавка', 'current_day_match_bonus':'Совпадение текущего дня: прибавка',
    'enemy_mismatch_penalty':'Несовпадение враждебной планеты: снижение', 'friend_mismatch_bonus':'Несовпадение дружественной планеты: прибавка',
    'neutral_mismatch_penalty':'Несовпадение нейтральной планеты: снижение', 'problem_number_match_penalty':'Совпадение числа проблемы: снижение',
    'janma_ank_22_bonus':'Джанма-анк 22: прибавка', 'janma_ank_22_match_bonus':'Джанма-анк 22 и день: прибавка',
    'cyclicity_bonus':'Повторяющиеся числа: прибавка', 'cyclicity_penalty':'Цикличность: снижение',
    'normalization_min':'Минимум нормализации', 'normalization_max':'Максимум нормализации',
    'energy_cap_multiplier':'Множитель максимума энергии', 'energy_floor_multiplier':'Множитель минимума энергии',
    'anti_cyclicity_enabled':'Уменьшать цикличность', 'anti_cyclicity_threshold':'Порог обнаружения цикличности',
    'anti_cyclicity_variation':'Величина вариации', 'favorable_day_threshold':'Благоприятный день: порог',
    'favorable_day_score_threshold':'Благоприятный день: порог баллов', 'best_day_threshold':'Лучший день: порог',
    'challenging_day_threshold':'Сложный день: порог', 'high_energy_week_threshold':'Высокая энергия недели: порог',
    'low_energy_week_threshold':'Низкая энергия недели: порог', 'favorable_week_threshold':'Благоприятная неделя: порог',
    'challenging_week_threshold':'Сложная неделя: порог', 'many_favorable_days_threshold':'Много благоприятных дней: количество',
    'several_challenging_days_threshold':'Несколько сложных дней: количество', 'sphere_excellent_threshold':'Сфера: отлично',
    'sphere_good_threshold':'Сфера: хорошо', 'sphere_satisfactory_threshold':'Сфера: удовлетворительно',
    'sphere_attention_threshold':'Сфера: требует внимания', 'sphere_best_days_threshold':'Сфера: лучшие дни',
    'sphere_challenging_days_threshold':'Сфера: сложные дни', 'optimal_start_energy_threshold':'Начинания: порог энергии',
    'optimal_start_min_days':'Начинания: минимум дней', 'completion_energy_min':'Завершение: минимум энергии',
    'completion_energy_max':'Завершение: максимум энергии', 'completion_min_days':'Завершение: минимум дней',
    'trend_rising_threshold':'Рост: величина изменения', 'trend_declining_threshold':'Спад: величина изменения',
    'transit_peak_threshold':'Транзит: пик энергии', 'transit_low_threshold':'Транзит: низкая энергия',
    'max_transits_per_month':'Транзитов в месяц: максимум', 'month_high_energy_threshold':'Месяц: высокая энергия',
    'month_low_energy_threshold':'Месяц: низкая энергия',
}

def settings_spec(kind):
    if kind == 'telegram-stars':
        from services.telegram_pricing import COLLECTION, PRODUCT_LABELS, MAX_STARS, default_prices
        return COLLECTION, default_prices(), {key: {'type': 'integer', 'label': label,
            'min': 0, 'max': MAX_STARS} for key, label in PRODUCT_LABELS.items()}
    if kind not in MODELS: raise HTTPException(404, 'Настройки не найдены')
    collection, model = MODELS[kind]
    defaults = {k:v for k,v in model().model_dump().items() if type(v) in (int,float,bool) and k not in ('version','is_active')}
    fields = {}
    for key, value in defaults.items():
        type_name = {int:'integer',float:'number',bool:'boolean'}[type(value)]
        field = {'type':type_name, 'label':LABELS[key]}
        if type(value) is not bool:
            low, high = 0, 1000 if kind == 'learning' else 1000000 if kind == 'costs' else 100
            if kind == 'planetary-energy':
                if key.endswith(('_bonus','_penalty')): high=1
                if key in ('line_sum_bonus','weekday_multiplier'): high=10
                if key=='energy_cap_multiplier': low,high=1,10
                if key=='energy_floor_multiplier': high=1
            if kind == 'monthly-route' and type(value) is int:
                low,high=1,7 if key in ('many_favorable_days_threshold','several_challenging_days_threshold') else 100 if key=='max_transits_per_month' else 31
            field.update(min=low,max=high)
        fields[key]=field
    return collection, defaults, fields


def validate_settings(kind, values):
    _, defaults, fields = settings_spec(kind)
    if set(values) != set(defaults): raise HTTPException(422, 'Неизвестная или отсутствующая настройка')
    for key,value in values.items():
        spec=fields[key];typ=spec['type']
        correct = type(value) is bool if typ=='boolean' else type(value) is int if typ=='integer' else type(value) in (int,float)
        if not correct or (typ!='boolean' and (not math.isfinite(value) or not spec['min'] <= value <= spec['max'])):
            raise HTTPException(422, 'Недопустимое значение: '+spec['label'])
    def ordered(*keys, strict=True):
        pairs=zip(keys,keys[1:])
        if any(not (values[a]<values[b] if strict else values[a]<=values[b]) for a,b in pairs):
            raise HTTPException(422, 'Пороги должны идти по возрастанию: '+', '.join(fields[k]['label'] for k in keys))
    if kind=='planetary-energy':
        ordered('normalization_min','normalization_max');ordered('energy_floor_multiplier','energy_cap_multiplier')
    if kind=='monthly-route':
        ordered('challenging_day_threshold','favorable_day_threshold','best_day_threshold')
        ordered('low_energy_week_threshold','challenging_week_threshold',strict=False)
        ordered('challenging_week_threshold','favorable_week_threshold')
        ordered('favorable_week_threshold','high_energy_week_threshold',strict=False)
        ordered('sphere_attention_threshold','sphere_satisfactory_threshold',strict=False)
        ordered('sphere_satisfactory_threshold','sphere_good_threshold','sphere_excellent_threshold')
        ordered('sphere_challenging_days_threshold','sphere_best_days_threshold')
        ordered('completion_energy_min','completion_energy_max',strict=False)
        ordered('transit_low_threshold','transit_peak_threshold');ordered('month_low_energy_threshold','month_high_energy_threshold')
    return values
