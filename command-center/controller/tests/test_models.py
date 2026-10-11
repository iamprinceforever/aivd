"""Model picker / download tests. Ollama is NEVER started: pulls run against controller/tests/fake_ollama.py, a test
double that only streams a recorded-shape /api/pull response and writes fixture blobs into a temp store."""
import base64
import hashlib
import json
import os
import shutil
import stat
import sys
import threading
import time
import unittest
from pathlib import Path

from controller import models as MD
from controller import pipeline as PL
from controller import server as S
from controller.tests import test_controller as TC
from controller.tests import test_pipeline as TP

Base, free_port, fake_specs = TC.Base, TC.free_port, TP.fake_specs

FAKE_SRC = Path(__file__).with_name("fake_ollama.py")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def fixture_model(name="aivd-fixture:tiny", size=300_000, seed=b"w"):
    weights = (seed * 97 + b"\x00") * (size // 98 + 1)
    weights = weights[:size]
    config = json.dumps({"model_family": "fixture", "model_type": "tiny"}).encode()
    template = b"{{ .Prompt }}"
    blobs = [{"b64": base64.b64encode(weights).decode(), "model": True,
              "media": "application/vnd.ollama.image.model"},
             {"b64": base64.b64encode(template).decode(), "media": "application/vnd.ollama.image.template"},
             {"b64": base64.b64encode(config).decode(), "media": "config"}]
    manifest = {"schemaVersion": 2, "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                "config": {"mediaType": "application/vnd.docker.container.image.v1+json",
                           "digest": "sha256:" + sha(config), "size": len(config)},
                "layers": [{"mediaType": "application/vnd.ollama.image.model", "digest": "sha256:" + sha(weights),
                            "size": len(weights)},
                           {"mediaType": "application/vnd.ollama.image.template",
                            "digest": "sha256:" + sha(template), "size": len(template)}]}
    text = json.dumps(manifest)
    entry = {"name": name, "family": "fixture", "params": "tiny", "quant": "F16", "rc6_allowlisted": False,
             "size_bytes": len(weights), "size_is_exact": True, "arch": {"layers": 1, "kv_heads": 1, "head_dim": 8},
             "pins": {"manifest_sha256": sha(text.encode()), "model_blob_sha256": sha(weights)}}
    return {"blobs": blobs, "manifest_text": text}, entry


def install(store, fx, name):
    (store / "blobs").mkdir(parents=True, exist_ok=True)
    for b in fx["blobs"]:
        data = base64.b64decode(b["b64"])
        (store / "blobs" / ("sha256-" + sha(data))).write_bytes(data)
    model, tag = name.split(":")
    mp = store / "manifests" / "registry.ollama.ai" / "library" / model / tag
    mp.parent.mkdir(parents=True, exist_ok=True)
    mp.write_text(fx["manifest_text"])


EST = {"num_ctx": 8192, "kv_bytes_per_element": 2, "compute_overhead_mib": 300, "runtime_overhead_mib": 100,
       "headroom_mib": 1024}


class ModelEnv:
    """Temp store, catalog, and a fake ollama binary (with fixture.json beside it)."""

    def setup_models(self, models, fixtures=None, extra_catalog=()):
        self.store = self.td / "store"
        self.store.mkdir()
        self.bindir = self.td / "fakebin"
        self.bindir.mkdir()
        self.binary = self.bindir / "ollama"
        self.binary.write_text(f"#!{sys.executable}\n" + FAKE_SRC.read_text())
        self.binary.chmod(0o700)
        (self.bindir / "fixture.json").write_text(json.dumps({"models": fixtures or {}}))
        self.catalog = self.td / "catalog.json"
        self.catalog.write_text(json.dumps({"schema": 1, "estimate": EST, "models": list(models) + list(extra_catalog)}))
        return {"model_store": str(self.store), "ollama_binary": str(self.binary), "pull_enabled": True,
                "pull_port": free_port(), "model_catalog": str(self.catalog), "pull_timeout_s": 60}

    def env_keys(self):
        p = self.bindir / "env_keys.json"
        return json.loads(p.read_text()) if p.exists() else None


