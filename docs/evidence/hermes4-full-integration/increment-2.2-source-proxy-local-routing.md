# Increment 2.2 - Source Proxy local routing

Date: 2026-05-29T19:57:07-04:00

```text
source_proxy/routing/litellm_router.py:            model=f"ollama_chat/{ollama_model}",
source_proxy/routing/ollama_route.py:_DEFAULT_OLLAMA_MODEL = "hermes4"
source_proxy/routing/ollama_route.py:    selected_via: str
source_proxy/routing/ollama_route.py:    selected_via = "default"
source_proxy/routing/ollama_route.py:        api_base, probe_ok, available_models, selected_via = _select_reachable_base(candidates)
source_proxy/routing/ollama_route.py:        selected_via = "env_first"
source_proxy/routing/ollama_route.py:            selected_via = f"{selected_via}+available_hermes"
source_proxy/routing/ollama_route.py:        litellm_model=f"ollama_chat/{model}",
source_proxy/routing/ollama_route.py:        selected_via=selected_via,
source_proxy/routing/ollama_route.py:            0 if "hermes4" in model.lower() else 1,
source_proxy/routing/ollama_route.py:        "ollama_chatexception",
source_proxy/routing/ollama_route.py:        "selected_via": route.selected_via,
source_proxy/routing/ollama_route.py:    storage = _ollama_model_storage_proof()
source_proxy/routing/ollama_route.py:        "requested_ollama_model": route.requested_model,
source_proxy/routing/ollama_route.py:        "selected_via": route.selected_via,
source_proxy/routing/ollama_route.py:        "model_storage_status": storage["status"],
source_proxy/routing/ollama_route.py:        "model_storage_path": storage["path"],
source_proxy/routing/ollama_route.py:        "model_storage_proof": storage["proof"],
source_proxy/routing/ollama_route.py:def _ollama_model_storage_proof() -> dict[str, str]:
source_proxy/routing/ollama_route.py:                str(meta.get("selected_via") or "probe_cache"),
source_proxy/routing/ollama_route.py:            selected_via = (
source_proxy/routing/ollama_route.py:                        else "fallback_default"
source_proxy/routing/ollama_route.py:                "selected_via": f"probe:{selected_via}",
source_proxy/routing/ollama_route.py:            return candidate, True, models, meta["selected_via"]
source_proxy/routing/ollama_route.py:    meta = {"probe_ok": False, "available_models": [], "selected_via": "probe_failed_use_first_env"}
source_proxy/routing/ollama_route.py:    return fallback, False, (), meta["selected_via"]
source_proxy/self_status.py:                    "requested_local_default": local_status.get("requested_ollama_model"),
source_proxy/self_status.py:                    "configured_ollama_model": local_status.get("ollama_model"),
source_proxy/self_status.py:                    "resolved_model": local_status.get("model"),
source_proxy/self_status.py:                    "selected_via": local_status.get("selected_via"),
source_proxy/self_status.py:                    "model_storage_status": local_status.get("model_storage_status"),
source_proxy/self_status.py:                    "model_storage_path": local_status.get("model_storage_path"),
source_proxy/self_status.py:                    "model_storage_proof": local_status.get("model_storage_proof"),
source_proxy/tests/test_ollama_route.py:            self.assertEqual(resolve_ollama_model_name(), "hermes4")
source_proxy/tests/test_ollama_route.py:            return_value=(True, ("qwen2.5-coder:7b", "hermes3:8b-abliterated")),
source_proxy/tests/test_ollama_route.py:        self.assertEqual(route.requested_model, "hermes4")
source_proxy/tests/test_ollama_route.py:        self.assertIn("available_hermes", route.selected_via)
source_proxy/tests/test_ollama_route.py:            return_value=(True, ("hermes4:latest", "qwen2.5-coder:7b")),
source_proxy/tests/test_ollama_route.py:        self.assertEqual(status["requested_ollama_model"], "hermes4")
source_proxy/tests/test_ollama_route.py:        self.assertEqual(status["ollama_model"], "hermes4:latest")
source_proxy/tests/test_ollama_route.py:        self.assertEqual(status["model"], "ollama_chat/hermes4:latest")
source_proxy/tests/test_ollama_route.py:        self.assertEqual(status["model_storage_status"], "proven")
source_proxy/tests/test_ollama_route.py:        self.assertEqual(status["model_storage_proof"], "OLLAMA_MODELS")
source_proxy/tests/test_ollama_route.py:    def test_local_route_maps_to_ollama_chat_model(self) -> None:
source_proxy/tests/test_ollama_route.py:                "SOURCE_PROXY_OLLAMA_MODEL": "qwen2.5-coder:7b",
source_proxy/tests/test_ollama_route.py:        self.assertEqual(local.model, "ollama_chat/qwen2.5-coder:7b")
source_proxy/tests/test_self_status.py:                    "model": "ollama_chat/hermes4",
source_proxy/tests/test_self_status.py:        self.assertEqual(manifest["model_routes"][0]["model"], "ollama_chat/hermes4")
source_proxy/tests/test_self_status.py:        self.assertIn("selected_via", manifest["model_routes"][0])
source_proxy/tests/test_self_status.py:        self.assertIn("requested_local_default", manifest["model_routes"][0])
source_proxy/tests/test_self_status.py:        self.assertIn("resolved_model", manifest["model_routes"][0])
source_proxy/tests/test_self_status.py:        self.assertIn("model_storage_status", manifest["model_routes"][0])
```

