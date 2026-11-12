#!/usr/bin/env python3
"""Verifica a assinatura dos webhooks de SAÍDA do R7 One (somente biblioteca padrão).

Esquema (igual ao do servidor): HMAC-SHA256 com a chave secreta do webhook sobre  "<timestamp>." + <corpo bruto>
Cabeçalhos recebidos: X-Rastreia-Signature = "sha256=<hex>", X-Rastreia-Timestamp = segundos Unix.

Uso na sua aplicação:
    from verify_signature import verify
    ok = verify(secret, request.headers["X-Rastreia-Timestamp"], raw_body_bytes, request.headers["X-Rastreia-Signature"])

Autoteste com vetor gerado pelo código real do R7 One:
    python3 verify_signature.py --selftest
"""
import hashlib
import hmac
import sys
import time


def sign(secret: str, timestamp: str, raw_body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), timestamp.encode("utf-8") + b"." + raw_body, hashlib.sha256).hexdigest()


def verify(secret: str, timestamp: str, raw_body: bytes, signature_header: str, tolerance_seconds: int = 300,
           now: float | None = None) -> bool:
    """True se a assinatura confere e o timestamp está dentro da tolerância (anti-replay)."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    try:
        ts = int(timestamp)
    except (TypeError, ValueError):
        return False
    if abs((now if now is not None else time.time()) - ts) > tolerance_seconds:
        return False
    return hmac.compare_digest(sign(secret, timestamp, raw_body), signature_header[len("sha256="):])


VECTOR = {
    "secret": "segredo-de-teste",
    "timestamp": "1762956000",
    "body": ('{"event": "lead.created", "event_id": "evt_00000000-0000-4000-8000-000000000001", '
             '"timestamp": "2026-11-12T14:00:00+00:00", "organization": {"id": "00000000-0000-4000-8000-000000000002", '
             '"name": "Empresa Exemplo"}, "data": {"lead": {"id": "00000000-0000-4000-8000-000000000003", '
             '"name": "João da Çilva"}}}'),
    "signature": "sha256=6d8f99e40ed0ff195191cc0bf0d4232f87a5f5731f908be162a80affc299e496",
}

if __name__ == "__main__":
    if "--selftest" not in sys.argv:
        sys.exit(__doc__)
    v = VECTOR
    body = v["body"].encode("utf-8")
    ok = verify(v["secret"], v["timestamp"], body, v["signature"], now=int(v["timestamp"]))
    bad_sig = verify(v["secret"], v["timestamp"], body + b" ", v["signature"], now=int(v["timestamp"]))
    old = verify(v["secret"], v["timestamp"], body, v["signature"], now=int(v["timestamp"]) + 3600)
    print("assinatura válida:", ok, "| corpo adulterado recusado:", not bad_sig, "| replay antigo recusado:", not old)
    sys.exit(0 if (ok and not bad_sig and not old) else 1)
