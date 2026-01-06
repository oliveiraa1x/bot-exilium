import discord
import json
from pathlib import Path
from discord import app_commands
from discord.ext import commands


class Inventario(commands.Cog):
    """Sistema de Inventário e Gerenciamento de Items"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_path = Path(__file__).parent.parent / "data"
        self.db_file = self.data_path / "db.json"
        
        # Emojis customizados do servidor
        self.emoji_alma = "<:alma:1456309061057511535>"
        self.emoji_bot = "<:bot:1456311134334637759>"
        self.emoji_papel = "<:papel:1456311322319917198>"
        self.emoji_exilum = "<:Exilum:1456311301495197839>"
        self.emoji_adm = "<:adm:1456311286529790075>"
        self.emoji_microfone = "<:microfone:1456311268439883920>"
        self.emoji_relogio = "<:relogio:1456311245018759230>"
        self.emoji_membro = "<:membro:1456311222315253910>"
        self.emoji_evento = "<:evento:1456311189352091671>"
    
    def load_json(self):
        """Carrega dados do arquivo db.json"""
        try:
            with open(self.db_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_json(self, data):
        """Salva dados no arquivo db.json"""
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_user_inventory(self, user_id: str):
        """Obtém inventário do usuário ou cria novo"""
        db = self.load_json()
        user_id_str = str(user_id)
        
        if "usuarios" not in db:
            db["usuarios"] = {}
        
        if user_id_str not in db["usuarios"]:
            db["usuarios"][user_id_str] = {
                "itens": {},
                "equipados": {},
                "created_at": ""
            }
            self.save_json(db)
        
        return db["usuarios"][user_id_str]
    
    def add_item(self, user_id: str, item_id: str, quantidade: int = 1):
        """Adiciona item ao inventário"""
        db = self.load_json()
        user_id_str = str(user_id)
        
        if "usuarios" not in db:
            db["usuarios"] = {}
        
        user_inv = self.get_user_inventory(user_id)
        
        if item_id not in user_inv["itens"]:
            user_inv["itens"][item_id] = 0
        
        user_inv["itens"][item_id] += quantidade
        db["usuarios"][user_id_str] = user_inv
        self.save_json(db)
        return True
    
    def remove_item(self, user_id: str, item_id: str, quantidade: int = 1) -> bool:
        """Remove item do inventário se existir em quantidade suficiente"""
        db = self.load_json()
        user_id_str = str(user_id)
        user_inv = self.get_user_inventory(user_id)
        
        if item_id not in user_inv["itens"] or user_inv["itens"][item_id] < quantidade:
            return False
        
        user_inv["itens"][item_id] -= quantidade
        if user_inv["itens"][item_id] == 0:
            del user_inv["itens"][item_id]
        
        db["usuarios"][user_id_str] = user_inv
        self.save_json(db)
        return True
    
    def equip_item(self, user_id: str, item_id: str) -> bool:
        """Equipa um item passivo"""
        db = self.load_json()
        user_id_str = str(user_id)
        user_inv = self.get_user_inventory(user_id)
        
        if item_id in user_inv["itens"] and user_inv["itens"][item_id] > 0:
            user_inv["equipados"][item_id] = True
            db["usuarios"][user_id_str] = user_inv
            self.save_json(db)
            return True
        return False
    
    def unequip_item(self, user_id: str, item_id: str) -> bool:
        """Desequipa um item"""
        db = self.load_json()
        user_id_str = str(user_id)
        user_inv = self.get_user_inventory(user_id)
        
        if item_id in user_inv["equipados"]:
            del user_inv["equipados"][item_id]
            db["usuarios"][user_id_str] = user_inv
            self.save_json(db)
            return True
        return False
    
    def get_almas(self, user_id: str) -> int:
        """Obtém quantidade de souls do usuário do sistema de economia"""
        db = self.load_json()
        user_id_str = str(user_id)
        return db.get(user_id_str, {}).get("soul", 0)
    
    def add_almas(self, user_id: str, quantidade: int):
        """Adiciona souls ao usuário"""
        db = self.load_json()
        user_id_str = str(user_id)
        if user_id_str not in db:
            db[user_id_str] = {"soul": 0}
        db[user_id_str]["soul"] = db[user_id_str].get("soul", 0) + quantidade
        self.save_json(db)
    
    def remove_almas(self, user_id: str, quantidade: int) -> bool:
        """Remove souls se tiver quantidade suficiente"""
        db = self.load_json()
        user_id_str = str(user_id)
        soul_atual = db.get(user_id_str, {}).get("soul", 0)
        
        if soul_atual >= quantidade:
            db[user_id_str]["soul"] = soul_atual - quantidade
            
            # Adicionar ao balance do bot (todas as almas gastas na economia)
            if "bot_souls" not in db:
                db["bot_souls"] = 0
            db["bot_souls"] = db.get("bot_souls", 0) + quantidade
            
            self.save_json(db)
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
    
    def get_itens_passivos(self) -> dict:
        """Obtém itens passivos do cog Loja"""
        loja_cog = self.bot.get_cog("Loja")
        if loja_cog and hasattr(loja_cog, "itens_passivos"):
            return loja_cog.itens_passivos
        return {}
    
    # ==================== COMANDOS ====================
    
    @app_commands.command(name="inventario", description="Veja seu inventário")
    async def inventario(self, interaction: discord.Interaction):
        """Mostra inventário do usuário"""
        db = self.load_json()
        user_inv = self.get_user_inventory(interaction.user.id)
        
        itens = user_inv.get("itens", {})
        almas = user_inv.get("almas", 0)
        
        if not itens:
            embed = discord.Embed(
                title="📦 Seu Inventário",
                description="Seu inventário está vazio",
                color=0x9B59B6
            )
            embed.add_field(name=f"{self.emoji_alma} Souls", value=f"**{almas:,}**", inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return
        
        # Organizar itens por raridade
        itens_por_raridade = {}
        passivos = self.get_itens_passivos()
        
        # Verificar nas lootboxes (do cog Loja)
        loja_cog = self.bot.get_cog("Loja")
        lootboxes = loja_cog.lootboxes if loja_cog else {}
        box_recompensas = loja_cog.box_recompensas if loja_cog else {}
        
        # Mapear todos os itens possíveis
        todos_itens = {}
        todos_itens.update(passivos)
        todos_itens.update(lootboxes)
        
        # Adicionar itens de recompensas de boxes
        for box_id, rewards in box_recompensas.items():
            for item in rewards.get("itens", []):
                item_id = item.get("id")
                if item_id and item_id not in todos_itens:
                    nome_completo = item.get("nome", item_id)
                    # Extrair apenas o emoji (primeiro caractere) e remover do nome
                    emoji = nome_completo.split()[0] if nome_completo else "⭐"
                    nome_sem_emoji = " ".join(nome_completo.split()[1:]) if len(nome_completo.split()) > 1 else nome_completo
                    todos_itens[item_id] = {
                        "nome": nome_sem_emoji,
                        "emoji": emoji,
                        "raridade": "comum"
                    }
        
        for item_id in itens.keys():
            if item_id in todos_itens:
                item_data = todos_itens[item_id]
                raridade = item_data.get("raridade", "comum")
                if raridade not in itens_por_raridade:
                    itens_por_raridade[raridade] = []
                
                emoji = item_data.get("emoji", "⭐")
                nome = item_data.get("nome", item_id)
                qtd = itens[item_id]
                equipado = " ✅" if user_inv.get("equipados", {}).get(item_id) else ""
                
                itens_por_raridade[raridade].append(f"{emoji} **{nome}** x{qtd}{equipado}")
        
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
        
        await interaction.response.send_message(embed=embed, ephemeral=False)
    
    async def autocomplete_item_equipar(self, interaction: discord.Interaction, current: str):
        """Autocomplete para mostrar itens passivos que o usuário possui"""
        user_inv = self.get_user_inventory(interaction.user.id)
        itens_inv = user_inv.get("itens", {})
        passivos = self.get_itens_passivos()
        
        # Filtrar apenas itens passivos que o usuário tem e que não estão equipados
        itens_disponiveis = []
        for item_id, item_data in passivos.items():
            quantidade = itens_inv.get(item_id, 0)
            if quantidade > 0:
                emoji = item_data.get("emoji", "⭐")
                nome = item_data.get("nome", item_id)
                equipado = "✅ " if user_inv.get("equipados", {}).get(item_id) else ""
                descricao = item_data.get("descricao", "")[:30] + "..." if len(item_data.get("descricao", "")) > 30 else item_data.get("descricao", "")
                itens_disponiveis.append(
                    app_commands.Choice(
                        name=f"{equipado}{emoji} {nome}",
                        value=item_id
                    )
                )
        
        # Filtrar baseado no que o usuário está digitando
        if current:
            itens_disponiveis = [
                choice for choice in itens_disponiveis
                if current.lower() in choice.name.lower() or current.lower() in choice.value.lower()
            ]
        
        return itens_disponiveis[:25]
    
    @app_commands.command(name="equipar", description="Equipe um item passivo")
    @app_commands.describe(item="Escolha um item para equipar")
    @app_commands.autocomplete(item=autocomplete_item_equipar)
    async def equipar(self, interaction: discord.Interaction, item: str):
        """Equipa um item passivo"""
        passivos = self.get_itens_passivos()
        
        if item not in passivos:
            await interaction.response.send_message(
                "❌ Item não é um equipável válido!",
                ephemeral=False
            )
            return
        
        if self.equip_item(interaction.user.id, item):
            item_data = passivos[item]
            emoji = item_data.get("emoji", "⭐")
            nome = item_data.get("nome", item)
            descricao = item_data.get("descricao", "Sem descrição")
            raridade = item_data.get("raridade", "comum")
            
            embed = discord.Embed(
                title="✅ Item Equipado!",
                description=f"Você equipou: {emoji} **{nome}**\n\n📜 **Efeito:**\n{descricao}",
                color=self.get_cor_embed(raridade)
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)
        else:
            await interaction.response.send_message(
                "❌ Você não tem esse item!",
                ephemeral=False
            )
    
    async def autocomplete_item_desequipar(self, interaction: discord.Interaction, current: str):
        """Autocomplete para mostrar itens equipados"""
        user_inv = self.get_user_inventory(interaction.user.id)
        equipados = user_inv.get("equipados", {})
        passivos = self.get_itens_passivos()
        
        # Filtrar apenas itens equipados
        itens_disponiveis = []
        for item_id in equipados.keys():
            if item_id in passivos:
                item_data = passivos[item_id]
                emoji = item_data.get("emoji", "⭐")
                nome = item_data.get("nome", item_id)
                itens_disponiveis.append(
                    app_commands.Choice(
                        name=f"✅ {emoji} {nome}",
                        value=item_id
                    )
                )
        
        # Filtrar baseado no que o usuário está digitando
        if current:
            itens_disponiveis = [
                choice for choice in itens_disponiveis
                if current.lower() in choice.name.lower() or current.lower() in choice.value.lower()
            ]
        
        return itens_disponiveis[:25]
    
    @app_commands.command(name="desequipar", description="Remove um item equipado")
    @app_commands.describe(item="Escolha um item para remover")
    @app_commands.autocomplete(item=autocomplete_item_desequipar)
    async def desequipar(self, interaction: discord.Interaction, item: str):
        """Desequipa um item"""
        passivos = self.get_itens_passivos()
        
        if self.unequip_item(interaction.user.id, item):
            item_data = passivos.get(item, {})
            emoji = item_data.get("emoji", "⭐")
            nome = item_data.get("nome", item)
            
            embed = discord.Embed(
                title="✅ Item Desequipado!",
                description=f"Você desequipou: {emoji} **{nome}**",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)
        else:
            await interaction.response.send_message(
                "❌ Você não tem esse item equipado!",
                ephemeral=False
            )


async def setup(bot):
    await bot.add_cog(Inventario(bot))
