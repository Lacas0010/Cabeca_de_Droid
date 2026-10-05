import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from static_data_manager import static_data_manager
from meta_comparator import resolve_character_canonical_slug, find_best_guide_file

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CANONICAL_STAT_MAP = {
    # Ofensivos
    "crit rate": "Taxa Crítica", "crit rate%": "Taxa Crítica", "taxa critica": "Taxa Crítica", "taxa crítica": "Taxa Crítica",
    "crit dmg": "Dano Crítico", "crit dmg%": "Dano Crítico", "dano critico": "Dano Crítico", "dano crítico": "Dano Crítico",
    "atk%": "ATK%", "atk_pct": "ATK%", "atk": "ATK%", "ataque%": "ATK%",
    "speed": "Velocidade", "spd": "Velocidade", "vel": "Velocidade", "velocidade": "Velocidade",
    "elemental mastery": "Maestria Elemental", "em": "Maestria Elemental", "maestria elemental": "Maestria Elemental",
    # Defensivos e Suporte
    "hp%": "HP%", "hp_pct": "HP%", "vida%": "HP%",
    "def%": "DEF%", "def_pct": "DEF%", "defesa%": "DEF%",
    "energy recharge": "Recarga de Energia", "er": "Recarga de Energia", "recarga de energia": "Recarga de Energia",
    "energy regeneration rate": "Taxa de Regeneração de Energia", "err": "Taxa de Regeneração de Energia",
    "healing bonus": "Bônus de Cura", "bonus de cura": "Bônus de Cura", "bônus de cura": "Bônus de Cura",
    # Elementais
    "pyro dmg": "Bônus de Dano Pyro", "pyro dmg bonus": "Bônus de Dano Pyro", "dano pyro": "Bônus de Dano Pyro",
    "hydro dmg": "Bônus de Dano Hydro", "hydro dmg bonus": "Bônus de Dano Hydro", "dano hydro": "Bônus de Dano Hydro",
    "electro dmg": "Bônus de Dano Electro", "electro dmg bonus": "Bônus de Dano Electro", "dano electro": "Bônus de Dano Electro",
    "cryo dmg": "Bônus de Dano Cryo", "cryo dmg bonus": "Bônus de Dano Cryo", "dano cryo": "Bônus de Dano Cryo",
    "anemo dmg": "Bônus de Dano Anemo", "anemo dmg bonus": "Bônus de Dano Anemo", "dano anemo": "Bônus de Dano Anemo",
    "geo dmg": "Bônus de Dano Geo", "geo dmg bonus": "Bônus de Dano Geo", "dano geo": "Bônus de Dano Geo",
    "dendro dmg": "Bônus de Dano Dendro", "dendro dmg bonus": "Bônus de Dano Dendro", "dano dendro": "Bônus de Dano Dendro",
    "physical dmg": "Bônus de Dano Físico", "physical dmg bonus": "Bônus de Dano Físico", "dano fisico": "Bônus de Dano Físico", "dano físico": "Bônus de Dano Físico",
    "lightning dmg": "Bônus de Dano de Raio", "lightning dmg bonus": "Bônus de Dano de Raio",
    "fire dmg": "Bônus de Dano de Fogo", "fire dmg bonus": "Bônus de Dano de Fogo",
    "ice dmg": "Bônus de Dano de Gelo", "ice dmg bonus": "Bônus de Dano de Gelo",
    "wind dmg": "Bônus de Dano de Vento", "wind dmg bonus": "Bônus de Dano de Vento",
    "quantum dmg": "Bônus de Dano Quântico", "quantum dmg bonus": "Bônus de Dano Quântico",
    "imaginary dmg": "Bônus de Dano Imaginário", "imaginary dmg bonus": "Bônus de Dano Imaginário",
    "ether dmg": "Bônus de Dano de Éter", "ether dmg bonus": "Bônus de Dano de Éter",
    "pen ratio": "Taxa de PEN", "pen": "Taxa de PEN",
    "anomaly proficiency": "Proficiência em Anomalia", "anomaly mastery": "Controle de Anomalia"
}

