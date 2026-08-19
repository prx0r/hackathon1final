from __future__ import annotations

"""Authenticated metadata for Pāṭala artifacts, shaped after in-toto Statement v1.

The module uses Ed25519 when the optional ``cryptography`` package is present.
Signatures authenticate who signed a statement; they do not make the predicate true.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import base64
import json

from .canonical import canonical_json_bytes, digest_json

STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
PREDICATE_PREFIX = "https://patala.dev/attestation/"


@dataclass(frozen=True)
class Subject:
    name: str
    digest: dict[str, str]


@dataclass(frozen=True)
class Statement:
    subject: tuple[Subject, ...]
    predicate_type: str
    predicate: dict[str, Any]
    statement_type: str = STATEMENT_TYPE

    def to_dict(self) -> dict[str, Any]:
        return {
            "_type": self.statement_type,
            "subject": [asdict(x) for x in self.subject],
            "predicateType": self.predicate_type,
            "predicate": self.predicate,
        }

    @property
    def digest(self) -> str:
        return digest_json(self.to_dict())


@dataclass(frozen=True)
class SignedEnvelope:
    payload_type: str
    payload_b64: str
    key_id: str
    signature_b64: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "payloadType": self.payload_type,
            "payload": self.payload_b64,
            "signatures": [{"keyid": self.key_id, "sig": self.signature_b64}],
        }


def statement_for(name: str, digest: str, predicate_type: str, predicate: dict[str, Any]) -> Statement:
    algo, value = digest.split(":", 1) if ":" in digest else ("sha256", digest)
    return Statement((Subject(name, {algo: value}),), predicate_type, predicate)


def generate_ed25519_keypair(private_path: str | Path, public_path: str | Path) -> tuple[Path, Path]:
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption
    except ImportError as exc:
        raise RuntimeError("install patala-research-ci[crypto] for Ed25519 support") from exc
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()
    private_path = Path(private_path); public_path = Path(public_path)
    private_path.write_bytes(priv.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()))
    public_path.write_bytes(pub.public_bytes(Encoding.Raw, PublicFormat.Raw))
    return private_path, public_path


def sign_statement(statement: Statement, private_key_path: str | Path, key_id: str = "local-ed25519") -> SignedEnvelope:
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ImportError as exc:
        raise RuntimeError("install patala-research-ci[crypto] for Ed25519 support") from exc
    raw = canonical_json_bytes(statement.to_dict())
    key = Ed25519PrivateKey.from_private_bytes(Path(private_key_path).read_bytes())
    sig = key.sign(raw)
    return SignedEnvelope(
        payload_type="application/vnd.in-toto+json",
        payload_b64=base64.b64encode(raw).decode(),
        key_id=key_id,
        signature_b64=base64.b64encode(sig).decode(),
    )


def verify_envelope(envelope: SignedEnvelope | dict[str, Any], public_key_path: str | Path) -> tuple[bool, dict[str, Any] | None]:
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError as exc:
        raise RuntimeError("install patala-research-ci[crypto] for Ed25519 support") from exc
    if isinstance(envelope, dict):
        sig = envelope["signatures"][0]
        env = SignedEnvelope(envelope["payloadType"], envelope["payload"], sig.get("keyid", ""), sig["sig"])
    else:
        env = envelope
    payload = base64.b64decode(env.payload_b64)
    signature = base64.b64decode(env.signature_b64)
    key = Ed25519PublicKey.from_public_bytes(Path(public_key_path).read_bytes())
    try:
        key.verify(signature, payload)
    except Exception:
        return False, None
    return True, json.loads(payload)
