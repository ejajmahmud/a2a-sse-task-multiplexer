"""CLI for A2A SSE Task Multiplexer."""
import argparse
import json
from .core import A2ASSEMultiplexer


def main():
    parser = argparse.ArgumentParser(description="A2A SSE Task Multiplexer CLI")
    parser.add_argument("--demo", action="store_true", help="Demonstrate out-of-order SSE stream merging")
    args = parser.parse_args()

    mux = A2ASSEMultiplexer(["agent-a", "agent-b"])
    mux.ingest("agent-a", 2, "completed", {"result": "ok"})
    mux.ingest("agent-a", 1, "working", {"progress": 50})
    mux.ingest("agent-b", 1, "completed", {"result": "done"})
    print(json.dumps({"events": mux.drain_all(), "summary": mux.status_summary()}, indent=2))


if __name__ == "__main__":
    main()
