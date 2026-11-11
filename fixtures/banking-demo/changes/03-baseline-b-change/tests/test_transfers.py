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


def test_transfer_exactly_at_limit_is_permitted() -> None:
    """SCN-003: a transfer that brings the day's total to the limit is permitted.

    Baseline-b change: the documented boundary is now covered by a test. It fails
    against the current implementation of TransferLedger.transfer.
    """
    ledger = TransferLedger()
    ledger.transfer(DAILY_TRANSFER_LIMIT_CENTS)
    assert ledger.transferred_cents == DAILY_TRANSFER_LIMIT_CENTS
    assert ledger.entries == [("transfer", DAILY_TRANSFER_LIMIT_CENTS)]
