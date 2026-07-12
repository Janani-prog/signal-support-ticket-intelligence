# Signal — single container serving the FastAPI backend + static frontend on one port.
# HF Spaces Docker requirement: listen on port 7860, run as a non-root user with uid 1000.
# Also deployable to Render (or any host that injects its own $PORT) — CMD below respects $PORT
# if set, defaulting to 7860 for HF Spaces / plain `docker run` / docker-compose.

FROM python:3.12-slim

# hdbscan has C extensions that may not ship a prebuilt wheel for every platform/Python combo.
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1
WORKDIR $HOME/app

COPY --chown=user requirements.txt .
# torch must come from the CPU-only wheel index first — otherwise `pip install -r requirements.txt`
# pulls the default CUDA-enabled build from PyPI (~2GB+ of unused nvidia-*-cu12 packages), which
# contradicts this project's stated CPU-only/no-GPU-dependency constraint even though it would
# still run fine on CPU. Installing the exact version here first means the later `torch==2.5.1`
# line in requirements.txt is already satisfied (pip treats `==2.5.1` as matching `2.5.1+cpu`)
# and won't be reinstalled from the default index.
RUN pip install --no-cache-dir --user torch==2.5.1+cpu --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --user -r requirements.txt

COPY --chown=user . .

# Build-time pipeline: regenerate all model/data artifacts inside the image rather than copying
# them from the host (they're gitignored/dockerignored — see TECHNICAL_ARCHITECTURE.md §4's
# "baked into the image" option). This also proves the pipeline is genuinely reproducible from
# source. Only the scripts whose *output* the deployed API actually reads at runtime are run
# here — train_transformer.py / evaluate.py / eval_retrieval.py etc. are dev-time evaluation
# scripts whose results are already committed as static reports under reports/.
#
# No summarization-model warmup step here (there was one, for bart-large-cnn) — Phase 7 switched
# summarization to a scikit-learn-only extractive approach (see src/retrieval/summarize.py) after
# bart-large-cnn's ~1.6GB memory footprint OOM'd on Render's 512MB free tier. Nothing to warm up.
RUN python -m src.data.ingest_banking77 \
    && python -m src.data.ingest_twitter_support \
    && python -m src.classification.train_baseline \
    && python -m src.clustering.cluster \
    && python -m src.retrieval.build_index

EXPOSE 7860
ENV PORT=7860 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    TOKENIZERS_PARALLELISM=false \
    MALLOC_ARENA_MAX=2
# Free-tier memory is the binding constraint (Render's 512MB cap), not CPU throughput — limiting
# BLAS/OpenMP thread pools and glibc malloc arenas (a well-known technique for multi-threaded
# Python services in containers) trades a little single-request latency for materially lower RSS,
# since each thread/arena otherwise gets its own allocation buffers.

# Shell form (not exec form) so $PORT is expanded at container start.
CMD python -m uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT}
