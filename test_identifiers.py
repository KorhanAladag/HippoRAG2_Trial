"""
Check whether exact identifiers survive indexing and retrieval.

Dense embeddings are weak on literal strings: a query for ERR-42 can rank
ERR-24 just as highly. Worse, if extraction never made the code a phrase node,
the graph cannot help at all. No published benchmark tests this, because none
of their corpora contains part numbers.

    python test_identifiers.py X200 ERR-42 F-12
"""

import sys

from hippo_factory import banner, build_hipporag, setup_logging


def main(tokens: list[str]) -> None:
    setup_logging()
    banner("IDENTIFIER TEST")

    hipporag = build_hipporag()
    phrases = list(hipporag.entity_embedding_store.get_all_texts())

    for token in tokens:
        low = token.lower()
        print("=" * 70)
        print(f"identifier: {token}")

        exact = [p for p in phrases if low == p.lower()]
        partial = [p for p in phrases if low in p.lower() and low != p.lower()]

        if exact:
            print(f"  exact phrase node : {exact[0]}")
        elif partial:
            print(f"  folded into       : {', '.join(partial[:5])}")
            print("  -> extraction merged it into a longer phrase.")
        else:
            print("  NOT a phrase node.")
            print("  -> extraction dropped it. Dense retrieval will not find")
            print("     it reliably. This is the case for a lexical index over")
            print("     the raw text, in PostgreSQL or Qdrant sparse vectors.")

        solutions = hipporag.retrieve(
            queries=[f"What information is available about {token}?"],
            num_to_retrieve=3,
        )
        print("\n  top passages:")
        for i, doc in enumerate(solutions[0].docs[:3], 1):
            hit = "HIT " if low in doc.lower() else "MISS"
            print(f"    {i}. [{hit}] {doc.replace(chr(10), ' ')[:150]}...")

        print(f"\n  A MISS at rank 1 means the system answered about something")
        print(f"  other than {token}. On a manual corpus that is the failure")
        print("  that matters most, and aggregate scores hide it.")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python test_identifiers.py X200 ERR-42 ...")
    main(sys.argv[1:])
