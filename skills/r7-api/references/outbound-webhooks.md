# Webhooks de saída (R7 One → seu sistema)

O R7 One avisa o **seu servidor** por HTTP `POST` quando algo acontece (lead novo, oportunidade ganha, reunião realizada...). Cada mensagem é **assinada** (HMAC-SHA256) e tem **retentativas automáticas**.

## Como configurar

No app: **Configurações › Webhooks de saída** (owner/admin da empresa). Campos de cada webhook:

| Campo | Descrição |
|---|---|
| `name` | nome do webhook |
| `target_url` | URL do seu servidor. `https://` (ou `http://`). Regras de segurança abaixo |
| `secret_key` | chave secreta do HMAC. O app gera uma; guarde-a no seu servidor |
| `events` | lista de eventos que você quer receber |
| `pipeline_id`, `stage_id` | opcionais: só eventos do funil/etapa informados (`null` = todos) |
| `custom_headers` | cabeçalhos extras enviados em toda entrega (ex.: `Authorization` do seu lado) |
| `is_active` | liga/desliga |

Dá para **testar** (envia um evento `ping` assinado), ver o **histórico de entregas** (status HTTP, resposta, tentativas) e **reenviar** uma entrega manualmente. Um agente também pode gerenciar isso por API autenticada: ver "Gerenciar por API" no fim.

**Regras da `target_url`:** só `http`/`https`; sem usuário/senha na URL; o host precisa resolver para IP **público** (bloqueia localhost, redes privadas, link-local/metadata de nuvem, `*.local`, `*.internal`); redirecionamentos são revalidados. Para desenvolvimento local use um túnel público (ngrok, Cloudflare Tunnel).

## O que chega no seu servidor

`POST <target_url>` com corpo JSON UTF-8:

```json
{
  "event": "deal.won",
  "event_id": "evt_00000000-0000-4000-8000-000000000001",
  "timestamp": "2026-11-12T14:00:00+00:00",
  "organization": {"id": "00000000-0000-4000-8000-000000000002", "name": "Empresa Exemplo"},
  "data": { }
}
```

`event_id` é único por evento. O conteúdo de `data` depende do evento (abaixo).

### Cabeçalhos

| Cabeçalho | Valor |
|---|---|
| `Content-Type` | `application/json` |
| `User-Agent` | `R7-One-Webhooks/1.0` |
| `X-Rastreia-Signature` | `sha256=<hex>`: HMAC-SHA256 do corpo (ver abaixo) |
| `X-Rastreia-Timestamp` | segundos Unix do envio |
| `X-Rastreia-Event` | nome do evento (ex.: `deal.won`) |
| `X-Rastreia-Delivery` | id da entrega. **Estável entre as retentativas** da mesma entrega: use como chave de deduplicação |

> Atenção: a página "Documentação da API" do app cita `X-Sinal-Signature`. O servidor **não** envia esse cabeçalho: o real é `X-Rastreia-Signature` (+ `X-Rastreia-Timestamp`). Ver `known-issues.md`.

### Verificar a assinatura (faça sempre)

```
assinatura = HMAC_SHA256( secret_key , timestamp + "." + corpo_bruto )   // hex minúsculo
cabeçalho  = "sha256=" + assinatura
```

Regras: use o **corpo bruto** exatamente como chegou (bytes), **antes** de fazer parse do JSON (reserializar muda os bytes e quebra a assinatura); compare em tempo constante; recuse `X-Rastreia-Timestamp` com mais de 5 minutos de diferença (anti-replay). O servidor não impõe essa tolerância: ela é sua.

Python (`scripts/verify_signature.py`):

```python
from verify_signature import verify
ok = verify(SECRET, headers["X-Rastreia-Timestamp"], raw_body_bytes, headers["X-Rastreia-Signature"])
```

Node (`scripts/verify_signature.js`), exemplo com Express (corpo bruto):

```js
const { verify } = require("./verify_signature");
app.post("/r7-webhook", express.raw({ type: "application/json" }), (req, res) => {
  const ok = verify(process.env.R7_WEBHOOK_SECRET, req.get("X-Rastreia-Timestamp"), req.body, req.get("X-Rastreia-Signature"));
  if (!ok) return res.status(401).end();
  const event = JSON.parse(req.body.toString("utf8"));
  // enfileire o processamento e responda rápido
  res.status(200).end();
});
```

