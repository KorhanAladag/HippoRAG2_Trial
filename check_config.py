"""
Validate configuration without touching any model or database.

Run this first on a new machine. It fails in a second on a typo rather than
three hours into an indexing run.

    python check_config.py
"""

from settings import settings

print("=" * 70)
print("CONFIGURATION")
print("=" * 70)
print(settings.describe())
print("=" * 70)
print("\nValid. Nothing was contacted: this only checks the values.")
print("Next: confirm the services are actually up.")
print(f"  curl {settings.llm_base_url}/models")
if settings.qdrant_url:
    print(f"  curl {settings.qdrant_url}/collections")
