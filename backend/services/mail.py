"""Configured SMTP delivery. No console-token fallback or secret logging."""
import os
import smtplib
import ssl
from pathlib import Path
import certifi
from email.message import EmailMessage
from starlette.concurrency import run_in_threadpool

def smtp_tls_context():
    context=ssl.create_default_context()
    # Some macOS Python installs have no system CA bundle. Keep verification on.
    if not context.get_ca_certs(): context.load_verify_locations(cafile=certifi.where())
    return context

class SMTPMailer:
    def __init__(self):
        self.host = os.environ.get('SMTP_HOST','')
        self.user = os.environ.get('SMTP_USER','')
        self.password = os.environ.get('SMTP_PASSWORD','')
        self.sender = os.environ.get('SMTP_FROM','') or self.user
        self.security = os.environ.get('SMTP_SECURITY','starttls')
        try: self.port = int(os.environ.get('SMTP_PORT','587'))
        except ValueError: self.port = 0
    @property
    def configured(self):
        return bool(self.host and self.sender and '@' in self.sender and 0 < self.port < 65536 and self.security in ('starttls','ssl') and (not self.user or self.password))
    def _send(self, to, subject, body, headers=None, html=None, images=None):
        if not self.configured: raise RuntimeError('Mail delivery is not configured')
        message = EmailMessage()
        message['From'], message['To'], message['Subject'] = self.sender, to, subject
        for name, value in (headers or {}).items(): message[name] = value
        message.set_content(body)
        if html:
            # The text stays for mail apps without HTML; pictures travel inside the letter (cid:), not as remote links.
            message.add_alternative(html, subtype='html')
            for cid, path in (images or {}).items():
                message.get_payload()[1].add_related(Path(path).read_bytes(), 'image', 'png', cid=f'<{cid}>')
        context = smtp_tls_context()
        if self.security == 'ssl': connection = smtplib.SMTP_SSL(self.host,self.port,timeout=12,context=context)
        else: connection = smtplib.SMTP(self.host,self.port,timeout=12)
        with connection as smtp:
            if self.security == 'starttls': smtp.ehlo(); smtp.starttls(context=context); smtp.ehlo()
            if self.user: smtp.login(self.user,self.password)
            smtp.send_message(message)
    async def send_reset(self, email, url):
        await run_in_threadpool(self._send,email,'Восстановление пароля NumerOM',
            f'Вы запросили восстановление доступа к NumerOM.\n\nОткройте ссылку и задайте новый пароль:\n{url}\n\nСсылка действует 30 минут и только один раз.\nЕсли вы не отправляли запрос, просто проигнорируйте это письмо: пароль не изменился.\n\nNumerOM')
    async def send_report_ready(self, email, url, minutes, chapters):
        video = f'персональное видео со схемами — около {minutes} мин' if minutes else 'персональное видео со схемами'
        await run_in_threadpool(self._send,email,'Ваш полный разбор NumerOM готов',
            'Здравствуйте!\n\nВаш полный разбор NumerOM готов и сохранён в личном кабинете:\n'
            f'— текст разбора: ваши потенциалы и то, на что стоит обратить внимание;\n— озвучка всех глав ({chapters});\n— {video}.\n\n'
            + (f'Открыть разбор:\n{url}\n\n' if url else 'Откройте раздел «Полный разбор» в приложении NumerOM.\n\n')
            + 'Повторная оплата не нужна: текст, аудио и видео остаются в вашем аккаунте.\n\nNumerOM')
    async def send_letter(self, email, subject, body, unsubscribe, html=None, images=None):
        """A recurring letter: mail apps show their own «Отписаться» button from List-Unsubscribe."""
        await run_in_threadpool(self._send, email, subject, body, {'List-Unsubscribe': f'<{unsubscribe}>'}, html, images)
    async def send_changed(self, email):
        await run_in_threadpool(self._send,email,'Пароль NumerOM изменён',
            'Пароль вашего аккаунта NumerOM изменён. Предыдущие сеансы завершены.\nЕсли это сделали не вы, немедленно восстановите доступ на сайте NumerOM и обратитесь в поддержку.\n\nNumerOM')
