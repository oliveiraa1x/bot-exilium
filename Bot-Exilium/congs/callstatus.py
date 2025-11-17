# cogs/callstatus.py
import discord
from discord import app_commands
from discord.ext import commands
import datetime
from typing import List, Tuple

class CallStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="call-status", description="Mostra quem está em call e há quanto tempo.")
    async def call_status(self, interaction: discord.Interaction):
        # Acessa as estruturas globais que o main.py expõe ao bot
        call_times = getattr(self.bot, "call_times", {})
        active_users = getattr(self.bot, "active_users", set())

        if not active_users:
            await interaction.response.send_message("🔕 Ninguém está em call no momento.", ephemeral=True)
            return

        # Monta lista de (member_display, tempo_segundos) para ordenar
        entries: List[Tuple[str, int, discord.Member]] = []

        for user_id in active_users:
            # tenta obter o membro no guild atual
            member = interaction.guild.get_member(user_id) if interaction.guild else None

            # se não achou como Member (pode ser usuário de outro guild ou fora do cache),
            # tenta buscar via fetch_user para ao menos mostrar o nome
            if member is None:
                try:
                    user_obj = await self.bot.fetch_user(user_id)
                    display_name = f"{user_obj.name}#{user_obj.discriminator}"
                    member_for_embed = None
                except Exception:
                    display_name = f"Usuário {user_id}"
                    member_for_embed = None
            else:
                display_name = member.display_name
                member_for_embed = member

            start = call_times.get(user_id, None)
            if start is None:
                seconds = 0
            else:
                seconds = int((datetime.datetime.now() - start).total_seconds())
                if seconds < 0:
                    seconds = 0

            entries.append((display_name, seconds, member_for_embed))

        # ordena por tempo decrescente
        entries.sort(key=lambda x: x[1], reverse=True)

        embed = discord.Embed(
            title="<:robo:1433191144140968158> Usuários em call",
            description=f"Total: **{len(entries)}**",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )

        # acrescenta cada usuário no embed com tempo formatado
        for name, seconds, member in entries:
            h, rem = divmod(seconds, 3600)
            m, s = divmod(rem, 60)
            tempo = f"{h}h {m}m {s}s" if seconds > 0 else "0s"
            if member:
                mention = member.mention
                embed.add_field(name=f"<:membro:1428925668950806558> {member.display_name}", value=f"{mention}\n⏳ {tempo}", inline=False)
            else:
                embed.add_field(name=f"<:membro:1428925668950806558> {name}", value=f"⏳ {tempo}", inline=False)

        embed.set_footer(text="Aeternum Exilium • Call Status")

        # envia resposta (não-ephemeral para todos verem)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(CallStatus(bot))