from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import random
import re

def parse_birth_date(birth_date: str) -> tuple[int, int, int]:
    """Parse birth date in DD.MM.YYYY format"""
    try:
        day, month, year = birth_date.split('.')
        return int(day), int(month), int(year)
    except:
        raise ValueError("Invalid date format. Use DD.MM.YYYY")

def reduce_to_single_digit(number: int) -> int:
    """Reduce number to single digit (except master numbers 11, 22, 33)"""
    if number in [11, 22, 33]:
        return number
    
    while number > 9:
        number = sum(int(digit) for digit in str(number))
    return number

# Vedic Numerology Calculations
def calculate_janma_ank(day: int, month: int, year: int) -> int:
    """Calculate Janma Ank (Life Path/Birth Number)"""
    total = day + month + year
    return reduce_to_single_digit(total)

def calculate_bhagya_ank(day: int, month: int, year: int) -> int:
    """Calculate Bhagya Ank (Destiny Number)"""
    all_digits = [int(d) for d in str(day) + str(month) + str(year)]
    total = sum(all_digits)
    return reduce_to_single_digit(total)

def calculate_atma_ank(day: int) -> int:
    """Calculate Atma Ank (Soul Number)"""
    return reduce_to_single_digit(day)

def calculate_nama_ank(name: str) -> int:
    """Calculate Nama Ank (Name Number) - simplified version"""
    # Vedic name number calculation (can be expanded with proper Sanskrit mappings)
    values = {
        'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8, 'i': 9,
        'j': 1, 'k': 2, 'l': 3, 'm': 4, 'n': 5, 'o': 6, 'p': 7, 'q': 8, 'r': 9,
        's': 1, 't': 2, 'u': 3, 'v': 4, 'w': 5, 'x': 6, 'y': 7, 'z': 8
    }
    total = sum(values.get(char.lower(), 0) for char in name if char.isalpha())
    return reduce_to_single_digit(total)

def calculate_shakti_ank(janma_ank: int, nama_ank: int) -> int:
    """Calculate Shakti Ank (Power Number)"""
    return reduce_to_single_digit(janma_ank + nama_ank)

def get_graha_names() -> Dict[int, str]:
    """Get Vedic planetary names for each number"""
    return {
        1: "सूर्य (Surya)",      # Sun
        2: "चन्द्र (Chandra)",    # Moon
        3: "गुरु (Guru)",         # Jupiter
        4: "राहु (Rahu)",         # North Node
        5: "बुध (Budha)",         # Mercury
        6: "शुक्र (Shukra)",      # Venus
        7: "केतु (Ketu)",         # South Node
        8: "शनि (Shani)",        # Saturn
        9: "मंगल (Mangal)"       # Mars
    }

def calculate_graha_shakti(day: int, month: int, year: int) -> Dict[str, int]:
    """Calculate Graha Shakti (Planetary Strength) with Vedic names"""
    birth_digits = [int(d) for d in str(day) + str(month) + str(year)]
    graha_names = get_graha_names()
    
    graha_shakti = {}
    for number, name in graha_names.items():
        # Use string keys for MongoDB compatibility
        graha_shakti[f"graha_{number}_{name}"] = birth_digits.count(number)
    
    return graha_shakti

