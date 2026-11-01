"""Original synthetic corrected implementation, independent of the policy oracle."""

import sys
from datetime import date


def late_fee(due: date, paid: date) -> int:
    grace = 7 if due >= date(2026, 11, 1) else 5
    return 2500 if (paid - due).days > grace else 0


if __name__ == "__main__":
    print(late_fee(date.fromisoformat(sys.argv[1]), date.fromisoformat(sys.argv[2])))
