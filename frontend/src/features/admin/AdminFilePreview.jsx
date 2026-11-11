import React, { useEffect, useState } from 'react';
import { getBackendUrl } from '../../utils/backendUrl';
import { readAdminResponse } from './requestHelpers';

// Protected downloads need a bearer header. Render only a local blob or plain text.
export default function AdminFilePreview({ file, endpoint = `/api/download-file/${encodeURIComponent(file.id)}` }) {
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  const type = file.mime_type || '';
  const supported = /^(image|video|audio|text)\//.test(type) || type === 'application/pdf' || file.extension?.toLowerCase() === 'pdf';

  useEffect(() => {
    setPreview(null); setError('');
    if (!supported) return undefined;
    const controller = new AbortController();
    let localUrl;
    let active = true;
    (async () => {
      try {
        const response = await fetch(`${getBackendUrl()}${endpoint}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }, signal: controller.signal,
        });
        if (!response.ok) await readAdminResponse(response);
        let content;
        if (type.startsWith('text/')) content = { text: await response.text() };
        else {
          const blob = await response.blob();
          const isPdf = type === 'application/pdf' || file.extension?.toLowerCase() === 'pdf';
          content = { url: URL.createObjectURL(isPdf ? new Blob([blob], { type: 'application/pdf' }) : blob) };
        }
        localUrl = content.url;
        if (active) setPreview(content);
        else if (localUrl) { URL.revokeObjectURL(localUrl); localUrl = null; }
      } catch (failure) {
        if (active) setError(failure.message || 'Не удалось загрузить файл.');
      }
    })();
    return () => { active = false; controller.abort(); if (localUrl) URL.revokeObjectURL(localUrl); };
  }, [file.id, file.extension, type, supported, endpoint, retry]);

  if (!supported) return <p>Для просмотра этого формата скачайте файл.</p>;
  if (error) return <div role="alert"><p>{error}</p><button type="button" className="nm-admin-button secondary" onClick={() => setRetry(value => value + 1)}>Повторить загрузку</button></div>;
  if (!preview) return <p role="status">Загрузка файла…</p>;
  if (preview.text !== undefined) return <pre className="whitespace-pre-wrap break-words">{preview.text}</pre>;
  if (type.startsWith('image/')) return <img src={preview.url} alt={file.original_name} className="max-w-full max-h-full mx-auto object-contain" />;
  if (type.startsWith('video/')) return <video controls src={preview.url} className="max-w-full max-h-full mx-auto" />;
  if (type.startsWith('audio/')) return <audio controls src={preview.url} />;
  return <iframe src={preview.url} title={file.original_name} className="w-full h-full" />;
}
