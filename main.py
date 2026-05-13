"""Savia firmware (Python) — entry point."""

import logging

from savia import app


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app.run()


if __name__ == "__main__":
    main()
