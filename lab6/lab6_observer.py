from abc import ABC, abstractmethod
from typing import List, Dict


# 1. Інтерфейс Спостерігача (Observer)
class IDocumentObserver(ABC):
    @abstractmethod
    def update(self, subject: "TextDocumentSubject", event_type: str) -> None:
        pass


# 2. Інтерфейс Суб'єкта / Видавця (Subject)
class IDocumentSubject(ABC):
    @abstractmethod
    def attach(self, observer: IDocumentObserver) -> None:
        pass

    @abstractmethod
    def detach(self, observer: IDocumentObserver) -> None:
        pass

    @abstractmethod
    def notify(self, event_type: str) -> None:
        pass


# 3. Конкретний Суб'єкт (ConcreteSubject) — Документ текстового редактора
class TextDocumentSubject(IDocumentSubject):
    def __init__(self, title: str, content: str, encoding: str = "UTF-8"):
        self._observers: List[IDocumentObserver] = []
        self.title = title
        self.content = content
        self.encoding = encoding
        self.current_line = 1
        self.is_modified = False

    def attach(self, observer: IDocumentObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)
            print(f"[Subject] Підписано спостерігача: {observer.__class__.__name__}")

    def detach(self, observer: IDocumentObserver) -> None:
        if observer in self._observers:
            self._observers.remove(observer)
            print(f"[Subject] Відписано спостерігача: {observer.__class__.__name__}")

    def notify(self, event_type: str) -> None:
        for observer in self._observers:
            observer.update(self, event_type)

    def edit_content(self, new_text: str) -> None:
        print(f"\n>>> Подія в редакторі: Зміна тексту в документі '{self.title}'")
        self.content = new_text
        self.is_modified = True
        self.notify("CONTENT_CHANGED")

    def go_to_line(self, line_number: int) -> None:
        print(f"\n>>> Подія в редакторі: Перехід на рядок №{line_number}")
        self.current_line = line_number
        self.notify("CURSOR_MOVED")

    def change_encoding(self, new_encoding: str) -> None:
        print(f"\n>>> Подія в редакторі: Зміна кодування на '{new_encoding}'")
        self.encoding = new_encoding
        self.is_modified = True
        self.notify("ENCODING_CHANGED")

    def get_line_count(self) -> int:
        return len(self.content.splitlines()) or 1


# 4. Конкретний Спостерігач №1: Рядок стану редактора (StatusBarObserver)
class StatusBarObserver(IDocumentObserver):
    def update(self, subject: TextDocumentSubject, event_type: str) -> None:
        lines = subject.get_line_count()
        chars = len(subject.content)
        mod_flag = "*" if subject.is_modified else ""
        print(
            f"  [StatusBar UI] Файл: {subject.title}{mod_flag} | "
            f"Рядок: {subject.current_line}/{lines} | "
            f"Символів: {chars} | Кодування: {subject.encoding}"
        )


# 5. Конкретний Спостерігач №2: Менеджер закладок (BookmarkTrackerObserver)
class BookmarkTrackerObserver(IDocumentObserver):
    def __init__(self, bookmarks: Dict[int, str]):
        self._bookmarks = bookmarks

    def update(self, subject: TextDocumentSubject, event_type: str) -> None:
        if event_type == "CURSOR_MOVED":
            if subject.current_line in self._bookmarks:
                note = self._bookmarks[subject.current_line]
                print(f"  [Bookmarks] УВАГА! На рядку {subject.current_line} знайдено закладку: '{note}'")
            else:
                print(f"  [Bookmarks] На рядку {subject.current_line} закладок немає.")
        elif event_type == "CONTENT_CHANGED":
            print(f"  [Bookmarks] Перевірено цілісність {len(self._bookmarks)} закладок після редагування.")


# 6. Конкретний Спостерігач №3: Служба автозбереження (AutoSaveObserver)
class AutoSaveObserver(IDocumentObserver):
    def __init__(self):
        self._save_count = 0

    def update(self, subject: TextDocumentSubject, event_type: str) -> None:
        if event_type in ("CONTENT_CHANGED", "ENCODING_CHANGED") and subject.is_modified:
            self._save_count += 1
            print(
                f"  [AutoSave] Автозбереження #{self._save_count}: резервну копію '{subject.title}' "
                f"записано у кодуванні {subject.encoding}."
            )


if __name__ == "__main__":
    # Створюємо видавця (активний документ у редакторі)
    doc = TextDocumentSubject(
        title="app_controller.py",
        content="import sys\n\ndef start():\n    print('Running...')\n",
        encoding="UTF-8"
    )

    # Створюємо спостерігачів та підписуємо їх на події документа
    status_bar = StatusBarObserver()
    bookmark_tracker = BookmarkTrackerObserver({3: "Початок функції start()"})
    auto_save = AutoSaveObserver()

    doc.attach(status_bar)
    doc.attach(bookmark_tracker)
    doc.attach(auto_save)

    # Моделюємо дії користувача в текстовому редакторі
    doc.go_to_line(3)
    doc.edit_content("import sys\n\ndef start():\n    print('Running KPI Editor...')\n    return 0\n")
    doc.change_encoding("UTF-16")

    # Відписуємо автозбереження і перевіряємо подальшу роботу
    print()
    doc.detach(auto_save)
    doc.go_to_line(5)