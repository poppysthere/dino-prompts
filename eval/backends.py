"""Model backends for the eval runner and judge.

Four backends, selected with EVAL_BACKEND (or --backend):
  forge  — the Prompt Forge debug API (same models the app uses). Needs:
             FORGE_BASE_URL   e.g. http://ec2-....amazonaws.com:8888/api
             FORGE_TOKEN      (or FORGE_EMAIL + FORGE_PASSWORD to login)
             FORGE_PROVIDER   provider name as shown in the forge model picker
             FORGE_MODEL      model name as shown in the forge model picker
  openai — any OpenAI-compatible chat completions endpoint. Needs:
             EVAL_API_BASE, EVAL_API_KEY, EVAL_MODEL
  azure  — a direct Azure OpenAI deployment. Needs:
             AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY,
             AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT
             Optional: AZURE_OPENAI_TIMEOUT (default 180 seconds)
  mock   — no network; replays scripted good-teacher replies. For testing the
           pipeline itself (runner -> transcript -> checker) without a model.
"""
import json
import os
import socket
import time
import urllib.error
import urllib.parse
import urllib.request


class Backend:
    def chat(self, system_prompt: str, messages: list) -> str:
        """messages: [{"role": "user"|"assistant", "content": str}] -> assistant text"""
        raise NotImplementedError


def _post_json(url: str, payload: dict, headers: dict, timeout: int = 90) -> dict:
    # The Forge ALB throws intermittent 400/5xx under load (seen 2026-07-15,
    # identical request succeeds on retry) — retry transient failures.
    last = None
    for attempt in range(3):
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", **headers},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
                socket.timeout) as e:  # socket.timeout != TimeoutError before 3.10
            code = getattr(e, "code", None)
            if code is not None and code not in (400, 429, 500, 502, 503, 504):
                raise
            last = e
            time.sleep(3 * (attempt + 1))
    raise last


class ForgeBackend(Backend):
    """Prompt Forge POST /debug — the same endpoint the forge web UI's debug chat uses."""

    def __init__(self):
        self.base = os.environ["FORGE_BASE_URL"].rstrip("/")
        self.provider = os.environ["FORGE_PROVIDER"]
        self.model = os.environ["FORGE_MODEL"]
        self.token = os.environ.get("FORGE_TOKEN") or self._login()

    def _login(self) -> str:
        email = os.environ["FORGE_EMAIL"]
        password = os.environ["FORGE_PASSWORD"]
        res = _post_json(f"{self.base}/auth/login", {"email": email, "password": password}, {})
        if res.get("code") != 200:
            raise RuntimeError(f"forge login failed: {res}")
        return res["data"]["token"] if isinstance(res.get("data"), dict) else res["data"]

    def chat(self, system_prompt, messages):
        payload = {
            "systemPrompt": system_prompt,
            "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
            "providerName": self.provider,
            "modelName": self.model,
        }
        # Forge surfaces its own upstream failures as a NORMAL 200 reply whose
        # content starts with "调用失败" ("call failed", seen 2026-07-16:
        # "channel not registered to an event loop") — retry those too.
        for attempt in range(4):
            res = _post_json(f"{self.base}/debug", payload, {"Authorization": self.token})
            if res.get("code") != 200:
                raise RuntimeError(f"forge /debug failed: {res}")
            content = res["data"]["content"]
            if not content.strip().startswith("调用失败"):
                return content
            time.sleep(5 * (attempt + 1))
        raise RuntimeError(f"forge /debug kept failing upstream: {content!r}")


class OpenAIBackend(Backend):
    def __init__(self):
        self.base = os.environ["EVAL_API_BASE"].rstrip("/")
        self.key = os.environ["EVAL_API_KEY"]
        self.model = os.environ["EVAL_MODEL"]

    def chat(self, system_prompt, messages):
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}]
            + [{"role": m["role"], "content": m["content"]} for m in messages],
        }
        res = _post_json(
            f"{self.base}/chat/completions", payload, {"Authorization": f"Bearer {self.key}"}
        )
        return res["choices"][0]["message"]["content"]


class AzureOpenAIBackend(Backend):
    """Direct Azure OpenAI deployment using the deployment-based chat API."""

    def __init__(self):
        self.endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
        self.key = os.environ["AZURE_OPENAI_API_KEY"]
        self.api_version = os.environ["AZURE_OPENAI_API_VERSION"]
        self.deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"]
        self.timeout = int(os.environ.get("AZURE_OPENAI_TIMEOUT", "180"))

    def chat(self, system_prompt, messages):
        payload = {
            "messages": [{"role": "system", "content": system_prompt}]
            + [{"role": m["role"], "content": m["content"]} for m in messages],
        }
        deployment = urllib.parse.quote(self.deployment, safe="")
        version = urllib.parse.quote(self.api_version, safe="")
        url = (
            f"{self.endpoint}/openai/deployments/{deployment}/chat/completions"
            f"?api-version={version}"
        )
        res = _post_json(url, payload, {"api-key": self.key}, timeout=self.timeout)
        return res["choices"][0]["message"]["content"]


class MockBackend(Backend):
    """Deterministic well-behaved teacher, driven by the page manifest.

    Only for validating pipeline plumbing. Reply plan:
      reply 1 -> the fixed opener
      reply 2 -> catch + count-down game invite
      reply 3 -> if the child's last message contains the word (very roughly), celebrate+finish;
                 else help move + say-it-big invite
      reply 4 -> honest close + finish line
    """

    def __init__(self, page: dict):
        self.page = page

    def chat(self, system_prompt, messages):
        word = self.page["word"]
        n_replies = sum(1 for m in messages if m["role"] == "assistant")
        user_msgs = [m["content"].lower() for m in messages if m["role"] == "user"
                     and not m["content"].startswith("The student has been silent")
                     and "UI is ready" not in m["content"]]
        said = any(word[:3] in u for u in user_msgs)
        finish = self.page["finish_line"]
        maybe_tag = "" if finish.endswith("]") else ""
        if n_replies == 0:
            return self.page["opener"]
        if n_replies == 1:
            return f"Oh, fun words! Ready? One, two, three. {word.upper()}![TEACHER_LISTEN][STUDENT_TALK]"
        if n_replies == 2 and said:
            return f"YOU SAID IT![TEACHER_APPLAUD] So brave! {finish}[TEMPLATE_FINISH]"
        if n_replies == 2:
            return f"It's okay! I help you! Say it SUPER big! {word.upper()}![TEACHER_LISTEN][STUDENT_TALK]"
        if said:
            return f"Wow, you did it! High five! {finish}[TEMPLATE_FINISH]"
        return f"You tried SO hard! High five! Listen: {word}! {finish}[TEMPLATE_FINISH]"


def make_backend(name: str, page: dict = None) -> Backend:
    name = (name or os.environ.get("EVAL_BACKEND", "mock")).lower()
    if name == "forge":
        return ForgeBackend()
    if name == "openai":
        return OpenAIBackend()
    if name == "azure":
        return AzureOpenAIBackend()
    if name == "mock":
        return MockBackend(page or {})
    raise ValueError(f"unknown backend: {name}")
