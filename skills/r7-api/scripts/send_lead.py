#!/usr/bin/env python3
"""Envia um lead ao webhook universal do R7 One (somente biblioteca padrão).

O token do webhook é da sua empresa e é um SEGREDO: passe por variável de ambiente, nunca em arquivo ou log.

  export R7_WEBHOOK_TOKEN=...            # app R7 One > Configurações > Integrações
  python3 send_lead.py --test --phone "+5585999990000"          # simulação: valida token e mostra como os campos serão lidos
  python3 send_lead.py --name "Maria" --phone "+5585999990000" --email maria@exemplo.com --utm-source google \
       --idempotency-key pedido-123                                # envio real (cria lead e oportunidade)

Campos extras: --extra '{"cargo":"Diretor"}'.  Saída: status HTTP e corpo da resposta (o token nunca é impresso).
"""
import argparse, json, os, sys, urllib.error, urllib.request

BASE = os.environ.get("R7_API", "https://api.r7one.app")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--test", action="store_true", help="simulação (?test=1): não cria nada")
    for f in ("name", "email", "phone", "message", "utm-source", "utm-medium", "utm-campaign", "utm-term", "utm-content",
              "idempotency-key"):
        ap.add_argument("--" + f)
    ap.add_argument("--extra", help="objeto JSON com campos livres")
    a = ap.parse_args()
    token = os.environ.get("R7_WEBHOOK_TOKEN", "")
    if len(token) < 20:
        sys.exit("Defina R7_WEBHOOK_TOKEN (token do webhook da empresa).")
    body = {k.replace("-", "_"): v for k, v in vars(a).items()
            if v and k not in ("test", "extra", "idempotency_key")}
    if a.extra:
        body["extra"] = json.loads(a.extra)
    url = f"{BASE}/webhooks/leads/{token}" + ("?test=1" if a.test else "")
    # O Cloudflare na frente da API bloqueia User-Agents de biblioteca padrão (erro 1010): envie um próprio.
    headers = {"Content-Type": "application/json", "User-Agent": "r7-api-skill/1.0"}
    if a.idempotency_key:
        headers["Idempotency-Key"] = a.idempotency_key
    req = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(r.status, r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(e.code, e.read().decode("utf-8"))
        sys.exit(1)


if __name__ == "__main__":
    main()