```diff
diff --git a/source_proxy/routing/litellm_router.py b/source_proxy/routing/litellm_router.py
index 4398628..0fe3d2b 100755
--- a/source_proxy/routing/litellm_router.py
+++ b/source_proxy/routing/litellm_router.py
@@ -7,6 +7,7 @@ from typing import Any
 
 from source_proxy.routing.ollama_route import (
     clear_ollama_route_cache,
+    ollama_route_status_entry,
     resolve_ollama_model_name,
     resolve_ollama_route,
 )
@@ -132,16 +133,20 @@ def route_model_for_alias(alias: str) -> str | None:
 
 
 def routing_status() -> list[dict[str, str | bool | None]]:
-    return [
-        {
+    statuses: list[dict[str, str | bool | None]] = []
+    local_status = ollama_route_status_entry()
+    for route_model in route_models():
+        item: dict[str, str | bool | None] = {
             "alias": route_model.alias,
             "provider": route_model.provider,
             "model": route_model.model,
             "enabled": route_model.enabled,
             "reason": route_model.reason,
         }
-        for route_model in route_models()
-    ]
+        if route_model.alias == "local" and route_model.provider == "ollama":
+            item.update(local_status)
+        statuses.append(item)
+    return statuses
 
 
 def clear_router_cache() -> None:
diff --git a/source_proxy/routing/ollama_route.py b/source_proxy/routing/ollama_route.py
index 1a8073c..eb6de00 100644
--- a/source_proxy/routing/ollama_route.py
+++ b/source_proxy/routing/ollama_route.py
@@ -9,8 +9,10 @@ from dataclasses import dataclass
 from typing import Any
 from urllib.parse import urlparse
 
-_DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:7b"
+_DEFAULT_OLLAMA_MODEL = "hermes4"
 _DEFAULT_OLLAMA_BASE = "http://127.0.0.1:11434"
+_DEFAULT_OLLAMA_HOME = "/usr/share/ollama/.ollama"
+_SPIRIT_8TB_ROOT = "/mnt/spirit-8tb"
 _PROBE_TIMEOUT_SECONDS = 2.0
 _PROBE_CACHE_SECONDS = 60.0
 
@@ -20,6 +22,7 @@ _probe_cache: tuple[float, str, dict[str, Any]] | None = None
 @dataclass(frozen=True)
 class OllamaRouteResolution:
     api_base: str
+    requested_model: str
     model: str
     litellm_model: str
     configured_candidates: tuple[str, ...]
@@ -73,6 +76,10 @@ def clear_ollama_route_cache() -> None:
 def resolve_ollama_route(*, probe: bool = True) -> OllamaRouteResolution:
     candidates = ollama_base_url_candidates()
     model = resolve_ollama_model_name()
+    explicit_model = bool(
+        os.getenv("SOURCE_PROXY_OLLAMA_MODEL", "").strip()
+        or os.getenv("OLLAMA_MODEL", "").strip()
+    )
     selected_via = "default"
     api_base = candidates[-1]
     probe_ok = False
@@ -84,13 +91,15 @@ def resolve_ollama_route(*, probe: bool = True) -> OllamaRouteResolution:
         api_base = candidates[0]
         selected_via = "env_first"
 
-    if probe_ok and available_models and model not in available_models:
-        if _DEFAULT_OLLAMA_MODEL in available_models:
-            model = _DEFAULT_OLLAMA_MODEL
-            selected_via = f"{selected_via}+default_model_fallback"
+    if probe_ok and available_models and model not in available_models and not explicit_model:
+        available_hermes = _preferred_available_hermes_model(available_models)
+        if available_hermes:
+            model = available_hermes
+            selected_via = f"{selected_via}+available_hermes"
 
     return OllamaRouteResolution(
         api_base=api_base.rstrip("/"),
+        requested_model=resolve_ollama_model_name(),
         model=model,
         litellm_model=f"ollama_chat/{model}",
         configured_candidates=tuple(candidates),
@@ -100,6 +109,20 @@ def resolve_ollama_route(*, probe: bool = True) -> OllamaRouteResolution:
     )
 
 
+def _preferred_available_hermes_model(available_models: tuple[str, ...]) -> str | None:
+    hermes_models = [model for model in available_models if "hermes" in model.lower()]
+    if not hermes_models:
+        return None
+    return sorted(
+        hermes_models,
+        key=lambda model: (
+            0 if "hermes4" in model.lower() else 1,
+            0 if "latest" in model.lower() else 1,
+            model,
+        ),
+    )[0]
+
+
 def local_model_unavailable_from_error(error: BaseException | str) -> bool:
     text = str(error).lower()
     markers = (
@@ -139,20 +162,50 @@ def local_model_unavailable_payload(
 
 def ollama_route_status_entry() -> dict[str, str | bool | None]:
     route = resolve_ollama_route(probe=True)
+    storage = _ollama_model_storage_proof()
     return {
         "alias": "local",
         "provider": "ollama",
         "model": route.litellm_model,
+        "requested_ollama_model": route.requested_model,
         "ollama_model": route.model,
         "api_base_host": safe_ollama_host_label(route.api_base),
         "api_base": route.api_base,
         "enabled": True,
         "probe_ok": route.probe_ok,
         "selected_via": route.selected_via,
+        "model_storage_status": storage["status"],
+        "model_storage_path": storage["path"],
+        "model_storage_proof": storage["proof"],
         "reason": None if route.probe_ok else "ollama_unreachable",
     }
 
 
+def _ollama_model_storage_proof() -> dict[str, str]:
+    env_path = os.getenv("OLLAMA_MODELS", "").strip()
+    if env_path:
+        real_env_path = os.path.realpath(env_path)
+        return {
+            "status": "proven" if real_env_path.startswith(_SPIRIT_8TB_ROOT) else "not_proven",
+            "path": real_env_path,
+            "proof": "OLLAMA_MODELS",
+        }
+
+    real_home = os.path.realpath(_DEFAULT_OLLAMA_HOME)
+    if real_home != _DEFAULT_OLLAMA_HOME:
+        return {
+            "status": "proven" if real_home.startswith(_SPIRIT_8TB_ROOT) else "not_proven",
+            "path": real_home,
+            "proof": f"{_DEFAULT_OLLAMA_HOME} symlink",
+        }
+
+    return {
+        "status": "not_proven",
+        "path": real_home,
+        "proof": "default_ollama_home",
+    }
+
+
 def _select_reachable_base(
     candidates: list[str],
 ) -> tuple[str, bool, tuple[str, ...], str]:
diff --git a/source_proxy/self_status.py b/source_proxy/self_status.py
index a609bc6..49ccaf5 100644
--- a/source_proxy/self_status.py
+++ b/source_proxy/self_status.py
@@ -8,6 +8,7 @@ from source_proxy.api.decision import AVAILABLE_ROUTES
 from source_proxy.agents.registry import get_provider_capability_payload
 from source_proxy.codex.adapter import build_codex_cli_status
 from source_proxy.routing.litellm_router import routing_status
+from source_proxy.routing.ollama_route import ollama_route_status_entry
 
 
 def build_self_status_manifest(project_root: Path | None = None) -> dict[str, Any]:
@@ -28,6 +29,7 @@ def build_self_status_manifest(project_root: Path | None = None) -> dict[str, An
         "disabled_tools": tools_manifest["disabled_tools"],
         "approval_boundaries": tools_manifest["approval_boundaries"],
         "available_routes": tools_manifest["available_routes"],
+        "model_routes": tools_manifest["model_routes"],
         "provider_capabilities": tools_manifest["provider_capabilities"],
         "codex_cli_status": tools_manifest["codex_cli_status"],
         "context_bundle_status": _context_bundle_status(root),
@@ -51,6 +53,7 @@ def build_tools_manifest(
         "disabled_tools": _disabled_tools(),
         "approval_boundaries": _approval_boundaries(),
         "available_routes": _available_routes(route_status),
+        "model_routes": _model_routes(route_status),
         "provider_capabilities": get_provider_capability_payload(),
         "codex_cli_status": codex_cli_status,
         "tool_manifest_notes": [
@@ -449,6 +452,38 @@ def _available_routes(routes: list[dict[str, str | bool | None]]) -> list[dict[s
     return available
 
 
+def _model_routes(routes: list[dict[str, str | bool | None]]) -> list[dict[str, Any]]:
+    enriched: list[dict[str, Any]] = []
+    local_status = ollama_route_status_entry()
+    for route in routes:
+        if not route.get("alias"):
+            continue
+        item: dict[str, Any] = {
+            "alias": str(route.get("alias") or ""),
+            "provider": str(route.get("provider") or ""),
+            "model": str(route.get("model") or ""),
+            "enabled": bool(route.get("enabled")),
+            "reason": route.get("reason"),
+            "source": "config",
+        }
+        if item["alias"] == "local" and item["provider"] == "ollama":
+            item.update(
+                {
+                    "api_base_host": local_status.get("api_base_host"),
+                    "requested_local_default": local_status.get("requested_ollama_model"),
+                    "configured_ollama_model": local_status.get("ollama_model"),
+                    "resolved_model": local_status.get("model"),
+                    "probe_ok": local_status.get("probe_ok"),
+                    "selected_via": local_status.get("selected_via"),
+                    "model_storage_status": local_status.get("model_storage_status"),
+                    "model_storage_path": local_status.get("model_storage_path"),
+                    "model_storage_proof": local_status.get("model_storage_proof"),
+                }
+            )
+        enriched.append(item)
+    return enriched
+
+
 def _context_bundle_status(root: Path) -> dict[str, Any]:
     bundle_names = ["repomix-output.ast.xml", "repomix-output.xml"]
     bundles = []
diff --git a/source_proxy/tests/test_ollama_route.py b/source_proxy/tests/test_ollama_route.py
index 43e4133..d97d8d7 100644
--- a/source_proxy/tests/test_ollama_route.py
+++ b/source_proxy/tests/test_ollama_route.py
@@ -8,6 +8,7 @@ from source_proxy.routing.litellm_router import clear_router_cache, route_models
 from source_proxy.routing.ollama_route import (
     clear_ollama_route_cache,
     local_model_unavailable_from_error,
+    ollama_route_status_entry,
     resolve_ollama_model_name,
     resolve_ollama_route,
 )
@@ -34,9 +35,9 @@ class OllamaRouteTests(unittest.TestCase):
             route = resolve_ollama_route(probe=True)
         self.assertTrue(route.probe_ok, route)
         self.assertIn("127.0.0.1", route.api_base)
-        self.assertEqual(route.model, "qwen2.5-coder:7b")
+        self.assertIn("hermes", route.model)
 
-    def test_default_model_is_qwen_coder_when_unconfigured(self) -> None:
+    def test_default_model_is_hermes_when_unconfigured(self) -> None:
         with mock.patch.dict(
             os.environ,
             {
@@ -45,7 +46,50 @@ class OllamaRouteTests(unittest.TestCase):
             },
             clear=False,
         ):
-            self.assertEqual(resolve_ollama_model_name(), "qwen2.5-coder:7b")
```

```text
```

## Result

GO. Source Proxy local routing defaults to Hermes 4, prefers installed Hermes models over Qwen when unconfigured, and now exposes requested local default, resolved model, selected_via, probe_ok, and 8TB storage proof fields.
