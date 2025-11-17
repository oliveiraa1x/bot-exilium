import discord
from discord import app_commands
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Mostra todos os comandos do bot.")
    async def help(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="<:mod1:1428924554121711707> Central de Ajuda",
            description="Aqui está a lista de comandos organizados por categorias:",
            color=discord.Color.black()
        )

        # -------------------------
        # CATEGORIA PERFIL
        # -------------------------
        embed.add_field(
            name="<:membro:1428925668950806558> Perfil",
            value=(
                "`/perfil` — mostra seu perfil completo.\n"
            ),
            inline=False
        )

        # -------------------------
        # CATEGORIA CALL
        # -------------------------
        embed.add_field(
            name="🎧 Sistema de Call",
            value=(
                "`/callstatus` — mostra seu tempo atual em call."
            ),
            inline=False
        )

        # -------------------------
        # CATEGORIA MENSAGENS
        # -------------------------
        embed.add_field(
            name="💬 Mensagens",
            value="`/mensagem` — cria mensagens personalizadas com estilo.",
            inline=False
        )

        # -------------------------
        # CATEGORIA UPTIME
        # -------------------------
        embed.add_field(
            name="⏳ Uptime",
            value="`/uptime` — mostra há quanto tempo o bot está online.",
            inline=False
        )

        embed.set_footer(text="Aeternum Exilium • Sistema de Ajuda")

        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))