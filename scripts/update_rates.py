#!/usr/bin/env python3
"""Gera rates.json para o app Quanto é.

- Peso -> dólar: taxa Visa (a que a Nomad aplica nas compras em pesos), pela calculadora pública da Visa.
- Dólar -> real: cotação comercial (AwesomeAPI; reserva: open.er-api.com).

Se uma fonte falhar, mantém o último valor bom publicado (ou o valor-semente do repositório),
com a data original, para o app mostrar que está desatualizado.

Uso: python3 scripts/update_rates.py caminho/de/saida/rates.json
"""
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36")
UTC = dt.timezone.utc
HERE = os.path.dirname(os.path.abspath(__file__))


def log(*a):
    print(*a, file=sys.stderr)


def get_json(url, headers=None, timeout=20):
    h = {"User-Agent": UA, "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US,en;q=0.9"}
    h.update(headers or {})
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def visa_ars():
    """Pesos por dólar na taxa Visa. Tenta hoje e volta até 6 dias."""
    today = dt.datetime.now(UTC).date()
    referer = "https://usa.visa.com/support/consumer/travel-support/exchange-rate-calculator.html"
    for back in range(0, 7):
        d = today - dt.timedelta(days=back)
        ds = d.strftime("%m/%d/%Y")
        q = urllib.parse.urlencode({
            "amount": "1", "fee": "0", "utcConvertedDate": ds, "exchangedate": ds,
            "fromCurr": "USD", "toCurr": "ARS",
        })
        try:
            j = get_json("https://usa.visa.com/cmsapi/fx/rates?" + q, {"Referer": referer})
            ov = j.get("originalValues") or {}
            # fromCurr = moeda do cartão (USD), toCurr = moeda da compra (ARS);
            # fxRateVisa vem em dólares por peso.
            fx = float(ov.get("fxRateVisa") or 0)
            if fx > 0:
                as_of = ov.get("asOfDate")
                date = dt.datetime.fromtimestamp(int(as_of), UTC).date().isoformat() if as_of else d.isoformat()
                return {"arsPerUsd": round(1 / fx, 4), "date": date,
                        "fetched": dt.datetime.now(UTC).isoformat(timespec="seconds"), "source": "visa"}
            log("visa", ds, "sem taxa:", str(j)[:200])
        except Exception as e:  # noqa: BLE001
            log("visa", ds, "falhou:", repr(e)[:200])
    return None


def brl_commercial():
    try:
        q = get_json("https://economia.awesomeapi.com.br/json/last/USD-BRL")["USDBRL"]
        t = dt.datetime.fromtimestamp(int(q["timestamp"]), UTC).isoformat(timespec="seconds")
        return {"commercial": round(float(q["ask"]), 4), "time": t, "source": "awesomeapi"}
    except Exception as e:  # noqa: BLE001
        log("awesomeapi falhou:", repr(e)[:200])
    try:
        j = get_json("https://open.er-api.com/v6/latest/USD")
        t = dt.datetime.fromtimestamp(int(j["time_last_update_unix"]), UTC).isoformat(timespec="seconds")
        return {"commercial": round(float(j["rates"]["BRL"]), 4), "time": t, "source": "er-api"}
    except Exception as e:  # noqa: BLE001
        log("er-api falhou:", repr(e)[:200])
    return None


def previous():
    url = os.environ.get("PAGES_URL")
    if url:
        try:
            return get_json(url.rstrip("/") + "/rates.json?nocache=" + str(int(dt.datetime.now().timestamp())))
        except Exception as e:  # noqa: BLE001
            log("rates.json publicado indisponível:", repr(e)[:200])
    try:
        with open(os.path.join(HERE, "seed_rates.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return {}


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "rates.json"
    prev = previous()
    visa = visa_ars()
    brl = brl_commercial()
    data = {
        "updated": dt.datetime.now(UTC).isoformat(timespec="seconds"),
        "visa": visa or prev.get("visa"),
        "brl": brl or prev.get("brl"),
    }
    log("visa:", "nova" if visa else "anterior", data["visa"])
    log("brl:", "nova" if brl else "anterior", data["brl"])
    if os.environ.get("GITHUB_ACTIONS"):
        # Anotações visíveis no resumo da execução do workflow
        level = "notice" if visa else "warning"
        print(f"::{level} title=Visa ({'nova' if visa else 'anterior'})::{json.dumps(data['visa'])}")
        print(f"::{'notice' if brl else 'warning'} title=Real ({'nova' if brl else 'anterior'})::{json.dumps(data['brl'])}")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    if not data["visa"]:
        sys.exit("Sem taxa Visa (nem anterior).")


if __name__ == "__main__":
    main()
