# Webhook de chamadas / reuniões R7 Calls (entrada)

Para a **plataforma de chamadas R7 Calls** (ou outra plataforma de reunião/ligação) avisar o R7 One quando uma reunião termina e a transcrição fica pronta. O R7 One liga o resultado à reunião e ao lead e guarda a transcrição.

```
POST https://api.r7one.app/webhooks/calls/{token}
Content-Type: application/json
```

## Autenticação

- `{token}`: um por empresa, **emitido pelo time do R7 One** (não é o mesmo token do webhook de leads). Trate como segredo.
- Token desconhecido ou desativado: `404 {"error":"not_found"}` (resposta uniforme).
- **Assinatura opcional por empresa** (testada: sem assinatura `401`, assinatura errada `401`, hex com ou sem `sha256=` `2xx`, timestamp com 1 h de diferença `401`). Se a empresa tiver segredo, envie `X-Signature: sha256=<hex>` (ou só o hex) com o HMAC-SHA256 do **corpo bruto**; ou, se enviar também `X-Timestamp` (tolerância de ±5 min), do texto `timestamp + "." + corpo`. Sem segredo configurado, a assinatura não é exigida. Atenção: este esquema (`X-Signature`/`X-Timestamp`) é **diferente** do dos webhooks de saída (`X-Rastreia-*`).

## Corpo

Aceita dois formatos. Obrigatórios: `event` e um identificador da reunião (`call.id` **ou** `meeting.code`); sem eles, `400`.

**Formato da plataforma de chamadas:**

```json
{
  "event": "call.completed",
  "sent_at": "2026-11-12T14:20:05-03:00",
  "call": {"id": "ABC-123", "direction": "outbound", "status": "answered",
           "started_at": "2026-11-12T14:03:10-03:00", "ended_at": "2026-11-12T14:12:40-03:00", "duration_seconds": 570},
  "metadata": {"external_id": "<id do agendamento no R7 One, quando você tiver>"},
  "lead": {"phone": "+5585999990000", "name": "Maria", "email": "maria@exemplo.com"},
  "agent": {"email": "ana@empresa.com", "name": "Ana"},
  "transcription": {"status": "completed", "language": "pt-BR", "text": "...",
                    "segments": [{"speaker": "agent", "start": 0.0, "end": 4.1, "text": "Bom dia"}],
                    "summary": "...", "sentiment": "positive"},
  "recording": {"url": "https://.../rec.mp3"}
}
```

**Formato R7 One:** `event`, `event_id`, `meeting.code`, `meeting.external_id`, `meeting.status`.

`transcription.status`: `processing`, `completed` ou `failed`. Se a transcrição demorar, mande um primeiro envio com `processing` e, depois, outro com o **mesmo `call.id`** e `completed`: o R7 One completa a mesma reunião, não cria outra.

## Comportamento

- Resposta de sucesso: **`202 Accepted`** quando o evento é aceito para processamento; `200` em `ping` (teste de conexão) e em reenvio duplicado (`{"duplicate": true}`). Trate qualquer `2xx` como recebido.
- Eventos que disparam a conferência da reunião: `call.completed`, `meeting.ended`, `transcript.ready`. Outros eventos são registrados como ignorados.
- Corpo de até **2 MB**; acima disso `413 {"error":"payload_too_large"}`.
- **Idempotência:** reenviar o mesmo evento responde `200 {"duplicate": true}` sem reprocessar. A chave é `event_id` (quando existe) ou uma combinação de reunião, evento, status da transcrição e `sent_at`.
- `2xx` = recebido (não repetir). `5xx` ou demora = repetir com espera crescente (1 min, 5 min, 30 min, 2 h, até 24 h). `404`, `400` e `413` não se repetem. `401` = assinatura inválida.
- O corpo tem dado pessoal (telefone, e-mail, transcrição): o R7 One não grava o corpo em log; use HTTPS e não registre o token.
- O vínculo com a reunião usa o identificador enviado: `call.id` (= código da reunião no R7 One) ou `metadata.external_id` (= id do agendamento no R7 One, quando você o tiver). Sem vínculo possível, o aviso fica registrado como "recebido, aguardando processamento".