def create_vedic_yantra(day: int, month: int, year: int) -> Dict[str, Any]:
    """Create Vedic Yantra (enhanced Pythagorean Square) with proper colors and planets"""
    birth_digits = [int(d) for d in str(day) + str(month) + str(year)]
    graha_names = get_graha_names()
    
    # Yantra matrix 3x3 with Vedic planetary positions
    yantra = [['', '', ''], ['', '', ''], ['', '', '']]
    
    # Vedic planetary positions in yantra
    graha_positions = {
        1: [0, 0],  # Surya - Top-left
        2: [1, 0],  # Chandra - Middle-left  
        3: [2, 0],  # Guru - Bottom-left
        4: [0, 1],  # Rahu - Top-center
        5: [1, 1],  # Budha - Center
        6: [2, 1],  # Shukra - Bottom-center
        7: [0, 2],  # Ketu - Top-right
        8: [1, 2],  # Shani - Middle-right
        9: [2, 2]   # Mangal - Bottom-right
    }
    
    # Fill yantra with numbers
    for i in range(1, 10):
        count = birth_digits.count(i)
        if count > 0:
            row, col = graha_positions[i]
            yantra[row][col] = str(i) * count
    
    # Calculate directional sums (Vedic interpretation)
    horizontal_sums = [sum(int(d) for cell in row for d in cell if d.isdigit()) for row in yantra]
    vertical_sums = [sum(int(d) for row in yantra for d in row[i] if d.isdigit()) for i in range(3)]
    
    # Diagonal sums for spiritual analysis
    main_diagonal = sum(int(d) for i in range(3) for d in yantra[i][i] if d.isdigit())
    anti_diagonal = sum(int(d) for i in range(3) for d in yantra[i][2-i] if d.isdigit())
    
    return {
        "yantra_matrix": yantra,
        "yantra_sums": {
            "horizontal": horizontal_sums,
            "vertical": vertical_sums,
            "diagonal": [main_diagonal, anti_diagonal]
        },
        "graha_positions": {str(k): v for k, v in graha_positions.items()},  # Convert keys to strings
        "graha_names": {str(k): v for k, v in graha_names.items()}  # Convert keys to strings
    }

def get_vedic_color_for_number(number: int) -> str:
    """Get traditional Vedic color for each planetary number"""
    vedic_colors = {
        1: "#FF6B35",  # Surya - Orange/Red
        2: "#E8F4FD",  # Chandra - Silver/White  
        3: "#FFD700",  # Guru - Yellow/Gold
        4: "#8B4513",  # Rahu - Brown/Dark
        5: "#90EE90",  # Budha - Green
        6: "#FFB6C1",  # Shukra - Pink/Rose
        7: "#9932CC",  # Ketu - Purple/Violet
        8: "#2F4F4F",  # Shani - Dark Grey/Black
        9: "#DC143C"   # Mangal - Red/Crimson
    }
    return vedic_colors.get(number, "#E5E5E5")

def calculate_mahadasha(birth_date: str) -> str:
    """Calculate current Mahadasha (major planetary period)"""
    day, month, year = parse_birth_date(birth_date)
    
    # Simplified Mahadasha calculation based on birth year
    birth_year_digit = reduce_to_single_digit(year)
    graha_names = get_graha_names()
    
    return graha_names.get(birth_year_digit, "Surya")

def calculate_antardasha(birth_date: str) -> str:
    """Calculate current Antardasha (minor planetary period)"""
    day, month, year = parse_birth_date(birth_date)
    
    # Simplified Antardasha based on current month
    current_month = datetime.now().month
    antardasha_number = reduce_to_single_digit(month + current_month)
    graha_names = get_graha_names()
    
    return graha_names.get(antardasha_number, "Chandra")

