"""Operational commands.

python -m app.cli seed-users [--file ../seed/users.json]
"""

import argparse
import json
import logging
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.services.episode_import import import_episodes
from app.services.users import seed_users

logger = logging.getLogger("app.cli")

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_USERS_FILE = REPO_ROOT / "seed" / "users.json"
DEFAULT_EPISODES_FILE = REPO_ROOT / "seed" / "episodes.csv"


def cmd_seed_users(path: Path) -> None:
    records = json.loads(path.read_text(encoding="utf-8"))
    with SessionLocal.begin() as db:
        created, skipped = seed_users(db, records)
    logger.info("seed_users", extra={"users_created": created, "users_skipped_existing": skipped})


def cmd_import_episodes(path: Path) -> None:
    with path.open(encoding="utf-8-sig", newline="") as fh, SessionLocal.begin() as db:
        report = import_episodes(db, fh).as_dict()
    errors = report.pop("errors")
    logger.info("import_episodes", extra={"file": str(path), **report})
    for err in errors:
        logger.info("import_episodes.skipped_row", extra=err)


def main(argv: list[str] | None = None) -> None:
    configure_logging(get_settings().log_level)
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    p_seed = sub.add_parser("seed-users", help="create users from a JSON file")
    p_seed.add_argument("--file", type=Path, default=DEFAULT_USERS_FILE)

    p_import = sub.add_parser("import-episodes", help="import an episodes CSV export")
    p_import.add_argument("--file", type=Path, default=DEFAULT_EPISODES_FILE)

    args = parser.parse_args(argv)
    if args.command == "seed-users":
        cmd_seed_users(args.file)
    elif args.command == "import-episodes":
        cmd_import_episodes(args.file)


if __name__ == "__main__":
    main()