# ---------------------------------------------------------------- catalog / RAM / specs
class CatalogTests(unittest.TestCase):
    def test_bundled_catalog(self):
        cat = MD.load_catalog(None, S.ALLOWED_MODELS)
        names = [m["name"] for m in cat["models"]]
        self.assertEqual(names[:3], ["qwen3:1.7b", "llama3.2:3b", "qwen3:8b"])
        rc6 = [m for m in cat["models"] if m["rc6_allowlisted"]]
        self.assertEqual(sorted(m["name"] for m in rc6), sorted(S.ALLOWED_MODELS))
        for m in rc6:
            self.assertTrue(m["pins"] and m["size_is_exact"])
        for m in cat["models"]:
            if not m["rc6_allowlisted"]:
                self.assertIsNone(m["pins"], "extras must not carry invented digests")
                self.assertFalse(m["size_is_exact"])
        self.assertEqual(cat["models"][0]["pins"]["model_blob_sha256"][:12], "3d0b790534fe")

    def bad(self, models, rx):
        td = Path(self.id().replace(".", "_"))
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.json"
            p.write_text(json.dumps({"estimate": EST, "models": models}))
            with self.assertRaisesRegex(MD.CatalogError, rx):
                MD.load_catalog(p, S.ALLOWED_MODELS)

    def test_catalog_cannot_widen_rc6_allowlist_or_invent_pins(self):
        base = {"family": "q", "size_bytes": 1, "arch": {"layers": 1, "kv_heads": 1, "head_dim": 1}}
        self.bad([dict(base, name="qwen3:4b", rc6_allowlisted=True, pins=None)], "not in the RC6 allowlist")
        self.bad([dict(base, name="qwen3:8b", rc6_allowlisted=True, pins=None)], "must carry pinned digests")
        self.bad([dict(base, name="x:1", pins={"manifest_sha256": "zz", "model_blob_sha256": "a" * 64})], "pins")
        self.bad([dict(base, name="X Y")], "unique name")
        self.bad([dict(base, name="a:1"), dict(base, name="a:1")], "unique name")

    def test_ram_estimate_and_fit_rules(self):
        cat = MD.load_catalog(None, S.ALLOWED_MODELS)
        q8 = next(m for m in cat["models"] if m["name"] == "qwen3:8b")
        ram = MD.estimate_ram(q8, cat["estimate"])
        self.assertEqual(ram["kv_cache_mib"], 1152)           # 2 x 36 x 8 x 128 x 2 B x 8192
        self.assertEqual(ram["weights_mib"], 4983)
        self.assertEqual(ram["recommended_kb"] - ram["estimate_kb"], 1024 * 1024)
        f = lambda avail, total=16_000_000: MD.fit_verdict(ram, {"mem_available_kb": avail, "mem_total_kb": total})
        self.assertEqual(f(ram["recommended_kb"])["verdict"], "FITS")
        self.assertEqual(f(ram["recommended_kb"] - 1)["verdict"], "TIGHT")
        self.assertEqual(f(ram["estimate_kb"])["verdict"], "TIGHT")
        ex = f(ram["estimate_kb"] - 1)
        self.assertEqual(ex["verdict"], "EXCEEDS")
        self.assertIn("will likely OOM", ex["reason"])
        self.assertIn("cannot fit", f(16_000_000, total=4_000_000)["reason"])
        self.assertEqual(MD.fit_verdict(ram, {"mem_available_kb": None, "mem_total_kb": None})["verdict"],
                         "NOT_VERIFIED")

    def test_specs_cpu_gpu_balloon(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "proc").mkdir()
            (d / "proc" / "meminfo").write_text("MemTotal: 16000000 kB\nMemAvailable: 6500000 kB\nSwapTotal: 0 kB\n")
            (d / "proc" / "cpuinfo").write_text("processor\t: 0\nmodel name\t: Test Xeon\n")
            (d / "dev").mkdir()
            (d / "sys" / "bus" / "virtio" / "drivers" / "virtio_balloon").mkdir(parents=True)
            s = MD.read_specs(d / "proc", d / "dev", d / "sys")
            self.assertEqual((s["mem_total_kb"], s["mem_available_kb"]), (16_000_000, 6_500_000))
            self.assertEqual(s["rc6_memory_gate_kb"], 7_600_000)
            self.assertFalse(s["rc6_memory_gate_met"])
            self.assertFalse(s["gpu"]["present"])
            self.assertTrue(s["balloon"])
            self.assertTrue(any("CPU only" in n for n in s["notes"]))
            self.assertEqual(s["cpu_model"], "Test Xeon")
            (d / "dev" / "nvidia0").write_text("")
            self.assertTrue(MD.read_specs(d / "proc", d / "dev", d / "sys")["gpu"]["present"])


