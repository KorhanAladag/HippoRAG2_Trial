"""
Application settings, loaded from the environment.

This is the pattern you will meet in production codebases, and the reasons
behind each piece are worth knowing:

WHY A .env FILE AT ALL
    Secrets and environment specific values must not live in the source tree,
    because the source tree goes into git and git history is forever. The same
    code has to run against a laptop, a staging box and production with
    different endpoints, so those values belong outside the code.

WHY A SETTINGS CLASS RATHER THAN os.getenv EVERYWHERE
    Scattered os.getenv calls fail late and quietly: a typo in a variable name
    surfaces three hours into an indexing run. Loading everything once, at
    import time, with types and validation, turns that into an error before
    any work starts.

WHY .env IS NOT READ IN PRODUCTION
    In a container or under systemd the variables are injected by the platform
    and no .env file exists. load_dotenv is written to never override what is
    already set, so the same code path works in both places.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Literal, Optional

from dotenv import load_dotenv

# override=False is deliberate. Real environment variables always win over the
# file, which is what lets the same image run in development and production.
load_dotenv(override=False)


class ConfigError(RuntimeError):
    """Raised when the configuration cannot produce a working application."""


# --- typed readers ---------------------------------------------------------
# Every value arrives from the environment as a string. These helpers convert
# and fail loudly, naming the variable, rather than raising a bare ValueError
# from somewhere deep in the call stack.

def _str(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _opt(name: str) -> Optional[str]:
    """Empty string and unset both mean 'not configured'."""
    value = os.getenv(name, "").strip()
    return value or None


def _int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from exc


def _float(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number, got {raw!r}") from exc


@dataclass(frozen=True)
class Settings:
    """
    Every value the application reads, resolved once.

    frozen=True means nothing can reassign a setting halfway through a run,
    which removes a whole class of confusing bugs.
    """

    # environment
    app_env: Literal["development", "staging", "production"]
    log_level: str

    # models
    llm_base_url: str
    embedding_base_url: str
    llm_api_key: Optional[str]
    extraction_model: str
    generation_model: str
    embedding_model: str
    embedding_batch_size: int

    # vector store
    vector_store_type: Literal["parquet", "qdrant", "chroma", "milvus"]
    qdrant_url: Optional[str]
    qdrant_api_key: Optional[str]

    # paths
    save_dir: str
    docs_folder: str
    metrics_file: str

    # chunking
    chunk_max_tokens: int
    chunk_overlap_tokens: int

    # graph
    synonymy_threshold: float

    # retrieval
    linking_top_k: int
    retrieval_top_k: int
    qa_top_k: int

    # ---------------------------------------------------------------
    @classmethod
    def load(cls) -> "Settings":
        settings = cls(
            app_env=_str("APP_ENV", "development"),
            log_level=_str("LOG_LEVEL", "INFO").upper(),
            llm_base_url=_str("LLM_BASE_URL", "http://localhost:11434/v1"),
            embedding_base_url=_str(
                "EMBEDDING_BASE_URL", "http://localhost:11434/v1/embeddings"
            ),
            llm_api_key=_opt("LLM_API_KEY"),
            extraction_model=_str("EXTRACTION_MODEL", "qwen2.5:7b-instruct"),
            generation_model=_str("GENERATION_MODEL", "qwen2.5:7b-instruct"),
            embedding_model=_str("EMBEDDING_MODEL", "bge-m3"),
            embedding_batch_size=_int("EMBEDDING_BATCH_SIZE", 16),
            vector_store_type=_str("VECTOR_STORE_TYPE", "qdrant"),
            qdrant_url=_opt("QDRANT_URL"),
            qdrant_api_key=_opt("QDRANT_API_KEY"),
            save_dir=_str("SAVE_DIR", "outputs"),
            docs_folder=_str("DOCS_FOLDER", "docs"),
            metrics_file=_str("METRICS_FILE", "build_metrics.json"),
            chunk_max_tokens=_int("CHUNK_MAX_TOKENS", 1000),
            chunk_overlap_tokens=_int("CHUNK_OVERLAP_TOKENS", 100),
            synonymy_threshold=_float("SYNONYMY_THRESHOLD", 0.8),
            linking_top_k=_int("LINKING_TOP_K", 5),
            retrieval_top_k=_int("RETRIEVAL_TOP_K", 200),
            qa_top_k=_int("QA_TOP_K", 5),
        )
        settings.validate()
        return settings

    # ---------------------------------------------------------------
    def validate(self) -> None:
        """
        Fail at startup rather than three hours into an indexing run.

        Every check here corresponds to a mistake that is easy to make and
        expensive to discover late.
        """
        problems: list[str] = []

        if self.app_env not in {"development", "production"}:
            problems.append(
                f"APP_ENV must be development or production, "
                f"got {self.app_env!r}"
            )

        if self.vector_store_type not in {"parquet", "qdrant", "chroma", "milvus"}:
            problems.append(
                f"VECTOR_STORE_TYPE must be parquet, qdrant, chroma or milvus, "
                f"got {self.vector_store_type!r}"
            )

        # The embeddings endpoint has a different path from chat completions.
        # Pointing both at /v1 is a common mistake and produces a confusing
        # 404 halfway through the first batch.
        if self.embedding_base_url.rstrip("/").endswith("/v1"):
            problems.append(
                "EMBEDDING_BASE_URL looks like a chat endpoint. Ollama expects "
                "/v1/embeddings for embeddings."
            )

        if not 0.0 < self.synonymy_threshold < 1.0:
            problems.append(
                f"SYNONYMY_THRESHOLD is a cosine similarity and must sit "
                f"between 0 and 1, got {self.synonymy_threshold}"
            )

        if self.qa_top_k > self.retrieval_top_k:
            problems.append(
                f"QA_TOP_K ({self.qa_top_k}) cannot exceed RETRIEVAL_TOP_K "
                f"({self.retrieval_top_k}): you cannot answer from more "
                f"passages than were retrieved."
            )

        if self.chunk_overlap_tokens >= self.chunk_max_tokens:
            problems.append(
                f"CHUNK_OVERLAP_TOKENS ({self.chunk_overlap_tokens}) must be "
                f"smaller than CHUNK_MAX_TOKENS ({self.chunk_max_tokens})."
            )

        # Production only rules. These would be annoying on a laptop and are
        # non negotiable on a shared machine.
        if self.app_env == "production":
            if self.vector_store_type == "parquet":
                problems.append(
                    "VECTOR_STORE_TYPE=parquet loads every embedding into the "
                    "process, roughly 0.85 MB per passage. Use qdrant in "
                    "production."
                )
            if self.qdrant_url and self.qdrant_url.startswith("http://") \
                    and "localhost" not in self.qdrant_url:
                problems.append(
                    "QDRANT_URL uses plain http to a remote host. Use https or "
                    "keep the traffic on localhost."
                )
            if self.qdrant_url and not self.qdrant_api_key \
                    and "localhost" not in self.qdrant_url:
                problems.append(
                    "A remote QDRANT_URL without QDRANT_API_KEY means an "
                    "unauthenticated vector database."
                )

        if problems:
            raise ConfigError(
                "Configuration is not usable:\n  - " + "\n  - ".join(problems)
            )

    # ---------------------------------------------------------------
    def describe(self) -> str:
        """
        Human readable summary, with secrets masked.

        Print this at the start of every run. When something behaves oddly two
        weeks from now, the log will say exactly what it was configured with.
        """
        def mask(value: Optional[str]) -> str:
            if not value:
                return "(not set)"
            return f"{value[:4]}...{value[-2:]}" if len(value) > 8 else "(set)"

        return "\n".join([
            f"environment    : {self.app_env}",
            f"extraction     : {self.extraction_model}",
            f"generation     : {self.generation_model}",
            f"embedding      : {self.embedding_model}",
            f"llm endpoint   : {self.llm_base_url}",
            f"llm api key    : {mask(self.llm_api_key)}",
            f"vector store   : {self.vector_store_type} "
            f"at {self.qdrant_url or 'local file'}",
            f"qdrant api key : {mask(self.qdrant_api_key)}",
            f"synonymy thr   : {self.synonymy_threshold}",
            f"top k          : linking {self.linking_top_k}, "
            f"retrieval {self.retrieval_top_k}, qa {self.qa_top_k}",
            f"save dir       : {self.save_dir}",
        ])


def _load_or_exit() -> Settings:
    """
    Load settings and turn a ConfigError into a clean message.

    A traceback is right for a bug in the code and wrong for a typo in a
    config file. The person who mistyped a variable needs to read one line,
    not twenty.
    """
    try:
        return Settings.load()
    except ConfigError as exc:
        print(f"\n{exc}\n", file=sys.stderr)
        print("Copy .env.example to .env and correct the values above.",
              file=sys.stderr)
        raise SystemExit(1)


# Loaded once at import. Every module does `from settings import settings`,
# so there is exactly one resolved configuration per process.
settings = _load_or_exit()