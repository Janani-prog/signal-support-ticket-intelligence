# Signal — single container serving the FastAPI backend + static frontend on one port.
# HF Spaces Docker requirement: listen on port 7860, run as a non-root user with uid 1000.

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
# The summarization model is also warmed here (not just at first request) so container startup
# loads it from the local image layer instead of downloading ~1.6GB over the network on every
# cold start — directly addresses the CPU-latency concern TECHNICAL_ARCHITECTURE.md §2.2 flags
# for free-tier hosting.
RUN python -m src.data.ingest_banking77 \
    && python -m src.data.ingest_twitter_support \
    && python -m src.classification.train_baseline \
    && python -m src.clustering.cluster \
    && python -m src.retrieval.build_index \
    && python -c "from transformers import pipeline; pipeline('summarization', model='facebook/bart-large-cnn')"

EXPOSE 7860

CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
