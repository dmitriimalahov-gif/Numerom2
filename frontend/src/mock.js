// Mock data for Vedic Numerology Calculator

export const mockPersonalNumbers = {
  getLifePathNumber: (dateString) => {
    // Mock calculation - in real app, this would be proper vedic numerology calculation
    const numbers = dateString.replace(/-/g, '').split('').map(Number);
    let sum = numbers.reduce((a, b) => a + b, 0);
    while (sum > 9 && sum !== 11 && sum !== 22 && sum !== 33) {
      sum = sum.toString().split('').map(Number).reduce((a, b) => a + b, 0);
    }
    return sum;
  },
  
  getDestinyNumber: (dateString) => {
    // Mock calculation for destiny number
    const day = parseInt(dateString.split('-')[2]);
    let sum = day;
    while (sum > 9 && sum !== 11 && sum !== 22 && sum !== 33) {
      sum = sum.toString().split('').map(Number).reduce((a, b) => a + b, 0);
    }
    return sum;
  },
  
  getSoulNumber: (dateString) => {
    // Mock calculation for soul number (based on birth day)
    const day = parseInt(dateString.split('-')[2]);
    return day > 9 ? day.toString().split('').map(Number).reduce((a, b) => a + b, 0) : day;
  }
};

export const mockNameNumber = {
  calculateNameNumber: (name) => {
    // Mock name number calculation using simple letter values
    const letterValues = {
      'а': 1, 'б': 2, 'в': 3, 'г': 4, 'д': 5, 'е': 6, 'ё': 6, 'ж': 7, 'з': 8, 'и': 9,
      'й': 1, 'к': 2, 'л': 3, 'м': 4, 'н': 5, 'о': 6, 'п': 7, 'р': 8, 'с': 9, 'т': 1,
      'у': 2, 'ф': 3, 'х': 4, 'ц': 5, 'ч': 6, 'ш': 7, 'щ': 8, 'ъ': 9, 'ы': 1, 'ь': 2,
      'э': 3, 'ю': 4, 'я': 5
    };
    
    const nameSum = name.toLowerCase().split('').reduce((sum, letter) => {
      return sum + (letterValues[letter] || 0);
    }, 0);
    
    let result = nameSum;
    while (result > 9 && result !== 11 && result !== 22 && result !== 33) {
      result = result.toString().split('').map(Number).reduce((a, b) => a + b, 0);
    }
    return result;
  }
};

export const mockCompatibility = {
  calculateCompatibility: (number1, number2) => {
    // Mock compatibility calculation
    const diff = Math.abs(number1 - number2);
    if (diff === 0) return { score: 100, level: 'Идеальная' };
    if (diff <= 2) return { score: 85, level: 'Очень хорошая' };
    if (diff <= 4) return { score: 70, level: 'Хорошая' };
    if (diff <= 6) return { score: 55, level: 'Удовлетворительная' };
    return { score: 40, level: 'Сложная' };
  }
};

// Vedic Time Periods Data
export const mockVedicTimes = {
  // Time periods for each day of the week (in minutes from sunrise)
  timePeriodsData: {
    'воскресенье': { // Sunday
      rahuKala: { start: 16, end: 56 },
      abhijitMuhurta: { start: 12, end: 39 },
      gulikaKala: { start: 13, end: 10 },
      yamaghanda: { start: 9, end: 24 }
    },
    'понедельник': { // Monday
      rahuKala: { start: 7, end: 8 },
      abhijitMuhurta: { start: 12, end: 39 },
      gulikaKala: { start: 22, end: 23 },
      yamaghanda: { start: 10, end: 11 }
    },
    'вторник': { // Tuesday
      rahuKala: { start: 15, end: 16 },
      abhijitMuhurta: { start: 12, end: 39 },
      gulikaKala: { start: 18, end: 19 },
      yamaghanda: { start: 11, end: 12 }
    },
    'среда': { // Wednesday
      rahuKala: { start: 12, end: 13 },
      abhijitMuhurta: { start: 12, end: 39 },
      gulikaKala: { start: 14, end: 15 },
      yamaghanda: { start: 12, end: 13 }
    },
    'четверг': { // Thursday
      rahuKala: { start: 13, end: 14 },
      abhijitMuhurta: { start: 12, end: 39 },
      gulikaKala: { start: 15, end: 16 },
      yamaghanda: { start: 13, end: 14 }
    },
    'пятница': { // Friday
      rahuKala: { start: 10, end: 11 },
      abhijitMuhurta: { start: 12, end: 39 },
      gulikaKala: { start: 21, end: 22 },
      yamaghanda: { start: 14, end: 15 }
    },
    'суббота': { // Saturday
      rahuKala: { start: 9, end: 10 },
      abhijitMuhurta: { start: 12, end: 39 },
      gulikaKala: { start: 6, end: 7 },
      yamaghanda: { start: 15, end: 16 }
    }
  },
  
  calculateVedicTimes: (date) => {
    const dayNames = ['воскресенье', 'понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота'];
    const dayOfWeek = dayNames[new Date(date).getDay()];
    
    return {
      dayOfWeek,
      periods: mockVedicTimes.timePeriodsData[dayOfWeek] || mockVedicTimes.timePeriodsData['понедельник']
    };
  }
};

