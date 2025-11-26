import discord
from discord.ext import commands
from discord import app_commands

class Frase(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        pass

    @app_commands.command(name="frase", description="Envie uma frase ou poesia para o servidor.")
    @app_commands.describe(frase="Sua frase ou poesia")
    async def frase(self, interaction: discord.Interaction, frase: str):
        # Deferir para ocultar totalmente o uso do comando
        await interaction.response.defer(thinking=False, ephemeral=True)

        # Embed que irá para o chat
        embed = discord.Embed(
            title="<:papel:1440921270366634075> Nova frase enviada!",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="<:membro:1428925668950806558> Autor:",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="✍️ Frase / Poesia:",
            value=frase,
            inline=False
        )

        # O BOT envia a mensagem pública — sem aparecer que usaram comando
        msg = await interaction.channel.send(embed=embed)

        # Reação automática
        try:
            await msg.add_reaction("💖")
        except:
            pass

        # NÃO enviar followup para permanecer invisível

async def setup(bot):
    cog = Frase(bot)
    await bot.add_cog(cog)