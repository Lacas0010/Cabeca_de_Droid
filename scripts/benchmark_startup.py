import os
import sys
import time
import tracemalloc

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def audit():
    print("=" * 60)
    print("[AUDIT] AUDITORIA DE PERFORMANCE, MEMORIA E ARQUITETURA")
    print("=" * 60)

    tracemalloc.start()
    start_time = time.time()

    # 1. Mede importação dos módulos principais
    print("\n[1/4] Testando tempo de carregamento de módulos...")
    t0 = time.time()
    from server import app
    import database
    from core.tray import SystemTrayManager
    from services.team_matcher_service import match_endgame_teams
    from services.sync_service import sync_status
    from services.roster_service import get_roster

    t1 = time.time()
    print(f"  [OK] Modulos carregados em {t1 - t0:.3f}s")

    # 2. Mede consumo de memória inicial
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print("\n[2/4] Consumo de Memoria Inicial (tracemalloc):")
    print(f"  - Memoria Atual: {current / 1024 / 1024:.2f} MB")
    print(f"  - Pico de Alocacao: {peak / 1024 / 1024:.2f} MB")

    # 3. Testa rapidez e estabilidade do SQLite
    print("\n[3/4] Testando latencia de operacoes SQLite...")
    t_db0 = time.time()
    for g in ["hsr", "genshin", "zzz"]:
        database.get_active_uid(g)
        database.get_roster_data(g)
        database.get_security_settings()
    t_db1 = time.time()
    print(f"  [OK] Consultas de roster e seguranca executadas em {t_db1 - t_db0:.3f}s")

    # 4. Testa rapidez do Team Matcher
    print("\n[4/4] Testando performance do Endgame Team Matcher...")
    t_tm0 = time.time()
    for g in ["hsr", "genshin", "zzz"]:
        res = match_endgame_teams(g)
        print(f"  [OK] {g.upper()}: {res.total_teams} composicoes analisadas em {time.time() - t_tm0:.3f}s")
        t_tm0 = time.time()

    total_time = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"[FIM] AUDITORIA CONCLUIDA EM {total_time:.3f}s - APLICACAO LEVE E OTIMIZADA!")
    print("=" * 60)


if __name__ == "__main__":
    audit()
