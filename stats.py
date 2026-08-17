"""
Turn the measured graph into a capacity plan.

    python stats.py
"""

import json
from pathlib import Path

from settings import settings

PAPER_EDGES_PER_PASSAGE = 120
PAPER_MB_PER_PASSAGE = 0.85  # 9.9 GB over 11,656 passages, parquet backend


def human(mb: float) -> str:
    if mb < 1024:
        return f"{mb:.0f} MB"
    if mb < 1024 * 1024:
        return f"{mb / 1024:.1f} GB"
    return f"{mb / 1024 / 1024:.1f} TB"


def main() -> None:
    path = Path(settings.metrics_file)
    if not path.exists():
        raise SystemExit(f"No {settings.metrics_file}. Run index.py first.")

    m = json.loads(path.read_text())
    passages = m.get("passages") or 0
    if not passages:
        raise SystemExit("No passages recorded. Did indexing finish?")

    epp = m["edges_per_passage"]
    spp = m["seconds_per_passage"]

    print("=" * 70)
    print("MEASURED ON YOUR CORPUS")
    print("=" * 70)
    print(f"documents           {m['documents']:,}")
    print(f"passages            {passages:,}")
    print(f"phrase nodes        {m['phrase_nodes']:,}")
    print(f"edges               {m['total_edges']:,}")
    print(f"  extracted         {m['extracted_triples']:,}")
    print(f"  synonymy          {m['synonymy_triples']:,}  "
          f"({m['synonymy_share']:.0%})")
    print(f"  passage links     {m['triples_with_passage']:,}")
    print(f"\nedges per passage   {epp}   (paper: {PAPER_EDGES_PER_PASSAGE})")
    print(f"seconds per passage {spp}")
    print(f"synonymy threshold  {m['synonymy_threshold']}")

    ratio = epp / PAPER_EDGES_PER_PASSAGE
    print("\n" + "-" * 70)
    if ratio > 1.3:
        print(f"Your corpus is {ratio:.1f}x denser than the paper's.")
        print("Technical text reuses terminology, which multiplies synonym")
        print("edges. Raise SYNONYMY_THRESHOLD to 0.85 and measure again.")
    elif ratio < 0.7:
        print(f"Your corpus is {ratio:.1f}x sparser than the paper's.")
        print("Check that extraction is finding entities at all before")
        print("treating a small graph as good news.")
    else:
        print(f"Density is close to the paper ({ratio:.1f}x), so its published")
        print("scaling behaviour should transfer reasonably well.")

    print("\n" + "=" * 70)
    print("PROJECTION")
    print("=" * 70)
    print(f"{'passages':>12}  {'edges':>14}  {'RAM if parquet':>15}  {'index':>10}")
    print("-" * 70)
    for target in (10_000, 100_000, 1_000_000, 10_000_000):
        hours = spp * target / 3600
        t = f"{hours:.1f} h" if hours < 48 else f"{hours / 24:.0f} d"
        print(f"{target:>12,}  {int(epp * target):>14,}  "
              f"{human(PAPER_MB_PER_PASSAGE * target):>15}  {t:>10}")

    if settings.vector_store_type == "qdrant":
        print("\nThe RAM column is what the parquet backend would have needed.")
        print("You are on Qdrant, so that memory lives in the vector service")
        print("rather than the Python process.")
    else:
        print(f"\nVECTOR_STORE_TYPE={settings.vector_store_type}: the RAM column")
        print("applies to you directly. Switch to qdrant before it bites.")
    print("=" * 70)


if __name__ == "__main__":
    main()
