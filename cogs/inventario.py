import discord
from discord import app_commands
from discord.ext import commands


class Inventario(commands.Cog):
    """Sistema de Inventário e Gerenciamento de Items"""
    
    def __init__(self, bot):
        self.bot = bot

    # ==================== HELPERS ====================

    def ensure_user(self, user_id: int) -> str:
        """Garante o registro do usuário no db.json (compartilhado com economia)."""
        economia_cog = self.bot.get_cog("Economia")
        if economia_cog and hasattr(economia_cog, "ensure_user"):
            return economia_cog.ensure_user(user_id)

        uid = str(user_id)
        db = self.bot.db()
        defaults = {
            "sobre": None,
            "tempo_total": 0,
            "soul": 0,
            "xp": 0,
            "level": 1,
            "last_daily": None,
            "last_mine": None,
            "mine_streak": 0,
            "daily_streak": 0,
            "last_caca": None,
            "caca_streak": 0,
            "caca_longa_ativa": None,
            "trabalho_atual": None,
            "last_trabalho": None,
            "missoes": [],
            "missoes_completas": [],
            "itens": {},
            "equipados": {},
        }

        if uid not in db:
            db[uid] = defaults.copy()
            self.bot.save_db(db)
        else:
            changed = False
            for key, value in defaults.items():
                if key not in db[uid]:
                    db[uid][key] = value
                    changed = True
            if changed:
                self.bot.save_db(db)
        return uid

    def get_user_inventory(self, user_id: int):
        """Obtém inventário do usuário a partir do db.json"""
        db = self.bot.db()
        uid = self.ensure_user(user_id)
        user_data = db.get(uid, {})

        # Garantir campos de inventário
        changed = False
        if "itens" not in user_data:
            user_data["itens"] = {}
            changed = True
        if "equipados" not in user_data:
            user_data["equipados"] = {}
            changed = True

        if changed:
            db[uid] = user_data
            self.bot.save_db(db)

        return user_data

    def add_item(self, user_id: int, item_id: str, quantidade: int = 1):
        """Adiciona item ao inventário"""
        db = self.bot.db()
        uid = self.ensure_user(user_id)
        user_inv = db.get(uid, {})
        itens = user_inv.setdefault("itens", {})
        itens[item_id] = itens.get(item_id, 0) + quantidade
        db[uid] = user_inv
        self.bot.save_db(db)
        return True

    def remove_item(self, user_id: int, item_id: str, quantidade: int = 1) -> bool:
        """Remove item do inventário se existir em quantidade suficiente"""
        db = self.bot.db()
        uid = self.ensure_user(user_id)
        user_inv = db.get(uid, {})
        itens = user_inv.get("itens", {})

        if item_id not in itens or itens[item_id] < quantidade:
            return False

        itens[item_id] -= quantidade
        if itens[item_id] == 0:
            del itens[item_id]

        user_inv["itens"] = itens
        db[uid] = user_inv
        self.bot.save_db(db)
        return True

    def equip_item(self, user_id: int, item_id: str) -> bool:
        """Equipa um item passivo"""
        db = self.bot.db()
        uid = self.ensure_user(user_id)
        user_inv = db.get(uid, {})
        itens = user_inv.get("itens", {})

        if item_id in itens and itens[item_id] > 0:
            equipados = user_inv.get("equipados", {})
            equipados[item_id] = True
            user_inv["equipados"] = equipados
            db[uid] = user_inv
            self.bot.save_db(db)
            return True
        return False

    def unequip_item(self, user_id: int, item_id: str) -> bool:
        """Desequipa um item"""
        db = self.bot.db()
        uid = self.ensure_user(user_id)
        user_inv = db.get(uid, {})
        equipados = user_inv.get("equipados", {})

        if item_id in equipados:
            del equipados[item_id]
            user_inv["equipados"] = equipados
            db[uid] = user_inv
            self.bot.save_db(db)
            return True
        return False

    def get_almas(self, user_id: int) -> int:
        """Obtém quantidade de almas (souls) do usuário"""
        uid = self.ensure_user(user_id)
        db = self.bot.db()
        return db.get(uid, {}).get("soul", 0)

    def add_almas(self, user_id: int, quantidade: int):
        """Adiciona almas (souls) ao usuário"""
        db = self.bot.db()
        uid = self.ensure_user(user_id)
        user_inv = db.get(uid, {})
        user_inv["soul"] = user_inv.get("soul", 0) + quantidade
        db[uid] = user_inv
        self.bot.save_db(db)

    def remove_almas(self, user_id: int, quantidade: int) -> bool:
        """Remove almas se tiver quantidade suficiente"""
        db = self.bot.db()
        uid = self.ensure_user(user_id)
        user_inv = db.get(uid, {})
        saldo = user_inv.get("soul", 0)
        if saldo >= quantidade:
            user_inv["soul"] = saldo - quantidade
            db[uid] = user_inv
            self.bot.save_db(db)
            return True
        return False

    def get_cor_embed(self, raridade: str) -> int:
        """Retorna cor do embed baseado na raridade"""
        cores = {
            "comum": 0x4A4A4A,
            "raro": 0x0099FF,
            "epico": 0x9933FF,
            "lendario": 0xFFD700,
            "ancestral": 0xFF4500
        }
        return cores.get(raridade, 0x808080)
    
    # ==================== COMANDOS ====================
    
    @app_commands.command(name="inventario", description="Veja seu inventário")
    async def inventario(self, interaction: discord.Interaction):
        """Mostra inventário do usuário"""
        db = self.bot.db()
        economia = db.get("_economia", {})
        user_inv = self.get_user_inventory(interaction.user.id)
        
        itens = user_inv.get("itens", {})
        almas = self.get_almas(interaction.user.id)
        
        if not itens:
            embed = discord.Embed(
                title="📦 Seu Inventário",
                description="Seu inventário está vazio",
                color=0x9B59B6
            )
            embed.add_field(name="💜 Almas", value=f"**{almas:,}**", inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Organizar itens por raridade
        itens_por_raridade = {}
        
        for categoria in ["itens_craft", "itens_forja", "itens_passivos", "loja_items"]:
            cat_items = economia.get(categoria, {})
            for item_id, item_data in cat_items.items():
                if item_id in itens:
                    raridade = item_data.get("raridade", "comum")
                    if raridade not in itens_por_raridade:
                        itens_por_raridade[raridade] = []
                    
                    emoji = item_data.get("emoji", "⭐")
                    nome = item_data.get("nome", item_id)
                    qtd = itens[item_id]
                    equipado = "✅" if user_inv.get("equipados", {}).get(item_id) else ""
                    
                    itens_por_raridade[raridade].append(f"{emoji} **{nome}** x{qtd} {equipado}")
        
        embed = discord.Embed(
            title="📦 Seu Inventário",
            color=0x9B59B6
        )
        
        ordem_raridade = ["ancestral", "lendario", "epico", "raro", "comum"]
        
        for raridade in ordem_raridade:
            if raridade in itens_por_raridade:
                items_list = "\n".join(itens_por_raridade[raridade])
                raridade_display = {
                    "ancestral": "🔴 ANCESTRAL",
                    "lendario": "🟡 LENDÁRIO",
                    "epico": "🟣 ÉPICO",
                    "raro": "🔵 RARO",
                    "comum": "⚪ COMUM"
                }
                embed.add_field(
                    name=raridade_display.get(raridade, raridade.upper()),
                    value=items_list,
                    inline=False
                )
        
        embed.add_field(name="💜 Almas", value=f"**{almas:,}**", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="equipar", description="Equipe um item passivo")
    @app_commands.describe(item="ID do item para equipar")
    async def equipar(self, interaction: discord.Interaction, item: str):
        """Equipa um item passivo"""
        db = self.bot.db()
        economia = db.get("_economia", {})
        
        # Procurar item em passivos 
        passivos = economia.get("itens_passivos", {})
        if item not in passivos:
            await interaction.response.send_message(
                "❌ Item não é um equipável válido!",
                ephemeral=True
            )
            return
        
        if self.equip_item(interaction.user.id, item):
            item_data = passivos[item]
            emoji = item_data.get("emoji", "⭐")
            nome = item_data.get("nome", item)
            
            embed = discord.Embed(
                title="✅ Item Equipado!",
                description=f"Você equipou: {emoji} **{nome}**",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(
                "❌ Você não tem esse item!",
                ephemeral=True
            )
    
    @app_commands.command(name="desequipar", description="Remove um item equipado")
    @app_commands.describe(item="ID do item para remover")
    async def desequipar(self, interaction: discord.Interaction, item: str):
        """Desequipa um item"""
        db = self.bot.db()
        passivos = db.get("_economia", {}).get("itens_passivos", {})
        
        if self.unequip_item(interaction.user.id, item):
            item_data = passivos.get(item, {})
            emoji = item_data.get("emoji", "⭐")
            nome = item_data.get("nome", item)
            
            embed = discord.Embed(
                title="✅ Item Desequipado!",
                description=f"Você desequipou: {emoji} **{nome}**",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(
                "❌ Você não tem esse item equipado!",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(Inventario(bot))