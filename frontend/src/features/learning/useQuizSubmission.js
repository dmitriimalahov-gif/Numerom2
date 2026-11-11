import { useRef, useState } from 'react';
import { api } from '../../services/api';

function newSubmissionId() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  const bytes = globalThis.crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 15) | 64;
  bytes[8] = (bytes[8] & 63) | 128;
  const hex = Array.from(bytes, value => value.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

// One submission identity survives retries; only the server decides the result.
export default function useQuizSubmission() {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const pending = useRef(false);
  const attempt = useRef(null);
  const reset = () => { if (!pending.current) { attempt.current = null; setError(''); } };
  const submit = async (lesson, answers) => {
    if (pending.current) return null;
    pending.current = true; setSubmitting(true); setError('');
    try {
      const body = { lesson_id: lesson.id, quiz_id: lesson.quiz.id || lesson.id, answers: Object.fromEntries(Object.entries(answers).sort(([a], [b]) => a.localeCompare(b))) };
      const key = JSON.stringify(body);
      if (attempt.current?.key !== key) attempt.current = { key, body: { ...body, submission_id: newSubmissionId() } };
      const result = await api.request('/student/quiz-attempt', { method: 'POST', body: attempt.current.body });
      if (!Number.isFinite(result?.score) || typeof result.passed !== 'boolean') throw new Error('Не удалось получить результат теста. Повторите отправку.');
      return result;
    } catch (failure) { setError(failure.message); return null; }
    finally { pending.current = false; setSubmitting(false); }
  };
  return { submit, reset, submitting, error };
}
