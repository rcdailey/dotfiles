"""Entry point for `python -m gh_review`."""

from __future__ import annotations

import sys

from .cli import build_parser
from .gh import GhError, check_deps, die


def main() -> None:
    args = build_parser().parse_args()
    check_deps()

    try:
        match args.command:
            case "view":
                from .commands.view import run

                run(
                    args.repo,
                    args.number,
                    show_all=args.show_all,
                    unanswered=args.unanswered,
                    since=args.since,
                    no_bots=args.no_bots,
                    max_body=args.max_body,
                )
            case "start":
                from .commands.start import run

                run(args.repo, args.number)
            case "delete":
                from .commands.delete import run

                run(args.review_id)
            case "comment":
                from .commands.comment import run

                run(
                    args.review_id,
                    args.path,
                    args.line,
                    args.body,
                    side=args.side,
                    start_line=args.start_line,
                    start_side=args.start_side,
                )
            case "reply":
                from .commands.reply import run

                run(
                    args.repo,
                    args.number,
                    args.comment_id,
                    args.body,
                )
    except GhError as exc:
        die(str(exc))
    except KeyboardInterrupt:
        sys.exit(130)
    except BrokenPipeError:
        sys.stderr.close()


if __name__ == "__main__":
    main()
