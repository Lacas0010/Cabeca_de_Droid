import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
import shutil
import tempfile
from unittest.mock import patch
from static_data_manager import static_data_manager
from meta_comparator import resolve_character_canonical_slug, find_best_guide_file, parse_meta_target
from services.ai_build_generator import AIBuildGenerator, sanitize_stat_name


class TestDynamicDataAndFuzzySuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Garante que os manifestos estejam carregados
        static_data_manager.load_all()

    def test_01_dynamic_upstream_sync(self):
        """Verifica se a sincronização upstream do HSR, Genshin e ZZZ funciona com fallback offline isolado."""
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("static_data_manager.requests.get", side_effect=OSError("offline test")),
            patch("scrapers.scraper_genshin.PrydwenGenshinScraper.get_character_list", return_value=[]),
            patch("scrapers.scraper_zzz.PrydwenZZZScraper.get_agent_list", return_value=[]),
            patch("scrapers.endgame_icons_scraper.sync_endgame_icons", return_value={}),
            patch("scrapers.role_icons_scraper.sync_role_icons", return_value={}),
            patch("scrapers.resource_icons_scraper.sync_resource_icons", return_value={}),
            patch("scrapers.equipment_effects_scraper.sync_equipment_effects", return_value={}),
            patch.object(static_data_manager, "_get_file_path", side_effect=lambda k: os.path.join(tmpdir, f"{k}.json")),
        ):
            results = static_data_manager.sync_upstream_data()
        self.assertIn("hsr", results)
        self.assertIn("genshin", results)
        self.assertIn("zzz", results)

        # Garante que as contagens de personagens são superiores a zero
        self.assertGreater(results["hsr"].get("character_count", 0), 20)
        self.assertGreater(results["genshin"].get("character_count", 0), 30)
        self.assertGreater(results["zzz"].get("character_count", 0), 10)

    def test_02_fuzzy_matching_and_name_resolution(self):
        """Testa o motor de Fuzzy Matching para resolver nomes com grafias variadas, inversões e apelidos."""
        # 1. Genshin Impact
        self.assertEqual(resolve_character_canonical_slug("genshin", "Raiden Shogun"), "raiden_shogun")
        self.assertIn(resolve_character_canonical_slug("genshin", "Kazuha Kaedehara"), ["kazuha", "kaedehara_kazuha"])
        self.assertEqual(resolve_character_canonical_slug("genshin", "Furina"), "furina")

        # 2. Honkai: Star Rail
        dhil_slug = resolve_character_canonical_slug("hsr", "Dan Heng • Imbibitor Lunae")
        self.assertIn(dhil_slug, ["dan_heng_imbibitor_lunae", "dan_heng_•_imbibitor_lunae"])
        self.assertEqual(resolve_character_canonical_slug("hsr", "Firefly"), "firefly")
        self.assertEqual(resolve_character_canonical_slug("hsr", "Acheron"), "acheron")
        self.assertEqual(resolve_character_canonical_slug("hsr", "Sunday"), "sunday")

    def test_03_hoyolab_numeric_id_lookup(self):
        """Testa a resolução direta de IDs numéricos oficiais da HoYoverse."""
        # Genshin: Ayaka = 10000002
        ayaka_slug = resolve_character_canonical_slug("genshin", "10000002")
        self.assertIn(ayaka_slug, ["kamisato_ayaka", "ayaka"])

        # HSR: Blade = 1205
        blade_slug = resolve_character_canonical_slug("hsr", "1205")
        self.assertIn(blade_slug, ["blade", "1205"])

    def test_04_day1_ai_build_generator(self):
        """Testa a geração automática de guias Day-1 isolada em tempfile.TemporaryDirectory()."""
        import tempfile

        test_slug = "personagem_unit_test_day1"
        test_game = "genshin"

        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch("services.ai_build_generator.BASE_DIR", tmpdir),
                patch("build_calculator.generate_meta_json_from_markdown"),
            ):
                generated_path = AIBuildGenerator.get_or_generate_guide(test_game, test_slug, "Pyro")
                self.assertIsNotNone(generated_path)
                self.assertTrue(os.path.exists(generated_path))
                self.assertTrue(os.path.abspath(generated_path).startswith(os.path.abspath(tmpdir)))

                with open(generated_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.assertIn("Guia de Build", content)
                    self.assertIn("Atributos Recomendados", content)
                    self.assertIn("ai_preliminary", content)

                self.assertTrue(AIBuildGenerator.is_ai_preliminary_guide(generated_path))

    def test_05_meta_comparator_day1_integration(self):
        """Testa se o comparador de meta invoca o gerador Day-1 isolado em diretório temporário."""
        import tempfile

        test_char = "novo_agente_misterioso_day1"
        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch("services.ai_build_generator.BASE_DIR", tmpdir),
                patch("build_calculator.generate_meta_json_from_markdown"),
            ):
                target = parse_meta_target("zzz", test_char, "Electric")
                self.assertIsNotNone(target)
                self.assertIn("weapons", target)
                self.assertIn("sets", target)
                self.assertTrue(os.path.exists(os.path.join(tmpdir, "zzz", "guias", f"{test_char}.md")))

    def test_06_short_name_collision_guard(self):
        """Garante que nomes curtos (<= 4 letras) não sofram falsos positivos por Levenshtein."""
        # Seth em ZZZ deve resolver para seth (Seth Lowell)
        self.assertEqual(resolve_character_canonical_slug("zzz", "Seth"), "seth")
        # Seth em Genshin NÃO deve colidir com Sethos
        self.assertNotEqual(resolve_character_canonical_slug("genshin", "Seth"), "sethos")
        # Sethos em Genshin deve resolver para sethos
        self.assertEqual(resolve_character_canonical_slug("genshin", "Sethos"), "sethos")
        # Anby em ZZZ deve resolver para anby
        self.assertEqual(resolve_character_canonical_slug("zzz", "Anby"), "anby")

    def test_07_stat_sanitization_pipeline(self):
        """Valida o pipeline de normalização e sanitização de atributos contra termos informais."""
        self.assertEqual(sanitize_stat_name("crit rate"), "Taxa Crítica")
        self.assertEqual(sanitize_stat_name("CRIT Rate%"), "Taxa Crítica")
        self.assertEqual(sanitize_stat_name("crit dmg"), "Dano Crítico")
        self.assertEqual(sanitize_stat_name("energy recharge"), "Recarga de Energia")
        self.assertEqual(sanitize_stat_name("pyro dmg bonus"), "Bônus de Dano Pyro")
        self.assertEqual(sanitize_stat_name("pen ratio"), "Taxa de PEN")

    def test_08_multi_element_traveler_and_trailblazer(self):
        """Testa a resolução de slugs distintos para todas as variantes do Viajante e Desbravador."""
        self.assertEqual(resolve_character_canonical_slug("genshin", "Viajante", element="Anemo"), "traveler_anemo")
        self.assertEqual(resolve_character_canonical_slug("genshin", "Viajante", element="Dendro"), "traveler_dendro")
        self.assertEqual(resolve_character_canonical_slug("genshin", "Traveler", element="Hydro"), "traveler_hydro")
        self.assertEqual(resolve_character_canonical_slug("genshin", "Viajante", element="Pyro"), "traveler_pyro")

        self.assertEqual(
            resolve_character_canonical_slug("hsr", "Desbravador", element="Harmony"), "trailblazer_•_harmony"
        )
        self.assertEqual(
            resolve_character_canonical_slug("hsr", "Trailblazer", element="Preservation"), "trailblazer_•_preservation"
        )
        self.assertEqual(
            resolve_character_canonical_slug("hsr", "Desbravador", element="Ice"), "trailblazer_•_remembrance"
        )
        self.assertEqual(
            resolve_character_canonical_slug("hsr", "Desbravador", element="Lightning"), "trailblazer_•_elation"
        )


if __name__ == "__main__":
    unittest.main()
