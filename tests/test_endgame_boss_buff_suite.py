import asyncio
import copy
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import endgame_extractor
from services import endgame_service


ROOT_DIR = Path(__file__).resolve().parent.parent


class TestEndgameBossBuffSuite(unittest.TestCase):
    """Testes unitários offline da Etapa 3: ícones de chefes e buffs nos cards de endgame."""

    def setUp(self):
        endgame_service.invalidate_endgame_cache()

    def tearDown(self):
        endgame_service.invalidate_endgame_cache()

    def test_clean_hoyolab_markup_strips_tags_and_links(self):
        raw = (
            "Aumenta o ATQ em <color=#f39001>500</color> e ativa "
            "{LINK#N1101}Surto de Bravura{/LINK}.\\n<i>Efeito acumulável.</i>"
        )
        cleaned = endgame_extractor._clean_hoyolab_markup(raw)
        self.assertNotIn("<color", cleaned)
        self.assertNotIn("</color>", cleaned)
        self.assertNotIn("{LINK", cleaned)
        self.assertNotIn("<i>", cleaned)
        self.assertIn("500", cleaned)
        self.assertIn("Surto de Bravura", cleaned)
        self.assertIn("Efeito acumulável.", cleaned)

    def test_hsr_extracts_pf_buffs_and_apc_bosses_plus_buffs_all_3_sides(self):
        mock_avatar = SimpleNamespace(
            id=1308, name="Acheron", level=80, element="lightning", rarity=5, icon="https://cdn.example/acheron.png", rank=2
        )
        pf_floor = SimpleNamespace(
            name="Palavras Imaginadas (IV)",
            star_num=4,
            score=78000,
            node_1=SimpleNamespace(
                avatars=[mock_avatar],
                monsters=[],
                buff=SimpleNamespace(
                    name="Habilidade de Toque",
                    icon="https://cdn.example/pf_buff1.png",
                    description="Aumenta Dano de Perícia Suprema em <color=#f39001>40%</color>.",
                    simple_description="Acumula Valor de Bravura.",
                ),
            ),
            node_2=SimpleNamespace(
                avatars=[mock_avatar],
                monsters=[],
                buff=SimpleNamespace(
                    name="Cadência Alegre",
                    icon="https://cdn.example/pf_buff2.png",
                    description="Inflige Indulgência.",
                    simple_description="",
                ),
            ),
            node_3=SimpleNamespace(
                avatars=[mock_avatar],
                monsters=[],
                buff=SimpleNamespace(
                    name="Eco Estelar",
                    icon="https://cdn.example/pf_buff3.png",
                    description="Bônus do Lado 3.",
                    simple_description="",
                ),
            ),
        )
        apc_season = SimpleNamespace(
            begin_time=SimpleNamespace(year=2026, month=11, day=16, hour=4, minute=0),
            end_time=SimpleNamespace(year=2026, month=12, day=28, hour=4, minute=0),
            upper_boss=SimpleNamespace(name="O Condutor Sofredor", icon="https://cdn.example/boss1.png"),
            lower_boss=SimpleNamespace(name="Guia do Declínio", icon="https://cdn.example/boss2.png"),
            starward_boss=SimpleNamespace(name="Cavaleiro Prateado", icon="https://cdn.example/boss3.png"),
        )
        apc_floor = SimpleNamespace(
            name="Dificuldade 4",
            star_num=4,
            score=7200,
            node_1=SimpleNamespace(
                avatars=[mock_avatar],
                monsters=[],
                buff=SimpleNamespace(name="Hora de Magia", icon="https://cdn.example/apc_b1.png", description="Euforia +30%."),
            ),
            node_2=SimpleNamespace(
                avatars=[mock_avatar],
                monsters=[],
                buff=SimpleNamespace(name="Enervação", icon="https://cdn.example/apc_b2.png", description="Dano de Perícia +30%."),
            ),
            node_3=SimpleNamespace(
                avatars=[mock_avatar],
                monsters=[],
                buff=SimpleNamespace(name="Alegria Radiante", icon="https://cdn.example/apc_b3.png", description="Quebra +50%."),
            ),
        )

        client = MagicMock()
        client.get_starrail_characters = AsyncMock(return_value=SimpleNamespace(characters=[]))
        client.get_starrail_challenge = AsyncMock(return_value=SimpleNamespace(floors=[], seasons=[]))
        client.get_starrail_pure_fiction = AsyncMock(return_value=SimpleNamespace(floors=[pf_floor], seasons=[]))
        client.get_starrail_apc_shadow = AsyncMock(return_value=SimpleNamespace(floors=[apc_floor], seasons=[apc_season]))

        _, modes = asyncio.run(endgame_extractor.extrair_endgame_hsr_data(client, 600156277))
        by_id = {m["id"]: m for m in modes}

        # Ficção Pura
        pf_teams = by_id["pure_fiction"]["teams"]
        self.assertEqual(len(pf_teams), 3)
        self.assertEqual(pf_teams[0]["buffs"][0]["name"], "Habilidade de Toque")
        self.assertEqual(pf_teams[0]["buffs"][0]["icon"], "https://cdn.example/pf_buff1.png")
        self.assertNotIn("<color", pf_teams[0]["buffs"][0]["desc"])
        self.assertEqual(pf_teams[2]["buffs"][0]["name"], "Eco Estelar")

        # Sombra Apocalíptica
        apc_teams = by_id["apocalyptic_shadow"]["teams"]
        self.assertEqual(len(apc_teams), 3)
        self.assertEqual(apc_teams[0]["boss"]["name"], "O Condutor Sofredor")
        self.assertEqual(apc_teams[0]["boss"]["icon"], "https://cdn.example/boss1.png")
        self.assertEqual(apc_teams[1]["boss"]["name"], "Guia do Declínio")
        self.assertEqual(apc_teams[2]["boss"]["name"], "Cavaleiro Prateado")
        self.assertEqual(apc_teams[0]["buffs"][0]["name"], "Hora de Magia")
        self.assertEqual(apc_teams[2]["buffs"][0]["name"], "Alegria Radiante")

    def test_genshin_theater_extracts_blessings_cards_and_boss_from_raw_and_parsed(self):
        mock_char = SimpleNamespace(
            id=10000089, name="Furina", level=90, element="Hydro", rarity=5, icon="https://cdn.example/furina.png"
        )
        act3 = SimpleNamespace(
            round_id=3,
            medal_obtained=True,
            characters=[mock_char],
            mystery_caches=[
                SimpleNamespace(
                    name="Surpresa: Milhares de Mistérios",
                    icon="https://cdn.example/card1.png",
                    description="Aumenta escolhas em <color=#f39001>1</color>.",
                )
            ],
            wondroud_booms=[
                SimpleNamespace(
                    name="Bônus Maravilhoso: Fúria",
                    icon="https://cdn.example/boom1.png",
                    description="ATQ +20%.",
                )
            ],
        )
        parsed_theater = SimpleNamespace(
            datas=[
                SimpleNamespace(
                    has_data=True,
                    schedule=SimpleNamespace(id=28, schedule_type=1, start_time=1793520000, end_time=1796112000),
                    stats=SimpleNamespace(medal_num=10, best_record=10, difficulty=4),
                    acts=[act3],
                )
            ]
        )
        raw_theater = {
            "data": [
                {
                    "has_detail_data": True,
                    "schedule": {"schedule_id": 28},
                    "detail": {
                        "rounds_data": [
                            {
                                "round_id": 3,
                                "enemies": [
                                    {
                                        "name": "Dragarto Primordial",
                                        "icon": "https://cdn.example/boss_geovishap.png",
                                        "level": 95,
                                    }
                                ],
                                "splendour_buff": {
                                    "buffs": [
                                        {
                                            "name": "Bênção de Cristal Electro",
                                            "icon": "https://cdn.example/blessing_electro.png",
                                            "level": 3,
                                            "level_effect": [
                                                {
                                                    "name": "Nível 3",
                                                    "desc": "Dano de Cristalização <color=#f39001>+60%</color>.",
                                                }
                                            ],
                                        }
                                    ]
                                },
                                "choice_cards": [],
                                "buffs": [],
                            }
                        ]
                    },
                }
            ]
        }

        async def fake_get_theater(uid, raw=False):
            return raw_theater if raw else parsed_theater

        client = MagicMock()
        client.get_genshin_spiral_abyss = AsyncMock(return_value=SimpleNamespace(floors=[]))
        client.get_imaginarium_theater = AsyncMock(side_effect=fake_get_theater)

        _, modes = asyncio.run(endgame_extractor.extrair_endgame_genshin_data(client, 615929016))
        self.assertEqual(len(modes), 1)
        team = modes[0]["teams"][0]
        self.assertEqual(team["boss"]["name"], "Dragarto Primordial")
        self.assertEqual(team["boss"]["icon"], "https://cdn.example/boss_geovishap.png")

        buff_kinds = [b["kind"] for b in team["buffs"]]
        self.assertEqual(buff_kinds, ["blessing", "buff", "card"])
        self.assertEqual(team["buffs"][0]["level"], 3)
        self.assertIn("+60%", team["buffs"][0]["desc"])
        self.assertNotIn("<color", team["buffs"][0]["desc"])

    def test_zzz_deadly_assault_extracts_boss_and_buffs(self):
        mock_agent = SimpleNamespace(
            id=1091, name="Miyabi", level=60, element="ice", rarity="S", icon="https://cdn.example/miyabi.png", rank=0
        )
        challenge = SimpleNamespace(
            score=35000,
            star=3,
            boss=[SimpleNamespace(name="Dead End Butcher", icon="https://cdn.example/butcher.png")],
            buffs=[
                SimpleNamespace(
                    name="Frenesi de Anomalia",
                    icon="https://cdn.example/da_buff.png",
                    description="Aumenta acúmulo de Anomalia em 25%.",
                )
            ],
            agents=[mock_agent],
            bangboo=None,
        )
        client = MagicMock()
        client.get_shiyu_defense = AsyncMock(return_value=SimpleNamespace(floors=[]))
        client.get_deadly_assault = AsyncMock(
            return_value=SimpleNamespace(
                start_time=1793520000,
                end_time=1794729600,
                total_star=9,
                total_score=100000,
                challenges=[challenge],
            )
        )

        _, modes = asyncio.run(endgame_extractor.extrair_endgame_zzz_data(client, 1000135767))
        self.assertEqual(len(modes), 1)
        team = modes[0]["teams"][0]
        self.assertEqual(team["boss"]["name"], "Dead End Butcher")
        self.assertEqual(team["boss"]["icon"], "https://cdn.example/butcher.png")
        self.assertEqual(team["buffs"][0]["name"], "Frenesi de Anomalia")

    def test_endgame_service_backfills_legacy_modes_and_proxies_tactical_icons(self):
        legacy_modes = [
            {
                "id": "apocalyptic_shadow",
                "name": "Sombra Apocalíptica",
                "badge": "AS",
                "stage": "Dificuldade 4",
                "stars": 4,
                "max_stars": 4,
                "metric_label": "Pontuação",
                "metric_value": "7.200",
                "reset_at": "2099-12-28T09:00:00Z",
                "teams": [
                    {
                        "name": "Lado 1",
                        "characters": [{"id": "1308", "name": "Acheron", "level": 80, "icon": "/assets/hsr_icon.png"}],
                        "monsters": [],
                    }
                ],
            }
        ]
        tactical_payload = {
            "apocalyptic_shadow": [
                {
                    "name": "Lado 1",
                    "boss": {"name": "O Condutor Sofredor", "icon": "https://act-webstatic.hoyoverse.com/boss.png"},
                    "buffs": [
                        {
                            "name": "Hora de Magia",
                            "icon": "https://act-webstatic.hoyoverse.com/buff.png",
                            "desc": "Euforia +30%",
                            "kind": "buff",
                        }
                    ],
                }
            ]
        }

        saved_calls = []

        def fake_save(game_id, uid, modes):
            saved_calls.append((game_id, uid, copy.deepcopy(modes)))

        with (
            patch("services.endgame_service.database.get_active_uid", return_value="600156277"),
            patch(
                "services.endgame_service.database.get_endgame_data",
                return_value={"modes": copy.deepcopy(legacy_modes), "updated_at": "2026-11-24", "uid": "600156277"},
            ),
            patch("services.endgame_service.database.save_endgame_data", side_effect=fake_save),
            patch("services.endgame_service.get_roster", new=AsyncMock(return_value=[])),
            patch("services.endgame_service.get_cookies", return_value={"ltuid_v2": "1", "ltoken_v2": "x"}),
            patch("services.endgame_service._fetch_live_reset_schedules", new=AsyncMock(return_value={})),
            patch(
                "services.endgame_service.endgame_extractor.extract_endgame_tactical_meta",
                new=AsyncMock(return_value=tactical_payload),
            ),
        ):
            res = asyncio.run(endgame_service.get_endgame("hsr", lang="pt"))

        team = res["modes"][0]["teams"][0]
        self.assertEqual(team["boss"]["name"], "O Condutor Sofredor")
        self.assertTrue(team["boss"]["icon"].startswith("/api/proxy_image?url="))
        self.assertIn("&w=64&format=webp", team["boss"]["icon"])
        self.assertEqual(team["buffs"][0]["name"], "Hora de Magia")
        self.assertTrue(team["buffs"][0]["icon"].startswith("/api/proxy_image?url="))

        # Persistiu no SQLite sem URL já envelopada em proxy
        self.assertEqual(len(saved_calls), 1)
        persisted_boss_icon = saved_calls[0][2][0]["teams"][0]["boss"]["icon"]
        self.assertTrue(persisted_boss_icon.startswith("https://"))

    def test_frontend_endgame_boss_buff_markup_and_styles(self):
        endgame_js = (ROOT_DIR / "static" / "js" / "modules" / "endgame.js").read_text(encoding="utf-8")
        self.assertIn("function renderEndgameTacticalStrip", endgame_js)
        self.assertIn("endgame-boss-pill", endgame_js)
        self.assertIn("endgame-buff-chip", endgame_js)
        self.assertIn("endgame-tactical-tooltip", endgame_js)
        self.assertIn("onerror=", endgame_js)

        endgame_css = (ROOT_DIR / "static" / "css" / "endgame_strategy.css").read_text(encoding="utf-8")
        self.assertIn(".endgame-tactical-strip", endgame_css)
        self.assertIn(".endgame-boss-pill", endgame_css)
        self.assertIn(".endgame-buff-chip", endgame_css)
        self.assertIn(".endgame-tactical-tooltip", endgame_css)
        self.assertIn("@media (max-width: 768px)", endgame_css)


if __name__ == "__main__":
    unittest.main()
