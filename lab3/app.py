import os
import sys
import webbrowser

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lab2')))
from lab2_repository import (
    DatabaseConnection, TextDocument, Bookmark, Snippet,
    DocumentRepository, BookmarkRepository, SnippetRepository
)

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lab2', 'text_editor.db'))
db = DatabaseConnection(DB_PATH)
doc_repo = DocumentRepository(db)
bm_repo = BookmarkRepository(db)
snip_repo = SnippetRepository(db)

docs = doc_repo.get_all()
doc = docs[0]
bms = bm_repo.get_by_document(doc.id)
snips = snip_repo.get_all()

docs_html = "".join([f"<tr><td>{d.id}</td><td><b>{d.title}</b></td><td>{d.encoding}</td></tr>" for d in docs])
bms_html = "".join([f"<tr><td>{b.id}</td><td>Рядок {b.line_number}</td><td>{b.note}</td></tr>" for b in bms])
snips_html = "".join([f"<tr><td>{s.id}</td><td>{s.name}</td><td><code>{s.trigger_prefix}</code></td></tr>" for s in snips])

html = f"""<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="UTF-8">
<title>Текстовий редактор — Лабораторна №3</title>
<style>
  body {{ font-family: sans-serif; background: #f0f2f5; padding: 20px; }}
  .card {{ background: #fff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 16px; margin-bottom: 20px; }}
  h3 {{ margin-top: 0; color: #1e293b; border-bottom: 2px solid #3b82f6; padding-bottom: 6px; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 14px; }}
  th, td {{ border: 1px solid #cbd5e1; padding: 8px; text-align: left; }}
  th {{ background: #f8fafc; }}
  input, select, textarea {{ width: 100%; padding: 6px; margin-top: 4px; margin-bottom: 10px; box-sizing: border-box; }}
  textarea {{ height: 110px; background: #0f172a; color: #f8fafc; font-family: monospace; }}
  button {{ background: #2563eb; color: #fff; border: none; padding: 8px 14px; border-radius: 6px; cursor: pointer; }}
</style>
</head>
<body>

<div class="card">
  <h3>Візуальна Форма №1: MainEditorWindow (Редактор тексту, кодування та підсвічування)</h3>
  <div class="grid">
    <div>
      <b>Документи в SQLite (DocumentRepository):</b>
      <table><tr><th>ID</th><th>Файл</th><th>Кодування</th></tr>{docs_html}</table>
      <p><b>Перехід на рядок:</b> <input type="number" value="2" style="width:70px;"> <button>Перейти</button></p>
    </div>
    <div>
      <label>Назва файлу:</label><input value="{doc.title}">
      <label>Кодування:</label><select><option>{doc.encoding}</option><option>UTF-16</option><option>Windows-1251</option></select>
      <label>Текст програми ({doc.language}):</label>
      <textarea>{doc.content}</textarea>
      <button onclick="alert('Збережено в БД через DocumentRepository!')">Зберегти зміни в БД</button>
    </div>
  </div>
</div>

<div class="card">
  <h3>Візуальна Форма №2: SnippetBookmarkManager (Менеджер закладок та сніппетів у БД)</h3>
  <div class="grid">
    <div>
      <b>Закладки документа (BookmarkRepository):</b>
      <table><tr><th>ID</th><th>Рядок</th><th>Нотатка</th></tr>{bms_html}</table>
      <label>Нова закладка (Рядок / Опис):</label>
      <input placeholder="Рядок: 4 — Перевірка циклу">
      <button>Додати закладку в SQLite</button>
    </div>
    <div>
      <b>Сніппети коду (SnippetRepository):</b>
      <table><tr><th>ID</th><th>Назва</th><th>Тригер</th></tr>{snips_html}</table>
      <label>Новий сніппет (Тригер / Шаблон):</label>
      <input placeholder="tryex -> try...except">
      <button>Додати сніппет в SQLite</button>
    </div>
  </div>
</div>

</body>
</html>"""

out = os.path.join(os.path.dirname(__file__), "ui_forms.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)

webbrowser.open("file://" + os.path.abspath(out))
print("Готово! Візуальні форми відкрито у браузері.")