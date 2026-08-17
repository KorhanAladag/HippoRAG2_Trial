"""
Construct the HippoRAG object from settings.

Kept separate from settings.py on purpose. settings.py answers "what is
configured" and has no knowledge of HippoRAG. This module answers "how do we
build the thing" and is the only place that imports the library. Swapping
engines later touches this file and nothing else.
"""

from __future__ import annotations

import logging

from settings import settings

logger = logging.getLogger(__name__)


def build_base_config():
    """Translate our settings into HippoRAG's BaseConfig."""
    from hipporag.utils.config_utils import BaseConfig

    return BaseConfig(
        # models
        llm_name=settings.extraction_model,
        llm_base_url=settings.llm_base_url,
        embedding_model_name=settings.embedding_model,
        embedding_base_url=settings.embedding_base_url,
        embedding_batch_size=settings.embedding_batch_size,
        # vector backend
        vector_store_type=settings.vector_store_type,
        qdrant_url=settings.qdrant_url,
        qdrant_api_key=settings.qdrant_api_key,
        # chunking
        preprocess_chunk_max_token_size=settings.chunk_max_tokens,
        preprocess_chunk_overlap_token_size=settings.chunk_overlap_tokens,
        # graph construction
        synonymy_edge_sim_threshold=settings.synonymy_threshold,
        # retrieval
        linking_top_k=settings.linking_top_k,
        retrieval_top_k=settings.retrieval_top_k,
        qa_top_k=settings.qa_top_k,
        save_dir=settings.save_dir,
        seed=42,
        temperature=0,
    )


def build_hipporag():
    """
    Build HippoRAG with a split extraction and answer model.

    HippoRAG accepts extraction_llm and qa_llm separately, so the split is
    native rather than a workaround. When both names match we pass one object
    and nothing is loaded twice.
    """
    from hipporag import HippoRAG

    config = build_base_config()

    if settings.extraction_model == settings.generation_model:
        return HippoRAG(global_config=config)

    # Two models: build a second LLM for answering only.
    from hipporag.llm import _get_llm_class

    qa_config = build_base_config()
    qa_config.llm_name = settings.generation_model
    return HippoRAG(global_config=config, qa_llm=_get_llm_class(qa_config))


def setup_logging() -> None:
    """Apply LOG_LEVEL from the environment. Called by every entry point."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def banner(title: str) -> None:
    """Print the resolved configuration at the start of a run."""
    print("=" * 70)
    print(title)
    print("-" * 70)
    print(settings.describe())
    print("=" * 70)
