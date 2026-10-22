#!/usr/bin/env python3
"""
==============================================================================
Cabeça de Droid - Script Único de Validação e Auto-Correção do Código
==============================================================================
Executa em sequência estrita:
1. Linter e Verificação de Sintaxe: `ruff check .`
2. Formatação de Código: `ruff format --check .`
3. Checagem Estática de Tipos: `mypy` focado em `schemas/` e `services/`
4. Suíte Completa de Testes Unitários Offline: `python -m unittest discover tests`

Uso no Antigravity IDE:
    python scripts/verify_codebase.py
==============================================================================
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# Configura encoding UTF-8 resiliente para Windows / PowerShell
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Raiz do projeto
ROOT_DIR = Path(__file__).resolve().parent.parent
os.chdir(ROOT_DIR)

# Localiza executáveis (preferindo .venv local se existir)
VENV_SCRIPTS = ROOT_DIR / ".venv" / ("Scripts" if sys.platform == "win32" else "bin")


def get_executable(name: str) -> str:
    """Retorna o caminho do executável dentro da .venv ou no PATH global."""
    if VENV_SCRIPTS.exists():
        exe_ext = ".exe" if sys.platform == "win32" else ""
        venv_candidate = VENV_SCRIPTS / f"{name}{exe_ext}"
        if venv_candidate.exists():
            return str(venv_candidate)
    return name


RUFF_BIN = get_executable("ruff")
MYPY_BIN = get_executable("mypy")
PYTHON_BIN = get_executable("python")


def run_step(step_name: str, cmd: list) -> bool:
    """Executa uma etapa de verificação com relatório claro de progresso."""
    sep = "=" * 78
    print(f"\n{sep}")
    print(f">> [{step_name.upper()}] Executando: {' '.join(cmd)}")
    print(f"{sep}")

    start_time = time.time()
    try:
        result = subprocess.run(cmd, cwd=str(ROOT_DIR), check=False)
        elapsed = time.time() - start_time

        if result.returncode == 0:
            print(f"[OK] [{step_name.upper()}] APROVADO com sucesso ({elapsed:.2f}s)")
            return True
        else:
            print(f"[FAIL] [{step_name.upper()}] FALHOU com código de saída {result.returncode} ({elapsed:.2f}s)")
            return False
    except FileNotFoundError as fnf:
        print(f"[FAIL] [{step_name.upper()}] Executável não encontrado ({cmd[0]}): {fnf}")
        print("  Dica: Execute '.venv\\Scripts\\pip install ruff mypy' para habilitar as verificações.")
        return False
    except Exception as exc:
        print(f"[FAIL] [{step_name.upper()}] Erro inesperado ao executar: {exc}")
        return False


def main() -> int:
    print("\n" + "#" * 78)
    print("  CABEÇA DE DROID - SUÍTE COMPLETA DE VALIDAÇÃO DE QUALIDADE (CI/CD)")
    print("#" * 78)

    steps = [
        ("1. Linter e Sintaxe (Ruff Check)", [RUFF_BIN, "check", "."]),
        ("2. Estilo e Formatação (Ruff Format)", [RUFF_BIN, "format", "--check", "."]),
        (
            "3. Checagem de Tipos Estáticos (Mypy)",
            [MYPY_BIN, "--ignore-missing-imports", "--no-strict-optional", "schemas/", "services/"],
        ),
        ("4. Suíte de Testes Unitários (Unittest)", [PYTHON_BIN, "-m", "unittest", "discover", "tests"]),
    ]

    total_start = time.time()
    for name, cmd in steps:
        success = run_step(name, cmd)
        if not success:
            total_elapsed = time.time() - total_start
            print("\n" + "!" * 78)
            print(f"[ERRO] VALIDAÇÃO INTERROMPIDA: A etapa '{name}' reportou inconsistências.")
            print(f"Tempo total transcorrido: {total_elapsed:.2f}s")
            print("Corrija os erros apontados acima antes de finalizar o ciclo de código.")
            print("!" * 78 + "\n")
            return 1

    total_elapsed = time.time() - total_start
    print("\n" + "=" * 78)
    print(">> SUCESSO TOTAL! Todas as 4 etapas de validação passaram com ZERO erros.")
    print(f"   Código 100% aprovado, tipado e com testes unitários em {total_elapsed:.2f}s.")
    print("=" * 78 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
