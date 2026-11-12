import unittest
import os
import re

class TestRosterViewModeSuite(unittest.TestCase):
    """
    Suíte de testes unitários para a alternância entre modo Grade (Grid)
    e modo Lista (List) na visualização dos personagens do Roster.
    """

    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.html_path = os.path.join(self.base_dir, "static", "index.html")
        self.css_path = os.path.join(self.base_dir, "static", "style.css")
        self.roster_path = os.path.join(self.base_dir, "static", "js", "modules", "roster.js")
        self.i18n_path = os.path.join(self.base_dir, "static", "js", "modules", "i18n.js")
        self.app_path = os.path.join(self.base_dir, "static", "js", "app.js")

    def test_html_view_mode_toggle_buttons_exist(self):
        """Valida se o HTML define os botões de alternância de modo Grade/Lista para os 3 jogos."""
        with open(self.html_path, "r", encoding="utf-8") as f:
            html = f.read()

        for game in ["zzz", "genshin", "hsr"]:
            self.assertIn(f'class="view-mode-toggle" data-game="{game}"', html)
            self.assertIn(f'data-mode="grid" data-game="{game}"', html)
            self.assertIn(f'data-mode="list" data-game="{game}"', html)

        self.assertIn('data-i18n-title="view_mode_grid"', html)
        self.assertIn('data-i18n-title="view_mode_list"', html)

    def test_css_list_view_and_toggle_styles_exist(self):
        """Valida as regras de estilo CSS para a visualização em lista, botões e responsividade mobile."""
        with open(self.css_path, "r", encoding="utf-8") as f:
            css = f.read()

        self.assertIn(".view-mode-toggle", css)
        self.assertIn(".view-mode-btn", css)
        self.assertIn(".character-gallery.list-view", css)
        self.assertIn(".char-card.char-list-row", css)
        self.assertIn(".char-list-col-main", css)
        self.assertIn(".char-list-avatar-wrap", css)
        self.assertIn(".char-list-col-weapon", css)
        self.assertIn(".char-list-col-actions", css)

        # Valida que as cores dos elementos nas bordas da lista foram definidas
        self.assertIn(".char-card.char-list-row.el-fire", css)
        self.assertIn(".char-card.char-list-row.el-ice", css)
        self.assertIn(".char-card.char-list-row.el-wind", css)
        self.assertIn(".char-card.char-list-row.el-electric", css)

        # Valida responsividade no mobile (<= 768px)
        self.assertIn(".char-list-col-weapon", css)
        self.assertIn("@media (max-width: 768px)", css)

    def test_roster_js_view_mode_logic_implemented(self):
        """Valida que roster.js implementa o armazenamento e alternância de modo sem recarregar rede."""
        with open(self.roster_path, "r", encoding="utf-8") as f:
            js = f.read()

        self.assertIn("currentRosterViewMode", js)
        self.assertIn("setupRosterViewModeToggle", js)
        self.assertIn("setRosterViewMode", js)
        self.assertIn("roster_view_mode", js)
        self.assertIn("char-list-row", js)
        self.assertIn("window.setupRosterViewModeToggle = setupRosterViewModeToggle", js)
        self.assertIn("window.setRosterViewMode = setRosterViewMode", js)

    def test_i18n_translation_keys_exist(self):
        """Valida se as novas chaves de tradução estão presentes em PT e EN."""
        with open(self.i18n_path, "r", encoding="utf-8") as f:
            code = f.read()

        pt_match = re.search(r"pt:\s*\{(.*?)\n\s*\},?\s*en:\s*\{", code, re.DOTALL)
        en_match = re.search(r"en:\s*\{(.*?)\n\s*\}\s*\};", code, re.DOTALL)
        self.assertIsNotNone(pt_match)
        self.assertIsNotNone(en_match)

        self.assertIn("view_mode_grid", pt_match.group(1))
        self.assertIn("view_mode_list", pt_match.group(1))
        self.assertIn("view_mode_grid", en_match.group(1))
        self.assertIn("view_mode_list", en_match.group(1))

    def test_app_js_initializes_toggle(self):
        """Valida se app.js chama setupRosterViewModeToggle na inicialização."""
        with open(self.app_path, "r", encoding="utf-8") as f:
            app_js = f.read()

        self.assertIn("setupRosterViewModeToggle", app_js)

    def test_option_c_css_rich_columns_defined(self):
        """Valida que todos os seletores CSS do modo lista Opção C (Arma com icon, Status de combate, Sets e Grade) existem."""
        with open(self.css_path, "r", encoding="utf-8") as f:
            css = f.read()

        # Coluna 2: Arma com ícone oficial e raridade
        self.assertIn(".char-list-weapon-wrap", css)
        self.assertIn(".char-list-weapon-icon-box", css)
        self.assertIn(".char-list-weapon-icon-box.rarity-5", css)
        self.assertIn(".char-list-weapon-icon-box.rarity-4", css)

        # Coluna 3: Relíquias / Artefatos / Discos (ícones das peças equipadas)
        self.assertIn(".char-list-col-relics", css)
        self.assertIn(".char-relics-strip", css)
        self.assertIn(".char-relic-piece-box", css)
        self.assertIn(".char-relic-piece-box.grade-sss", css)
        self.assertIn(".char-relic-piece-box.grade-s", css)
        self.assertIn(".char-relic-piece-box.slot-empty", css)

        # Coluna 4: Conjuntos de relíquias (4p, 2p) e slots equipados
        self.assertIn(".char-list-col-sets", css)
        self.assertIn(".char-sets-tags", css)
        self.assertIn(".char-set-tag", css)
        self.assertIn(".char-relic-slots-bar", css)
        self.assertIn(".char-relic-dots", css)
        self.assertIn(".char-relic-dot.filled", css)

        # Coluna 5: Roll Value Grade e botão de Inspecionar
        self.assertIn(".char-list-col-actions", css)
        self.assertIn(".char-list-grade-wrap", css)
        self.assertIn(".char-list-btn-inspect", css)
        self.assertIn(".char-list-chevron", css)

        # Responsividade tablet (1024px) e mobile (768px)
        self.assertIn("@media (max-width: 1024px)", css)
        self.assertIn(".char-list-col-sets", css)
        self.assertIn(".char-list-col-stats", css)

    def test_option_c_extractors_and_rendering_in_roster_js(self):
        """Valida se os helpers de extração da Opção C e a geração dos 5 blocos estão no roster.js."""
        with open(self.roster_path, "r", encoding="utf-8") as f:
            js = f.read()

        # Funções extratoras
        self.assertIn("function extractRosterWeapon", js)
        self.assertIn("function extractRosterKeyStats", js)
        self.assertIn("function extractRosterSets", js)
        self.assertIn("function extractRosterRelicPieces", js)
        self.assertIn("window.extractRosterWeapon = extractRosterWeapon", js)
        self.assertIn("window.extractRosterKeyStats = extractRosterKeyStats", js)
        self.assertIn("window.extractRosterSets = extractRosterSets", js)
        self.assertIn("window.extractRosterRelicPieces = extractRosterRelicPieces", js)

        # Renderização das 5 colunas
        self.assertIn("char-list-col-main", js)
        self.assertIn("char-list-col-weapon", js)
        self.assertIn("char-list-col-relics", js)
        self.assertIn("char-list-col-sets", js)
        self.assertIn("char-list-col-actions", js)
        self.assertIn("char-list-weapon-icon-box", js)
        self.assertIn("char-relics-strip", js)
        self.assertIn("char-relic-piece-box", js)
        self.assertIn("char-sets-tags", js)
        self.assertIn("char-relic-dots", js)
        self.assertIn("char-list-btn-inspect", js)

    def test_parse_sets_from_raw_md_mechanics(self):
        """Valida que parse_sets_from_raw_md descarta peças avulsas (1 peça) e preserva nomes oficiais completos."""
        import database

        # Caso HSR (4p + 2p)
        md_hsr = "- **Relíquias:** Profeta de Alcance Distante (4 peças) + Vonwacq Vivaz (2 peças)"
        sets_hsr = database.parse_sets_from_raw_md(md_hsr)
        self.assertEqual(sets_hsr, ["4p Profeta de Alcance Distante", "2p Vonwacq Vivaz"])

        # Caso Genshin (4p com 1 peça avulsa descartada)
        md_genshin = "- **Artefatos:** Coração Forjado (4 peças) + Selo da Insulação (1 peças)"
        sets_genshin = database.parse_sets_from_raw_md(md_genshin)
        self.assertEqual(sets_genshin, ["4p Coração Forjado"])

        # Caso ZZZ (4p + 2p)
        md_zzz = "- **Discos:** Metal do Pica-Pau (4 peças) + Punk Hormonal (2 peças)"
        sets_zzz = database.parse_sets_from_raw_md(md_zzz)
        self.assertEqual(sets_zzz, ["4p Metal do Pica-Pau", "2p Punk Hormonal"])

        # Caso vazio / sem peças
        self.assertEqual(database.parse_sets_from_raw_md(""), [])
        self.assertEqual(database.parse_sets_from_raw_md("- **Relíquias:** Nenhuma relíquia equipada"), [])

    def test_get_weapon_rarity_resolution(self):
        """Valida que get_weapon_rarity identifica corretamente 5★, 4★, 3★ e 1★ nos manifestos dos 3 jogos."""
        import database

        # HSR (Cones de Luz)
        self.assertEqual(database.get_weapon_rarity("hsr", "Euforia Repleta de Bênçãos"), 5)
        self.assertEqual(database.get_weapon_rarity("hsr", "Luzes Noturnas"), 5)
        self.assertEqual(database.get_weapon_rarity("hsr", "Na Noite"), 5)
        self.assertEqual(database.get_weapon_rarity("hsr", "Jogo de Espadas"), 4)
        self.assertEqual(database.get_weapon_rarity("hsr", "Morte Mútua"), 3)

        # Genshin (Armas)
        self.assertEqual(database.get_weapon_rarity("genshin", "Asa Gelada do Lago Branco"), 5)
        self.assertEqual(database.get_weapon_rarity("genshin", "Lira do Tecedor da Luz"), 5)
        self.assertEqual(database.get_weapon_rarity("genshin", "Farpa"), 4)
        self.assertEqual(database.get_weapon_rarity("genshin", "Espadão do Julgamento"), 1)

        # ZZZ (Motores W)
        self.assertEqual(database.get_weapon_rarity("zzz", "Motor da Constelação"), 4)
        self.assertEqual(database.get_weapon_rarity("zzz", "Perfuratriz - Eixo Vermelho"), 4)
        self.assertEqual(database.get_weapon_rarity("zzz", "Espinhaço Afiado"), 5)
        self.assertEqual(database.get_weapon_rarity("zzz", "Estopim de Enxofre"), 5)
        self.assertEqual(database.get_weapon_rarity("zzz", "The Brimstone"), 5)
        self.assertEqual(database.get_weapon_rarity("zzz", "[Lunar] Plenilúnio"), 3)

    def test_relic_piece_box_css_rarity_classes(self):
        """Valida se o CSS define estilizações por raridade para peças de relíquias/discos."""
        with open(self.css_path, "r", encoding="utf-8") as f:
            css = f.read()

        self.assertIn(".char-relic-piece-box.rarity-5", css)
        self.assertIn(".char-relic-piece-box.rarity-4", css)
        self.assertIn(".char-relic-piece-box.rarity-3", css)


if __name__ == "__main__":
    unittest.main()
