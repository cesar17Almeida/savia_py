"""Savia firmware (Python) — entry point."""

import argparse
import logging
from pathlib import Path

from savia import app, config


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="savia", description="Firmware estación Savia")
    p.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Ruta al TOML de configuración (opcional; defaults si se omite).",
    )
    return p.parse_args(argv)


def main() -> None:
    args = parse_args()
    cfg = config.load(args.config)
    logging.basicConfig(
        level=cfg.log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app.run(cfg)


if __name__ == "__main__":
    main()
