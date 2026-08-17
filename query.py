"""
Ask questions against the indexed graph, and measure latency.

Two modes, and the difference is a debugging tool:
  qa        full pipeline, writes an answer
  retrieve  passages only, which isolates retrieval from the answer model

When an answer is wrong, run retrieve first. If the right passage never came
back, changing the answer model will not help.

    python query.py
    python query.py --retrieve
    python query.py "one question"
"""

import argparse
import statistics
import time
from pathlib import Path

from hippo_factory import banner, build_hipporag, setup_logging

QUESTIONS_FILE = "questions.txt"


def load_questions() -> list[str]:
    path = Path(QUESTIONS_FILE)
    if not path.exists():
        raise SystemExit(
            f"No {QUESTIONS_FILE}. Write 20 to 30 real questions there, "
            f"one per line. A question set from the people who will use the "
            f"system is worth more than any published benchmark."
        )
    return [q.strip() for q in path.read_text().splitlines() if q.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question", nargs="*", help="ask a single question")
    parser.add_argument("--retrieve", action="store_true",
                        help="show retrieved passages instead of answers")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    setup_logging()
    banner("RETRIEVAL" if args.retrieve else "QUESTION ANSWERING")

    questions = args.question or load_questions()
    hipporag = build_hipporag()

    latencies: list[float] = []
    for question in questions:
        started = time.perf_counter()

        if args.retrieve:
            solutions = hipporag.retrieve(queries=[question],
                                          num_to_retrieve=args.top_k)
            took = time.perf_counter() - started
            print(f"\nQ: {question}")
            for i, doc in enumerate(solutions[0].docs[: args.top_k], 1):
                print(f"  {i}. {doc.replace(chr(10), ' ')[:180]}...")
        else:
            solutions, _, _ = hipporag.rag_qa(queries=[question])
            took = time.perf_counter() - started
            print(f"\nQ: {question}")
            print(f"A: {solutions[0].answer}")

        latencies.append(took)
        print(f"   [{took:.1f}s]")

    if len(latencies) > 1:
        ordered = sorted(latencies)
        p95 = ordered[max(0, int(len(ordered) * 0.95) - 1)]
        print("\n" + "=" * 70)
        print(f"questions {len(latencies)}   "
              f"median {statistics.median(latencies):.1f}s   p95 {p95:.1f}s")
        print("Reference: the paper measures 1.2s per query with a served 70B.")
        print("=" * 70)


if __name__ == "__main__":
    main()
