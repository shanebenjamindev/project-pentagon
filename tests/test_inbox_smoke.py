"""Smoke tests for manager inbox flows; all paths and AI startup are mocked."""
import json
import os
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))
import pt_manager as pm


class InboxSmoke(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_tasks = pm.TASKS
        pm.TASKS = self.tmp.name
        self.env = mock.patch.dict(os.environ, {"ORCH_DATA": self.tmp.name})
        self.env.start()
        self.tid = "demo"
        os.makedirs(os.path.join(self.tmp.name, self.tid, "manager"))
        with open(os.path.join(self.tmp.name, self.tid, "status"), "w") as f:
            f.write("state=cho\nstep=2\n")
        self.started = []
        self.stack = [
            mock.patch.object(pm.tracker, "manager_info", return_value={"running": False, "pid": 0}),
            mock.patch.object(pm, "session_started", return_value=True),
            mock.patch.object(pm, "start_turn", side_effect=self.fake_start),
            mock.patch.object(pm, "progress"),
            mock.patch.object(pm, "set_size"),
            mock.patch.object(pm, "classify_turn", return_value="vua"),
        ]
        for p in self.stack:
            p.start()

    def tearDown(self):
        for p in reversed(self.stack):
            p.stop()
        pm.TASKS = self.old_tasks
        self.env.stop()
        self.tmp.cleanup()

    def fake_start(self, tid, prompt, **kwargs):
        self.started.append(prompt)
        return 123

    def inbox_file(self):
        return os.path.join(pm.mdir(self.tid), "inbox.jsonl")

    def write_inbox(self, *texts):
        with open(self.inbox_file(), "w", encoding="utf-8") as f:
            for text in texts:
                f.write(json.dumps({"text": text, "size": "auto", "model": ""}) + "\n")

    def test_pending_cleared_when_preparation_raises(self):
        with mock.patch.object(pm, "append_event", side_effect=OSError("disk")):
            with self.assertRaises(OSError):
                pm.send(self.tid, "hello", size="nho")
        self.assertFalse(pm.get(self.tid, "pending"))

    def test_thread_start_failure_clears_pending(self):
        pm.put(self.tid, "size", "vua")
        class BrokenThread:
            def __init__(self, *args, **kwargs):
                pass
            def start(self):
                raise OSError("thread unavailable")
        with mock.patch.object(pm.threading, "Thread", BrokenThread):
            with self.assertRaises(OSError):
                pm.send(self.tid, "new request", reaper=True, size="auto")
        self.assertFalse(pm.get(self.tid, "pending"))

    def test_send_after_stop_merges_old_then_new_and_starts(self):
        self.write_inbox("old")
        pm.put(self.tid, "inbox.paused", "1")
        pm.send(self.tid, "new", size="auto")
        self.assertEqual(len(self.started), 1)
        self.assertLess(self.started[0].index("old"), self.started[0].index("new"))
        self.assertFalse(os.path.exists(os.path.join(pm.mdir(self.tid), "inbox.paused")))
        self.assertFalse(os.path.exists(self.inbox_file()))

    def test_send_during_retry_starts_immediately(self):
        pm.put(self.tid, "retry_at", int(__import__("time").time()) + 3600)
        result = pm.send(self.tid, "now", size="nho")
        self.assertEqual(result, {"queued": False})
        self.assertEqual(len(self.started), 1)

    def test_cancel_clears_inbox(self):
        self.write_inbox("discard")
        pm.cancel_task(self.tid)
        self.assertFalse(os.path.exists(self.inbox_file()))

    def test_drain_failure_restores_claimed_messages(self):
        self.write_inbox("keep")
        with mock.patch.object(pm, "start_turn", side_effect=RuntimeError("start failed")):
            with self.assertRaises(RuntimeError):
                pm.drain_inbox(self.tid)
        self.assertTrue(os.path.exists(self.inbox_file()))
        with open(self.inbox_file(), encoding="utf-8") as f:
            self.assertIn("keep", f.read())
        self.assertFalse(any(n.startswith("inbox.claimed.") for n in os.listdir(pm.mdir(self.tid))))

    def test_stale_classification_pending_expires_after_ten_minutes(self):
        pm.put(self.tid, "pending", "Quản lý đang phân loại cỡ task để chọn model…")
        pending = os.path.join(pm.mdir(self.tid), "pending")
        old = time.time() - 601
        os.utime(pending, (old, old))
        with mock.patch.object(pm.tracker, "task_ids", return_value=[self.tid]):
            pm.check_queue()
        self.assertFalse(pm.get(self.tid, "pending"))

    def test_run_paused_inbox_busy_keeps_pause_and_clears_retry(self):
        pm.put(self.tid, "inbox.paused", "1")
        pm.put(self.tid, "retry_at", int(time.time()) + 3600)
        with mock.patch.object(pm.tracker, "manager_info", return_value={"running": True, "pid": 123}):
            with self.assertRaisesRegex(RuntimeError, "quản lý đang bận"):
                pm.run_paused_inbox(self.tid)
        self.assertTrue(os.path.exists(os.path.join(pm.mdir(self.tid), "inbox.paused")))
        self.assertFalse(pm.get(self.tid, "retry_at"))

    def test_enqueue_normalizes_invalid_size_to_auto(self):
        with pm.inbox_lock(self.tid):
            pm.enqueue_inbox_locked(self.tid, "hello", "not-a-size", "", "", "")
        with open(self.inbox_file(), encoding="utf-8") as f:
            row = json.loads(f.readline())
        self.assertEqual(row["size"], "auto")

    def test_check_queue_catches_oserror_per_task(self):
        qf = os.path.join(pm.mdir(self.tid), "queued.txt")
        with open(qf, "w", encoding="utf-8") as f:
            f.write("waiting")
        with mock.patch.object(pm.tracker, "task_ids", return_value=[self.tid]), \
             mock.patch.object(pm, "start_turn", side_effect=OSError("disk unavailable")):
            pm.check_queue()
        self.assertTrue(os.path.exists(qf))
        self.assertTrue(os.path.exists(os.path.join(pm.mdir(self.tid), "event-throttle-queue-error")))


if __name__ == "__main__":
    unittest.main()
