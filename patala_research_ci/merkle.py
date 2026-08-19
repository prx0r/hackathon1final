from __future__ import annotations

"""RFC-6962-style Merkle utilities for tamper-evident checkpoints.

Merkle proofs establish inclusion/history integrity; they do not establish truth.
"""

from dataclasses import dataclass, asdict
from typing import Iterable
import base64
import hashlib


def _h_leaf(data: bytes) -> bytes:
    return hashlib.sha256(b"\x00" + data).digest()


def _h_node(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(b"\x01" + left + right).digest()


def leaf_hash(data: bytes) -> str:
    return _h_leaf(data).hex()


def merkle_root(leaves: Iterable[bytes]) -> str:
    level = [_h_leaf(x) for x in leaves]
    if not level:
        return hashlib.sha256(b"").hexdigest()
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            if i + 1 == len(level):
                nxt.append(level[i])
            else:
                nxt.append(_h_node(level[i], level[i + 1]))
        level = nxt
    return level[0].hex()


def inclusion_proof(leaves: list[bytes], index: int) -> list[dict[str, str]]:
    if not (0 <= index < len(leaves)):
        raise IndexError(index)
    level = [_h_leaf(x) for x in leaves]
    idx = index
    proof: list[dict[str, str]] = []
    while len(level) > 1:
        sibling = idx - 1 if idx % 2 else idx + 1
        if sibling < len(level):
            proof.append({"side": "left" if sibling < idx else "right", "hash": level[sibling].hex()})
        nxt = []
        for i in range(0, len(level), 2):
            nxt.append(level[i] if i + 1 == len(level) else _h_node(level[i], level[i + 1]))
        idx //= 2
        level = nxt
    return proof


def verify_inclusion(data: bytes, proof: list[dict[str, str]], root_hex: str) -> bool:
    cur = _h_leaf(data)
    for step in proof:
        sib = bytes.fromhex(step["hash"])
        cur = _h_node(sib, cur) if step["side"] == "left" else _h_node(cur, sib)
    return cur.hex() == root_hex


@dataclass(frozen=True)
class MerkleCheckpoint:
    size: int
    root: str
    created_at: str
    signer: str | None = None
    signature_b64: str | None = None

    def to_dict(self):
        return asdict(self)

    def signing_bytes(self) -> bytes:
        return f"patala-checkpoint-v1\n{self.size}\n{self.root}\n{self.created_at}\n".encode()

    def with_signature(self, signer: str, signature: bytes) -> "MerkleCheckpoint":
        return MerkleCheckpoint(self.size, self.root, self.created_at, signer, base64.b64encode(signature).decode())
