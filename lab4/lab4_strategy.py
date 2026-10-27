import re
from abc import ABC, abstractmethod


# 1. Інтерфейс Стратегії (Strategy)
class ISyntaxHighlightStrategy(ABC):
    @abstractmethod
    def get_language_name(self) -> str:
        pass

    @abstractmethod
    def highlight(self, text: str) -> str:
        pass


# 2. Конкретна стратегія №1: Підсвічування синтаксису Python
class PythonHighlightStrategy(ISyntaxHighlightStrategy):
    def __init__(self):
        self.keywords = ["def", "return", "if", "else", "for", "in", "import", "class", "print"]

    def get_language_name(self) -> str:
        return "Python"

    def highlight(self, text: str) -> str:
        lines = []
        for idx, line in enumerate(text.splitlines(), 1):
            if line.strip().startswith("#"):
                formatted = f"[COMMENT: {line}]"
            else:
                formatted = line
                for kw in self.keywords:
                    formatted = re.sub(rf"\b({kw})\b", r"[KW:\1]", formatted)
            lines.append(f"{idx:02d} | {formatted}")
        return "\n".join(lines)


# 3. Конкретна стратегія №2: Підсвічування розмітки Markdown
class MarkdownHighlightStrategy(ISyntaxHighlightStrategy):
    def get_language_name(self) -> str:
        return "Markdown"

    def highlight(self, text: str) -> str:
        lines = []
        for idx, line in enumerate(text.splitlines(), 1):
            if line.strip().startswith("#"):
                formatted = f"[HEADING: {line}]"
            else:
                formatted = re.sub(r"\*\*(.*?)\*\*", r"[BOLD:\1]", line)
            lines.append(f"{idx:02d} | {formatted}")
        return "\n".join(lines)


# 4. Конкретна стратегія №3: Підсвічування розмітки HTML/XML
class HtmlHighlightStrategy(ISyntaxHighlightStrategy):
    def get_language_name(self) -> str:
        return "HTML/XML"

    def highlight(self, text: str) -> str:
        lines = []
        for idx, line in enumerate(text.splitlines(), 1):
            formatted = re.sub(r"(</?[a-zA-Z0-9]+>)", r"[TAG:\1]", line)
            lines.append(f"{idx:02d} | {formatted}")
        return "\n".join(lines)


# 5. Клас Контексту (Context) — Текстовий редактор
class TextEditorContext:
    def __init__(self, document_title: str, encoding: str, strategy: ISyntaxHighlightStrategy):
        self.document_title = document_title
        self.encoding = encoding
        self._strategy = strategy

    def set_strategy(self, strategy: ISyntaxHighlightStrategy) -> None:
        print(f"\n[Context] Зміна стратегії підсвічування на: {strategy.get_language_name()}")
        self._strategy = strategy

    def render_document(self, raw_text: str) -> str:
        header = (
            f"=== Файл: {self.document_title} | Кодування: {self.encoding} "
            f"| Режим синтаксису: {self._strategy.get_language_name()} ==="
        )
        body = self._strategy.highlight(raw_text)
        result = f"{header}\n{body}"
        print(result)
        return result


# Демонстрація роботи патерну Strategy
if __name__ == "__main__":
    # Створюємо контекст редактора з початковою стратегією Python
    editor = TextEditorContext("script.py", "UTF-8", PythonHighlightStrategy())
    python_code = "# Обчислення суми\ndef calculate(items):\n    for x in items:\n        print(x)\n    return True"
    editor.render_document(python_code)

    # Динамічно змінюємо стратегію на Markdown під час виконання програми
    editor.document_title = "README.md"
    editor.set_strategy(MarkdownHighlightStrategy())
    md_text = "# Текстовий редактор\nПідтримує **макроси**, **сніппети** та **закладки**."
    editor.render_document(md_text)

    # Динамічно змінюємо стратегію на HTML
    editor.document_title = "index.html"
    editor.set_strategy(HtmlHighlightStrategy())
    html_text = "<div>\n    <h1>Hello KPI</h1>\n</div>"
    editor.render_document(html_text)