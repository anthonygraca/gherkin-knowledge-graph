# cta:artifact CODE-002
"""Transfer operations and the daily allowance for the banking demo."""

from __future__ import annotations

from dataclasses import dataclass, field

DAILY_TRANSFER_LIMIT_CENTS = 100_000


class DailyLimitExceededError(ValueError):
    """Raised when a transfer would push the day's total past the daily limit."""


@dataclass
class TransferLedger:
    """Accumulates transfers for one account against a daily allowance."""

    limit_cents: int = DAILY_TRANSFER_LIMIT_CENTS
    transferred_cents: int = 0
    entries: list[tuple[str, int]] = field(default_factory=list)

    def transfer(self, amount_cents: int) -> None:
        if amount_cents <= 0:
            raise ValueError("transfer amount must be positive")
        if self.transferred_cents + amount_cents >= self.limit_cents:
            raise DailyLimitExceededError("daily transfer limit exceeded")
        self.transferred_cents += amount_cents
        self.entries.append(("transfer", amount_cents))
