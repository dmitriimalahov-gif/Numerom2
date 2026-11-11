// Arithmetic extracted unchanged from ComprehensiveReport.jsx. Parity is covered by tests.
"use strict";
const reduceToSingleDigitForFractal = (num) => {
    if (num === 0)
        return 0;
    let result = num;
    while (result > 9) {
        result = String(result).split('').reduce((sum, digit) => sum + parseInt(digit, 10), 0);
    }
    return result;
};
const calculateBehaviorFractal = (birthDate) => {
    if (!birthDate)
        return null;
    try {
        let day, month, year;
        if (birthDate.includes('.')) {
            const parts = birthDate.split('.');
            day = parseInt(parts[0], 10);
            month = parseInt(parts[1], 10);
            year = parseInt(parts[2], 10);
        }
        else if (birthDate.includes('-')) {
            const parts = birthDate.split('-');
            year = parseInt(parts[0], 10);
            month = parseInt(parts[1], 10);
            day = parseInt(parts[2], 10);
        }
        else {
            return null;
        }
        if (isNaN(day) || isNaN(month) || isNaN(year))
            return null;
        const digit1 = reduceToSingleDigitForFractal(day);
        const digit2 = reduceToSingleDigitForFractal(month);
        const digit3 = reduceToSingleDigitForFractal(year);
        const digit4 = reduceToSingleDigitForFractal(day + month + year);
        return {
            digit1,
            digit2,
            digit3,
            digit4,
            fractal: `${digit1}${digit2}${digit3}${digit4}`
        };
    }
    catch {
        return null;
    }
};
const calculateTaskNumbers = (soulNumber, mindNumber, destinyNumber, yearNumber) => {
    if (soulNumber === null || soulNumber === undefined ||
        mindNumber === null || mindNumber === undefined ||
        destinyNumber === null || destinyNumber === undefined ||
        yearNumber === null || yearNumber === undefined) {
        return null;
    }
    try {
        const problem1 = Math.abs(soulNumber - mindNumber);
        const problem1Reduced = reduceToSingleDigitForFractal(problem1);
        const period1Start = 36 - destinyNumber;
        const period1End = period1Start + 9;
        const problem2 = Math.abs(soulNumber - yearNumber);
        const problem2Reduced = reduceToSingleDigitForFractal(problem2);
        const period2Start = period1End;
        const period2End = period2Start + 9;
        const problem3 = Math.abs(problem1Reduced - problem2Reduced);
        const problem3Reduced = reduceToSingleDigitForFractal(problem3);
        const problem4 = Math.abs(mindNumber - yearNumber);
        const problem4Reduced = reduceToSingleDigitForFractal(problem4);
        const period4Start = period2End;
        return {
            problem1: problem1Reduced,
            problem2: problem2Reduced,
            problem3: problem3Reduced,
            problem4: problem4Reduced,
            period1: { start: period1Start, end: period1End },
            period2: { start: period2Start, end: period2End },
            period3: { start: 0, end: null },
            period4: { start: period4Start, end: null },
            calculations: {
                problem1Raw: problem1,
                problem2Raw: problem2,
                problem3Raw: problem3,
                problem4Raw: problem4,
                soulNumber,
                mindNumber,
                destinyNumber,
                yearNumber
            }
        };
    }
    catch {
        return null;
    }
};
const calculateShadowsPeaksChallenges = (birthDate) => {
    if (!birthDate)
        return null;
    try {
        let day, month, year;
        if (birthDate.includes('.')) {
            const parts = birthDate.split('.');
            day = parseInt(parts[0], 10);
            month = parseInt(parts[1], 10);
            year = parseInt(parts[2], 10);
        }
        else if (birthDate.includes('-')) {
            const parts = birthDate.split('-');
            year = parseInt(parts[0], 10);
            month = parseInt(parts[1], 10);
            day = parseInt(parts[2], 10);
        }
        else {
            return null;
        }
        if (isNaN(day) || isNaN(month) || isNaN(year))
            return null;
        const reduceToSingleDigit = (num) => {
            let n = Math.abs(num);
            while (n > 9) {
                n = String(n).split('').reduce((sum, digit) => sum + parseInt(digit, 10), 0);
            }
            return n;
        };
        const destinyNumber = reduceToSingleDigit(day + month + year);
        const baseNumber = reduceToSingleDigit(day + month);
        const dayReduced = reduceToSingleDigit(day);
        const monthReduced = reduceToSingleDigit(month);
        const years = [];
        for (let age = 1; age <= 100; age++) {
            const currentYear = year + age;
            const chlg = reduceToSingleDigit(dayReduced + monthReduced + currentYear);
            years.push({
                age,
                year: currentYear,
                chlg
            });
        }
        const firstPeriodStart = 27 - destinyNumber;
        const periodLength = 9;
        const yearReduced = reduceToSingleDigit(year);
        // Author's table «Тени · Вершины · Вызовы · Переходы»: four 9-year periods (labelled 23–32, 32–41, …).
        // Peaks: day + month, day + year, the sum of both, month + year. Challenges: the matching differences.
        // Shadow = peak + day, month, year, destiny in turn; transition = shadow + peak + challenge.
        const firstPeak = reduceToSingleDigit(dayReduced + monthReduced);
        const secondPeak = reduceToSingleDigit(dayReduced + yearReduced);
        const peaks = [firstPeak, secondPeak, reduceToSingleDigit(firstPeak + secondPeak), reduceToSingleDigit(monthReduced + yearReduced)];
        const firstChallenge = Math.abs(monthReduced - dayReduced);
        const secondChallenge = Math.abs(dayReduced - yearReduced);
        const challenges = [firstChallenge, secondChallenge, Math.abs(firstChallenge - secondChallenge), Math.abs(monthReduced - yearReduced)];
        const shadowBases = [dayReduced, monthReduced, yearReduced, destinyNumber];
        const periods = peaks.map((peak, i) => {
            const startAge = firstPeriodStart + i * periodLength;
            const endAge = startAge + periodLength;
            const shadow = reduceToSingleDigit(shadowBases[i] + peak);
            const challenge = challenges[i];
            const transition = reduceToSingleDigit(shadow + peak + challenge);
            return {
                index: i + 1,
                startAge,
                endAge,
                years: years.filter(y => y.age >= startAge && y.age < endAge),
                shadow,
                peak,
                challenge,
                transition,
                periodNumbers: [shadow, peak, challenge, transition]
            };
        });
        return {
            baseNumber,
            destinyNumber,
            birthDate: { day, month, year },
            years,
            periods,
            sequence: years.map(y => y.chlg).join(' ')
        };
    }
    catch {
        return null;
    }
};
const calculateIndividualNumbers = (birthDate, targetDate = null, destinyNumber = null) => {
    if (!birthDate)
        return null;
    try {
        let birthDay, birthMonth, birthYear;
        if (birthDate.includes('.')) {
            const parts = birthDate.split('.');
            birthDay = parseInt(parts[0], 10);
            birthMonth = parseInt(parts[1], 10);
            birthYear = parseInt(parts[2], 10);
        }
        else if (birthDate.includes('-')) {
            const parts = birthDate.split('-');
            birthYear = parseInt(parts[0], 10);
            birthMonth = parseInt(parts[1], 10);
            birthDay = parseInt(parts[2], 10);
        }
        else {
            return null;
        }
        if (isNaN(birthDay) || isNaN(birthMonth) || isNaN(birthYear))
            return null;
        const reduceToSingleDigit = (num) => {
            let n = Math.abs(num);
            while (n > 9) {
                n = String(n).split('').reduce((sum, digit) => sum + parseInt(digit, 10), 0);
            }
            return n;
        };
        if (destinyNumber === null || destinyNumber === undefined) {
            const destinySum = birthDay + birthMonth + birthYear;
            destinyNumber = reduceToSingleDigit(destinySum);
        }
        const now = targetDate ? new Date(targetDate) : new Date();
        const currentYear = now.getFullYear();
        const currentMonth = now.getMonth() + 1;
        const currentDay = now.getDate();
        const chig = reduceToSingleDigit(birthDay + birthMonth + currentYear);
        const chim = reduceToSingleDigit(chig + currentMonth);
        const chid = reduceToSingleDigit(chim + currentDay);
        const chpgValue = reduceToSingleDigit(Math.abs(chig - destinyNumber));
        const chpg = {
            value: chpgValue,
            calculation: `|${chig} - ${destinyNumber}| = ${Math.abs(chig - destinyNumber)} → ${chpgValue}`
        };
        const chpmValue = reduceToSingleDigit(Math.abs(birthMonth - chim));
        const chpm = {
            value: chpmValue,
            calculation: `|${birthMonth} - ${chim}| = ${Math.abs(birthMonth - chim)} → ${chpmValue}`
        };
        const chpdValue = reduceToSingleDigit(Math.abs(birthDay - chid));
        const chpd = {
            value: chpdValue,
            calculation: `|${birthDay} - ${chid}| = ${Math.abs(birthDay - chid)} → ${chpdValue}`
        };
        return {
            birthDate: { day: birthDay, month: birthMonth, year: birthYear },
            currentDate: { day: currentDay, month: currentMonth, year: currentYear },
            destinyNumber: destinyNumber,
            chig: {
                value: chig,
                calculation: `${birthDay} + ${birthMonth} + ${currentYear} = ${birthDay + birthMonth + currentYear} → ${chig}`
            },
            chim: {
                value: chim,
                calculation: `${chig} + ${currentMonth} = ${chig + currentMonth} → ${chim}`
            },
            chid: {
                value: chid,
                calculation: `${chim} + ${currentDay} = ${chim + currentDay} → ${chid}`
            },
            chpg: chpg,
            chpm: chpm,
            chpd: chpd
        };
    }
    catch {
        return null;
    }
};

module.exports={reduceToSingleDigitForFractal,calculateBehaviorFractal,calculateTaskNumbers,calculateShadowsPeaksChallenges,calculateIndividualNumbers};
