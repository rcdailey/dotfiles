"""Entry point for `python -m research`."""

from research._error_ledger import run_with_error_ledger
from research.cli import cli

if __name__ == "__main__":
    run_with_error_ledger(cli)
