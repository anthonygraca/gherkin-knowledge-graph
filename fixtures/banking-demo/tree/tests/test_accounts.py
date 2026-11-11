# cta:artifact TEST-001
"""Tests for src/accounts.py — the verification chain of SCN-001."""

import pytest

from src.accounts import Account, InsufficientFundsError


def test_withdraw_debits_balance_and_records_history() -> None:
    account = Account("acct-1", balance_cents=10_000)
    account.withdraw(2_500)
    assert account.balance_cents == 7_500
    assert account.history == [("withdrawal", 2_500)]


def test_withdraw_rejects_amount_above_balance() -> None:
    account = Account("acct-1", balance_cents=1_000)
    with pytest.raises(InsufficientFundsError):
        account.withdraw(1_500)
    assert account.balance_cents == 1_000
    assert account.history == []


def test_withdraw_allows_fractional_amounts() -> None:
    """SCN-001 withdraws 10.50 from a 100.00 balance."""
    account = Account("acct-1", balance_cents=10_000)
    account.withdraw(1_050)
    assert account.balance_cents == 8_950
