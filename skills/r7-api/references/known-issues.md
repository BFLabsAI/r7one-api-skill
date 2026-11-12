# Divergências conhecidas e pegadinhas

Conferidas contra o código do R7 One em 2026-11-12. Quando a página **Documentação da API** do app e o código divergirem, **vale o código** (este documento).

## Erros na página "Documentação da API" do app

| Tema | A página diz | O servidor faz de verdade |
|---|---|---|
| Assinatura dos webhooks de saída | cabeçalho `X-Sinal-Signature` | envia `X-Rastreia-Signature: sha256=<hex>` + `X-Rastreia-Timestamp` (+ `X-Rastreia-Event`, `X-Rastreia-Delivery`). O cabeçalho `X-Sinal-Signature` **não é enviado** |
| O que é assinado | (exemplo de código só do corpo) | HMAC-SHA256 de `"<timestamp>." + corpo bruto` |
| `telefone` no webhook de leads | marcado como obrigatório | basta **e-mail válido OU telefone** |
| Nomes dos campos | só em português (`nome`, `telefone`) | aceita inglês e português (`name`/`nome`, `phone`/`telefone`/`whatsapp`/`celular`, `email`/`e-mail`...) |
| Eventos de saída | exemplos de `data` com `deal_id`, `won_at`, `closer` e `attribution` com UTMs soltos | o `data` real tem `deal`, `lead`, `pipeline`, `stage`, `attribution{sdr,closer}`, `products` e, no ganho, `negotiation`, `payment`, `company` (ver `outbound-webhooks.md`) |
| Eventos disponíveis | 5 | a tela oferece 5; o servidor emite outros (`deal.lost`, `deal.stage_changed`, `negotiation.*`, `funnel.*`) |

## Pegadinhas de integração

- **Cloudflare bloqueia User-Agent de biblioteca padrão.** Chamadas com `Python-urllib` (e similares sem navegador) recebem `403` com corpo `error code: 1010`. Defina um `User-Agent` próprio.
- **JSON inválido dá `400` mesmo com token errado:** o corpo é lido antes de o token ser validado.
- **Token do webhook de leads e token do webhook de chamadas são diferentes** e emitidos separadamente. O segredo do webhook de saída é um terceiro valor (chave HMAC).
- **Um lead novo gera dois eventos de saída:** `lead.created` e `deal.created`. Se você assinou os dois, trate como eventos distintos (cada um tem seu `event_id`).
- **Assinatura:** use o corpo **bruto**. Frameworks que parseiam o JSON antes (e reserializam) quebram a verificação.
- **At-least-once:** webhooks de saída podem repetir e chegar fora de ordem; deduplique por `X-Rastreia-Delivery`.
- **Telefone sem DDI:** o servidor aceita qualquer máscara, mas prefira E.164 (`+55...`). Dois leads com o mesmo número em formatos diferentes são a mesma pessoa.
- **E-mail inválido é descartado em silêncio** no webhook de leads (sem erro). Se for o único identificador, a resposta é `400`.
- **`channel`/`canal` não define a origem** do lead; só aparece no log. Use `utm_source` e `utm_medium`.
- **Empresa em implantação** responde `423` a capturas (webhook de leads e `event: "lead"` do rastreio).
- **Sem limite de taxa nem de tamanho de corpo nas rotas públicas de entrada** (confirmado em teste: 300 req em 1,5 s e corpos de 20 MB aceitos). Em implementação (Issues #879 e #880). Até lá: corpos pequenos, ritmo moderado, `Idempotency-Key` nos retries. O login (`/auth/login`) já limita: 60 tentativas por IP, depois `429`.
- **A API de gerenciamento de webhooks de saída não valida o nome do evento** (`201` para evento inexistente): confira a grafia.
- **`loss_reason`** de `deal.lost` é um catálogo da empresa; texto livre vira "Outro motivo".
- **Webhook de chamadas responde `202`** (aceito para processamento), não `200`, para eventos reais; `200` só em `ping` e duplicado.

## O que esta skill não cobre (de propósito)

O R7 One tem também uma API **autenticada interna** (mais de 600 operações) que liga o front-end ao back-end: leads, oportunidades, funis, agenda, chat, relatórios etc. Ela **não é uma API pública**: exige login de usuário (JWT de 15 minutos), não tem API key, e pode mudar sem aviso junto com o app. Esta skill não a documenta. A única parte dela documentada aqui é o gerenciamento de webhooks de saída (`outbound-webhooks.md`), útil para um agente se cadastrar para receber eventos.
