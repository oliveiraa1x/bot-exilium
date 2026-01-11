
import discord
from discord.ext import commands
from discord import app_commands

def format_time(sec):
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return f"{h}h {m}m {s}s"

class TopTempo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="top-tempo", description="Mostra o ranking de tempo em call (Global).")
    async def top_tempo(self, interaction: discord.Interaction):
        await interaction.response.defer()
        db = self.bot.db()

        # Buscar todos os usuários do banco de dados
        ranking_items = []
        for uid, data in db.items():
            # Pular chaves especiais
            if uid in ["bot_souls", "usuarios"]:
                continue
            
            try:
                user_id = int(uid)
                tempo_total = data.get("tempo_total", 0)
                if tempo_total > 0:  # Apenas usuários com tempo registrado
                    ranking_items.append((uid, tempo_total))
            except (ValueError, TypeError):
                continue

        # Ordenar e pegar top 10
        ranking = sorted(
            ranking_items,
            key=lambda x: x[1],
            reverse=True
        )[:10]

        embed = discord.Embed(
            title="🏆 Top 10 — Tempo em Call (Global)",
            color=discord.Color.gold()
        )

        if not ranking:
            embed.description = "Ainda não há registros."
        else:
            for pos, (uid, seconds) in enumerate(ranking, start=1):
                # Tentar buscar do cache do servidor primeiro
                member = interaction.guild.get_member(int(uid)) if interaction.guild else None
                if member:
                    nome = member.display_name
                else:
                    # Buscar do banco de dados globalmente
                    try:
                        user = await self.bot.fetch_user(int(uid))
                        nome = user.name
                    except (discord.NotFound, discord.HTTPException):
                        nome = f"Usuário {uid}"
                embed.add_field(name=f"{pos}. {nome}", value=format_time(seconds), inline=False)

        await interaction.followup.send(embed=embed)

async def setup(bot):
    if bot.get_cog("TopTempo") is None:
        await bot.add_cog(TopTempo(bot))