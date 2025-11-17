import discord
from discord import app_commands
from discord.ext import commands

class Mensagem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="mensagem",
        description="Cria uma mensagem personalizada com embed."
    )
    @app_commands.describe(
        titulo="Título da mensagem",
        descricao="Conteúdo do embed",
        cor="Cor em HEX (ex: #5865F2)",
        imagem="Link de uma imagem grande",
        thumbnail="Link da imagem pequena (miniatura)"
    )
    async def mensagem(
        self,
        interaction: discord.Interaction,
        titulo: str,
        descricao: str,
        cor: str = "#5865F2",
        imagem: str = None,
        thumbnail: str = None
    ):
        try:
            color = discord.Color(int(cor.replace("#", ""), 16))
        except:
            color = discord.Color.blurple()

        embed = discord.Embed(
            title=titulo,
            description=descricao,
            color=color
        )

        if imagem:
            embed.set_image(url=imagem)

        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        embed.set_footer(text=f"")

        await interaction.response.send_message("Mensagem enviada!", ephemeral=True)
        await interaction.channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Mensagem(bot))