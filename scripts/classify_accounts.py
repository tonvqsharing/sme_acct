"""Retroactively classify existing accounts by first digit.

Run after applying migration 4107c140af78.
Usage: python -m scripts.classify_accounts
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src.bricks.coa.domain import classify_account


def classify_existing_accounts(db_url: str = "sqlite:///./sme_acct.db") -> int:
    """Classify all existing accounts by first digit. Returns count updated."""
    engine = create_engine(db_url)
    updated = 0

    with Session(engine) as session:
        # Get all accounts without account_type
        rows = session.execute(
            text("SELECT id, code, account_type FROM accounts WHERE account_type IS NULL")
        ).fetchall()

        for row in rows:
            account_id, code, _ = row
            try:
                account_type = classify_account(code)
                session.execute(
                    text("UPDATE accounts SET account_type = :type WHERE id = :id"),
                    {"type": account_type.value, "id": account_id},
                )
                updated += 1
            except ValueError as e:
                print(f"Warning: Could not classify account {code}: {e}")

        session.commit()

    return updated


if __name__ == "__main__":
    count = classify_existing_accounts()
    print(f"Classified {count} accounts")
