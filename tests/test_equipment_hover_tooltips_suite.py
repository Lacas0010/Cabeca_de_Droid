import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database
from scrapers import equipment_effects_scraper as eq_scraper
from services import roster_service


ROOT_DIR = Path(__file__).resolve().parent.parent


class TestEquipmentHoverTooltipsSuite(unittest.TestCase):
    """Testes unitários offline para scraping, persistência, enriquecimento e hover tooltips de armas e conjuntos."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        self.orig_db = database.DATABASE_NAME
        database.DATABASE_NAME = str(self.tmp_path / "test_equip.db")
        database._DB_SCHEMA_READY_PATHS.clear()
        database.init_db()
        roster_service.invalidate_roster_cache()

    def tearDown(self) -> None:
        database.DATABASE_NAME = self.orig_db
        database._DB_SCHEMA_READY_PATHS.clear()
        roster_service.invalidate_roster_cache()
        self.tmp_dir.cleanup()

    def test_hsr_placeholder_interpolation_and_sync_offline(self) -> None:
        desc_s1 = eq_scraper.interpolate_hsr_desc(
            "Aumenta o ATQ em #1[i]% por #2[i] rodada(s) e VEL em #3[f1]%.",
            [0.24, 2, 0.065],
        )
        self.assertEqual(desc_s1, "Aumenta o ATQ em 24% por 2 rodada(s) e VEL em 6.5%.")

        fake_lc_pt = {
            "23024": {"id": "23024", "name": "Ao Véu Inalcançável", "rarity": 5, "desc": "Lore apenas"}
        }
        fake_ranks_pt = {
            "23024": {
                "id": "23024",
                "skill": "Mente Sombria",
                "desc": "Aumenta a Chance de CRIT em #1[i]%.",
                "params": [[0.12], [0.14], [0.16], [0.18], [0.20]],
            }
        }
        fake_relics_pt = {
            "117": {
                "id": "117",
                "name": "Mergulhador{F#a} Pioneir{M#o}{F#a} de Águas Mortas",
                "desc": ["Aumenta o Dano causado em 12%.", "Aumenta a Chance de CRIT em 4%."],
            }
        }
        fake_pieces_pt = {
            "61171": {"id": "61171", "set_id": "117", "name": "Capacete Pioneiro"}
        }
        fake_lc_en = {"23024": {"id": "23024", "name": "Into the Unreachable Veil"}}
        fake_relics_en = {"117": {"id": "117", "name": "Pioneer Diver of Dead Waters"}}

        def fake_fetch(urls, **kwargs):
            u = urls[0]
            if "pt/light_cones.json" in u:
                return fake_lc_pt
            if "pt/light_cone_ranks.json" in u:
                return fake_ranks_pt
            if "pt/relic_sets.json" in u:
                return fake_relics_pt
            if "pt/relics.json" in u:
                return fake_pieces_pt
            if "en/light_cones.json" in u:
                return fake_lc_en
            if "en/relic_sets.json" in u:
                return fake_relics_en
            return None

        out_file = str(self.tmp_path / "hsr_equipment_effects.json")
        with (
            patch.object(eq_scraper, "_fetch_json", side_effect=fake_fetch),
            patch.object(eq_scraper, "_fetch_hoyowiki_list", return_value=[]),
            patch.object(eq_scraper, "equipment_effects_json_path", return_value=out_file),
            patch.object(eq_scraper, "get_resource_path", return_value=out_file),
        ):
            res = eq_scraper.sync_equipment_effects(["hsr"], force=True)
            self.assertEqual(res["hsr"]["weapons"], 1)
            self.assertEqual(res["hsr"]["sets"], 1)
            self.assertTrue(os.path.exists(out_file))

            # Lookup por nome PT-BR com rank S5 e por variante masculina do conjunto
            roster_service.invalidate_roster_cache("hsr")
            w_s5 = roster_service.lookup_weapon_effect("hsr", "Ao Véu Inalcançável", rank=5)
            self.assertEqual(w_s5["passive_name"], "Mente Sombria")
            self.assertEqual(w_s5["desc"], "Aumenta a Chance de CRIT em 20%.")

            w_en = roster_service.lookup_weapon_effect("hsr", "Into the Unreachable Veil", rank=1)
            self.assertEqual(w_en["desc"], "Aumenta a Chance de CRIT em 12%.")

            s_masc = roster_service.lookup_set_effect("hsr", "Mergulhador Pioneiro de Águas Mortas")
            self.assertIn("12%", s_masc["two_pc"])
            self.assertIn("4%", s_masc["four_pc"])

    def test_genshin_and_zzz_sync_offline(self) -> None:
        fake_gi_rel = {
            "data": {
                "items": {
                    "15035": {
                        "id": 15035,
                        "name": "Coração Forjado",
                        "affixList": {"2150350": "ATQ +18%.", "2150351": "Aumenta Dano em 50%."},
                    }
                }
            }
        }
        fake_gi_weap = {"data": {"items": {"11515": {"id": 11515, "name": "Asa Gelada", "rank": 5}}}}
        fake_gi_wdet = {
            "data": {
                "affix": {
                    "111515": {
                        "name": "Cisne da Neve",
                        "upgrade": {
                            "0": "Aumenta Dano CRIT em <color=#99FFFFFF>20%</color>.",
                            "4": "Aumenta Dano CRIT em <color=#99FFFFFF>40%</color>.",
                        },
                    }
                }
            }
        }

        def fake_gi_fetch(urls, **kwargs):
            u = urls[0]
            if "/pt/reliquary" in u:
                return fake_gi_rel
            if "/pt/weapon/11515" in u:
                return fake_gi_wdet
            if "/pt/weapon" in u:
                return fake_gi_weap
            return {"data": {"items": {}}}

        gi_file = str(self.tmp_path / "genshin_equipment_effects.json")
        with (
            patch.object(eq_scraper, "_fetch_json", side_effect=fake_gi_fetch),
            patch.object(eq_scraper, "equipment_effects_json_path", return_value=gi_file),
            patch.object(eq_scraper, "get_resource_path", return_value=gi_file),
        ):
            res = eq_scraper.sync_equipment_effects(["genshin"], force=True)
            self.assertEqual(res["genshin"]["weapons"], 1)
            self.assertEqual(res["genshin"]["sets"], 1)

            roster_service.invalidate_roster_cache("genshin")
            w_r5 = roster_service.lookup_weapon_effect("genshin", "Asa Gelada", rank=5)
            self.assertEqual(w_r5["passive_name"], "Cisne da Neve")
            self.assertEqual(w_r5["desc"], "Aumenta Dano CRIT em 40%.")
            s_gi = roster_service.lookup_set_effect("genshin", "Coração Forjado")
            self.assertEqual(s_gi["two_pc"], "ATQ +18%.")
            self.assertEqual(s_gi["four_pc"], "Aumenta Dano em 50%.")

        # ZZZ split de skill 5-tuple e extração de disco via reliquary_set_effect
        p_name, p_desc, p_ranks = eq_scraper._split_zzz_wengine_skill(
            'Fogo Enjaulado<p>Fogo Enjaulado Causa mais <span style="color:green">15%/17,25%/19,5%/21,75%/24%</span> de Dano.</p>'
        )
        self.assertEqual(p_name, "Fogo Enjaulado")
        self.assertEqual(p_desc, "Causa mais 15% de Dano.")
        self.assertEqual(p_ranks["5"], "Causa mais 24% de Dano.")

        two_d, four_d = eq_scraper._extract_zzz_disc_effects_from_page(
            {
                "modules": [
                    {
                        "components": [
                            {
                                "component_id": "reliquary_set_effect",
                                "data": json.dumps(
                                    {
                                        "two_set_effect": "<p>Recuperação de Energia +20%</p>",
                                        "four_set_effect": "<p>Equipe causa +18% de dano.</p>",
                                    }
                                ),
                            }
                        ]
                    }
                ]
            }
        )
        self.assertEqual(two_d, "Recuperação de Energia +20%")
        self.assertEqual(four_d, "Equipe causa +18% de dano.")

    def test_database_roundtrip_and_roster_build_enrichment(self) -> None:
        database.save_game_account("100001", "zzz", "ProxyTest", 60, 100)
        database.save_character(
            uid="100001",
            game_id="zzz",
            char_id="1201",
            name="AgenteTesteEquip",
            level=60,
            rarity=5,
            rank_str="M0",
            element="ICE",
            icon="",
            weapon_name="Motor da Constelação",
            weapon_level=60,
            weapon_rank=1,
            weapon_icon="",
            raw_md="",
            sets_json=json.dumps(["4p Punk Hormonal", "2p Techno Baiacu"], ensure_ascii=False),
            weapon_info_json=json.dumps(
                {
                    "passive_name": "Surra do Cavaleiro",
                    "desc": "Usar Ataque de Assistência aumenta o ATQ em 12% por 12s.",
                    "main_stat": "ATQ Base 594",
                    "sub_stat": "ATQ 25%",
                },
                ensure_ascii=False,
            ),
            sets_detail_json=json.dumps(
                [
                    {
                        "label": "4p Punk Hormonal",
                        "name": "Punk Hormonal",
                        "pieces": 4,
                        "two_pc": "ATQ +10%",
                        "four_pc": "Ao entrar em combate, ATQ +25% por 10s.",
                    }
                ],
                ensure_ascii=False,
            ),
        )

        # Fallback do catálogo para o segundo conjunto (Techno Baiacu)
        fake_zzz_cat = {
            "game_id": "zzz",
            "weapons": {},
            "sets": {
                "technobaiacu": {
                    "name": "Techno Baiacu",
                    "two_pc": "Taxa de Perfuração +8%",
                    "four_pc": "Dano de Suprema +20%.",
                    "aliases": ["Puffer Electro"],
                }
            },
        }
        zzz_file = str(self.tmp_path / "zzz_equipment_effects.json")
        Path(zzz_file).write_text(json.dumps(fake_zzz_cat, ensure_ascii=False), encoding="utf-8")

        with (
            patch.object(eq_scraper, "equipment_effects_json_path", return_value=zzz_file),
            patch.object(eq_scraper, "get_resource_path", return_value=zzz_file),
        ):
            roster_service.invalidate_roster_cache("zzz")
            build = roster_service.parse_character_build_data("zzz", "AgenteTesteEquip")

            # Compatibilidade retroativa de sets (lista de strings) preservada
            self.assertEqual(build["sets"], ["4p Punk Hormonal", "2p Techno Baiacu"])

            # Arma enriquecida com passiva e stats live do SQLite
            wi = build["weapon_info"]
            self.assertEqual(wi["passive_name"], "Surra do Cavaleiro")
            self.assertIn("12%", wi["desc"])
            self.assertEqual(wi["main_stat"], "ATQ Base 594")

            # Conjuntos enriquecidos mesclando SQLite live + catálogo dinâmico
            sd = build["sets_detail"]
            self.assertEqual(len(sd), 2)
            self.assertEqual(sd[0]["name"], "Punk Hormonal")
            self.assertEqual(sd[0]["pieces"], 4)
            self.assertIn("25%", sd[0]["four_pc"])
            self.assertEqual(sd[1]["name"], "Techno Baiacu")
            self.assertEqual(sd[1]["pieces"], 2)
            self.assertEqual(sd[1]["two_pc"], "Taxa de Perfuração +8%")

    def test_frontend_weapon_and_sets_tooltip_contract(self) -> None:
        roster_js = (ROOT_DIR / "static" / "js" / "modules" / "roster.js").read_text(encoding="utf-8")
        index_html = (ROOT_DIR / "static" / "index.html").read_text(encoding="utf-8")
        style_css = (ROOT_DIR / "static" / "style.css").read_text(encoding="utf-8")

        self.assertIn('id="ins-weapon-detail"', index_html)
        self.assertIn('id="ins-weapon-hint"', index_html)
        self.assertIn("weapon-detail--interactive", roster_js)
        self.assertIn("set-item--interactive", roster_js)
        self.assertIn("build.weapon_info", roster_js)
        self.assertIn("build.sets_detail", roster_js)
        self.assertIn('weaponDetailEl.setAttribute("data-hoyo-tooltip", "true")', roster_js)
        self.assertIn('item.setAttribute("data-hoyo-tooltip", "true")', roster_js)
        self.assertIn(".weapon-detail--interactive:hover", style_css)
        self.assertIn(".set-item--interactive:hover", style_css)


if __name__ == "__main__":
    unittest.main()
