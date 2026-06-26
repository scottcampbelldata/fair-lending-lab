"""DB engine + dataframe helper."""
from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache

import pandas as pd
import psycopg
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from flab.config import get_settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_engine(get_settings().database_url, pool_pre_ping=True, future=True)


@contextmanager
def get_conn():
    s = get_settings()
    with psycopg.connect(s.psycopg_dsn) as conn:
        yield conn


def fetch_df(sql: str, params: dict | None = None) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(sql, conn, params=params)
