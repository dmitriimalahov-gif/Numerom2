"""Pure name number calculation, preserved from the active server."""
def _letters_to_number_sum(text: str) -> int:
    if not text:
        return 0
    norm = [ch for ch in (text or '').upper() if 'A' <= ch <= 'Z']
    total = 0
    for ch in norm:
        total += ord(ch) - ord('A') + 1  # A=1 ... Z=26
    return total

def calculate_full_name_number(name: str = '', surname: str = '') -> int:
    """
    Число имени: используем ТОЛЬКО латиницу из поля name и фамилии.
    Полное число имени = reduce( sum(буквы имени+фамилии) ).
    """
    base_sum = _letters_to_number_sum((name or '') + (surname or ''))
    x = abs(int(base_sum))
    while x > 9:
        x = sum(int(d) for d in str(x))
    return x

