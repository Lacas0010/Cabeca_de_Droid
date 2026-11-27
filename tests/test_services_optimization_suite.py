import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import build_calculator
import endgame_extractor
import extractor
import meta_comparator
from calculators.account_strategy import analyze_account_gaps, recommend_relic_crafting
from calculators.gacha_math import simulate_gacha_probabilities
from calculators.stat_breakpoints import calculate_stat_breakpoints
from schemas.simulation import RelicPieceModel, SimulateSwapRequest
from scrapers.scraper_genshin import PrydwenGenshinScraper
from scrapers.scraper_meta import PrydwenMetaScraper
from scrapers.scraper_prydwen import PrydwenScraper
from scrapers.scraper_zzz import PrydwenZZZScraper
from services import endgame_service, gacha_tracker_service, roster_service, team_matcher_service
from services.simulation_service import simulate_relic_swap
from services.translation_service import traduzir_item


class TestServicesOptimizationSuite(unittest.TestCase):
    def test_genshin_master_ids_from_hoyolab_mappings(self):
        """Valida que Neuvillette, Charlotte e Furina resolvem para os IDs corretos (10000087, 10000088, 10000089)."""
        master = build_calculator.fetch_master_id_list("genshin")
        self.assertEqual(master.get("neuvillette"), "10000087")
        self.assertEqual(master.get("charlotte"), "10000088")
        self.assertEqual(master.get("furina"), "10000089")

    def test_calculate_ascension_zero_xp_books_when_at_target(self):
        """Valida xp_books_purple == 0 quando xp_diff <= 0."""
        res = build_calculator.calculate_ascension("genshin", 90, 90)
        self.assertIsNotNone(res)
        self.assertEqual(res["xp_needed"], 0)
        self.assertEqual(res["xp_books_purple"], 0)

    def test_daily_farm_recommendations_summary_and_guards(self):
        """Valida chaves de summary_totals, guarda de rv=None, char_profile=None e chamadas únicas por char."""
        roster = [
            {
                "id": "10000089",
                "name": "Furina",
                "level": 60,
                "overall_grade": "B",
                "overall_score": None,
                "weapon": {"name": "Fleuve Cendre", "level": 60},
                "skills": [{"name": "Skill", "level": 4, "max_level": 10}],
            }
        ]
        mock_sdm = MagicMock()
        mock_sdm.get_daily_farm_schedule.return_value = {"farmable_characters": ["furina"]}
        mock_sdm.get_character_profile.side_effect = KeyError("missing")
        mock_sdm._enrich_character_profile.side_effect = KeyError("missing")
        mock_sdm.get_weapon_profile.return_value = {}

        with patch("static_data_manager.static_data_manager", mock_sdm):
            res = build_calculator.get_daily_farm_recommendations("genshin", roster=roster, day_of_week=1)

        self.assertEqual(len(res["priority_targets"]), 1)
        asc = res["priority_targets"][0]["items_needed"]["ascension"]
        self.assertIsNotNone(asc)
        self.assertEqual(res["summary_totals"]["boss_mats"], asc["boss_items_needed"])
        self.assertGreaterEqual(res["summary_totals"]["currency"], asc["currency_needed"])
        self.assertGreaterEqual(res["summary_totals"]["xp_books"], asc["xp_books_purple"])
        mock_sdm.get_daily_farm_schedule.assert_called_once()
        mock_sdm.get_character_profile.assert_called_once()

    def test_find_trash_relics_uses_substats_priority_and_sub_string(self):
        """Valida que find_trash_relics lê guide['substats_priority'] e relic['sub'] em string."""
        meta_data = {
            "acheron": {
                "main_stats": {"body": ["crit_rate", "crit_dmg"]},
                "substats_priority": ["crit_rate", "crit_dmg", "atk_pct", "spd"],
            }
        }
        relics = [
            {
                "name": "Peça Boa String",
                "slot": "Corpo",
                "main_stat": "DEF (54%)",
                "sub": "Taxa CRIT: 8.5%, Dano CRIT: 16.0%, VEL: 4",
                "character_name": "Acheron",
            },
            {
                "name": "Peça Lixo String",
                "slot": "Corpo",
                "main_stat": "DEF (54%)",
                "sub": "DEF: 40, PV: 120",
                "character_name": "Acheron",
            },
        ]
        result = build_calculator.find_trash_relics("hsr", relics, meta_data)
        self.assertEqual(result["coringa_count"], 1)
        self.assertEqual(result["trash_count"], 1)

    def test_generate_daily_farm_order_hsr_zzz_material_keys(self):
        """Valida uso de calyx_mat/stagnant_shadow_mat (HSR) e chip_type/core_skill_mat (ZZZ)."""
        hsr_roster = [
            {
                "name": "Acheron",
                "level": 60,
                "rarity": 5,
                "skills": [{"name": "Suprema", "level": 4, "max_level": 10}],
                "weapon": {"name": "Cone", "level": 60},
            }
        ]
        zzz_roster = [
            {
                "name": "Miyabi",
                "level": 40,
                "rarity": 5,
                "skills": [{"name": "Especial", "level": 5, "max_level": 12}],
                "weapon": {"name": "Motor", "level": 40},
            }
        ]
        with patch("static_data_manager.static_data_manager.get_character_profile") as mock_prof:
            mock_prof.return_value = {
                "calyx_mat": "Cálice de Rastros da Inexistência",
                "stagnant_shadow_mat": "Sombra Estagnada Elétrica",
                "path": "Nihility",
            }
            order_hsr = build_calculator.generate_daily_farm_order(
                "hsr", roster=hsr_roster, current_energy=240, max_energy=240
            )
            self.assertEqual(order_hsr["tasks"][0]["material_name"], "Cálice de Rastros da Inexistência")
            self.assertTrue(any(t["material_name"] == "Sombra Estagnada Elétrica" for t in order_hsr["tasks"]))
            self.assertLessEqual(mock_prof.call_count, 2)

            mock_prof.reset_mock()
            mock_prof.return_value = {
                "chip_type": "Chip de Anomalia Glacial",
                "core_skill_mat": "Dado de Caos Superior",
                "specialty": "Anomaly",
            }
            order_zzz = build_calculator.generate_daily_farm_order(
                "zzz", roster=zzz_roster, current_energy=240, max_energy=240
            )
            self.assertEqual(order_zzz["tasks"][0]["material_name"], "Chip de Anomalia Glacial")
            self.assertTrue(any(t["material_name"] == "Dado de Caos Superior" for t in order_zzz["tasks"]))
            self.assertLessEqual(mock_prof.call_count, 2)

    def test_gacha_math_zzz_hard_pity_num_sims_guard_and_target_copies(self):
        """Valida hard pity 90 no ZZZ, guarda de num_simulations<=0 e target_rank=None com current_copies=1."""
        res_hard = simulate_gacha_probabilities(
            game_id="zzz",
            current_pity=89,
            is_guaranteed=True,
            pulls_available=1,
            target_rank=0,
            current_rank=-1,
            num_simulations=500,
        )
        self.assertEqual(res_hard["success_rate"], 100.0)

        res_zero = simulate_gacha_probabilities(
            game_id="hsr",
            current_pity=0,
            is_guaranteed=False,
            pulls_available=10,
            num_simulations=0,
        )
        self.assertEqual(res_zero["success_rate"], 0.0)
        self.assertEqual(res_zero["num_simulations"], 0)

        res_add = simulate_gacha_probabilities(
            game_id="genshin",
            current_pity=89,
            is_guaranteed=True,
            pulls_available=1,
            target_copies=1,
            current_copies=1,
            target_rank=None,
            num_simulations=200,
        )
        self.assertEqual(res_add["needed_new_copies"], 1)
        self.assertEqual(res_add["success_rate"], 100.0)

    def test_stat_breakpoints_200_tier_progress(self):
        """Valida prev_val=160.1 para velocidade entre 160.1 e 200.0."""
        res = calculate_stat_breakpoints("hsr", "Sparkle", {"speed": 180.0})
        spd_bp = next(b for b in res["breakpoints"] if "SPD" in b["stat"])
        expected_prog = round(((180.0 - 160.1) / (200.0 - 160.1)) * 100.0, 1)
        self.assertAlmostEqual(spd_bp["tier_progress"], expected_prog, places=1)

    def test_simulate_relic_swap_normalizes_current_stats_keys(self):
        """Valida que aliases como 'spd' e 'Taxa Crítica' são somados ao delta em simulate_relic_swap."""
        req = SimulateSwapRequest(
            game_id="hsr",
            char_name="Acheron",
            target_slot="feet",
            current_relics=[
                RelicPieceModel(slot="feet", name="Old", main_stat="ATK% (43.2%)", sub_stats="VEL: 2")
            ],
            replacement_relic=RelicPieceModel(slot="feet", name="New", main_stat="ATK% (43.2%)", sub_stats="VEL: 6"),
            current_stats={"spd": 132.0, "Taxa Crítica": "70%", "Dano Crítico": 140.0},
        )
        resp = simulate_relic_swap(req)
        # 132.0 + 4.0 = 136.0 SPD -> 10000 / 136.0 = 73.5 AV/turno e tier 134.0 SPD atingido
        self.assertTrue(any("73.5 AV/turno" in f for f in resp.breakpoint_feedback))
        self.assertTrue(any("134.0 SPD" in f for f in resp.breakpoint_feedback))

    def test_account_strategy_space_keys_numeric_guards_and_herta_case(self):
        """Valida matches com espaço (Kaedehara Kazuha, Ruan Mei, Jane Doe), casts seguros e 'herta' lowercase."""
        res_g = recommend_relic_crafting("genshin", [{"name": "Kaedehara Kazuha", "level": "90?", "rarity": "5★", "overall_score": "65%"}])
        self.assertIn("Sombra Verde", res_g["recommendations"][0]["target_set_name"])

        res_h = recommend_relic_crafting("hsr", [{"name": "Ruan Mei", "level": 80, "rarity": 5, "overall_score": "bad"}])
        self.assertNotIn("Set de Ornamentos", res_h["recommendations"][0]["target_set_name"])
        self.assertTrue(len(res_h["recommendations"][0]["target_set_name"]) > 3)
        self.assertIn("Corda", res_h["recommendations"][0]["slot_name"])

        res_z = recommend_relic_crafting("zzz", [{"name": "Jane Doe", "level": 60, "rarity": 5, "overall_score": None}])
        self.assertIn("Metal de Presas", res_z["recommendations"][0]["target_set_name"])

        gaps_h = analyze_account_gaps("hsr", [{"name": "herta", "level": "80", "rarity": "4", "element": "Ice"}])
        gap_ids = [g["id"] for g in gaps_h["critical_gaps"]]
        self.assertNotIn("hsr_no_pure_fiction_core", gap_ids)

    def test_roster_and_team_matcher_cache_invalidation_and_data_path_priority(self):
        """Valida limpeza de _MANIFESTS_CACHE e prioridade de get_data_path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            static_dir = os.path.join(tmpdir, "static_data")
            os.makedirs(static_dir, exist_ok=True)
            with open(os.path.join(static_dir, "hsr_manifest.json"), "w", encoding="utf-8") as f:
                json.dump({"characters": {"custom_hero": {"name": "Custom Hero", "path": "Harmony"}}}, f)

            with (
                patch("services.roster_service.get_data_path", side_effect=lambda rel: os.path.join(tmpdir, rel)),
                patch("services.team_matcher_service.get_data_path", side_effect=lambda rel: os.path.join(tmpdir, rel)),
            ):
                roster_service.invalidate_roster_cache("hsr")
                man_r = roster_service._get_manifest("hsr")
                man_t = team_matcher_service._get_manifest("hsr")
                self.assertIn("custom_hero", man_r)
                self.assertIn("custom_hero", man_t.get("characters", {}))

                roster_service.invalidate_roster_cache("hsr")
                self.assertNotIn("hsr", roster_service._MANIFESTS_CACHE)
                self.assertNotIn("hsr", team_matcher_service._MANIFESTS_CACHE)

    def test_endgame_cache_keyed_by_active_uid(self):
        """Valida que _ENDGAME_CACHE separa entradas por active_uid."""
        import asyncio

        endgame_service.invalidate_endgame_cache()
        with (
            patch("services.endgame_service.database.get_active_uid", side_effect=["uid_1", "uid_2"]),
            patch(
                "services.endgame_service.database.get_endgame_data",
                side_effect=[
                    {"uid": "uid_1", "updated_at": "t1", "modes": [{"name": "Caos da Memória", "teams": []}]},
                    {"uid": "uid_2", "updated_at": "t2", "modes": [{"name": "Caos da Memória", "teams": []}]},
                ],
            ),
            patch("services.endgame_service.get_roster", return_value=[]),
        ):
            r1 = asyncio.run(endgame_service.get_endgame("hsr", "pt"))
            r2 = asyncio.run(endgame_service.get_endgame("hsr", "pt"))
        self.assertEqual(r1["uid"], "uid_1")
        self.assertEqual(r2["uid"], "uid_2")

    def test_static_ranks_non_blocking_by_default_and_writes_to_data_path(self):
        """Valida que get_static_ranks_for_character não faz I/O de rede por padrão e escreve em get_data_path."""
        orig_cache = roster_service._HSR_EIDOLON_CACHE
        roster_service._HSR_EIDOLON_CACHE = {}
        try:
            with patch("services.roster_service.fetch_fandom_shards_for_character") as mock_fetch:
                res = roster_service.get_static_ranks_for_character("hsr", "999999", "Unknown Hero")
                self.assertEqual(res, [])
                mock_fetch.assert_not_called()

            with tempfile.TemporaryDirectory() as tmpdir:
                fake_ranks = [{"pos": 1, "name": "Eidolon 1", "icon": "https://img/1.png", "desc": ""}]
                with (
                    patch("services.roster_service.fetch_fandom_shards_for_character", return_value=fake_ranks),
                    patch("services.roster_service.get_data_path", side_effect=lambda rel: os.path.join(tmpdir, rel)),
                    patch("services.roster_service.get_resource_path", side_effect=lambda rel: os.path.join(tmpdir, "ro_bundle", rel)),
                ):
                    res_net = roster_service.get_static_ranks_for_character(
                        "hsr", "999999", "Unknown Hero", allow_network=True
                    )
                self.assertEqual(len(res_net), 1)
                self.assertTrue(os.path.exists(os.path.join(tmpdir, "static_data", "hsr_eidolons.json")))
                self.assertFalse(os.path.exists(os.path.join(tmpdir, "ro_bundle", "static_data", "hsr_eidolons.json")))
        finally:
            roster_service._HSR_EIDOLON_CACHE = orig_cache

    def test_get_hsr_effective_id_single_db_call_and_get_overview_skips_disk_when_db_active(self):
        """Valida eliminação de chamadas duplicadas ao DB e leituras redundantes em disco em get_overview."""
        with patch("services.roster_service.database.get_roster_data", return_value=[]) as mock_db:
            roster_service.get_hsr_effective_id({"name": "NonExistentXYZ", "id": ""})
            self.assertEqual(mock_db.call_count, 1)

        roster_service.invalidate_roster_cache()
        active_db = {
            g: {"active": True, "uid": "123", "nickname": "Trailblazer", "level": 70, "char_count": 5, "five_stars": 2}
            for g in ("hsr", "genshin", "zzz")
        }
        with (
            patch("services.roster_service.database.get_overview_data", return_value=active_db),
            patch("services.roster_service.os.path.exists", side_effect=AssertionError("should not touch disk")),
        ):
            ov = roster_service.get_overview()
        self.assertEqual(ov["hsr"]["nickname"], "Trailblazer")

    def test_gacha_tracker_exact_standard_match_and_batch_db_icon_lookup(self):
        """Valida match exato em is_standard_5_star e consulta em lote para ícones do SQLite."""
        self.assertTrue(gacha_tracker_service.is_standard_5_star("hsr", "Himeko"))
        self.assertFalse(gacha_tracker_service.is_standard_5_star("hsr", "Himeko Nova"))

        gacha_tracker_service.reload_icons_cache()
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [
            {"name": "CustomChar", "icon": "https://img/c.png", "weapon_name": "CustomWep", "weapon_icon": "https://img/w.png"}
        ]
        mock_conn.cursor.return_value = mock_cur
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = mock_conn
        mock_ctx.__exit__.return_value = False

        with (
            patch("services.gacha_tracker_service.database.get_connection", return_value=mock_ctx) as mock_get_conn,
            patch("services.gacha_tracker_service.database.get_active_uid", return_value="7001"),
            patch(
                "services.gacha_tracker_service.database.get_gacha_pulls_filtered",
                return_value=(
                    [
                        {"id": "1", "time": "2026-01-01", "item_name": "CustomChar", "item_type": "character", "rarity": 5},
                        {"id": "2", "time": "2026-01-01", "item_name": "CustomWep", "item_type": "weapon", "rarity": 5},
                    ],
                    2,
                ),
            ),
        ):
            hist = gacha_tracker_service.get_gacha_pulls_history_detailed("hsr")
        self.assertEqual(mock_get_conn.call_count, 1)
        self.assertEqual(len(hist.pulls), 2)
        self.assertIn("CustomChar", hist.pulls[0].name)

    def test_translation_scraper_extractor_and_meta_comparator_optimizations(self):
        """Valida regexes pré-compilados, preservação PT-BR, slug ZZZ e deduplicação de sanitize_genshin_url."""
        self.assertIn("Recordação", traduzir_item("Remembrance"))
        self.assertEqual(extractor.get_zzz_prydwen_slug("Soldier 0 - Anby"), "soldier-0-anby")
        self.assertIs(endgame_extractor.sanitize_genshin_url, extractor.sanitize_genshin_url)

        self.assertIn("Recordação", PrydwenMetaScraper().translate_to_portuguese("Remembrance"))
        self.assertIn("Taxa Crítica", PrydwenGenshinScraper().translate_to_portuguese("CRIT Rate"))
        self.assertIn("Cone de Luz", PrydwenScraper().translate_to_portuguese("Light Cone"))
        self.assertIn("Cinema (Mindscape)", PrydwenZZZScraper().translate_to_portuguese("Mindscape"))

        with patch(
            "meta_comparator.resolve_character_canonical_slug", wraps=meta_comparator.resolve_character_canonical_slug
        ) as mock_res:
            meta_comparator.parse_meta_target("hsr", "Acheron")
            self.assertEqual(mock_res.call_count, 1)

    def test_extractor_persists_relics_via_save_relics_batch(self):
        """Valida que _persist_character_relics utiliza database.save_relics_batch em lote."""
        import database

        relics = [
            {"name": "Peça 1", "slot": "head", "main": "HP", "sub": "CR: 5%", "icon": ""},
            {"name": "Peça 2", "slot": "hands", "main": "ATK", "sub": "CD: 10%", "icon": ""},
        ]
        with (
            patch.object(database, "save_relics_batch", create=True, return_value=2) as mock_batch,
            patch.object(database, "save_relic") as mock_single,
        ):
            extractor._persist_character_relics(database, "7001", "Acheron", relics)
        mock_batch.assert_called_once_with("7001", "Acheron", relics, clear_existing=True)
        mock_single.assert_not_called()

    def test_master_ids_authoritative_resolution_all_games(self):
        """Valida que IDs oficiais (Natlan/Fontaine, HSR e ZZZ) não sofrem deslocamento por mapeamentos legados."""
        g_master = build_calculator.fetch_master_id_list("genshin")
        self.assertEqual(g_master.get("xilonen"), "10000103")
        self.assertEqual(g_master.get("chasca"), "10000104")
        self.assertEqual(g_master.get("mualani"), "10000102")
        self.assertEqual(g_master.get("kinich"), "10000101")
        self.assertEqual(g_master.get("mavuika"), "10000106")
        self.assertEqual(g_master.get("citlali"), "10000107")
        self.assertEqual(g_master.get("arlecchino"), "10000096")
        self.assertEqual(g_master.get("clorinde"), "10000098")
        self.assertEqual(g_master.get("wanderer"), "10000075")
        self.assertEqual(g_master.get("faruzan"), "10000076")
        self.assertEqual(g_master.get("yaoyao"), "10000077")

        h_master = build_calculator.fetch_master_id_list("hsr")
        self.assertEqual(h_master.get("firefly"), "1310")
        self.assertEqual(h_master.get("argenti"), "1302")
        self.assertEqual(h_master.get("anaxa"), "1405")
        self.assertEqual(h_master.get("tribbie"), "1403")
        self.assertEqual(h_master.get("fugue"), "1225")

        z_master = build_calculator.fetch_master_id_list("zzz")
        self.assertEqual(z_master.get("miyabi"), "1091")
        self.assertEqual(z_master.get("astra_yao"), "1311")
        self.assertEqual(z_master.get("evelyn"), "1321")
        self.assertEqual(z_master.get("ellen"), "1191")
        self.assertEqual(z_master.get("billy"), "1081")

    def test_dmg_percent_maps_to_elemental_dmg_not_crit_dmg(self):
        """Valida que DMG% genérico (ex.: Cálice da Chasca/Varka) mapeia para elemental_dmg e nunca crit_dmg."""
        self.assertEqual(build_calculator.normalize_stat_name("DMG%"), "elemental_dmg")
        self.assertEqual(build_calculator.normalize_stat_name("CRIT DMG%"), "crit_dmg")
        self.assertTrue(build_calculator.is_stat_equivalent("elemental_dmg", "anemo_dmg"))
        self.assertTrue(build_calculator.is_stat_equivalent("pyro_dmg", "elemental_dmg"))
        self.assertFalse(build_calculator.is_stat_equivalent("elemental_dmg", "crit_dmg"))

    def test_generate_genshin_meta_xilonen_chasca_xianyun_and_empty_stub(self):
        """Valida extração de Xilonen, Chasca (DMG% -> elemental_dmg), inferência de Xianyun e filtro de stubs vazios."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                os.makedirs("genshin/guias", exist_ok=True)
                with open("genshin/guias/xilonen.md", "w", encoding="utf-8") as f:
                    f.write(
                        "# Guia de Build - Xilonen\n"
                        "### Atributos Principais (Main Stats)\n"
                        "- **Ampulheta (Sands):** Recarga de Energia / DEF% (Anything)\n"
                        "- **Cálice (Goblet):** DEF% (Anything)\n"
                        "- **Tiara (Circlet):** Bônus de Cura / DEF% / Taxa Crítica (Anything)\n"
                        "### Subatributos Prioritários (Sub-stats)\n"
                        "ER = DEF%\n"
                    )
                with open("genshin/guias/chasca.md", "w", encoding="utf-8") as f:
                    f.write(
                        "# Guia de Build - Chasca\n"
                        "### Atributos Principais (Main Stats)\n"
                        "- **Ampulheta (Sands):** ATK%\n"
                        "- **Cálice (Goblet):** ATK% >= DMG% > Maestria Elemental\n"
                        "- **Tiara (Circlet):** Dano Crítico > Taxa Crítica\n"
                        "### Subatributos Prioritários (Sub-stats)\n"
                        "Taxa Crítica = Dano Crítico > ATK% > EM\n"
                    )
                with open("genshin/guias/xianyun.md", "w", encoding="utf-8") as f:
                    f.write(
                        "# Guia de Build - Xianyun\n"
                        "### Atributos Principais (Main Stats)\n"
                        "- **Ampulheta (Sands):** ATK% / Recarga de Energia\n"
                        "- **Cálice (Goblet):** ATK% / Bônus de Dano Anemo\n"
                        "- **Tiara (Circlet):** ATK% / Taxa Crítica\n"
                    )
                with open("genshin/guias/stub_vazio.md", "w", encoding="utf-8") as f:
                    f.write("# Guia de Build - Stub Vazio\nNenhuma arma listada.\n")

                build_calculator.META_DATA_CACHE.clear()
                build_calculator.generate_meta_json_from_markdown("genshin")
                with open("genshin/meta_data_genshin.json", "r", encoding="utf-8") as mf:
                    meta = json.load(mf)

                self.assertIn("10000103", meta)
                self.assertEqual(meta["10000103"]["main_stats"]["sands"], ["er", "def_pct"])
                self.assertEqual(meta["10000103"]["main_stats"]["goblet"], ["def_pct"])
                self.assertEqual(meta["10000103"]["substats_priority"], ["er", "def_pct"])

                self.assertIn("10000104", meta)
                self.assertEqual(meta["10000104"]["main_stats"]["goblet"], ["atk_pct", "elemental_dmg", "em"])
                self.assertNotIn("crit_dmg", meta["10000104"]["main_stats"]["goblet"])

                self.assertIn("10000093", meta)
                self.assertEqual(meta["10000093"]["substats_priority"], ["atk_pct", "er", "crit_rate"])
                self.assertNotIn("stub_vazio", meta)
            finally:
                os.chdir(orig_cwd)
                build_calculator.META_DATA_CACHE.clear()

    def test_prydwen_genshin_scraper_dedups_and_keeps_primary_build(self):
        """Valida que PrydwenGenshinScraper remove duplicatas entre abas e mantém os stats da build principal."""
        html = """
        <html><body>
          <div class="weapon-rank-table">
            <div class="build-rank-row"><a class="loadout-item"><strong>Peak Patrol Song</strong></a><span class="build-gear-dupes">R1</span></div>
          </div>
          <div class="weapon-rank-table">
            <div class="build-rank-row"><a class="loadout-item"><strong>Peak Patrol Song</strong></a><span class="build-gear-dupes">R1</span></div>
          </div>
          <div class="artifact-rank-table">
            <div class="build-rank-row"><a class="loadout-item"><strong>Scroll of the Hero of Cinder City</strong></a></div>
          </div>
          <div class="artifact-rank-table">
            <div class="build-rank-row"><a class="loadout-item"><strong>Scroll of the Hero of Cinder City</strong></a></div>
          </div>
          <div class="main-stat-row"><div class="main-stat-slot">Sands</div><strong>Energy Recharge / DEF%</strong></div>
          <div class="main-stat-row"><div class="main-stat-slot">Sands</div><strong>ATK%</strong></div>
          <div class="stat-priority-strip" aria-label="ER = DEF%"></div>
          <div class="stat-priority-strip" aria-label="CRIT Rate > ATK%"></div>
        </body></html>
        """
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.raise_for_status = MagicMock()
        with patch("scrapers.scraper_genshin.requests.get", return_value=mock_resp):
            data = PrydwenGenshinScraper().scrape_character_guide("Xilonen", "https://example.test/xilonen")
        self.assertEqual(len(data["weapons"]), 1)
        self.assertEqual(len(data["artifacts"]), 1)
        self.assertEqual(len(data["stats_main"]), 1)
        self.assertEqual(data["stats_main"][0]["value"], "Energy Recharge / DEF%")
        self.assertEqual(data["stats_sub"], "ER = DEF%")

    def test_get_meta_data_auto_repairs_stale_corrupted_json_and_preserves_flex_any(self):
        """Valida auto-reparo de meta_data desatualizado/corrompido, preservação de 'any' flex e 'er' inferido."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                os.makedirs("genshin/guias", exist_ok=True)
                with open("genshin/guias/xilonen.md", "w", encoding="utf-8") as f:
                    f.write(
                        "# Guia de Build - Xilonen\n"
                        "### Atributos Principais (Main Stats)\n"
                        "- **Ampulheta (Sands):** Recarga de Energia / DEF% (Anything)\n"
                        "- **Cálice (Goblet):** DEF% (Anything)\n"
                        "- **Tiara (Circlet):** Bônus de Cura / DEF% / Taxa Crítica (Anything)\n"
                        "### Subatributos Prioritários (Sub-stats)\n"
                        "ER = DEF%\n"
                    )
                with open("genshin/guias/mona.md", "w", encoding="utf-8") as f:
                    f.write(
                        "# Guia de Build - Mona\n"
                        "### Atributos Principais (Main Stats)\n"
                        "- **Ampulheta (Sands):** Recarga de Energia\n"
                        "- **Cálice (Goblet):** Anything\n"
                        "- **Tiara (Circlet):** Taxa Crítica / Anything\n"
                        "### Subatributos Prioritários (Sub-stats)\n"
                        "ER\n"
                    )
                with open("genshin/guias/kamisato_ayaka.md", "w", encoding="utf-8") as f:
                    f.write(
                        "# Guia de Build - Kamisato Ayaka\n"
                        "### Atributos Principais (Main Stats)\n"
                        "- **Ampulheta (Sands):** ATK%\n"
                        "- **Cálice (Goblet):** Bônus de Dano Cryo / ATK%\n"
                        "- **Tiara (Circlet):** Dano Crítico / Taxa Crítica\n"
                    )

                # Simula meta_data_genshin.json corrompido (Xilonen com dados da Chasca / crit_dmg no goblet)
                corrupted = {
                    "10000103": {
                        "name": "Xilonen",
                        "main_stats": {"sands": ["atk_pct"], "goblet": ["atk_pct", "crit_dmg"], "circlet": ["crit_dmg"]},
                        "substats_priority": ["crit_rate", "crit_dmg"],
                        "general_benchmarks": {},
                    }
                }
                with open("genshin/meta_data_genshin.json", "w", encoding="utf-8") as mf:
                    json.dump(corrupted, mf)

                build_calculator.META_DATA_CACHE.clear()
                repaired = build_calculator.get_meta_data("genshin")

                self.assertEqual(repaired["10000103"]["main_stats"]["goblet"], ["def_pct"])
                self.assertEqual(repaired["10000103"]["substats_priority"], ["er", "def_pct"])
                self.assertEqual(repaired["10000041"]["main_stats"]["circlet"], ["crit_rate", "any"])
                self.assertEqual(repaired["10000002"]["substats_priority"], ["crit_rate", "crit_dmg", "atk_pct", "er"])
            finally:
                os.chdir(orig_cwd)
                build_calculator.META_DATA_CACHE.clear()

    def test_prydwen_genshin_get_character_list_extracts_weapon_element_rarity(self):
        """Valida extração dinâmica de weapon, element e rarity nos cards do Prydwen Genshin (ex.: Odette -> Sword)."""
        html = """
        <html><body>
          <a class="pw-card avatar-card rarity-5 element-cryo" href="/genshin-impact/characters/odette">
            <img alt="Odette" src="https://cdn.prydwen.gg/images/genshin-impact/characters/odette_card.webp" />
            <img alt="" src="https://cdn.prydwen.gg/images/genshin-impact/icons/element_cryo.webp" />
            <img alt="" src="https://cdn.prydwen.gg/images/genshin-impact/icons/weapon_sword.webp" />
            <span>Odette</span>
          </a>
        </body></html>
        """
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.raise_for_status = MagicMock()
        with patch("scrapers.scraper_genshin.requests.get", return_value=mock_resp):
            chars = PrydwenGenshinScraper().get_character_list()
        self.assertEqual(len(chars), 1)
        self.assertEqual(chars[0]["name"], "Odette")
        self.assertEqual(chars[0]["weapon"], "Sword")
        self.assertEqual(chars[0]["element"], "Cryo")
        self.assertEqual(chars[0]["rarity"], 5)


if __name__ == "__main__":
    unittest.main()
