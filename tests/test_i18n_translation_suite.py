import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from server import app
from services.translation_service import traduzir_item
from schemas.config import ConfigSaveRequest


class TestI18nTranslationSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_translation_service_pt_and_en(self):
        """Valida que o translation service suporta tanto tradução para PT quanto preservação/reversão para EN."""
        # Teste PT
        pt_res = traduzir_item("Crit Rate", lang="pt")
        self.assertIn("CRIT", pt_res)

        # Teste EN direto
        en_res = traduzir_item("Crit Rate", lang="en")
        self.assertEqual(en_res, "Crit Rate")

        # Teste com sufixo (4-PC)
        res_suffix = traduzir_item("Musketeer of Wild Wheat (4-PC)", lang="pt")
        self.assertTrue(res_suffix.endswith("(4-PC)"))

    def test_config_schema_language_support(self):
        """Valida que o schema ConfigSaveRequest aceita o campo language."""
        req_pt = ConfigSaveRequest(language="pt")
        self.assertEqual(req_pt.language, "pt")

        req_en = ConfigSaveRequest(language="en")
        self.assertEqual(req_en.language, "en")

    def test_api_config_language_endpoint(self):
        """Valida leitura e persistência do idioma na API /api/config."""
        # Salva idioma 'en'
        post_res = self.client.post("/api/config", json={"language": "en"})
        self.assertEqual(post_res.status_code, 200)

        # Lê configuração e confere idioma
        get_res = self.client.get("/api/config")
        self.assertEqual(get_res.status_code, 200)
        data = get_res.json()
        self.assertIn("language", data)
        self.assertEqual(data["language"], "en")

        # Restaura idioma para 'pt'
        self.client.post("/api/config", json={"language": "pt"})

    def test_frontend_i18n_module_exists(self):
        """Valida a existência e integridade das chaves básicas no módulo i18n.js."""
        i18n_file = os.path.join("static", "js", "modules", "i18n.js")
        self.assertTrue(os.path.exists(i18n_file))

        with open(i18n_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("TRANSLATIONS", content)
        self.assertIn("pt:", content)
        self.assertIn("en:", content)
        self.assertIn("setLanguage", content)
        self.assertIn("t(", content)

    def test_i18n_parity_and_html_coverage(self):
        """Valida paridade estrita de 100% entre chaves PT e EN e cobertura total de tags HTML."""
        import re

        i18n_file = os.path.join("static", "js", "modules", "i18n.js")
        with open(i18n_file, "r", encoding="utf-8") as f:
            code = f.read()

        pt_match = re.search(r'pt:\s*\{(.*?)\n\s*\},?\s*en:\s*\{', code, re.DOTALL)
        en_match = re.search(r'en:\s*\{(.*?)\n\s*\}\s*\};', code, re.DOTALL)
        self.assertIsNotNone(pt_match)
        self.assertIsNotNone(en_match)

        def extract_keys(body):
            keys = set()
            for line in body.splitlines():
                line = line.strip()
                if not line or line.startswith("//"):
                    continue
                m = re.match(r'([a-zA-Z0-9_]+)\s*:', line)
                if m:
                    keys.add(m.group(1))
            return keys

        pt_keys = extract_keys(pt_match.group(1))
        en_keys = extract_keys(en_match.group(1))

        self.assertEqual(pt_keys, en_keys, f"Diferenças entre PT e EN: {pt_keys ^ en_keys}")

        html_file = os.path.join("static", "index.html")
        with open(html_file, "r", encoding="utf-8") as f:
            html = f.read()

        html_keys = set(re.findall(r'data-i18n="([^"]+)"', html))
        html_ph_keys = set(re.findall(r'data-i18n-placeholder="([^"]+)"', html))
        all_html_keys = html_keys | html_ph_keys

        missing_pt = all_html_keys - pt_keys
        missing_en = all_html_keys - en_keys
        self.assertEqual(len(missing_pt), 0, f"Chaves HTML ausentes em PT: {missing_pt}")
        self.assertEqual(len(missing_en), 0, f"Chaves HTML ausentes em EN: {missing_en}")



    @patch("services.endgame_service.database.get_endgame_data")
    def test_endgame_translation_en(self, mock_get_endgame):
        """Valida que get_endgame traduz modos, estágios e métricas quando lang='en'."""
        mock_get_endgame.return_value = {
            "modes": [
                {
                    "name": "Defesa Shiyu (Shiyu Defense)",
                    "stage": "Piso 12 (Câmara 3)",
                    "metric_label": "Rodadas Utilizadas",
                    "teams": [
                        {
                            "name": "Lado 1",
                            "characters": [{"name": "Ellen", "level": 60}],
                            "monsters": [{"name": "Inimigo", "level": 60}]
                        }
                    ]
                }
            ],
            "uid": "100222333"
        }
        res = self.client.get("/api/endgame/zzz?lang=en")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        modes = data["modes"]
        self.assertEqual(len(modes), 1)
        self.assertEqual(modes[0]["name"], "Shiyu Defense")
        self.assertEqual(modes[0]["stage"], "Floor 12 (Chamber 3)")
        self.assertEqual(modes[0]["metric_label"], "Cycles Used")
        self.assertEqual(modes[0]["teams"][0]["name"], "Side 1")
        self.assertEqual(modes[0]["teams"][0]["monsters"][0]["name"], "Enemy")

    @patch("services.team_matcher_service.database.get_roster_data")
    @patch("services.team_matcher_service.database.get_active_uid")
    @patch("services.team_matcher_service.load_team_archetypes")
    def test_team_matcher_translation_en(self, mock_arch, mock_uid, mock_roster):
        """Valida que match_endgame_teams traduz justificativas funcionais e modos para o inglês."""
        mock_uid.return_value = "700111222"
        mock_roster.return_value = [
            {"name": "Silver Wolf", "level": 80, "rarity": 5, "element": "Quantum", "role": "Debuffer"}
        ]
        mock_arch.return_value = [
            {
                "team_name": "Acheron Nihility Blast",
                "game_id": "hsr",
                "mode": "Caos da Memória (MoC)",
                "tier": "T0",
                "members": [
                    {"name": "Jiaoqiu", "role": "Debuffer", "element": "Fire"}
                ]
            }
        ]
        res = self.client.get("/api/endgame/team-match/hsr?lang=en")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("teams", data)
        team = data["teams"][0]
        self.assertEqual(team["mode"], "Memory of Chaos (MoC)")
        subs = team["members"][0]["substitutes"]
        self.assertTrue(len(subs) > 0)
        self.assertIn("Same tactical role", subs[0]["synergy_reason"])
        self.assertIn("battle-ready", subs[0]["synergy_reason"])


if __name__ == "__main__":
    unittest.main()