# ---------------------------------------------------------------- listing / status / verify
class ListingTests(ModelEnv, Base):
    def mgr_ctl(self, avail=6_500_000, total=16_000_000, **kw):
        c = self.ctl(**kw)
        c.models.specs = lambda: fake_specs(avail, total)
        return c

    def test_scan_names_come_from_manifest_paths_only(self):
        fx, e = fixture_model()
        cfg = self.setup_models([e])
        install(self.store, fx, "aivd-fixture:tiny")
        install(self.store, fx, "someone-else:latest")          # not in catalog
        c = self.mgr_ctl(**cfg)
        lst = c.models.listing()
        self.assertEqual([x["name"] for x in lst["catalog"]], ["aivd-fixture:tiny"])
        self.assertEqual(lst["catalog"][0]["install"]["status"], "installed")
        self.assertEqual([x["name"] for x in lst["installed_other"]], ["someone-else:latest"])
        self.assertFalse(lst["policy"]["listing_starts_ollama"])
        self.assertIsNone(self.env_keys())                      # listing never ran the binary

    def test_install_statuses(self):
        fx, e = fixture_model()
        cfg = self.setup_models([e])
        c = self.mgr_ctl(**cfg)
        st = lambda: c.models.assess("aivd-fixture:tiny")["install"]["status"]
        self.assertEqual(st(), "missing")
        install(self.store, fx, "aivd-fixture:tiny")
        self.assertEqual(st(), "installed")
        blob = next((self.store / "blobs").glob("sha256-*"))
        data = blob.read_bytes()
        blob.write_bytes(data[:-1])
        self.assertEqual(st(), "incomplete")
        blob.write_bytes(data)
        e2 = dict(e, pins={"manifest_sha256": "0" * 64, "model_blob_sha256": e["pins"]["model_blob_sha256"]})
        self.catalog.write_text(json.dumps({"estimate": EST, "models": [e2]}))
        c2 = self.mgr_ctl(**cfg)
        self.assertEqual(c2.models.assess("aivd-fixture:tiny")["install"]["status"], "differs_from_pin")

    def test_sorting_groups_and_recommendation(self):
        fa, ea = fixture_model("fix-a:1", 100_000, b"a")
        fb, eb = fixture_model("fix-b:2", 200_000, b"b")
        fc, ec = fixture_model("fix-c:3", 300_000, b"c")
        ec = dict(ec, size_bytes=40_000_000_000)                   # far too large
        cfg = self.setup_models([ec, eb, ea])
        install(self.store, fa, "fix-a:1")
        c = self.mgr_ctl(**cfg)
        lst = c.models.listing()
        self.assertEqual([(x["name"], x["group"]) for x in lst["catalog"]],
                         [("fix-a:1", "installed_fits"), ("fix-b:2", "fits_not_installed"), ("fix-c:3", "too_large")])
        self.assertEqual(lst["catalog"][2]["fit"]["verdict"], "EXCEEDS")
        self.assertEqual(lst["recommendation"]["model_id"], "fix-a:1")
        self.assertIn("installed", lst["recommendation"]["reason"])
        shutil.rmtree(self.store / "manifests")
        self.assertEqual(c.models.listing()["recommendation"]["model_id"], "fix-b:2")   # largest fitting catalog
        c.models.specs = lambda: fake_specs(10, 16_000_000)
        self.assertIsNone(c.models.listing()["recommendation"]["model_id"])

    def test_real_catalog_with_low_memory_marks_qwen8b_too_large(self):
        c = self.mgr_ctl(avail=6_400_000)
        lst = c.models.listing()
        q8 = next(x for x in lst["catalog"] if x["name"] == "qwen3:8b")
        self.assertEqual(q8["fit"]["verdict"], "EXCEEDS")
        self.assertEqual(lst["catalog"][-1]["group"], "too_large")
        self.assertEqual(q8["install"]["status"], "not_verified")       # no store configured
        self.assertFalse(lst["policy"]["pull_enabled"])

    def test_verify_deep_detects_tamper(self):
        fx, e = fixture_model()
        self.setup_models([e])
        install(self.store, fx, "aivd-fixture:tiny")
        model = MD.load_catalog(self.catalog)["models"][0]
        v = MD.verify_deep(self.store, "aivd-fixture:tiny", model)
        self.assertTrue(v["ok"], v)
        blob = self.store / "blobs" / ("sha256-" + e["pins"]["model_blob_sha256"])
        data = bytearray(blob.read_bytes())
        time.sleep(0.05)
        data[10] ^= 1
        blob.write_bytes(bytes(data))
        v = MD.verify_deep(self.store, "aivd-fixture:tiny", model)
        self.assertFalse(v["ok"])
        self.assertIn("DIGEST MISMATCH", v["reason"])

    def test_config_validation(self):
        cfgm = self.setup_models([fixture_model()[1]])
        with self.assertRaises(S.ConfigError):
            self.cfg(**dict(cfgm, pull_port=11434))
        with self.assertRaises(S.ConfigError):
            self.cfg(pull_enabled=True)
        with self.assertRaises(S.ConfigError):
            self.cfg(model_store=str(self.repo))
        with self.assertRaises(S.ConfigError):
            self.cfg(model_store="relative/store")
        bad = self.td / "bad.json"
        bad.write_text(json.dumps({"estimate": EST, "models": [{"name": "qwen3:4b", "family": "q", "size_bytes": 1,
                                   "arch": {"layers": 1, "kv_heads": 1, "head_dim": 1}, "rc6_allowlisted": True,
                                   "pins": None}]}))
        with self.assertRaisesRegex(S.ConfigError, "RC6 allowlist"):
            self.cfg(model_catalog=str(bad))

    def test_only_models_module_starts_serve(self):
        for f in ("server.py", "pipeline.py"):
            src = (Path(S.__file__).parent / f).read_text()
            self.assertNotIn(', "serve"]', src)                # no serve argv outside models.py
        src = Path(MD.__file__).read_text()
        self.assertEqual(src.count('[cfg["ollama_binary"], "serve"]'), 1)
        self.assertIn('"OLLAMA_NOPRUNE": "1"', src)
        self.assertIn('f"127.0.0.1:{port}"', src)


