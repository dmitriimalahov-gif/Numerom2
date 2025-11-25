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

def reduce_to_single_digit_always(number: int) -> int:
    """Reduce number to single digit always, no exceptions for master numbers"""
    while number > 9:
        number = sum(int(digit) for digit in str(number))
    return number

# Vedic Numerology Calculations
def calculate_janma_ank(day: int, month: int, year: int) -> int:
    """Calculate Janma Ank (Life Path/Birth Number)"""
    total = day + month + year
    return reduce_to_single_digit(total)

def calculate_bhagya_ank(day: int, month: int, year: int) -> int:
    """Calculate Bhagya Ank (Destiny Number) - always reduced to single digit (no master numbers)"""
    all_digits = [int(d) for d in str(day) + str(month) + str(year)]
    total = sum(all_digits)
    return reduce_to_single_digit_always(total)

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
def generate_weekly_planetary_energy(birth_date: str, user_numbers: Dict[str, int] = None, city: str = "Москва", 
                                     pythagorean_square: Dict[str, Any] = None, fractal_behavior: List[int] = None,
                                     problem_numbers: List[int] = None, name_numbers: Dict[str, int] = None,
                                     weekday_energy: Dict[str, float] = None, janma_ank: int = None,
                                     modifiers_config: Dict[str, Any] = None, start_date: datetime = None) -> List[Dict[str, Any]]:
    """Generate weekly planetary energy data for charts with enhanced calculation"""
    day, month, year = parse_birth_date(birth_date)
    if janma_ank is None:
        janma_ank = calculate_janma_ank(day, month, year)
    destiny_number = calculate_bhagya_ank(day, month, year)  # Destiny number (always reduced to single digit)
    
    # Calculate fractal behavior if not provided
    if fractal_behavior is None:
        day_reduced = reduce_to_single_digit(day)
        month_reduced = reduce_to_single_digit(month)
        year_reduced = reduce_to_single_digit(year)
        year_sum = reduce_to_single_digit(day + month + year)
        fractal_behavior = [day_reduced, month_reduced, year_reduced, year_sum]
    
    weekly_data = []
    # Use provided start_date or default to today
    if start_date is None:
        base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        base_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Generate 7 days of energy data
    for i in range(7):
        current_date = base_date + timedelta(days=i)
        
        # Calculate individual numbers for this specific date to check relationships
        # Individual year = reduce(day + month + current_year)
        current_year = current_date.year
        current_month = current_date.month
        current_day = current_date.day
        
        individual_year = reduce_to_single_digit(day + month + current_year)
        individual_month = reduce_to_single_digit(individual_year + current_month)
        individual_day = reduce_to_single_digit(individual_month + current_day)
        
        # Check relationships between destiny number, name numbers, and current day
        # This ensures energies change from week to week
        week_modifier = 0
        if name_numbers:
            # Check if destiny number matches name numbers for this week
            name_num = name_numbers.get('total_name_number') or name_numbers.get('full_name_number') or name_numbers.get('name_number')
            if name_num:
                # Calculate week number (week of year)
                week_number = current_date.isocalendar()[1]
                week_reduced = reduce_to_single_digit(week_number)
                
                # If destiny number, name number, or individual day match, add week-specific modifier
                if destiny_number == week_reduced or name_num == week_reduced or individual_day == week_reduced:
                    week_modifier = 5  # Positive modifier for matches
                elif abs(destiny_number - week_reduced) > 5:
                    week_modifier = -3  # Negative modifier for large differences
        
        # Use enhanced calculation
        day_energy = calculate_enhanced_daily_planetary_energy(
            destiny_number=destiny_number,
            date=current_date,
            birth_date=birth_date,
            user_numbers=user_numbers,
            pythagorean_square=pythagorean_square,
            fractal_behavior=fractal_behavior,
            problem_numbers=problem_numbers,
            name_numbers=name_numbers,
            weekday_energy=weekday_energy,
            janma_ank=janma_ank,
            city=city,
            modifiers_config=modifiers_config
        )
        
        # Apply week-specific modifier to ensure variation between weeks
        if week_modifier != 0:
            # Apply modifier to all planets proportionally
            for planet_key in day_energy:
                day_energy[planet_key] = max(0, min(100, day_energy[planet_key] + week_modifier))
        
        weekly_data.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "day_name": current_date.strftime("%A"),
            **day_energy
        })
    
    return weekly_data

