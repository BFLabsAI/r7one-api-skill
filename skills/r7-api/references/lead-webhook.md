# Webhook universal de leads (entrada)

Como **qualquer sistema** coloca leads no R7 One: formulários, Zapier, n8n, Make, RD Station, CRMs, landing pages, outro back-end ou um agente de IA. É a integração mais usada.

```
POST https://api.r7one.app/webhooks/leads/{token}
Content-Type: application/json
```

## Autenticação

- O `{token}` na URL identifica a **empresa (organização)** e funciona como senha. **Um token por empresa.**
- Onde pegar: no app R7 One, **Configurações › Integrações** (campo "Webhook token") ou no menu **Documentação da API** (mostra a URL pronta). Peça a um owner/admin da empresa.
- Trate como segredo: não coloque em repositório, front-end público ou log. Se vazar, gere outro no app (o antigo deixa de valer).
- Token com menos de 20 caracteres ou desconhecido responde `404 {"error":"Token inválido"}`.
- Não há `Authorization`, assinatura ou API key: só o token.

## Cabeçalhos

| Cabeçalho | Obrigatório | Descrição |
|---|---|---|
| `Content-Type: application/json` | sim | corpo JSON UTF-8 (um **objeto**, não array) |
| `Idempotency-Key` | não (recomendado) | até 1024 caracteres. Com ele, reenviar a mesma requisição **não** cria lead, levantada de mão, oportunidade nem evento de novo: devolve o lead original. Reusar a chave com payload diferente dá `409 idempotency_conflict`. Sem ele, cada requisição conta como uma captura nova (a pessoa continua deduplicada por telefone/e-mail) |
| `User-Agent` | defina um | o Cloudflare à frente da API **bloqueia User-Agents de biblioteca padrão** (ex.: `Python-urllib`) com `403 error code: 1010`. Use `curl`, `requests`, `axios`, `fetch` ou um UA próprio |

CORS: a rota aceita chamadas de **qualquer origem** (`Access-Control-Allow-Origin: *`), então pode ser chamada direto do navegador. Mas isso expõe o token no front-end: prefira chamar do servidor.

## Corpo: campos aceitos

**Regra única de obrigatoriedade:** é preciso **e-mail válido OU telefone**. Sem nenhum dos dois: `400 {"error":"Informe ao menos e-mail ou telefone"}`. Todos os outros campos são opcionais.

| Campo (e apelidos aceitos) | Tipo | Limite | Obrigatório | O que vira |
|---|---|---|---|---|
| `phone` (`telefone`, `whatsapp`, `celular`) | string | 50 | **um dos dois: telefone ou e-mail** | telefone do lead; normalizado para E.164 (`+5585999990000`). Aceita qualquer máscara |
| `email` (`e-mail`) | string | 200 | **um dos dois: telefone ou e-mail** | e-mail do lead. E-mail com formato inválido é **descartado em silêncio** (não dá erro; se não houver telefone, aí sim vira `400`) |
| `name` (`nome`, `full_name`) | string | 200 | não | nome. Também é o título da oportunidade (sem nome: "Lead Webhook") |
| `message` (`mensagem`, `observacao`) | string | 2000 | não | mensagem/observação |
| `utm_source` (`utm_source_platform`, `utm_source_plataform`, `origem`) | string | 200 | não | origem do tráfego. `origem` só é usada se não vier `utm_source` |
| `utm_medium` | string | 200 | não | meio |
| `utm_campaign` (`origem`) | string | 200 | não | campanha. `origem` é fallback |
| `utm_term` | string | 200 | não | palavra-chave |
| `utm_content` | string | 200 | não | criativo |
| `utm_audience` | string | – | não | público; guardado em `extra.utm_audience` |
| `referrer` | string | 500 | não | página de origem |
| `landing_path` | string | 500 | não | caminho da landing |
| `landing_page_title` (`landing_page`) | string | 255 | não | título da landing |
| `gclid` | string | 200 | não | Google Ads click id |
| `fbclid` | string | 200 | não | Meta click id |
| `device` | string | 50 | não | dispositivo |
| `channel` (`canal`) | string | 50 | não | **só uma dica**: aparece no log do webhook e na resposta (`channel`). **Não** define a origem do card; a origem canônica é calculada de `utm_source`, `utm_medium`, `referrer` e tracking |
| `consultor` (`owner_email`) | string | – | não | guardado em `extra.consultor` |
| `ad_id`, `adset_id`, `campaign_id` | string/int | 32 dígitos | não | no topo ou dentro de `extra`. Só valem se forem **numéricos** (ids do Meta Ads); macros não preenchidas como `{{ad.id}}`, `null`, `0` são ignoradas. Valores válidos viram os ids de anúncio do lead (cruzam com relatórios de coorte) |
| `extra` | objeto | – | não | campos livres do seu sistema. **Qualquer chave desconhecida no topo do corpo** também vai para `extra` |

> Aviso sobre a página "Documentação da API" do app: ela marca `telefone` como obrigatório e usa nomes em português. O código aceita os nomes em inglês **e** português e exige só "e-mail ou telefone". Ver `known-issues.md`.

## Exemplos

Mínimo (só o obrigatório):

```bash
curl -X POST "https://api.r7one.app/webhooks/leads/$R7_WEBHOOK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+5585999990000"}'
```

