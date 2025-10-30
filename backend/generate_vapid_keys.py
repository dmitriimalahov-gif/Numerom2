#!/usr/bin/env python3
"""
Скрипт для генерации VAPID ключей для Web Push уведомлений

Запустите этот скрипт один раз и добавьте сгенерированные ключи в .env файл:

python generate_vapid_keys.py

Затем добавьте в .env:
VAPID_PUBLIC_KEY=<публичный_ключ>
VAPID_PRIVATE_KEY=<приватный_ключ>
"""

from py_vapid import Vapid

def generate_vapid_keys():
    vapid = Vapid()
    vapid.generate_keys()

    public_key = vapid.public_key.export_public().decode('utf-8')
    private_key = vapid.private_key.export().decode('utf-8')

    print("=" * 80)
    print("VAPID Keys Generated Successfully!")
    print("=" * 80)
    print("\nAdd these keys to your .env file:\n")
    print(f"VAPID_PUBLIC_KEY={public_key}")
    print(f"VAPID_PRIVATE_KEY={private_key}")
    print("\n" + "=" * 80)
    print("\nPublic key (для frontend):")
    print(public_key)
    print("\n" + "=" * 80)

    # Сохраняем в файл для удобства
    with open('.env.vapid', 'w') as f:
        f.write(f"VAPID_PUBLIC_KEY={public_key}\n")
        f.write(f"VAPID_PRIVATE_KEY={private_key}\n")

    print("\nКлючи также сохранены в файл .env.vapid")
    print("Скопируйте их в ваш основной .env файл")

if __name__ == "__main__":
    generate_vapid_keys()