def sanitize_stat_name(stat_str: str) -> str:
    """Normaliza e sanitiza um nome de atributo contra o vocabulário oficial."""
    if not stat_str:
        return "ATK%"
    clean = stat_str.strip().lower()
    clean = re.sub(r'[\*\(\)\[\]]', '', clean)
    if clean in CANONICAL_STAT_MAP:
        return CANONICAL_STAT_MAP[clean]
    for k, v in CANONICAL_STAT_MAP.items():
        if k in clean or clean in k:
            return v
    return stat_str.strip()

class AIBuildPayload(BaseModel):
    """Schema Pydantic rígido para validação de saídas estruturadas de IA."""
    character_name: str = Field(..., description="Nome oficial do personagem")
    weapons: List[str] = Field(default_factory=list, description="Lista de armas/cones recomendados")
    relic_sets: List[str] = Field(default_factory=list, description="Lista de conjuntos recomendados")
    planar_sets: List[str] = Field(default_factory=list, description="Ornamentos planares recomendados (HSR)")
    main_stats: Dict[str, str] = Field(default_factory=dict, description="Atributos principais por slot")
    sub_stats: List[str] = Field(default_factory=list, description="Subatributos prioritários")
    pros: List[str] = Field(default_factory=list, description="Pontos fortes do personagem")
    cons: List[str] = Field(default_factory=list, description="Pontos fracos do personagem")
    optimization_summary: str = Field(default="", description="Resumo de otimização de combate")

