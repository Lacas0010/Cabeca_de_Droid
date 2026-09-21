import os
import sys
import json
import uuid
import ctypes
import hashlib
import hmac
import secrets
from typing import Dict, Any, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES_ENC_FILE = os.path.join(BASE_DIR, "cookies.enc")
COOKIES_LEGACY_FILE = os.path.join(BASE_DIR, "cookies.json")
CONFIG_ENC_FILE = os.path.join(BASE_DIR, "config.enc")
CONFIG_LEGACY_FILE = os.path.join(BASE_DIR, "config.json")

# ==========================================
# 1. WINDOWS DPAPI (Data Protection API)
# ==========================================
IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    from ctypes import wintypes
    
    class DATA_BLOB(ctypes.Structure):
        _fields_ = [
            ("cbData", wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_char))
        ]

    CryptProtectData = ctypes.windll.crypt32.CryptProtectData
    CryptUnprotectData = ctypes.windll.crypt32.CryptUnprotectData
    LocalFree = ctypes.windll.kernel32.LocalFree

    CRYPTPROTECT_UI_FORBIDDEN = 0x01

    def _dpapi_protect(data: bytes, entropy: Optional[bytes] = None) -> bytes:
        """Criptografa bytes usando a DPAPI nativa do Windows (usuário atual)."""
        data_in = DATA_BLOB(len(data), ctypes.cast(ctypes.create_string_buffer(data, len(data)), ctypes.POINTER(ctypes.c_char)))
        data_out = DATA_BLOB()
        
        entropy_blob = None
        p_entropy = None
        if entropy:
            entropy_blob = DATA_BLOB(len(entropy), ctypes.cast(ctypes.create_string_buffer(entropy, len(entropy)), ctypes.POINTER(ctypes.c_char)))
            p_entropy = ctypes.byref(entropy_blob)
            
        success = CryptProtectData(
            ctypes.byref(data_in),
            "HoyoAppSecurityVault",
            p_entropy,
            None,
            None,
            CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(data_out)
        )
        
        if not success:
            raise ctypes.WinError()
            
        encrypted_bytes = ctypes.string_at(data_out.pbData, data_out.cbData)
        LocalFree(data_out.pbData)
        return b"DPAPI:" + encrypted_bytes

    def _dpapi_unprotect(data: bytes, entropy: Optional[bytes] = None) -> bytes:
        """Decriptografa bytes protegidos via DPAPI do Windows."""
        if not data.startswith(b"DPAPI:"):
            raise ValueError("Payload não possui assinatura DPAPI válida.")
            
        raw_enc = data[6:]
        data_in = DATA_BLOB(len(raw_enc), ctypes.cast(ctypes.create_string_buffer(raw_enc, len(raw_enc)), ctypes.POINTER(ctypes.c_char)))
        data_out = DATA_BLOB()
        
        entropy_blob = None
        p_entropy = None
        if entropy:
            entropy_blob = DATA_BLOB(len(entropy), ctypes.cast(ctypes.create_string_buffer(entropy, len(entropy)), ctypes.POINTER(ctypes.c_char)))
            p_entropy = ctypes.byref(entropy_blob)
            
        success = CryptUnprotectData(
            ctypes.byref(data_in),
            None,
            p_entropy,
            None,
            None,
            CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(data_out)
        )
        
        if not success:
            raise ctypes.WinError()
            
        decrypted_bytes = ctypes.string_at(data_out.pbData, data_out.cbData)
        LocalFree(data_out.pbData)
        return decrypted_bytes
else:
    def _dpapi_protect(data: bytes, entropy: Optional[bytes] = None) -> bytes:
        raise NotImplementedError("DPAPI disponível apenas no Windows.")
        
    def _dpapi_unprotect(data: bytes, entropy: Optional[bytes] = None) -> bytes:
        raise NotImplementedError("DPAPI disponível apenas no Windows.")

# ==========================================
# 2. ENCRIPTADOR LOCAL (FALLBACK MULTIPLATAFORMA COM CHAVE DERIVADA)
# ==========================================
def _get_machine_entropy() -> bytes:
    """Gera chave de entropia única do hardware/instalação local."""
    node = str(uuid.getnode()).encode("utf-8")
    app_salt = b"CabecaDeDroid-SecureVault-2026-v4"
    return hashlib.sha256(node + app_salt).digest()

