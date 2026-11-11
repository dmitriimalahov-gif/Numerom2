export async function readAdminResponse(response) {
  let data;
  try { data = await response.json(); } catch { data = null; }
  if (!response.ok) {
    const detail = data?.detail;
    const message = response.status >= 500 ? 'Сервер временно недоступен. Повторите попытку.' : typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(item => item.msg).join('. ') : 'Не удалось выполнить действие. Повторите попытку.';
    throw new Error(message);
  }
  return data;
}
