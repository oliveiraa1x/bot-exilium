import discord
from discord import app_commands
from discord.ext import commands

class Perfil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="perfil", description="Mostra um perfil bonito do usuário.")
    async def perfil(self, interaction: discord.Interaction, membro: discord.Member = None):
        membro = membro or interaction.user

        embed = discord.Embed(
            title=f"<:membro:1428925668950806558> Perfil de {membro.name}",
            color=discord.Color.blurple()
        )

        # Avatar (compatível com versões que usam display_avatar)
        avatar_url = getattr(membro, "avatar", None)
        if avatar_url:
            thumb = membro.avatar.url
        else:
            thumb = membro.display_avatar.url
        embed.set_thumbnail(url=thumb)

        # Datas
        embed.add_field(
            name="<:event:1428924599990616186> Conta criada em:",
            value=membro.created_at.strftime("%d/%m/%Y"),
            inline=True
        )

        embed.add_field(
            name="📥 Entrou no servidor:",
            value=membro.joined_at.strftime("%d/%m/%Y") if membro.joined_at else "Desconhecido",
            inline=True
        )

        # Cargos (ordem do mais alto para o mais baixo, sem @everyone)
        cargos = [cargo.mention for cargo in membro.roles[::-1] if cargo.name != "@everyone"]

        embed.add_field(
        name="<:ponto1:1430319216787066962> Cargos:",
        value=", ".join(cargos) if cargos else "Nenhum cargo",
        inline=False
       )


        # Banner (se tiver)
        try:
            user = await self.bot.fetch_user(membro.id)
            if user.banner:
                embed.set_image(url=user.banner.url)
        except Exception:
            pass

        embed.set_footer(text="Aeternum Exilium • Sistema de Perfil")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Perfil(bot))