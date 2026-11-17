"""
Script de empacotamento standalone para Windows (PyInstaller + ZIP).

Gera:
  - dist/Cabeca_de_Droid.exe (--onefile --noconsole)
  - dist/Cabeca_de_Droid-Windows-x64.zip (contendo Cabeca_de_Droid.exe e .env.example)
"""

import hashlib
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import List


ROOT_DIR = Path(__file__).resolve().parent
BUILD_DIR = ROOT_DIR / "build"
DIST_DIR = ROOT_DIR / "dist"
SPEC_PATH = ROOT_DIR / "Cabeca_de_Droid.spec"

APP_NAME = "Cabeca_de_Droid"
EXE_NAME = f"{APP_NAME}.exe"
ZIP_NAME = f"{APP_NAME}-Windows-x64.zip"

EXCLUDED_ASSET_DIRS = {"cache", "elements", "shards"}
REQUIRED_SAKUGA_COMPONENTS = (
    "button.js",
    "toggle.js",
    "slider.js",
    "checkbox.js",
    "radio.js",
    "input.js",
    "tabs.js",
    "progress.js",
    "rating.js",
    "toast.js",
    "tooltip.js",
)


def verify_sakuga_vendor_assets() -> Path:
    """Garante que os 11 Web Components do Sakuga VFX existem localmente para build 100% offline."""
    vendor_dir = ROOT_DIR / "static" / "vendor" / "sakuga-vfx"
    missing = [name for name in REQUIRED_SAKUGA_COMPONENTS if not (vendor_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(
            f"Componentes Sakuga VFX ausentes em {vendor_dir}: {', '.join(missing)}"
        )
    return vendor_dir


def ensure_icon_file(staging_assets_dir: Path) -> Path:
    """Garante a existência de assets/logo.ico gerado a partir de assets/logo.png se necessário."""
    png_path = ROOT_DIR / "assets" / "logo.png"
    existing_ico = ROOT_DIR / "assets" / "logo.ico"
    staged_ico = staging_assets_dir / "logo.ico"

    if existing_ico.is_file():
        shutil.copy2(existing_ico, staged_ico)
        return staged_ico

    if not png_path.is_file():
        raise FileNotFoundError(f"Ícone fonte não encontrado: {png_path}")

    from PIL import Image

    with Image.open(png_path) as img:
        img.save(
            staged_ico,
            format="ICO",
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )
    return staged_ico


def prepare_staging_assets() -> tuple[Path, Path]:
    """
    Prepara uma cópia limpa dos assets estáticos do repositório (excluindo caches de runtime)
    e retorna (staging_assets_dir, icon_path).
    """
    staging_assets = BUILD_DIR / "bundled_assets"
    if staging_assets.exists():
        shutil.rmtree(staging_assets)
    staging_assets.mkdir(parents=True, exist_ok=True)

    src_assets = ROOT_DIR / "assets"
    if src_assets.is_dir():
        for entry in src_assets.iterdir():
            if entry.name in EXCLUDED_ASSET_DIRS:
                continue
            dst = staging_assets / entry.name
            if entry.is_dir():
                shutil.copytree(entry, dst, dirs_exist_ok=True)
            elif entry.is_file():
                shutil.copy2(entry, dst)

    icon_path = ensure_icon_file(staging_assets)
    return staging_assets, icon_path


def build_pyinstaller_command(staging_assets: Path, icon_path: Path) -> List[str]:
    """Monta os argumentos completos para o PyInstaller."""
    sep = ";" if os.name == "nt" else ":"

    data_mappings = [
        (ROOT_DIR / "static", "static"),
        (staging_assets, "assets"),
        (ROOT_DIR / "locales", "locales"),
        (ROOT_DIR / "static_data", "static_data"),
        (ROOT_DIR / "traducoes.json", "."),
    ]

    hidden_imports = [
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "pystray._win32",
        "PIL._tkinter_finder",
        "curl_cffi",
        "curl_cffi.requests",
        "genshin",
        "rapidfuzz",
        "bs4",
        "httpx",
        "playwright",
        "pydantic",
        "packaging",
        "version",
        "updater",
    ]

    collect_submodules = ["routers", "services", "schemas", "core", "scrapers"]
    collect_data = ["curl_cffi", "genshin"]

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--noconsole",
        "--name",
        APP_NAME,
        "--icon",
        str(icon_path),
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR / "pyinstaller"),
    ]

    for src, dst in data_mappings:
        if src.exists():
            cmd.extend(["--add-data", f"{src}{sep}{dst}"])

    for mod in hidden_imports:
        cmd.extend(["--hidden-import", mod])

    for pkg in collect_submodules:
        cmd.extend(["--collect-submodules", pkg])

    for pkg in collect_data:
        cmd.extend(["--collect-data", pkg])

    cmd.append(str(ROOT_DIR / "main.py"))
    return cmd


def package_zip(exe_path: Path, output_zip: Path) -> Path:
    """Empacota o executável final e .env.example em um arquivo ZIP limpo."""
    if not exe_path.is_file():
        raise FileNotFoundError(f"Executável não encontrado para compactação: {exe_path}")

    if output_zip.exists():
        output_zip.unlink()

    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(exe_path, arcname=exe_path.name)
        env_example = ROOT_DIR / ".env.example"
        if env_example.is_file():
            zf.write(env_example, arcname=".env.example")

    return output_zip


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    print("[BUILD] Verificando Web Components offline do Sakuga VFX...")
    verify_sakuga_vendor_assets()
    print("[BUILD] Preparando assets estáticos e ícone...")
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    staging_assets, icon_path = prepare_staging_assets()
    cmd = build_pyinstaller_command(staging_assets, icon_path)

    print("[BUILD] Executando PyInstaller (--onefile --noconsole)...")
    result = subprocess.run(cmd, cwd=str(ROOT_DIR), check=False)
    if result.returncode != 0:
        print(f"[ERROR] PyInstaller falhou com código {result.returncode}.")
        return result.returncode

    if SPEC_PATH.is_file():
        try:
            SPEC_PATH.unlink()
        except OSError:
            pass

    exe_path = DIST_DIR / EXE_NAME
    zip_path = DIST_DIR / ZIP_NAME

    print(f"[BUILD] Empacotando artefato ZIP em {zip_path}...")
    package_zip(exe_path, zip_path)

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    digest = file_sha256(zip_path)
    print(f"[SUCCESS] Build concluído: {zip_path} ({size_mb:.2f} MB)")
    print(f"[SUCCESS] SHA256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
