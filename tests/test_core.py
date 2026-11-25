"""Tests for A2A SSE Task Multiplexer."""
import unittest
from a2a_sse_task_multiplexer.core import A2ASSEMultiplexer


class TestA2ASSEMultiplexer(unittest.TestCase):
    def test_reorders_out_of_order_frames(self):
        mux = A2ASSEMultiplexer(["t1"])
        mux.ingest("t1", 2, "completed")
        self.assertEqual(mux.drain_ordered("t1"), [])
        mux.ingest("t1", 1, "working")
        drained = mux.drain_ordered("t1")
        self.assertEqual([d["seq"] for d in drained], [1, 2])
        self.assertTrue(mux.status_summary()["all_done"])

    def test_deduplicates_duplicate_seq(self):
        mux = A2ASSEMultiplexer(["t1"])
        self.assertTrue(mux.ingest("t1", 1, "working"))
        self.assertFalse(mux.ingest("t1", 1, "working"))
        mux.drain_ordered("t1")
        self.assertFalse(mux.ingest("t1", 1, "working"))

    def test_multi_agent_barrier_summary(self):
        mux = A2ASSEMultiplexer(["a", "b"])
        mux.ingest("a", 1, "completed")
        mux.ingest("b", 1, "failed")
        mux.drain_all()
        summary = mux.status_summary()
        self.assertEqual(summary["completed"], 1)
        self.assertEqual(summary["failed"], 1)
        self.assertTrue(summary["all_done"])
