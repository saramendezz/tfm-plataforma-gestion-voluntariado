"""Prueba de carga básica (RNF-03). Solo biblioteca estándar.
Uso: python tools/loadtest.py --base http://127.0.0.1:8000 --users 20 --requests 50
Requiere: python manage.py seed_demo --reset y el servidor en marcha."""
import argparse, json, statistics, time
from concurrent.futures import ThreadPoolExecutor
from urllib import request, error

PASSWORD = "Demo-2026-pass"


def call(base, path, token=None, data=None, timeout=15):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    body = json.dumps(data).encode() if data is not None else None
    req = request.Request(base + path, data=body, headers=headers)
    try:
        with request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"null")
    except error.HTTPError as e:
        return e.code, None
    except Exception:
        return 0, None


def login(base, username):
    status, body = call(base, "/api/auth/login/", data={"username": username, "password": PASSWORD})
    if status != 200 or not body:
        raise SystemExit(f"No se pudo iniciar sesión con {username} (estado {status}). ¿Ejecutaste seed_demo?")
    return body["access"]


def timed(base, path, token):
    t = time.perf_counter()
    status, _ = call(base, path, token)
    return (time.perf_counter() - t) * 1000, status == 200


def run(base, label, path_for, tokens, total, workers):
    jobs = [(path_for(i), tokens[i % len(tokens)]) for i in range(total)]
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        res = list(ex.map(lambda j: timed(base, j[0], j[1]), jobs))
    wall = time.perf_counter() - t0
    times = sorted(r[0] for r in res)
    errors = sum(1 for r in res if not r[1])
    p95 = times[max(0, int(len(times) * 0.95) - 1)]
    print(f"{label:<28}{workers:>5}{total:>8}{errors:>8}{statistics.mean(times):>9.0f}{p95:>9.0f}{total / wall:>9.1f}")
    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--users", type=int, default=20)
    ap.add_argument("--requests", type=int, default=50)
    a = ap.parse_args()
    vols = [login(a.base, f"demo_vol{i:02d}") for i in range(1, a.users + 1)]
    org = login(a.base, "demo_org1")
    status, needs = call(a.base, "/api/needs/", org)
    items = needs.get("results", []) if isinstance(needs, dict) else (needs or [])
    need_id = items[0]["id"] if items else 1
    print(f"{'Endpoint':<28}{'Conc.':>5}{'Pet.':>8}{'Err.':>8}{'Media':>9}{'P95':>9}{'Pet/s':>9}   (ms)")
    errs = 0
    for c in (1, 10, 25):
        errs += run(a.base, "needs/compatible/", lambda i: "/api/needs/compatible/", vols, a.requests, c)
        errs += run(a.base, "needs/ (organización)", lambda i: "/api/needs/", [org], a.requests, c)
        errs += run(a.base, "needs/<id>/potential/", lambda i: f"/api/needs/{need_id}/potential/", [org], a.requests, c)
    print(f"Errores totales: {errs}")


if __name__ == "__main__":
    main()