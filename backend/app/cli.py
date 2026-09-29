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
from app.services.users import seed_users

logger = logging.getLogger("app.cli")

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_USERS_FILE = REPO_ROOT / "seed" / "users.json"


def cmd_seed_users(path: Path) -> None:
    records = json.loads(path.read_text(encoding="utf-8"))
    with SessionLocal.begin() as db:
        created, skipped = seed_users(db, records)
    logger.info("seed_users", extra={"users_created": created, "users_skipped_existing": skipped})


def main(argv: list[str] | None = None) -> None:
    configure_logging(get_settings().log_level)
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    p_seed = sub.add_parser("seed-users", help="create users from a JSON file")
    p_seed.add_argument("--file", type=Path, default=DEFAULT_USERS_FILE)

    args = parser.parse_args(argv)
    if args.command == "seed-users":
        cmd_seed_users(args.file)


if __name__ == "__main__":
    main()
