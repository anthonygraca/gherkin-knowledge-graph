# cta:artifact TEST-002
"""Tests for src/transfers.py — the verification chain of SCN-003."""

import pytest

from src.transfers import DAILY_TRANSFER_LIMIT_CENTS, DailyLimitExceededError, TransferLedger


def test_transfer_under_the_daily_limit_is_recorded() -> None:
    ledger = TransferLedger()
    ledger.transfer(5_000)
    assert ledger.transferred_cents == 5_000
    assert ledger.entries == [("transfer", 5_000)]


def test_transfer_above_the_daily_limit_is_rejected() -> None:
    ledger = TransferLedger()
    with pytest.raises(DailyLimitExceededError):
        ledger.transfer(DAILY_TRANSFER_LIMIT_CENTS + 50_000)
    assert ledger.transferred_cents == 0
    assert ledger.entries == []
