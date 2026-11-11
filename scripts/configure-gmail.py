"""Interactive local setup: never echo or transmit the Gmail app password."""
from getpass import getpass
from pathlib import Path
from dotenv import dotenv_values, set_key


def main():
    path = Path(__file__).resolve().parents[1] / 'backend' / '.env'
    current = dotenv_values(path)
    sender = current.get('SMTP_USER', '').strip()
    if not sender.endswith('@gmail.com'):
        raise SystemExit('Сначала укажите адрес Gmail в SMTP_USER локальных настроек сервера.')
    print(f'Подключение NumerOM к {sender}')
    print('Создайте пароль приложения NumerOM: https://myaccount.google.com/apppasswords')
    print('Вставьте выданный Google пароль ниже. Символы при вводе не показываются.')
    password = ''.join(getpass('Пароль приложения (Enter — отмена): ').split())
    if not password:
        print('Отменено. Настройки не изменены.'); return
    if len(password) != 16 or not password.isascii() or not password.isalpha():
        raise SystemExit('Ожидался 16-символьный пароль приложения Google. Ничего не сохранено.')
    for key, value in {'SMTP_HOST':'smtp.gmail.com', 'SMTP_PORT':'587',
                       'SMTP_SECURITY':'starttls', 'SMTP_FROM':sender,
                       'SMTP_PASSWORD':password}.items():
        set_key(path, key, value)
    path.chmod(0o600)
    print('Пароль сохранён только в локальных настройках сервера. Письма не отправлялись.')
    print('Перезапустите сервер NumerOM, чтобы применить настройки.')
    print('Для доступа с телефона нужен публичный HTTPS-адрес в PASSWORD_RESET_URL.')


if __name__ == '__main__':
    try: main()
    except (KeyboardInterrupt, EOFError): print('\nОтменено.')