Completo:

```bash
curl -X POST "https://api.r7one.app/webhooks/leads/$R7_WEBHOOK_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: pedido-2026-000123" \
  -d '{
    "name": "Maria Souza",
    "phone": "+55 (85) 99999-0000",
    "email": "maria@exemplo.com",
    "message": "Quero conhecer a mentoria",
    "utm_source": "google", "utm_medium": "cpc", "utm_campaign": "lancamento-q4",
    "utm_content": "video-02", "gclid": "Cj0KCQ...",
    "ad_id": "120211111111111111",
    "extra": {"cargo": "Diretora", "faturamento": "50k-100k"},
    "cidade": "Fortaleza"
  }'
```

(`cidade` não é um campo conhecido: vai para `extra.cidade`.)

**Simulação sem criar nada** (valida o token e mostra como cada campo foi lido): acrescente `?test=1`.

```bash
curl -X POST "https://api.r7one.app/webhooks/leads/$R7_WEBHOOK_TOKEN?test=1" \
  -H "Content-Type: application/json" -d '{"nome":"Teste","telefone":"85999990000"}'
# 200 {"ok": true, "test": true, "parsed": {"name": "Teste", "phone": "85999990000", ...}}
```

Script pronto: `scripts/send_lead.py --test ...` (token só por variável de ambiente `R7_WEBHOOK_TOKEN`).

## Resposta de sucesso (`200`)

```json
{
  "ok": true,
  "lead_id": "00000000-0000-4000-8000-000000000000",
  "channel": "webhook",
  "received": ["name", "phone", "utm_source"],
  "alt_phone_added": true
}
```

`received` lista as chaves que você enviou. `alt_phone_added` só aparece quando o telefone enviado foi adicionado como telefone alternativo de um lead já existente.

## O que acontece no R7 One

- **Pessoa nova** (telefone/e-mail inéditos na empresa): cria o lead **e** uma oportunidade (card) na primeira etapa do funil de entrada padrão.
- **Pessoa que já existe sem oportunidade ativa:** cria só a oportunidade.
- **Pessoa que já existe com oportunidade ativa:** não cria card novo; atualiza o cadastro, registra a nova "levantada de mão" e **não troca origem nem responsável**.
- A atribuição do **primeiro contato** é preservada; capturas posteriores só atualizam o último contato.
- Quando cria um **lead novo**, dispara os eventos de saída `lead.created` **e** `deal.created` (a oportunidade que nasce) para os webhooks de saída da empresa (ver `outbound-webhooks.md`).
- Toda tentativa, boa ou ruim, é registrada no log de webhooks da empresa.

## Erros

| HTTP | Corpo | Quando | O que fazer |
|---|---|---|---|
| 400 | `{"error":"Payload inválido: envie um objeto JSON"}` | corpo vazio, não-JSON ou JSON que não é objeto (acontece **antes** de validar o token) | corrija o corpo |
| 400 | `{"error":"Informe ao menos e-mail ou telefone"}` | sem e-mail válido nem telefone | envie um dos dois |
| 404 | `{"error":"Token inválido"}` | token ausente, curto (<20) ou desconhecido | confira o token |
| 405 | `{"error":"Use POST com corpo JSON"}` | GET (ferramentas testam a URL com GET) | use POST |
| 409 | `{"error":"...","code":"idempotency_conflict"}` | mesma `Idempotency-Key` com payload diferente | gere outra chave |
| 409 | `{"error":"E-mail e telefone pertencem a leads diferentes","code":"identity_conflict"}` | o e-mail é de um lead e o telefone de outro | envie só um identificador ou resolva o duplicado no app |
| 423 | `{"error":"...","detail":"..."}` | empresa em **implantação**: captura temporariamente recusada | tente depois ou fale com o R7 One |
| 500 | `{"error":"Não foi possível registrar o lead"}` | falha interna | repita com a **mesma** `Idempotency-Key` |
| 403 | `error code: 1010` (texto) | Cloudflare bloqueou o User-Agent | defina um User-Agent |

Estratégia de retry: em `5xx`, timeout ou erro de rede, repita com **a mesma `Idempotency-Key`** (assim não duplica). Não repita `400`, `404`, `405`, `409` nem `423` sem mudar algo.

## Limites

- **Tamanho do corpo:** até **1 MiB** (1 048 576 bytes). Acima disso: `413 {"error":"payload_too_large"}`, antes de validar o token. Um lead real tem poucos KB. (Antes do PR #884 não havia teto: testei 1, 5 e 20 MB e todos foram aceitos.)
- **Taxa:** **300 req/min por IP** e **600 req/min por token**; acima disso `429 {"error":"rate_limited"}` com `Retry-After` (segundos). **Respeite sempre o `Retry-After`** e reenvie depois; para importação em lote, distribua o envio e use `Idempotency-Key`. Token inexistente ou desativado responde `404` e conta num freio à parte: **20 respostas 404/min por IP**, depois `429`. Não insista em loop com token errado. A contagem é por processo do servidor (pode chegar a 2x durante um deploy).
- A resposta só volta depois que lead, oportunidade e atividade inicial são gravados (tudo na mesma transação); se algo falhar, nada fica pela metade.
