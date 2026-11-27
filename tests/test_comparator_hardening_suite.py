import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import extractor
import meta_comparator
from calculators.benchmark_radar import build_radar_benchmark_payload
from calculators.equipment_comparator import (
    evaluate_build_comparison,
    localize_equipment_name,
    normalize_main_stat_key,
)
from scrapers.scraper_genshin import PrydwenGenshinScraper
from scrapers.scraper_prydwen import PrydwenScraper
from scrapers.scraper_zzz import PrydwenZZZScraper


class TestComparatorHardeningSuite(unittest.TestCase):
    """Suite de regressão e blindagem do Comparador Meta, Scrapers e Guias (100% offline)."""

    def test_01_hsr_scraper_filters_browse_chips_and_preserves_in_combat(self):
        scraper = PrydwenScraper()
        list_html = """
        <div>
          <div class="hsr-browse-items">
            <a class="hsr-browse-chip kind-rarity" href="/star-rail/characters/rarity/4-star">4-Star</a>
            <a class="hsr-browse-chip kind-path" href="/star-rail/characters/path/abundance">Abundance</a>
            <a class="hsr-browse-chip kind-element" href="/star-rail/characters/element/fire">Fire</a>
          </div>
          <a href="/star-rail/characters/evanescia"><span class="emp-name">Evanescia</span></a>
          <a href="/star-rail/characters/evanescia-calculations">Calc</a>
        </div>
        """

        class _FakeResp:
            text = list_html

            def raise_for_status(self):
                return None

        with patch("scrapers.scraper_prydwen.requests.get", return_value=_FakeResp()):
            chars = scraper.get_character_list()
        self.assertEqual([c["name"] for c in chars], ["Evanescia"])

        guide_html = """
        <div class="hsr-endgame-row">
          <div class="hsr-stat-tile"><span>Speed</span></div>
          <div class="hsr-endgame-value">
            <span class="value">Base SPD or 134</span>
            <div class="hsr-endgame-comment"><p>Very long explanation paragraph about Certified Bangers and turns.</p></div>
          </div>
        </div>
        <div class="hsr-endgame-row">
          <div class="hsr-stat-tile"><span>Crit Rate</span></div>
          <div class="hsr-endgame-value">
            <span class="value">100%</span>
            <div class="hsr-endgame-comment"><p>(in-combat)</p></div>
          </div>
        </div>
        """
        soup = BeautifulSoup(guide_html, "html.parser")
        data = {
            "pros": [],
            "cons": [],
            "review": [],
            "skills_active": [],
            "skills_traces": [],
            "skills_eidolons": [],
            "light_cones": [],
            "relics": [],
            "planar_ornaments": [],
            "stats_main": [],
            "stats_sub": "",
            "endgame_stats": [],
            "stats_info": "",
            "talent_priority": "",
            "teams": [],
        }
        parsed = scraper._scrape_hsr_nextjs_guide(soup, data)
        self.assertIn("Speed: Base SPD or 134", parsed["endgame_stats"])
        self.assertIn("Crit Rate: 100% (in-combat)", parsed["endgame_stats"])

    def test_02_scrapers_guard_against_empty_guides_and_overwrites(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # HSR empty guide must not be created
            hsr_scraper = PrydwenScraper()
            empty_hsr = {
                "pros": [], "cons": [], "review": [],
                "skills_active": [], "skills_traces": [], "skills_eidolons": [],
                "light_cones": [], "relics": [], "planar_ornaments": [],
                "stats_main": [], "stats_sub": "", "endgame_stats": [],
                "stats_info": "", "talent_priority": "", "teams": [],
            }
            p_hsr = hsr_scraper.save_to_markdown("Fake Teaser", empty_hsr, output_dir=tmpdir)
            self.assertFalse(os.path.exists(p_hsr))

            # ZZZ empty guide must not be created & existing valid guide must not be overwritten
            zzz_scraper = PrydwenZZZScraper()
            empty_zzz = {
                "pros": [], "cons": [], "review": [],
                "skills_active": [], "skills_passives": [], "skills_mindscapes": [],
                "w_engines": [], "discs": [], "disk_sets": [],
                "stats_main": [], "stats_sub": "", "stats_info": "",
                "stats_endgame": [], "talent_priority": "", "teams": [],
            }
            p_zzz = zzz_scraper.save_to_markdown("Sunbringer", empty_zzz, output_dir=tmpdir)
            self.assertFalse(os.path.exists(p_zzz))

            valid_zzz = dict(empty_zzz, w_engines=[{"name": "Signature", "percentage": "100%", "super": "", "justification": ""}], stats_main=["Disk 4 CRIT DMG%", "Disk 5 ATK%", "Disk 6 ATK%"])
            p_zzz_ok = zzz_scraper.save_to_markdown("Sigrid", valid_zzz, output_dir=tmpdir)
            self.assertTrue(os.path.exists(p_zzz_ok))
            original_txt = Path(p_zzz_ok).read_text(encoding="utf-8")
            degraded_zzz = dict(valid_zzz, stats_main=[])
            zzz_scraper.save_to_markdown("Sigrid", degraded_zzz, output_dir=tmpdir)
            self.assertEqual(Path(p_zzz_ok).read_text(encoding="utf-8"), original_txt)

            # Genshin must NEVER translate weapon/artifact names (e.g. 'Staff of the Scarlet Sands')
            gen_scraper = PrydwenGenshinScraper()
            gen_data = {
                "weapons": ["**Staff of the Scarlet Sands (R1)** - Good with Electro DMG"],
                "artifacts": ["**Emblem of Severed Fate** - Best Energy Recharge set"],
                "stats_main": [{"slot": "Sands", "value": "Energy Recharge"}],
                "stats_sub": "CRIT Rate > Energy Recharge",
                "stats_info": "",
                "talent_priority": "Burst > Skill",
                "skills_active": [],
                "skills_passives": [],
                "constellations": [],
                "synergies": [],
                "teams": [],
            }
            p_gen = gen_scraper.save_to_markdown("Raiden Shogun", gen_data, output_dir=tmpdir)
            gen_md = Path(p_gen).read_text(encoding="utf-8")
            self.assertIn("**Staff of the Scarlet Sands (R1)**", gen_md)
            self.assertNotIn("Scarlet Ampulheta", gen_md)
            self.assertIn("**Emblem of Severed Fate**", gen_md)

    def test_03_zzz_scraper_deduplicates_desktop_mobile_main_stats(self):
        html = """
        <div class="tabs"></div>
        <div class="tab-inside"></div>
        <div class="tab-inside"></div>
        <div class="tab-inside">
          <div class="build-tips">
            <div class="main-stats">
              <div class="box">Disk 4 CRIT DMG% &gt; ATK%</div>
              <div class="box">Disk 5 PEN Ratio%</div>
              <div class="box">Disk 6 ATK%</div>
            </div>
          </div>
          <div class="build-tips">
            <div class="main-stats">
              <div class="box">Disk 4 CRIT DMG% &gt; ATK%</div>
              <div class="box">Disk 5 PEN Ratio%</div>
              <div class="box">Disk 6 ATK%</div>
            </div>
          </div>
        </div>
        <div class="tab-inside"></div>
        """

        class _FakeResp:
            text = html

            def raise_for_status(self):
                return None

        scraper = PrydwenZZZScraper()
        with patch("scrapers.scraper_zzz.requests.get", return_value=_FakeResp()):
            res = scraper.scrape_agent_guide("Sigrid", "https://www.prydwen.gg/zenless/characters/sigrid")
        self.assertEqual(len(res["stats_main"]), 3)
        self.assertEqual(res["stats_main"][0], "Disk 4 CRIT DMG% > ATK%")

    def test_04_extractor_sanitize_stat_name_never_doubles_impacto(self):
        self.assertEqual(extractor.sanitize_stat_name("Impacto"), "Impacto")
        self.assertEqual(extractor.sanitize_stat_name("Impact"), "Impacto")
        self.assertEqual(extractor.sanitize_stat_name("Taxa de Perfuração"), "Perfuração")

    def test_05_canonical_slug_resolution_hsr_pt_names_and_trailblazer(self):
        roster = [
            {"id": "8009", "name": "Desbravador(a)", "element": "lightning"},
            {"id": "1413", "name": "Noite Eterna", "element": "ice"},
            {"id": "1321", "name": "A Dália", "element": "fire"},
            {"id": "1112", "name": "Topaz e Dinheirinho", "element": "fire"},
            {"id": "1006", "name": "Loba Prateada", "element": "quantum"},
        ]
        self.assertEqual(
            meta_comparator.resolve_character_canonical_slug("hsr", "Desbravador(a)", "lightning", roster),
            "trailblazer_•_elation",
        )
        self.assertEqual(
            meta_comparator.resolve_character_canonical_slug("hsr", "Desbravador(a)", "ice", []),
            "trailblazer_•_remembrance",
        )
        self.assertEqual(
            meta_comparator.resolve_character_canonical_slug("hsr", "Noite Eterna", "ice", roster),
            "march_7th_•_evernight",
        )
        self.assertEqual(
            meta_comparator.resolve_character_canonical_slug("hsr", "A Dália", "fire", roster),
            "the_dahlia",
        )
        self.assertEqual(
            meta_comparator.resolve_character_canonical_slug("hsr", "Topaz e Dinheirinho", "fire", roster),
            "topaz_&_numby",
        )
        self.assertEqual(
            meta_comparator.resolve_character_canonical_slug("hsr", "Loba Prateada", "quantum", roster),
            "silver_wolf",
        )

    def test_06_canonical_equipment_matching_pt_en_and_hsr_planar(self):
        # Evanescia: PT-BR HoYoLAB <-> EN Prydwen via catálogo dinâmico oficial
        self.assertEqual(
            localize_equipment_name("hsr", "weapons", "Until the Flowers Bloom Again", "pt"),
            "Um Encontro na Próxima Primavera",
        )
        self.assertEqual(
            localize_equipment_name("hsr", "weapons", "Flowing Nightglow", "pt"),
            "Luzes Noturnas",
        )
        self.assertEqual(
            localize_equipment_name("genshin", "weapons", "Azurelight", "pt"),
            "Azul Brilhante",
        )
        self.assertEqual(
            localize_equipment_name("genshin", "sets", "Finale of the Deep Galleries", "pt"),
            "Epílogo do Corredor",
        )

        ev_eval = evaluate_build_comparison(
            "hsr",
            player_build={
                "weapon": "Um Encontro na Próxima Primavera (Nv. 80, R1)",
                "weapon_clean": "Um Encontro na Próxima Primavera",
                "sets": [
                    "Menina Mágica Sempre Gloriosa (4 peças)",
                    "Estágio Zero de Punklorde (2 peças)",
                ],
                "pieces": [
                    {"slot": "Corpo", "main": "Dano CRIT (64.8%)"},
                    {"slot": "Bota", "main": "ATQ% (43.2%)"},
                    {"slot": "Esfera", "main": "PV% (43.2%)"},
                    {"slot": "Corda", "main": "ATQ% (43.2%)"},
                ],
            },
            meta_target={
                "weapon": "Um Encontro na Próxima Primavera",
                "weapons_raw": ["Until the Flowers Bloom Again", "Today's Good Luck"],
                "relic_sets_raw": ["Ever-Glorious Magical Girl"],
                "planar_sets_raw": ["Punklorde Stage Zero"],
                "stats": {
                    "Corpo": "Dano Crítico / Taxa Crítica",
                    "Bota": "Qualquer (Flex) / VEL",
                    "Esfera": "Qualquer (Flex)",
                    "Corda": "Qualquer (Flex)",
                },
            },
        )
        self.assertEqual(ev_eval["weapon"]["tier"], 1)
        self.assertEqual(ev_eval["weapon"]["score"], 25)
        self.assertEqual(ev_eval["sets"]["tier"], 1)
        self.assertEqual(ev_eval["sets"]["score"], 25)
        self.assertTrue(ev_eval["sets"]["has_bis_relic"])
        self.assertTrue(ev_eval["sets"]["has_bis_planar"])
        self.assertEqual(ev_eval["slots_score"], 30.0)
        self.assertEqual(ev_eval["slot_issues"], [])

    def test_07_main_stat_normalization_prevents_taxa_rate_collisions(self):
        # 'Taxa' / 'Rate' em Energia, Acerto de Efeito e Perfuração NUNCA podem virar crit_rate!
        self.assertEqual(normalize_main_stat_key("Taxa de Regen. Energia (19.4%)")[0], "er")
        self.assertEqual(normalize_main_stat_key("Energy Regen Rate")[0], "er")
        self.assertEqual(normalize_main_stat_key("Taxa de Acerto de Efeito (43.2%)")[0], "ehr")
        self.assertEqual(normalize_main_stat_key("Effect Hit Rate")[0], "ehr")
        self.assertEqual(normalize_main_stat_key("Taxa de Perfuração (24%)")[0], "pen_pct")
        self.assertEqual(normalize_main_stat_key("PEN Ratio%")[0], "pen_pct")
        self.assertEqual(normalize_main_stat_key("Proficiência de Anomalia (92)")[0], "anomaly_prof")
        self.assertEqual(normalize_main_stat_key("Maestria de Anomalia (30%)")[0], "anomaly_mastery")
        self.assertEqual(normalize_main_stat_key("Taxa Crítica (32.4%)")[0], "crit_rate")
        self.assertEqual(normalize_main_stat_key("Dano Crítico (64.8%)")[0], "crit_dmg")

        # Elemento errado no Cálice/Esfera deve ser detectado como mismatch
        wrong_elem = evaluate_build_comparison(
            "genshin",
            player_build={
                "weapon_clean": "Signature",
                "sets": [],
                "pieces": [{"slot": "Copo", "main": "Dano Pyro (46.6%)"}],
            },
            meta_target={
                "weapons_raw": ["Signature"],
                "all_sets_raw": [],
                "stats": {"Copo": "Bônus de Dano Cryo"},
            },
        )
        self.assertEqual(wrong_elem["slots"][0]["status"], "mismatch")

    def test_08_radar_zero_omitted_stats_and_zzz_english_compaction(self):
        # Stat secundário omitido pelo HoYoLAB quando = 0% (ex.: Bônus de Cura) não deve aparecer como 'missing'
        radar = build_radar_benchmark_payload(
            "hsr",
            "Huohuo",
            player_stats={"PV": "6500", "ATQ": "1800", "DEF": "1100", "VEL": "140", "Regen. Energia": "119.4%"},
            endgame_stats={"Vida": "6.000+", "VEL": "134+", "Bônus de Cura": "34.5%+"},
        )
        by_key = {a["stat_key"]: a for a in radar["axes"]}
        self.assertEqual(by_key["healing_bonus"]["status"], "low")
        self.assertEqual(by_key["healing_bonus"]["actual_display"], "0.0%")

        # Compactação/tradução de notas em inglês de ZZZ (Císsia, Yixuan)
        radar_zzz = build_radar_benchmark_payload(
            "zzz",
            "Císsia",
            player_stats={"ATQ": "3000", "Taxa CRIT": "55.0%", "Dano CRIT": "160.0%", "PV": "10000"},
            endgame_stats={
                "Taxa CRIT": "50% - 57% (with Signature W-Engine, pre-combat)",
                "Dano CRIT": "150%+",
            },
        )
        cr_ax = next(a for a in radar_zzz["axes"] if a["stat_key"] == "crit_rate")
        self.assertNotIn("with Signature", cr_ax["target_display_pt"])

    def test_09_frontend_comparator_zero_hardcoded_dict_and_valid_retry(self):
        js_txt = Path("static/js/modules/build_comparator.js").read_text(encoding="utf-8")
        self.assertNotIn("const translationDict =", js_txt)
        self.assertIn("data.comparison_eval", js_txt)
        self.assertIn('onclick="loadBuildComparison()"', js_txt)
        self.assertNotIn("window.loadComparison", js_txt)
        # UI do Radar exibe valores reais nos vértices/readout (sem % de aderência ratio_pct na UI)
        self.assertIn("_formatRadarActualValue", js_txt)
        self.assertNotIn("ratio_pct", js_txt)
        self.assertNotIn("avg_ratio_pct", js_txt)

    def test_10_genshin_scaling_consistency_and_full_radar_baselines(self):
        # Linnea (DEF), Escoffier (ATK), Nefer (EM), Odette (ATK), Nicole (ATK) NUNCA podem pedir Vida 30k+!
        for cname, expected_stat in (
            ("Linnea", "DEF"),
            ("Escoffier", "ATQ"),
            ("Nefer", "Proficiência Elemental"),
            ("Odette", "ATQ"),
            ("Nicole", "ATQ"),
        ):
            mt = meta_comparator.parse_meta_target("genshin", cname)
            eg = mt.get("endgame_stats") or {}
            self.assertIn(expected_stat, eg, f"{cname} deveria ter meta de {expected_stat}, obteve {eg}")
            self.assertNotIn("Vida", eg, f"{cname} não escala com Vida, mas pediu {eg}")

        # Blindagem futura: preset estático pedindo Vida 32k em guia DEF% deve ser rejeitado automaticamente
        self.assertFalse(
            meta_comparator._is_benchmark_consistent_with_guide(
                "genshin",
                {"Vida": "32.000+", "Taxa Crítica": "65%+"},
                {"Areia": "DEF%", "Copo": "DEF%", "Tiara": "Taxa Crítica"},
                "DEF% > Taxa Crítica > Dano Crítico",
            )
        )

        # Radar completo com médias realistas para Zibai (DEF-scaler: ATQ fica em 1.000 - 1.500 sem punir nota!)
        zibai_stats = {
            "PV": "17500",
            "ATQ": "1180",
            "DEF": "2650",
            "Taxa CRIT": "72.0%",
            "Dano CRIT": "175.0%",
            "Recarga": "115.0%",
            "Prof. Element.": "85",
        }
        zibai_radar = build_radar_benchmark_payload(
            "genshin",
            "Zibai",
            zibai_stats,
            {"DEF": "2.500+", "Taxa Crítica": "70%+", "Dano Crítico": "140%+"},
            include_baseline_stats=True,
        )
        # Todos os 7 status aparecem no breakdown e 6 vértices formam o polígono hexágono
        self.assertEqual(len(zibai_radar["axes"]), 7)
        self.assertEqual(zibai_radar["summary"]["plotted_count"], 6)
        self.assertEqual(zibai_radar["summary"]["radar_mode"], "polygon")
        # Nota baseada apenas nas 3 metas principais (3/3 OK -> 20.0 pontos!)
        self.assertEqual(zibai_radar["summary"]["met_count"], 3)
        self.assertEqual(zibai_radar["summary"]["benchmark_score_20"], 20.0)

        by_key = {a["stat_key"]: a for a in zibai_radar["axes"]}
        self.assertFalse(by_key["def_flat"]["is_baseline"])
        self.assertTrue(by_key["atk_flat"]["is_baseline"])
        self.assertEqual(by_key["atk_flat"]["target_display_pt"], "1.000 - 1.500")
        self.assertEqual(by_key["atk_flat"]["status"], "ok")
        self.assertTrue(by_key["hp_flat"]["is_baseline"])
        self.assertEqual(by_key["hp_flat"]["target_display_pt"], "15.000 - 19.000")

        # HSR Evanescia também passa de 3 eixos para hexágono completo (6 eixos) sem perder nota
        ev_radar = build_radar_benchmark_payload(
            "hsr",
            "Evanescia",
            {"PV": "3200", "ATQ": "2100", "DEF": "950", "VEL": "115", "Taxa CRIT": "65.4%", "Dano CRIT": "278.9%"},
            {"VEL": "Base SPD or 134", "Taxa Crítica": "100% (in-combat)", "Dano Crítico": "220%+"},
            include_baseline_stats=True,
        )
        self.assertEqual(len(ev_radar["axes"]), 6)
        self.assertEqual(ev_radar["summary"]["plotted_count"], 6)
        self.assertEqual(ev_radar["summary"]["met_count"], 2)

    def test_11_scraper_meta_overwrite_guard_and_evaluate_stats_schema(self):
        import tempfile
        from scrapers.scraper_meta import PrydwenMetaScraper
        from schemas.static_data import EvaluateStatsRequest

        scraper = PrydwenMetaScraper()
        with tempfile.TemporaryDirectory() as tmpdir:
            meta_fp = os.path.join(tmpdir, "meta_e_tierlists_atual.md")
            endgame_fp = os.path.join(tmpdir, "meta_endgame_report.md")
            valid_content = "# Conteúdo válido existente\n" + ("linha de tier list válida\n" * 15)
            with open(meta_fp, "w", encoding="utf-8") as f:
                f.write(valid_content)
            with open(endgame_fp, "w", encoding="utf-8") as f:
                f.write(valid_content)

            scraper.save_meta_markdown({"changelog": [], "characters": []}, filepath=meta_fp)
            scraper.save_endgame_markdown({}, filepath=endgame_fp)

            with open(meta_fp, encoding="utf-8") as f:
                self.assertEqual(f.read(), valid_content)
            with open(endgame_fp, encoding="utf-8") as f:
                self.assertEqual(f.read(), valid_content)

        req = EvaluateStatsRequest.model_validate({"ATQ": "2500", "Taxa Crítica": "75%"})
        self.assertEqual(req.root["ATQ"], "2500")


if __name__ == "__main__":
    unittest.main()
