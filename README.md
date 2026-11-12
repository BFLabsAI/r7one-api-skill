# R7 One API Skill

Skill de agente ([Agent Skills](https://skills.sh)) para **conectar outros sistemas e agentes de IA ao R7 One**, o CRM com IA da R7 Treinamentos.

Documenta a **API pública de integração** (webhooks), validada contra o código do R7 One:

- **Entrada:** webhook universal de leads, rastreio de landing page, webhook de chamadas/reuniões (R7 Calls).
- **Saída:** webhooks assinados (HMAC-SHA256) com eventos como `lead.created`, `deal.won`, `appointment.completed`, com payloads reais, retentativas e verificação de assinatura.
- Campos **obrigatórios marcados**, erros, idempotência, exemplos `curl`, OpenAPI 3.1 e scripts de teste.

> Não documenta a API autenticada interna do app (front-end ↔ back-end), que não é pública.

## Instalar

```bash
npx skills add BFLabsAI/r7one-api-skill
```

Ou copie `skills/r7-api/` para a pasta de skills do seu agente (`~/.claude/skills/`, `~/.codex/skills/`...).

## Conteúdo

| Caminho | O que é |
|---|---|
| `skills/r7-api/SKILL.md` | instruções da skill |
| `skills/r7-api/references/lead-webhook.md` | enviar leads (campos, erros, idempotência) |
| `skills/r7-api/references/outbound-webhooks.md` | receber eventos, assinatura, retentativas, payloads |
| `skills/r7-api/references/tracking-webhook.md` | visitas e cadastros de landing page |
| `skills/r7-api/references/calls-webhook.md` | webhook de chamadas/reuniões |
| `skills/r7-api/references/known-issues.md` | divergências e pegadinhas |
| `skills/r7-api/references/openapi.yaml` | OpenAPI 3.1 (também em `openapi/`) |
| `skills/r7-api/scripts/` | `send_lead.py`, `verify_signature.py`, `verify_signature.js` |

## Você precisa de

O **token do webhook da sua empresa** (app R7 One › Configurações › Integrações). Esta skill não dá acesso a dados por si só.

## Aviso

É produção: envios reais criam leads e oportunidades. Use `?test=1` para testar. Dados de leads são pessoais (LGPD). Gerada em 2026-11-12; se algo divergir, vale o servidor.

## Licença

MIT. BF Labs / R7 Treinamentos.
