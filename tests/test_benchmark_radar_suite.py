import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient

import build_calculator
from calculators.benchmark_radar import (
    build_radar_benchmark_payload,
    canonicalize_benchmark_key,
    deduplicate_endgame_stats,
    parse_benchmark_spec,
    parse_stat_number,
    standardize_main_stat_display,
)
from server import app


class TestBenchmarkRadarSuite(unittest.TestCase):
    """Testes offline da padronização de benchmarks e do Gráfico Radar no #build-inspector."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_parse_stat_number_pt_thousands_vs_decimals(self):
        self.assertEqual(parse_stat_number("3.000+"), 3000.0)
        self.assertEqual(parse_stat_number("35.000+"), 35000.0)
        self.assertEqual(parse_stat_number("70.000+"), 70000.0)
        self.assertEqual(parse_stat_number("1,600+"), 1600.0)
        self.assertEqual(parse_stat_number("2.88+"), 2.88)
        self.assertEqual(parse_stat_number("19.4%"), 19.4)
        self.assertEqual(parse_stat_number("124.44%"), 124.44)
        self.assertEqual(parse_stat_number("1.20"), 1.2)
        self.assertEqual(build_calculator.clean_value("3.000+"), (3000.0, False))
        self.assertEqual(build_calculator.clean_value("2.88+"), (2.88, False))

    def test_02_canonicalize_and_deduplicate_filters_bogus_keys(self):
        self.assertEqual(canonicalize_benchmark_key("phainon", "hsr"), "")
        self.assertEqual(canonicalize_benchmark_key("sunday", "hsr"), "")
        self.assertEqual(canonicalize_benchmark_key("bronya", "hsr"), "")
        self.assertEqual(canonicalize_benchmark_key("effect hit rating", "hsr"), "ehr")
        self.assertEqual(canonicalize_benchmark_key("energy regeneration", "hsr"), "err")
        self.assertEqual(canonicalize_benchmark_key("Impactoo", "zzz"), "impact")

        raw = {
            "ATQ": "3.500+",
            "Taxa Crítica": "70%+",
            "Taxa CRIT": "70%+",
            "Dano Crítico": "160%+",
            "Dano CRIT": "160%+",
            "hp_flat": "3000+",
            "phainon": "136 SPD",
            "sunday": "135 SPD",
        }
        cleaned = deduplicate_endgame_stats(raw, game_id="hsr")
        self.assertEqual(list(cleaned.keys()), ["ATQ", "Taxa Crítica", "Dano Crítico", "Vida"])
        self.assertNotIn("phainon", cleaned)
        self.assertNotIn("sunday", cleaned)

    def test_03_standardize_main_stat_anything_cases(self):
        self.assertEqual(standardize_main_stat_display("Anything", "pt"), "Qualquer (Flex)")
        self.assertEqual(standardize_main_stat_display("Anything", "en"), "Any (Flex)")
        self.assertEqual(standardize_main_stat_display("PV% / Anything", "pt"), "PV% / Qualquer (Flex)")
        self.assertEqual(standardize_main_stat_display("DEF% (Anything)", "pt"), "DEF% / Qualquer (Flex)")
        self.assertEqual(
            standardize_main_stat_display("Bônus de Cura / DEF% / Taxa Crítica (Anything)", "pt"),
            "Bônus de Cura / DEF% / Taxa Crítica / Qualquer (Flex)",
        )

    def test_04_special_benchmark_expressions_all_games(self):
        # Cipher: dual in-combat / out-of-combat -> usa 50% fora de combate
        spec_cipher = parse_benchmark_spec("crit_rate", "100% (In Combat) / 50% (Outside of Combat)", "hsr")
        self.assertEqual(spec_cipher["target_min"], 50.0)
        self.assertFalse(spec_cipher["is_in_combat"])
        self.assertIn("pre_combat", spec_cipher["tags"])

        # Evernight: before passive
        spec_ever = parse_benchmark_spec("crit_rate", "65% before Noite Eterna passive (100% with Noite Eterna passive)", "hsr")
        self.assertEqual(spec_ever["target_min"], 65.0)
        self.assertFalse(spec_ever["is_in_combat"])

        # Aventurine Waveflair: números apenas entre parênteses
        spec_wave = parse_benchmark_spec("spd", "As high as possible ( 160-200 )", "hsr")
        self.assertEqual(spec_wave["target_min"], 160.0)
        self.assertEqual(spec_wave["target_ideal"], 200.0)

        # Yukong: relativo puro (nunca pode parsear '1' de '1-2 Speed slower')
        spec_yukong = parse_benchmark_spec("spd", "1-2 Speed slower than sustain", "hsr")
        self.assertTrue(spec_yukong["is_flexible"])
        self.assertIsNone(spec_yukong["target_min"])
        self.assertEqual(spec_yukong["mode"], "relative")

        # Bronya: relativo + fallback 160+
        spec_bronya = parse_benchmark_spec("spd", "1-2 Speed slower than carry / 160+ (0 Speed Carry)", "hsr")
        self.assertEqual(spec_bronya["target_min"], 160.0)
        self.assertIn("relative", spec_bronya["tags"])

        # Pela/Tingyun: tier (Recommended)
        spec_pela = parse_benchmark_spec("spd", "134 / 143 (Recommended) / 160+", "hsr")
        self.assertEqual(spec_pela["target_min"], 143.0)
        self.assertEqual(spec_pela["target_ideal"], 160.0)

        # Mortenax Blade: opcional 0% or 40-67%
        spec_opt = parse_benchmark_spec("ehr", "0% or 40-67%", "hsr")
        self.assertEqual(spec_opt["target_min"], 40.0)
        self.assertEqual(spec_opt["target_ideal"], 67.0)
        self.assertTrue(spec_opt["is_optional"])

        # Ashveil ER: Base (flexível)
        spec_base = parse_benchmark_spec("err", "Base", "hsr")
        self.assertTrue(spec_base["is_flexible"])
        self.assertIsNone(spec_base["target_min"])

    def test_05_evanescia_radar_payload_and_special_cases(self):
        player_stats = {
            "PV": "3400",
            "ATQ": "2400",
            "VEL": "115",
            "Taxa CRIT": "65.4%",
            "Dano CRIT": "278.9%",
        }
        endgame = {
            "SPD": "Base SPD or 134",
            "CRIT Rate": "100% (in-combat)",
            "CRIT DMG": "220%+",
        }
        radar = build_radar_benchmark_payload(
            "hsr",
            "Evanescia",
            player_stats,
            endgame,
            main_stats={"Corpo": "Dano CRIT", "Bota": "Qualquer (Flex)", "Esfera": "Qualquer (Flex)"},
        )
        self.assertEqual(radar["summary"]["radar_mode"], "polygon")
        self.assertEqual(len(radar["axes"]), 3)
        self.assertEqual([fn["label_pt"] for fn in radar["flex_notes"]], ["Bota", "Esfera"])

        by_key = {ax["stat_key"]: ax for ax in radar["axes"]}
        # VEL Base (115 >= 90) aceita ramo Base SPD -> ok e plota no anel 100%
        self.assertEqual(by_key["spd"]["status"], "ok")
        self.assertEqual(by_key["spd"]["radar_ratio"], 1.0)
        self.assertIn("base_ok", by_key["spd"]["tags"])
        # CRIT Rate 65.4% vs 100% (in-combat) -> close (amarelo com aviso Em combate)
        self.assertEqual(by_key["crit_rate"]["status"], "close")
        self.assertIn("in_combat", by_key["crit_rate"]["tags"])
        # CRIT DMG 278.9% vs 220%+ -> ok e cap visual 1.2 no radar
        self.assertEqual(by_key["crit_dmg"]["status"], "ok")
        self.assertEqual(by_key["crit_dmg"]["radar_ratio"], 1.2)

    def test_06_hsr_err_and_zzz_er_scale_alignment(self):
        # HSR ERR: 19.4%+ deve comparar contra 119.4% (não contra 19.4%!)
        radar_low = build_radar_benchmark_payload(
            "hsr", "Sunday", {"Regen. Energia": "100.0%"}, {"Taxa de Regen. Energia": "19.4%+"}
        )
        self.assertEqual(radar_low["axes"][0]["target_min"], 119.4)
        self.assertEqual(radar_low["axes"][0]["status"], "low")
        self.assertLess(radar_low["axes"][0]["ratio_pct"], 85.0)

        radar_ok = build_radar_benchmark_payload(
            "hsr", "Sunday", {"Regen. Energia": "119.4%"}, {"Taxa de Regen. Energia": "19.4%+"}
        )
        self.assertEqual(radar_ok["axes"][0]["status"], "ok")

        # ZZZ ER: 25%+ convertido contra base 1.20 -> 1.50
        radar_zzz = build_radar_benchmark_payload(
            "zzz", "Astra Yao", {"ATQ": "3200", "Recup. Energia": "2.16"}, {"ATQ": "3.000+", "Taxa de Regen. Energia": "25%+"}
        )
        by_key = {a["stat_key"]: a for a in radar_zzz["axes"]}
        self.assertEqual(by_key["atk_flat"]["target_min"], 3000.0)
        self.assertEqual(by_key["atk_flat"]["status"], "ok")
        self.assertEqual(by_key["err"]["target_min"], 1.5)
        self.assertEqual(by_key["err"]["status"], "ok")
        self.assertEqual(radar_zzz["summary"]["radar_mode"], "gauges")

    def test_07_api_compare_returns_meta_radar_and_html_contracts(self):
        mock_build = {
            "weapon": "Signature",
            "weapon_clean": "Signature",
            "sets": ["4p Set"],
            "stats": {"VEL": "115", "Taxa CRIT": "68.0%", "Dano CRIT": "250.0%"},
            "pieces": [{"slot": "Bota", "main": "ATQ% (43.2%)"}],
        }
        mock_meta = {
            "weapon": "Signature",
            "weapons": ["Signature"],
            "sets": ["4p Set"],
            "all_sets": ["4p Set"],
            "stats": {"Bota": "Qualquer (Flex)"},
            "endgame_stats": {"VEL": "Base SPD or 134", "Taxa Crítica": "100% (in-combat)", "Dano Crítico": "220%+"},
        }
        with (
            patch("services.roster_service.database.get_roster_data", return_value=[]),
            patch("services.roster_service.parse_character_build_data", return_value=mock_build),
            patch("services.roster_service.parse_meta_target", return_value=mock_meta),
        ):
            res = self.client.get("/api/compare/hsr/Evanescia")

        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("meta_radar", data)
        self.assertEqual(data["meta_radar"]["summary"]["radar_mode"], "polygon")
        self.assertEqual(len(data["meta_radar"]["axes"]), 3)

        # Contrato de UI: Radar container e abas segmentadas presentes sem <button cru
        with open("static/index.html", "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn('id="ins-meta-radar-card"', html)
        self.assertIn('id="ins-radar-svg-wrap"', html)
        self.assertIn('class="inspector-tabs-segmented"', html)
        self.assertIn('class="inspector-header-actions"', html)
        self.assertNotIn("<button", html)

    def test_08_sigrid_overcap_in_battle_and_max_6_axes(self):
        # Sigrid: 33.8% CRIT Rate com Passiva de Núcleo (+66% em combate) -> Cap Ideal atingido!
        sigrid_stats = {
            "PV": "11352",
            "ATQ": "3206",
            "DEF": "805",
            "Taxa CRIT": "33.8%",
            "Dano CRIT": "155.6%",
        }
        sigrid_endgame = {
            "ATK": "3000 - 3400+",
            "HP": "9500+",
            "DEF": "750+",
            "Taxa Crítica": "33.8% (any more and she’ll overcap due to the 66% from her Passiva de Núcleo!)",
            "Dano Crítico": "150% - 210%+ (W-Engine mainstat and D4 picks can give it a large range)",
        }
        radar = build_radar_benchmark_payload("zzz", "Sigrid", sigrid_stats, sigrid_endgame)
        self.assertEqual(radar["summary"]["radar_mode"], "polygon")
        self.assertEqual(radar["summary"]["met_count"], 5)
        by_key = {a["stat_key"]: a for a in radar["axes"]}
        cr = by_key["crit_rate"]
        self.assertEqual(cr["target_min"], 33.8)
        self.assertEqual(cr["status"], "ok")
        self.assertIn("cap", cr["tags"])
        self.assertNotIn("overcap", cr["tags"])
        self.assertLess(len(cr["target_display_pt"]), 30)
        self.assertIn("overcap", cr["tooltip_note"].lower())

        # Overcap explícito se passar muito de 33.8% (ex.: 48%)
        radar_over = build_radar_benchmark_payload("zzz", "Sigrid", {"Taxa CRIT": "48.0%"}, {"Taxa Crítica": sigrid_endgame["Taxa Crítica"]})
        self.assertIn("overcap", radar_over["axes"][0]["tags"])

        # Evelyn: 'at least 55%' fora de combate
        spec_evelyn = parse_benchmark_spec(
            "crit_rate",
            "80 - 100% (including Passiva de Núcleo) Evelyn requires 80%... she'll need at least 55% in order to operate optimally.",
            "zzz",
        )
        self.assertEqual(spec_evelyn["target_min"], 55.0)
        self.assertIn("pre_combat", spec_evelyn["tags"])

        # Cap de no máximo 6 vértices no polígono SVG quando personagem tem 7+ benchmarks
        seven_stats = {"ATQ": "3000", "PV": "10000", "DEF": "900", "Taxa CRIT": "80%", "Dano CRIT": "170%", "Prof. Anomalia": "300", "Maest. Anomalia": "120"}
        seven_meta = {"ATQ": "2800+", "Vida": "10000+", "DEF": "800+", "Taxa CRIT": "75%+", "Dano CRIT": "150%+", "Proficiência de Anomalia": "240+", "Maestria de Anomalia": "116+"}
        radar_7 = build_radar_benchmark_payload("zzz", "Miyabi", seven_stats, seven_meta)
        self.assertEqual(len(radar_7["axes"]), 7)
        self.assertEqual(radar_7["summary"]["plotted_count"], 6)


if __name__ == "__main__":
    unittest.main()