# ---------------------------------------------------------------- puller (fake binary)
class PullTests(ModelEnv, Base):
    def pctl(self, fixtures, models=None, avail=6_500_000, proc=False, **kw):
        fx, e = fixture_model()
        cfg = self.setup_models(models or [e], fixtures)
        cfg.update(kw)
        c = S.Controller(self.cfg(**cfg), env={"PATH": os.environ.get("PATH", ""), "GITHUB_TOKEN": "t0k",
                                                "AIVD_RC6_AUTHORIZE_START_RUNTIME": "x", "HOME": "/nonexistent"},
                         meminfo=lambda: avail, proc_check=lambda: proc)
        c.models.specs = lambda: fake_specs(avail)
        return c, e

    def test_pull_success_progress_verify_and_stop(self):
        fx, e = fixture_model()
        c, _ = self.pctl({"aivd-fixture:tiny": dict(fx, chunk=50_000)})
        prog, lines = [], []
        res = c.models.puller.pull(c.models.by_name["aivd-fixture:tiny"], "test", on_line=lines.append,
                                   on_progress=prog.append)
        self.assertEqual(res["outcome"], "succeeded", res)
        self.assertTrue(res["verify"]["ok"])
        self.assertTrue(res["verify"]["pinned"])
        self.assertTrue(res["serve"]["started"])
        self.assertTrue(res["serve"]["stopped"])
        self.assertTrue(res["serve"]["bind"].startswith("127.0.0.1:"))
        self.assertEqual(res["layers"], 3)
        self.assertEqual(prog[-1]["percent"], 100.0)
        self.assertTrue(any(0 < p["percent"] < 100 for p in prog))
        self.assertTrue(any("layer" in ln and "%" in ln for ln in lines))
        self.assertEqual(c.models.assess("aivd-fixture:tiny")["install"]["status"], "installed")
        keys = self.env_keys()
        self.assertIn("OLLAMA_NOPRUNE", keys)
        for k in keys:
            self.assertNotIn("AUTHORI", k)
            self.assertNotIn("TOKEN", k)
        job = c.models.puller.snapshot()
        self.assertEqual(job["state"], "succeeded")
        self.assertNotIn("_t0", c.models.listing()["pull"])
        audit = (self.state / "audit.jsonl").read_text()
        self.assertIn("pull_model", audit)
        self.assertNotIn(str(self.td), audit)

    def test_digest_mismatch_fails(self):
        fx, e = fixture_model()
        c, _ = self.pctl({"aivd-fixture:tiny": dict(fx, tamper=True)})
        res = c.models.puller.pull(c.models.by_name["aivd-fixture:tiny"], "test")
        self.assertEqual(res["outcome"], "failed")
        self.assertIn("DIGEST MISMATCH", res["reason"])
        self.assertTrue(res["serve"]["stopped"])

    def test_registry_error_is_reported_redacted(self):
        fx, e = fixture_model()
        c, _ = self.pctl({"aivd-fixture:tiny": dict(fx, error_after_layers="network error at " + str(self.td))})
        res = c.models.puller.pull(c.models.by_name["aivd-fixture:tiny"], "test")
        self.assertEqual(res["outcome"], "failed")
        self.assertIn("registry/ollama error", res["reason"])
        self.assertNotIn(str(self.td), json.dumps(res))

    def test_cancel_and_timeout_stop_the_server(self):
        fx, e = fixture_model()
        c, _ = self.pctl({"aivd-fixture:tiny": dict(fx, chunk=1000, delay=0.05)})
        th = threading.Thread(target=lambda: setattr(self, "r", c.models.puller.pull(
            c.models.by_name["aivd-fixture:tiny"], "test")))
        th.start()
        for _ in range(100):
            j = c.models.puller.snapshot()
            if j and j["progress"].get("completed", 0) > 0:
                break
            time.sleep(0.1)
        self.assertTrue(c.models.puller.busy())
        self.assertEqual(c.models.puller.pull(c.models.by_name["aivd-fixture:tiny"], "x")["outcome"], "busy")
        self.assertTrue(c.models.puller.cancel())
        th.join(30)
        self.assertEqual(self.r["outcome"], "cancelled")
        self.assertTrue(self.r["serve"]["stopped"])
        self.assertFalse(c.models.puller.cancel())
        r2 = c.models.puller.pull(c.models.by_name["aivd-fixture:tiny"], "test", timeout=2)
        self.assertEqual(r2["outcome"], "timeout")
        self.assertTrue(r2["serve"]["stopped"])

    def test_preconditions_block_without_starting_anything(self):
        fx, e = fixture_model()
        big = dict(e, name="aivd-fixture:huge", size_bytes=40_000_000_000)
        for kw, rx, name in (({"proc": True}, "already running", "aivd-fixture:tiny"),
                             ({"pull_enabled": False}, "disabled", "aivd-fixture:tiny"),
                             ({}, "will likely OOM|cannot fit", "aivd-fixture:huge")):
            with self.subTest(rx=rx):
                c, _ = self.pctl({"aivd-fixture:tiny": fx}, models=[e, big], **kw)
                res = c.models.puller.pull(c.models.by_name[name], "test")
                self.assertEqual(res["outcome"], "blocked")
                self.assertRegex(res["reason"], rx)
                self.assertFalse(res["serve"]["started"])
                self.assertIsNone(self.env_keys())
                shutil.rmtree(self.td / "fakebin")
                shutil.rmtree(self.td / "store")


