
import discord
from discord import app_commands
from discord.ext import commands
import datetime

def format_time(seconds: int):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"

class Perfil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        self.bot.tree.remove_command(self.perfil.name, type=self.perfil.type)

    async def get_user_rank(self, db: dict, user_id: str, category: str, interaction: discord.Interaction):
        """Calcula o ranking do usuário em uma categoria específica"""
        ranking_items = []
        checked_users = {}  # Cache de usuários já verificados
        
        for uid, data in db.items():
            try:
                uid_int = int(uid)
                is_bot = None
                
                # Verificar cache primeiro
                if uid in checked_users:
                    is_bot = checked_users[uid]
                else:
                    member = interaction.guild.get_member(uid_int) if interaction.guild else None
                    if member:
                        is_bot = member.bot
                        checked_users[uid] = is_bot
                    else:
                        try:
                            user = await self.bot.fetch_user(uid_int)
                            is_bot = user.bot
                            checked_users[uid] = is_bot
                        except:
                            checked_users[uid] = True  # Marcar como bot se não conseguir buscar
                            continue
                
                if not is_bot:
                    if category == "call":
                        value = data.get("tempo_total", 0)
                    elif category == "souls":
                        value = data.get("soul", 0)
                    elif category == "xp":
                        value = data.get("xp", 0)
                    else:
                        continue
                    ranking_items.append((uid, value))
            except (ValueError, discord.NotFound, discord.HTTPException):
                continue
        
        # Ordenar por valor (maior primeiro)
        ranking_items.sort(key=lambda x: x[1], reverse=True)
        
        # Encontrar posição do usuário
        for pos, (uid, _) in enumerate(ranking_items, start=1):
            if uid == user_id:
                return pos
        
        return None

    @app_commands.command(name="perfil", description="Mostra um perfil bonito e completo do usuário.")
    async def perfil(self, interaction: discord.Interaction, membro: discord.Member = None):
        # Defer early to evitar expiração do interaction
        await interaction.response.defer(thinking=False, ephemeral=False)

        membro = membro or interaction.user
        db = self.bot.db()

        user_id = str(membro.id)

        # Criar conta no DB caso não exista
        if user_id not in db:
            db[user_id] = {
                "sobre": None,
                "tempo_total": 0,
                "soul": 0,
                "xp": 0,
                "level": 1
            }
            self.bot.save_db(db)

        # SOBRE MIM
        sobre = db[user_id].get("sobre") or "❌ Nenhum Sobre Mim definido ainda."

        # TEMPO TOTAL
        tempo_total = db[user_id].get("tempo_total", 0)
        tempo_total_fmt = format_time(tempo_total)

        # TEMPO ATUAL NA CALL
        if membro.id in self.bot.active_users:
            start = self.bot.call_times.get(membro.id, datetime.datetime.now())
            elapsed = datetime.datetime.now() - start
            tempo_atual = format_time(int(elapsed.total_seconds()))
        else:
            tempo_atual = "❌ Não está em call"

        # ECONOMIA
        souls = db[user_id].get("soul", 0)
        xp = db[user_id].get("xp", 0)
        level = db[user_id].get("level", 1)

        # Calcular rankings
        rank_call = await self.get_user_rank(db, user_id, "call", interaction)
        rank_souls = await self.get_user_rank(db, user_id, "souls", interaction)
        rank_xp = await self.get_user_rank(db, user_id, "xp", interaction)

        rank_souls_text = f"#{rank_souls}" if rank_souls else "Sem ranking"
        rank_xp_text = f"#{rank_xp}" if rank_xp else "Sem ranking"

        # DADOS PARA ABA SOBRE
        # Contar itens passivos equipados
        user_inv = db.get("usuarios", {}).get(user_id, {})
        equipados = user_inv.get("equipados", {})
        buffs_ativos = len(equipados)
        
        # Contar missões completas
        missoes_completas = len(db[user_id].get("missoes_completas", []))
        
        # Contar itens no inventário
        itens_inventario = sum(user_inv.get("itens", {}).values())

        # EMBED PRINCIPAL
        embed = discord.Embed(
            title=f"👤 Perfil de {membro.display_name}",
            color=discord.Color.red()
        )

        # Avatar
        embed.set_thumbnail(url=(membro.avatar.url if membro.avatar else membro.display_avatar.url))

        # Datas da conta
        embed.add_field(
            name="<:ponto1:1430319216787066962> Conta criada em:",
            value=membro.created_at.strftime("%d/%m/%Y"),
            inline=True
        )

        embed.add_field(
            name="<:ponto1:1430319216787066962> Entrou no servidor:",
            value=membro.joined_at.strftime("%d/%m/%Y") if membro.joined_at else "Desconhecido",
            inline=True
        )

        embed.add_field(name="\u200b", value="\u200b", inline=True)

        # SOBRE MIM
        embed.add_field(
            name="<:papel:1456311322319917198> Sobre Mim:",
            value=sobre,
            inline=False
        )

        # TEMPO EM CALL (apenas atual e total)
        embed.add_field(
            name="<:microfone:1456311268439883920> Tempo em Call",
            value=f"**Atual:** {tempo_atual}",
            inline=True
        )

        embed.add_field(
            name="⏱️ Tempo Total em Call",
            value=f"**{tempo_total_fmt}**",
            inline=True
        )

        # Banner
        try:
            user = await self.bot.fetch_user(membro.id)
            if user.banner:
                embed.set_image(url=user.banner.url)
        except:
            pass

        embed.set_footer(text="Aeternum Exilium • Sistema de Perfil")

        # VIEW COM BOTÃO SOBRE
        class PerfilView(discord.ui.View):
            def __init__(self, bot_instance, member, data):
                super().__init__(timeout=180)
                self.bot = bot_instance
                self.member = member
                self.data = data
                self.showing_sobre = False
            
            @discord.ui.button(label="📊 Sobre", style=discord.ButtonStyle.primary)
            async def sobre_button(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                if button_interaction.user.id != interaction.user.id:
                    await button_interaction.response.send_message("❌ Apenas quem chamou o comando pode usar os botões!", ephemeral=True)
                    return
                
                if not self.showing_sobre:
                    # Mostrar aba Sobre
                    embed_sobre = discord.Embed(
                        title=f"📊 Sobre - {self.member.display_name}",
                        color=discord.Color.blue()
                    )
                    
                    embed_sobre.set_thumbnail(url=(self.member.avatar.url if self.member.avatar else self.member.display_avatar.url))
                    
                    # STATS
                    embed_sobre.add_field(
                        name="📈 Stats",
                        value=f"**Buffs Ativos:** {self.data['buffs_ativos']}/8\n"
                              f"**Missões Feitas:** {self.data['missoes_completas']}",
                        inline=False
                    )
                    
                    # MOCHILA
                    embed_sobre.add_field(
                        name="🎒 Mochila",
                        value=f"**Rank Souls:** {self.data['rank_souls_text']}\n"
                              f"**Moedas:** {self.data['souls']:,} 💎\n"
                              f"**Itens:** {self.data['itens_inventario']}",
                        inline=False
                    )

                    # Nível e ranks
                    embed_sobre.add_field(
                        name="⭐ Nível & XP",
                        value=f"**Nível:** {self.data['level']}\n"
                              f"**XP:** {self.data['xp']:,}\n"
                              f"**Rank XP:** {self.data['rank_xp_text']}\n"
                              f"**Rank Top Souls:** {self.data['rank_souls_text']}",
                        inline=False
                    )
                    
                    embed_sobre.set_footer(text="Aeternum Exilium • Sistema de Perfil")
                    
                    button.label = "👤 Voltar"
                    button.style = discord.ButtonStyle.secondary
                    self.showing_sobre = True
                    
                    await button_interaction.response.edit_message(embed=embed_sobre, view=self)
                else:
                    # Voltar ao perfil principal
                    button.label = "📊 Sobre"
                    button.style = discord.ButtonStyle.primary
                    self.showing_sobre = False
                    
                    await button_interaction.response.edit_message(embed=embed, view=self)

        view = PerfilView(
            self.bot,
            membro,
            {
                'buffs_ativos': buffs_ativos,
                'missoes_completas': missoes_completas,
                'rank_souls_text': rank_souls_text,
                'rank_xp_text': rank_xp_text,
                'souls': souls,
                'itens_inventario': itens_inventario,
                'level': level,
                'xp': xp
            }
        )

        await interaction.followup.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Perfil(bot))
