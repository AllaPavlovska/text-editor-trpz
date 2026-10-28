from abc import ABC, abstractmethod
from typing import Dict, List


# 1. Інтерфейс Пристосуванця (Flyweight)
class ITokenFlyweight(ABC):
    @abstractmethod
    def render(self, text_value: str, line: int, column: int) -> str:
        """Приймає зовнішній стан (extrinsic state): текст токена, рядок і стовпчик."""
        pass


# 2. Конкретний поділюваний Пристосуванець (ConcreteFlyweight)
class SharedTokenStyle(ITokenFlyweight):
    """Зберігає внутрішній незмінний стан (intrinsic state): параметри шрифту та кольору."""

    def __init__(self, token_type: str, font_family: str, font_size: int, color_hex: str, is_bold: bool):
        self._token_type = token_type
        self._font_family = font_family
        self._font_size = font_size
        self._color_hex = color_hex
        self._is_bold = is_bold

    def render(self, text_value: str, line: int, column: int) -> str:
        weight = "Bold" if self._is_bold else "Normal"
        return (
            f"[Рядок {line:02d}, Стовп. {column:02d}] Токен {repr(text_value):12} -> "
            f"Стиль({self._token_type}: {self._font_family} {self._font_size}pt, "
            f"{self._color_hex}, {weight}) [id об'єкта стилю={id(self)}]"
        )


# 3. Неподілюваний Пристосуванець (UnsharedConcreteFlyweight)
class CustomBookmarkFlyweight(ITokenFlyweight):
    """Унікальний маркер для рядка з індивідуальною закладкою користувача."""

    def __init__(self, bookmark_note: str, highlight_bg: str = "#FEF08A"):
        self._bookmark_note = bookmark_note
        self._highlight_bg = highlight_bg

    def render(self, text_value: str, line: int, column: int) -> str:
        return (
            f"[Рядок {line:02d}, Стовп. {column:02d}] Токен {repr(text_value):12} -> "
            f"[УНІКАЛЬНА ЗАКЛАДКА: '{self._bookmark_note}', Фон={self._highlight_bg}]"
        )


# 4. Фабрика Пристосуванців (FlyweightFactory)
class StyleFlyweightFactory:
    def __init__(self):
        self._pool: Dict[str, SharedTokenStyle] = {}

    def get_style(
        self,
        token_type: str,
        font_family: str = "JetBrains Mono",
        font_size: int = 12,
        color_hex: str = "#FFFFFF",
        is_bold: bool = False
    ) -> SharedTokenStyle:
        key = f"{token_type}_{font_family}_{font_size}_{color_hex}_{is_bold}"
        if key not in self._pool:
            print(f"[FlyweightFactory] Створено НОВИЙ об'єкт стилю в пулі: '{token_type}' ({color_hex})")
            self._pool[key] = SharedTokenStyle(token_type, font_family, font_size, color_hex, is_bold)
        else:
            print(f"[FlyweightFactory] Повернено ІСНУЮЧИЙ об'єкт стилю з пулу: '{token_type}'")
        return self._pool[key]

    def get_pool_size(self) -> int:
        return len(self._pool)


# 5. Контекст (Зовнішній стан токена) та Клієнт (Буфер редактора)
class DocumentTokenContext:
    def __init__(self, text_value: str, line: int, column: int, flyweight: ITokenFlyweight):
        self.text_value = text_value
        self.line = line
        self.column = column
        self._flyweight = flyweight

    def draw(self) -> str:
        return self._flyweight.render(self.text_value, self.line, self.column)


class SyntaxDocumentBuffer:
    def __init__(self, factory: StyleFlyweightFactory):
        self._factory = factory
        self._tokens: List[DocumentTokenContext] = []

    def add_shared_token(
        self, text: str, line: int, col: int, token_type: str, color: str, bold: bool = False
    ) -> None:
        style = self._factory.get_style(token_type=token_type, color_hex=color, is_bold=bold)
        self._tokens.append(DocumentTokenContext(text, line, col, style))

    def add_custom_bookmark_token(self, text: str, line: int, col: int, note: str) -> None:
        unshared = CustomBookmarkFlyweight(bookmark_note=note)
        self._tokens.append(DocumentTokenContext(text, line, col, unshared))

    def render_all(self) -> None:
        print("\n=== Відмальовування буфера документа (використання патерну Flyweight) ===")
        for token in self._tokens:
            print(token.draw())
        print(
            f"\n[Статистика пам'яті]: Всього токенів у документі: {len(self._tokens)} | "
            f"Фізично створено об'єктів SharedTokenStyle у пам'яті: {self._factory.get_pool_size()}"
        )


if __name__ == "__main__":
    factory = StyleFlyweightFactory()
    buffer = SyntaxDocumentBuffer(factory)

    # Додаємо 8 токенів коду Python (ключові слова, ідентифікатори, оператори повторюються)
    buffer.add_shared_token("def", 1, 1, "KEYWORD", "#C084FC", bold=True)
    buffer.add_shared_token("calc", 1, 5, "IDENTIFIER", "#E2E8F0", bold=False)
    buffer.add_shared_token("if", 2, 5, "KEYWORD", "#C084FC", bold=True)
    buffer.add_shared_token("x", 2, 8, "IDENTIFIER", "#E2E8F0", bold=False)
    buffer.add_shared_token("return", 3, 9, "KEYWORD", "#C084FC", bold=True)
    buffer.add_shared_token("x", 3, 16, "IDENTIFIER", "#E2E8F0", bold=False)
    buffer.add_shared_token("'UTF-8'", 4, 5, "STRING", "#86EFAC", bold=False)

    # Додаємо неподілюваний пристосуванець (унікальна закладка користувача)
    buffer.add_custom_bookmark_token("TODO_FIX", 5, 1, "Перевірити кодування файлу перед збереженням")

    buffer.render_all()
    