"""Original synthetic fixture with the deliberate payment-date policy-selection defect."""

import sys
from datetime import date


def late_fee(due: date, paid: date) -> int:
    # BUG: the approved rule selects by due, not paid.
    grace = 7 if paid >= date(2026, 11, 1) else 5
    return 2500 if (paid - due).days > grace else 0


if __name__ == "__main__":
    print(late_fee(date.fromisoformat(sys.argv[1]), date.fromisoformat(sys.argv[2])))
