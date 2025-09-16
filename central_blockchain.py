#!/usr/bin/env python3
"""
Central Blockchain Development
--------------------------------
A simple, educational blockchain implemented as a *centralized system*:
- A single authority (CentralBlockchain) manages the canonical chain.
- Clients would submit transactions/blocks to this authority instead of peer-to-peer consensus.

Features:
- Block structure with index, timestamp, data, prev_hash, hash, nonce
- Proof-of-Work mining with adjustable difficulty
- setBlock, getBlock, blocksExplorer, mineBlock methods
- Simple CLI to add and explore blocks
- Optional Flask API to run the central authority as a small HTTP service

Usage (CLI):
    python central_blockchain.py --add "Hello"
    python central_blockchain.py --list
    python central_blockchain.py --get 1
    python central_blockchain.py --mine "Pay 10 to Alice" --difficulty 3

Usage (Server - optional):
    python central_blockchain.py --serve --port 5000 --difficulty 3
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
from time import time
from typing import List, Optional, Any
import argparse
import json
import os

# -----------------------
# Block structure
# -----------------------
@dataclass
class Block:
    index: int
    timestamp: float
    data: Any
    previous_hash: str
    nonce: int = 0
    hash: str = ""

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of the block contents (excluding the 'hash' field)."""
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
        }, separators=(",", ":"), sort_keys=True)
        return sha256(block_string.encode("utf-8")).hexdigest()


# -----------------------
# Centralized Blockchain
# -----------------------
class CentralBlockchain:
    """
    Centralized manager of the blockchain (single authority).
    Holds the canonical chain in-memory and optionally on-disk.
    """
    def __init__(self, difficulty: int = 3, persist_path: Optional[str] = "chain.json"):
        self.difficulty = int(difficulty)
        self.prefix = "0" * self.difficulty
        self.persist_path = persist_path
        self.chain: List[Block] = []

        if self.persist_path and os.path.exists(self.persist_path):
            self._load()
        if not self.chain:
            self.chain.append(self._create_genesis_block())
            self._persist()

    # ------------------- Core helpers -------------------
    def _create_genesis_block(self) -> Block:
        genesis = Block(index=0, timestamp=time(), data="Genesis Block", previous_hash="0"*64)
        genesis.hash = genesis.compute_hash()
        return genesis

    def _persist(self) -> None:
        if not self.persist_path:
            return
        with open(self.persist_path, "w", encoding="utf-8") as f:
            json.dump([asdict(b) for b in self.chain], f, indent=2)

    def _load(self) -> None:
        try:
            with open(self.persist_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self.chain = [Block(**b) for b in raw]
        except Exception:
            self.chain = []

    # ------------------- Required API -------------------
    def setBlock(self, data: Any) -> Block:
        """
        Create a new block with given data, mine it under current difficulty, and append to chain.
        """
        prev = self.chain[-1]
        new_block = Block(
            index=prev.index + 1,
            timestamp=time(),
            data=data,
            previous_hash=prev.hash,
            nonce=0,
            hash=""
        )
        mined = self.mineBlock(new_block)
        self.chain.append(mined)
        self._persist()
        return mined

    def getBlock(self, index: int) -> Optional[Block]:
        """Return block by index if exists."""
        if 0 <= index < len(self.chain):
            return self.chain[index]
        return None

    def blocksExplorer(self) -> List[dict]:
        """Return the whole chain as serializable dicts (explorer-like)."""
        return [asdict(b) for b in self.chain]

    def mineBlock(self, block: Block) -> Block:
        """
        Proof-of-Work: find a nonce such that block.hash starts with '0' * difficulty.
        """
        while True:
            digest = block.compute_hash()
            if digest.startswith(self.prefix):
                block.hash = digest
                return block
            block.nonce += 1

    # ------------------- Validation (extra) -------------------
    def is_valid(self) -> bool:
        """
        Validate the entire chain.
        """
        if not self.chain:
            return False
        if self.chain[0].hash != self.chain[0].compute_hash():
            return False
        for i in range(1, len(self.chain)):
            prev = self.chain[i-1]
            curr = self.chain[i]
            if curr.previous_hash != prev.hash:
                return False
            if curr.compute_hash() != curr.hash:
                return False
            if not curr.hash.startswith(self.prefix):
                return False
        return True


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Central Blockchain (educational)")
    p.add_argument("--difficulty", type=int, default=3, help="Proof-of-Work difficulty (leading zeros).")
    p.add_argument("--add", type=str, help="Add a new block with this data (mined & appended).")
    p.add_argument("--list", action="store_true", help="List all blocks (explorer).")
    p.add_argument("--get", type=int, help="Get block by index.")
    p.add_argument("--mine", type=str, help="Mine a block with this data (preview only, not appended).")
    p.add_argument("--serve", action="store_true", help="Run as centralized HTTP service (Flask).")
    p.add_argument("--port", type=int, default=5000, help="Port for the HTTP service.")
    p.add_argument("--store", type=str, default="chain.json", help="Path to persist the chain.")
    return p


def main():
    args = build_parser().parse_args()
    bc = CentralBlockchain(difficulty=args.difficulty, persist_path=args.store)

    if args.mine and not args.add:
        temp = Block(index=len(bc.chain), timestamp=time(), data=args.mine, previous_hash=bc.chain[-1].hash)
        mined = bc.mineBlock(temp)
        print(json.dumps(asdict(mined), indent=2))
        return

    if args.add:
        b = bc.setBlock(args.add)
        print("Mined & appended block:")
        print(json.dumps(asdict(b), indent=2))
        return

    if args.get is not None:
        b = bc.getBlock(args.get)
        if b:
            print(json.dumps(asdict(b), indent=2))
        else:
            print(f"Block {args.get} not found.")
        return

    if args.list:
        print(json.dumps(bc.blocksExplorer(), indent=2))
        return

    if args.serve:
        try:
            from flask import Flask, request, jsonify
        except ImportError:
            print("Flask not installed. Run: pip install Flask")
            return

        app = Flask(_name_)

        @app.get("/")
        def root():
            return jsonify({
                "name": "Central Blockchain (educational)",
                "difficulty": bc.difficulty,
                "length": len(bc.chain),
                "valid": bc.is_valid()
            })

        @app.get("/blocks")
        def blocks():
            return jsonify(bc.blocksExplorer())

        @app.get("/blocks/<int:index>")
        def get_block(index: int):
            blk = bc.getBlock(index)
            if not blk:
                return jsonify({"error": "not found"}), 404
            return jsonify(asdict(blk))

        @app.post("/blocks")
        def add_block():
            payload = request.get_json(force=True, silent=True) or {}
            data = payload.get("data", "")
            new_blk = bc.setBlock(data)
            return jsonify(asdict(new_blk)), 201

        app.run(host="0.0.0.0", port=args.port, debug=False)
        return

    # Default: show help
    print("No action given. Try: --add, --list, --get, --mine, or --serve")
    print("Use -h for help.")


if __name__ == "__main__":
    main()