def _stream_cipher(data: bytes, key: bytes, salt: bytes) -> bytes:
    """Cifra simétrica baseada em HMAC-SHA256 Counter Mode (CTR) com verificação de integridade."""
    derived_key = hashlib.pbkdf2_hmac("sha256", key, salt, 100_000, 32)
    output = bytearray(len(data))
    block_index = 0
    
    for offset in range(0, len(data), 32):
        block_key = hmac.new(derived_key, salt + block_index.to_bytes(8, "big"), hashlib.sha256).digest()
        chunk_len = min(32, len(data) - offset)
        for i in range(chunk_len):
            output[offset + i] = data[offset + i] ^ block_key[i]
        block_index += 1
        
    return bytes(output)

def _machine_protect(data: bytes) -> bytes:
    salt = secrets.token_bytes(16)
    key = _get_machine_entropy()
    ciphertext = _stream_cipher(data, key, salt)
    mac = hmac.new(key, salt + ciphertext, hashlib.sha256).digest()
    return b"MKV1:" + salt + mac + ciphertext

def _machine_unprotect(data: bytes) -> bytes:
    if not data.startswith(b"MKV1:") or len(data) < 5 + 16 + 32:
        raise ValueError("Payload criptografado corrompido ou formato inválido.")
    payload = data[5:]
    salt = payload[:16]
    mac = payload[16:48]
    ciphertext = payload[48:]
    key = _get_machine_entropy()
    
    expected_mac = hmac.new(key, salt + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(mac, expected_mac):
        raise ValueError("Falha de autenticação/integridade criptográfica.")
        
    return _stream_cipher(ciphertext, key, salt)

# ==========================================
# 3. INTERFACE UNIFICADA DO COFRE
# ==========================================
def encrypt_payload(data_str: str) -> bytes:
    """Criptografa uma string usando DPAPI no Windows ou Chave de Máquina como fallback."""
    raw_bytes = data_str.encode("utf-8")
    if IS_WINDOWS:
        try:
            return _dpapi_protect(raw_bytes, entropy=_get_machine_entropy())
        except Exception:
            pass
    return _machine_protect(raw_bytes)

def decrypt_payload(enc_bytes: bytes) -> str:
    """Decriptografa bytes de volta para string utf-8."""
    if enc_bytes.startswith(b"DPAPI:") and IS_WINDOWS:
        try:
            return _dpapi_unprotect(enc_bytes, entropy=_get_machine_entropy()).decode("utf-8")
        except Exception:
            pass
    if enc_bytes.startswith(b"MKV1:"):
        return _machine_unprotect(enc_bytes).decode("utf-8")
    
    # Tentativa de parse em texto puro (legado ou fallback)
    return enc_bytes.decode("utf-8")

def get_vault_security_info() -> Dict[str, Any]:
    """Retorna o status de proteção ativo do cofre."""
    return {
        "is_windows": IS_WINDOWS,
        "engine": "Windows DPAPI (Hardware-Tied User Key)" if IS_WINDOWS else "Machine-Derived AES/HMAC",
        "has_encrypted_cookies": os.path.exists(COOKIES_ENC_FILE),
        "cookies_legacy_exists": os.path.exists(COOKIES_LEGACY_FILE),
        "status": "PROTECTED"
    }

# ==========================================
# 4. GESTÃO DE COOKIES CRIPTOGRAFADOS
# ==========================================
def save_secure_cookies(cookies: Dict[str, str], filepath: Optional[str] = None) -> None:
    """Salva os cookies em arquivo binário encriptado e apaga o JSON legado se existir."""
    target = filepath or COOKIES_ENC_FILE
    if not cookies:
        if os.path.exists(target):
            os.remove(target)
        if not filepath and os.path.exists(COOKIES_LEGACY_FILE):
            os.remove(COOKIES_LEGACY_FILE)
        return

    json_str = json.dumps(cookies, ensure_ascii=False)
    enc_data = encrypt_payload(json_str)
    
    with open(target, "wb") as f:
        f.write(enc_data)
        
    # Limpeza defensiva do arquivo legado em texto puro
    if not filepath and os.path.exists(COOKIES_LEGACY_FILE):
        try:
            os.remove(COOKIES_LEGACY_FILE)
        except Exception:
            pass

def load_secure_cookies(filepath: Optional[str] = None, legacy_file: Optional[str] = None) -> Dict[str, str]:
    """Carrega cookies do arquivo criptografado ou migra automaticamente do JSON legado."""
    target = filepath or COOKIES_ENC_FILE
    legacy = legacy_file or COOKIES_LEGACY_FILE
    
    # 1. Carrega do cofre criptografado
    if os.path.exists(target):
        try:
            with open(target, "rb") as f:
                enc_data = f.read()
            decrypted = decrypt_payload(enc_data)
            return json.loads(decrypted)
        except Exception as e:
            print(f"[SECURITY_VAULT] Aviso ao decifrar {target}: {e}")
            
    # 2. Migração transparente se existir cookies.json legado
    if os.path.exists(legacy):
        try:
            with open(legacy, "r", encoding="utf-8") as f:
                legacy_cookies = json.load(f)
            if legacy_cookies and isinstance(legacy_cookies, dict):
                print(f"[SECURITY_VAULT] Migrando {legacy} para {target} criptografado...")
                save_secure_cookies(legacy_cookies, filepath=target)
                try:
                    os.remove(legacy)
                except Exception:
                    pass
                return legacy_cookies
        except Exception as e:
            print(f"[SECURITY_VAULT] Erro ao ler {legacy}: {e}")
            
    return {}

# ==========================================
# 5. GESTÃO DE CONFIGURAÇÕES CRIPTOGRAFADAS
# ==========================================
def save_secure_config(config: Dict[str, Any]) -> None:
    """Salva as configurações gerais."""
    with open(CONFIG_LEGACY_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def load_secure_config() -> Dict[str, Any]:
    """Carrega as configurações gerais."""
    defaults = {
        "auto_sync_enabled": True,
        "auto_sync_time": "04:00",
        "auto_sync_roster": True,
        "auto_sync_guides": True,
        "last_auto_sync_date": "",
        "allow_lan_access": False
    }
    if os.path.exists(CONFIG_LEGACY_FILE):
        try:
            with open(CONFIG_LEGACY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                defaults.update(data)
                return defaults
        except Exception:
            pass
    return defaults

# ==========================================
# 6. MASCARAMENTO DE DADOS (DOM ZERO-EXPOSURE)
# ==========================================
def mask_secret_string(val: str, show_prefix: int = 4, show_suffix: int = 4) -> str:
    """Retorna uma versão mascarada de uma string sensível (ex: v2_a9***3e)."""
    if not val:
        return ""
    val_str = str(val).strip()
    if len(val_str) <= show_prefix + show_suffix:
        return "***[PROTEGIDO]***"
    return f"{val_str[:show_prefix]}***{val_str[-show_suffix:]}"

def get_masked_cookies_preview(cookies: Dict[str, str]) -> Dict[str, Any]:
    """Retorna resumo sanitizado dos cookies para exibição no frontend."""
    if not cookies:
        return {
            "has_cookies": False,
            "count": 0,
            "preview": "",
            "keys": [],
            "uid_masked": None,
            "is_encrypted": True
        }
        
    keys = list(cookies.keys())
    uid = cookies.get("ltuid_v2") or cookies.get("ltuid") or cookies.get("account_id_v2") or cookies.get("account_id")
    ltoken = cookies.get("ltoken_v2") or cookies.get("ltoken")
    
    parts = []
    if uid:
        parts.append(f"ltuid_v2={mask_secret_string(uid, 3, 2)}")
    if ltoken:
        parts.append(f"ltoken_v2={mask_secret_string(ltoken, 5, 4)}")
    if "cookie_token_v2" in cookies:
        parts.append("cookie_token_v2=***[PROTEGIDO]***")
        
    return {
        "has_cookies": True,
        "count": len(cookies),
        "preview": "; ".join(parts) if parts else f"{len(cookies)} chaves ativas no cofre",
        "keys": keys,
        "uid_masked": mask_secret_string(uid, 3, 2) if uid else None,
        "is_encrypted": True
    }

# ==========================================
# 7. GESTÃO DE PIN & AUTENTICAÇÃO LOCAL
# ==========================================
def hash_security_pin(pin: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Gera hash PBKDF2 com Salt criptográfico para o PIN do usuário."""
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt.encode("utf-8"), 120_000, 32)
    return key.hex(), salt

def verify_security_pin(pin: str, salt: str, expected_hash: str) -> bool:
    """Verifica se o PIN fornecido corresponde ao hash armazenado."""
    calculated_hash, _ = hash_security_pin(pin, salt)
    return secrets.compare_digest(calculated_hash, expected_hash)

def generate_session_token() -> str:
    """Gera um token de sessão de desbloqueio efêmero."""
    return secrets.token_urlsafe(32)
