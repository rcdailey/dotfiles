"""Entry point for `python -m research`."""

import sys

from research._argv import normalize_arguments
from research._error_ledger import run_with_error_ledger
from research.cli import cli

if __name__ == "__main__":
    original_arguments = sys.argv[1:]
    sys.argv[1:] = normalize_arguments(sys.argv[1:])
    run_with_error_ledger(cli, original_arguments)
