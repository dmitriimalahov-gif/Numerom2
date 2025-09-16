import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Label } from './ui/label';

const AleksandrovPythagorean = () => {
  const [birthDate, setBirthDate] = useState('');
  const [calculation, setCalculation] = useState(null);

  // Colors for numbers 1-9 according to Aleksandrov method
  const numberColors = {
    1: '#E74C3C', // Red - Leadership, Sun
    2: '#A8A8A8', // Gray - Cooperation, Moon  
    3: '#FF8C00', // Orange - Creativity, Jupiter
    4: '#A0764A', // Brown - Stability, Uranus
    5: '#7FB069', // Green - Freedom, Mercury
    6: '#FFB6C1', // Pink - Care, Venus
    7: '#708090', // Slate Gray - Mystery, Neptune
    8: '#2E4BC6', // Blue - Material power, Saturn
    9: '#9370DB'  // Purple - Wisdom, Mars
  };

  const calculateAleksandrovSquare = () => {
    if (!birthDate.match(/^\d{2}\.\d{2}\.\d{4}$/)) {
      alert('Введите дату в формате ДД.ММ.ГГГГ');
      return;
    }

    const [day, month, year] = birthDate.split('.');
    const birthDigits = (day + month + year).split('').map(Number).filter(d => d !== 0);
    
    // First working number (sum of all birth digits)
    let firstWorkingNumber = birthDigits.reduce((a, b) => a + b, 0);
    
    // Second working number (sum of digits of first working number)
    let secondWorkingNumber = firstWorkingNumber.toString().split('').map(Number).reduce((a, b) => a + b, 0);
    
    // Third working number (first - 2 * first digit of birth date)
    const firstDigit = parseInt(day.charAt(0));
    let thirdWorkingNumber = firstWorkingNumber - (2 * firstDigit);
    
    // Fourth working number (sum of digits of third working number)
    let fourthWorkingNumber = Math.abs(thirdWorkingNumber).toString().split('').map(Number).reduce((a, b) => a + b, 0);

    // All digits for analysis
    const allDigits = [
      ...birthDigits,
      ...firstWorkingNumber.toString().split('').map(Number),
      ...secondWorkingNumber.toString().split('').map(Number),
      ...Math.abs(thirdWorkingNumber).toString().split('').map(Number),
      ...fourthWorkingNumber.toString().split('').map(Number)
    ];

    // Count occurrences of each digit (1-9)
    const digitCounts = {};
    for (let i = 1; i <= 9; i++) {
      digitCounts[i] = allDigits.filter(digit => digit === i).length;
    }

    // Calculate character lines (horizontals)
    const character1 = digitCounts[1] + digitCounts[2] + digitCounts[3]; // Self-esteem line
    const character2 = digitCounts[4] + digitCounts[5] + digitCounts[6]; // Family line
    const character3 = digitCounts[7] + digitCounts[8] + digitCounts[9]; // Habits line

    // Calculate stability lines (verticals)  
    const stability1 = digitCounts[1] + digitCounts[4] + digitCounts[7]; // Self-determination
    const stability2 = digitCounts[2] + digitCounts[5] + digitCounts[8]; // Family stability
    const stability3 = digitCounts[3] + digitCounts[6] + digitCounts[9]; // Talent stability

    // Calculate spiritual lines (diagonals)
    const spiritual1 = digitCounts[1] + digitCounts[5] + digitCounts[9]; // Spirit ascending
    const spiritual2 = digitCounts[3] + digitCounts[5] + digitCounts[7]; // Passion line

    // Calculate basic numbers according to Aleksandrov
    const soulNumber = parseInt(day) > 9 ? 
      parseInt(day).toString().split('').map(Number).reduce((a, b) => a + b) : 
      parseInt(day);
      
    const mindNumber = parseInt(month) > 9 ? 
      parseInt(month).toString().split('').map(Number).reduce((a, b) => a + b) : 
      parseInt(month);
      
    const destinyNumber = secondWorkingNumber;
    const mindNumber2 = fourthWorkingNumber;
    const wisdomNumber = Math.abs(destinyNumber - mindNumber2);
    const rulingNumber = parseInt(day + month);

    setCalculation({
      soulNumber,
      mindNumber, 
      destinyNumber,
      mindNumber2,
      wisdomNumber,
      rulingNumber,
      workingNumbers: {
        first: firstWorkingNumber,
        second: secondWorkingNumber,
        third: thirdWorkingNumber,
        fourth: fourthWorkingNumber
      },
      digitCounts,
      characteristics: {
        character: [character1, character2, character3],
        stability: [stability1, stability2, stability3],
        spiritual: [spiritual1, spiritual2]
      }
    });
  };

  const SquareCell = ({ number, count }) => (
    <div 
      className="w-16 h-16 flex items-center justify-center text-white font-bold text-xl rounded-lg shadow-lg border-2"
      style={{ 
        backgroundColor: count > 0 ? numberColors[number] : '#333333',
        borderColor: count > 0 ? numberColors[number] : '#666666',
        opacity: count > 0 ? 1 : 0.4
      }}
    >
      {count > 0 ? '1'.repeat(count) : number}
    </div>
  );

  const InfoCell = ({ label, value, color = '#4B5563' }) => (
    <div className="flex items-center justify-between p-3 text-white rounded-lg shadow-lg" style={{ backgroundColor: color }}>
      <span className="font-semibold text-sm">{label}</span>
      <span className="text-xl font-bold">{value}</span>
    </div>
  );

  return (
    <div className="space-y-6">
      <Card className="border-emerald-200 shadow-lg">
        <CardHeader className="bg-gradient-to-r from-emerald-100 to-teal-100">
          <CardTitle className="text-emerald-800">Квадрат Пифагора по методу Александрова</CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="space-y-4 mb-6">
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
            <Button 
              onClick={calculateAleksandrovSquare}
              disabled={!birthDate.trim()}
              className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700"
            >
              Рассчитать по методу Александрова
            </Button>
          </div>

          {calculation && (
            <div className="bg-black p-6 rounded-lg">
              <div className="flex justify-center space-x-8">
                {/* Left column - Main numbers */}
                <div className="space-y-3">
                  <InfoCell label="Ч/Д" value={calculation.soulNumber} color="#E74C3C" />
                  <InfoCell label="Ч/У" value={calculation.mindNumber} color="#A8A8A8" />
                  <InfoCell label="Ч/С" value={calculation.destinyNumber} color="#FF8C00" />
                </div>

                {/* Center - Aleksandrov Square */}
                <div className="flex flex-col items-center space-y-4">
                  {/* Working numbers */}
                  <div className="grid grid-cols-4 gap-2 mb-2">
                    <InfoCell label="1РЧ" value={calculation.workingNumbers.first} color="#4B5563" />
                    <InfoCell label="2РЧ" value={calculation.workingNumbers.second} color="#4B5563" />
                    <InfoCell label="3РЧ" value={calculation.workingNumbers.third} color="#4B5563" />
                    <InfoCell label="4РЧ" value={calculation.workingNumbers.fourth} color="#4B5563" />
                  </div>

                  {/* Square grid */}
                  <div className="grid grid-cols-3 gap-2">
                    <SquareCell number={1} count={calculation.digitCounts[1]} />
                    <SquareCell number={2} count={calculation.digitCounts[2]} />
                    <SquareCell number={3} count={calculation.digitCounts[3]} />
                    <SquareCell number={4} count={calculation.digitCounts[4]} />
                    <SquareCell number={5} count={calculation.digitCounts[5]} />
                    <SquareCell number={6} count={calculation.digitCounts[6]} />
                    <SquareCell number={7} count={calculation.digitCounts[7]} />
                    <SquareCell number={8} count={calculation.digitCounts[8]} />
                    <SquareCell number={9} count={calculation.digitCounts[9]} />
                  </div>
                  
                  {/* Stability (bottom row) */}
                  <div className="flex space-x-2">
                    {calculation.characteristics.stability.map((stability, index) => (
                      <div 
                        key={index}
                        className="w-16 h-12 flex items-center justify-center bg-blue-600 text-white font-bold rounded-lg"
                      >
                        {stability}
                      </div>
                    ))}
                  </div>

                  {/* Additional numbers */}
                  <div className="flex space-x-4">
                    <InfoCell label="Ч/У*" value={calculation.mindNumber2} color="#9370DB" />
                    <InfoCell label="Ч/М" value={calculation.wisdomNumber} color="#7FB069" />
                    <InfoCell label="П/Ч" value={calculation.rulingNumber} color="#2E4BC6" />
                  </div>
                </div>

                {/* Right column - Character lines */}
                <div className="space-y-3">
                  {calculation.characteristics.character.map((char, index) => (
                    <div 
                      key={index}
                      className="w-16 h-16 flex items-center justify-center bg-red-600 text-white font-bold text-xl rounded-lg"
                    >
                      {char}
                    </div>
                  ))}
                  
                  {/* Spiritual lines */}
                  <div className="space-y-2 mt-4">
                    {calculation.characteristics.spiritual.map((spiritual, index) => (
                      <div 
                        key={index}
                        className="w-16 h-12 flex items-center justify-center bg-purple-600 text-white font-bold rounded-lg"
                      >
                        {spiritual}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Aleksandrov interpretation */}
              <div className="mt-8 space-y-4 text-white">
                <h3 className="text-xl font-bold text-center">Анализ по методу Александрова</h3>
                <div className="grid md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <h4 className="font-semibold mb-2 text-red-400">Линии характера:</h4>
                    <p>1-я строка ({calculation.characteristics.character[0]}): самооценка</p>
                    <p>2-я строка ({calculation.characteristics.character[1]}): семья, быт</p>
                    <p>3-я строка ({calculation.characteristics.character[2]}): привычки, стабильность</p>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2 text-blue-400">Линии стабильности:</h4>
                    <p>1-й столбец ({calculation.characteristics.stability[0]}): самоопределение</p>
                    <p>2-й столбец ({calculation.characteristics.stability[1]}): быт, семья</p>
                    <p>3-й столбец ({calculation.characteristics.stability[2]}): таланты</p>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2 text-purple-400">Духовные линии:</h4>
                    <p>Восходящая ({calculation.characteristics.spiritual[0]}): духовность</p>
                    <p>Нисходящая ({calculation.characteristics.spiritual[1]}): плотские желания</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AleksandrovPythagorean;