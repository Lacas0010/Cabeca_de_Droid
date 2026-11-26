import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import build_calculator
import meta_comparator
from scrapers.scraper_genshin import PrydwenGenshinScraper
from scrapers.scraper_prydwen import PrydwenScraper, extract_prydwen_card_name
from scrapers.scraper_zzz import PrydwenZZZScraper


class TestPrydwenEndgameAndNames(unittest.TestCase):
    """Testes offline garantindo extração limpa de nomes (sem badges) e Recommended Endgame Stats do Prydwen."""

    def test_extract_prydwen_card_name_ignores_badges(self):
        html = """
        <div>
          <a href="/star-rail/characters/aha">
            <div class="avatar"><span class="emp-name">Aha</span><span class="tag new">New</span></div>
          </a>
          <a href="/zenless/characters/astra-yao">
            <div class="avatar"><span class="emp-name">Astra Yao</span><span class="tag">HSR</span></div>
          </a>
          <a class="pw-card" href="/genshin-impact/characters/mitya">
            <span class="genshin-card-name ds-card-name">Mitya</span><span class="tag new">New</span>
          </a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        links = soup.find_all("a")
        self.assertEqual(extract_prydwen_card_name(links[0], "aha"), "Aha")
        self.assertEqual(extract_prydwen_card_name(links[1], "astra-yao"), "Astra Yao")
        self.assertEqual(extract_prydwen_card_name(links[2], "mitya"), "Mitya")

    @patch("curl_cffi.requests.get")
    def test_character_lists_strip_badges_across_games(self, mock_get):
        def _fake_get(url, **kwargs):
            resp = MagicMock()
            if "/star-rail/" in url:
                resp.text = (
                    '<a href="/star-rail/characters/aha"><span class="emp-name">Aha</span>'
                    '<span class="tag new">New</span></a>'
                )
            elif "/zenless/" in url:
                resp.text = (
                    '<a href="/zenless/characters/severian"><span class="emp-name">Severian</span>'
                    '<span class="tag new">New</span></a>'
                )
            else:
                resp.text = (
                    '<a href="/genshin-impact/characters/anastasya">'
                    '<span class="genshin-card-name">Anastasya</span><span class="tag future">7.3</span></a>'
                )
            return resp

        mock_get.side_effect = _fake_get

        self.assertEqual(PrydwenScraper().get_character_list()[0]["name"], "Aha")
        self.assertEqual(PrydwenZZZScraper().get_agent_list()[0]["name"], "Severian")
        self.assertEqual(PrydwenGenshinScraper().get_character_list()[0]["name"], "Anastasya")

    @patch("scrapers.scraper_prydwen.requests.get")
    def test_scrape_hsr_endgame_stats_and_markdown_export(self, mock_get):
        sample_html = """
        <html><body>
          <div class="tab-inside"><div class="skill-header">Skill Test</div><div class="skill-with-coloring">Test</div></div>
          <div class="tab-inside">
            <h5>Pros</h5><div><p>Great support</p></div>
            <h5>Cons</h5><div><p>Niche</p></div>
            <div class="section-analysis"><p>Increases base SPD from 80 SPD and gives 12% CRIT Rate in review prose.</p></div>
          </div>
          <div class="tab-inside">
            <div class="build-stats">
              <div class="main-stats">
                <div class="flex-1">Body: CRIT Rate</div>
                <div class="flex-1">Feet: Speed</div>
                <div class="flex-1">Planar Sphere: HP% / DEF%</div>
                <div class="flex-1">Link Rope: HP% / DEF%</div>
              </div>
              <div class="flex-wrap"><div class="flex-1">Substats: SPD > CRIT Rate / CRIT DMG</div></div>
            </div>
            <div class="content-header Quantum">Recommended endgame stats</div>
            <div>
              <div class="raw list">
                <ul>
                  <li><p>Speed: <strong>150+</strong></p></li>
                  <li><p>Crit Rate: <strong>100%</strong> (In combat)</p></li>
                  <li><p>Crit DMG: <strong>140%+</strong></p></li>
                </ul>
              </div>
            </div>
          </div>
        </body></html>
        """
        resp = MagicMock()
        resp.text = sample_html
        mock_get.return_value = resp

        scraper = PrydwenScraper()
        data = scraper.scrape_character_guide("Aha", "https://www.prydwen.gg/star-rail/characters/aha")
        self.assertEqual(
            data["endgame_stats"],
            ["Speed: 150+", "Crit Rate: 100% (In combat)", "Crit DMG: 140%+"],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = scraper.save_to_markdown("Aha", data, output_dir=tmpdir)
            with open(md_path, "r", encoding="utf-8") as f:
                md_text = f.read()
            self.assertIn("#### Atributos Finais Recomendados (Endgame Stats)", md_text)
            self.assertIn("- Speed: 150+", md_text)
            self.assertIn("- Crit Rate: 100% (In combat)", md_text)
            self.assertIn("- Crit DMG: 140%+", md_text)

    def test_generate_meta_json_resolves_dynamic_id_and_ignores_prose_numbers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                os.makedirs("hsr/guias", exist_ok=True)
                os.makedirs("static_data", exist_ok=True)

                manifest = {
                    "characters": {
                        "aeon_★_aha": {
                            "id": "aeon_★_aha",
                            "name": "Aeon ★ Aha",
                            "hoyolab_id": "1511",
                        }
                    }
                }
                with open("static_data/hsr_manifest.json", "w", encoding="utf-8") as f:
                    json.dump(manifest, f)

                with open("static_data/character_aliases.json", "w", encoding="utf-8") as f:
                    json.dump({"hsr": {}}, f)
                with open("static_data/hoyolab_mappings.json", "w", encoding="utf-8") as f:
                    json.dump({"hsr": {}}, f)

                # Guia preliminar Day-1 com valores genéricos errados
                with open("hsr/guias/aeon_★_aha.md", "w", encoding="utf-8") as f:
                    f.write(
                        '<!-- METADATA: {"source": "ai_preliminary"} -->\n'
                        "# Guia de Build - Aeon ★ Aha\n"
                        "- Body: Taxa Crítica / Dano Crítico\n"
                        "- Feet: Velocidade > ATK%\n"
                        "- Planar Sphere: Bônus de Dano quantum / HP%\n"
                        "- Link Rope: ATK%\n"
                        "#### Subatributos Prioritários (Sub-stats)\n"
                        "Taxa Crítica > Dano Crítico > ATK% > Velocidade\n"
                    )

                # Guia oficial do Prydwen com nome curto 'Aha' (e menção ao Aeon ★ Aha no texto)
                with open("hsr/guias/aha.md", "w", encoding="utf-8") as f:
                    f.write(
                        "# Guia de Build - Aha\n"
                        "### Análise Detalhada\n"
                        "Granting Aeon ★ Aha 12% CRIT Rate and changing base SPD from 80 SPD.\n"
                        "### Atributos Recomendados (Stats)\n"
                        "#### Atributos Principais (Main Stats)\n"
                        "- Body: CRIT Rate\n"
                        "- Feet: Speed\n"
                        "- Planar Sphere: HP% / DEF%\n"
                        "- Link Rope: HP% / DEF%\n"
                        "#### Subatributos Prioritários (Sub-stats)\n"
                        "vel > CRIT Rate / CRIT DMG\n"
                        "#### Atributos Finais Recomendados (Endgame Stats)\n"
                        "- Speed: 150+\n"
                        "- Crit Rate: 100% (In combat)\n"
                        "- Crit DMG: 140%+\n"
                    )

                with patch("build_calculator.get_resource_path", side_effect=lambda p: os.path.join(tmpdir, p)):
                    build_calculator.META_DATA_CACHE.clear()
                    build_calculator.generate_meta_json_from_markdown("hsr")

                with open("hsr/meta_data_hsr.json", "r", encoding="utf-8") as f:
                    meta_db = json.load(f)

                self.assertIn("1511", meta_db)
                self.assertNotIn("aha", meta_db)
                entry = meta_db["1511"]
                self.assertEqual(entry["name"], "Aeon ★ Aha")
                self.assertEqual(
                    entry["main_stats"],
                    {
                        "body": ["crit_rate"],
                        "feet": ["spd"],
                        "planar_sphere": ["hp_pct", "def_pct"],
                        "link_rope": ["hp_pct", "def_pct"],
                    },
                )
                self.assertEqual(entry["substats_priority"], ["spd", "crit_rate", "crit_dmg"])
                self.assertEqual(
                    entry["general_benchmarks"],
                    {
                        "spd": ">= 150",
                        "crit_rate": ">= 100% (In combat)",
                        "crit_dmg": ">= 140%",
                    },
                )
            finally:
                os.chdir(orig_cwd)
                build_calculator.META_DATA_CACHE.clear()

    def test_find_best_guide_prefers_official_over_preliminary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            guides_dir = os.path.join(tmpdir, "hsr", "guias")
            os.makedirs(guides_dir, exist_ok=True)
            with open(os.path.join(guides_dir, "aeon_★_aha.md"), "w", encoding="utf-8") as f:
                f.write('<!-- METADATA: {"source": "ai_preliminary"} -->\n# Preliminar\n')
            official = os.path.join(guides_dir, "aha.md")
            with open(official, "w", encoding="utf-8") as f:
                f.write("# Guia Oficial Prydwen\n")

            with patch.object(meta_comparator, "BASE_DIR", tmpdir), patch.object(
                meta_comparator, "resolve_character_canonical_slug", return_value="aeon_★_aha"
            ):
                found = meta_comparator.find_best_guide_file("hsr", "Aeon ★ Aha", "Quantum")
                self.assertEqual(os.path.normpath(found), os.path.normpath(official))

    def test_sanitize_substats_strips_qualifiers_and_brackets(self):
        evanescia_raw = ["CRIT Rate until 100% in combat", "CRIT DMG"]
        self.assertEqual(build_calculator.sanitize_substats(evanescia_raw, "hsr"), ["crit_rate", "crit_dmg"])

        hyacine_raw = ["SPD to 200 or more", "HP%", "CRIT DMG", "= Effect RES"]
        self.assertEqual(
            build_calculator.sanitize_substats(hyacine_raw, "hsr"),
            ["spd", "hp_pct", "crit_dmg", "res"],
        )

        cipher_raw = ["[SPD", "ehr", "CRIT RATE = CRIT DMG", "ATK%] or [SPD", "ehr", "hp_pct", "= DEF%]"]
        self.assertEqual(
            build_calculator.sanitize_substats(cipher_raw, "hsr"),
            ["spd", "ehr", "crit_rate", "crit_dmg", "atk_pct"],
        )

    @patch("scrapers.scraper_prydwen.requests.get")
    def test_scrape_prydwen_substats_with_until_qualifier(self, mock_get):
        html = """
        <html><body>
          <div class="tab-inside"><div class="skill-header">Basic</div><div class="skill-with-coloring">x</div></div>
          <div class="tab-inside"><h5>Pros</h5><div><p>p</p></div></div>
          <div class="tab-inside">
            <div class="build-stats">
              <div class="main-stats">
                <div class="flex-1">Body: CRIT DMG</div>
                <div class="flex-1">Feet: Anything</div>
                <div class="flex-1">Planar Sphere: Anything</div>
                <div class="flex-1">Link Rope: Energy Regen Rate</div>
              </div>
              <div class="flex-wrap"><div class="flex-1">Substats: CRIT Rate until 100% in combat &gt; CRIT DMG</div></div>
            </div>
          </div>
        </body></html>
        """
        resp = MagicMock()
        resp.text = html
        mock_get.return_value = resp

        data = PrydwenScraper().scrape_character_guide("Evanescia", "https://www.prydwen.gg/star-rail/characters/evanescia")
        self.assertEqual(data["stats_sub"], "crit_rate > crit_dmg")

    def test_score_relic_treats_anything_main_stat_as_ideal(self):
        fake_meta = {
            "1505": {
                "main_stats": {
                    "body": ["crit_dmg"],
                    "feet": ["anything"],
                    "planar_sphere": ["anything"],
                    "link_rope": ["err"],
                },
                "substats_priority": ["crit_rate", "crit_dmg"],
                "general_benchmarks": {"crit_rate": ">= 100% (in-combat)", "crit_dmg": ">= 220%"},
                "name": "Evanescia",
            }
        }
        with patch("build_calculator.get_meta_data", return_value=fake_meta):
            grade_feet, score_feet = build_calculator.score_relic(
                "hsr", "1505", "Pés", "PV (43.2%)", "VEL: 4, Taxa CRIT: 5.8%, Dano CRIT: 18.1%"
            )
            grade_sphere, score_sphere = build_calculator.score_relic(
                "hsr", "1505", "Esfera Plana", "DEF (54.0%)", "PV: 105, DEF: 16, Taxa CRIT: 5.8%, Dano CRIT: 19.4%"
            )
            self.assertGreaterEqual(score_feet, 75.0)
            self.assertGreaterEqual(score_sphere, 75.0)
            self.assertIn(grade_feet, ("SS", "SSS"))
            self.assertIn(grade_sphere, ("SS", "SSS"))

    @patch("scrapers.scraper_zzz.requests.get")
    def test_zzz_agent_list_extracts_specialty_element_and_rarity(self, mock_get):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.text = """
        <html><body>
          <a href="/zenless/characters/yixuan">
            <div class="avatar pw-card zzz rarity-S">
              <div class="element"><img alt="Yixuan Ether element" src="https://cdn.prydwen.gg/ele_yi.webp"/></div>
              <div class="class"><img alt="Yixuan Rupture style" src="https://cdn.prydwen.gg/style_rupture.webp"/></div>
              <span class="emp-name">Yixuan</span>
            </div>
          </a>
          <a href="/zenless/characters/pan-yinhu">
            <div class="avatar pw-card zzz rarity-A">
              <div class="element"><img alt="Pan Yinhu Physical element" src="https://cdn.prydwen.gg/ele_physical.webp"/></div>
              <div class="class"><img alt="Pan Yinhu Defence style" src="https://cdn.prydwen.gg/style_defence.webp"/></div>
              <span class="emp-name">Pan Yinhu</span>
            </div>
          </a>
          <a href="/zenless/characters/claret">
            <div class="avatar pw-card zzz rarity-S">
              <div class="element"><img alt="Claret Electric element" src="https://cdn.prydwen.gg/ele_electric.webp"/></div>
              <div class="class"><img alt="Claret Armorer style" src="https://cdn.prydwen.gg/style_armorer.webp"/></div>
              <span class="emp-name">Claret</span>
            </div>
          </a>
        </body></html>
        """
        mock_get.return_value = resp

        agents = {a["name"]: a for a in PrydwenZZZScraper().get_agent_list()}
        self.assertEqual(agents["Yixuan"]["specialty"], "Rupture")
        self.assertEqual(agents["Yixuan"]["element"], "Ether")
        self.assertEqual(agents["Yixuan"]["rarity"], 5)

        self.assertEqual(agents["Pan Yinhu"]["specialty"], "Defense")
        self.assertEqual(agents["Pan Yinhu"]["element"], "Physical")
        self.assertEqual(agents["Pan Yinhu"]["rarity"], 4)

        self.assertEqual(agents["Claret"]["specialty"], "Armorer")
        self.assertEqual(agents["Claret"]["element"], "Electric")
        self.assertEqual(agents["Claret"]["rarity"], 5)

    def test_sync_zzz_updates_non_curated_specialty_from_prydwen(self):
        from static_data_manager import StaticDataManager

        mgr = StaticDataManager.__new__(StaticDataManager)
        mgr._cache = {
            "zzz": {
                "characters": {
                    "yixuan": {
                        "id": "yixuan",
                        "name": "Yixuan",
                        "rarity": 5,
                        "element": "Physical",
                        "specialty": "Attack",
                    },
                    "astra": {
                        "id": "astra",
                        "name": "Astra Yao",
                        "rarity": 5,
                        "element": "Ether",
                        "specialty": "Support",
                        "expert_key": "new_eridu",
                    },
                }
            }
        }
        mocked_agents = [
            {"name": "Yixuan", "url": "https://www.prydwen.gg/zenless/characters/yixuan", "specialty": "Rupture", "element": "Ether", "rarity": 5},
            {"name": "Zhao", "url": "https://www.prydwen.gg/zenless/characters/zhao", "specialty": "Defense", "element": "Ice", "rarity": 5},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = os.path.join(tmpdir, "zzz_manifest.json")
            with patch.object(mgr, "_get_file_path", return_value=manifest_path), patch(
                "scrapers.PrydwenZZZScraper.get_agent_list", return_value=mocked_agents
            ):
                res = mgr._sync_zzz()
                self.assertEqual(res["status"], "success")
                self.assertEqual(mgr._cache["zzz"]["characters"]["yixuan"]["specialty"], "Rupture")
                self.assertEqual(mgr._cache["zzz"]["characters"]["yixuan"]["element"], "Ether")
                self.assertEqual(mgr._cache["zzz"]["characters"]["zhao"]["specialty"], "Defense")
                self.assertEqual(mgr._cache["zzz"]["characters"]["zhao"]["element"], "Ice")
                self.assertEqual(mgr._cache["zzz"]["characters"]["astra"]["specialty"], "Support")

    def test_zzz_quick_specialty_filter_ui_and_js_wiring(self):
        with open(os.path.join("static", "index.html"), "r", encoding="utf-8") as hf:
            soup = BeautifulSoup(hf.read(), "html.parser")

        spec_bar = soup.find("div", class_="specialty-filters", attrs={"data-game": "zzz"})
        self.assertIsNotNone(spec_bar)
        spec_vals = [b.get("data-specialty") for b in spec_bar.find_all(class_="filter-btn")]
        self.assertEqual(
            spec_vals,
            ["all", "attack", "stun", "anomaly", "support", "defense", "rupture", "armorer"],
        )

        audit_group = soup.select_one('#audit-panel-zzz .filter-pills[data-filter-type="specialty"]')
        self.assertIsNotNone(audit_group)
        audit_vals = [b.get("data-val") for b in audit_group.find_all(class_="audit-pill")]
        self.assertEqual(audit_vals, spec_vals)

        with open(os.path.join("static", "js", "modules", "roster.js"), "r", encoding="utf-8") as rf:
            roster_js = rf.read()
        self.assertIn(":not(.specialty-filters)", roster_js)
        self.assertIn('.specialty-filters[data-game="${gameId}"]', roster_js)
        self.assertIn("syncSpecialtyUI", roster_js)
        self.assertIn("ruptura", roster_js)
        self.assertIn("armeiro", roster_js)

    def test_official_icons_for_zzz_specialties_hsr_paths_and_genshin_weapons(self):
        with open(os.path.join("static", "index.html"), "r", encoding="utf-8") as hf:
            soup = BeautifulSoup(hf.read(), "html.parser")

        bars = [
            ("zzz", "specialty-filters", "data-specialty"),
            ("hsr", "path-filters", "data-path"),
            ("genshin", "weapon-filters", "data-weapon"),
        ]
        for game_id, cls_name, attr_name in bars:
            bar = soup.find("div", class_=cls_name, attrs={"data-game": game_id})
            self.assertIsNotNone(bar)
            for btn in bar.find_all(class_="filter-btn"):
                val = btn.get(attr_name)
                if val == "all":
                    continue
                self.assertIsNone(btn.find("i"), f"Generic icon remains in {game_id}/{val}")
                img = btn.find("img")
                self.assertIsNotNone(img, f"Official icon missing in {game_id}/{val}")
                expected_src = f"/assets/icons/{game_id}_{val}.png"
                actual_src = str(img.get("src") or "").split("?", 1)[0]
                self.assertEqual(actual_src, expected_src)
                disk_path = expected_src.lstrip("/")
                self.assertTrue(os.path.exists(disk_path), f"Missing asset file: {disk_path}")

    @patch("scrapers.scraper_prydwen.requests.get")
    def test_hsr_nextjs_layout_parsing_and_empty_overwrite_guard(self, mock_get):
        nextjs_html = """
        <html><body>
          <div class="hsr-build-card">
            <h3 class="hsr-build-card-title">Evanescia Light Cone Ranking</h3>
            <table class="hsr-rank-table"><tbody>
              <tr>
                <td>1</td>
                <td><a class="hsr-gear-name">Until the Flowers Bloom Again</a> <span class="hsr-gear-badge">S1</span></td>
                <td>127.03%</td>
                <td><div class="hsr-rank-note">Signature Light Cone.</div></td>
              </tr>
            </tbody></table>
          </div>
          <div class="hsr-build-card">
            <h3 class="hsr-build-card-title">Best Relic Sets</h3>
            <table class="hsr-rank-table"><tbody>
              <tr><td>1</td><td><a class="hsr-gear-name">Ever-Glorious Magical Girl</a></td><td>100%</td><td><div class="hsr-rank-note">BiS 4pc.</div></td></tr>
            </tbody></table>
          </div>
          <div class="hsr-build-card">
            <h3 class="hsr-build-card-title">Best Planetary Sets</h3>
            <table class="hsr-rank-table"><tbody>
              <tr><td>1</td><td><a class="hsr-gear-name">Punklorde Stage Zero</a></td><td>100%</td><td><div class="hsr-rank-note">BiS 2pc.</div></td></tr>
            </tbody></table>
          </div>
          <div class="hsr-main-stat-build">
            <div class="hsr-main-stat-row"><div class="hsr-stat-tile"><span>Body</span></div><div>CRIT DMG</div></div>
            <div class="hsr-main-stat-row"><div class="hsr-stat-tile"><span>Feet</span></div><div>Anything</div></div>
            <div class="hsr-main-stat-row"><div class="hsr-stat-tile"><span>Planar Sphere</span></div><div>Anything</div></div>
            <div class="hsr-main-stat-row"><div class="hsr-stat-tile"><span>Link Rope</span></div><div>Energy Regen Rate</div></div>
          </div>
          <div class="hsr-priority-panel">
            <h4>Sub Stats</h4>
            <div class="hsr-priority-strip">
              <div class="hsr-priority-tile primary">CRIT Rate until 100% in combat</div>
              <div class="hsr-priority-operator">&gt;</div>
              <div class="hsr-priority-tile">CRIT DMG</div>
            </div>
          </div>
          <div class="hsr-endgame-panel">
            <div class="hsr-endgame-row">
              <div>Speed</div>
              <div class="hsr-endgame-value"><span>Base SPD or 134</span><div class="hsr-endgame-comment">Long note</div></div>
            </div>
            <div class="hsr-endgame-row"><div>Crit Rate</div><div class="hsr-endgame-value">100%</div></div>
            <div class="hsr-endgame-row"><div>Crit DMG</div><div class="hsr-endgame-value">220%+</div></div>
          </div>
        </body></html>
        """
        resp = MagicMock()
        resp.text = nextjs_html
        mock_get.return_value = resp

        scraper = PrydwenScraper()
        data = scraper.scrape_character_guide("Evanescia", "https://www.prydwen.gg/star-rail/characters/evanescia")

        self.assertEqual(
            data["stats_main"],
            [
                "Body: CRIT DMG",
                "Feet: Anything",
                "Planar Sphere: Anything",
                "Link Rope: Energy Regen Rate",
            ],
        )
        self.assertEqual(data["stats_sub"], "crit_rate > crit_dmg")
        self.assertEqual(data["endgame_stats"], ["Speed: Base SPD or 134", "Crit Rate: 100%", "Crit DMG: 220%+"])
        self.assertEqual(data["light_cones"][0]["name"], "Until the Flowers Bloom Again")
        self.assertEqual(data["relics"][0]["name"], "Ever-Glorious Magical Girl")
        self.assertEqual(data["planar_ornaments"][0]["name"], "Punklorde Stage Zero")

        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = scraper.save_to_markdown("Evanescia", data, output_dir=tmpdir)
            with open(md_path, "r", encoding="utf-8") as f:
                saved_before = f.read()
            self.assertIn("Planar Sphere: Anything", saved_before)

            # Simula raspagem degradada sem stats_main -> NÃO pode sobrescrever guia válido
            empty_data = {k: ([] if isinstance(v, list) else "") for k, v in data.items()}
            scraper.save_to_markdown("Evanescia", empty_data, output_dir=tmpdir)
            with open(md_path, "r", encoding="utf-8") as f:
                saved_after = f.read()
            self.assertEqual(saved_before, saved_after)

    def test_genshin_reactive_crit_dps_infers_em_substat(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                os.makedirs("genshin/guias", exist_ok=True)
                os.makedirs("static_data", exist_ok=True)
                with open("static_data/hoyolab_mappings.json", "w", encoding="utf-8") as f:
                    json.dump({"genshin": {"10000098": "clorinde"}}, f)
                with open("static_data/character_aliases.json", "w", encoding="utf-8") as f:
                    json.dump({"genshin": {}}, f)
                with open("genshin/guias/clorinde.md", "w", encoding="utf-8") as f:
                    f.write(
                        "# Guia de Build - Clorinde\n"
                        "## Atributos Recomendados (Stats)\n"
                        "### Atributos Principais (Main Stats)\n"
                        "- **Ampulheta (Sands):** ATK%\n"
                        "- **Cálice (Goblet):** Bônus de Dano Electro / ATK%\n"
                        "- **Tiara (Circlet):** Dano Crítico / Taxa Crítica\n"
                    )
                import build_calculator

                build_calculator.META_DATA_CACHE.clear()
                build_calculator.generate_meta_json_from_markdown("genshin")
                meta = build_calculator.get_meta_data("genshin")
                subs = meta.get("clorinde", {}).get("substats_priority", [])
                self.assertEqual(subs, ["crit_rate", "crit_dmg", "atk_pct", "em", "er"])
            finally:
                os.chdir(orig_cwd)
                import build_calculator as bc_cleanup

                bc_cleanup.META_DATA_CACHE.clear()


if __name__ == "__main__":
    unittest.main()