# ---------------------------------------------------------------- HTTP endpoints
class ModelHttpTests(ModelEnv, Base):
    req, pair, auth = TC.HttpTests.req, TC.HttpTests.pair, TC.HttpTests.auth

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    def setUp(self):
        super().setUp()
        TC.make_fake_repo(self.repo)
        (self.td / "dist").mkdir()
        fx, e = fixture_model()
        self.fx = fx
        cfgm = self.setup_models([e], {"aivd-fixture:tiny": fx})
        cfg = self.cfg(ui_dir=str(self.td / "dist"), **cfgm)
        self.port = cfg["port"]
        self.c = S.Controller(cfg, env={"PATH": os.environ.get("PATH", "")}, meminfo=lambda: 1,
                              proc_check=lambda: False)
        self.c.models.specs = lambda: fake_specs(6_500_000)
        self.httpd = S.ThreadingHTTPServer(("127.0.0.1", self.port), S.make_handler(self.c))
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.origin = f"http://127.0.0.1:{self.port}"

    def test_models_listing_requires_session(self):
        st, _, _ = self.req("GET", "/api/models", headers={"Origin": self.origin})
        self.assertEqual(st, 401)
        res = self.pair()
        st, out, _ = self.req("GET", "/api/models", headers=self.auth(res))
        self.assertEqual(st, 200)
        self.assertEqual(out["catalog"][0]["name"], "aivd-fixture:tiny")
        self.assertIn("system", out)
        self.assertNotIn(str(self.td), json.dumps(out["policy"]))

    def test_pull_model_auth_csrf_allowlist_and_flow(self):
        body = {"model_id": "aivd-fixture:tiny"}
        st, _, _ = self.req("POST", "/api/ops/pull_model", body, {"Origin": self.origin})
        self.assertEqual(st, 401)
        res = self.pair()
        st, _, _ = self.req("POST", "/api/ops/pull_model", body, self.auth(res, csrf=False))
        self.assertEqual(st, 403)
        h = self.auth(res)
        h["Origin"] = "https://evil.example"
        self.assertEqual(self.req("POST", "/api/ops/pull_model", body, h)[0], 403)
        for bad in ({"model_id": "evil/model:latest"}, {"model_id": "llama3.1:70b"}):
            st, out, _ = self.req("POST", "/api/ops/pull_model", bad, self.auth(res))
            self.assertEqual(st, 400, out)
        st, _, _ = self.req("POST", "/api/ops/pull_model", dict(body, store="/tmp"), self.auth(res))
        self.assertEqual(st, 400)
        st, out, _ = self.req("POST", "/api/ops/pull_model", body, self.auth(res))
        self.assertEqual(st, 202, out)
        for _ in range(100):
            st, out, _ = self.req("GET", "/api/models", headers=self.auth(res))
            if out["pull"] and out["pull"]["state"] != "running":
                break
            time.sleep(0.1)
        self.assertEqual(out["pull"]["state"], "succeeded", out["pull"])
        self.assertEqual(out["catalog"][0]["install"]["status"], "installed")
        st, out, _ = self.req("POST", "/api/ops/pull_model", body, self.auth(res))
        self.assertEqual((st, out["status"]), (200, "ALREADY_INSTALLED"))
        self.assertEqual(self.req("POST", "/api/ops/cancel_pull", {}, self.auth(res))[0], 409)