def get_vedic_upayas(janma_ank: int) -> List[str]:
    """Get Vedic remedies (Upayas) for each birth number"""
    upayas = {
        1: [
            "सूर्य नमस्कार का अभ्यास करें (Practice Surya Namaskara)",
            "रविवार को लाल वस्त्र धारण करें (Wear red clothes on Sunday)",
            "गुड़ और गेहूं का दान करें (Donate jaggery and wheat)"
        ],
        2: [
            "सोमवार को श्वेत वस्त्र धारण करें (Wear white clothes on Monday)", 
            "चांदी की अंगूठी पहनें (Wear silver ring)",
            "चावल और दूध का दान करें (Donate rice and milk)"
        ],
        3: [
            "गुरुवार को पीले वस्त्र धारण करें (Wear yellow clothes on Thursday)",
            "पुखराज धारण करें (Wear Yellow Sapphire)",
            "हल्दी और चना दाल का दान करें (Donate turmeric and gram dal)"
        ],
        4: [
            "शनिवार को काले तिल का दान करें (Donate black sesame on Saturday)",
            "गोमेद धारण करें (Wear Hessonite garnet)",
            "राहु मंत्र का जाप करें (Chant Rahu mantras)"
        ],
        5: [
            "बुधवार को हरे वस्त्र धारण करें (Wear green clothes on Wednesday)",
            "पन्ना धारण करें (Wear Emerald)",
            "मूंग दाल का दान करें (Donate green gram)"
        ],
        6: [
            "शुक्रवार को सफ़ेद या गुलाबी वस्त्र धारण करें (Wear white or pink on Friday)",
            "हीरा या ओपल धारण करें (Wear Diamond or Opal)",
            "चीनी और दूध का दान करें (Donate sugar and milk)"
        ],
        7: [
            "मंगलवार को बैंगनी वस्त्र धारण करें (Wear purple clothes on Tuesday)",
            "लहसुनिया धारण करें (Wear Cat's Eye)",
            "केतु मंत्र का जाप करें (Chant Ketu mantras)"
        ],
        8: [
            "शनिवार को काले वस्त्र धारण करें (Wear black clothes on Saturday)",
            "नीलम धारण करें (Wear Blue Sapphire)",
            "तिल और काले उड़द का दान करें (Donate sesame and black gram)"
        ],
        9: [
            "मंगलवार को लाल वस्त्र धारण करें (Wear red clothes on Tuesday)",
            "मूंगा धारण करें (Wear Red Coral)",
            "गुड़ और मसूर दाल का दान करें (Donate jaggery and red lentils)"
        ]
    }
    return upayas.get(janma_ank, ["नियमित ध्यान और प्राणायाम करें (Practice regular meditation and pranayama)"])

def get_vedic_mantras(janma_ank: int) -> List[str]:
    """Get Vedic mantras for each birth number"""
    mantras = {
        1: ["ॐ ह्राम ह्रीम ह्राम सः सूर्याय नमः", "गायत्री मंत्र"],
        2: ["ॐ सोम सोमाय नमः", "चन्द्र मंत्र"],
        3: ["ॐ ग्राम ग्रीम ग्राम सः गुरवे नमः", "बृहस्पति मंत्र"],
        4: ["ॐ रां राहवे नमः", "राहु मंत्र"],
        5: ["ॐ बुम बुधाय नमः", "बुध मंत्र"],
        6: ["ॐ शुम शुक्राय नमः", "शुक्र मंत्र"],
        7: ["ॐ केम केतवे नमः", "केतु मंत्र"],
        8: ["ॐ शम शनैश्चराय नमः", "शनि मंत्र"],
        9: ["ॐ अम अंगारकाय नमः", "मंगल मंत्र"]
    }
    return mantras.get(janma_ank, ["ॐ गं गणपतये नमः"])

def get_vedic_gemstones(janma_ank: int) -> List[str]:
    """Get recommended Vedic gemstones"""
    gemstones = {
        1: ["माणिक्य (Ruby)", "गार्नेट (Garnet)"],
        2: ["मोती (Pearl)", "मूनस्टोन (Moonstone)"],
        3: ["पुखराज (Yellow Sapphire)", "सिट्रिन (Citrine)"],
        4: ["गोमेद (Hessonite)", "कार्नेलियन (Carnelian)"],
        5: ["पन्ना (Emerald)", "पेरिडॉट (Peridot)"],
        6: ["हीरा (Diamond)", "ओपल (Opal)"],
        7: ["लहसुनिया (Cat's Eye)", "अमेथिस्ट (Amethyst)"],
        8: ["नीलम (Blue Sapphire)", "अनुलोम (Iolite)"],
        9: ["मूंगा (Red Coral)", "कारेलियन (Carnelian)"]
    }
    return gemstones.get(janma_ank, ["स्फटिक (Crystal Quartz)"])