class AIBuildGenerator:
    """
    Gerador autônomo e determinístico de builds Day-1 com validação Pydantic,
    sanitização de status e rastreamento de proveniência ('ai_preliminary').
    """

    @staticmethod
    def is_ai_preliminary_guide(file_path: str) -> bool:
        """Verifica se um arquivo de guia foi gerado por IA preliminar."""
        if not file_path or not os.path.isfile(file_path):
            return False
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                head = f.read(500)
                return "ai_preliminary" in head or "Guia Preliminar" in head
        except Exception:
            return False

    @staticmethod
    def get_or_generate_guide(game_id: str, char_name: str, element: str = "") -> Optional[str]:
        """
        Garante que um guia exista para o personagem. Se não existir, gera automaticamente
        e salva no diretório de guias do jogo correspondente com proveniência explícita.
        """
        g = game_id.lower().strip()
        existing = find_best_guide_file(g, char_name, element)
        if existing and os.path.isfile(existing):
            return existing

        canonical_slug = resolve_character_canonical_slug(g, char_name, element)
        if not canonical_slug:
            canonical_slug = char_name.lower().replace(" ", "_")

        char_profile = static_data_manager.get_character_profile(g, char_name) or {}
        char_name_clean = char_profile.get("name", char_name)
        elem = element or char_profile.get("element", "Físico / Physical")
        role = char_profile.get("path") or char_profile.get("specialty") or char_profile.get("weapon") or "DPS"
        rarity = char_profile.get("rarity", 5)

        # 1. Tentar gerar com Groq Cloud estruturado se configurado
        guide_md = None
        try:
            from groq_rag import GroqRAG
            groq = GroqRAG()
            if groq.client:
                prompt = (
                    f"Você é o analista mestre de teoria e metagame de {g.upper()} (HoYoverse).\n"
                    f"Gere um JSON estrito para o personagem '{char_name_clean}' ({rarity}★, Elemento: {elem}, Classe: {role}).\n"
                    f"Retorne APENAS um JSON válido no seguinte formato:\n"
                    f"{{\n"
                    f'  "character_name": "{char_name_clean}",\n'
                    f'  "weapons": ["Opção Assinatura 5★", "Opção F2P 4★"],\n'
                    f'  "relic_sets": ["Conjunto Principal (4-PC)"],\n'
                    f'  "planar_sets": ["Ornamento Principal (2-PC)"],\n'
                    f'  "main_stats": {{"slot_1": "Taxa Crítica / Dano Crítico", "slot_2": "ATK% / Velocidade", "slot_3": "Bônus de Dano {elem}"}},\n'
                    f'  "sub_stats": ["Taxa Crítica", "Dano Crítico", "ATK%", "Velocidade"],\n'
                    f'  "pros": ["Alto dano e sinergia com times de {elem}"],\n'
                    f'  "cons": ["Requer investimento balanceado de atributos"],\n'
                    f'  "optimization_summary": "Manter proporção 1:2 de Taxa Crítica para Dano Crítico."\n'
                    f"}}"
                )

                models = [
                    "openai/gpt-oss-120b",
                    "groq/compound",
                    "groq/compound-mini",
                    "openai/gpt-oss-20b",
                    "qwen/qwen3.6-27b"
                ]
                for mod in models:
                    try:
                        resp = groq.client.chat.completions.create(
                            model=mod,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.1,
                            max_tokens=1000
                        )
                        if resp and resp.choices and resp.choices[0].message.content:
                            raw_txt = resp.choices[0].message.content.strip()
                            json_match = re.search(r'\{.*\}', raw_txt, re.DOTALL)
                            if json_match:
                                parsed = json.loads(json_match.group(0))
                                validated = AIBuildPayload(**parsed)
                                guide_md = AIBuildGenerator._build_markdown_from_payload(g, validated, elem, role)
                                break
                    except Exception:
                        continue

        except Exception as e:
            print(f"[AI_BUILD_GENERATOR] Aviso: Falha no gerador Groq ({e}). Usando fallback determinístico.")

        # 2. Se a IA estiver offline ou payload inválido, usar template determinístico seguro
        if not guide_md:
            guide_md = AIBuildGenerator._generate_template_guide(g, char_name_clean, elem, role, rarity)

        # 3. Gravação com Metadata de Proveniência
        guides_dir = os.path.join(BASE_DIR, g, "guias")
        os.makedirs(guides_dir, exist_ok=True)
        file_path = os.path.join(guides_dir, f"{canonical_slug}.md")

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(guide_md)
            print(f"[AI_BUILD_GENERATOR] Guia Day-1 gerado com sucesso [ai_preliminary]: {file_path}")

            # Atualizar cache estruturado do build_calculator
            try:
                from build_calculator import generate_meta_json_from_markdown
                generate_meta_json_from_markdown(g)
            except Exception:
                pass

            return file_path
        except Exception as err:
            print(f"[AI_BUILD_GENERATOR] Erro ao gravar guia Day-1: {err}")
            return None

    @staticmethod
    def _build_markdown_from_payload(game_id: str, p: AIBuildPayload, element: str, role: str) -> str:
        """Constrói Markdown padronizado e sanitizado a partir de um AIBuildPayload validado."""
        now_iso = datetime.now().isoformat()
        weapons_md = "\n".join([f"- **{w}** (100.00% de eficácia)" if i == 0 else f"- **{w}** (90.00% de eficácia)" for i, w in enumerate(p.weapons or ["Arma Principal 5★", "Arma F2P 4★"])])
        sets_md = "\n".join([f"- **{s}** (100.00% de eficácia)" for s in (p.relic_sets or ["Conjunto Principal (4-PC)"])])
        
        planar_md = ""
        if game_id == "hsr" and p.planar_sets:
            planar_md = "### Melhores Ornamentos Planares (2 Peças)\n" + "\n".join([f"- **{pl}** (100.00% de eficácia)" for pl in p.planar_sets]) + "\n\n"

        sanitized_sub = " > ".join([sanitize_stat_name(s) for s in p.sub_stats]) if p.sub_stats else "Taxa Crítica > Dano Crítico > ATK% > Velocidade"

        if game_id == "genshin":
            main_block = f"- Areia do Tempo: {sanitize_stat_name(p.main_stats.get('sands', p.main_stats.get('slot_1', 'ATK%')))}\n- Cálice de Eonóthemo: {sanitize_stat_name(p.main_stats.get('goblet', p.main_stats.get('slot_2', f'Bônus de Dano {element}')))}\n- Tiara de Logos: {sanitize_stat_name(p.main_stats.get('circlet', p.main_stats.get('slot_3', 'Taxa Crítica / Dano Crítico')))}"
            weapon_title = "Melhores Armas"
            sets_title = "Melhores Conjuntos de Artefatos (4 Peças)"
        elif game_id == "hsr":
            main_block = f"- Body: {sanitize_stat_name(p.main_stats.get('body', p.main_stats.get('slot_1', 'Taxa Crítica / Dano Crítico')))}\n- Feet: {sanitize_stat_name(p.main_stats.get('feet', p.main_stats.get('slot_2', 'Velocidade / ATK%')))}\n- Planar Sphere: {sanitize_stat_name(p.main_stats.get('sphere', p.main_stats.get('slot_3', f'Bônus de Dano {element}')))}\n- Link Rope: {sanitize_stat_name(p.main_stats.get('rope', p.main_stats.get('slot_4', 'ATK% / Taxa de Regeneração de Energia')))}"
            weapon_title = "Melhores Cones de Luz"
            sets_title = "Melhores Conjuntos de Relíquias (4 Peças)"
        else:
            main_block = f"- Slot 4: {sanitize_stat_name(p.main_stats.get('slot_4', p.main_stats.get('slot_1', 'Taxa Crítica / Dano Crítico')))}\n- Slot 5: {sanitize_stat_name(p.main_stats.get('slot_5', p.main_stats.get('slot_2', f'Bônus de Dano {element}')))}\n- Slot 6: {sanitize_stat_name(p.main_stats.get('slot_6', p.main_stats.get('slot_3', 'ATK% / Taxa de Regeneração de Energia')))}"
            weapon_title = "Melhores Motores-W (W-Engines)"
            sets_title = "Melhores Discos de Drive (4 Peças)"

        pros_md = "\n".join([f"- {pr}" for pr in (p.pros or [f"Alta sinergia com composições {element}."])])
        cons_md = "\n".join([f"- {cn}" for cn in (p.cons or ["Exige balanceamento de status para rendimento ótimo."])])

        return (
            f"<!-- METADATA: {{\"source\": \"ai_preliminary\", \"game_id\": \"{game_id}\", \"generated_at\": \"{now_iso}\"}} -->\n"
            f"# Guia de Build - {p.character_name}\n"
            f"> [!NOTE]\n"
            f"> **Guia Preliminar IA (Llama 3.3 / GPT-OSS)**: Gerado automaticamente no Day-1 com base nas mecânicas de {element} / {role}.\n\n"
            f"## Review\n"
            f"### Prós (Pontos Fortes)\n"
            f"{pros_md}\n\n"
            f"### Contras (Pontos Fracos)\n"
            f"{cons_md}\n\n"
            f"## Recomendações de Equipamentos\n"
            f"### {weapon_title}\n"
            f"{weapons_md}\n\n"
            f"### {sets_title}\n"
            f"{sets_md}\n\n"
            f"{planar_md}"
            f"### Atributos Recomendados (Stats)\n"
            f"#### Atributos Principais (Main Stats)\n"
            f"{main_block}\n\n"
            f"#### Subatributos Prioritários (Sub-stats)\n"
            f"{sanitized_sub}\n\n"
            f"#### Análise de Atributos e Otimização\n"
            f"{p.optimization_summary or 'Priorize atingir os breakpoints de Crítico e atributos de suporte do personagem.'}\n"
        )

    @staticmethod
    def _generate_template_guide(game_id: str, name: str, element: str, role: str, rarity: int) -> str:
        """Template determinístico inteligente baseado no arquétipo do personagem."""
        now_iso = datetime.now().isoformat()
        is_support = any(k in str(role).lower() for k in ["harmony", "harmonia", "support", "suporte", "abundance", "abundancia", "heal", "curador", "defense", "preservation"])
        
        main_stat_1 = "Recarga de Energia / HP%" if is_support else "Taxa Crítica / Dano Crítico"
        sub_stats = "Recarga de Energia > Velocidade > HP% > DEF%" if is_support else "Taxa Crítica > Dano Crítico > ATK% > Velocidade"

        if game_id == "genshin":
            main_block = f"- Areia do Tempo: {'Recarga de Energia / HP%' if is_support else 'ATK% / Recarga de Energia'}\n- Cálice de Eonóthemo: Bônus de Dano {element} / HP%\n- Tiara de Logos: {main_stat_1}"
            weapon_sec = "### Melhores Armas\n- **Arma Assinatura / 5★** (100.00% de eficácia)\n- **Opção 4★ / Favonius** (90.00% de eficácia)"
            set_sec = "### Melhores Conjuntos de Artefatos (4 Peças)\n- **Conjunto Geral Recomendado (4-PC)** (100.00% de eficácia)"
            planar_sec = ""
        elif game_id == "hsr":
            main_block = f"- Body: {main_stat_1}\n- Feet: Velocidade > ATK%\n- Planar Sphere: Bônus de Dano {element} / HP%\n- Link Rope: {'Taxa de Regeneração de Energia' if is_support else 'ATK%'}"
            weapon_sec = "### Melhores Cones de Luz\n- **Cone de Luz Assinatura** (100.00% de eficácia)\n- **Opção 4★ Alternativa** (90.00% de eficácia)"
            set_sec = "### Melhores Conjuntos de Relíquias (4 Peças)\n- **Conjunto Geral Recomendado (4-PC)** (100.00% de eficácia)"
            planar_sec = "### Melhores Ornamentos Planares (2 Peças)\n- **Ornamento Geral Recomendado (2-PC)** (100.00% de eficácia)\n"
        else:
            main_block = f"- Slot 4: {main_stat_1}\n- Slot 5: Bônus de Dano {element} / Taxa de PEN\n- Slot 6: {'Taxa de Regeneração de Energia' if is_support else 'ATK%'}"
            weapon_sec = "### Melhores Motores-W (W-Engines)\n- **Motor-W Assinatura** (100.00% de eficácia)\n- **Opção 4★ Alternativa** (90.00% de eficácia)"
            set_sec = "### Melhores Discos de Drive (4 Peças)\n- **Conjunto Geral Recomendado (4-PC)** (100.00% de eficácia)"
            planar_sec = ""

        return (
            f"<!-- METADATA: {{\"source\": \"ai_preliminary\", \"game_id\": \"{game_id}\", \"generated_at\": \"{now_iso}\"}} -->\n"
            f"# Guia de Build - {name}\n"
            f"> [!NOTE]\n"
            f"> **Guia Preliminar Automático (Day-1)**: Recomendações calibradas pelo arquétipo oficial de {element} / {role}.\n\n"
            f"## Review\n"
            f"### Prós (Pontos Fortes)\n"
            f"- Alta sinergia com composições do elemento {element}.\n"
            f"- Excelente escalamento e utilidade como {role}.\n\n"
            f"### Contras (Pontos Fracos)\n"
            f"- Exige balanceamento cuidadoso de status para atingir o potencial máximo.\n\n"
            f"## Recomendações de Equipamentos\n"
            f"{weapon_sec}\n\n"
            f"{set_sec}\n\n"
            f"{planar_sec}\n"
            f"### Atributos Recomendados (Stats)\n"
            f"#### Atributos Principais (Main Stats)\n"
            f"{main_block}\n\n"
            f"#### Subatributos Prioritários (Sub-stats)\n"
            f"{sub_stats}\n\n"
            f"#### Análise de Atributos e Otimização\n"
            f"Equilibre atributos ofensivos ou de suporte conforme o papel principal na equipe.\n"
        )