# ---------------------------------------------------------------- pipeline integration
class PipelineModelTests(ModelEnv, TP.PipelineBase):
    def mctl(self, fixtures=None, models=None, avail=6_500_000, **kw):
        fx, e = fixture_model()
        cfg = self.setup_models(models or [e], fixtures if fixtures is not None else {"aivd-fixture:tiny": fx})
        cfg.update(kw)
        c = self.pctl(mem=avail, env={"PATH": os.environ.get("PATH", "")}, **cfg)
        return c, fx, e

    def test_auto_pull_on_pipeline_then_verify(self):
        c, fx, e = self.mctl()
        doc = self.run_to_end(c, model_id="aivd-fixture:tiny", auto_pull=True)
        s = self.step(doc, "model")
        self.assertEqual(s["status"], "PASS", s["reason"])
        self.assertEqual(s["details"]["install_before"], "missing")
        self.assertEqual(s["details"]["install_after"], "installed")
        self.assertEqual(s["details"]["pull"]["outcome"], "succeeded")
        self.assertIsInstance(s["details"]["pull"]["duration_s"], float)
        self.assertTrue(s["details"]["verify"]["ok"])
        self.assertTrue(s["details"]["ollama_started"])
        self.assertTrue(s["details"]["pull"]["serve"]["stopped"])
        self.assertTrue(any(l["step"] == "model" and "layer" in l["line"] for l in doc["log"]))
        self.assertEqual(doc["options"]["model_id"], "aivd-fixture:tiny")
        pb = self.step(doc, "partb")
        self.assertEqual(pb["status"], "BLOCKED")                       # a download never authorizes Part B
        ids = {i["id"]: i["state"] for i in pb["details"]["checklist"]}
        self.assertEqual(ids["MODEL_READY"], "PASS")
        self.assertEqual(ids["MODEL_ATTEMPT"], "FAIL")                  # catalog extra: not RC6-allowlisted
        self.assertEqual(doc["verdict"]["model"]["model_id"], "aivd-fixture:tiny")
        self.assertEqual(self.handoffs, [])

    def test_missing_without_confirmation_is_blocked_and_not_pulled(self):
        c, fx, e = self.mctl()
        doc = self.run_to_end(c, model_id="aivd-fixture:tiny", auto_pull=False)
        s = self.step(doc, "model")
        self.assertEqual(s["status"], "BLOCKED")
        self.assertIn("not confirmed", s["reason"])
        self.assertIsNone(self.env_keys())

    def test_exceeds_ram_blocked_with_exact_numbers_and_no_pull(self):
        fx, e = fixture_model()
        big = dict(e, size_bytes=40_000_000_000)
        c, _, _ = self.mctl(models=[big])
        doc = self.run_to_end(c, model_id="aivd-fixture:tiny", auto_pull=True)
        s = self.step(doc, "model")
        self.assertEqual(s["status"], "BLOCKED")
        self.assertRegex(s["reason"], r"required ~[\d,]+ kB vs MemAvailable 6,500,000 kB")
        self.assertIn("Not downloaded", s["reason"])
        self.assertIsNone(self.env_keys())
        self.assertFalse(s["details"]["ollama_started"])
        ids = {i["id"]: i["state"] for i in self.step(doc, "partb")["details"]["checklist"]}
        self.assertEqual(ids["MODEL_READY"], "FAIL")

    def test_installed_model_verified_without_starting_ollama(self):
        c, fx, e = self.mctl()
        install(self.store, fx, "aivd-fixture:tiny")
        doc = self.run_to_end(c, model_id="aivd-fixture:tiny", auto_pull=True)
        s = self.step(doc, "model")
        self.assertEqual(s["status"], "PASS", s["reason"])
        self.assertIn("not in the RC6 allowlist", s["reason"])
        self.assertFalse(s["details"]["ollama_started"])
        self.assertIsNone(self.env_keys())

    def test_unknown_model_rejected_and_no_model_skipped(self):
        c, fx, e = self.mctl()
        code, res = c.pipeline.start({"full_suite": False, "partb_confirm": "", "model_id": "evil:latest",
                                      "attempt_id": "", "auto_pull": True})
        self.assertEqual(code, 400)
        doc = self.run_to_end(c)
        self.assertEqual(self.step(doc, "model")["status"], "SKIPPED")

    def test_pipeline_refuses_while_pull_running(self):
        c, fx, e = self.mctl({"aivd-fixture:tiny": dict(fixture_model()[0], chunk=1000, delay=0.05)})
        th = threading.Thread(target=c.models.puller.pull, args=(c.models.by_name["aivd-fixture:tiny"], "op"))
        th.start()
        for _ in range(100):
            if c.models.puller.busy():
                break
            time.sleep(0.05)
        code, res = c.pipeline.start({"full_suite": False, "partb_confirm": "", "model_id": "", "attempt_id": "",
                                      "auto_pull": False})
        self.assertEqual(code, 409)
        self.assertEqual(c.op_pull({"model_id": "aivd-fixture:tiny"})[0], 409)
        c.models.puller.cancel()
        th.join(30)


if __name__ == "__main__":
    unittest.main()
