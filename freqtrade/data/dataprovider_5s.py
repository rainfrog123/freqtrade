"""5s DataProvider for Freqtrade.

Live/dry-run candles come from the TradingView SQLite collector.
Backtesting uses the normal DataProvider path (feather/json datadir).
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pandas as pd
from pandas import DataFrame

from freqtrade.constants import Config, ListPairsWithTimeframes
from freqtrade.data.dataprovider import DataProvider
from freqtrade.enums import RunMode


logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = "/allah/blue/trading/tools/realtime/tradingview/data/tv_candles.db"


def get_5s_db_path(config: Config) -> str | None:
    path = config.get("5s_database_path", DEFAULT_DB_PATH)
    return path if Path(path).exists() else None


class DP5s(DataProvider):
    """5s candle DataProvider — SQLite for live, parent class for backtest."""

    def __init__(self, config: Config, exchange=None, pairlists=None, rpc=None):
        super().__init__(config, exchange, pairlists, rpc)
        self._db = get_5s_db_path(config)
        self._symbol_map = config.get("5s_symbol_map", {})
        logger.info("DP5s: database %s", "ready" if self._db else "not found")

    def _is_backtest(self) -> bool:
        return self._config.get("runmode", RunMode.OTHER) == RunMode.BACKTEST

    def _map_symbol(self, pair: str) -> str:
        return self._symbol_map.get(pair, pair)

    def _load_5s(self, pair: str, limit: int = 500) -> DataFrame:
        if not self._db:
            logger.warning("DP5s: database not available")
            return DataFrame()
        try:
            symbol = self._map_symbol(pair)
            with sqlite3.connect(self._db) as conn:
                df = pd.read_sql_query(
                    "SELECT ts, open, high, low, close, volume FROM candles "
                    "WHERE symbol = ? ORDER BY ts DESC LIMIT ?",
                    conn,
                    params=(symbol, limit),
                )
            if df.empty:
                logger.warning("DP5s: no data for %s (symbol=%s)", pair, symbol)
                return df
            df["date"] = pd.to_datetime(df["ts"], unit="s", utc=True)
            return (
                df[["date", "open", "high", "low", "close", "volume"]]
                .sort_values("date")
                .reset_index(drop=True)
            )
        except Exception as e:
            logger.error("DP5s: error loading %s: %s", pair, e)
            return DataFrame()

    def ohlcv(
        self, pair: str, timeframe: str | None = None, copy: bool = True, candle_type: str = ""
    ) -> DataFrame:
        tf = timeframe or self._config.get("timeframe", "1h")
        if tf == "5s" and not self._is_backtest():
            df = self._load_5s(pair)
            return df.copy() if copy else df
        return super().ohlcv(pair, tf, copy, candle_type)

    def get_pair_dataframe(
        self, pair: str, timeframe: str | None = None, candle_type: str = ""
    ) -> DataFrame:
        tf = timeframe or self._config.get("timeframe", "1h")
        if tf == "5s" and not self._is_backtest():
            return self._load_5s(pair)
        return super().get_pair_dataframe(pair, tf, candle_type)

    def refresh(
        self,
        pairlist: ListPairsWithTimeframes,
        helping_pairs: ListPairsWithTimeframes | None = None,
    ) -> None:
        if self._is_backtest():
            super().refresh(pairlist, helping_pairs)
            return
        pl = [(p, t, c) for p, t, c in pairlist if t != "5s"]
        hp = [(p, t, c) for p, t, c in (helping_pairs or []) if t != "5s"] or None
        if pl or hp:
            super().refresh(pl, hp)
