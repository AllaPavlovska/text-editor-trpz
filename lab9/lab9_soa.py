import base64
import hashlib
import hmac
import json
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Any


# =====================================================================
# 1. MIDDLEWARE: Двостороннє шифрування та Менеджер токенів автентифікації
# =====================================================================
class BidirectionalCipher:
    """Забезпечує двостороннє симетричне шифрування/дешифрування трафіку між клієнтом і SOA-сервісом."""

    def __init__(self, secret_key: str):
        self._key = hashlib.sha256(secret_key.encode("utf-8")).digest()

    def encrypt(self, plain_text: str) -> str:
        raw = plain_text.encode("utf-8")
        xored = bytes([b ^ self._key[i % len(self._key)] for i, b in enumerate(raw)])
        return base64.urlsafe_b64encode(xored).decode("ascii")

    def decrypt(self, cipher_b64: str) -> str:
        xored = base64.urlsafe_b64decode(cipher_b64.encode("ascii"))
        raw = bytes([b ^ self._key[i % len(self._key)] for i, b in enumerate(xored)])
        return raw.decode("utf-8")


class AuthTokenManager:
    """Генерація та перевірка підписаних токенів автентифікації (HMAC-SHA256)."""

    def __init__(self, secret: str):
        self._secret = secret.encode("utf-8")

    def issue_token(self, username: str) -> str:
        payload = base64.urlsafe_b64encode(username.encode("utf-8")).decode("ascii")
        signature = hmac.new(self._secret, payload.encode("ascii"), hashlib.sha256).hexdigest()[:24]
        return f"{payload}.{signature}"

    def verify_token(self, token: str) -> bool:
        if not token or "." not in token:
            return False
        payload, sig = token.split(".", 1)
        expected = hmac.new(self._secret, payload.encode("ascii"), hashlib.sha256).hexdigest()[:24]
        return hmac.compare_digest(sig, expected)


# =====================================================================
# 2. СЕРВЕРНА ЧАСТИНА: Локальний SOA Web Service текстового редактора
# =====================================================================
SHARED_SECRET = "KPI_TRPZ_VARIANT3_SECRET_KEY_2026"
cipher_engine = BidirectionalCipher(SHARED_SECRET)
token_manager = AuthTokenManager(SHARED_SECRET)

CLOUD_SNIPPETS = [
    {"name": "For Loop", "trigger": "fori", "code": "for i in range(n):\n    pass", "lang": "Python"},
    {"name": "Main Guard", "trigger": "ifmain", "code": "if __name__ == '__main__':\n    main()", "lang": "Python"},
]


class EditorSoaRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Вимикаємо стандартний шум HTTP-логів

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length).decode("utf-8")
        req_json = json.loads(raw_body)

        # Ендпоінт 1: Автентифікація клієнта та видача токена
        if self.path == "/api/auth/login":
            decrypted = json.loads(cipher_engine.decrypt(req_json["payload"]))
            user = decrypted.get("username")
            token = token_manager.issue_token(user)
            print(f"[SOA Service] Автентифіковано користувача '{user}'. Видано токен: {token}")
            self._send_encrypted({"status": "OK", "token": token})
            return

        # Перевірка Bearer-токена для захищених сервісів
        auth_header = self.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "")
        if not token_manager.verify_token(token):
            self._send_encrypted({"status": "ERROR", "message": "Invalid Auth Token"}, code=401)
            return

        decrypted_data = json.loads(cipher_engine.decrypt(req_json["payload"]))

        # Ендпоінт 2: Сервіс синхронізації сніппетів коду з хмари
        if self.path == "/api/snippets/sync":
            lang = decrypted_data.get("language", "Python")
            matched = [s for s in CLOUD_SNIPPETS if s["lang"] == lang]
            print(f"[SOA Service] Запит сніппетів ({lang}) з валідним токеном. Знайдено: {len(matched)}")
            self._send_encrypted({"status": "OK", "snippets": matched})

        # Ендпоінт 3: Сервіс віддаленої перевірки кодування та закладок документа
        elif self.path == "/api/document/validate-encoding":
            title = decrypted_data["title"]
            content = decrypted_data["content"]
            encoding = decrypted_data["encoding"]
            byte_len = len(content.encode(encoding))
            print(f"[SOA Service] Перевірено кодування '{encoding}' для файлу '{title}' ({byte_len} байт)")
            self._send_encrypted({
                "status": "OK",
                "file": title,
                "encoding": encoding,
                "byte_size": byte_len,
                "lines": len(content.splitlines()),
                "verified_by": "EditorEncodingMicroservice_v1"
            })

    def _send_encrypted(self, response_dict: Dict[str, Any], code: int = 200):
        plain_json = json.dumps(response_dict, ensure_ascii=False)
        encrypted_payload = cipher_engine.encrypt(plain_json)
        out_bytes = json.dumps({"payload": encrypted_payload}).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(out_bytes)))
        self.end_headers()
        self.wfile.write(out_bytes)


# =====================================================================
# 3. КЛІЄНТСЬКА ЧАСТИНА: Клієнт Текстового редактора
# =====================================================================
class TextEditorSoaClient:
    def __init__(self, base_url: str, cipher: BidirectionalCipher):
        self._base_url = base_url
        self._cipher = cipher
        self._token: str = ""

    def _post_encrypted(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        plain_json = json.dumps(data, ensure_ascii=False)
        encrypted_payload = self._cipher.encrypt(plain_json)
        print(f"\n[Client -> SOA] POST {endpoint} | Зашифрований пакет: {encrypted_payload[:38]}...")

        body = json.dumps({"payload": encrypted_payload}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        req = urllib.request.Request(f"{self._base_url}{endpoint}", data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            resp_body = json.loads(resp.read().decode("utf-8"))
            decrypted_json = self._cipher.decrypt(resp_body["payload"])
            print(f"[SOA -> Client] Розшифрована відповідь сервісу: {decrypted_json}")
            return json.loads(decrypted_json)

    def login(self, username: str, password: str) -> None:
        res = self._post_encrypted("/api/auth/login", {"username": username, "password": password})
        self._token = res.get("token", "")

    def sync_snippets(self, language: str) -> None:
        self._post_encrypted("/api/snippets/sync", {"language": language})

    def validate_document_encoding(self, title: str, content: str, encoding: str) -> None:
        self._post_encrypted(
            "/api/document/validate-encoding",
            {"title": title, "content": content, "encoding": encoding}
        )


if __name__ == "__main__":
    # Піднімаємо Web Service на вільному локальному порті автоматично
    server = HTTPServer(("127.0.0.1", 0), EditorSoaRequestHandler)
    port = server.server_port
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"=== Локальний SOA Web Service запущено на http://127.0.0.1:{port} ===")

    # Демонстрація роботи клієнта текстового редактора з SOA-сервісом
    client = TextEditorSoaClient(f"http://127.0.0.1:{port}", cipher_engine)
    client.login("alla_pavlovska", "kpi_2026_pass")
    client.sync_snippets("Python")
    client.validate_document_encoding(
        title="editor_core.py",
        content="# -*- coding: utf-8 -*-\ndef run():\n    print('SOA Works!')",
        encoding="UTF-8"
    )

    server.shutdown()
    print("\n=== Сеанс SOA завершено успішно ===")