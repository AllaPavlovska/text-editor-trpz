from abc import ABC, abstractmethod
from typing import List


# 1. Інтерфейс Команди (Command)
class ICommand(ABC):
    @abstractmethod
    def execute(self) -> None:
        pass

    @abstractmethod
    def undo(self) -> None:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass


# 2. Одержувач (Receiver) — Текстовий буфер редактора
class TextBufferReceiver:
    def __init__(self, title: str = "main.py"):
        self.title = title
        self._content = ""

    def insert_at_end(self, text: str) -> None:
        self._content += text

    def remove_last_chars(self, count: int) -> None:
        if count > 0:
            self._content = self._content[:-count]

    def get_content(self) -> str:
        return self._content


# 3. Конкретна команда №1: Вставка тексту
class InsertTextCommand(ICommand):
    def __init__(self, receiver: TextBufferReceiver, text: str):
        self._receiver = receiver
        self._text = text

    def execute(self) -> None:
        self._receiver.insert_at_end(self._text)

    def undo(self) -> None:
        self._receiver.remove_last_chars(len(self._text))

    def get_name(self) -> str:
        return f"InsertText({repr(self._text)})"


# 4. Конкретна команда №2: Розгортання сніппета коду за тригером
class InsertSnippetCommand(ICommand):
    def __init__(self, receiver: TextBufferReceiver, trigger: str, template: str):
        self._receiver = receiver
        self._trigger = trigger
        self._formatted = f"\n# [Snippet: {trigger}]\n{template}\n"

    def execute(self) -> None:
        self._receiver.insert_at_end(self._formatted)

    def undo(self) -> None:
        self._receiver.remove_last_chars(len(self._formatted))

    def get_name(self) -> str:
        return f"InsertSnippet(trigger='{self._trigger}')"


# 5. Конкретна команда №3: Макрос (послідовність команд)
class MacroCommand(ICommand):
    def __init__(self, name: str):
        self._name = name
        self._commands: List[ICommand] = []

    def add_command(self, cmd: ICommand) -> None:
        self._commands.append(cmd)

    def execute(self) -> None:
        for cmd in self._commands:
            cmd.execute()

    def undo(self) -> None:
        for cmd in reversed(self._commands):
            cmd.undo()

    def get_name(self) -> str:
        return f"MacroCommand('{self._name}', steps={len(self._commands)})"


# 6. Ініціатор (Invoker) — Контролер команд і журнал Undo редактора
class EditorInvoker:
    def __init__(self):
        self._history: List[ICommand] = []

    def execute_command(self, cmd: ICommand) -> None:
        print(f"[Invoker] Виконання команди: {cmd.get_name()}")
        cmd.execute()
        self._history.append(cmd)

    def undo_last(self) -> None:
        if not self._history:
            print("[Invoker] Історія порожня, нічого скасовувати.")
            return
        cmd = self._history.pop()
        print(f"[Invoker] Скасування (Undo): {cmd.get_name()}")
        cmd.undo()


if __name__ == "__main__":
    buffer = TextBufferReceiver("module.py")
    invoker = EditorInvoker()

    # 1. Виконуємо просту команду вставки заголовка
    cmd1 = InsertTextCommand(buffer, "# -*- coding: utf-8 -*-\n")
    invoker.execute_command(cmd1)

    # 2. Виконуємо команду вставки сніппета
    cmd2 = InsertSnippetCommand(buffer, "defmain", "def main():\n    print('Hello KPI!')")
    invoker.execute_command(cmd2)

    # 3. Створюємо та виконуємо макрос із двох команд
    macro = MacroCommand("Автопідпис і виклик main")
    macro.add_command(InsertTextCommand(buffer, "\n# Автор: Павловська А. В.\n"))
    macro.add_command(InsertTextCommand(buffer, "if __name__ == '__main__':\n    main()\n"))
    invoker.execute_command(macro)

    print("\n=== Буфер документа після виконання команд та макросу ===")
    print(buffer.get_content())

    # 4. Демонструємо скасування (Undo) макросу однією дією
    invoker.undo_last()
    print("=== Буфер документа після Undo макросу ===")
    print(buffer.get_content())