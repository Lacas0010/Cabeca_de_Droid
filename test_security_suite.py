"""
Suite de Testes Automatizados para os 7 Pilares de Segurança do Cabeça de Droid
"""
import os
import sys
import json
import shutil
import tempfile
import unittest

# Importa módulos sob teste
import security_vault
import log_sanitizer
import database

class TestSecurityVault(unittest.TestCase):
    def test_dpapi_or_kdf_encryption_roundtrip(self):
        sample_data = {
            "ltuid_v2": "123456789",
            "ltoken_v2": "v2_CAESECd0zSAMPLETOKENxyz987654321",
            "cookie_token_v2": "v2_SAMPLE_COOKIE_TOKEN_SECRET",
            "account_id_v2": "123456789"
        }
        test_file = os.path.join(tempfile.gettempdir(), "test_cookies.enc")
        try:
            # Salva encriptado
            security_vault.save_secure_cookies(sample_data, filepath=test_file)
            self.assertTrue(os.path.exists(test_file))
            
            # Verifica que o arquivo no disco NÃO é plaintext json
            with open(test_file, "rb") as f:
                raw_bytes = f.read()
            self.assertNotIn(b"v2_CAESECd0zSAMPLETOKENxyz987654321", raw_bytes)
            
            # Lê de volta decriptado
            loaded = security_vault.load_secure_cookies(filepath=test_file)
            self.assertEqual(loaded.get("ltuid_v2"), "123456789")
            self.assertEqual(loaded.get("ltoken_v2"), "v2_CAESECd0zSAMPLETOKENxyz987654321")
            self.assertEqual(loaded.get("cookie_token_v2"), "v2_SAMPLE_COOKIE_TOKEN_SECRET")
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_migration_legacy_plaintext_cookies(self):
        legacy_file = os.path.join(tempfile.gettempdir(), "test_legacy_cookies.json")
        enc_file = os.path.join(tempfile.gettempdir(), "test_migrated_cookies.enc")
        try:
            with open(legacy_file, "w", encoding="utf-8") as f:
                json.dump({"ltuid_v2": "999888", "ltoken_v2": "v2_LEGACY_TOKEN_TEST"}, f)
            
            # Chama load_secure_cookies apontando para o arquivo legado
            data = security_vault.load_secure_cookies(filepath=enc_file, legacy_file=legacy_file)
            self.assertEqual(data.get("ltuid_v2"), "999888")
            self.assertEqual(data.get("ltoken_v2"), "v2_LEGACY_TOKEN_TEST")
            
            # Verifica que o legado foi deletado e o .enc foi criado
            self.assertFalse(os.path.exists(legacy_file))
            self.assertTrue(os.path.exists(enc_file))
        finally:
            if os.path.exists(legacy_file):
                os.remove(legacy_file)
            if os.path.exists(enc_file):
                os.remove(enc_file)

    def test_token_masking(self):
        cookies = {
            "ltuid_v2": "123456789",
            "ltoken_v2": "v2_CAESECd0zSAMPLETOKENxyz987654321",
            "account_id_v2": "123456789"
        }
        res = security_vault.get_masked_cookies_preview(cookies)
        preview_str = res["preview"]
        self.assertNotIn("v2_CAESECd0zSAMPLETOKENxyz987654321", preview_str)
        self.assertIn("123***89", preview_str)
        self.assertIn("v2_CA***4321", preview_str)

        groq_key = "gsk_1234567890abcdef1234567890abcdef"
        masked_groq = security_vault.mask_secret_string(groq_key, show_prefix=4, show_suffix=4)
        self.assertNotIn("abcdef1234567890", masked_groq)
        self.assertTrue(masked_groq.startswith("gsk_"))

    def test_pin_hashing_and_verification(self):
        pin = "123456"
        pin_hash, salt = security_vault.hash_security_pin(pin)
        self.assertTrue(security_vault.verify_security_pin(pin, salt, pin_hash))
        self.assertFalse(security_vault.verify_security_pin("000000", salt, pin_hash))

