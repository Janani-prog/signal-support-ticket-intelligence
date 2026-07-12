"""Shared text-cleaning utilities for ticket ingestion (T1.3).

Applied to both the labeled (banking77) and unlabeled (Twitter CS) corpora so downstream
classification/clustering/retrieval see consistently normalized text.
"""

import re

import pandas as pd

_EMAIL_RE = re.compile(r"\S+@\S+\.\S+")
_PHONE_RE = re.compile(r"(?<!\d)(\+?\d[\d\-\.\s]{7,}\d)(?!\d)")
_URL_RE = re.compile(r"https?://\S+")
_HANDLE_RE = re.compile(r"@\w+")
_WHITESPACE_RE = re.compile(r"\s+")


def strip_pii_shaped_tokens(text: str) -> str:
    """Redacts email/phone/URL/@handle-shaped tokens as a precaution.

    Per SECURITY_AND_ACCESS.md §1: source datasets are public, but scrub anything
    incidentally-identifying (e.g. a real email pasted into a tweet) before it's persisted.
    """
    text = _EMAIL_RE.sub("[EMAIL]", text)
    text = _URL_RE.sub("[URL]", text)
    text = _PHONE_RE.sub("[PHONE]", text)
    text = _HANDLE_RE.sub("[HANDLE]", text)
    return text


def normalize_whitespace(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()


def clean_text(text: str) -> str:
    return normalize_whitespace(strip_pii_shaped_tokens(str(text)))


def clean_dataframe(df: pd.DataFrame, text_col: str) -> pd.DataFrame:
    """Cleans `text_col` in place, drops empty/duplicate rows on that column."""
    df = df.copy()
    df[text_col] = df[text_col].map(clean_text)
    df = df[df[text_col].str.len() > 0]
    df = df.drop_duplicates(subset=[text_col]).reset_index(drop=True)
    return df
