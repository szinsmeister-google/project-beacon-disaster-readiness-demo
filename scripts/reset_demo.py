#!/usr/bin/env python3
"""Resets the Spanner `DeploymentPlan` table back to its clean pre-demo state."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.gcp import get_spanner_database


def main() -> None:
    db = get_spanner_database()

    def _clear(txn):
        txn.execute_update("DELETE FROM DeploymentPlan WHERE status IN ('Proposed', 'ACTIVE_DISPATCH')")

    db.run_in_transaction(_clear)
    print("Reset Project Beacon `DeploymentPlan` table cleanly.")


if __name__ == "__main__":
    main()
