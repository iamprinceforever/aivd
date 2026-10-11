"""Child stop handling: children start with default SIGINT/SIGTERM even when the controller ignores them, and
timeouts escalate SIGINT -> SIGTERM -> SIGKILL. Only throwaway `python -c` children are started; nothing here
touches the research repo, Ollama, or any gate."""
import os
import signal
import subprocess
import sys
import time
import unittest
from unittest import mock

from controller import procs as PR
from controller import server as S
from controller.tests import test_controller as TC
from controller.tests.test_pipeline import PipelineBase

SLEEPER = "print('ready', flush=True); import time; time.sleep(60)"
TRAP_INT = ("import signal, time; signal.signal(signal.SIGINT, signal.SIG_IGN); print('ready', flush=True); "
            "time.sleep(60)")
TRAP_BOTH = ("import signal, time; signal.signal(signal.SIGINT, signal.SIG_IGN); "
             "signal.signal(signal.SIGTERM, signal.SIG_IGN); print('ready', flush=True); time.sleep(60)")
POSIX = PR.HAS_KILLPG


class SigintIgnoredMixin:
    """Simulate a controller started as a background job (`cmd &` in a non-interactive shell): SIGINT is SIG_IGN
    in the controller process itself, and an ignored disposition is inherited across fork+exec."""

    def ignore_sigint(self):
        prev = signal.signal(signal.SIGINT, signal.SIG_IGN)
        self.addCleanup(signal.signal, signal.SIGINT, prev)


@unittest.skipUnless(POSIX, "process groups / signals are POSIX-only")
class PipelineStopTests(SigintIgnoredMixin, PipelineBase):
    def run_cmd(self, code, timeout=1, grace=1):
        c = self.pctl()
        c.pipeline.stop_grace = grace
        seen = []
        t0 = time.time()
        rc, lines, to = c.pipeline._run_cmd([sys.executable, "-c", code], str(self.td),
                                            {"PATH": os.environ.get("PATH", "")}, timeout, seen.append)
        return c, rc, lines, to, time.time() - t0, seen

    def test_timeout_works_when_controller_ignores_sigint(self):
        self.ignore_sigint()
        c, rc, lines, to, dt, seen = self.run_cmd(SLEEPER)
        self.assertTrue(to)
        self.assertEqual(lines[0], "ready\n")
        self.assertEqual(c.pipeline.last_stop_signal, "SIGINT")   # the child got default SIGINT back
        self.assertLess(dt, 10)
        self.assertIn("<step timeout: process group stopped by SIGINT>", seen)

    def test_child_trapping_sigint_is_escalated_to_sigterm(self):
        c, rc, lines, to, dt, _ = self.run_cmd(TRAP_INT, timeout=2)
        self.assertTrue(to)
        self.assertEqual(c.pipeline.last_stop_signal, "SIGTERM")
        self.assertEqual(rc, -signal.SIGTERM)
        self.assertLess(dt, 15)

    def test_child_trapping_sigint_and_sigterm_is_escalated_to_sigkill(self):
        self.ignore_sigint()
        c, rc, lines, to, dt, _ = self.run_cmd(TRAP_BOTH, timeout=2)
        self.assertTrue(to)
        self.assertEqual(c.pipeline.last_stop_signal, "SIGKILL")
        self.assertEqual(rc, -signal.SIGKILL)
        self.assertLess(dt, 15)

    def test_no_timeout_records_no_stop_signal(self):
        c, rc, lines, to, dt, _ = self.run_cmd("print('ok')", timeout=10)
        self.assertFalse(to)
        self.assertEqual(rc, 0)
        self.assertIsNone(c.pipeline.last_stop_signal)


@unittest.skipUnless(POSIX, "process groups / signals are POSIX-only")
class RunnerStopTests(SigintIgnoredMixin, TC.Base):
    """The guarded runner path (server._spawn/_wait) with the same mocked entry script GateTests uses."""
    all_pass_ctl = TC.GateTests.all_pass_ctl
    body = TC.GateTests.body
    wait_done = TC.GateTests.wait_done

    def test_runner_timeout_works_when_controller_ignores_sigint(self):
        self.ignore_sigint()
        c, _ = self.all_pass_ctl(run_sleep=30)
        c.cfg["max_run_seconds"] = 1
        c.cfg["stop_grace_s"] = 1
        self.assertEqual(c.op_run(self.body())[0], 202)
        t0 = time.time()
        r = self.wait_done(c, 15)
        self.assertEqual(r["state"], "timeout")
        self.assertEqual(r["stopped_by"], "SIGINT")
        self.assertLess(time.time() - t0, 15)


@unittest.skipUnless(POSIX, "process groups / signals are POSIX-only")
class ProcsUnitTests(SigintIgnoredMixin, unittest.TestCase):
    def spawn(self, code):
        p = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, stdin=subprocess.DEVNULL,
                             **PR.spawn_kwargs())
        self.addCleanup(lambda: (p.poll() is None and p.kill(), p.stdout.close()))
        self.assertEqual(p.stdout.readline(), b"ready\n")
        return p

    def test_children_start_with_default_sigint_even_if_parent_ignores_it(self):
        self.ignore_sigint()
        p = subprocess.Popen([sys.executable, "-c", "import signal; print(signal.getsignal(signal.SIGINT) is "
                              "signal.default_int_handler)"], stdout=subprocess.PIPE, **PR.spawn_kwargs())
        self.assertEqual(p.communicate(timeout=20)[0].strip(), b"True")
        q = subprocess.Popen([sys.executable, "-c", "import signal; print(signal.getsignal(signal.SIGINT) is "
                              "signal.SIG_IGN)"], stdout=subprocess.PIPE, start_new_session=True)
        self.assertEqual(q.communicate(timeout=20)[0].strip(), b"True")   # what happened before the fix

    def test_stop_escalation_order(self):
        self.assertEqual(PR.stop(self.spawn(SLEEPER), 1), "SIGINT")
        self.assertEqual(PR.stop(self.spawn(TRAP_INT), 1), "SIGTERM")
        self.assertEqual(PR.stop(self.spawn(TRAP_BOTH), 1), "SIGKILL")

    def test_already_exited(self):
        p = subprocess.Popen([sys.executable, "-c", "pass"], **PR.spawn_kwargs())
        p.wait(timeout=20)
        self.assertEqual(PR.stop(p, 1), "exited")

    def test_new_session_so_group_signals_never_reach_the_controller(self):
        p = self.spawn(SLEEPER)
        self.assertNotEqual(os.getpgid(p.pid), os.getpgid(0))
        PR.stop(p, 1)

    def test_fallback_without_killpg_uses_terminate_then_kill(self):
        with mock.patch.object(PR, "HAS_KILLPG", False):
            self.assertEqual(set(PR.spawn_kwargs()), {"creationflags"})
            self.assertEqual(PR.stop(self.spawn(SLEEPER), 1), "terminate")
            self.assertEqual(PR.stop(self.spawn(TRAP_BOTH), 1), "kill")


class StopGraceConfigTests(TC.Base):
    def test_stop_grace_config_range(self):
        self.assertEqual(self.cfg(stop_grace_s=7)["stop_grace_s"], 7)
        for bad in (0, 121, True, "5"):
            with self.subTest(bad=bad), self.assertRaises(S.ConfigError):
                self.cfg(stop_grace_s=bad)


if __name__ == "__main__":
    unittest.main()
