"""Apply the versioned schema to the dedicated build database only."""
import os
from packages.operations.ledger import Ledger

if __name__ == "__main__":
    Ledger(os.environ["DATABASE_URL"]).initialize()
    print("Dedicated schema migration complete.")