def calculate_comprehensive_vedic_numerology(birth_date: str, name: str = "") -> Dict[str, Any]:
    """Calculate comprehensive Vedic numerology analysis"""
    day, month, year = parse_birth_date(birth_date)
    
    # Core Vedic numbers
    janma_ank = calculate_janma_ank(day, month, year)
    bhagya_ank = calculate_bhagya_ank(day, month, year)
    atma_ank = calculate_atma_ank(day)
    nama_ank = calculate_nama_ank(name) if name else janma_ank
    shakti_ank = calculate_shakti_ank(janma_ank, nama_ank)
    
    # Planetary analysis
    graha_shakti = calculate_graha_shakti(day, month, year)
    
    # Yantra analysis
    yantra_analysis = create_vedic_yantra(day, month, year)
    
    # Current planetary periods
    mahadasha = calculate_mahadasha(birth_date)
    antardasha = calculate_antardasha(birth_date)
    
    # Remedial measures
    upayas = get_vedic_upayas(janma_ank)
    mantras = get_vedic_mantras(janma_ank)
    gemstones = get_vedic_gemstones(janma_ank)
    
    return {
        "janma_ank": janma_ank,
        "nama_ank": nama_ank,
        "bhagya_ank": bhagya_ank,
        "atma_ank": atma_ank,
        "shakti_ank": shakti_ank,
        "graha_shakti": graha_shakti,
        "mahadasha": mahadasha,
        "antardasha": antardasha,
        "yantra_matrix": yantra_analysis["yantra_matrix"],
        "yantra_sums": yantra_analysis["yantra_sums"],
        "graha_positions": yantra_analysis["graha_positions"],
        "graha_names": yantra_analysis["graha_names"],
        "upayas": upayas,
        "mantras": mantras,
        "gemstones": gemstones
    }

# Planetary Energy Chart Data Generation
def generate_weekly_planetary_energy(birth_date: str) -> List[Dict[str, Any]]:
    """Generate weekly planetary energy data for charts"""
    day, month, year = parse_birth_date(birth_date)
    janma_ank = calculate_janma_ank(day, month, year)
    
    weekly_data = []
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Generate 7 days of energy data
    for i in range(7):
        current_date = base_date + timedelta(days=i)
        day_energy = calculate_daily_planetary_energy(janma_ank, current_date)
        weekly_data.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "day_name": current_date.strftime("%A"),
            **day_energy
        })
    
    return weekly_data

def calculate_daily_planetary_energy(janma_ank: int, date: datetime) -> Dict[str, int]:
    """Calculate planetary energy for a specific day"""
    # Base energy calculation using birth number and current date
    day_number = date.day
    month_number = date.month
    year_number = date.year % 100
    
    # Calculate energy for each planet (1-100 scale)
    base_energy = (janma_ank * 10) % 100
    
    return {
        "surya": min(100, max(0, base_energy + (day_number % 20) - 10)),
        "chandra": min(100, max(0, base_energy + (month_number % 20) - 10)),
        "mangal": min(100, max(0, base_energy + ((day_number + month_number) % 20) - 10)),
        "budha": min(100, max(0, base_energy + (year_number % 20) - 10)),
        "guru": min(100, max(0, base_energy + ((day_number * 2) % 20) - 10)),
        "shukra": min(100, max(0, base_energy + ((month_number * 2) % 20) - 10)),
        "shani": min(100, max(0, base_energy + ((year_number * 2) % 20) - 10)),
        "rahu": min(100, max(0, base_energy + ((day_number + year_number) % 20) - 10)),
        "ketu": min(100, max(0, base_energy + ((month_number + year_number) % 20) - 10))
    }

