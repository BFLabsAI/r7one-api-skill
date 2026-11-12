#!/usr/bin/env node
// Verifica a assinatura dos webhooks de SAÍDA do R7 One (Node, sem dependências).
// Esquema: HMAC-SHA256(secret, "<timestamp>." + <corpo bruto>), hex.
// Cabeçalhos: X-Rastreia-Signature = "sha256=<hex>", X-Rastreia-Timestamp = segundos Unix.
// IMPORTANTE: use o corpo BRUTO (Buffer), não o JSON já parseado e reserializado.
const crypto = require("crypto");

function sign(secret, timestamp, rawBody) {
  return crypto.createHmac("sha256", secret).update(Buffer.concat([Buffer.from(timestamp + "."), Buffer.from(rawBody)])).digest("hex");
}

function verify(secret, timestamp, rawBody, signatureHeader, toleranceSeconds = 300, nowSeconds = Date.now() / 1000) {
  if (!signatureHeader || !signatureHeader.startsWith("sha256=")) return false;
  const ts = Number(timestamp);
  if (!Number.isFinite(ts) || Math.abs(nowSeconds - ts) > toleranceSeconds) return false;
  const expected = Buffer.from(sign(secret, timestamp, rawBody), "utf8");
  const provided = Buffer.from(signatureHeader.slice("sha256=".length), "utf8");
  return expected.length === provided.length && crypto.timingSafeEqual(expected, provided);
}

module.exports = { sign, verify };

if (require.main === module) {
  if (!process.argv.includes("--selftest")) { console.log("Uso: node verify_signature.js --selftest"); process.exit(2); }
  const v = {
    secret: "segredo-de-teste",
    timestamp: "1762956000",
    body: '{"event": "lead.created", "event_id": "evt_00000000-0000-4000-8000-000000000001", "timestamp": "2026-11-12T14:00:00+00:00", "organization": {"id": "00000000-0000-4000-8000-000000000002", "name": "Empresa Exemplo"}, "data": {"lead": {"id": "00000000-0000-4000-8000-000000000003", "name": "João da Çilva"}}}',
    signature: "sha256=6d8f99e40ed0ff195191cc0bf0d4232f87a5f5731f908be162a80affc299e496",
  };
  const now = Number(v.timestamp);
  const ok = verify(v.secret, v.timestamp, Buffer.from(v.body, "utf8"), v.signature, 300, now);
  const tampered = !verify(v.secret, v.timestamp, Buffer.from(v.body + " ", "utf8"), v.signature, 300, now);
  const replay = !verify(v.secret, v.timestamp, Buffer.from(v.body, "utf8"), v.signature, 300, now + 3600);
  console.log("assinatura válida:", ok, "| corpo adulterado recusado:", tampered, "| replay antigo recusado:", replay);
  process.exit(ok && tampered && replay ? 0 : 1);
}
