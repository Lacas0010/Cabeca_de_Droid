"""
Auto-Updater via GitHub Releases para o Cabeça de Droid.

Fornece:
  - Verificação assíncrona de novas releases semânticas no GitHub
  - Download em background com rastreamento de progresso (0.0 a 1.0)
  - Extração segura contra ZipSlip
  - Substituição segura do executável no Windows via script .bat desanexado
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import httpx

import version as app_version

try:
    from packaging.version import InvalidVersion, Version
except ImportError:  # Fallback seguro caso packaging não esteja disponível
    Version = None  # type: ignore[assignment]
    InvalidVersion = Exception  # type: ignore[assignment]


GITHUB_REPO = "Lacas0010/Cabeca_de_Droid"
GITHUB_RELEASES_LATEST_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_RELEASES_PAGE_URL = f"https://github.com/{GITHUB_REPO}/releases"
ALLOWED_DOWNLOAD_PREFIXES = (
    "https://github.com/",
    "https://objects.githubusercontent.com/",
    "https://release-assets.githubusercontent.com/",
    "https://codeload.github.com/",
)
PRESERVED_USER_NAMES = (".env", "hoyo_app.db", "cookies.json", "cookies.enc")

_STATE_LOCK = threading.Lock()
_UPDATER_STATE: Dict[str, Any] = {
    "running": False,
    "stage": "idle",
    "progress": 0.0,
    "message": "Pronto para verificar atualizações.",
    "is_frozen": bool(getattr(sys, "frozen", False)),
    "target_version": None,
    "release_url": GITHUB_RELEASES_PAGE_URL,
    "error": None,
}


def get_current_version() -> str:
    return str(getattr(app_version, "__version__", "1.0.0")).lstrip("vV").strip()


def is_app_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def parse_semver_tuple(raw_version: str) -> Tuple[int, ...]:
    cleaned = str(raw_version or "").lstrip("vV").strip()
    core = cleaned.split("-", 1)[0].split("+", 1)[0]
    nums = [int(p) for p in re.findall(r"\d+", core)]
    return tuple(nums) if nums else (0,)


def is_newer_version(latest_raw: str, current_raw: str) -> bool:
    latest_clean = str(latest_raw or "").lstrip("vV").strip()
    current_clean = str(current_raw or "").lstrip("vV").strip()
    if not latest_clean:
        return False
    if Version is not None:
        try:
            return Version(latest_clean) > Version(current_clean)
        except InvalidVersion:
            pass
    return parse_semver_tuple(latest_clean) > parse_semver_tuple(current_clean)


def select_windows_zip_asset(assets: list[dict[str, Any]]) -> Tuple[Optional[str], int]:
    """Seleciona o asset .zip do Windows a partir da resposta da API do GitHub."""
    candidates = [
        a
        for a in (assets or [])
        if str(a.get("name") or "").lower().endswith(".zip") and a.get("browser_download_url")
    ]
    if not candidates:
        return None, 0

    for preferred_token in ("cabeca_de_droid-windows", "windows-x64", "windows"):
        for asset in candidates:
            if preferred_token in str(asset.get("name") or "").lower():
                return str(asset["browser_download_url"]), int(asset.get("size") or 0)

    first = candidates[0]
    return str(first["browser_download_url"]), int(first.get("size") or 0)


async def check_for_updates(timeout_sec: float = 5.0) -> Dict[str, Any]:
    """Consulta de forma assíncrona a última release no GitHub (tolerante a modo offline)."""
    current = get_current_version()
    frozen = is_app_frozen()
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"Cabeca-de-Droid/{current}",
    }

    try:
        async with httpx.AsyncClient(timeout=timeout_sec, follow_redirects=True) as client:
            resp = await client.get(GITHUB_RELEASES_LATEST_URL, headers=headers)
            resp.raise_for_status()
            payload = resp.json()
    except Exception as exc:
        return {
            "update_available": False,
            "is_frozen": frozen,
            "current_version": current,
            "latest_version": current,
            "release_notes": "",
            "download_url": None,
            "asset_size": 0,
            "release_url": GITHUB_RELEASES_PAGE_URL,
            "error": str(exc),
        }

    latest_tag = str(payload.get("tag_name") or "").strip()
    latest = latest_tag.lstrip("vV").strip() or current
    download_url, asset_size = select_windows_zip_asset(payload.get("assets") or [])
    release_notes = str(payload.get("body") or "").strip()
    release_url = str(payload.get("html_url") or GITHUB_RELEASES_PAGE_URL)
    update_available = is_newer_version(latest, current)

    return {
        "update_available": update_available,
        "is_frozen": frozen,
        "current_version": current,
        "latest_version": latest,
        "release_notes": release_notes,
        "download_url": download_url,
        "asset_size": asset_size,
        "release_url": release_url,
        "error": None,
    }


def _set_state(**kwargs: Any) -> None:
    with _STATE_LOCK:
        _UPDATER_STATE.update(kwargs)


def get_updater_status() -> Dict[str, Any]:
    with _STATE_LOCK:
        snapshot = dict(_UPDATER_STATE)
    snapshot["is_frozen"] = is_app_frozen()
    return snapshot


def safe_extract_zip(zip_path: Path, extract_dir: Path) -> Path:
    """Extrai um arquivo ZIP garantindo proteção contra ZipSlip."""
    extract_dir.mkdir(parents=True, exist_ok=True)
    target_root = extract_dir.resolve()

    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            member_path = (target_root / member.filename).resolve()
            if not str(member_path).startswith(str(target_root)):
                raise ValueError(f"Entrada ZIP inválida detectada (ZipSlip): {member.filename}")
        zf.extractall(target_root)

    return target_root


def resolve_extracted_payload_dir(extract_root: Path) -> Path:
    """Resolve a pasta que contém Cabeca_de_Droid.exe após extração."""
    for exe_candidate in extract_root.rglob("*.exe"):
        return exe_candidate.parent
    return extract_root


def build_windows_update_batch_script(
    pid: int,
    source_dir: Path,
    target_dir: Path,
    exe_path: Path,
    temp_root: Path,
    parent_pid: Optional[int] = None,
    log_path: Optional[Path] = None,
) -> str:
    """
    Gera um script .bat em %TEMP% que aguarda o encerramento do processo atual
    (e do bootloader pai do PyInstaller --onefile), substitui o executável e
    demais arquivos preservando dados do usuário, reinicia o novo .exe em ambiente
    limpo e remove os temporários.
    """
    preserved_list = " ".join(f'"{name}"' for name in PRESERVED_USER_NAMES)
    resolved_ppid = int(parent_pid) if (parent_pid and int(parent_pid) > 0 and int(parent_pid) != int(pid)) else 0
    resolved_log = log_path or (temp_root.parent / "cabeca_updater_last.log")
    return "\r\n".join(
        [
            "@echo off",
            "chcp 65001 >NUL 2>&1",
            "setlocal enabledelayedexpansion",
            f"set PID={int(pid)}",
            f"set PPID={resolved_ppid}",
            f'set "SRC_DIR={source_dir}"',
            f'set "DST_DIR={target_dir}"',
            f'set "EXE_PATH={exe_path}"',
            f'set "EXE_NAME={exe_path.name}"',
            f'set "TMP_ROOT={temp_root}"',
            f'set "LOG_FILE={resolved_log}"',
            "",
            'echo [Updater] Inicio %DATE% %TIME% PID=%PID% PPID=%PPID% > "%LOG_FILE%"',
            'echo [Updater] SRC=%SRC_DIR% >> "%LOG_FILE%"',
            'echo [Updater] DST=%DST_DIR% >> "%LOG_FILE%"',
            "",
            "set WAIT_TRIES=0",
            ":wait_exit",
            "set STILL_RUNNING=0",
            'tasklist /FI "PID eq %PID%" 2>NUL | findstr /R "\\<%PID%\\>" >NUL',
            "if not errorlevel 1 set STILL_RUNNING=1",
            'if not "%PPID%"=="0" (',
            '    tasklist /FI "PID eq %PPID%" 2>NUL | findstr /R "\\<%PPID%\\>" >NUL',
            "    if not errorlevel 1 set STILL_RUNNING=1",
            ")",
            'if "%STILL_RUNNING%"=="1" (',
            "    ping -n 2 127.0.0.1 >NUL",
            "    set /a WAIT_TRIES+=1",
            "    if !WAIT_TRIES! LSS 30 goto wait_exit",
            ")",
            "",
            "ping -n 2 127.0.0.1 >NUL",
            'if not exist "%DST_DIR%" mkdir "%DST_DIR%"',
            'if exist "%DST_DIR%\\%EXE_NAME%.old" del /F /Q "%DST_DIR%\\%EXE_NAME%.old" >NUL 2>&1',
            "",
            f'robocopy "%SRC_DIR%" "%DST_DIR%" /E /IS /IT /R:3 /W:1 /XF {preserved_list} *.db *.sqlite *.sqlite3 *.enc *.key *.exe /XD zzz hsr genshin logs cache >> "%LOG_FILE%" 2>&1',
            "",
            "set COPY_TRIES=0",
            ":copy_exe_loop",
            'copy /Y "%SRC_DIR%\\%EXE_NAME%" "%EXE_PATH%" >> "%LOG_FILE%" 2>&1',
            "if not errorlevel 1 goto exe_replaced",
            'if exist "%EXE_PATH%" (',
            '    move /Y "%EXE_PATH%" "%DST_DIR%\\%EXE_NAME%.old" >NUL 2>&1',
            '    copy /Y "%SRC_DIR%\\%EXE_NAME%" "%EXE_PATH%" >> "%LOG_FILE%" 2>&1',
            "    if not errorlevel 1 goto exe_replaced",
            ")",
            "set /a COPY_TRIES+=1",
            "if !COPY_TRIES! LSS 20 (",
            "    ping -n 2 127.0.0.1 >NUL",
            "    goto copy_exe_loop",
            ")",
            'echo [Updater] ERRO: Nao foi possivel substituir "%EXE_PATH%" >> "%LOG_FILE%"',
            "goto cleanup",
            "",
            ":exe_replaced",
            'echo [Updater] Executavel atualizado com sucesso em "%EXE_PATH%" >> "%LOG_FILE%"',
            'if exist "%DST_DIR%\\%EXE_NAME%.old" del /F /Q "%DST_DIR%\\%EXE_NAME%.old" >NUL 2>&1',
            'start "" /D "%DST_DIR%" "%EXE_PATH%"',
            'echo [Updater] Novo processo iniciado >> "%LOG_FILE%"',
            "",
            ":cleanup",
            "ping -n 3 127.0.0.1 >NUL",
            'if exist "%TMP_ROOT%" rmdir /S /Q "%TMP_ROOT%" >NUL 2>&1',
            '(goto) 2>nul & del "%~f0"',
            "",
        ]
    )


def _build_clean_subprocess_env() -> Dict[str, str]:
    """Remove variáveis internas do PyInstaller (_PYI_* / _MEIPASS*) para que o novo .exe reinicie limpo."""
    clean_env = dict(os.environ)
    for key in list(clean_env.keys()):
        upper = key.upper()
        if upper.startswith("_PYI_") or upper.startswith("_MEIPASS") or upper in (
            "PYTHONHOME",
            "PYTHONPATH",
            "TCL_LIBRARY",
            "TK_LIBRARY",
        ):
            clean_env.pop(key, None)

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass and "PATH" in clean_env:
        norm_mei = os.path.normcase(os.path.normpath(str(meipass)))
        filtered_paths = [
            p for p in clean_env["PATH"].split(os.pathsep)
            if p and os.path.normcase(os.path.normpath(p)) != norm_mei
        ]
        clean_env["PATH"] = os.pathsep.join(filtered_paths)
    return clean_env


def _launch_detached_batch_and_exit(bat_path: Path) -> None:
    creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200) | getattr(
        subprocess, "CREATE_NO_WINDOW", 0x08000000
    )
    subprocess.Popen(
        ["cmd", "/c", str(bat_path)],
        cwd=str(bat_path.parent),
        env=_build_clean_subprocess_env(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creation_flags,
        close_fds=True,
    )
    os._exit(0)


def _download_zip_with_progress(download_url: str, dest_zip: Path) -> None:
    if not any(download_url.startswith(prefix) for prefix in ALLOWED_DOWNLOAD_PREFIXES):
        raise ValueError("URL de download fora dos domínios oficiais do GitHub.")

    headers = {"User-Agent": f"Cabeca-de-Droid/{get_current_version()}"}
    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        with client.stream("GET", download_url, headers=headers) as response:
            response.raise_for_status()
            total_bytes = int(response.headers.get("Content-Length") or 0)
            downloaded = 0
            with open(dest_zip, "wb") as out_file:
                for chunk in response.iter_bytes(chunk_size=65536):
                    if not chunk:
                        continue
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    if total_bytes > 0:
                        ratio = min(1.0, downloaded / total_bytes)
                        _set_state(
                            progress=round(0.05 + ratio * 0.65, 3),
                            message=f"Baixando atualização... ({int(ratio * 100)}%)",
                        )


def _run_frozen_update_worker(download_url: str, target_version: str) -> None:
    temp_dir: Optional[Path] = None
    try:
        temp_dir = Path(tempfile.mkdtemp(prefix="cabeca_updater_"))
        zip_path = temp_dir / "update.zip"
        extract_dir = temp_dir / "extracted"

        _set_state(
            running=True,
            stage="downloading",
            progress=0.05,
            message="Baixando atualização...",
            target_version=target_version,
            error=None,
        )
        _download_zip_with_progress(download_url, zip_path)

        _set_state(
            stage="extracting",
            progress=0.80,
            message="Extraindo arquivos da nova versão...",
        )
        safe_extract_zip(zip_path, extract_dir)
        payload_dir = resolve_extracted_payload_dir(extract_dir)

        exe_path = Path(sys.executable).resolve()
        app_dir = exe_path.parent
        exes_in_payload = list(payload_dir.glob("*.exe"))
        new_exe_name = exes_in_payload[0].name if exes_in_payload else exe_path.name
        target_exe_path = app_dir / new_exe_name

        bat_fd, bat_raw = tempfile.mkstemp(prefix="cabeca_apply_", suffix=".bat")
        os.close(bat_fd)
        bat_path = Path(bat_raw)
        bat_content = build_windows_update_batch_script(
            pid=os.getpid(),
            parent_pid=os.getppid(),
            source_dir=payload_dir,
            target_dir=app_dir,
            exe_path=target_exe_path,
            temp_root=temp_dir,
        )
        with open(bat_path, "w", encoding="utf-8", newline="") as bat_file:
            bat_file.write(bat_content)

        _set_state(
            running=False,
            stage="applying",
            progress=1.0,
            message="Reiniciando aplicação para concluir atualização...",
        )
        time.sleep(1.5)
        _launch_detached_batch_and_exit(bat_path)
    except Exception as exc:
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        _set_state(
            running=False,
            stage="error",
            progress=0.0,
            message=f"Falha ao atualizar: {exc}",
            error=str(exc),
        )


async def start_update_process(
    download_url: Optional[str] = None,
    target_version: Optional[str] = None,
    release_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Inicia a rotina de download/instalação (ou orienta git pull no modo desenvolvimento)."""
    with _STATE_LOCK:
        already_running = bool(_UPDATER_STATE.get("running"))
    if already_running:
        return get_updater_status()

    if not is_app_frozen():
        latest_url = release_url or GITHUB_RELEASES_PAGE_URL
        _set_state(
            running=False,
            stage="dev_mode",
            progress=1.0,
            message="Modo desenvolvimento (Python/Git): execute 'git pull origin main' ou baixe a release manualmente.",
            target_version=target_version,
            release_url=latest_url,
            error=None,
        )
        return get_updater_status()

    resolved_url = download_url
    resolved_ver = target_version
    resolved_page = release_url or GITHUB_RELEASES_PAGE_URL

    if not resolved_url:
        check_info = await check_for_updates()
        resolved_url = check_info.get("download_url")
        resolved_ver = check_info.get("latest_version")
        resolved_page = check_info.get("release_url") or resolved_page

    if not resolved_url:
        _set_state(
            running=False,
            stage="error",
            progress=0.0,
            message="Pacote Windows (.zip) não encontrado na release selecionada.",
            release_url=resolved_page,
            error="Pacote Windows (.zip) ausente nos assets da release.",
        )
        return get_updater_status()

    _set_state(
        running=True,
        stage="downloading",
        progress=0.02,
        message="Iniciando download da atualização...",
        target_version=resolved_ver,
        release_url=resolved_page,
        error=None,
    )
    worker = threading.Thread(
        target=_run_frozen_update_worker,
        args=(resolved_url, str(resolved_ver or "")),
        daemon=True,
    )
    worker.start()
    return get_updater_status()
