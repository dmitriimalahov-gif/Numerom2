import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Label } from './ui/label';

const VedicNumerologyCalculator = () => {
  const [birthDate, setBirthDate] = useState('');
  const [currentDate, setCurrentDate] = useState('');
  const [calculation, setCalculation] = useState(null);

  // Vedic planets colors and positions - lime green theme
  const planetData = {
    1: { name: 'Сурья', planet: 'Солнце', color: '#84CC16', position: { row: 0, col: 0 } },
    2: { name: 'Чандра', planet: 'Луна', color: '#A3E635', position: { row: 1, col: 0 } },
    3: { name: 'Гуру', planet: 'Юпитер', color: '#BEF264', position: { row: 2, col: 0 } },
    4: { name: 'Раху', planet: 'Раху', color: '#65A30D', position: { row: 0, col: 1 } },
    5: { name: 'Буддхи', planet: 'Меркурий', color: '#7FB069', position: { row: 1, col: 1 } }, // Main center color
    6: { name: 'Шукра', planet: 'Венера', color: '#BEF264', position: { row: 2, col: 1 } },
    7: { name: 'Кету', planet: 'Кету', color: '#84CC16', position: { row: 0, col: 2 } },
    8: { name: 'Шани', planet: 'Сатурн', color: '#A3E635', position: { row: 1, col: 2 } },
    9: { name: 'Мангал', planet: 'Марс', color: '#BEF264', position: { row: 2, col: 2 } }
  };

  const calculateVedicNumerology = () => {
    if (!birthDate.match(/^\d{2}\.\d{2}\.\d{4}$/)) {
      alert('Введите дату рождения в формате ДД.ММ.ГГГГ');
      return;
    }
    
    if (!currentDate.match(/^\d{2}\.\d{2}\.\d{4}$/)) {
      alert('Введите текущую дату в формате ДД.ММ.ГГГГ');
      return;
    }

    const [bDay, bMonth, bYear] = birthDate.split('.').map(Number);
    const [cDay, cMonth, cYear] = currentDate.split('.').map(Number);
    
    // Basic calculations according to Aleksandrov method
    const birthDigits = birthDate.replace(/\./g, '').split('').map(Number).filter(d => d !== 0);
    
    // Working numbers
    const firstWorkingNumber = birthDigits.reduce((a, b) => a + b, 0);
    const secondWorkingNumber = firstWorkingNumber.toString().split('').map(Number).reduce((a, b) => a + b, 0);
    const firstDigit = parseInt(birthDate.charAt(0));
    const thirdWorkingNumber = firstWorkingNumber - (2 * firstDigit);
    const fourthWorkingNumber = Math.abs(thirdWorkingNumber).toString().split('').map(Number).reduce((a, b) => a + b, 0);

    // All digits for square
    const allDigits = [
      ...birthDigits,
      ...firstWorkingNumber.toString().split('').map(Number),
      ...secondWorkingNumber.toString().split('').map(Number),
      ...Math.abs(thirdWorkingNumber).toString().split('').map(Number),
      ...fourthWorkingNumber.toString().split('').map(Number)
    ];

    // Count planetary energies (digits 1-9)
    const planetCounts = {};
    for (let i = 1; i <= 9; i++) {
      planetCounts[i] = allDigits.filter(digit => digit === i).length;
    }

    // Main numbers
    const soulNumber = bDay > 9 ? bDay.toString().split('').map(Number).reduce((a, b) => a + b) : bDay;
    const mindNumber = bMonth > 9 ? bMonth.toString().split('').map(Number).reduce((a, b) => a + b) : bMonth;
    const destinyNumber = secondWorkingNumber;
    const mindNumber2 = fourthWorkingNumber;
    const wisdomNumber = Math.abs(destinyNumber - mindNumber2);
    
    // К/П - Код жизненного пути (Life Path Code)
    const lifePathCode = (soulNumber + mindNumber + destinyNumber) % 9 || 9;
    
    // ПЧ - Правящее число (Ruling Number) - highlighted
    const rulingNumber = parseInt(bDay.toString() + bMonth.toString());
    
    // Individual year, month, day numbers
    const yearSum = cYear.toString().split('').map(Number).reduce((a, b) => a + b);
    const individualYearNumber = (bDay + bMonth + yearSum) % 9 || 9; // ЧИГ
    const individualMonthNumber = (individualYearNumber + cMonth) % 9 || 9; // ЧИМ  
    const individualDayNumber = (individualMonthNumber + cDay) % 9 || 9; // ЧИД
    
    // Problem numbers
    const yearProblemNumber = (individualYearNumber + 4) % 9 || 9; // ПИГ
    const monthProblemNumber = (individualMonthNumber + 4) % 9 || 9; // ПИМ
    const dayProblemNumber = (individualDayNumber + 4) % 9 || 9; // ПИД
    const problemNumber = (soulNumber + destinyNumber + 4) % 9 || 9; // ЧП

    // Planet strengths (simplified calculation)
    const planetStrengths = {};
    for (let i = 1; i <= 9; i++) {
      planetStrengths[i] = Math.max(1, Math.min(10, planetCounts[i] * 2 + (i === soulNumber ? 3 : 0)));
    }

    // Character lines (horizontals)
    const character1 = planetCounts[1] + planetCounts[4] + planetCounts[7]; // Top row
    const character2 = planetCounts[2] + planetCounts[5] + planetCounts[8]; // Middle row
    const character3 = planetCounts[3] + planetCounts[6] + planetCounts[9]; // Bottom row

    // Stability lines (verticals)
    const stability1 = planetCounts[1] + planetCounts[2] + planetCounts[3]; // Left column
    const stability2 = planetCounts[4] + planetCounts[5] + planetCounts[6]; // Middle column
    const stability3 = planetCounts[7] + planetCounts[8] + planetCounts[9]; // Right column

    // Spiritual lines (diagonals)
    const spiritual1 = planetCounts[1] + planetCounts[5] + planetCounts[9]; // Main diagonal
    const spiritual2 = planetCounts[3] + planetCounts[5] + planetCounts[7]; // Anti-diagonal

    setCalculation({
      // Main numbers
      soulNumber,
      mindNumber,
      destinyNumber,
      mindNumber2,
      wisdomNumber,
      lifePathCode,
      rulingNumber,
      problemNumber,
      
      // Individual numbers
      individualYearNumber,
      individualMonthNumber,
      individualDayNumber,
      yearProblemNumber,
      monthProblemNumber,
      dayProblemNumber,
      
      // Planet data
      planetCounts,
      planetStrengths,
      
      // Lines
      characteristics: {
        character: [character1, character2, character3],
        stability: [stability1, stability2, stability3],
        spiritual: [spiritual1, spiritual2]
      },
      
      // Working numbers
      workingNumbers: {
        first: firstWorkingNumber,
        second: secondWorkingNumber,
        third: thirdWorkingNumber,
        fourth: fourthWorkingNumber
      }
    });
  };

  const PlanetCell = ({ number, count, strength }) => (
    <div className="flex flex-col items-center">
      <div 
        className="w-16 h-16 flex flex-col items-center justify-center text-white font-bold rounded-lg shadow-lg border-2 relative"
        style={{ 
          backgroundColor: count > 0 ? planetData[number].color : '#374151',
          borderColor: count > 0 ? planetData[number].color : '#6B7280',
          opacity: count > 0 ? 1 : 0.4
        }}
      >
        <div className="text-lg">{number}</div>
        <div className="text-xs">{count > 0 ? '●'.repeat(Math.min(count, 5)) : ''}</div>
      </div>
      <div className="text-xs mt-1 text-center">
        <div className="font-semibold" style={{ color: planetData[number].color }}>
          {planetData[number].name}
        </div>
        <div className="text-gray-600">{planetData[number].planet}</div>
        <div className="text-xs font-bold">Сила: {strength}</div>
      </div>
    </div>
  );

  const InfoCell = ({ label, value, highlighted = false }) => (
    <div 
      className={`flex items-center justify-between p-3 text-white rounded-lg shadow-lg ${
        highlighted ? 'ring-4 ring-yellow-400 ring-offset-2' : ''
      }`}
      style={{ backgroundColor: highlighted ? '#7FB069' : '#65A30D' }}
    >
      <span className="font-semibold text-sm">{label}</span>
      <span className={`text-xl font-bold ${highlighted ? 'text-yellow-100' : ''}`}>{value}</span>
    </div>
  );

  return (
    <div className="space-y-6">
      <Card className="border-lime-300 shadow-lg">
        <CardHeader style={{ background: 'linear-gradient(to right, #D9F99D, #BEF264)' }}>
          <CardTitle className="text-lime-800">Ведическая нумерология по методу Александрова</CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid md:grid-cols-2 gap-4 mb-6">
            <div>
              <Label htmlFor="birthDate">Дата рождения (ДД.ММ.ГГГГ)</Label>
              <Input
                id="birthDate"
                value={birthDate}
                onChange={(e) => setBirthDate(e.target.value)}
                placeholder="10.01.1982"
                className="mt-2"
              />
            </div>
            <div>
              <Label htmlFor="currentDate">Текущая дата (ДД.ММ.ГГГГ)</Label>
              <Input
                id="currentDate"
                value={currentDate}
                onChange={(e) => setCurrentDate(e.target.value)}
                placeholder="17.08.2025"
                className="mt-2"
              />
            </div>
          </div>
          <Button 
            onClick={calculateVedicNumerology}
            disabled={!birthDate.trim() || !currentDate.trim()}
            className="w-full"
            style={{ background: 'linear-gradient(to right, #65A30D, #7FB069)' }}
          >
            Рассчитать ведическую нумерологию
          </Button>
        </CardContent>
      </Card>

      {calculation && (
        <div className="bg-black p-6 rounded-lg">
          <div className="grid lg:grid-cols-3 gap-8">
            
            {/* Left column - Main numbers */}
            <div className="space-y-3">
              <InfoCell label="Ч/Д" value={calculation.soulNumber} />
              <InfoCell label="Ч/У" value={calculation.mindNumber} />
              <InfoCell label="Ч/С" value={calculation.destinyNumber} />
              <InfoCell label="К/П" value={calculation.lifePathCode} />
              <InfoCell label="ПЧ" value={calculation.rulingNumber} highlighted={true} />
              <InfoCell label="ЧП" value={calculation.problemNumber} />
              
              {/* Individual numbers */}
              <div className="pt-4 space-y-2">
                <InfoCell label="ЧИГ" value={calculation.individualYearNumber} />
                <InfoCell label="ЧИМ" value={calculation.individualMonthNumber} />
                <InfoCell label="ЧИД" value={calculation.individualDayNumber} />
              </div>
              
              {/* Problem numbers */}
              <div className="pt-4 space-y-2">
                <InfoCell label="ПИГ" value={calculation.yearProblemNumber} />
                <InfoCell label="ПИМ" value={calculation.monthProblemNumber} />
                <InfoCell label="ПИД" value={calculation.dayProblemNumber} />
              </div>
            </div>

            {/* Center - Vedic Square */}
            <div className="flex flex-col items-center space-y-4">
              <h3 className="text-white font-bold text-lg">Ведический квадрат планет</h3>
              
              {/* Working numbers */}
              <div className="grid grid-cols-4 gap-2 mb-4">
                <InfoCell label="1РЧ" value={calculation.workingNumbers.first} />
                <InfoCell label="2РЧ" value={calculation.workingNumbers.second} />
                <InfoCell label="3РЧ" value={calculation.workingNumbers.third} />
                <InfoCell label="4РЧ" value={calculation.workingNumbers.fourth} />
              </div>

              {/* Planet square in vedic order */}
              <div className="grid grid-cols-3 gap-3">
                <PlanetCell 
                  number={1} 
                  count={calculation.planetCounts[1]} 
                  strength={calculation.planetStrengths[1]}
                />
                <PlanetCell 
                  number={4} 
                  count={calculation.planetCounts[4]} 
                  strength={calculation.planetStrengths[4]}
                />
                <PlanetCell 
                  number={7} 
                  count={calculation.planetCounts[7]} 
                  strength={calculation.planetStrengths[7]}
                />
                
                <PlanetCell 
                  number={2} 
                  count={calculation.planetCounts[2]} 
                  strength={calculation.planetStrengths[2]}
                />
                <PlanetCell 
                  number={5} 
                  count={calculation.planetCounts[5]} 
                  strength={calculation.planetStrengths[5]}
                />
                <PlanetCell 
                  number={8} 
                  count={calculation.planetCounts[8]} 
                  strength={calculation.planetStrengths[8]}
                />
                
                <PlanetCell 
                  number={3} 
                  count={calculation.planetCounts[3]} 
                  strength={calculation.planetStrengths[3]}
                />
                <PlanetCell 
                  number={6} 
                  count={calculation.planetCounts[6]} 
                  strength={calculation.planetStrengths[6]}
                />
                <PlanetCell 
                  number={9} 
                  count={calculation.planetCounts[9]} 
                  strength={calculation.planetStrengths[9]}
                />
              </div>

              {/* Stability (verticals) */}
              <div className="flex space-x-4">
                <InfoCell label="Стаб.1" value={calculation.characteristics.stability[0]} />
                <InfoCell label="Стаб.2" value={calculation.characteristics.stability[1]} />
                <InfoCell label="Стаб.3" value={calculation.characteristics.stability[2]} />
              </div>
            </div>

            {/* Right column - Character & Spiritual */}
            <div className="space-y-3">
              <h4 className="text-lime-400 font-semibold">Линии характера:</h4>
              {calculation.characteristics.character.map((char, index) => (
                <InfoCell key={index} label={`Хар.${index + 1}`} value={char} />
              ))}
              
              <h4 className="text-lime-400 font-semibold pt-4">Духовные линии:</h4>
              {calculation.characteristics.spiritual.map((spiritual, index) => (
                <InfoCell key={index} label={`Дух.${index + 1}`} value={spiritual} />
              ))}
              
              <div className="pt-4">
                <InfoCell label="Ч/У*" value={calculation.mindNumber2} />
                <div className="mt-2">
                  <InfoCell label="Ч/М" value={calculation.wisdomNumber} />
                </div>
              </div>
            </div>
          </div>

          {/* Interpretation section */}
          <div className="mt-8 p-6 bg-lime-900 bg-opacity-30 rounded-lg">
            <h3 className="text-lime-400 font-bold text-xl mb-4 text-center">Ведическая трактовка</h3>
            <div className="grid md:grid-cols-3 gap-6 text-lime-100 text-sm">
              <div>
                <h4 className="font-semibold mb-3 text-lime-300">Основные числа:</h4>
                <p><strong>ПЧ ({calculation.rulingNumber}):</strong> Ваше правящее число - ключ к пониманию жизненного пути</p>
                <p><strong>К/П ({calculation.lifePathCode}):</strong> Код жизненного пути показывает основную карму</p>
                <p><strong>ЧП ({calculation.problemNumber}):</strong> Число проблемы указывает на кармические задачи</p>
              </div>
              <div>
                <h4 className="font-semibold mb-3 text-lime-300">Индивидуальные циклы:</h4>
                <p><strong>ЧИГ ({calculation.individualYearNumber}):</strong> Энергия текущего года</p>
                <p><strong>ЧИМ ({calculation.individualMonthNumber}):</strong> Влияние месяца</p>
                <p><strong>ЧИД ({calculation.individualDayNumber}):</strong> Энергия дня</p>
              </div>
              <div>
                <h4 className="font-semibold mb-3 text-lime-300">Проблемные циклы:</h4>
                <p><strong>ПИГ ({calculation.yearProblemNumber}):</strong> Вызовы года</p>
                <p><strong>ПИМ ({calculation.monthProblemNumber}):</strong> Трудности месяца</p>
                <p><strong>ПИД ({calculation.dayProblemNumber}):</strong> Препятствия дня</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VedicNumerologyCalculator;