class TestLogSanitizer(unittest.TestCase):
    def test_redaction(self):
        dirty_log = "Error syncing with ltoken_v2=v2_SECRET_ABCDEF_1234567890 and ltuid_v2=987654321. Groq key: gsk_abcdef1234567890xyz"
        clean_log = log_sanitizer.sanitize_log(dirty_log)
        self.assertNotIn("v2_SECRET_ABCDEF_1234567890", clean_log)
        self.assertNotIn("gsk_abcdef1234567890xyz", clean_log)
        self.assertIn("ltoken_v2=***[LTOKEN_REDACTED]***", clean_log)
        self.assertIn("gsk_***[API_KEY_REDACTED]***", clean_log)

class TestDatabaseSecuritySettings(unittest.TestCase):
    def test_pin_and_lan_db_flow(self):
        database.init_db()
        # PIN
        database.set_security_pin("8888")
        self.assertTrue(database.verify_security_pin_attempt("8888"))
        self.assertFalse(database.verify_security_pin_attempt("1111"))
        
        database.disable_security_pin()
        settings = database.get_security_settings()
        self.assertFalse(settings["pin_enabled"])

        # LAN
        database.set_lan_access(True)
        self.assertTrue(database.is_lan_access_allowed())
        database.set_lan_access(False)
        self.assertFalse(database.is_lan_access_allowed())

class TestServerSecurityEndpoints(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient
        from server import app
        self.client = TestClient(app)

    def test_security_status_endpoint(self):
        response = self.client.get("/api/security/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("storage_backend", data)
        self.assertIn("dpapi_available", data)
        self.assertIn("pin_enabled", data)
        self.assertIn("allow_lan_access", data)

    def test_config_never_returns_raw_cookies(self):
        response = self.client.get("/api/config")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # cookies_raw deve ser sempre vazio ou string vazia
        self.assertEqual(data.get("cookies_raw"), "")
        self.assertIn("cookies_preview", data)

    def test_pin_set_verify_disable_api_flow(self):
        # Configura PIN 9999
        res = self.client.post("/api/security/pin/set", json={"pin": "9999"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get("status"), "ok")

        # Verifica PIN errado
        bad_res = self.client.post("/api/security/pin/verify", json={"pin": "0000"})
        self.assertEqual(bad_res.status_code, 401)

        # Testa middleware de bloqueio (423 Locked) em rotas protegidas
        locked_client = self.client.__class__(self.client.app) # cliente sem cookies de sessão
        locked_res = locked_client.get("/api/overview")
        self.assertEqual(locked_res.status_code, 423)

        # Verifica PIN correto com o cliente bloqueado e recebe cookie de sessão
        ok_res = locked_client.post("/api/security/pin/verify", json={"pin": "9999"})
        self.assertEqual(ok_res.status_code, 200)
        self.assertEqual(ok_res.json().get("status"), "ok")

        # Rota agora deve responder 200
        unlocked_res = locked_client.get("/api/overview")
        self.assertEqual(unlocked_res.status_code, 200)

        # Desativa PIN
        dis_res = locked_client.post("/api/security/pin/disable", json={})
        self.assertEqual(dis_res.status_code, 200)

        # Com PIN desativado, novo cliente sem sessão acessa normalmente
        anon_client = self.client.__class__(self.client.app)
    def test_lan_access_env_override(self):
        # Testa se ALLOW_LAN=1 sobrepõe o banco e permite conexões externas
        old_val = os.environ.get("ALLOW_LAN")
        try:
            os.environ["ALLOW_LAN"] = "1"
            self.assertTrue(database.is_lan_access_allowed())
            os.environ["ALLOW_LAN"] = "0"
            os.environ.pop("ALLOW_LAN", None)
        finally:
            if old_val is not None:
                os.environ["ALLOW_LAN"] = old_val
            else:
                os.environ.pop("ALLOW_LAN", None)

if __name__ == "__main__":
    unittest.main()
