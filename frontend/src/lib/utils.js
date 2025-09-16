import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

export function formatDate(dateString) {
  try {
    const [day, month, year] = dateString.split('.');
    return `${day}.${month}.${year}`;
  } catch {
    return dateString;
  }
}

export function validateBirthDate(dateString) {
  const regex = /^\d{2}\.\d{2}\.\d{4}$/;
  if (!regex.test(dateString)) {
    return false;
  }
  
  const [day, month, year] = dateString.split('.').map(Number);
  
  if (day < 1 || day > 31) return false;
  if (month < 1 || month > 12) return false;
  if (year < 1900 || year > new Date().getFullYear()) return false;
  
  return true;
}