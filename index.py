"""
Index a corpus and measure what it produces.

The reference figure is 120 edges per passage, measured by the HippoRAG 2
authors on MuSiQue. Technical documentation is not Wikipedia, so your ratio
will differ, and that difference is what sizes the deployment.

    python index.py
"""

import json
import time
from pathlib import Path

from hippo_factory import banner, build_hipporag, setup_logging
from settings import settings


def read_docs(folder: str) -> list[str]:
    """
    Read .txt and .md files. HippoRAG chunks internally, so whole documents
    go in rather than pre split pieces.
    """
    path = Path(folder)
    if not path.exists():
        raise SystemExit(
            f"DOCS_FOLDER points at '{folder}', which does not exist. "
            f"Create it or change DOCS_FOLDER in .env."
        )

    docs = [
        text
        for f in sorted(path.rglob("*"))
        if f.is_file() and f.suffix.lower() in {".txt", ".md"}
        if (text := f.read_text(encoding="utf-8", errors="ignore").strip())
    ]

    if not docs:
        raise SystemExit(f"No .txt or .md files found under '{folder}'.")
    return docs


def main() -> None:
    setup_logging()
    banner("INDEXING")

    docs = read_docs(settings.docs_folder)
    total_chars = sum(len(d) for d in docs)
    print(f"documents      : {len(docs):,}")
    print(f"characters     : {total_chars:,}\n")

    hipporag = build_hipporag()

    started = time.perf_counter()
    hipporag.index(docs=docs)
    elapsed = time.perf_counter() - started

    # get_graph_info reads the embedding stores and the edge map, so these are
    # the counts that were actually written, not what we hoped for.
    info = hipporag.get_graph_info()
    passages = info["num_passage_nodes"]

    metrics = {
        "documents": len(docs),
        "characters": total_chars,
        "passages": passages,
        "phrase_nodes": info["num_phrase_nodes"],
        "total_nodes": info["num_total_nodes"],
        "extracted_triples": info["num_extracted_triples"],
        "synonymy_triples": info["num_synonymy_triples"],
        "triples_with_passage": info["num_triples_with_passage_node"],
        "total_edges": info["num_total_triples"],
        "index_seconds": round(elapsed, 1),
        "extraction_model": settings.extraction_model,
        "embedding_model": settings.embedding_model,
        "synonymy_threshold": settings.synonymy_threshold,
        "vector_store": settings.vector_store_type,
    }

    if passages:
        metrics |= {
            "edges_per_passage": round(info["num_total_triples"] / passages, 1),
            "nodes_per_passage": round(info["num_total_nodes"] / passages, 1),
            "seconds_per_passage": round(elapsed / passages, 2),
            "synonymy_share": round(
                info["num_synonymy_triples"] / max(1, info["num_total_triples"]), 3
            ),
        }

    Path(settings.metrics_file).write_text(json.dumps(metrics, indent=2))

    print("\n" + "=" * 70)
    print(f"indexed in {elapsed / 60:.1f} min")
    print(f"passages {passages:,}   phrase nodes {info['num_phrase_nodes']:,}")
    print(f"edges    {info['num_total_triples']:,}")
    print(f"  extracted {info['num_extracted_triples']:,}   "
          f"synonymy {info['num_synonymy_triples']:,}   "
          f"passage {info['num_triples_with_passage_node']:,}")
    if passages:
        print(f"\nedges per passage  : {metrics['edges_per_passage']}   "
              f"(paper reports 120)")
        print(f"synonymy share     : {metrics['synonymy_share']:.0%}   "
              f"(paper is around 80%)")
        print(f"seconds per passage: {metrics['seconds_per_passage']}")
    print(f"\nmetrics written to {settings.metrics_file}")
    print("Next: python stats.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