Os dois scripts têm `--selftest` com um vetor gerado pelo código do próprio R7 One.

### Resposta, retentativas e ordem

- Responda **2xx em até 5 segundos**. Processe de forma assíncrona (enfileire e responda).
- **Sucesso** = qualquer `2xx`. **Retenta** em: timeout (5 s), erro de conexão, `429` e `5xx`. Qualquer outro `4xx` é **falha permanente** (não retenta).
- Até **8 tentativas** com espera exponencial a partir de 5 s (5, 10, 20... até 1 h) com jitter. Se você responder `429` ou `503` com `Retry-After`, o R7 One espera pelo menos esse tempo (até 24 h).
- **At-least-once:** o mesmo evento pode chegar mais de uma vez e **fora de ordem**. Deduplique por `X-Rastreia-Delivery` (ou `event_id`) e use os timestamps de `data` para ordenar.
- Depois de esgotar as tentativas a entrega fica como falha e pode ser reenviada manualmente pelo app (ou pela API de gerenciamento).

## Eventos

### Oferecidos na tela de configuração

| Evento | Quando |
|---|---|
| `lead.created` | entra um lead **novo** na empresa (por webhook, landing, importação etc.). Um lead novo dispara **também** `deal.created` (a oportunidade que nasce com ele): assine só o que precisa para não processar duplicado |
| `deal.created` | uma oportunidade é criada no funil |
| `deal.won` | a oportunidade é marcada como ganha |
| `appointment.scheduled` | uma reunião/compromisso é agendado |
| `appointment.completed` | a reunião é marcada como realizada |

### Também emitidos pelo servidor

O servidor também gera os eventos abaixo; eles são entregues se o nome estiver na lista `events` do webhook, mas a tela de configuração hoje **não os lista** (cadastre-os pela API de gerenciamento; não verifiquei o comportamento em produção): `deal.lost`, `deal.stage_changed`, `negotiation.opened`, `negotiation.updated`, `negotiation.cancelled`, `funnel.submission.completed`, `funnel.qualified`. O evento `ping` é só do botão de teste.

### `data` por evento (formato real do código)

Os exemplos usam valores fictícios.

**`lead.created`**

```json
{"lead": {"id": "<uuid>", "name": "Maria Souza", "phone": "+5585999990000", "email": "maria@exemplo.com",
          "funil_captura": "webhook", "created_at": "2026-11-12T14:00:00+00:00"},
 "tracking": {"utm_source": "google", "utm_medium": "cpc", "utm_campaign": "lancamento-q4", "utm_content": "video-02"}}
```

**`deal.created`, `deal.won`, `deal.lost`, `deal.stage_changed`**

```json
{"deal": {"id": "<uuid>", "status": "won", "value": 15000.0, "amount": 15000.0, "title": "Maria Souza",
          "closed_at": "2026-11-12T16:20:00+00:00", "created_at": "2026-11-01T10:00:00+00:00", "loss_reason": null},
 "lead": {"id": "<uuid>", "name": "Maria Souza", "phone": "+5585999990000", "email": "maria@exemplo.com"},
 "pipeline": {"id": "<uuid>", "name": "Vendas"},
 "stage": {"id": "<uuid>", "name": "Ganho"},
 "attribution": {"sdr": {"id": "<uuid>", "name": "Ana", "email": "ana@empresa.com"}, "closer": null},
 "products": [{"product_id": "<uuid>", "name": "Mentoria", "quantity": 1, "unit_price": 15000.0, "total_price": 15000.0}]}
```

`products` exclui itens bônus. `loss_reason` só vem preenchido em `deal.lost`. Em **`deal.won`** o objeto ganha também:

