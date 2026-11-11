# cta:artifact CODE-001
"""Account operations for the banking demo."""

from __future__ import annotations

from dataclasses import dataclass, field


class InsufficientFundsError(ValueError):
    """Raised when a withdrawal exceeds the available balance."""


@dataclass
class Account:
    """A single account with a cent-precision balance and an operation history."""

    account_id: str
    balance_cents: int = 0
    history: list[tuple[str, int]] = field(default_factory=list)

    def deposit(self, amount_cents: int) -> None:
        if amount_cents <= 0:
            raise ValueError("deposit amount must be positive")
        self.balance_cents += amount_cents
        self.history.append(("deposit", amount_cents))

    def withdraw(self, amount_cents: int) -> None:
        """Debit the balance by ``amount_cents``, recording the operation."""
        if amount_cents <= 0:
            raise ValueError("withdrawal amount must be positive")
        if amount_cents > self.balance_cents:
            raise InsufficientFundsError("insufficient funds for withdrawal")
        self.balance_cents -= amount_cents
        self.history.append(("withdrawal", amount_cents))
