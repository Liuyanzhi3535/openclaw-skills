# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

```bash
# 安裝依賴（建立 .venv）
uv sync

# 跑所有測試
uv run pytest

# 跑單一測試檔
uv run pytest tests/skills/test_calendar_gcal.py

# 跑單一測試
uv run pytest tests/skills/test_calendar_gcal.py::test_list_events_returns_events

# 測試 + coverage 報告
uv run pytest --cov=sidecar --cov=skills --cov-report=term-missing

# Lint
uv run ruff check .

# 本地啟動 sidecar（開發用，綁 0.0.0.0 方便測試）
uv run uvicorn sidecar.router:app --host 0.0.0.0 --port 8080 --reload
```

## 架構

這個 repo 是部署在 K8s Pod 內的 **sidecar**，與 OpenClaw（Claude AI agent）共存於同一 Pod。

```
sidecar/router.py       → FastAPI app 入口，整合所有 skill router
skills/<skill_name>/
    main.py             → skill 業務邏輯，定義 APIRouter
    __init__.py         → export router
    SKILL.md            → openclaw 讀的說明書（endpoint 描述、呼叫範例）
tests/
    conftest.py         → shared fixtures：TestClient、mock_google_service
    test_router.py      → /healthz 整合測試
    skills/             → 各 skill 的測試
```

**新增 skill 的步驟**：
1. 建立 `skills/<name>/main.py`，定義 `router = APIRouter(prefix="/skill/<name>")`
2. 在 `skills/<name>/__init__.py` export router
3. 在 `skills/<name>/SKILL.md` 寫給龍蝦讀的說明（name、description、呼叫範例）
4. 在 `sidecar/router.py` 加入 `app.include_router(...)`
5. 在 `tests/skills/test_<name>.py` 加測試

## 部署

- **CI**（`.github/workflows/ci.yml`）：PR 時自動 lint + test
- **CD**（`.github/workflows/build-push.yml`）：push main 時 build Docker → ghcr.io → `kubectl rollout restart`
- **Helm**（`helm/my-values.yaml`）：
  - `initContainers` 在 Pod 啟動時把所有 `SKILL.md` 複製到 PVC（`~/.openclaw/workspace/skills/`），openclaw 從這裡認識 skill
  - `extraContainers` 跑 sidecar，監聽 `127.0.0.1:8080`

## Credentials

Google OAuth token 放在 K8s Secret，掛載至 `/credentials/google_token.json`。
本地測試時用 `scripts/oauth_init.py` 初始化 token，再放到對應路徑。
測試中一律透過 `mock_google_service` fixture mock，不需要真實 token。
