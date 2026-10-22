import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from fastapi.testclient import TestClient
from server import app
from build_calculator import calculate_stat_breakpoints


class TestActionBreakpointsSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_hsr_speed_breakpoints_and_action_value(self):
        """Valida o cálculo de Action Value (10000/SPD) e ciclos de MoC em HSR."""
        stats = {"speed": 135.2, "crit_rate": 72.0, "crit_dmg": 145.0}
        res = calculate_stat_breakpoints("hsr", "Acheron", stats)

        self.assertEqual(res["game_id"], "hsr")
        self.assertIsNotNone(res["speed_action_value"])
        self.assertAlmostEqual(res["speed_action_value"], 74.0, delta=0.5)
        self.assertIn("Ciclo 0", res["cycles_summary"])
        self.assertIn("2 Ação", res["cycles_summary"])

        spd_bp = next(b for b in res["breakpoints"] if "SPD" in b["stat"])
        self.assertTrue(spd_bp["is_reached"])
        self.assertIn("134.0 SPD", spd_bp["status"])
        self.assertIn("143.0 SPD", spd_bp["next_goal"])

    def test_hsr_speed_tuning_tips(self):
        """Valida orientações táticas de Speed Tuning para Bronya, Sparkle e Robin."""
        # 1. Bronya (-1 SPD Tuning)
        bronya_res = calculate_stat_breakpoints("hsr", "Bronya", {"speed": 134.0})
        bronya_spd = next(b for b in bronya_res["breakpoints"] if "SPD" in b["stat"])
        self.assertIn("-1 SPD", bronya_spd["speed_tuning_tip"])

        # 2. Sparkle (160.1+ Hyper Speed)
        sparkle_res = calculate_stat_breakpoints("hsr", "Sparkle", {"speed": 161.4})
        sparkle_spd = next(b for b in sparkle_res["breakpoints"] if "SPD" in b["stat"])
        self.assertIn("Hyper-Speed", sparkle_spd["speed_tuning_tip"])
        self.assertIn("160.1 SPD", sparkle_spd["status"])

        # 3. Robin (Vonwacq Tuning)
        robin_res = calculate_stat_breakpoints("hsr", "Robin", {"speed": 122.0})
        robin_spd = next(b for b in robin_res["breakpoints"] if "SPD" in b["stat"])
        self.assertIn("Vonwacq", robin_spd["speed_tuning_tip"])

    def test_genshin_energy_recharge_and_favonius_check(self):
        """Valida metas de Recarga por personagem e checagem de arma Favonius em Genshin."""
        # Xiangling abaixo da meta (170% < 200%)
        stats_bad = {"er": 170.0, "crit_rate": 50.0, "crit_dmg": 100.0}
        res_bad = calculate_stat_breakpoints("genshin", "Xiangling", stats_bad)
        er_bad = next(b for b in res_bad["breakpoints"] if "ER" in b["stat"])
        self.assertFalse(er_bad["is_reached"])
        self.assertIn("Faltam 30.0% de ER", er_bad["next_goal"])

        # Bennett com Taxa Crítica muito baixa para Favonius Proc (< 40%)
        stats_bennett = {"er": 210.0, "crit_rate": 22.0, "crit_dmg": 80.0}
        res_bennett = calculate_stat_breakpoints("genshin", "Bennett", stats_bennett)
        fav_bp = next((b for b in res_bennett["breakpoints"] if "Favonius" in b["stat"]), None)
        self.assertIsNotNone(fav_bp)
        self.assertFalse(fav_bp["is_reached"])
        self.assertIn("40% - 50%", fav_bp["status"])

    def test_zzz_anomaly_and_impact_breakpoints(self):
        """Valida limiares de Proficiência em Anomalia (Jane Doe) e Impacto (Stunner) no ZZZ."""
        # Jane Doe com 425 AP (acima do cap de 420)
        jane_res = calculate_stat_breakpoints("zzz", "Jane Doe", {"ap": 425.0})
        ap_bp = next(b for b in jane_res["breakpoints"] if "Anomalia" in b["stat"])
        self.assertTrue(ap_bp["is_reached"])
        self.assertIn("100% Taxa CRIT", ap_bp["status"])

        # Qingyi com 142 Impacto
        qingyi_res = calculate_stat_breakpoints("zzz", "Qingyi", {"impact": 142.0})
        imp_bp = next(b for b in qingyi_res["breakpoints"] if "Impacto" in b["stat"])
        self.assertTrue(imp_bp["is_reached"])

    def test_crit_ratio_1_2_balance(self):
        """Valida cálculo da proporção áurea de dano crítico 1:2."""
        # Equilibrado (1:2)
        res_ok = calculate_stat_breakpoints("hsr", "Seele", {"crit_rate": 70.0, "crit_dmg": 140.0})
        crit_bp = next(b for b in res_ok["breakpoints"] if "1:2" in b["stat"])
        self.assertTrue(crit_bp["is_reached"])
        self.assertIn("Proporção Áurea", crit_bp["status"])

        # Desequilibrado (1:5.5)
        res_skewed = calculate_stat_breakpoints("hsr", "Seele", {"crit_rate": 35.0, "crit_dmg": 195.0})
        crit_skewed = next(b for b in res_skewed["breakpoints"] if "1:2" in b["stat"])
        self.assertFalse(crit_skewed["is_reached"])
        self.assertIn("Taxa CRIT", crit_skewed["next_goal"])

    def test_api_stats_breakpoints_endpoint(self):
        """Valida que o endpoint POST /api/stats/breakpoints retorna o contrato correto."""
        payload = {"game_id": "hsr", "char_name": "Sparkle", "stats": {"spd": 160.5, "crit_dmg": 210.0, "ehr": 12.0}}
        response = self.client.post("/api/stats/breakpoints", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["char_name"], "Sparkle")
        self.assertEqual(data["game_id"], "hsr")
        self.assertGreater(len(data["breakpoints"]), 0)
        self.assertIn("Sparkle", data["breakpoints"][0]["speed_tuning_tip"])


if __name__ == "__main__":
    unittest.main()
