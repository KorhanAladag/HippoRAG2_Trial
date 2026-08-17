"""
Test the revision cycle: add a manual, then remove it.

A superseded procedure that stays in the index is a safety problem for device
documentation, not an inconvenience. HippoRAG's delete() uses reference
counting, so a triple only goes if no remaining document produced it. This
verifies that on your data instead of trusting the description.

    python test_revision.py docs/new_manual.txt
"""

import sys
import time
from pathlib import Path

from hippo_factory import banner, build_hipporag, setup_logging


def snapshot(hipporag) -> dict:
    info = hipporag.get_graph_info()
    return {
        "passages": info["num_passage_nodes"],
        "phrases": info["num_phrase_nodes"],
        "edges": info["num_total_triples"],
    }


def show(label: str, s: dict) -> None:
    print(f"{label:<20} passages {s['passages']:>7,}   "
          f"phrases {s['phrases']:>7,}   edges {s['edges']:>9,}")


def main(doc_path: str) -> None:
    setup_logging()
    banner("REVISION TEST")

    text = Path(doc_path).read_text(encoding="utf-8", errors="ignore").strip()
    if not text:
        raise SystemExit(f"{doc_path} is empty.")

    hipporag = build_hipporag()

    before = snapshot(hipporag)
    show("before", before)

    print("\nadding...")
    t0 = time.perf_counter()
    hipporag.index(docs=[text])
    add_time = time.perf_counter() - t0
    show("after add", snapshot(hipporag))
    print(f"  {add_time:.1f}s")

    print("\ndeleting the same document...")
    t0 = time.perf_counter()
    hipporag.delete(docs_to_delete=[text])
    del_time = time.perf_counter() - t0
    after_del = snapshot(hipporag)
    show("after delete", after_del)
    print(f"  {del_time:.1f}s")

    print("\n" + "=" * 70)
    if after_del == before:
        print("Clean: the graph returned to its exact starting state.")
    else:
        print("Not identical, which can still be correct.")
        for key in ("passages", "phrases", "edges"):
            diff = after_del[key] - before[key]
            if diff:
                print(f"  {key}: {diff:+,} left behind")
        print("\nLeftover phrases and edges are expected when another document")
        print("also produced them: reference counting keeps shared facts alive.")
        print("Leftover passages are not expected and indicate a real problem.")

    print(f"\nadd {add_time:.1f}s, delete {del_time:.1f}s at this corpus size.")
    print("Delete rebuilds the retrieval objects, so it grows with the corpus.")
    print("Measure it again on the full corpus: this number decides whether")
    print("revisions stay practical.")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python test_revision.py path/to/manual.txt")
    main(sys.argv[1])
