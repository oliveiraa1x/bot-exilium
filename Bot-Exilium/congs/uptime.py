import discord
from discord.ext import commands
from discord import app_commands
import datetime

class Uptime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="uptime", description="Mostra há quanto tempo o bot está online.")
    async def uptime(self, interaction: discord.Interaction):
        bot_start_time = self.bot.start_time
        uptime = datetime.datetime.now() - bot_start_time

        h, r = divmod(int(uptime.total_seconds()), 3600)
        m, s = divmod(r, 60)
        tempo = f"{h}h {m}m {s}s"

        embed = discord.Embed(
            title="<:ponto1:1430319216787066962> Uptime do Bot",
            description=f"O bot está online há **{tempo}**.",
            color=discord.Color.green()
        )
        embed.set_footer(text="Aeternum Exilium | Sistema de Status")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Uptime(bot))