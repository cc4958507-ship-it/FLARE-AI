import { useSyncExternalStore } from 'react';
import ar from './ar.json';
import research from './ar-research.json';

export type Language = 'en' | 'ar';
const dictionary: Record<string, string> = {...ar, ...research};
let language: Language = 'en';
try { language = localStorage.getItem('flare-language') === 'ar' ? 'ar' : 'en'; } catch { /* Storage may be disabled. */ }
const listeners = new Set<() => void>();
export function getLanguage() { return language; }
export function setLanguage(next: Language) {
  language = next;
  document.documentElement.lang = next;
  document.documentElement.dir = next === 'ar' ? 'rtl' : 'ltr';
  try { localStorage.setItem('flare-language', next); } catch { /* Keep the in-memory selection. */ }
  listeners.forEach(listener => listener());
}
export function useLanguage() {
  return useSyncExternalStore(listener => {listeners.add(listener); return () => listeners.delete(listener);}, getLanguage);
}
// Preserve API values, source identifiers, numbers and React nodes; translate display strings only.
export function t<T>(value: T): T {
  if (language !== 'ar' || typeof value !== 'string') return value;
  const key = value.trim().replace(/\s+/g, ' ');
  if (dictionary[key]) return (value.match(/^\s*/)?.[0] + dictionary[key] + value.match(/\s*$/)?.[0]) as T;
  if (value.startsWith('Matched: ')) return (t('Matched') + ': ' + value.slice(9)) as T;
  if (value.includes(' · ')) return value.split(' · ').map(part => t(part)).join(' · ') as T;
  return value;
}
export function msg(template: string, values: (string | number)[]) {
  return t(template).replace(/\{(\d+)\}/g, (_, index) => String(t(values[Number(index)])));
}
setLanguage(language);
