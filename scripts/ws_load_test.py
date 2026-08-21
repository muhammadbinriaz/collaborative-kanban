#!/usr/bin/env python3
"""Simple WebSocket load smoke test against a running API.

Usage:
  python scripts/ws_load_test.py --url ws://localhost:8000 --token <access_jwt> --board <board_id> --clients 20
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time

import websockets


async def one_client(url: str, token: str, board_id: str, duration: float) -> list[float]:
    latencies: list[float] = []
    uri = f"{url.rstrip('/')}/ws/boards/{board_id}?token={token}"
    async with websockets.connect(uri, ping_interval=20) as ws:
        end = time.perf_counter() + duration
        while time.perf_counter() < end:
            started = time.perf_counter()
            await ws.send(json.dumps({"type": "ping", "at": started}))
            try:
                await asyncio.wait_for(ws.recv(), timeout=5)
            except asyncio.TimeoutError:
                continue
            latencies.append((time.perf_counter() - started) * 1000)
            await asyncio.sleep(0.25)
    return latencies


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="ws://localhost:8000")
    parser.add_argument("--token", required=True)
    parser.add_argument("--board", required=True)
    parser.add_argument("--clients", type=int, default=10)
    parser.add_argument("--duration", type=float, default=10.0)
    args = parser.parse_args()

    results = await asyncio.gather(
        *[one_client(args.url, args.token, args.board, args.duration) for _ in range(args.clients)]
    )
    flat = [item for group in results for item in group]
    print(f"clients={args.clients} samples={len(flat)}")
    if flat:
        print(
            "latency_ms "
            f"p50={statistics.median(flat):.1f} "
            f"avg={statistics.mean(flat):.1f} "
            f"max={max(flat):.1f}"
        )


if __name__ == "__main__":
    asyncio.run(main())
