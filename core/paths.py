import os
import sys
import shutil
from typing import List

APP_NAME = "Cabeca_de_Droid"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def is_frozen() -> bool:
    """Retorna True quando executado a partir de um pacote congelado (PyInstaller)."""
    return bool(getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))


def get_bundle_root() -> str:
    """Retorna a raiz de recursos empacotados (_MEIPASS em produção ou raiz do repo em dev)."""
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return PROJECT_ROOT


def get_data_dir() -> str:
    """
    Retorna o diretório gravável para dados persistentes (SQLite, cofre, cache, guias, logs).
    - Override explícito via CABECA_DE_DROID_DATA_DIR (útil para testes e portabilidade).
    - Executável congelado no Windows: %APPDATA%\\Cabeca_de_Droid.
    - Executável congelado POSIX: ~/.local/share/Cabeca_de_Droid.
    - Modo desenvolvimento/servidor Linux: raiz do projeto.
    """
    override = os.environ.get("CABECA_DE_DROID_DATA_DIR", "").strip()
    if override:
        os.makedirs(override, exist_ok=True)
        return os.path.abspath(override)

    if is_frozen():
        if sys.platform == "win32":
            base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
        else:
            base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
        data_dir = os.path.join(base, APP_NAME)
        os.makedirs(data_dir, exist_ok=True)
        return os.path.abspath(data_dir)

    return PROJECT_ROOT


def get_data_path(relative_path: str) -> str:
    """Obtém o caminho absoluto gravável dentro do diretório de dados persistentes."""
    return os.path.join(get_data_dir(), relative_path)


def get_resource_path(relative_path: str) -> str:
    """
    Obtém o caminho absoluto para um recurso ou manifesto:
    1. Se já existir versão atualizada/baixada no diretório gravável de dados, prioriza-a.
    2. Caso contrário, resolve contra o bundle (_MEIPASS em produção ou raiz do repo em dev).
    """
    data_candidate = os.path.join(get_data_dir(), relative_path)
    if os.path.exists(data_candidate):
        return data_candidate
    return os.path.join(get_bundle_root(), relative_path)


def _should_upgrade_seeded_file(sub: str, rel_file: str, src_file: str, dst_file: str, version_changed: bool) -> bool:
    """Decide se um arquivo já existente em get_data_dir() deve ser atualizado pelo bundle mais recente."""
    if not os.path.exists(dst_file):
        return True

    norm_rel = rel_file.replace("\\", "/").lower()
    # Ao trocar de versão do .exe, atualiza ícones estáticos empacotados (ex.: HSR HD, Resina corrigida)
    if version_changed and sub == "assets":
        if norm_rel.startswith(("icons/", "resources/", "endgame/", "elements/")):
            return True

    # Para current_banners.json, atualiza se o cache local estiver em schema legado (sem duration_type/end_date)
    # ou mais antigo que o bundle da nova release
    if sub == "static_data" and norm_rel == "current_banners.json":
        try:
            import json

            with open(dst_file, "r", encoding="utf-8") as df:
                dst_data = json.load(df)
            with open(src_file, "r", encoding="utf-8") as sf:
                src_data = json.load(sf)
            if isinstance(dst_data, dict) and isinstance(src_data, dict):
                # Detecta schema legado sem duration_type / end_date
                for g_val in dst_data.values():
                    if not isinstance(g_val, dict):
                        continue
                    for b in g_val.get("banners") or []:
                        if isinstance(b, dict) and b.get("duration_type") is None:
                            return True
                # Ou bundle mais recente via last_updated
                src_ts = max((str(v.get("last_updated") or "") for v in src_data.values() if isinstance(v, dict)), default="")
                dst_ts = max((str(v.get("last_updated") or "") for v in dst_data.values() if isinstance(v, dict)), default="")
                if src_ts and (not dst_ts or src_ts > dst_ts):
                    return True
        except Exception:
            return True

    return False


def seed_bundled_resources(subdirs: List[str] | None = None) -> None:
    """
    Quando executado via executável congelado, copia arquivos iniciais de manifestos/assets
    do bundle (_MEIPASS) para get_data_dir() caso ainda não existam lá, e atualiza assets visuais
    versionados ou caches de banners em schema legado quando o aplicativo é atualizado.
    """
    if not is_frozen():
        return

    bundle_root = get_bundle_root()
    data_root = get_data_dir()
    target_subdirs = subdirs or ["static_data", "assets"]

    current_ver = ""
    try:
        import version as _app_version

        current_ver = str(getattr(_app_version, "__version__", "") or "").strip()
    except Exception:
        current_ver = ""

    marker_path = os.path.join(data_root, ".bundle_version")
    prev_ver = ""
    if os.path.isfile(marker_path):
        try:
            with open(marker_path, "r", encoding="utf-8") as mf:
                prev_ver = mf.read().strip()
        except OSError:
            prev_ver = ""
    version_changed = bool(current_ver and current_ver != prev_ver)

    for sub in target_subdirs:
        src_base = os.path.join(bundle_root, sub)
        if not os.path.isdir(src_base):
            continue
        dst_base = os.path.join(data_root, sub)
        for root, _, files in os.walk(src_base):
            rel_dir = os.path.relpath(root, src_base)
            dst_dir = dst_base if rel_dir == "." else os.path.join(dst_base, rel_dir)
            os.makedirs(dst_dir, exist_ok=True)
            for fname in files:
                src_file = os.path.join(root, fname)
                dst_file = os.path.join(dst_dir, fname)
                rel_file = fname if rel_dir == "." else os.path.join(rel_dir, fname)
                if _should_upgrade_seeded_file(sub, rel_file, src_file, dst_file, version_changed):
                    try:
                        shutil.copy2(src_file, dst_file)
                    except OSError:
                        pass

    if current_ver and version_changed and subdirs is None:
        try:
            with open(marker_path, "w", encoding="utf-8") as mf:
                mf.write(current_ver)
        except OSError:
            pass


def load_local_env() -> None:
    """
    Carrega variáveis opcionais de um arquivo .env (sem dependência externa)
    do diretório do executável/projeto e do diretório de dados persistentes.
    Variáveis já definidas no ambiente do sistema operacional têm precedência.
    """
    candidates = [os.path.join(get_data_dir(), ".env")]
    if is_frozen():
        candidates.insert(0, os.path.join(os.path.dirname(sys.executable), ".env"))
    else:
        candidates.insert(0, os.path.join(PROJECT_ROOT, ".env"))

    for env_path in candidates:
        if not os.path.isfile(env_path):
            continue
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key:
                        os.environ.setdefault(key, val)
        except OSError:
            pass
