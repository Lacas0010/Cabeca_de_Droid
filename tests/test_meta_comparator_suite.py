import unittest
import os
import json
from fastapi.testclient import TestClient
from server import app, parse_character_build_data, parse_meta_target
import database

class TestMetaComparatorSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_parse_character_build_data_hsr(self):
        """Valida a extração estruturada de dados da build do jogador para HSR."""
        roster = database.get_roster_data("hsr")
        if not roster:
            self.skipTest("Sem roster de HSR no banco")
        char_name = roster[0].get("name")
        build_data = parse_character_build_data("hsr", char_name)
        
        self.assertEqual(build_data["name"], char_name)
        self.assertIn("weapon", build_data)
        self.assertIn("pieces", build_data)
        self.assertIn("stats", build_data)
        self.assertIsInstance(build_data["pieces"], list)
        self.assertIsInstance(build_data["stats"], dict)
        if len(build_data["pieces"]) > 0:
            p = build_data["pieces"][0]
            self.assertIn("slot", p)
            self.assertIn("main", p)

    def test_02_parse_character_build_data_genshin(self):
        """Valida a extração estruturada de dados da build do jogador para Genshin."""
        roster = database.get_roster_data("genshin")
        if not roster:
            self.skipTest("Sem roster de Genshin no banco")
        char_name = roster[0].get("name")
        build_data = parse_character_build_data("genshin", char_name)
        
        self.assertEqual(build_data["name"], char_name)
        self.assertIn("weapon", build_data)
        self.assertIn("pieces", build_data)
        self.assertIn("stats", build_data)

    def test_03_parse_character_build_data_zzz(self):
        """Valida a extração estruturada de dados da build do jogador para ZZZ."""
        roster = database.get_roster_data("zzz")
        if not roster:
            self.skipTest("Sem roster de ZZZ no banco")
        char_name = roster[0].get("name")
        build_data = parse_character_build_data("zzz", char_name)
        
        self.assertEqual(build_data["name"], char_name)
        self.assertIn("weapon", build_data)
        self.assertIn("pieces", build_data)
        self.assertIn("stats", build_data)

    def test_04_parse_meta_target_clean_hsr(self):
        """Valida que o meta_target de HSR extrai armas e sets limpos sem justificativas."""
        meta = parse_meta_target("hsr", "Acheron")
        self.assertIn("weapon", meta)
        self.assertIn("weapons", meta)
        self.assertIn("sets", meta)
        self.assertIn("stats", meta)
        self.assertIn("endgame_stats", meta)
        
        # Garante que as armas extraídas não contêm justificativas
        for w in meta["weapons"]:
            self.assertFalse(w.lower().startswith("justificativa"))
            self.assertFalse(w.lower().startswith("review"))
            self.assertLess(len(w), 80)
            
        # Garante que os sets extraídos não contêm justificativas
        for s in meta["all_sets"]:
            self.assertFalse(s.lower().startswith("justificativa"))
            self.assertFalse(s.lower().startswith("disk"))

    def test_05_parse_meta_target_clean_genshin(self):
        """Valida que o meta_target de Genshin extrai slots limpos (Areia, Copo, Tiara)."""
        meta = parse_meta_target("genshin", "Odette")
        self.assertIn("stats", meta)
        self.assertIn("endgame_stats", meta)
        
        # Garante que os slots foram mapeados
        for slot in ["Areia", "Copo", "Tiara"]:
            if slot in meta["stats"]:
                val = meta["stats"][slot]
                self.assertNotIn("():", val)
                self.assertLess(len(val), 100)

    def test_06_parse_meta_target_clean_zzz(self):
        """Valida que o meta_target de ZZZ extrai discos 4, 5, 6 e endgame stats."""
        meta = parse_meta_target("zzz", "Alice")
        self.assertIn("stats", meta)
        self.assertIn("endgame_stats", meta)
        self.assertTrue(any(d in meta["stats"] for d in ["Disco 4", "Disco 5", "Disco 6"]))

    def test_07_api_compare_endpoint_all_games(self):
        """Valida a resposta do endpoint HTTP /api/compare/{game_id}/{char_name}."""
        test_cases = [
            ("hsr", "Desbravador(a)"),
            ("genshin", "Odette"),
            ("zzz", "Sigrid")
        ]
        for gid, cname in test_cases:
            res = self.client.get(f"/api/compare/{gid}/{cname}")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["game_id"], gid)
            self.assertIn("player_build", data)
            self.assertIn("meta_target", data)
            
            pb = data["player_build"]
            self.assertIn("weapon", pb)
            self.assertIn("sets", pb)
            self.assertIn("stats", pb)
            self.assertIn("pieces", pb)
            
            mt = data["meta_target"]
            self.assertIn("weapon", mt)
            self.assertIn("weapons", mt)
            self.assertIn("sets", mt)
            self.assertIn("stats", mt)
            self.assertIn("endgame_stats", mt)

    def test_08_api_compare_invalid_game(self):
        """Valida que requisição com jogo inválido retorna erro 400."""
        res = self.client.get("/api/compare/invalid_game/some_char")
        self.assertEqual(res.status_code, 400)

    def test_09_archetype_and_character_benchmarks_genshin(self):
        """Valida que personagens de Genshin com arquétipos diferentes recebem metas adequadas."""
        # Hu Tao deve ter meta de Vida e Proficiência, não ATQ genérico
        meta_hutao = parse_meta_target("genshin", "Hu Tao")
        self.assertIn("Vida", meta_hutao["endgame_stats"])
        self.assertIn("Taxa Crítica", meta_hutao["endgame_stats"])
        self.assertEqual(meta_hutao["endgame_stats"]["Vida"], "30.000+")
        
        # Kazuha deve focar em Proficiência Elemental e Recarga
        meta_kazuha = parse_meta_target("genshin", "Kaedehara Kazuha")
        self.assertIn("Proficiência Elemental", meta_kazuha["endgame_stats"])
        self.assertEqual(meta_kazuha["endgame_stats"]["Proficiência Elemental"], "900+")
        
        # Raiden deve focar em Recarga de Energia
        meta_raiden = parse_meta_target("genshin", "Shogun Raiden")
        self.assertIn("Recarga de Energia", meta_raiden["endgame_stats"])
        self.assertEqual(meta_raiden["endgame_stats"]["Recarga de Energia"], "250%+")

    def test_10_archetype_and_character_benchmarks_hsr(self):
        """Valida que personagens de HSR recebem metas reais conforme seu papel (DoT, Quebra, Tanque, DPS)."""
        # Kafka (DoT) deve focar em ATQ, VEL e Acerto de Efeito
        meta_kafka = parse_meta_target("hsr", "Kafka")
        self.assertIn("ATQ", meta_kafka["endgame_stats"])
        self.assertIn("Acerto de Efeito", meta_kafka["endgame_stats"])
        self.assertIn("VEL", meta_kafka["endgame_stats"])
        
        # Firefly (Quebra) deve focar em Efeito de Quebra e VEL
        meta_firefly = parse_meta_target("hsr", "Vaga-lume")
        self.assertIn("Efeito de Quebra", meta_firefly["endgame_stats"])
        self.assertEqual(meta_firefly["endgame_stats"]["Efeito de Quebra"], "250%+")
        
        # Aventurine (Preservação/DEF) deve focar em DEF 4000+
        meta_aventurine = parse_meta_target("hsr", "Aventurine")
        self.assertIn("DEF", meta_aventurine["endgame_stats"])
        self.assertEqual(meta_aventurine["endgame_stats"]["DEF"], "4.000+")

    def test_11_archetype_and_character_benchmarks_zzz(self):
        """Valida que personagens de ZZZ recebem metas reais conforme seu papel (Anomalia, Atordoamento, DPS)."""
        # Jane (Anomalia)
        meta_jane = parse_meta_target("zzz", "Jane Doe")
        self.assertIn("Proficiência de Anomalia", meta_jane["endgame_stats"])
        self.assertEqual(meta_jane["endgame_stats"]["Proficiência de Anomalia"], "420+")
        
        # Caesar (Impacto / Tanque)
        meta_caesar = parse_meta_target("zzz", "Caesar King")
        self.assertIn("Impacto", meta_caesar["endgame_stats"])
        self.assertEqual(meta_caesar["endgame_stats"]["Impacto"], "160+")
        
        # Miyabi (DPS Crítico)
        meta_miyabi = parse_meta_target("zzz", "Hoshimi Miyabi")
        self.assertIn("Taxa CRIT", meta_miyabi["endgame_stats"])
        self.assertEqual(meta_miyabi["endgame_stats"]["Taxa CRIT"], "70%+")

    def test_12_alias_resolution_pt_br(self):
        """Valida que aliases em português encontram o arquivo de guia correto e não caem em branco."""
        # HSR: Vaga-lume deve carregar as armas de firefly.md
        meta_vagalume = parse_meta_target("hsr", "Vaga-lume")
        self.assertTrue(len(meta_vagalume["weapons"]) > 0 or meta_vagalume["weapon"] != "Não informado")
        
        # HSR: Cisne Negro deve carregar as armas de black_swan.md
        meta_cisne = parse_meta_target("hsr", "Cisne Negro")
        self.assertTrue(len(meta_cisne["weapons"]) > 0 or meta_cisne["weapon"] != "Não informado")

        # ZZZ: N.º 11 deve encontrar o guia de soldier_11.md
        meta_soldier = parse_meta_target("zzz", "N.º 11")
        self.assertTrue(len(meta_soldier["weapons"]) > 0 or meta_soldier["weapon"] != "Não informado")

    def test_13_mavuika_weapon_translation_and_no_er(self):
        """Valida que Mavuika tem arma traduzida para Mil Sóis Ardentes, Códice de Obsidiana e não usa Recarga de Energia."""
        meta_mavuika = parse_meta_target("genshin", "Mavuika")
        self.assertEqual(meta_mavuika["weapon"], "Mil Sóis Ardentes")
        self.assertIn("Mil Sóis Ardentes", meta_mavuika["weapons"])
        self.assertEqual(meta_mavuika["sets"][0], "Códice de Obsidiana")
        self.assertNotIn("Recarga de Energia", meta_mavuika["endgame_stats"])
        self.assertIn("Proficiência Elemental", meta_mavuika["endgame_stats"])

    def test_14_skirk_weapon_translation_and_no_er(self):
        """Valida que Skirk tem arma traduzida para Luz Lazúli, Galerias da Sombra da Onda e não usa Recarga de Energia."""
        meta_skirk = parse_meta_target("genshin", "Skirk")
        self.assertEqual(meta_skirk["weapon"], "Luz Lazúli")
        self.assertIn("Luz Lazúli", meta_skirk["weapons"])
        self.assertEqual(meta_skirk["sets"][0], "Galerias da Sombra da Onda")
        self.assertNotIn("Recarga de Energia", meta_skirk["endgame_stats"])

if __name__ == "__main__":
    unittest.main()

