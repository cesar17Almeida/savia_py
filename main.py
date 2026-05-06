"""
Savia firmware (Python) — entry point.

Bootstrap order:
  1. Load config                       (savia.config)
  2. Create shared events / queues     (savia.events)
  3. Open SQLite                       (savia.storage)
  4. Start native threads (blocking I/O):
       - sensor reader                 (savia.sensors)
       - storage writer                (savia.storage)
  5. Run asyncio orchestrator          (savia.orchestrator)
       - BLE peripheral                (savia.ble)
       - LoRa uplink scheduler         (savia.lora)
       - Supervisor / watchdog         (savia.supervisor)
  6. ML inference is launched on demand as a multiprocessing.Process
     by the orchestrator                (savia.ml).
"""


def main() -> None:
    raise NotImplementedError("Skeleton — bootstrap to be implemented.")


if __name__ == "__main__":
    main()
