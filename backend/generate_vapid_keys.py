#!/usr/bin/env python3
"""
Скрипт для генерации VAPID ключей для Web Push уведомлений

Запустите этот скрипт один раз и добавьте сгенерированные ключи в .env файл:

python generate_vapid_keys.py

Затем добавьте в .env:
VAPID_PUBLIC_KEY=<публичный_ключ>
VAPID_PRIVATE_KEY=<приватный_ключ>
"""

import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

def generate_vapid_keys():
    # Генерируем приватный ключ напрямую через cryptography
    private_key = ec.generate_private_key(ec.SECP256R1())

    # Получаем публичный ключ
    public_key = private_key.public_key()

    # Экспортируем приватный ключ в PEM формате
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    # Экспортируем публичный ключ в формате, подходящем для VAPID
    public_numbers = public_key.public_numbers()

    # Конвертируем в uncompressed point format для VAPID
    x_bytes = public_numbers.x.to_bytes(32, byteorder='big')
    y_bytes = public_numbers.y.to_bytes(32, byteorder='big')

    # VAPID использует uncompressed point: 0x04 + x + y
    public_bytes = b'\x04' + x_bytes + y_bytes
    public_key_b64 = base64.urlsafe_b64encode(public_bytes).decode('utf-8').rstrip('=')

    print("=" * 80)
    print("VAPID Keys Generated Successfully!")
    print("=" * 80)
    print("\nAdd these keys to your .env file:\n")
    print(f"VAPID_PUBLIC_KEY={public_key_b64}")
    print(f"VAPID_PRIVATE_KEY={private_pem.replace(chr(10), '\\n')}")
    print("\n" + "=" * 80)
    print("\nPublic key (для frontend):")
    print(public_key_b64)
    print("\n" + "=" * 80)

    # Сохраняем в файл для удобства
    import os
    import shutil

    vapid_file = '/app/.env.vapid'

    # Если .env.vapid существует как директория - удаляем её
    if os.path.exists(vapid_file):
        if os.path.isdir(vapid_file):
            shutil.rmtree(vapid_file)
        else:
            os.remove(vapid_file)

    with open(vapid_file, 'w') as f:
        f.write(f"VAPID_PUBLIC_KEY={public_key_b64}\n")
        # Сохраняем приватный ключ в одну строку с \n в виде литералов
        private_pem_escaped = private_pem.replace('\n', '\\n')
        f.write(f'VAPID_PRIVATE_KEY="{private_pem_escaped}"\n')

    print("\nКлючи также сохранены в файл .env.vapid")
    print("Скопируйте их в ваш основной .env файл")

if __name__ == "__main__":
    generate_vapid_keys()