```json
{"negotiation": {"id": "<uuid>", "deal_id": "<uuid>", "state": "won", "opened_at": "...", "origin": "...",
                 "list_total": 15000.0, "amount": 15000.0,
                 "items": [{"product_id": "<uuid>", "name": "Mentoria", "quantity": 1, "list_unit_price": 15000.0,
                            "unit_price": 15000.0, "total_price": 15000.0, "is_bonus": false}]},
 "payment": {"method_id": "<uuid>", "method_key": "pix", "installments_count": 1, "down_payment_amount": 0.0,
             "down_payment_date": null, "installments": [{"seq": 1, "due_date": "2026-12-12", "amount": 15000.0}]},
 "company": null,
 "b2b_company_pending": false}
```

(`payment` é `null` sem forma de pagamento; `company` só existe em empresas no modo B2B; `b2b_company_pending: true` = ganhou sem empresa vinculada.)

**`appointment.scheduled`, `appointment.completed`**

```json
{"appointment_id": "<uuid>", "organization_id": "<uuid>", "lead_id": "<uuid>", "deal_id": "<uuid>",
 "status": "agendada", "starts_at": "2026-11-13T15:00:00+00:00", "ends_at": "2026-11-13T15:45:00+00:00",
 "scheduled_at": "2026-11-13T15:00:00+00:00", "completed_at": null, "meeting_link": "https://...",
 "appointment": {"id": "<uuid>", "deal_id": "<uuid>", "status": "agendada", "starts_at": "...", "ends_at": "...",
                 "held_at": null, "meeting_link": "https://...", "meeting_type": "diagnostico", "modality": "online",
                 "duration_minutes": 45, "notes": null},
 "consultant": {"id": "<uuid>", "name": "Consultor", "email": "consultor@empresa.com"},
 "closer_user_id": "<uuid>", "sdr_user_id": null,
 "lead": {"id": "<uuid>", "name": "Maria Souza", "phone": "+5585999990000", "email": "...", "company": null},
 "deal": {"id": "<uuid>", "pipeline_id": "<uuid>", "stage_id": "<uuid>", "title": "Maria Souza", "amount": 0.0, "status": "active"}}
```

Status de reunião: `agendada`, `realizada`, `cancelada`, `nao_compareceu`.

**`negotiation.*`**: `deal` (`id`, `title`, `status`, `pipeline_id`, `stage_id`), `lead` (`id`, `name`, `phone`, `email`) e os blocos `negotiation`, `payment`, `company` iguais aos de `deal.won`.

> O conjunto exato de campos pode crescer; ignore campos desconhecidos e não dependa da ordem das chaves. Campos podem vir `null`.

## Gerenciar por API (avançado)

Exige login (Bearer JWT de um owner/admin): `POST /auth/login` com e-mail e senha devolve `access_token` (15 min) e `refresh_token` (30 dias, rotativo). O papel mínimo é owner/admin.

| Método | Caminho | Uso |
|---|---|---|
| `GET` | `/api/v1/outbound-webhooks` | lista os webhooks da empresa |
| `POST` | `/api/v1/outbound-webhooks` | cria. Corpo: `name` (**obrigatório**), `target_url` (**obrigatório**), `events` (lista), `secret_key` (gerada se omitida), `pipeline_id`, `stage_id`, `is_active` (padrão `true`), `custom_headers`, `organization_id` |
| `GET` | `/api/v1/outbound-webhooks/{id}` | detalhe |
| `PATCH` | `/api/v1/outbound-webhooks/{id}` | altera (todos os campos opcionais) |
| `DELETE` | `/api/v1/outbound-webhooks/{id}` | remove |
| `GET` | `/api/v1/outbound-webhooks/{id}/logs` | histórico de entregas (filtro `event_type`, paginado) |
| `POST` | `/api/v1/outbound-webhooks/{id}/test` | envia um `ping` assinado |
| `POST` | `/api/v1/outbound-webhooks/{id}/logs/{log_id}/retry` | reenvia uma entrega |

```bash
curl -X POST "https://api.r7one.app/api/v1/outbound-webhooks" \
  -H "Authorization: Bearer $R7_TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Meu CRM","target_url":"https://meu-servidor.com/r7-webhook","events":["lead.created","deal.won"]}'
```

A resposta traz o `secret_key` (guarde-o: é a chave para verificar a assinatura). Esta API autenticada é a mesma usada pelo app; os campos acima foram conferidos no código, mas não testei contra produção com credenciais.
