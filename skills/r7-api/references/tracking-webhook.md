# Webhook de rastreio de landing page (entrada)

Para páginas **publicadas no R7 One** (landing pages do app) ou páginas suas que reportam visitas e cadastros a elas. Registra **visualização** e **cadastro** de uma landing, com UTMs.

```
POST https://api.r7one.app/webhooks/track
Content-Type: application/json
```

- **Sem token.** A página é identificada pelo `slug` de uma landing **publicada** da empresa. Slug inexistente ou não publicado: `404 {"detail":"Página não encontrada"}`.
- CORS aberto (qualquer origem), pensado para ser chamado do navegador.
- `Idempotency-Key` opcional (até 1024 caracteres), com o mesmo efeito do webhook de leads: reenviar a mesma chave não duplica o cadastro.
- Se você só quer **enviar leads** de um sistema seu, use o `lead-webhook.md` (com token), não este.

## Corpo

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `slug` | string (1 a 200) | **sim** | slug da landing publicada |
| `event` | `"view"` ou `"lead"` | **sim** | `view` = visita; `lead` = cadastro |
| `tracking` | objeto | não | UTMs e contexto: `utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content` (até 200), `referrer`, `landing_path` (até 500), `gclid`, `fbclid` (até 200), `device` (até 50) |
| `lead` | objeto | **sim, se `event` = `lead`** | `name` (200), `email` (e-mail válido, até 200), `phone` (50), `message` (2000). **É preciso e-mail OU telefone.** Campos extras do formulário (ex.: `faturamento`, `equipe`) são aceitos e guardados com o lead (até 100 campos, 2000 caracteres cada) |

Visita:

```bash
curl -X POST "https://api.r7one.app/webhooks/track" -H "Content-Type: application/json" \
  -d '{"slug":"minha-landing","event":"view","tracking":{"utm_source":"instagram","utm_campaign":"bio"}}'
# 200 {"ok": true}
```

Cadastro:

```bash
curl -X POST "https://api.r7one.app/webhooks/track" -H "Content-Type: application/json" \
  -H "Idempotency-Key: form-7f3a9" \
  -d '{"slug":"minha-landing","event":"lead",
       "tracking":{"utm_source":"google","utm_medium":"cpc","gclid":"Cj0KCQ..."},
       "lead":{"name":"Maria Souza","phone":"+5585999990000","email":"maria@exemplo.com","faturamento":"50k-100k"}}'
# 200 {"ok": true}   (ou {"ok": true, "alt_phone_added": true})
```

## Respostas

| HTTP | Quando |
|---|---|
| 200 `{"ok": true}` | registrado |
| 400 `{"detail":"Informe e-mail ou telefone"}` | `event: "lead"` sem e-mail nem telefone |
| 404 `{"detail":"Página não encontrada"}` | slug inexistente ou landing não publicada |
| 409 `{"detail":{"code":"idempotency_conflict"}}` | mesma chave com corpo diferente |
| 409 `{"detail":{"code":"identity_conflict"}}` | e-mail e telefone de leads diferentes |
| 422 | corpo inválido (campo ausente, `event` fora de `view`/`lead`, e-mail mal formado) |
| 423 | empresa em implantação (só para `event: "lead"`) |
| 500 | falha interna: repita com a mesma `Idempotency-Key` |

Cadastros por aqui geram lead e oportunidade com as mesmas regras do webhook de leads, e disparam `lead.created` (webhook de saída) para pessoas novas.
