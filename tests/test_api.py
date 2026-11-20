"""Pruebas controladas de la API: ninguna llega al proveedor real.

Ejecutar:  python -m unittest discover -s tests -t . -v
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import openai
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from api import config
from api.app import app
from api.config import API_KEY_VARIABLE, Settings
from api.llm import get_chat_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FAKE_KEY = "sk-test-SECRETO-123456"
ORIGIN_OK = ("http://localhost:8000", "http://127.0.0.1:8000")
ORIGIN_FOREIGN = "http://evil.example.com"
FAKE_REQUEST = httpx.Request("POST", "https://proveedor.invalid/v1/chat/completions")


class LogCollector(logging.Handler):
    """Guarda todo lo registrado para comprobar que no contiene secretos."""

    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(self.format(record))


def status_error(cls, status: int, body: dict | None = None):
    """Crea un error del SDK de OpenAI con texto que intenta filtrar la clave."""
    response = httpx.Response(status, request=FAKE_REQUEST)
    return cls(f"detalle con {FAKE_KEY}", response=response, body=body)


class ApiTestCase(unittest.TestCase):
    """Base: clave falsa, .env inexistente, modelo simulado y red real bloqueada."""

    def setUp(self) -> None:
        env = patch.dict(os.environ, {API_KEY_VARIABLE: FAKE_KEY})
        env.start()
        self.addCleanup(env.stop)

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        env_file = patch.object(config, "ENV_FILE", Path(tmp.name) / "no-existe.env")
        env_file.start()
        self.addCleanup(env_file.stop)

        # Cualquier salida HTTP real hace fallar la prueba.
        self.network = patch.object(
            httpx.AsyncClient,
            "send",
            new_callable=AsyncMock,
            side_effect=AssertionError("llamada de red real bloqueada"),
        )
        self.network_mock = self.network.start()
        self.addCleanup(self.network.stop)

        self.model = patch.object(
            ChatOpenAI,
            "ainvoke",
            new_callable=AsyncMock,
            return_value=AIMessage(content="respuesta simulada"),
        )
        self.model_mock = self.model.start()
        self.addCleanup(self.model.stop)

        self.logs = LogCollector()
        logging.getLogger().addHandler(self.logs)
        self.addCleanup(logging.getLogger().removeHandler, self.logs)

        get_chat_client.cache_clear()
        self.client = TestClient(app)

    def remove_key(self) -> None:
        os.environ.pop(API_KEY_VARIABLE, None)

    def sent_messages(self) -> list[tuple[str, str]]:
        """Mensajes entregados al modelo en la única llamada: (rol, texto)."""
        self.assertEqual(self.model_mock.await_count, 1)
        messages = self.model_mock.await_args.args[0]
        return [(message.type, message.content) for message in messages]

    def assert_error(self, response, status: int, code: str) -> dict:
        self.assertEqual(response.status_code, status, response.text)
        body = response.json()
        self.assertEqual(list(body), ["error"])
        self.assertEqual(sorted(body["error"]), ["code", "message"])
        self.assertEqual(body["error"]["code"], code)
        self.assertTrue(body["error"]["message"])
        return body

    def assert_no_secret(self, response=None) -> None:
        if response is not None:
            self.assertNotIn(FAKE_KEY, response.text)
            self.assertNotIn("SECRETO", json.dumps(dict(response.headers)))
        self.assertNotIn(FAKE_KEY, "\n".join(self.logs.lines))


class HealthTests(ApiTestCase):
    def test_health_with_key(self) -> None:
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "RAGLAB"})
        self.model_mock.assert_not_awaited()
        self.network_mock.assert_not_awaited()

    def test_health_without_key(self) -> None:
        self.remove_key()
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "RAGLAB"})
        self.model_mock.assert_not_awaited()


class ChatSuccessTests(ApiTestCase):
    def test_without_history_uses_default(self) -> None:
        response = self.client.post("/api/chat", json={"question": "Hola"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"answer": "respuesta simulada", "sources": []}
        )
        self.assertEqual(self.sent_messages(), [("human", "Hola")])

    def test_empty_history_equals_no_history(self) -> None:
        response = self.client.post("/api/chat", json={"question": "Hola", "history": []})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.sent_messages(), [("human", "Hola")])

    def test_history_order_and_current_question_once(self) -> None:
        history = [
            {"user": "u1", "assistant": "a1"},
            {"user": "u2", "assistant": "a2"},
        ]
        response = self.client.post(
            "/api/chat", json={"question": "actual", "history": history}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.sent_messages(),
            [
                ("human", "u1"),
                ("ai", "a1"),
                ("human", "u2"),
                ("ai", "a2"),
                ("human", "actual"),
            ],
        )

    def test_no_shared_history_between_requests(self) -> None:
        self.client.post(
            "/api/chat",
            json={"question": "q1", "history": [{"user": "x", "assistant": "y"}]},
        )
        self.client.post("/api/chat", json={"question": "q2"})
        second_call = self.model_mock.await_args_list[1].args[0]
        self.assertEqual([m.content for m in second_call], ["q2"])

    def test_texts_are_trimmed(self) -> None:
        response = self.client.post(
            "/api/chat",
            json={
                "question": "  pregunta \n",
                "history": [{"user": "  u ", "assistant": "\ta\t"}],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.sent_messages(), [("human", "u"), ("ai", "a"), ("human", "pregunta")]
        )

    def test_answer_is_trimmed(self) -> None:
        self.model_mock.return_value = AIMessage(content="  hecho  \n")
        response = self.client.post("/api/chat", json={"question": "q"})
        self.assertEqual(response.json()["answer"], "hecho")

    def test_limits_accepted_ten_turns_and_8000_chars(self) -> None:
        text = "x" * 8000
        history = [{"user": text, "assistant": text} for _ in range(10)]
        response = self.client.post(
            "/api/chat", json={"question": text, "history": history}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.sent_messages()), 21)

    def test_length_counted_after_trimming(self) -> None:
        text = "  " + "x" * 8000 + "  "
        response = self.client.post("/api/chat", json={"question": text})
        self.assertEqual(response.status_code, 200)


class ChatValidationTests(ApiTestCase):
    def assert_rejected(self, payload=None, *, content: bytes | None = None) -> None:
        # Sin clave: si la validación no fuera primero, se vería un 503.
        self.remove_key()
        if content is None:
            response = self.client.post("/api/chat", json=payload)
        else:
            response = self.client.post(
                "/api/chat", content=content, headers={"Content-Type": "application/json"}
            )
        self.assert_error(response, 422, "validation_error")
        self.model_mock.assert_not_awaited()
        self.network_mock.assert_not_awaited()

    def test_rejections(self) -> None:
        turn = {"user": "u", "assistant": "a"}
        cases = {
            "11 turnos": {"question": "q", "history": [turn] * 11},
            "pregunta 8001": {"question": "x" * 8001},
            "user 8001": {"question": "q", "history": [{"user": "x" * 8001, "assistant": "a"}]},
            "assistant 8001": {"question": "q", "history": [{"user": "u", "assistant": "x" * 8001}]},
            "pregunta vacía": {"question": ""},
            "pregunta solo espacios": {"question": "   \n\t "},
            "user solo espacios": {"question": "q", "history": [{"user": "  ", "assistant": "a"}]},
            "assistant vacío": {"question": "q", "history": [{"user": "u", "assistant": ""}]},
            "sin pregunta": {},
            "pregunta numérica": {"question": 123},
            "pregunta nula": {"question": None},
            "pregunta lista": {"question": ["a"]},
            "history cadena": {"question": "q", "history": "hola"},
            "history nulo": {"question": "q", "history": None},
            "history objeto": {"question": "q", "history": {"user": "u", "assistant": "a"}},
            "turno cadena": {"question": "q", "history": ["hola"]},
            "user numérico": {"question": "q", "history": [{"user": 1, "assistant": "a"}]},
            "assistant booleano": {"question": "q", "history": [{"user": "u", "assistant": True}]},
            "campo extra raíz": {"question": "q", "extra": 1},
            "campo extra turno": {"question": "q", "history": [{"user": "u", "assistant": "a", "x": 1}]},
            "turno sin assistant": {"question": "q", "history": [{"user": "u"}]},
            "turno sin user": {"question": "q", "history": [{"assistant": "a"}]},
            "turno vacío": {"question": "q", "history": [{}]},
            "cuerpo no objeto": ["q"],
        }
        for name, payload in cases.items():
            with self.subTest(name):
                self.assert_rejected(payload)

    def test_invalid_json_and_empty_body(self) -> None:
        self.assert_rejected(content=b"{no es json")
        self.assert_rejected(content=b"")

    def test_validation_message_does_not_echo_input(self) -> None:
        response = self.client.post("/api/chat", json={"question": "x" * 8001})
        self.assertNotIn("xxxxxxxx", response.text)
        self.assertIn("question", response.json()["error"]["message"])


class ChatErrorTests(ApiTestCase):
    def post(self):
        return self.client.post("/api/chat", json={"question": "hola"})

    def test_missing_key_is_503(self) -> None:
        self.remove_key()
        self.assert_error(self.post(), 503, "missing_api_key")
        self.model_mock.assert_not_awaited()

    def test_blank_key_is_503(self) -> None:
        os.environ[API_KEY_VARIABLE] = "   "
        self.assert_error(self.post(), 503, "missing_api_key")

    def test_provider_failures(self) -> None:
        cases = [
            ("401", status_error(openai.AuthenticationError, 401), 503, "provider_authentication_error"),
            ("403", status_error(openai.PermissionDeniedError, 403), 503, "provider_authentication_error"),
            ("402", status_error(openai.APIStatusError, 402), 503, "provider_quota_exceeded"),
            (
                "429 cuota",
                status_error(openai.RateLimitError, 429, {"code": "insufficient_quota"}),
                503,
                "provider_quota_exceeded",
            ),
            ("429 límite", status_error(openai.RateLimitError, 429), 503, "provider_rate_limited"),
            ("404", status_error(openai.NotFoundError, 404), 503, "provider_model_not_found"),
            ("500", status_error(openai.InternalServerError, 500), 503, "provider_unavailable"),
            ("503", status_error(openai.APIStatusError, 503), 503, "provider_unavailable"),
            ("400", status_error(openai.BadRequestError, 400), 502, "provider_rejected_request"),
            ("conexión", openai.APIConnectionError(request=FAKE_REQUEST), 502, "provider_connection_error"),
            ("timeout SDK", openai.APITimeoutError(request=FAKE_REQUEST), 504, "provider_timeout"),
            ("timeout asyncio", asyncio.TimeoutError(), 504, "provider_timeout"),
            ("excepción rara", ValueError(f"roto {FAKE_KEY}"), 502, "provider_malformed_response"),
        ]
        codes = set()
        for name, exc, status, code in cases:
            with self.subTest(name):
                self.model_mock.side_effect = exc
                response = self.post()
                self.assert_error(response, status, code)
                self.assert_no_secret(response)
                codes.add(code)
        # Las causas son distinguibles: ninguna se reduce a un único código.
        self.assertGreaterEqual(len(codes), 8)

    def test_messages_differ_by_cause(self) -> None:
        messages = set()
        for exc in (
            status_error(openai.AuthenticationError, 401),
            status_error(openai.RateLimitError, 429),
            status_error(openai.InternalServerError, 500),
        ):
            self.model_mock.side_effect = exc
            messages.add(self.post().json()["error"]["message"])
        self.assertEqual(len(messages), 3)

    def test_real_deadline_returns_504(self) -> None:
        async def slow(*args, **kwargs):
            await asyncio.sleep(5)

        self.model_mock.side_effect = slow
        fast = Settings(api_key=FAKE_KEY, timeout_seconds=0.05)
        with patch("api.routes.load_settings", return_value=fast):
            response = self.post()
        self.assert_error(response, 504, "provider_timeout")

    def test_bad_responses(self) -> None:
        cases = [
            ("vacía", AIMessage(content=""), "provider_empty_response"),
            ("solo espacios", AIMessage(content="  \n "), "provider_empty_response"),
            ("contenido lista", AIMessage(content=[{"type": "text", "text": "hola"}]), "provider_malformed_response"),
            ("sin contenido", None, "provider_malformed_response"),
            ("objeto ajeno", {"choices": []}, "provider_malformed_response"),
        ]
        for name, value, code in cases:
            with self.subTest(name):
                self.model_mock.return_value = value
                self.assert_error(self.post(), 502, code)

    def test_secret_not_in_logs_or_settings_repr(self) -> None:
        self.model_mock.side_effect = status_error(openai.AuthenticationError, 401)
        response = self.post()
        self.assert_no_secret(response)
        self.assertTrue(any("provider_authentication_error" in l for l in self.logs.lines))
        self.assertNotIn(FAKE_KEY, repr(Settings(api_key=FAKE_KEY)))


class WireTests(ApiTestCase):
    """Atraviesa el SDK real de OpenAI, con la red sustituida por un transporte falso."""

    def setUp(self) -> None:
        super().setUp()
        self.model.stop()  # usa el ainvoke real: solo se simula la capa HTTP.
        self.addCleanup(self.model.start)

    def reply(self, status: int, *, json_body=None, content=None):
        """Simula al proveedor: la respuesta debe llevar la petición real recibida."""

        def build(request: httpx.Request, **kwargs) -> httpx.Response:
            if content is None:
                return httpx.Response(status, json=json_body, request=request)
            return httpx.Response(status, content=content, request=request)

        self.network_mock.side_effect = build

    def completion_body(self, content: str) -> dict:
        return {
            "id": "x",
            "object": "chat.completion",
            "created": 0,
            "model": config.MODEL_NAME,
            "choices": [
                {"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": content}}
            ],
        }

    def test_payload_provider_model_and_order(self) -> None:
        self.reply(200, json_body=self.completion_body("desde el SDK"))
        response = self.client.post(
            "/api/chat",
            json={"question": "actual", "history": [{"user": "u1", "assistant": "a1"}]},
        )
        self.assertEqual(response.json(), {"answer": "desde el SDK", "sources": []})
        self.assertEqual(self.network_mock.await_count, 1)
        request = self.network_mock.await_args.args[0]
        self.assertTrue(str(request.url).startswith("https://openrouter.ai/api/v1/"))
        payload = json.loads(request.content)
        self.assertEqual(payload["model"], "cohere/north-mini-code:free")
        self.assertEqual(
            [(m["role"], m["content"]) for m in payload["messages"]],
            [("user", "u1"), ("assistant", "a1"), ("user", "actual")],
        )
        self.assert_no_secret(response)

    def test_no_automatic_retries(self) -> None:
        self.reply(500, json_body={"error": {"message": f"fallo {FAKE_KEY}"}})
        response = self.client.post("/api/chat", json={"question": "q"})
        self.assert_error(response, 503, "provider_unavailable")
        self.assertEqual(self.network_mock.await_count, 1)
        self.assert_no_secret(response)

    def test_transport_timeout_and_connection_errors(self) -> None:
        cases = [
            (httpx.ReadTimeout("lento"), 504, "provider_timeout"),
            (httpx.ConnectError("sin red"), 502, "provider_connection_error"),
        ]
        for exc, status, code in cases:
            with self.subTest(code):
                self.network_mock.side_effect = exc
                response = self.client.post("/api/chat", json={"question": "q"})
                self.assert_error(response, status, code)

    def test_malformed_http_body(self) -> None:
        self.reply(200, content=b"<html>no es json</html>")
        response = self.client.post("/api/chat", json={"question": "q"})
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["error"]["code"], "provider_malformed_response")


class CorsTests(ApiTestCase):
    def test_allowed_origins(self) -> None:
        for origin in ORIGIN_OK:
            with self.subTest(origin):
                preflight = self.client.options(
                    "/api/chat",
                    headers={
                        "Origin": origin,
                        "Access-Control-Request-Method": "POST",
                        "Access-Control-Request-Headers": "content-type",
                    },
                )
                self.assertEqual(preflight.status_code, 200)
                self.assertEqual(preflight.headers["access-control-allow-origin"], origin)
                simple = self.client.get("/api/health", headers={"Origin": origin})
                self.assertEqual(simple.headers["access-control-allow-origin"], origin)

    def test_error_responses_keep_cors_headers(self) -> None:
        response = self.client.post(
            "/api/chat", json={"question": ""}, headers={"Origin": ORIGIN_OK[0]}
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.headers["access-control-allow-origin"], ORIGIN_OK[0])

    def test_foreign_origin_gets_no_cors_headers(self) -> None:
        simple = self.client.get("/api/health", headers={"Origin": ORIGIN_FOREIGN})
        self.assertNotIn("access-control-allow-origin", simple.headers)
        preflight = self.client.options(
            "/api/chat",
            headers={"Origin": ORIGIN_FOREIGN, "Access-Control-Request-Method": "POST"},
        )
        self.assertNotIn("access-control-allow-origin", preflight.headers)
        self.assertEqual(preflight.status_code, 400)


class ImportTests(unittest.TestCase):
    def run_python(self, code: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-c", code],
            cwd=PROJECT_ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_import_does_not_load_console_scripts_or_ask_input(self) -> None:
        code = (
            "import builtins, sys\n"
            "builtins.input = lambda *a: (_ for _ in ()).throw(SystemExit('input'))\n"
            "import api.app\n"
            "loaded = [m for m in ('Chat', 'ChatVS', 'ChatThinking') if m in sys.modules]\n"
            "assert not loaded, loaded\n"
            "print('ok')\n"
        )
        result = self.run_python(code)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "ok")

    def test_import_without_key_does_not_fail(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != API_KEY_VARIABLE}
        result = subprocess.run(
            [sys.executable, "-c", "import api.app; print('ok')"],
            cwd=PROJECT_ROOT,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