def apply_anti_cyclicity_to_period(period_data: List[Dict[str, Any]], modifiers_config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Apply anti-cyclicity function to a period of data (month/quarter)
    This ensures that each planet has its own dynamic range (0-100%) and varies between days
    Energies can reach 0% or 100% based on matches/mismatches
    """
    if not period_data or len(period_data) < 2:
        return period_data
    
    # Get anti-cyclicity settings
    if modifiers_config is None:
        modifiers_config = {}
    
    anti_cyclicity_enabled = modifiers_config.get('anti_cyclicity_enabled', True)
    if not anti_cyclicity_enabled:
        return period_data
    
    import statistics
    from datetime import datetime
    
    # Get threshold and variation from config
    threshold = modifiers_config.get('anti_cyclicity_threshold', 5.0)
    variation = modifiers_config.get('anti_cyclicity_variation', 3.0)
    
    # Planet order for deterministic variation
    planet_order = ['surya', 'chandra', 'mangal', 'budha', 'guru', 'shukra', 'shani', 'rahu', 'ketu']
    variation_pattern = [0, 1, -1, 2, -2, 1.5, -1.5, 0.5, -0.5]
    
    # Apply anti-cyclicity for each planet individually across the period
    for planet_idx, planet_key in enumerate(planet_order):
        # Get all energies for this planet across the period
        planet_energies = []
        for day_data in period_data:
            if planet_key in day_data:
                planet_energies.append(day_data[planet_key])
        
        if len(planet_energies) < 2:
            continue
        
        # Calculate standard deviation for this planet across the period
        try:
            std_dev = statistics.stdev(planet_energies)
        except:
            std_dev = 0
        
        # If standard deviation is too low (planet energy is too constant), add variation
        if std_dev < threshold:
            # Add variation to each day for this planet
            for day_idx, day_data in enumerate(period_data):
                if planet_key not in day_data:
                    continue
                
                # Calculate variation based on day index and planet position
                day_variation = (day_idx % 7) * 0.4 * variation_pattern[planet_idx % len(variation_pattern)]
                planet_variation = variation * variation_pattern[planet_idx % len(variation_pattern)]
                
                # Add date-based variation if date is available
                if 'date' in day_data:
                    try:
                        date_obj = datetime.strptime(day_data['date'], "%Y-%m-%d")
                        date_variation = (date_obj.day % 9) * 0.3 * (1 if planet_idx % 2 == 0 else -1)
                        month_variation = (date_obj.month % 7) * 0.2 * (1 if planet_idx % 3 == 0 else -1)
                    except:
                        date_variation = 0
                        month_variation = 0
                else:
                    date_variation = 0
                    month_variation = 0
                
                total_variation = day_variation + planet_variation + date_variation + month_variation
                day_data[planet_key] = min(100, max(0, day_data[planet_key] + total_variation))
        
        # Check for cyclicity between consecutive days for this planet
        for day_idx in range(1, len(period_data)):
            if planet_key not in period_data[day_idx] or planet_key not in period_data[day_idx - 1]:
                continue
            
            current_energy = period_data[day_idx][planet_key]
            prev_energy = period_data[day_idx - 1][planet_key]
            difference = abs(current_energy - prev_energy)
            
            # If difference is too small (days are too similar for this planet), add variation
            if difference < 2.0:  # Threshold for day-to-day similarity for this planet
                # Add variation to break similarity
                day_variation = (day_idx % 7) * 0.5 * variation_pattern[planet_idx % len(variation_pattern)]
                planet_variation = variation * variation_pattern[planet_idx % len(variation_pattern)] * 0.8
                
                # Add date-based variation if available
                if 'date' in period_data[day_idx]:
                    try:
                        date_obj = datetime.strptime(period_data[day_idx]['date'], "%Y-%m-%d")
                        date_variation = (date_obj.day % 9) * 0.4 * (1 if planet_idx % 2 == 0 else -1)
                    except:
                        date_variation = 0
                else:
                    date_variation = 0
                
                total_variation = day_variation + planet_variation + date_variation
                period_data[day_idx][planet_key] = min(100, max(0, period_data[day_idx][planet_key] + total_variation))
    
    return period_data

def calculate_daily_planetary_energy(janma_ank: int, date: datetime, birth_date: str = None, user_numbers: Dict[str, int] = None, city: str = "Москва") -> Dict[str, int]:
    """
    Calculate planetary energy for a specific day with enhanced logic
    Includes:
    - Planetary hours (time belonging to each planet)
    - Maximum friend bonus (best friendliness indicator)
    - Maximum enemy penalty (worst enemy indicator)
    - All values normalized to 0-100%
    """
    try:
        from vedic_time_calculations import get_sunrise_sunset, calculate_planetary_hours, calculate_night_planetary_hours
    except:
        # Fallback if imports fail
        get_sunrise_sunset = None
        calculate_planetary_hours = None
        calculate_night_planetary_hours = None
    
    # Base energy calculation using birth number and current date
    day_number = date.day
    month_number = date.month
    year_number = date.year % 100
    
    # Calculate energy for each planet (1-100 scale)
    base_energy = (janma_ank * 10) % 100
    
    # Calculate personal day number
    personal_day = 0
    if birth_date and user_numbers:
        try:
            day, month, year = parse_birth_date(birth_date)
            current_year = date.year
            current_month = date.month
            current_day = date.day
            
            # Personal year = reduce_to_single_digit(day + month + current_year)
            personal_year = reduce_to_single_digit(day + month + current_year)
            # Personal month = reduce_to_single_digit(personal_year + current_month)
            personal_month = reduce_to_single_digit(personal_year + current_month)
            # Personal day = reduce_to_single_digit(personal_month + current_day)
            personal_day = reduce_to_single_digit(personal_month + current_day)
        except:
            pass
    
    # Planet relationships (friends and enemies)
    planet_relationships = {
        'Surya': {'friends': ['Chandra', 'Mangal', 'Guru'], 'enemies': ['Shukra', 'Shani']},
        'Chandra': {'friends': ['Surya', 'Budh'], 'enemies': []},
        'Mangal': {'friends': ['Surya', 'Chandra', 'Guru'], 'enemies': ['Budh']},
        'Budh': {'friends': ['Surya', 'Shukra'], 'enemies': ['Chandra']},
        'Guru': {'friends': ['Surya', 'Chandra', 'Mangal'], 'enemies': ['Budh', 'Shukra']},
        'Shukra': {'friends': ['Budh', 'Shani'], 'enemies': ['Surya', 'Chandra']},
        'Shani': {'friends': ['Budh', 'Shukra', 'Rahu'], 'enemies': ['Surya', 'Chandra', 'Mangal']},
        'Rahu': {'friends': ['Budh', 'Shukra', 'Shani'], 'enemies': ['Surya', 'Chandra', 'Mangal']},
        'Ketu': {'friends': ['Mangal', 'Guru'], 'enemies': ['Surya', 'Chandra', 'Budh']}
    }
    
    # Number to planet mapping
    number_to_planet = {
        1: 'Surya', 2: 'Chandra', 3: 'Guru', 4: 'Rahu',
        5: 'Budh', 6: 'Shukra', 7: 'Ketu', 8: 'Shani', 9: 'Mangal'
    }
    
    # Planet name normalization (Budh -> Budha, etc.)
    planet_name_map = {
        'Surya': 'surya', 'Chandra': 'chandra', 'Mangal': 'mangal',
        'Budh': 'budha', 'Budha': 'budha', 'Guru': 'guru',
        'Shukra': 'shukra', 'Shani': 'shani', 'Rahu': 'rahu', 'Ketu': 'ketu'
    }
    
    # Get ruling planet for the day (based on weekday)
    weekday = date.weekday()  # 0=Monday, 6=Sunday
    day_planets = ['Chandra', 'Mangal', 'Budh', 'Guru', 'Shukra', 'Shani', 'Surya']
    ruling_planet = day_planets[weekday]
    
    # Calculate base energies for each planet
    planet_energies = {
        "surya": base_energy + (day_number % 20) - 10,
        "chandra": base_energy + (month_number % 20) - 10,
        "mangal": base_energy + ((day_number + month_number) % 20) - 10,
        "budha": base_energy + (year_number % 20) - 10,
        "guru": base_energy + ((day_number * 2) % 20) - 10,
        "shukra": base_energy + ((month_number * 2) % 20) - 10,
        "shani": base_energy + ((year_number * 2) % 20) - 10,
        "rahu": base_energy + ((day_number + year_number) % 20) - 10,
        "ketu": base_energy + ((month_number + year_number) % 20) - 10
    }
    
    # Add personal day bonus
    if personal_day > 0:
        personal_day_planet = number_to_planet.get(personal_day)
        if personal_day_planet:
            planet_key = planet_name_map.get(personal_day_planet, personal_day_planet.lower())
            if planet_key in planet_energies:
                planet_energies[planet_key] += 15  # Bonus for personal day planet
    
    # Add user personal day bonus (if user has personal day number)
    if user_numbers and user_numbers.get('personal_day'):
        user_personal_day = user_numbers.get('personal_day')
        user_personal_day_planet = number_to_planet.get(user_personal_day)
        if user_personal_day_planet:
            planet_key = planet_name_map.get(user_personal_day_planet, user_personal_day_planet.lower())
            if planet_key in planet_energies:
                planet_energies[planet_key] += 10  # Bonus for user's personal day planet
    
    # Calculate planetary hours for the day (time belonging to each planet)
    planetary_hours_count = {
        "surya": 0, "chandra": 0, "mangal": 0, "budha": 0,
        "guru": 0, "shukra": 0, "shani": 0, "rahu": 0, "ketu": 0
    }
    
    if get_sunrise_sunset and calculate_planetary_hours and calculate_night_planetary_hours:
        try:
            sunrise, sunset = get_sunrise_sunset(city, date)
            # Count day hours
            day_hours = calculate_planetary_hours(sunrise, sunset, weekday)
            for hour_data in day_hours:
                planet_name = hour_data.get("planet", "")
                planet_key = planet_name_map.get(planet_name, planet_name.lower())
                if planet_key in planetary_hours_count:
                    planetary_hours_count[planet_key] += 1
            
            # Count night hours
            next_sunrise = sunrise + timedelta(days=1)
            night_hours = calculate_night_planetary_hours(sunset, next_sunrise, weekday)
            for hour_data in night_hours:
                planet_name = hour_data.get("planet", "")
                planet_key = planet_name_map.get(planet_name, planet_name.lower())
                if planet_key in planetary_hours_count:
                    planetary_hours_count[planet_key] += 1
        except:
            pass
    
    # Apply planetary hours bonus (each hour adds +2 to energy)
    for planet_key, hours_count in planetary_hours_count.items():
        if planet_key in planet_energies:
            planet_energies[planet_key] += hours_count * 2
    
    # Find maximum friend bonus and maximum enemy penalty
    max_friend_bonus = 0
    max_enemy_penalty = 0
    
    # Calculate friend/enemy modifiers for each planet
    ruling_planet_data = planet_relationships.get(ruling_planet, {})
    friends = ruling_planet_data.get('friends', [])
    enemies = ruling_planet_data.get('enemies', [])
    
    # Find maximum bonuses/penalties
    for planet_name, planet_key in [('Surya', 'surya'), ('Chandra', 'chandra'), ('Mangal', 'mangal'),
                                     ('Budh', 'budha'), ('Guru', 'guru'), ('Shukra', 'shukra'),
                                     ('Shani', 'shani'), ('Rahu', 'rahu'), ('Ketu', 'ketu')]:
        if planet_name in friends:
            max_friend_bonus = max(max_friend_bonus, 15)  # Maximum friend bonus
        if planet_name in enemies:
            max_enemy_penalty = max(max_enemy_penalty, 15)  # Maximum enemy penalty
    
    # Apply friend/enemy modifiers based on ruling planet
    for planet_name, planet_key in [('Surya', 'surya'), ('Chandra', 'chandra'), ('Mangal', 'mangal'),
                                     ('Budh', 'budha'), ('Guru', 'guru'), ('Shukra', 'shukra'),
                                     ('Shani', 'shani'), ('Rahu', 'rahu'), ('Ketu', 'ketu')]:
        if planet_key in planet_energies:
            # Add bonus for friendly planets (proportional to max friend bonus)
            if planet_name in friends:
                # Calculate proportional bonus: 15 points for best friendliness
                friend_bonus = 15 if len(friends) > 0 else 0
                planet_energies[planet_key] += friend_bonus
            # Subtract penalty for enemy planets (proportional to max enemy penalty)
            if planet_name in enemies:
                # Calculate proportional penalty: -15 points for worst enmity
                enemy_penalty = -15 if len(enemies) > 0 else 0
                planet_energies[planet_key] += enemy_penalty
    
    # Normalize all values to 0-100 range
    # First, find min and max to scale properly
    min_energy = min(planet_energies.values()) if planet_energies else 0
    max_energy = max(planet_energies.values()) if planet_energies else 100
    
    result = {}
    if max_energy > min_energy:
        # Scale to 0-100 range
        for planet_key, energy in planet_energies.items():
            normalized = ((energy - min_energy) / (max_energy - min_energy)) * 100
            result[planet_key] = min(100, max(0, int(normalized)))
    else:
        # If all values are the same, set to base value
        base_normalized = 50  # Middle value
        for planet_key in planet_energies:
            result[planet_key] = base_normalized
    
    return result

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

def calculate_enhanced_daily_planetary_energy(
    destiny_number: int,
    date: datetime,
    birth_date: str = None,
    user_numbers: Dict[str, int] = None,
    pythagorean_square: Dict[str, Any] = None,
    fractal_behavior: List[int] = None,
    problem_numbers: List[int] = None,
    name_numbers: Dict[str, int] = None,
    weekday_energy: Dict[str, float] = None,
    janma_ank: int = None,
    city: str = "Москва",
    modifiers_config: Dict[str, Any] = None
) -> Dict[str, int]:
    """
    Enhanced planetary energy calculation with all factors:
    Uses configurable modifiers from modifiers_config if provided, otherwise uses defaults
    """
    # Get modifiers from config or use defaults
    if modifiers_config is None:
        modifiers_config = {}
    
    # Helper function to get config value or default
    def get_modifier(key: str, default: float) -> float:
        return modifiers_config.get(key, default)
    
    # Number to planet mapping
    number_to_planet = {
        1: 'Surya', 2: 'Chandra', 3: 'Guru', 4: 'Rahu',
        5: 'Budh', 6: 'Shukra', 7: 'Ketu', 8: 'Shani', 9: 'Mangal'
    }
    
    # Planet name normalization
    planet_name_map = {
        'Surya': 'surya', 'Chandra': 'chandra', 'Mangal': 'mangal',
        'Budh': 'budha', 'Budha': 'budha', 'Guru': 'guru',
        'Shukra': 'shukra', 'Shani': 'shani', 'Rahu': 'rahu', 'Ketu': 'ketu'
    }
    
    # Planet relationships (friendliness/hostility)
    planet_relationships = {
        'Surya': {'friends': ['Chandra', 'Mangal', 'Guru'], 'enemies': ['Shukra', 'Shani']},
        'Chandra': {'friends': ['Surya', 'Budh'], 'enemies': []},
        'Mangal': {'friends': ['Surya', 'Chandra', 'Guru'], 'enemies': ['Budh']},
        'Budh': {'friends': ['Surya', 'Shukra'], 'enemies': ['Chandra']},
        'Guru': {'friends': ['Surya', 'Chandra', 'Mangal'], 'enemies': ['Budh', 'Shukra']},
        'Shukra': {'friends': ['Budh', 'Shani'], 'enemies': ['Surya', 'Chandra']},
        'Shani': {'friends': ['Budh', 'Shukra', 'Rahu'], 'enemies': ['Surya', 'Chandra', 'Mangal']},
        'Rahu': {'friends': ['Budh', 'Shukra', 'Shani'], 'enemies': ['Surya', 'Chandra', 'Mangal']},
        'Ketu': {'friends': ['Mangal', 'Guru'], 'enemies': ['Surya', 'Chandra', 'Budh']}
    }
    
    # Get ruling planet for the day (based on weekday)
    weekday = date.weekday()  # 0=Monday, 6=Sunday
    day_planets = ['Chandra', 'Mangal', 'Budh', 'Guru', 'Shukra', 'Shani', 'Surya']
    ruling_planet = day_planets[weekday]
    
    # Calculate base energy = (Janma Ank × 10) mod 100
    if janma_ank is None:
        if birth_date:
            try:
                day, month, year = parse_birth_date(birth_date)
                janma_ank = calculate_janma_ank(day, month, year)
            except:
                janma_ank = destiny_number  # Fallback to destiny number
    
    base_energy = (janma_ank * 10) % 100
    
    # Get date components for modification functions
    day_num = date.day
    month_num = date.month
    year_num = date.year % 100  # Last two digits of year
    
    # Functions of modification for each planet (fP(date))
    # These are based on date and create unique variation for each planet
    modification_functions = {
        "surya": day_num % 20,
        "chandra": month_num % 20,
        "mangal": (day_num + month_num) % 20,
        "budha": year_num % 20,
        "guru": (day_num * 2) % 20,
        "shukra": (month_num * 2) % 20,
        "shani": (year_num * 2) % 20,
        "rahu": (day_num + year_num) % 20,
        "ketu": (month_num + year_num) % 20
    }
    
    # Initialize base energy for each planet = base_energy + fP(date)
    planet_energies = {
        "surya": base_energy + modification_functions["surya"],
        "chandra": base_energy + modification_functions["chandra"],
        "mangal": base_energy + modification_functions["mangal"],
        "budha": base_energy + modification_functions["budha"],
        "guru": base_energy + modification_functions["guru"],
        "shukra": base_energy + modification_functions["shukra"],
        "shani": base_energy + modification_functions["shani"],
        "rahu": base_energy + modification_functions["rahu"],
        "ketu": base_energy + modification_functions["ketu"]
    }
    
    # 1. Planet friendliness/hostility: +12 for friends, -12 for enemies
    ruling_planet_data = planet_relationships.get(ruling_planet, {})
    friends = ruling_planet_data.get('friends', [])
    enemies = ruling_planet_data.get('enemies', [])
    
    for planet_name, planet_key in [('Surya', 'surya'), ('Chandra', 'chandra'), ('Mangal', 'mangal'),
                                     ('Budh', 'budha'), ('Guru', 'guru'), ('Shukra', 'shukra'),
                                     ('Shani', 'shani'), ('Rahu', 'rahu'), ('Ketu', 'ketu')]:
        if planet_key in planet_energies:
            if planet_name in friends:
                # +12 for friendly planets (can be configured, but default is 12)
                friend_bonus = get_modifier('friend_planet_bonus', 0.10)
                # Convert percentage to absolute value if needed, or use direct value
                if friend_bonus < 1:
                    # It's a percentage, convert to absolute (12 = 0.12 * 100)
                    planet_energies[planet_key] += 12
                else:
                    planet_energies[planet_key] += friend_bonus
            elif planet_name in enemies:
                # -12 for enemy planets (can be configured, but default is 12)
                enemy_penalty = get_modifier('enemy_planet_penalty', 0.10)
                # Convert percentage to absolute value if needed, or use direct value
                if enemy_penalty < 1:
                    # It's a percentage, convert to absolute (12 = 0.12 * 100)
                    planet_energies[planet_key] -= 12
                else:
                    planet_energies[planet_key] -= enemy_penalty
    
    # 2. Fractal behavior: present planets +10%, absent -10%
    if fractal_behavior:
        fractal_planets = set()
        for num in fractal_behavior:
            if num in number_to_planet:
                planet_name = number_to_planet[num]
                planet_key = planet_name_map.get(planet_name, planet_name.lower())
                fractal_planets.add(planet_key)
        
        for planet_key in planet_energies:
            if planet_key in fractal_planets:
                planet_energies[planet_key] += destiny_number * get_modifier('fractal_present_bonus', 0.10)
            else:
                planet_energies[planet_key] -= destiny_number * get_modifier('fractal_absent_penalty', 0.10)
    
    # 3. Problem numbers: -10% for present
    if problem_numbers:
        problem_planets = set()
        for num in problem_numbers:
            if num in number_to_planet:
                planet_name = number_to_planet[num]
                planet_key = planet_name_map.get(planet_name, planet_name.lower())
                problem_planets.add(planet_key)
        
        for planet_key in problem_planets:
            if planet_key in planet_energies:
                planet_energies[planet_key] -= destiny_number * get_modifier('problem_number_penalty', 0.10)
    
    # 4. Individual year, month, day
    if birth_date:
        try:
            day, month, year = parse_birth_date(birth_date)
            current_year = date.year
            current_month = date.month
            current_day = date.day
            
            # Individual year = reduce(day + month + current_year)
            individual_year = reduce_to_single_digit(day + month + current_year)
            # Individual month = reduce(individual_year + current_month)
            individual_month = reduce_to_single_digit(individual_year + current_month)
            # Individual day = reduce(individual_month + current_day)
            individual_day = reduce_to_single_digit(individual_month + current_day)
            
            # Apply modifiers for individual numbers with different weights
            # Individual year - important, add energy
            if individual_year in number_to_planet:
                planet_name = number_to_planet[individual_year]
                planet_key = planet_name_map.get(planet_name, planet_name.lower())
                if planet_key in planet_energies:
                    planet_energies[planet_key] += destiny_number * get_modifier('individual_year_bonus', 0.06)
            
            # Individual month - add energy
            if individual_month in number_to_planet:
                planet_name = number_to_planet[individual_month]
                planet_key = planet_name_map.get(planet_name, planet_name.lower())
                if planet_key in planet_energies:
                    planet_energies[planet_key] += destiny_number * get_modifier('individual_month_bonus', 0.05)
            
            # Individual day - most important for current day, add more energy
            # +15 for planet of personal day number (individual day)
            if individual_day in number_to_planet:
                planet_name = number_to_planet[individual_day]
                planet_key = planet_name_map.get(planet_name, planet_name.lower())
                if planet_key in planet_energies:
                    # +15 for planet of personal day number
                    planet_energies[planet_key] += 15
            
            # +10 for planet of user's personal day number (if user has personal day)
            if user_numbers and user_numbers.get('personal_day'):
                user_personal_day = user_numbers.get('personal_day')
                if user_personal_day in number_to_planet:
                    planet_name = number_to_planet[user_personal_day]
                    planet_key = planet_name_map.get(planet_name, planet_name.lower())
                    if planet_key in planet_energies:
                        # +10 for planet of user's personal day number
                        planet_energies[planet_key] += 10
            
            # Calculate problem numbers (ЧПГ, ЧПМ, ЧПД)
            # ЧПГ (Число проблемы года) = ЧИГ - число судьбы (по модулю)
            problem_year = reduce_to_single_digit(abs(individual_year - destiny_number))
            # ЧПМ (Число проблемы месяца) = месяц рождения - ЧИМ (по модулю)
            problem_month = reduce_to_single_digit(abs(month - individual_month))
            # ЧПД (Число проблемы дня) = день рождения - ЧИД (по модулю)
            problem_day = reduce_to_single_digit(abs(day - individual_day))
            
            # MODIFIER: Problem numbers matching - energy drops to almost zero
            # Get all important numbers for comparison with problem numbers
            important_numbers_for_problems = {
                'individual_year': individual_year,
                'individual_month': individual_month,
                'individual_day': individual_day,
                'current_day': current_day_reduced,
                'soul': user_numbers.get('soul_number') if user_numbers else None,
                'mind': user_numbers.get('mind_number') if user_numbers else None,
                'destiny': destiny_number,
                'janma_ank': janma_ank if janma_ank else None
            }
            
            # Check if problem numbers match important numbers
            problem_numbers_list = [
                ('chpg', problem_year),
                ('chpm', problem_month),
                ('chpd', problem_day)
            ]
            
            for problem_key, problem_value in problem_numbers_list:
                if problem_value in number_to_planet:
                    problem_planet_name = number_to_planet[problem_value]
                    problem_planet_key = planet_name_map.get(problem_planet_name, problem_planet_name.lower())
                    
                    if problem_planet_key in planet_energies:
                        # Check if problem number matches any important number
                        for num_key, num_value in important_numbers_for_problems.items():
                            if num_value is None:
                                continue
                            
                            # Reduce to single digit if needed
                            num_reduced = num_value
                            if num_value > 9 and num_value not in [11, 22, 33]:
                                num_reduced = reduce_to_single_digit(num_value)
                            
                            # If problem number matches important number - energy drops significantly (but not to zero)
                            if problem_value == num_reduced:
                                # MATCH: Energy drops significantly (but not extreme) - will be normalized later
                                planet_energies[problem_planet_key] -= destiny_number * get_modifier('problem_number_match_penalty', 0.80)
            
            # MODIFIER 1: If day matches personal day - energy increases significantly (but not to 100%)
            # Check if current day number (reduced) matches individual day
            current_day_reduced_for_check = reduce_to_single_digit(current_day)
            if current_day_reduced_for_check == individual_day:
                # This day matches personal day - add significant energy boost
                if individual_day in number_to_planet:
                    planet_name = number_to_planet[individual_day]
                    planet_key = planet_name_map.get(planet_name, planet_name.lower())
                    if planet_key in planet_energies:
                        # Add significant boost (but not extreme) - will be normalized later
                        planet_energies[planet_key] += destiny_number * get_modifier('personal_day_match_bonus', 0.60)
            
            # MODIFIER 2: If personal month number matches day - add 50% energy
            # Check if individual_month matches current_day (reduced to single digit)
            current_day_reduced = reduce_to_single_digit(current_day)
            if individual_month == current_day_reduced:
                # Personal month matches day - add 50% energy
                if individual_month in number_to_planet:
                    planet_name = number_to_planet[individual_month]
                    planet_key = planet_name_map.get(planet_name, planet_name.lower())
                    if planet_key in planet_energies:
                        planet_energies[planet_key] += destiny_number * get_modifier('personal_month_match_bonus', 0.50)
            
            # ENHANCED: Day number matching logic - maximize good values, minimize bad
            # Get all important numbers for comparison (including problem numbers)
            important_numbers = {
                'individual_day': individual_day,
                'individual_month': individual_month,
                'individual_year': individual_year,
                'current_day': current_day_reduced,
                'soul': user_numbers.get('soul_number') if user_numbers else None,
                'mind': user_numbers.get('mind_number') if user_numbers else None,
                'destiny': destiny_number,
                'janma_ank': janma_ank if janma_ank else None,
                'problem_year': problem_year,
                'problem_month': problem_month,
                'problem_day': problem_day
            }
            
            # Check for matches and mismatches
            for num_key, num_value in important_numbers.items():
                if num_value is None:
                    continue
                
                # Skip problem numbers in this loop - they are handled separately
                if num_key in ['problem_year', 'problem_month', 'problem_day']:
                    continue
                
                # Reduce to single digit if needed (except for master numbers)
                num_reduced = num_value
                if num_value > 9 and num_value not in [11, 22, 33]:
                    num_reduced = reduce_to_single_digit(num_value)
                
                if num_reduced in number_to_planet:
                    planet_name = number_to_planet[num_reduced]
                    planet_key = planet_name_map.get(planet_name, planet_name.lower())
                    
                    if planet_key in planet_energies:
                        # Check if this number matches any problem number - if so, energy drops significantly
                        if num_reduced == problem_year or num_reduced == problem_month or num_reduced == problem_day:
                            # PROBLEM NUMBER MATCH: Energy drops significantly (but not extreme)
                            planet_energies[planet_key] -= destiny_number * get_modifier('problem_number_match_penalty', 0.80)
                            continue  # Skip other modifiers for this planet
                        
                        # Check for matches with current day
                        if num_reduced == current_day_reduced:
                            # MATCH: Maximum good value - add significant energy
                            planet_energies[planet_key] += destiny_number * get_modifier('current_day_match_bonus', 0.40)
                        else:
                            # Check if planets are enemies
                            planet_data = planet_relationships.get(planet_name, {})
                            ruling_planet_data = planet_relationships.get(ruling_planet, {})
                            
                            # Check if this planet is enemy of ruling planet
                            if planet_name in ruling_planet_data.get('enemies', []):
                                # ENEMY: Reduce energy significantly
                                planet_energies[planet_key] -= destiny_number * get_modifier('enemy_mismatch_penalty', 0.30)
                            # Check if this planet is friend of ruling planet
                            elif planet_name in ruling_planet_data.get('friends', []):
                                # FRIEND: Add some energy even if not exact match
                                planet_energies[planet_key] += destiny_number * get_modifier('friend_mismatch_bonus', 0.15)
                            else:
                                # NEUTRAL: Small reduction for mismatch
                                planet_energies[planet_key] -= destiny_number * get_modifier('neutral_mismatch_penalty', 0.10)
            
            # Additional check: if problem numbers match current day or other important numbers
            for problem_num in [problem_year, problem_month, problem_day]:
                if problem_num in number_to_planet:
                    problem_planet_name = number_to_planet[problem_num]
                    problem_planet_key = planet_name_map.get(problem_planet_name, problem_planet_name.lower())
                    
                    if problem_planet_key in planet_energies:
                        # Check if problem number matches current day
                        if problem_num == current_day_reduced:
                            # Problem number matches current day - energy drops significantly
                            planet_energies[problem_planet_key] -= destiny_number * get_modifier('problem_number_match_penalty', 0.80)
                        
                        # Check if problem number matches individual numbers
                        if problem_num == individual_year or problem_num == individual_month or problem_num == individual_day:
                            # Problem number matches individual number - energy drops significantly
                            planet_energies[problem_planet_key] -= destiny_number * get_modifier('problem_number_match_penalty', 0.80)
            
            # Handle Janma Ank = 22 (master number)
            if janma_ank == 22:
                # Master number 22 - special handling
                # 22 reduces to 4 (Rahu), but has special power
                rahu_key = 'rahu'
                if rahu_key in planet_energies:
                    # Master number 22 gives extra power to Rahu
                    planet_energies[rahu_key] += destiny_number * get_modifier('janma_ank_22_bonus', 0.25)
                
                # Also check if 22 matches any important numbers
                if current_day_reduced == 4:  # 22 reduces to 4
                    if rahu_key in planet_energies:
                        planet_energies[rahu_key] += destiny_number * get_modifier('janma_ank_22_match_bonus', 0.30)
            
            # Handle cyclicity - redirect energy when cycles occur
            # Check for repeating patterns in numbers
            number_sequence = [individual_year, individual_month, individual_day, current_day_reduced]
            unique_numbers = set(number_sequence)
            
            # If we have cyclicity (repeating numbers), redirect energy
            if len(unique_numbers) < len(number_sequence):
                # Cyclicity detected - redistribute energy
                repeated_numbers = [n for n in number_sequence if number_sequence.count(n) > 1]
                for repeated_num in set(repeated_numbers):
                    if repeated_num in number_to_planet:
                        planet_name = number_to_planet[repeated_num]
                        planet_key = planet_name_map.get(planet_name, planet_name.lower())
                        if planet_key in planet_energies:
                            # Increase energy for repeated numbers (cyclicity boost)
                            planet_energies[planet_key] += destiny_number * get_modifier('cyclicity_bonus', 0.20)
                            
                            # Redirect some energy from non-repeated planets
                            for other_key in planet_energies:
                                if other_key != planet_key:
                                    # Small reduction to redirect energy
                                    planet_energies[other_key] -= destiny_number * get_modifier('cyclicity_penalty', 0.05)
        except:
            pass
    
    # 5. Pythagorean Square: more digits = more energy
    if pythagorean_square:
        planet_counts = pythagorean_square.get('planet_counts', {})
        for num, count in planet_counts.items():
            if num in number_to_planet:
                planet_name = number_to_planet[num]
                planet_key = planet_name_map.get(planet_name, planet_name.lower())
                if planet_key in planet_energies:
                    # More digits = more energy (each digit adds bonus%)
                    planet_energies[planet_key] += destiny_number * get_modifier('pythagorean_digit_bonus', 0.03) * count
    
    # 6. Personal numbers (soul, mind, destiny, wisdom, ruling)
    if user_numbers:
        # Soul number - very important, add more energy
        soul_num = user_numbers.get('soul_number')
        if soul_num and soul_num in number_to_planet:
            planet_name = number_to_planet[soul_num]
            planet_key = planet_name_map.get(planet_name, planet_name.lower())
            if planet_key in planet_energies:
                planet_energies[planet_key] += destiny_number * get_modifier('soul_number_bonus', 0.08)
        
        # Mind number - important, add energy
        mind_num = user_numbers.get('mind_number')
        if mind_num and mind_num in number_to_planet:
            planet_name = number_to_planet[mind_num]
            planet_key = planet_name_map.get(planet_name, planet_name.lower())
            if planet_key in planet_energies:
                planet_energies[planet_key] += destiny_number * get_modifier('mind_number_bonus', 0.06)
        
        # Destiny number - already used as base, but can add bonus
        destiny_num = user_numbers.get('destiny_number')
        if destiny_num and destiny_num in number_to_planet:
            planet_name = number_to_planet[destiny_num]
            planet_key = planet_name_map.get(planet_name, planet_name.lower())
            if planet_key in planet_energies:
                planet_energies[planet_key] += destiny_number * get_modifier('destiny_number_bonus', 0.05)
        
        # Wisdom number - add energy
        wisdom_num = user_numbers.get('wisdom_number')
        if wisdom_num and wisdom_num in number_to_planet:
            planet_name = number_to_planet[wisdom_num]
            planet_key = planet_name_map.get(planet_name, planet_name.lower())
            if planet_key in planet_energies:
                planet_energies[planet_key] += destiny_number * get_modifier('wisdom_number_bonus', 0.04)
        
        # Ruling number - very important, add more energy
        ruling_num = user_numbers.get('ruling_number')
        if ruling_num:
            # Ruling number can be master number (11, 22), so reduce it first
            if ruling_num > 9:
                ruling_num = reduce_to_single_digit(ruling_num)
            if ruling_num in number_to_planet:
                planet_name = number_to_planet[ruling_num]
                planet_key = planet_name_map.get(planet_name, planet_name.lower())
                if planet_key in planet_energies:
                    planet_energies[planet_key] += destiny_number * get_modifier('ruling_number_bonus', 0.07)
    
    # 7. Horizontals, verticals, diagonals
    if pythagorean_square:
        # Calculate sums for horizontals, verticals, diagonals
        planet_counts = pythagorean_square.get('planet_counts', {})
        
        # Horizontals: (1-4-7), (2-5-8), (3-6-9)
        horizontal1 = planet_counts.get(1, 0) + planet_counts.get(4, 0) + planet_counts.get(7, 0)
        horizontal2 = planet_counts.get(2, 0) + planet_counts.get(5, 0) + planet_counts.get(8, 0)
        horizontal3 = planet_counts.get(3, 0) + planet_counts.get(6, 0) + planet_counts.get(9, 0)
        
        # Verticals: (1-2-3), (4-5-6), (7-8-9)
        vertical1 = planet_counts.get(1, 0) + planet_counts.get(2, 0) + planet_counts.get(3, 0)
        vertical2 = planet_counts.get(4, 0) + planet_counts.get(5, 0) + planet_counts.get(6, 0)
        vertical3 = planet_counts.get(7, 0) + planet_counts.get(8, 0) + planet_counts.get(9, 0)
        
        # Diagonals: (1-5-9), (3-5-7)
        diagonal1 = planet_counts.get(1, 0) + planet_counts.get(5, 0) + planet_counts.get(9, 0)
        diagonal2 = planet_counts.get(3, 0) + planet_counts.get(5, 0) + planet_counts.get(7, 0)
        
        # Apply modifiers based on sums for each planet in the line
        line_bonus = get_modifier('line_sum_bonus', 2.0)
        # Horizontal 1: planets 1, 4, 7
        for num in [1, 4, 7]:
            if num in number_to_planet:
                planet_name = number_to_planet[num]
                planet_key = planet_name_map.get(planet_name, planet_name.lower())
                if planet_key in planet_energies:
                    planet_energies[planet_key] += horizontal1 * line_bonus
        
        # Horizontal 2: planets 2, 5, 8
        for num in [2, 5, 8]:
            if num in number_to_planet:
                planet_name = number_to_planet[num]
                planet_key = planet_name_map.get(planet_name, planet_name.lower())
                if planet_key in planet_energies:
                    planet_energies[planet_key] += horizontal2 * line_bonus
        
        # Horizontal 3: planets 3, 6, 9
        for num in [3, 6, 9]:
            if num in number_to_planet:
                planet_name = number_to_planet[num]
                planet_key = planet_name_map.get(planet_name, planet_name.lower())
                if planet_key in planet_energies:
                    planet_energies[planet_key] += horizontal3 * line_bonus
        
        # Vertical 1: planets 1, 2, 3
        for num in [1, 2, 3]:
            if num in number_to_planet:
                planet_name = number_to_planet[num]
                planet_key = planet_name_map.get(planet_name, planet_name.lower())
                if planet_key in planet_energies:
                    planet_energies[planet_key] += vertical1 * line_bonus
        
        # Vertical 2: planets 4, 5, 6
        for num in [4, 5, 6]:
            if num in number_to_planet:
                planet_name = number_to_planet[num]
                planet_key = planet_name_map.get(planet_name, planet_name.lower())
                if planet_key in planet_energies:
                    planet_energies[planet_key] += vertical2 * line_bonus
        
        # Vertical 3: planets 7, 8, 9
        for num in [7, 8, 9]:
            if num in number_to_planet:
                planet_name = number_to_planet[num]
                planet_key = planet_name_map.get(planet_name, planet_name.lower())
                if planet_key in planet_energies:
                    planet_energies[planet_key] += vertical3 * line_bonus
        
        # Diagonal 1: planets 1, 5, 9
        for num in [1, 5, 9]:
            if num in number_to_planet:
                planet_name = number_to_planet[num]
                planet_key = planet_name_map.get(planet_name, planet_name.lower())
                if planet_key in planet_energies:
                    planet_energies[planet_key] += diagonal1 * line_bonus
        
        # Diagonal 2: planets 3, 5, 7
        for num in [3, 5, 7]:
            if num in number_to_planet:
                planet_name = number_to_planet[num]
                planet_key = planet_name_map.get(planet_name, planet_name.lower())
                if planet_key in planet_energies:
                    planet_energies[planet_key] += diagonal2 * line_bonus
    
    # 8. Name and surname
    if name_numbers:
        # Name number - add energy
        name_num = name_numbers.get('name_number') or name_numbers.get('first_name_number')
        if name_num and name_num in number_to_planet:
            planet_name = number_to_planet[name_num]
            planet_key = planet_name_map.get(planet_name, planet_name.lower())
            if planet_key in planet_energies:
                planet_energies[planet_key] += destiny_number * get_modifier('name_number_bonus', 0.04)
        
        # Surname number - add energy
        surname_num = name_numbers.get('surname_number') or name_numbers.get('last_name_number')
        if surname_num and surname_num in number_to_planet:
            planet_name = number_to_planet[surname_num]
            planet_key = planet_name_map.get(planet_name, planet_name.lower())
            if planet_key in planet_energies:
                planet_energies[planet_key] += destiny_number * get_modifier('surname_number_bonus', 0.04)
        
        # Total name number - add energy
        total_name_num = name_numbers.get('total_name_number') or name_numbers.get('full_name_number')
        if total_name_num and total_name_num in number_to_planet:
            planet_name = number_to_planet[total_name_num]
            planet_key = planet_name_map.get(planet_name, planet_name.lower())
            if planet_key in planet_energies:
                planet_energies[planet_key] += destiny_number * get_modifier('total_name_bonus', 0.05)
        
        # MODIFIER 3: Check for name/surname matches with important numbers
        # Get ruling planet number
        ruling_planet_num = None
        for num, planet in number_to_planet.items():
            if planet == ruling_planet:
                ruling_planet_num = num
                break
        
        # Get individual day and month numbers
        individual_day_num = None
        individual_month_num = None
        if birth_date:
            try:
                day, month, year = parse_birth_date(birth_date)
                current_year = date.year
                current_month = date.month
                current_day = date.day
                # Individual year = reduce(day + month + current_year)
                individual_year_calc = reduce_to_single_digit(day + month + current_year)
                # Individual month = reduce(individual_year + current_month)
                individual_month_num = reduce_to_single_digit(individual_year_calc + current_month)
                # Individual day = reduce(individual_month + current_day)
                individual_day_num = reduce_to_single_digit(individual_month_num + current_day)
            except:
                pass
        
        # Check if name number matches ruling planet, individual day, or individual month
        if name_num:
            if ruling_planet_num and name_num == ruling_planet_num:
                # Name matches ruling planet - add significant energy
                planet_key = planet_name_map.get(ruling_planet, ruling_planet.lower())
                if planet_key in planet_energies:
                    planet_energies[planet_key] += destiny_number * 0.30  # +30% energy
            if individual_day_num and name_num == individual_day_num:
                # Name matches individual day - add significant energy
                if name_num in number_to_planet:
                    planet_name = number_to_planet[name_num]
                    planet_key = planet_name_map.get(planet_name, planet_name.lower())
                    if planet_key in planet_energies:
                        planet_energies[planet_key] += destiny_number * 0.25  # +25% energy
            if individual_month_num and name_num == individual_month_num:
                # Name matches individual month - add energy
                if name_num in number_to_planet:
                    planet_name = number_to_planet[name_num]
                    planet_key = planet_name_map.get(planet_name, planet_name.lower())
                    if planet_key in planet_energies:
                        planet_energies[planet_key] += destiny_number * 0.20  # +20% energy
        
        # Check if surname number matches ruling planet, individual day, or individual month
        if surname_num:
            if ruling_planet_num and surname_num == ruling_planet_num:
                # Surname matches ruling planet - add significant energy
                planet_key = planet_name_map.get(ruling_planet, ruling_planet.lower())
                if planet_key in planet_energies:
                    planet_energies[planet_key] += destiny_number * 0.30  # +30% energy
            if individual_day_num and surname_num == individual_day_num:
                # Surname matches individual day - add significant energy
                if surname_num in number_to_planet:
                    planet_name = number_to_planet[surname_num]
                    planet_key = planet_name_map.get(planet_name, planet_name.lower())
                    if planet_key in planet_energies:
                        planet_energies[planet_key] += destiny_number * 0.25  # +25% energy
            if individual_month_num and surname_num == individual_month_num:
                # Surname matches individual month - add energy
                if surname_num in number_to_planet:
                    planet_name = number_to_planet[surname_num]
                    planet_key = planet_name_map.get(planet_name, planet_name.lower())
                    if planet_key in planet_energies:
                        planet_energies[planet_key] += destiny_number * 0.20  # +20% energy
        
        # Check if total name number matches ruling planet, individual day, or individual month
        if total_name_num:
            if ruling_planet_num and total_name_num == ruling_planet_num:
                # Total name matches ruling planet - add very significant energy
                planet_key = planet_name_map.get(ruling_planet, ruling_planet.lower())
                if planet_key in planet_energies:
                    planet_energies[planet_key] += destiny_number * 0.40  # +40% energy
            if individual_day_num and total_name_num == individual_day_num:
                # Total name matches individual day - add very significant energy
                if total_name_num in number_to_planet:
                    planet_name = number_to_planet[total_name_num]
                    planet_key = planet_name_map.get(planet_name, planet_name.lower())
                    if planet_key in planet_energies:
                        planet_energies[planet_key] += destiny_number * 0.35  # +35% energy
            if individual_month_num and total_name_num == individual_month_num:
                # Total name matches individual month - add significant energy
                if total_name_num in number_to_planet:
                    planet_name = number_to_planet[total_name_num]
                    planet_key = planet_name_map.get(planet_name, planet_name.lower())
                    if planet_key in planet_energies:
                        planet_energies[planet_key] += destiny_number * 0.30  # +30% energy
    
    # 9. Weekday indicators (maximum weight)
    if weekday_energy:
        weekday_mult = get_modifier('weekday_multiplier', 3.0)
        for planet_key, energy_value in weekday_energy.items():
            if planet_key in planet_energies:
                # Maximum weight - multiply by configured multiplier (very important factor)
                planet_energies[planet_key] += energy_value * weekday_mult
    
    # 10. Rahu kala, Buli kala, Obhit muhurta
    try:
        from vedic_time_calculations import get_sunrise_sunset, calculate_rahu_kaal, calculate_abhijit_muhurta
        if get_sunrise_sunset and calculate_rahu_kaal and calculate_abhijit_muhurta:
            try:
                sunrise, sunset = get_sunrise_sunset(city, date)
                current_time = date.replace(hour=12, minute=0, second=0, microsecond=0)  # Use noon as default
                
                # Calculate Rahu kala
                rahu_start, rahu_end = calculate_rahu_kaal(sunrise, sunset, weekday)
                in_rahu_kala = rahu_start <= current_time <= rahu_end
                
                # Calculate Abhijit muhurta (Obhit muhurta)
                abhijit_start, abhijit_end = calculate_abhijit_muhurta(sunrise, sunset)
                in_abhijit = abhijit_start <= current_time <= abhijit_end
                
                # Apply modifiers based on periods
                # Rahu kala is generally unfavorable, so reduce energy for ruling planet
                if in_rahu_kala:
                    ruling_planet_key = planet_name_map.get(ruling_planet, ruling_planet.lower())
                    if ruling_planet_key in planet_energies:
                        planet_energies[ruling_planet_key] -= destiny_number * 0.15  # -15% during Rahu kala
                
                # Abhijit muhurta is favorable, so increase energy
                if in_abhijit:
                    # Increase energy for friendly planets during Abhijit
                    for planet_name in friends:
                        planet_key = planet_name_map.get(planet_name, planet_name.lower())
                        if planet_key in planet_energies:
                            planet_energies[planet_key] += destiny_number * 0.20  # +20% during Abhijit
            except:
                pass
    except:
        pass
    
    # Anti-cyclicity function: remove cyclical patterns for each planet individually
    # This ensures each planet has its own dynamic range (0-100%) based on matches/mismatches
    anti_cyclicity_enabled = get_modifier('anti_cyclicity_enabled', True)
    if anti_cyclicity_enabled:
        import statistics
        
        # Get threshold and variation from config
        threshold = get_modifier('anti_cyclicity_threshold', 5.0)
        variation = get_modifier('anti_cyclicity_variation', 3.0)
        
        # Planet order for deterministic variation
        planet_order = ['surya', 'chandra', 'mangal', 'budha', 'guru', 'shukra', 'shani', 'rahu', 'ketu']
        variation_pattern = [0, 1, -1, 2, -2, 1.5, -1.5, 0.5, -0.5]  # Variation multipliers
        
        # Calculate standard deviation of all energies
        energy_values = list(planet_energies.values())
        if len(energy_values) > 1:
            try:
                std_dev = statistics.stdev(energy_values)
            except:
                std_dev = 0
            
            # If standard deviation is too low (all planets too similar), add variation to each planet
            if std_dev < threshold:
                for i, planet_key in enumerate(planet_order):
                    if planet_key in planet_energies:
                        # Add deterministic variation based on planet position
                        variation_amount = variation * variation_pattern[i % len(variation_pattern)]
                        planet_energies[planet_key] += variation_amount
        
        # Apply anti-cyclicity for each planet individually
        # This ensures each planet can reach 0% or 100% based on matches/mismatches
        for i, planet_key in enumerate(planet_order):
            if planet_key not in planet_energies:
                continue
            
            current_energy = planet_energies[planet_key]
            
            # Calculate variation for this specific planet based on its position
            planet_variation = variation * variation_pattern[i % len(variation_pattern)]
            
            # Add date-based variation to create unique pattern for each planet
            day_variation = (date.day % 9) * 0.5 * (1 if i % 2 == 0 else -1)
            month_variation = (date.month % 7) * 0.3 * (1 if i % 3 == 0 else -1)
            
            # Combine variations
            total_variation = planet_variation + day_variation + month_variation
            
            # Apply variation to break cyclicity for this planet
            planet_energies[planet_key] = current_energy + total_variation
    
    # Normalize all values to 0-100 range using clamp function
    # Allow values to reach exactly 0% and 100% based on matches/mismatches
    # clamp(0, 100, x) = min(100, max(0, x))
    result = {}
    for planet_key, energy in planet_energies.items():
        # Apply clamp function: min(100, max(0, energy))
        # This allows energies to reach 0% and 100% when there are strong matches/mismatches
        clamped_energy = min(100, max(0, energy))
        result[planet_key] = int(clamped_energy)
    
    return result