# Enhanced Quiz Question Pool
VEDIC_QUIZ_QUESTIONS = [
    {
        "id": "vedic_1",
        "question": "Какой цвет лучше всего отражает вашу внутренную энергию?",
        "options": [
            {"text": "Огненно-красный (अग्नि)", "value": 1},
            {"text": "Лунно-серебристый (चाँदी)", "value": 2}, 
            {"text": "Солнечно-золотой (सुनहरा)", "value": 3},
            {"text": "Земляно-коричневый (भूमि)", "value": 4},
            {"text": "Природно-зелёный (हरा)", "value": 5},
            {"text": "Нежно-розовый (गुलाबी)", "value": 6},
            {"text": "Мистически-фиолетовый (बैंगनी)", "value": 7},
            {"text": "Глубоко-синий (नीला)", "value": 8},
            {"text": "Страстно-алый (लाल)", "value": 9}
        ],
        "category": "vedic_colors"
    },
    {
        "id": "vedic_2", 
        "question": "В какое время суток вы чувствуете наибольший прилив сил?",
        "options": [
            {"text": "На рассвете (उषाकाल)", "value": 1},
            {"text": "Ранним утром (प्रातःकाल)", "value": 2},
            {"text": "В полдень (मध्याह्न)", "value": 3},
            {"text": "После полудня (अपराह्न)", "value": 4},
            {"text": "Вечером (सायंकाल)", "value": 5},
            {"text": "На закате (सूर्यास्त)", "value": 6},
            {"text": "В сумерки (गोधूलि)", "value": 7},
            {"text": "Ночью (रात्रि)", "value": 8},
            {"text": "В полночь (अर्धरात्रि)", "value": 9}
        ],
        "category": "vedic_time"
    },
    {
        "id": "vedic_3",
        "question": "Какой элемент природы вас больше всего привлекает?",
        "options": [
            {"text": "Огонь (अग्नि) - трансформация", "value": 1},
            {"text": "Вода (जल) - текучесть", "value": 2},
            {"text": "Воздух (वायु) - движение", "value": 3},
            {"text": "Земля (पृथ्वी) - стабильность", "value": 4},
            {"text": "Эфир (आकाश) - пространство", "value": 5},
            {"text": "Растения (वनस्पति) - рост", "value": 6},
            {"text": "Металлы (धातु) - прочность", "value": 7},
            {"text": "Кристаллы (रत्न) - чистота", "value": 8},
            {"text": "Энергия (शक्ति) - сила", "value": 9}
        ],
        "category": "vedic_elements"
    },
    {
        "id": "personality_1",
        "question": "Как вы предпочитаете решать жизненные проблемы?",
        "options": [
            {"text": "Действую решительно и быстро", "value": 1},
            {"text": "Ищу гармоничное решение для всех", "value": 2},
            {"text": "Подхожу творчески и нестандартно", "value": 3},
            {"text": "Планирую каждый шаг методично", "value": 4},
            {"text": "Изучаю все возможные варианты", "value": 5},
            {"text": "Забочусь о благе близких людей", "value": 6},
            {"text": "Медитирую и слушаю интуицию", "value": 7},
            {"text": "Выбираю практичное решение", "value": 8},
            {"text": "Руководствуюсь высшими принципами", "value": 9}
        ],
        "category": "problem_solving"
    },
    {
        "id": "spiritual_1",
        "question": "Что для вас означает духовное развитие?",
        "options": [
            {"text": "Лидерство и самопознание", "value": 1},
            {"text": "Гармония и сотрудничество", "value": 2},
            {"text": "Творческое самовыражение", "value": 3},
            {"text": "Создание прочной основы", "value": 4},
            {"text": "Поиск истины и свободы", "value": 5},
            {"text": "Служение и забота о других", "value": 6},
            {"text": "Глубокое понимание мироздания", "value": 7},
            {"text": "Достижение материального баланса", "value": 8},
            {"text": "Универсальная любовь и мудрость", "value": 9}
        ],
        "category": "spirituality"
    }
    # Add more questions for variety...
]

def get_randomized_quiz_questions(num_questions: int = 10) -> List[Dict[str, Any]]:
    """Get randomized quiz questions from the pool"""
    available_questions = VEDIC_QUIZ_QUESTIONS.copy()
    
    # Ensure we have enough questions
    if len(available_questions) < num_questions:
        # Duplicate and modify questions if needed
        additional_needed = num_questions - len(available_questions)
        for i in range(additional_needed):
            base_question = available_questions[i % len(VEDIC_QUIZ_QUESTIONS)].copy()
            base_question["id"] = f"{base_question['id']}_extra_{i}"
            available_questions.append(base_question)
    
    # Randomly select questions
    selected_questions = random.sample(available_questions, num_questions)
    
    # Randomize answer order for each question
    for question in selected_questions:
        random.shuffle(question["options"])
    
    return selected_questions