export const numberDescriptions = {
  1: {
    title: "Лидер",
    description: "Люди числа 1 - прирожденные лидеры. Они независимы, амбициозны и всегда стремятся быть первыми.",
    traits: ["Лидерство", "Независимость", "Амбициозность", "Инициативность"],
    recommendations: "Развивайте терпение и учитесь работать в команде. Избегайте чрезмерного эгоизма.",
    color: "#E74C3C" // Red
  },
  2: {
    title: "Дипломат", 
    description: "Число 2 символизирует сотрудничество, гармонию и дипломатию. Эти люди миротворцы по природе.",
    traits: ["Сотрудничество", "Дипломатия", "Чувствительность", "Гармония"],
    recommendations: "Укрепляйте уверенность в себе. Не позволяйте другим принимать решения за вас.",
    color: "#A8A8A8" // Gray
  },
  3: {
    title: "Творец",
    description: "Люди числа 3 обладают ярким творческим потенциалом и отличными коммуникативными способностями.",
    traits: ["Творчество", "Коммуникабельность", "Оптимизм", "Вдохновение"],
    recommendations: "Сосредоточьтесь на развитии дисциплины и завершении начатых проектов.",
    color: "#FF8C00" // Orange
  },
  4: {
    title: "Строитель",
    description: "Число 4 представляет стабильность, практичность и методичность в работе.",
    traits: ["Стабильность", "Практичность", "Надежность", "Организованность"],
    recommendations: "Учитесь быть более гибкими и открытыми к изменениям.",
    color: "#A0764A" // Brown
  },
  5: {
    title: "Свободный дух",
    description: "Люди числа 5 любят свободу, приключения и постоянные изменения в жизни.",
    traits: ["Свобода", "Адаптивность", "Любознательность", "Энергичность"],
    recommendations: "Развивайте постоянство и учитесь принимать обязательства.",
    color: "#7FB069" // Mint Green
  },
  6: {
    title: "Заботливый",
    description: "Число 6 символизирует заботу, ответственность и стремление помогать другим.",
    traits: ["Забота", "Ответственность", "Сострадание", "Семейность"],
    recommendations: "Не забывайте о своих потребностях, заботясь о других.",
    color: "#FFB6C1" // Light Pink
  },
  7: {
    title: "Мистик",
    description: "Люди числа 7 - глубокие мыслители, стремящиеся к знаниям и духовному развитию.",
    traits: ["Интуиция", "Анализ", "Духовность", "Мудрость"],
    recommendations: "Развивайте социальные навыки и учитесь доверять другим.",
    color: "#708090" // Slate Gray
  },
  8: {
    title: "Материалист",
    description: "Число 8 представляет амбиции в материальной сфере, власть и деловую хватку.",
    traits: ["Амбиции", "Материальный успех", "Власть", "Организация"],
    recommendations: "Помните о важности духовных ценностей и отношений с людьми.",
    color: "#2E4BC6" // Blue
  },
  9: {
    title: "Гуманист",
    description: "Люди числа 9 - альтруисты, стремящиеся сделать мир лучше для всех.",
    traits: ["Альтруизм", "Сострадание", "Мудрость", "Универсальность"],
    recommendations: "Учитесь принимать несовершенство мира и работать с практическими ограничениями.",
    color: "#E74C3C" // Red
  }
};

export const vedicTimeDescriptions = {
  rahuKala: {
    title: "Раху Кала",
    description: "Неблагоприятный период, управляемый теневой планетой Раху. Не рекомендуется начинать новые дела.",
    color: "#FF6B6B"
  },
  abhijitMuhurta: {
    title: "Абхиджит Мухурта",
    description: "Самый благоприятный период дня для любых начинаний и важных дел.",
    color: "#51C878"
  },
  gulikaKala: {
    title: "Гулика Кала", 
    description: "Период Гулики, неблагоприятен для новых начинаний, но хорош для завершения дел.",
    color: "#D2691E"
  },
  yamaghanda: {
    title: "Ямаганда",
    description: "Период Ямы, следует избегать важных решений и путешествий.",
    color: "#9370DB"
  }
};