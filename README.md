# hipporag-env

HippoRAG 2 on local Ollama with Qdrant, configured the way a production
service would be: nothing environment specific lives in the source tree.

## The configuration pattern

Three files matter, and the split between them is the point.

| file | committed | role |
|---|---|---|
| `.env.example` | yes | the contract. Every variable, documented, with safe defaults and blank secrets |
| `.env` | **no** | the real values on this machine. Ignored by git |
| `settings.py` | yes | loads, types and validates. Fails at startup, not mid run |

Why not scatter `os.getenv` calls through the code: a typo in a variable name
then surfaces three hours into an indexing run. Loading once, with validation,
turns that into a one second failure with a readable message.

Why `.env` is not read in production: under Docker or systemd the platform
injects the variables and no file exists. `load_dotenv(override=False)` means
real environment variables always win, so the same code runs in both places.

## Setup

    cp .env.example .env          # then edit
    pip install -r requirements.txt
    python check_config.py        # validates without contacting anything

    ollama pull qwen2.5:7b-instruct
    ollama pull bge-m3
    docker compose up -d

Confirm the services really are up, since `check_config.py` only checks values:

    curl http://localhost:11434/v1/models
    curl http://localhost:6333/collections
    nvidia-smi
    ollama ps                     # PROCESSOR column should read GPU

## Run

    python index.py                          index docs/ and measure
    python stats.py                          projection to a full corpus
    python query.py                          run questions.txt
    python query.py --retrieve               passages only, no answer model
    python test_identifiers.py X200 ERR-42
    python test_revision.py docs/new.txt     add then delete, verify clean

Override anything for a single run without touching `.env`:

    SYNONYMY_THRESHOLD=0.85 python index.py
    GENERATION_MODEL=qwen2.5:14b-instruct python query.py

## Why Qdrant from the first run

HippoRAG defaults to a parquet vector store that loads every embedding into
the Python process: about 0.85 MB per passage, so roughly 85 GB at 100,000
passages. Switching backends later means re-embedding the whole corpus. With
`APP_ENV=production` the settings module refuses to start on parquet for
exactly this reason.

## The numbers to watch

`index.py` writes `build_metrics.json`:

- **edges per passage**, against the paper's 120
- **synonymy share**, against the paper's roughly 80 percent
- **seconds per passage**, which sets the full index time
- **passages**, the denominator for everything else

`SYNONYMY_THRESHOLD` is the strongest lever on graph size, because most edges
are synonym edges. Raise it for a smaller graph, lower it for better recall.
