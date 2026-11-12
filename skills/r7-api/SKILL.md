---
name: r7-api
description: >-
  Use when connecting other systems or AI agents to R7 One (the CRM of R7 Treinamentos) through its public
  integration API. Covers sending leads into R7 One with the universal lead webhook (POST /webhooks/leads/{token}),
  receiving R7 One events on your own server through signed outbound webhooks (lead.created, deal.won,
  appointment.completed and more), verifying HMAC signatures, landing page tracking, and R7 Calls meeting
  webhooks. Trigger on R7 One webhook, r7one integration, api.r7one.app, lead webhook, or Zapier, n8n or Make
  sending data to R7 One. Not for the internal app API.
---

# R7 One: API pública de integração

O R7 One (CRM com IA da R7 Treinamentos, `https://api.r7one.app`) se conecta a outros sistemas por **webhooks**. Esta skill documenta essa API de integração: o que enviar, o que receber, campos obrigatórios, erros e segurança. Tudo foi conferido contra o código do R7 One.

## Escolha a integração

| Quero... | Direção | Leia |
|---|---|---|
| **Mandar leads** de um sistema, formulário, Zapier/n8n/Make ou agente para o R7 One | entra | `references/lead-webhook.md` |
| **Receber avisos** no meu servidor (lead novo, venda ganha, reunião realizada...) | sai | `references/outbound-webhooks.md` |
| Registrar **visitas e cadastros de uma landing page** do R7 One | entra | `references/tracking-webhook.md` |
| Plataforma de chamadas avisar que a **reunião terminou** (com transcrição) | entra | `references/calls-webhook.md` |
| Contrato formal (OpenAPI 3.1) | todos | `references/openapi.yaml` |
| Divergências com a página do app e pegadinhas | | `references/known-issues.md` |

## O que você precisa ter

- **Webhook de leads:** o **token da empresa**. No app R7 One: **Configurações › Integrações** (ou menu **Documentação da API**). Quem tem acesso: owner/admin da empresa.
- **Webhooks de saída:** uma URL pública HTTPS do seu servidor e a chave secreta (`secret_key`) do webhook, cadastrada em **Configurações › Webhooks de saída**.
- **Webhook de chamadas:** token emitido pelo time do R7 One.
- Não existe API key pública: as outras rotas do app (leads, funis, agenda, chat, relatórios) são a **API interna autenticada** do front-end, não documentada aqui e sujeita a mudar sem aviso.

## Começo rápido

```bash
# 1) Teste sem criar nada (valida o token e mostra como os campos serão lidos)
curl -X POST "https://api.r7one.app/webhooks/leads/$R7_WEBHOOK_TOKEN?test=1" \
  -H "Content-Type: application/json" -d '{"name":"Teste","phone":"+5585999990000"}'

# 2) Envio real (o mínimo é telefone OU e-mail). Idempotency-Key evita duplicar em retry
curl -X POST "https://api.r7one.app/webhooks/leads/$R7_WEBHOOK_TOKEN" \
  -H "Content-Type: application/json" -H "Idempotency-Key: pedido-123" \
  -d '{"name":"Maria Souza","phone":"+5585999990000","email":"maria@exemplo.com","utm_source":"google"}'
```

Scripts prontos em `scripts/`: `send_lead.py` (envia ou simula um lead), `verify_signature.py` e `verify_signature.js` (validam a assinatura dos webhooks de saída; `--selftest` roda com um vetor do código real).

## Regras que valem sempre

- **O token é segredo.** Nunca em repositório, front-end público, log, chat ou mensagem. Leia de variável de ambiente (`R7_WEBHOOK_TOKEN`, `R7_WEBHOOK_SECRET`).
- **É produção.** Um envio real cria lead e oportunidade de verdade e pode disparar alertas e automações. Use `?test=1` para testar e peça confirmação ao usuário antes de envios reais em massa.
- **Dados de leads são pessoais (LGPD).** Envie só o necessário e não repasse a terceiros.
- **Sempre use `Idempotency-Key`** em envios que podem ser repetidos (retry, filas). Em `5xx`/timeout repita com a **mesma** chave; não repita `400`/`404`/`409`/`423`.
- **Defina um `User-Agent`** nas chamadas: o Cloudflare bloqueia bibliotecas padrão (`403 error code: 1010`).
- **Verifique sempre a assinatura** dos webhooks de saída, sobre o **corpo bruto**, e deduplique por `X-Rastreia-Delivery` (a entrega é at-least-once).
- **Não invente campos.** Use só os documentados. Campos desconhecidos no webhook de leads viram `extra` (não dão erro).
- Domínio: lead = pessoa (deduplicada por telefone/e-mail); oportunidade (deal) = card no funil, no máximo uma ativa por lead; fuso de negócio `America/Fortaleza`.

## Como foi verificado

Gerada em 2026-11-12 contra o código do R7 One e **testada de ponta a ponta** numa instância local isolada (clone descartável do banco de teste, sem credenciais de produção):

- **119 verificações de caixa-preta** passaram: webhook de leads (aliases, limites de campo, idempotência, deduplicação, conflitos, CORS, 423), rastreio de landing, webhook de chamadas (2 MB, duplicado e **assinatura**), login/refresh/logout (incl. rate limit do login), CRUD de webhooks de saída, bloqueio SSRF, entrega assinada de **`lead.created`, `deal.created`, `deal.stage_changed`, `deal.won`, `deal.lost`, `negotiation.opened|updated|cancelled`, `appointment.scheduled` e `appointment.completed`** (assinatura conferida com os scripts desta skill), `Retry-After`, 5xx com **8 tentativas até falha definitiva** e 4xx como falha permanente.
- **Testes do próprio R7 One** para essas rotas e para `funnel.*` passaram (121 e 39 em duas rodadas).
- Smoke em todas as 723 operações da API (incluindo a interna): nenhuma travou; 2 devolveram `500` em casos de borda (já em Issues #859 e #860).
- **Limites de entrada (implementados, Epic #878):** corpo máx. 1 MiB (`413`), 300/min por IP, 600/min por token, 20 404/min por IP (`429` + `Retry-After`). Smoke em produção do `429` e do IP real pendente (ver `known-issues.md`).

Em **produção** só verifiquei ao vivo as respostas de erro das rotas públicas (token inválido, GET, JSON inválido, bloqueio de User-Agent), sem envios reais. Se algo divergir, vale o servidor.
