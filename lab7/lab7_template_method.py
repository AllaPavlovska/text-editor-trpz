from abc import ABC, abstractmethod
from typing import Dict, List


# 1. Абстрактний базовий клас із Шаблонним методом (AbstractClass)
class DocumentExportTemplate(ABC):
    """
    Визначає скелет алгоритму експорту та перекодування документа текстового редактора.
    Підкласи перевизначають окремі кроки форматування без зміни структури алгоритму.
    """

    # ШАБЛОННИЙ МЕТОД (Template Method) — фіксує послідовність кроків алгоритму
    def export_document(
        self,
        title: str,
        content: str,
        encoding: str,
        bookmarks: Dict[int, str]
    ) -> str:
        lines = self.normalize_text(content)
        header = self.format_header(title, encoding)

        formatted_lines: List[str] = []
        for idx, line in enumerate(lines, start=1):
            note = bookmarks.get(idx, "")
            formatted_lines.append(self.format_line(idx, line, note))

        body = "\n".join(formatted_lines)
        footer = self.format_footer(len(lines))

        full_output = f"{header}\n{body}\n{footer}".strip()
        encoded_bytes = self.encode_output(full_output, encoding)

        print(f"=== Експорт через {self.__class__.__name__} (Кодування: {encoding}, Байтів: {len(encoded_bytes)}) ===")
        print(full_output)
        print()
        return full_output

    # Загальний крок 1 (спільна реалізація для всіх підкласів)
    def normalize_text(self, content: str) -> List[str]:
        return [line.rstrip() for line in content.splitlines()]

    # Загальний крок 2 (перевірка та перекодування у вибране кодування)
    def encode_output(self, raw_output: str, encoding: str) -> bytes:
        return raw_output.encode(encoding, errors="replace")

    # Абстрактні кроки, які реалізуються в дочірніх класах (Primitive Operations)
    @abstractmethod
    def format_header(self, title: str, encoding: str) -> str:
        pass

    @abstractmethod
    def format_line(self, line_num: int, text: str, bookmark_note: str) -> str:
        pass

    @abstractmethod
    def format_footer(self, total_lines: int) -> str:
        pass


# 2. Конкретний клас №1: Експорт документа у формат HTML
class HtmlDocumentExporter(DocumentExportTemplate):
    def format_header(self, title: str, encoding: str) -> str:
        return (
            f"<!DOCTYPE html>\n<html>\n<head>\n"
            f"  <meta charset=\"{encoding}\">\n"
            f"  <title>{title}</title>\n</head>\n<body>\n<pre>"
        )

    def format_line(self, line_num: int, text: str, bookmark_note: str) -> str:
        bm_tag = f" <mark>[Закладка: {bookmark_note}]</mark>" if bookmark_note else ""
        return f"<span class='line' id='L{line_num}'>{line_num:02d}: {text}</span>{bm_tag}"

    def format_footer(self, total_lines: int) -> str:
        return f"</pre>\n<footer>Всього рядків: {total_lines}</footer>\n</body>\n</html>"


# 3. Конкретний клас №2: Експорт документа у формат Markdown
class MarkdownDocumentExporter(DocumentExportTemplate):
    def format_header(self, title: str, encoding: str) -> str:
        return f"# Документ: `{title}` (Кодування: `{encoding}`)\n\n```python"

    def format_line(self, line_num: int, text: str, bookmark_note: str) -> str:
        suffix = f"  # <-- [Закладка: {bookmark_note}]" if bookmark_note else ""
        return f"{line_num:02d} | {text}{suffix}"

    def format_footer(self, total_lines: int) -> str:
        return f"```\n> *Експортовано рядків: {total_lines}*"


# 4. Конкретний клас №3: Експорт у чистий вихідний файл Python із метаданими
class PythonSourceExporter(DocumentExportTemplate):
    def format_header(self, title: str, encoding: str) -> str:
        return f"# -*- coding: {encoding.lower()} -*-\n# Файл: {title}"

    def format_line(self, line_num: int, text: str, bookmark_note: str) -> str:
        if bookmark_note:
            return f"{text}  # [BOOKMARK L{line_num}: {bookmark_note}]"
        return text

    def format_footer(self, total_lines: int) -> str:
        return f"# --- Кінець файлу ({total_lines} рядків) ---"


if __name__ == "__main__":
    sample_code = "def compute_sum(a, b):\n    result = a + b\n    return result"
    sample_bookmarks = {2: "Перевірити переповнення"}

    # Використовуємо один і той самий шаблонний алгоритм для різних форматів і кодувань
    html_exporter = HtmlDocumentExporter()
    html_exporter.export_document("math_utils.py", sample_code, "UTF-8", sample_bookmarks)

    md_exporter = MarkdownDocumentExporter()
    md_exporter.export_document("math_utils.py", sample_code, "UTF-16", sample_bookmarks)

    py_exporter = PythonSourceExporter()
    py_exporter.export_document("math_utils.py", sample_code, "Windows-1251", sample_bookmarks)