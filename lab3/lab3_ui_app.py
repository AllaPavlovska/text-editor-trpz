import os
import sys
import webbrowser
from threading import Timer
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Підключаємо наш модуль Repository та моделі з Лабораторної роботи №2
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lab2')))
from lab2_repository import (
    DatabaseConnection,
    TextDocument,
    Bookmark,
    Snippet,
    DocumentRepository,
    BookmarkRepository,
    SnippetRepository
)

# Ініціалізуємо БД та репозиторії
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lab2', 'text_editor.db'))
db = DatabaseConnection(DB_PATH)
doc_repo = DocumentRepository(db)
bm_repo = BookmarkRepository(db)
snip_repo = SnippetRepository(db)

# Додамо початкові дані, якщо база порожня
if not doc_repo.get_all():
    doc_id = doc_repo.add(TextDocument(
        id=None,
        title="editor_core.py",
        file_path="/Users/allapavlovska/projects/editor_core.py",
        content="def init_editor():\n    # Ініціалізація текстового редактора\n    encoding = 'UTF-8'\n    print('Editor started in', encoding)\n\nif __name__ == '__main__':\n    init_editor()",
        encoding="UTF-8",
        language="Python"
    ))
    bm_repo.add(Bookmark(id=None, document_id=doc_id, line_number=3, page_number=1, note="Налаштування кодування"))
    snip_repo.add(Snippet(id=None, name=" Цикл For", trigger_prefix="fori", code_template="for i in range(10):\n    print(i)", language="Python"))


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>Текстовий редактор — Лабораторна робота №3 (Варіант 3)</title>
    <style>
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { margin: 0; padding: 20px; background: #f0f2f5; color: #1c1e21; }
        .header { background: #1e293b; color: #fff; padding: 14px 20px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
        .header h2 { margin: 0; font-size: 18px; }
        .tabs { display: flex; gap: 10px; }
        .tab-btn { background: #334155; color: #fff; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; text-decoration: none; font-size: 14px; }
        .tab-btn.active { background: #3b82f6; }
        .window-card { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.06); overflow: hidden; margin-bottom: 20px; }
        .window-titlebar { background: #e2e8f0; padding: 10px 16px; font-weight: 700; font-size: 14px; color: #0f172a; border-bottom: 1px solid #cbd5e1; display: flex; align-items: center; gap: 8px; }
        .dots { display: flex; gap: 6px; margin-right: 8px; }
        .dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
        .dot.r { background: #ff5f56; } .dot.y { background: #ffbd2e; } .dot.g { background: #27c93f; }
        .window-body { padding: 18px; display: grid; grid-template-columns: 280px 1fr; gap: 20px; }
        .window-body-form2 { padding: 18px; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        label { display: block; font-size: 12px; font-weight: 600; color: #475569; margin-bottom: 4px; margin-top: 10px; }
        input, select, textarea { width: 100%; padding: 8px 10px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px; }
        textarea.code-area { font-family: "SF Mono", Menlo, monospace; height: 220px; background: #0f172a; color: #f8fafc; line-height: 1.5; padding: 12px; }
        .btn { background: #2563eb; color: white; border: none; padding: 9px 14px; border-radius: 6px; font-weight: 600; cursor: pointer; margin-top: 12px; font-size: 13px; }
        .btn-secondary { background: #475569; }
        .btn-danger { background: #dc2626; padding: 4px 8px; font-size: 11px; margin: 0; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }
        th, td { border: 1px solid #e2e8f0; padding: 8px 10px; text-align: left; }
        th { background: #f8fafc; color: #334155; }
        .status-bar { background: #f1f5f9; padding: 8px 16px; border-top: 1px solid #cbd5e1; font-size: 12px; color: #334155; display: flex; justify-content: space-between; }
        .badge { background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }
        .syntax-preview { background: #1e293b; color: #e2e8f0; padding: 12px; border-radius: 6px; font-family: monospace; font-size: 12px; white-space: pre-wrap; margin-top: 10px; border-left: 4px solid #3b82f6; }
        .kw { color: #c084fc; font-weight: bold; } .str { color: #86efac; } .com { color: #94a3b8; font-style: italic; }
    </style>
</head>
<body>

<div class="header">
    <h2>Текстовий редактор (Варіант 3) — Лабораторна робота №3</h2>
    <div class="tabs">
        <a href="/?view=form1&doc_id={current_doc_id}" class="tab-btn {active_form1}">Візуальна Форма №1: Головне вікно редактора</a>
        <a href="/?view=form2&doc_id={current_doc_id}" class="tab-btn {active_form2}">Візуальна Форма №2: Менеджер закладок і сніппетів</a>
    </div>
</div>

<!-- ФОРМА 1: ГОЛОВНЕ ВІКНО ТЕКСТОВОГО РЕДАКТОРА -->
<div class="window-card" style="display: {display_form1};">
    <div class="window-titlebar">
        <div class="dots"><span class="dot r"></span><span class="dot y"></span><span class="dot g"></span></div>
        Форма №1 — MainEditorWindow (Редагування документів, Кодування, Навігація та Синтаксис)
    </div>
    <div class="window-body">
        <div>
            <h4 style="margin-top:0;">Документи в БД (Repository):</h4>
            <table>
                <thead><tr><th>ID</th><th>Файл</th><th>Кодування</th><th>Дія</th></tr></thead>
                <tbody>
                    {docs_rows}
                </tbody>
            </table>

            <hr style="margin: 16px 0; border: 0; border-top: 1px solid #e2e8f0;">
            <h4 style="margin: 0 0 8px 0;">Швидкий перехід / Сніппет:</h4>
            <form method="GET" action="/">
                <input type="hidden" name="view" value="form1">
                <input type="hidden" name="doc_id" value="{current_doc_id}">
                <label>Перейти на рядок (Go to Line):</label>
                <div style="display:flex; gap:6px;">
                    <input type="number" name="goto_line" value="{goto_line}" min="1" placeholder="№ рядка">
                    <button type="submit" class="btn" style="margin:0;">Перейти</button>
                </div>
            </form>

            <form method="POST" action="/insert_snippet">
                <input type="hidden" name="doc_id" value="{current_doc_id}">
                <label>Вставити сніппет з БД:</label>
                <div style="display:flex; gap:6px;">
                    <select name="snippet_id">{snippets_options}</select>
                    <button type="submit" class="btn btn-secondary" style="margin:0;">Вставити</button>
                </div>
            </form>
        </div>

        <div>
            <form method="POST" action="/save_document">
                <input type="hidden" name="doc_id" value="{current_doc_id}">
                <div style="display: grid; grid-template-columns: 1fr 1fr 160px 140px; gap: 10px;">
                    <div>
                        <label>Назва файлу:</label>
                        <input type="text" name="title" value="{doc_title}" required>
                    </div>
                    <div>
                        <label>Шлях у файловій системі:</label>
                        <input type="text" name="file_path" value="{doc_path}" required>
                    </div>
                    <div>
                        <label>Кодування файлу:</label>
                        <select name="encoding">
                            <option value="UTF-8" {enc_utf8}>UTF-8</option>
                            <option value="UTF-16" {enc_utf16}>UTF-16</option>
                            <option value="Windows-1251" {enc_win1251}>Windows-1251</option>
                            <option value="ASCII" {enc_ascii}>ASCII</option>
                        </select>
                    </div>
                    <div>
                        <label>Підсвічування мови:</label>
                        <select name="language">
                            <option value="Python" {lang_py}>Python</option>
                            <option value="C#" {lang_cs}>C#</option>
                            <option value="HTML" {lang_html}>HTML/XML</option>
                        </select>
                    </div>
                </div>

                <label>Вміст текстового буфера (Редагування):</label>
                <textarea class="code-area" name="content">{doc_content}</textarea>

                <div style="display:flex; gap:10px;">
                    <button type="submit" name="action" value="update" class="btn">Зберегти зміни в БД (Update)</button>
                    <button type="submit" name="action" value="create" class="btn btn-secondary">Зберегти як новий документ (Insert)</button>
                </div>
            </form>

            <label style="margin-top:14px;">Попередній перегляд підсвічування синтаксису та активного рядка:</label>
            <div class="syntax-preview">{highlighted_preview}</div>
        </div>
    </div>
    <div class="status-bar">
        <span>Статус: <b>{status_msg}</b></span>
        <span>Активний документ ID: <b>{current_doc_id}</b> | Кодування: <span class="badge">{doc_encoding}</span> | Рядків: <b>{line_count}</b> | Закладок у документі: <b>{bm_count}</b></span>
    </div>
</div>

<!-- ФОРМА 2: МЕНЕДЖЕР ЗАКЛАДОК ТА СНІППЕТІВ -->
<div class="window-card" style="display: {display_form2};">
    <div class="window-titlebar">
        <div class="dots"><span class="dot r"></span><span class="dot y"></span><span class="dot g"></span></div>
        Форма №2 — SnippetBookmarkManagerForm (Керування закладками документа та базою сніппетів у SQLite)
    </div>
    <div class="window-body-form2">
        <!-- Ліва колонка: Закладки -->
        <div>
            <h4 style="margin-top:0;">Закладки документа «{doc_title}» (BookmarkRepository)</h4>
            <table>
                <thead><tr><th>ID</th><th>Рядок</th><th>Сторінка</th><th>Коментар (Нотатка)</th><th>Дія</th></tr></thead>
                <tbody>
                    {bookmarks_rows}
                </tbody>
            </table>

            <form method="POST" action="/add_bookmark" style="background:#f8fafc; padding:12px; border-radius:6px; margin-top:14px; border:1px solid #e2e8f0;">
                <h5 style="margin:0 0 6px 0;">Додати нову закладку в БД:</h5>
                <input type="hidden" name="document_id" value="{current_doc_id}">
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                    <div><label>Номер рядка:</label><input type="number" name="line_number" value="1" min="1" required></div>
                    <div><label>Номер сторінки:</label><input type="number" name="page_number" value="1" min="1" required></div>
                </div>
                <label>Опис / Нотатка закладки:</label>
                <input type="text" name="note" placeholder="Наприклад: Перевірити алгоритм кодування" required>
                <button type="submit" class="btn">Додати закладку в SQLite</button>
            </form>
        </div>

        <!-- Права колонка: Сніппети -->
        <div>
            <h4 style="margin-top:0;">Бібліотека сніппетів коду (SnippetRepository)</h4>
            <table>
                <thead><tr><th>ID</th><th>Назва</th><th>Тригер</th><th>Мова</th><th>Шаблон коду</th><th>Дія</th></tr></thead>
                <tbody>
                    {snippets_rows}
                </tbody>
            </table>

            <form method="POST" action="/add_snippet" style="background:#f8fafc; padding:12px; border-radius:6px; margin-top:14px; border:1px solid #e2e8f0;">
                <h5 style="margin:0 0 6px 0;">Додати новий сніппет в БД:</h5>
                <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:10px;">
                    <div><label>Назва:</label><input type="text" name="name" placeholder="Try-Except блок" required></div>
                    <div><label>Тригер (скорочення):</label><input type="text" name="trigger_prefix" placeholder="tryex" required></div>
                    <div><label>Мова:</label><input type="text" name="language" value="Python" required></div>
                </div>
                <label>Тіло шаблону коду (Template):</label>
                <textarea name="code_template" rows="3" required placeholder="try:\n    pass\nexcept Exception as e:\n    print(e)"></textarea>
                <button type="submit" class="btn">Зберегти сніппет в SQLite</button>
            </form>
        </div>
    </div>
    <div class="status-bar">
        <span>Підключено до БД: <b>{db_path}</b></span>
        <span>Усі зміни автоматично зберігаються через шаблон <b>Repository</b></span>
    </div>
</div>

</body>
</html>
"""

def highlight_code(content: str, goto_line: int = 0) -> str:
    lines = content.splitlines()
    result = []
    keywords = ["def ", "return", "if ", "else:", "for ", "in ", "import ", "from ", "class ", "print"]
    for idx, line in enumerate(lines, start=1):
        safe_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if safe_line.strip().startswith("#"):
            safe_line = f'<span class="com">{safe_line}</span>'
        else:
            for kw in keywords:
                safe_line = safe_line.replace(kw, f'<span class="kw">{kw}</span>')
        prefix = f"👉 {idx:02d} | " if idx == goto_line else f"   {idx:02d} | "
        if idx == goto_line:
            safe_line = f'<span style="background:#1d4ed8; color:#fff; padding:1px 6px; border-radius:3px;">{safe_line}</span>'
        result.append(prefix + safe_line)
    return "\n".join(result)


class EditorUIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        view = params.get("view", ["form1"])[0]
        status_msg = params.get("msg", ["Готово до роботи (повний цикл UI <-> Repository <-> SQLite)"])[0]
        goto_line = int(params.get("goto_line", ["0"])[0] or 0)

        docs = doc_repo.get_all()
        current_doc_id = int(params.get("doc_id", [docs[0].id if docs else 1])[0])
        current_doc = doc_repo.get_by_id(current_doc_id) or (docs[0] if docs else TextDocument(1, "new.py", "/tmp/new.py", "", "UTF-8", "Python"))

        bookmarks = bm_repo.get_by_document(current_doc.id)
        snippets = snip_repo.get_all()

        docs_rows = "".join([
            f"<tr style='background:{'#eff6ff' if d.id == current_doc.id else 'transparent'}'>"
            f"<td>{d.id}</td><td><a href='/?view=form1&doc_id={d.id}'><b>{d.title}</b></a></td>"
            f"<td><span class='badge'>{d.encoding}</span></td>"
            f"<td><a href='/?view=form2&doc_id={d.id}'>Закладки</a></td></tr>"
            for d in docs
        ])

        bookmarks_rows = "".join([
            f"<tr><td>{b.id}</td><td><a href='/?view=form1&doc_id={current_doc.id}&goto_line={b.line_number}'>Рядок {b.line_number}</a></td>"
            f"<td>Стор. {b.page_number}</td><td>{b.note}</td>"
            f"<td><form method='POST' action='/delete_bookmark' style='margin:0;'>"
            f"<input type='hidden' name='bm_id' value='{b.id}'><input type='hidden' name='doc_id' value='{current_doc.id}'>"
            f"<button class='btn btn-danger'>Видалити</button></form></td></tr>"
            for b in bookmarks
        ]) or "<tr><td colspan='5'>Закладок ще немає</td></tr>"

        snippets_rows = "".join([
            f"<tr><td>{s.id}</td><td><b>{s.name}</b></td><td><code>{s.trigger_prefix}</code></td><td>{s.language}</td>"
            f"<td><pre style='margin:0;font-size:11px;'>{s.code_template}</pre></td>"
            f"<td><form method='POST' action='/delete_snippet' style='margin:0;'>"
            f"<input type='hidden' name='snip_id' value='{s.id}'><input type='hidden' name='doc_id' value='{current_doc.id}'>"
            f"<button class='btn btn-danger'>Видалити</button></form></td></tr>"
            for s in snippets
        ]) or "<tr><td colspan='6'>Сніппетів ще немає</td></tr>"

        snippets_options = "".join([f"<option value='{s.id}'>{s.trigger_prefix} ({s.name})</option>" for s in snippets])

        html = HTML_TEMPLATE.format(
            current_doc_id=current_doc.id,
            active_form1="active" if view == "form1" else "",
            active_form2="active" if view == "form2" else "",
            display_form1="block" if view == "form1" else "none",
            display_form2="block" if view == "form2" else "none",
            docs_rows=docs_rows,
            goto_line=goto_line if goto_line > 0 else "",
            snippets_options=snippets_options,
            doc_title=current_doc.title,
            doc_path=current_doc.file_path,
            doc_content=current_doc.content,
            doc_encoding=current_doc.encoding,
            enc_utf8="selected" if current_doc.encoding == "UTF-8" else "",
            enc_utf16="selected" if current_doc.encoding == "UTF-16" else "",
            enc_win1251="selected" if current_doc.encoding == "Windows-1251" else "",
            enc_ascii="selected" if current_doc.encoding == "ASCII" else "",
            lang_py="selected" if current_doc.language == "Python" else "",
            lang_cs="selected" if current_doc.language == "C#" else "",
            lang_html="selected" if current_doc.language == "HTML" else "",
            highlighted_preview=highlight_code(current_doc.content, goto_line),
            status_msg=status_msg,
            line_count=current_doc.get_line_count(),
            bm_count=len(bookmarks),
            bookmarks_rows=bookmarks_rows,
            snippets_rows=snippets_rows,
            db_path=DB_PATH
        )

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        data = {k: v[0] for k, v in parse_qs(body, keep_blank_values=True).items()}

        if self.path == "/save_document":
            doc_id = int(data.get("doc_id", 1))
            action = data.get("action", "update")
            doc = TextDocument(
                id=doc_id if action == "update" else None,
                title=data.get("title", "untitled.py"),
                file_path=data.get("file_path", "/tmp/untitled.py"),
                content=data.get("content", ""),
                encoding=data.get("encoding", "UTF-8"),
                language=data.get("language", "Python")
            )
            if action == "create":
                doc_id = doc_repo.add(doc)
                msg = f"Створено новий документ ID={doc_id} у БД"
            else:
                doc_repo.update(doc)
                msg = f"Документ ID={doc_id} оновлено в БД"
            self.redirect(f"/?view=form1&doc_id={doc_id}&msg={msg}")

        elif self.path == "/insert_snippet":
            doc_id = int(data.get("doc_id", 1))
            snip_id = int(data.get("snippet_id", 1))
            doc = doc_repo.get_by_id(doc_id)
            snip = snip_repo.get_by_id(snip_id)
            if doc and snip:
                doc.content = doc.content.rstrip() + "\n\n" + snip.code_template
                doc_repo.update(doc)
            self.redirect(f"/?view=form1&doc_id={doc_id}&msg=Вставлено сніппет '{snip.trigger_prefix}'")

        elif self.path == "/add_bookmark":
            doc_id = int(data.get("document_id", 1))
            bm = Bookmark(
                id=None,
                document_id=doc_id,
                line_number=int(data.get("line_number", 1)),
                page_number=int(data.get("page_number", 1)),
                note=data.get("note", "")
            )
            bm_repo.add(bm)
            self.redirect(f"/?view=form2&doc_id={doc_id}&msg=Закладку збережено в БД")

        elif self.path == "/delete_bookmark":
            bm_id = int(data.get("bm_id", 0))
            doc_id = int(data.get("doc_id", 1))
            bm_repo.delete(bm_id)
            self.redirect(f"/?view=form2&doc_id={doc_id}&msg=Закладку видалено з БД")

        elif self.path == "/add_snippet":
            doc_id = int(data.get("doc_id", 1))
            snip = Snippet(
                id=None,
                name=data.get("name", "Snippet"),
                trigger_prefix=data.get("trigger_prefix", "snip"),
                code_template=data.get("code_template", ""),
                language=data.get("language", "Python")
            )
            snip_repo.add(snip)
            self.redirect(f"/?view=form2&doc_id={doc_id}&msg=Сніппет додано в БД")

        elif self.path == "/delete_snippet":
            snip_id = int(data.get("snip_id", 0))
            doc_id = int(data.get("doc_id", 1))
            snip_repo.delete(snip_id)
            self.redirect(f"/?view=form2&doc_id={doc_id}&msg=Сніппет видалено з БД")

    def redirect(self, location: str):
        from urllib.parse import quote
        parts = location.split("&msg=")
        if len(parts) == 2:
            location = parts[0] + "&msg=" + quote(parts[1])
        self.send_response(303)
        self.send_header("Location", location)
        self.end_headers()


if __name__ == "__main__":
    PORT = 8765
    print(f"=== Запуск UI Текстового редактора (Лабораторна робота №3) ===")
    print(f"[DB] Підключено базу даних: {DB_PATH}")
    print(f"[UI] Відкрийте у браузері: http://127.0.0.1:{PORT}")
    print("Для зупинки сервера натисніть Ctrl+C у терміналі.")
    Timer(0.8, lambda: webbrowser.open(f"http://127.0.0.1:{PORT}")).start()
    server = HTTPServer(("127.0.0.1", PORT), EditorUIHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[UI] Роботу завершено.")
EOF
