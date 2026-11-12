"""
Script de Otimização e Conversão de Imagens do Cabeça de Droid
Redimensiona ativos locais para as resoluções adequadas de renderização em tela,
gerando pares WebP modernos e reduzindo o peso total em mais de 90%.
"""
import os
import sys
from PIL import Image

def optimize_banners():
    print("--- 1. OTIMIZANDO BANNERS ---")
    banners = [
        ("assets/hsr_banner.png", 1440),
        ("assets/genshin_banner.png", 1440),
        ("assets/zzz_banner.png", 1440),
        ("assets/config_banner.png", 720),
    ]
    for rel_path, max_w in banners:
        if not os.path.exists(rel_path):
            continue
        orig_sz = os.path.getsize(rel_path) / 1024
        webp_path = os.path.splitext(rel_path)[0] + ".webp"
        with Image.open(rel_path) as img:
            w, h = img.size
            if w > max_w:
                ratio = max_w / w
                new_size = (int(w * ratio), int(h * ratio))
                res = img.resize(new_size, Image.Resampling.LANCZOS)
            else:
                res = img.copy()
            # Salva versão WebP
            res.save(webp_path, "WEBP", quality=82, method=6)
            # Salva versão PNG otimizada para fallback
            res.save(rel_path, "PNG", optimize=True)
            
        webp_sz = os.path.getsize(webp_path) / 1024
        png_sz = os.path.getsize(rel_path) / 1024
        print(f"  {rel_path}: {orig_sz:.1f} KB -> PNG: {png_sz:.1f} KB | WebP: {webp_sz:.1f} KB")

def optimize_icons():
    print("\n--- 2. OTIMIZANDO ÍCONES E LOGO ---")
    # Logo
    if os.path.exists("assets/logo.ico"):
        with Image.open("assets/logo.ico") as img:
            res = img.resize((96, 96), Image.Resampling.LANCZOS)
            res.save("assets/logo.webp", "WEBP", quality=90)
            res.save("assets/logo.png", "PNG", optimize=True)
        print("  assets/logo.webp e assets/logo.png gerados (96x96)")

    icons = [
        ("assets/chat_icon.png", 96),
        ("assets/config_icon.png", 96),
        ("assets/genshin_icon.png", 96),
        ("assets/zzz_icon.png", 96),
        ("assets/home_icon.png", 64),
    ]
    for rel_path, max_dim in icons:
        if not os.path.exists(rel_path):
            continue
        orig_sz = os.path.getsize(rel_path) / 1024
        webp_path = os.path.splitext(rel_path)[0] + ".webp"
        with Image.open(rel_path) as img:
            res = img.resize((max_dim, max_dim), Image.Resampling.LANCZOS)
            res.save(webp_path, "WEBP", quality=85)
            res.save(rel_path, "PNG", optimize=True)
        webp_sz = os.path.getsize(webp_path) / 1024
        png_sz = os.path.getsize(rel_path) / 1024
        print(f"  {rel_path}: {orig_sz:.1f} KB -> PNG: {png_sz:.1f} KB | WebP: {webp_sz:.1f} KB")

def optimize_shards():
    print("\n--- 3. OTIMIZANDO SHARDS DE EIDOLONS ---")
    shards_dir = os.path.join("assets", "shards", "hsr")
    if not os.path.exists(shards_dir):
        print("  Diretório de shards não encontrado.")
        return
        
    files = [f for f in os.listdir(shards_dir) if f.lower().endswith(".png")]
    total = len(files)
    print(f"  Encontrados {total} arquivos para otimizar...")
    
    total_orig = 0
    total_new = 0
    
    for idx, fname in enumerate(files):
        p = os.path.join(shards_dir, fname)
        orig_sz = os.path.getsize(p)
        total_orig += orig_sz
        
        webp_path = os.path.splitext(p)[0] + ".webp"
        try:
            with Image.open(p) as img:
                w, h = img.size
                if w > 128 or h > 128:
                    res = img.resize((128, 128), Image.Resampling.LANCZOS)
                    res.save(p, "PNG", optimize=True)
                else:
                    res = img.copy()
                res.save(webp_path, "WEBP", quality=85)
        except Exception as e:
            print(f"  Erro ao processar {fname}: {e}")
            continue
            
        new_sz = os.path.getsize(p)
        total_new += new_sz
        
        if (idx + 1) % 200 == 0 or (idx + 1) == total:
            print(f"  Progresso: {idx + 1}/{total} ({(idx + 1) / total * 100:.1f}%)")
            
    print(f"  Total Shards: {total_orig / (1024*1024):.1f} MB -> {total_new / (1024*1024):.1f} MB (economia de {(total_orig - total_new)/(1024*1024):.1f} MB)")

if __name__ == "__main__":
    optimize_banners()
    optimize_icons()
    optimize_shards()
    print("\n[SUCESSO] Otimização concluída!")
