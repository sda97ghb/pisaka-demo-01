numbers = "0123456789"
english_letters = "abcdefghijklmnopqrstuvwxyz"
russian_letters = "абвгдежзийклмнопрстуфхцчшщъыьэюя"
russian_replacements = [
    "a",
    "b",
    "v",
    "g",
    "d",
    "e",
    "zh",
    "z",
    "i",
    "y",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "r",
    "s",
    "t",
    "u",
    "f",
    "h",
    "ts",
    "ch",
    "sh",
    "sch",
    "",
    "y",
    "",
    "e",
    "yu",
    "ya",
]


def slugify(text: str) -> str:
    # Простой способ генерации слага для примера.
    # В реальном приложении скорее всего будет отдельный модуль для этого
    slug_letters = []
    for letter in text.lower():
        if letter == " ":
            slug_letters.append("-")
        if letter in english_letters or letter in numbers:
            slug_letters.append(letter)
        if (letter_idx := russian_letters.find(letter)) >= 0:
            slug_letters.append(russian_replacements[letter_idx])
    return "".join(slug_letters)


def is_valid_slug(slug: str) -> bool:
    if not slug:
        return False
    for letter in slug:
        if letter == "-":
            continue
        if letter in numbers:
            continue
        if letter in english_letters:
            continue
        return False
    return True
