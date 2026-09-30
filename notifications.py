import os
import json
import datetime
from typing import Dict, Any, List, Optional
from curl_cffi import requests

class NotificationService:
    def __init__(self):
        self._energy_alert_tracker: Dict[str, bool] = {}

    def send_discord_webhook(
        self,
        webhook_url: str,
        title: str,
        description: str,
        color: int = 0x38bdf8,
        fields: Optional[List[Dict[str, Any]]] = None,
        footer_text: str = "Cabeça de Droid • HoYo Assistant v4.5"
    ) -> Dict[str, Any]:
        """
        Envia uma mensagem rica com Embed para o Webhook do Discord.
        """
        if not webhook_url or not webhook_url.startswith("https://discord.com/api/webhooks/"):
            return {"success": False, "error": "URL de Webhook do Discord inválida."}

        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "footer": {"text": footer_text},
            "fields": fields or []
        }

        payload = {
            "username": "Cabeça de Droid (HoYoBot)",
            "avatar_url": "https://act.hoyolab.com/app/community-game-records/images/favicon.ico",
            "embeds": [embed]
        }

        try:
            resp = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            if resp.status_code in (200, 204):
                return {"success": True, "status_code": resp.status_code}
            else:
                return {
                    "success": False,
                    "status_code": resp.status_code,
                    "error": f"Discord respondeu com HTTP {resp.status_code}: {resp.text}"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_telegram_message(
        self,
        bot_token: str,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML"
    ) -> Dict[str, Any]:
        """
        Envia uma mensagem formatada para o Chat ID configurado através do Telegram Bot API.
        """
        if not bot_token or not chat_id:
            return {"success": False, "error": "Bot Token ou Chat ID do Telegram não informados."}

        url = f"https://api.telegram.org/bot{bot_token.strip()}/sendMessage"
        payload = {
            "chat_id": chat_id.strip(),
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }

        try:
            resp = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            data = resp.json() if resp.text else {}
            if resp.status_code == 200 and data.get("ok"):
                return {"success": True}
            else:
                err_desc = data.get("description") or resp.text
                return {"success": False, "status_code": resp.status_code, "error": err_desc}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_notification(
        self,
        title: str,
        message: str,
        config: Dict[str, Any],
        color: int = 0x38bdf8,
        fields: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Despacha a notificação para todos os canais configurados e ativos (Discord e/ou Telegram).
        """
        results = {
            "discord": {"attempted": False, "success": False},
            "telegram": {"attempted": False, "success": False}
        }

        if not config.get("notifications_enabled", False):
            return {"status": "disabled", "message": "Notificações desativadas nas configurações.", "results": results}

        discord_url = (config.get("discord_webhook_url") or "").strip()
        if discord_url:
            results["discord"]["attempted"] = True
            disc_res = self.send_discord_webhook(
                webhook_url=discord_url,
                title=title,
                description=message,
                color=color,
                fields=fields
            )
            results["discord"].update(disc_res)

        tg_token = (config.get("telegram_bot_token") or "").strip()
        tg_chat = (config.get("telegram_chat_id") or "").strip()
        if tg_token and tg_chat:
            results["telegram"]["attempted"] = True
            # Formatação HTML para o Telegram
            tg_text = f"<b>🤖 {title}</b>\n\n{message}"
            if fields:
                tg_text += "\n"
                for f in fields:
                    tg_text += f"\n• <b>{f.get('name', '')}</b>: {f.get('value', '')}"
            tg_text += "\n\n<i>— Cabeça de Droid v4.5</i>"

            tg_res = self.send_telegram_message(
                bot_token=tg_token,
                chat_id=tg_chat,
                text=tg_text
            )
            results["telegram"].update(tg_res)

        return {"status": "sent", "results": results}

    def test_channels(self, discord_url: str, tg_token: str, tg_chat: str) -> Dict[str, Any]:
        """
        Dispara mensagens de teste independentes para validar as credenciais do Discord e Telegram.
        """
        test_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        res = {
            "discord": {"attempted": False, "success": False, "message": "Não configurado"},
            "telegram": {"attempted": False, "success": False, "message": "Não configurado"}
        }

        if discord_url and discord_url.strip():
            res["discord"]["attempted"] = True
            d_res = self.send_discord_webhook(
                webhook_url=discord_url.strip(),
                title="🔔 Teste de Notificação • Cabeça de Droid",
                description=f"Suas notificações do Discord foram configuradas com sucesso!\nO assistente está pronto para enviar alertas em segundo plano.",
                color=0x10b981,
                fields=[
                    {"name": "Status do Servidor", "value": "🟢 Online & Blindado", "inline": True},
                    {"name": "Data/Hora", "value": test_time, "inline": True}
                ]
            )
            res["discord"]["success"] = d_res.get("success", False)
            res["discord"]["message"] = "Notificação de teste enviada com sucesso ao Discord!" if d_res.get("success") else d_res.get("error", "Erro ao enviar.")

        if tg_token and tg_token.strip() and tg_chat and tg_chat.strip():
            res["telegram"]["attempted"] = True
            t_text = (
                f"🔔 <b>Teste de Notificação • Cabeça de Droid</b>\n\n"
                f"Seu bot do Telegram foi conectado com sucesso ao servidor!\n\n"
                f"• <b>Status:</b> 🟢 Online & Blindado\n"
                f"• <b>Data/Hora:</b> {test_time}\n\n"
                f"<i>O assistente agora te notificará automaticamente sobre Resina cheia, Check-in diário e Códigos novos.</i>"
            )
            t_res = self.send_telegram_message(
                bot_token=tg_token.strip(),
                chat_id=tg_chat.strip(),
                text=t_text
            )
            res["telegram"]["success"] = t_res.get("success", False)
            res["telegram"]["message"] = "Notificação de teste enviada com sucesso ao Telegram!" if t_res.get("success") else t_res.get("error", "Erro ao enviar.")

        return res

    def notify_checkin_summary(self, logs: List[Dict[str, Any]], config: Dict[str, Any]) -> None:
        """
        Dispara resumo do check-in diário caso tenha ocorrido sucesso ou alerta relevante.
        """
        if not config.get("notifications_enabled") or not config.get("notify_on_checkin", True):
            return

        if not logs:
            return

        claimed = [l for l in logs if l.get("status") == "SUCCESS"]
        errors = [l for l in logs if l.get("status") == "ERROR"]

        # Se todas já tinham sido resgatadas e não houve novos resgates nem erros, podemos ignorar para evitar spam
        if not claimed and not errors:
            return

        game_names = {"hsr": "Honkai: Star Rail", "genshin": "Genshin Impact", "zzz": "Zenless Zone Zero"}
        title = "🎁 Resumo do Auto-Check-in Diário"
        
        fields = []
        for l in logs:
            g_name = game_names.get(l.get("game_id", ""), l.get("game_id", "").upper())
            status_icon = "✅" if l.get("status") == "SUCCESS" else ("ℹ️" if l.get("status") == "ALREADY_CLAIMED" else "❌")
            fields.append({
                "name": f"{status_icon} {g_name} (UID: {l.get('uid', '—')})",
                "value": l.get("message", "Sem detalhes."),
                "inline": False
            })

        color = 0x10b981 if claimed and not errors else (0xef4444 if errors else 0x38bdf8)
        desc = "O assistente executou a rotina de check-in automático diário nas suas contas da HoYoverse:"
        
        self.send_notification(
            title=title,
            message=desc,
            config=config,
            color=color,
            fields=fields
        )

    def check_energy_and_alert(
        self,
        daily_notes: Dict[str, Dict[str, Any]],
        config: Dict[str, Any]
    ) -> None:
        """
        Verifica o nível de energia/resina/bateria de cada jogo e dispara alertas
        quando atingir o limite configurado (ex: >= 90%), sem enviar spam repetido.
        """
        if not config.get("notifications_enabled") or not config.get("notify_on_energy_cap", True):
            return

        threshold_pct = config.get("energy_cap_threshold_pct", 90)
        game_names = {"hsr": "Honkai: Star Rail (Poder de Desbravamento)", "genshin": "Genshin Impact (Resina)", "zzz": "Zenless Zone Zero (Bateria)"}

        for game_id, data in daily_notes.items():
            curr = data.get("current_energy", 0)
            max_val = data.get("max_energy", 240)
            uid = data.get("uid", "default")
            tracker_key = f"{game_id}_{uid}"

            if max_val <= 0:
                continue

            pct = (curr / max_val) * 100

            # Se atingiu o limite e ainda não alertou nesta rodada
            if pct >= threshold_pct:
                if not self._energy_alert_tracker.get(tracker_key, False):
                    self._energy_alert_tracker[tracker_key] = True
                    rec_time = data.get("recovery_time") or "Em breve"
                    g_label = game_names.get(game_id, game_id.upper())

                    title = f"🔋 Alerta de Energia: {game_id.upper()} Quase Cheia!"
                    desc = f"Sua energia em <b>{g_label}</b> atingiu <b>{curr}/{max_val}</b> ({pct:.0f}%)."
                    
                    fields = [
                        {"name": "Conta / UID", "value": str(uid), "inline": True},
                        {"name": "Tempo p/ Recuperação Total", "value": str(rec_time), "inline": True},
                        {"name": "Dica de Otimização", "value": "Gaste sua energia nos domínios do dia para evitar desperdício de recarga!", "inline": False}
                    ]

                    self.send_notification(
                        title=title,
                        message=desc,
                        config=config,
                        color=0xf59e0b,
                        fields=fields
                    )
            # Se o jogador gastou energia (caiu para < threshold - 15%), resetamos a trava para poder alertar no próximo ciclo
            elif pct < (threshold_pct - 15):
                self._energy_alert_tracker[tracker_key] = False

    def notify_promo_codes(
        self,
        game_id: str,
        redeemed_codes: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> None:
        """
        Envia notificação quando novos códigos promocionais são resgatados automaticamente na conta.
        """
        if not config.get("notifications_enabled") or not config.get("notify_on_codes", True):
            return

        if not redeemed_codes:
            return

        game_names = {"hsr": "Honkai: Star Rail", "genshin": "Genshin Impact", "zzz": "Zenless Zone Zero"}
        g_name = game_names.get(game_id.lower(), game_id.upper())

        title = f"🎁 Novos Códigos Promocionais Resgatados! ({g_name})"
        desc = f"O assistente detectou e resgatou automaticamente <b>{len(redeemed_codes)} novo(s) código(s)</b> na sua conta de <b>{g_name}</b>:"

        fields = []
        for c in redeemed_codes:
            code_str = c.get("code", "")
            rewards_str = c.get("rewards", "") or c.get("message", "Resgatado")
            fields.append({
                "name": f"💎 Código: {code_str}",
                "value": str(rewards_str),
                "inline": False
            })

        self.send_notification(
            title=title,
            message=desc,
            config=config,
            color=0xf59e0b,
            fields=fields
        )

    def generate_morning_briefing(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Gera um relatório executivo matinal unificado consolidando:
        - Estado de energia/resina dos 3 jogos
        - Status do Check-in diário
        - Ordem de serviço do dia (domínios e farm recomendados)
        - Metas de banners e gacha forecast ativas
        - Dica de ouro de síntese de relíquias
        """
        import database
        from build_calculator import generate_daily_farm_order, recommend_relic_crafting

        now_dt = datetime.datetime.now()
        date_str = now_dt.strftime("%d/%m/%Y")
        weekday_names = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
        weekday_str = weekday_names[now_dt.weekday()]

        # 1. Status de Energia e Check-in
        game_statuses = []
        for g, g_name, icon in [("hsr", "Honkai: Star Rail", "🚂"), ("genshin", "Genshin Impact", "✨"), ("zzz", "Zenless Zone Zero", "⚡")]:
            roster = database.get_roster_data(g)
            farm_order = generate_daily_farm_order(g, current_energy=180, roster=roster)
            top_task = farm_order["tasks"][0]["description"] if farm_order["tasks"] else "Farm livre / Cálice Dourado"

            game_statuses.append({
                "game_id": g,
                "game_name": g_name,
                "icon": icon,
                "characters_count": len(roster),
                "top_task": top_task,
                "domain_type": farm_order["tasks"][0]["type_label"] if farm_order["tasks"] else "Livre"
            })

        # 2. Metas de Gacha Forecast
        active_goals = database.get_gacha_goals()
        goals_summary = []
        for goal in active_goals[:3]:
            goals_summary.append({
                "character_name": goal.get("character_name", ""),
                "target_rank_str": goal.get("target_rank_str", "E0"),
                "success_rate": goal.get("success_rate", 0),
                "target_days": goal.get("target_days", 21)
            })

        # 3. Dica de Síntese
        craft_hsr = recommend_relic_crafting("hsr", database.get_roster_data("hsr"))
        top_craft = craft_hsr["recommendations"][0] if craft_hsr.get("recommendations") else None

        # 4. Formatações para Envio
        discord_fields = []
        
        # Campo de Farm do Dia
        farm_desc_lines = []
        for gs in game_statuses:
            farm_desc_lines.append(f"**{gs['icon']} {gs['game_name']}:** {gs['top_task']}")
        discord_fields.append({
            "name": "🎯 Roteiro de Farm Prioritário Hoje",
            "value": "\n".join(farm_desc_lines),
            "inline": False
        })

        # Campo de Metas de Banner
        if goals_summary:
            goals_lines = []
            for g in goals_summary:
                goals_lines.append(f"• **{g['character_name']} ({g['target_rank_str']}):** {g['success_rate']}% chance projetada (em {g['target_days']} dias)")
            discord_fields.append({
                "name": "🔮 Metas de Gacha Forecast",
                "value": "\n".join(goals_lines),
                "inline": False
            })

        # Campo de Dica de Síntese
        if top_craft:
            discord_fields.append({
                "name": "💎 Dica de Síntese & Resina Automodeladora",
                "value": f"**{top_craft['character_name']}** -> Fabricar **{top_craft['slot_name']}** ({top_craft['recommended_main_stat']}) no set *{top_craft['target_set_name']}*.\n*Ganho: {top_craft['expected_gain']}*",
                "inline": False
            })

        title = f"☀️ Morning Briefing • {weekday_str} ({date_str})"
        desc = "Seu resumo diário automatizado do <b>Cabeça de Droid</b> com prioridades de energia, farm e metas de gacha:"

        return {
            "title": title,
            "date": date_str,
            "weekday": weekday_str,
            "description": desc,
            "games": game_statuses,
            "gacha_goals": goals_summary,
            "top_craft": top_craft,
            "discord_fields": discord_fields
        }

    def send_morning_briefing(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Envia o Morning Briefing para Discord e/ou Telegram."""
        briefing = self.generate_morning_briefing(config)

        res = self.send_notification(
            title=briefing["title"],
            message=briefing["description"],
            config=config,
            color=0x38bdf8,
            fields=briefing["discord_fields"]
        )
        return {"briefing": briefing, "delivery": res}


notifier = NotificationService()

