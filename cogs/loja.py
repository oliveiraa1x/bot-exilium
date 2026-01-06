import discord
import json
import random
import asyncio
from datetime import datetime, timedelta
from discord import app_commands
from discord.ext import commands
from pathlib import Path


class Loja(commands.Cog):
    """Sistema de Loja, Compra e Venda de Items"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_path = Path(__file__).parent.parent / "data"
        self.db_file = self.data_path / "db.json"
        
        # Emojis customizados do servidor
        self.emoji_alma = "<:alma:1456309061057511535>"
        
        # Lootboxes disponíveis na loja
        self.lootboxes = {
            "box_iniciante": {
                "nome": "📦 Box Iniciante",
                "valor": 500,
                "emoji": "📦",
                "raridade": "comum",
                "tipo": "lootbox",
                "descricao": f"Uma caixa misteriosa para iniciantes\n{self.emoji_alma} 50-125 Souls + Itens básicos"
            },
            "box_rara": {
                "nome": "🎁 Box Rara",
                "valor": 3000,
                "emoji": "🎁",
                "raridade": "raro",
                "tipo": "lootbox",
                "descricao": f"Contém itens raros e valiosos\n{self.emoji_alma} 300-750 Souls + Itens raros"
            },
            "box_ultra": {
                "nome": "💎 Box Ultra",
                "valor": 5000,
                "emoji": "💎",
                "raridade": "epico",
                "tipo": "lootbox",
                "descricao": f"Uma caixa épica com grandes recompensas\n{self.emoji_alma} 500-1.250 Souls + Itens épicos"
            },
            "box_mitica": {
                "nome": "⚡ Box Mítica",
                "valor": 8000,
                "emoji": "⚡",
                "raridade": "lendario",
                "tipo": "lootbox",
                "descricao": f"Recompensas míticas te aguardam\n{self.emoji_alma} 800-2.000 Souls + Itens lendários"
            },
            "box_lendaria": {
                "nome": "👑 Box Lendária",
                "valor": 12000,
                "emoji": "👑",
                "raridade": "ancestral",
                "tipo": "lootbox",
                "descricao": f"A mais poderosa de todas as caixas\n{self.emoji_alma} 1.200-3.000 Souls + Itens ancestrais"
            }
        }
        
        # Recompensas das lootboxes
        self.box_recompensas = {
            "box_iniciante": {
                "souls_min": 50,
                "souls_max": 125,
                "itens": [
                    {"id": "pocao_vida", "nome": "🧪 Poção de Vida", "chance": 0.5, "qtd_min": 1, "qtd_max": 3},
                    {"id": "pocao_mana", "nome": "💙 Poção de Mana", "chance": 0.5, "qtd_min": 1, "qtd_max": 3},
                    {"id": "fragmento_comum", "nome": "⚪ Fragmento Comum", "chance": 0.7, "qtd_min": 2, "qtd_max": 5},
                ]
            },
            "box_rara": {
                "souls_min": 300,
                "souls_max": 750,
                "itens": [
                    {"id": "pocao_vida_grande", "nome": "🧪 Grande Poção de Vida", "chance": 0.6, "qtd_min": 2, "qtd_max": 5},
                    {"id": "elixir_xp", "nome": "✨ Elixir de XP", "chance": 0.5, "qtd_min": 1, "qtd_max": 3, "xp": 500},
                    {"id": "fragmento_raro", "nome": "🔵 Fragmento Raro", "chance": 0.7, "qtd_min": 3, "qtd_max": 7},
                    {"id": "gema_azul", "nome": "💎 Gema Azul", "chance": 0.4, "qtd_min": 1, "qtd_max": 2},
                ]
            },
            "box_ultra": {
                "souls_min": 500,
                "souls_max": 1250,
                "itens": [
                    {"id": "elixir_xp_grande", "nome": "✨ Grande Elixir de XP", "chance": 0.7, "qtd_min": 2, "qtd_max": 4, "xp": 1000},
                    {"id": "fragmento_epico", "nome": "🟣 Fragmento Épico", "chance": 0.6, "qtd_min": 3, "qtd_max": 6},
                    {"id": "gema_roxa", "nome": "💜 Gema Roxa", "chance": 0.5, "qtd_min": 1, "qtd_max": 3},
                    {"id": "cristal_poder", "nome": "🔮 Cristal de Poder", "chance": 0.3, "qtd_min": 1, "qtd_max": 2},
                ]
            },
            "box_mitica": {
                "souls_min": 800,
                "souls_max": 2000,
                "itens": [
                    {"id": "elixir_lendario", "nome": "🌟 Elixir Lendário", "chance": 0.6, "qtd_min": 2, "qtd_max": 5, "xp": 2000},
                    {"id": "fragmento_lendario", "nome": "🟡 Fragmento Lendário", "chance": 0.7, "qtd_min": 4, "qtd_max": 8},
                    {"id": "gema_dourada", "nome": "💛 Gema Dourada", "chance": 0.5, "qtd_min": 2, "qtd_max": 4},
                    {"id": "essencia_mitica", "nome": "⚡ Essência Mítica", "chance": 0.4, "qtd_min": 1, "qtd_max": 3},
                    {"id": "runa_poder", "nome": "📿 Runa de Poder", "chance": 0.25, "qtd_min": 1, "qtd_max": 2},
                ]
            },
            "box_lendaria": {
                "souls_min": 1200,
                "souls_max": 3000,
                "itens": [
                    {"id": "elixir_ancestral", "nome": "🌠 Elixir Ancestral", "chance": 0.7, "qtd_min": 3, "qtd_max": 6, "xp": 3500},
                    {"id": "fragmento_ancestral", "nome": "🔴 Fragmento Ancestral", "chance": 0.8, "qtd_min": 5, "qtd_max": 10},
                    {"id": "gema_ancestral", "nome": "🔥 Gema Ancestral", "chance": 0.6, "qtd_min": 2, "qtd_max": 5},
                    {"id": "essencia_divina", "nome": "👑 Essência Divina", "chance": 0.5, "qtd_min": 1, "qtd_max": 3},
                    {"id": "runa_lendaria", "nome": "🎴 Runa Lendária", "chance": 0.4, "qtd_min": 1, "qtd_max": 2},
                    {"id": "nucleo_cosmico", "nome": "🌌 Núcleo Cósmico", "chance": 0.2, "qtd_min": 1, "qtd_max": 1},
                ]
            }
        }
        
        # Valores de XP dos elixires
        self.elixir_xp_values = {
            "elixir_xp": 500,
            "elixir_xp_grande": 1000,
            "elixir_lendario": 2000,
            "elixir_ancestral": 3500
        }

        # Configuração do mercado
        self.mercado_taxa = 0.05  # 5% taxa por venda
        
        # Itens passivos equipáveis
        self.itens_passivos = {
            "anel_velocidade": {
                "nome": "⏰ Anel da Velocidade",
                "valor": 5000,
                "emoji": "⏰",
                "raridade": "raro",
                "tipo": "passivo",
                "bonus": {"cooldown_reduz": 0.1},
                "descricao": "Reduz o cooldown de todos os comandos em 10%"
            },
            "anel_fortuna": {
                "nome": "💰 Anel da Fortuna",
                "valor": 8000,
                "emoji": "💰",
                "raridade": "epico",
                "tipo": "passivo",
                "bonus": {"soul_bonus": 0.15},
                "descricao": "Aumenta ganho de souls em 15%"
            },
            "amuleto_sabedoria": {
                "nome": "📿 Amuleto da Sabedoria",
                "valor": 7000,
                "emoji": "📿",
                "raridade": "epico",
                "tipo": "passivo",
                "bonus": {"xp_bonus": 0.20},
                "descricao": "Aumenta ganho de XP em 20%"
            },
            "botas_hermes": {
                "nome": "👢 Botas de Hermes",
                "valor": 10000,
                "emoji": "👢",
                "raridade": "lendario",
                "tipo": "passivo",
                "bonus": {"cooldown_reduz": 0.2, "soul_bonus": 0.1},
                "descricao": "Reduz cooldowns em 20% e aumenta souls em 10%"
            },
            "coroa_exilium": {
                "nome": "👑 Coroa de Exilium",
                "valor": 25000,
                "emoji": "👑",
                "raridade": "ancestral",
                "tipo": "passivo",
                "bonus": {"soul_bonus": 0.25, "xp_bonus": 0.25, "cooldown_reduz": 0.15},
                "descricao": "⚡ +25% Souls | +25% XP | -15% Cooldowns"
            },
            "medalhao_membro": {
                "nome": "🏅 Medalhão do Membro Elite",
                "valor": 15000,
                "emoji": "🏅",
                "raridade": "lendario",
                "tipo": "passivo",
                "bonus": {"xp_bonus": 0.30},
                "descricao": "Aumenta ganho de XP em 30%"
            },
            "bracelete_adm": {
                "nome": "💎 Bracelete do Administrador",
                "valor": 20000,
                "emoji": "💎",
                "raridade": "ancestral",
                "tipo": "passivo",
                "bonus": {"soul_bonus": 0.20, "cooldown_reduz": 0.25},
                "descricao": "🔥 +20% Souls | -25% Cooldowns"
            },
            "colar_microfone": {
                "nome": "🎤 Colar do Orador",
                "valor": 6000,
                "emoji": "🎤",
                "raridade": "raro",
                "tipo": "passivo",
                "bonus": {"xp_bonus": 0.12},
                "descricao": "Aumenta XP ganho por mensagens em 12%"
            }
        }

        # Itens de RPG disponíveis para compra na loja
        self.itens_rpg_loja = {
            "espada_madeira": {
                "nome": "🪵 Espada de Madeira",
                "valor": 300,
                "emoji": "🪵",
                "raridade": "comum",
                "tipo": "especial",
                "descricao": "Arma básica que concede +½ coração de dano médio por ataque no combate RPG. Use /equipar-rpg após comprar."
            }
        }
    
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

    def display_name(self, item_data: dict) -> str:
        """Retorna nome sem duplicar emoji (remove emoji se já estiver no nome)"""
        nome = item_data.get("nome", "Item")
        emoji = item_data.get("emoji", "")
        if emoji and nome.startswith(emoji):
            # remove o emoji inicial do nome
            nome = nome[len(emoji):].strip()
        return nome
    # ==================== Mercado Helpers ====================
    def ensure_mercado(self, db: dict) -> dict:
        """Garante estrutura do mercado no DB"""
        if "mercado" not in db:
            db["mercado"] = {"listings": [], "taxa": self.mercado_taxa}
        if "listings" not in db["mercado"]:
            db["mercado"]["listings"] = []
        return db

    def add_market_listing(self, seller_id: int, item_id: str, quantidade: int, valor: int) -> str:
        """Adiciona anúncio ao mercado e retorna ID do anúncio"""
        db = self.load_json()
        db = self.ensure_mercado(db)
        listing_id = f"{seller_id}-{item_id}-{int(datetime.now().timestamp())}-{random.randint(1000,9999)}"
        db["mercado"]["listings"].append({
            "id": listing_id,
            "seller_id": str(seller_id),
            "item_id": item_id,
            "quantidade": quantidade,
            "valor": valor,
            "created_at": datetime.now().isoformat()
        })
        self.save_json(db)
        return listing_id

    def get_market_listings(self) -> list:
        """Retorna lista de anúncios atuais"""
        db = self.load_json()
        db = self.ensure_mercado(db)
        return db["mercado"]["listings"]

    def remove_market_listing(self, listing_id: str, dec_qtd: int = None):
        """Remove ou decrementa quantidade de um anúncio"""
        db = self.load_json()
        db = self.ensure_mercado(db)
        listings = db["mercado"]["listings"]
        for i, l in enumerate(listings):
            if l.get("id") == listing_id:
                if dec_qtd is not None and l.get("quantidade", 0) > dec_qtd:
                    l["quantidade"] = l["quantidade"] - dec_qtd
                else:
                    listings.pop(i)
                break
        db["mercado"]["listings"] = listings
        self.save_json(db)
        return True
    
    def get_user_inventory(self, user_id: str):
        """Obtém inventário do usuário"""
        db = self.load_json()
        user_id_str = str(user_id)
        
        if "usuarios" not in db:
            db["usuarios"] = {}
        
        if user_id_str not in db["usuarios"]:
            db["usuarios"][user_id_str] = {
                "itens": {},
                "equipados": {},
                "created_at": datetime.now().isoformat()
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
    
    def remove_item(self, user_id: str, item_id: str, quantidade: int = 1) -> bool:
        """Remove item do inventário"""
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
    
    def get_almas(self, user_id: str) -> int:
        """Obtém almas (soul) do usuário do sistema de economia"""
        db = self.load_json()
        user_id_str = str(user_id)
        return db.get(user_id_str, {}).get("soul", 0)
    
    def add_almas(self, user_id: str, quantidade: int):
        """Adiciona almas (soul) ao usuário"""
        db = self.load_json()
        user_id_str = str(user_id)
        if user_id_str not in db:
            db[user_id_str] = {"soul": 0}
        db[user_id_str]["soul"] = db[user_id_str].get("soul", 0) + quantidade
        self.save_json(db)
    
    def remove_almas(self, user_id: str, quantidade: int) -> bool:
        """Remove almas (soul) se tiver quantidade suficiente"""
        db = self.load_json()
        user_id_str = str(user_id)
        soul_atual = db.get(user_id_str, {}).get("soul", 0)
        
        if soul_atual >= quantidade:
            db[user_id_str]["soul"] = soul_atual - quantidade
            
            # Adicionar ao balance do bot
            if "bot_souls" not in db:
                db["bot_souls"] = 0
            db["bot_souls"] = db.get("bot_souls", 0) + quantidade
            
            self.save_json(db)
            return True
        return False
    
    def get_cor_embed(self, raridade: str):
        """Obtém cor do embed baseado na raridade"""
        cores = {
            "comum": 0x4A4A4A,
            "raro": 0x0099FF,
            "epico": 0x9933FF,
            "lendario": 0xFFD700,
            "ancestral": 0xFF4500
        }
        return cores.get(raridade, 0x808080)
    
    # ==================== COMANDOS ====================
    
    @app_commands.command(name="loja", description="Acesse a loja e compre itens com souls")
    async def loja(self, interaction: discord.Interaction):
        """Mostra loja de itens"""
        db = self.load_json()
        loja_items_db = db.get("loja_items", {})
        
        # Combinar lootboxes, itens passivos e items da loja
        loja_items = {**self.lootboxes, **self.itens_passivos, **self.itens_rpg_loja, **loja_items_db}
        
        user_almas = self.get_almas(interaction.user.id)
        
        # Categorizar itens
        categorias = {
            "consumivel": [],
            "lootbox": [],
            "passivo": [],
            "especial": []
        }
        
        for item_id, item_data in loja_items.items():
            tipo = item_data.get("tipo", "consumivel")
            if tipo in categorias:
                categorias[tipo].append((item_id, item_data))
        
        # Criar view com buttons
        class LojaView(discord.ui.View):
            def __init__(self, ctx_self, items, db_data):
                super().__init__(timeout=300)
                self.ctx = ctx_self
                self.items = items
                self.db_data = db_data
                self.current_category = "consumivel"
                self.page = 0
            
            @discord.ui.button(label="Consumíveis", style=discord.ButtonStyle.primary)
            async def consumivel_btn(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                self.current_category = "consumivel"
                self.page = 0
                await self.update_embed(button_interaction)
            
            @discord.ui.button(label="Lootboxes", style=discord.ButtonStyle.primary)
            async def lootbox_btn(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                self.current_category = "lootbox"
                self.page = 0
                await self.update_embed(button_interaction)
            
            @discord.ui.button(label="Itens Passivos", style=discord.ButtonStyle.success)
            async def passivo_btn(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                self.current_category = "passivo"
                self.page = 0
                await self.update_embed(button_interaction)
            
            @discord.ui.button(label="Especiais", style=discord.ButtonStyle.danger)
            async def especial_btn(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                self.current_category = "especial"
                self.page = 0
                await self.update_embed(button_interaction)
            
            async def update_embed(self, interaction: discord.Interaction):
                items = categorias[self.current_category]
                items_per_page = 5
                max_pages = max((len(items) + items_per_page - 1) // items_per_page, 1)
                
                if self.page >= max_pages:
                    self.page = max_pages - 1
                
                embed = discord.Embed(
                    title=f"🏪 Loja - {self.current_category.upper()}",
                    description=f"Suas Souls: **{user_almas}** {self.ctx.emoji_alma}\nPágina {self.page + 1}/{max_pages}",
                    color=0xFF6B9D
                )
                
                start_idx = self.page * items_per_page
                end_idx = start_idx + items_per_page
                
                for item_id, item_data in items[start_idx:end_idx]:
                    valor = item_data.get("valor", 0)
                    raridade = item_data.get("raridade", "comum")
                    emoji = item_data.get("emoji", "⭐")
                    descricao = item_data.get("descricao", "Sem descrição")
                    nome = self.ctx.display_name(item_data)
                    embed.add_field(
                        name=f"{emoji} {nome}",
                        value=f"**Custo:** {valor} {self.ctx.emoji_alma}\n{descricao}\n**ID:** `{item_id}`",
                        inline=False
                    )
                
                if not items:
                    embed.description = f"Suas Souls: **{user_almas}** {self.ctx.emoji_alma}\n\nNenhum item nesta categoria ainda!"
                
                await interaction.response.edit_message(embed=embed, view=self)
        
        view = LojaView(self, categorias, db)
        
        embed = discord.Embed(
            title="🏪 Loja - CONSUMÍVEIS",
            description=f"Suas Souls: **{user_almas}** {self.emoji_alma}\nPágina 1/1",
            color=0xFF6B9D
        )
        
        if not loja_items:
            embed.description = f"Suas Souls: **{user_almas}** {self.emoji_alma}\n\nLoja em construção! Volte em breve."
        
        await interaction.response.send_message(embed=embed, view=view)
    
    async def autocomplete_item_comprar(self, interaction: discord.Interaction, current: str):
        """Autocomplete para listar itens disponíveis na loja"""
        db = self.load_json()
        loja_items = {**self.lootboxes, **self.itens_passivos, **self.itens_rpg_loja, **db.get("loja_items", {})}
        escolhas = []
        for item_id, item_data in loja_items.items():
            emoji = item_data.get("emoji", "⭐")
            nome = self.display_name(item_data)
            custo = item_data.get("valor", 0)
            display = f"{emoji} {nome} - {custo} {self.emoji_alma}"
            escolhas.append(app_commands.Choice(name=display[:100], value=item_id))
        if current:
            escolhas = [c for c in escolhas if current.lower() in c.name.lower() or current.lower() in c.value.lower()]
        return escolhas[:25]
    
    @app_commands.command(name="comprar", description="Compre um item da loja")
    @app_commands.describe(item="Escolha um item", quantidade="Quantidade (padrão: 1)")
    @app_commands.autocomplete(item=autocomplete_item_comprar)
    async def comprar(self, interaction: discord.Interaction, item: str = None, quantidade: int = 1):
        """Compra um item da loja com confirmação"""
        db = self.load_json()
        loja_items = {**self.lootboxes, **self.itens_passivos, **self.itens_rpg_loja, **db.get("loja_items", {})}

        # Se não passar item, orientar uso do autocomplete
        if not item:
            await interaction.response.send_message(
                "Selecione o item pelo popup do parâmetro do comando.",
                ephemeral=True
            )
            return

        if item not in loja_items:
            await interaction.response.send_message("❌ Item não existe na loja!", ephemeral=True)
            return

        item_data = loja_items[item]
        valor_unitario = item_data.get("valor", 0)

        # Itens passivos só podem ser comprados 1 por vez
        if item_data.get("tipo") == "passivo":
            quantidade = 1
            # Verificar se já possui o item
            user_inv = self.get_user_inventory(interaction.user.id)
            if item in user_inv.get("itens", {}):
                await interaction.response.send_message(
                    f"❌ Você já possui {item_data.get('emoji', '')} **{item_data.get('nome')}**!",
                    ephemeral=True
                )
                return

        custo_total = valor_unitario * quantidade
        user_almas = self.get_almas(interaction.user.id)

        class ConfirmarCompraView(discord.ui.View):
            def __init__(self, ctx_self, item_id, item_info, qtd, total):
                super().__init__(timeout=120)
                self.ctx = ctx_self
                self.item_id = item_id
                self.item_info = item_info
                self.qtd = qtd
                self.total = total

            @discord.ui.button(label="Confirmar", style=discord.ButtonStyle.success)
            async def confirmar(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                if button_interaction.user.id != interaction.user.id:
                    await button_interaction.response.send_message("❌ Apenas quem iniciou a compra pode confirmar.", ephemeral=True)
                    return
                # Revalidar saldo
                saldo = self.ctx.get_almas(interaction.user.id)
                if saldo < self.total:
                    await button_interaction.response.send_message(
                        f"❌ Souls insuficientes. Você tem {saldo} {self.ctx.emoji_alma} e precisa de {self.total} {self.ctx.emoji_alma}.",
                        ephemeral=True
                    )
                    return
                # Regras de passivo: 1 unidade
                if self.item_info.get("tipo") == "passivo" and self.qtd != 1:
                    self.qtd = 1
                # Efetivar compra
                self.ctx.remove_almas(interaction.user.id, self.total)
                self.ctx.add_item(interaction.user.id, self.item_id, self.qtd)

                ok = discord.Embed(
                    title="✅ Compra realizada!",
                    description=f"Você comprou **{self.qtd}x** {self.item_info.get('emoji','')} **{self.item_info.get('nome','Item')}**",
                    color=discord.Color.green()
                )
                ok.add_field(name="Custo", value=f"{self.total} {self.ctx.emoji_alma}", inline=False)
                ok.set_footer(text=f"Souls restantes: {saldo - self.total}")
                await button_interaction.response.edit_message(embed=ok, view=None)

            @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger)
            async def cancelar(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                if button_interaction.user.id != interaction.user.id:
                    await button_interaction.response.send_message("❌ Apenas quem iniciou a compra pode cancelar.", ephemeral=True)
                    return
                cancel = discord.Embed(
                    title="🛑 Compra cancelada",
                    description="Nenhuma alteração foi feita.",
                    color=discord.Color.red()
                )
                await button_interaction.response.edit_message(embed=cancel, view=None)

        embed = discord.Embed(
            title="🛒 Confirmar Compra",
            description=(
                f"Item: {item_data.get('emoji','')} **{self.display_name(item_data)}**\n"
                f"Quantidade: **{quantidade}x**\n"
                f"Preço unitário: **{valor_unitario}** {self.emoji_alma}\n"
                f"Total: **{custo_total}** {self.emoji_alma}"
            ),
            color=0xFF6B9D
        )
        embed.set_footer(text=f"Seu saldo: {user_almas} {self.emoji_alma}")
        view = ConfirmarCompraView(self, item, item_data, quantidade, custo_total)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)
    
    async def autocomplete_box(self, interaction: discord.Interaction, current: str):
        """Autocomplete para mostrar lootboxes que o usuário possui"""
        user_inv = self.get_user_inventory(interaction.user.id)
        itens_inv = user_inv.get("itens", {})
        
        # Filtrar apenas lootboxes que o usuário tem
        boxes_disponiveis = []
        for box_id, box_data in self.lootboxes.items():
            quantidade = itens_inv.get(box_id, 0)
            if quantidade > 0:
                boxes_disponiveis.append(
                    app_commands.Choice(
                        name=f"{box_data['emoji']} {box_data['nome']} (x{quantidade})",
                        value=box_id
                    )
                )
        
        # Filtrar baseado no que o usuário está digitando
        if current:
            boxes_disponiveis = [
                choice for choice in boxes_disponiveis
                if current.lower() in choice.name.lower() or current.lower() in choice.value.lower()
            ]
        
        return boxes_disponiveis[:25]  # Discord limita a 25 opções
    
    @app_commands.command(name="abrir", description="Abra uma lootbox do seu inventário")
    @app_commands.describe(box="Escolha uma box para abrir")
    @app_commands.autocomplete(box=autocomplete_box)
    async def abrir(self, interaction: discord.Interaction, box: str):
        """Abre uma lootbox"""
        await interaction.response.defer()
        
        # Verificar se é uma lootbox válida
        if box not in self.lootboxes:
            embed = discord.Embed(
                title="❌ Lootbox inválida!",
                description=f"Use uma das seguintes:\n" + "\n".join([f"• `{k}` - {v['nome']}" for k, v in self.lootboxes.items()]),
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Verificar se o usuário tem essa box
        user_inv = self.get_user_inventory(interaction.user.id)
        itens_inv = user_inv.get("itens", {})
        
        if box not in itens_inv or itens_inv[box] < 1:
            embed = discord.Embed(
                title="❌ Você não possui essa lootbox!",
                description=f"Compre na `/loja` primeiro",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Remover a box do inventário
        self.remove_item(interaction.user.id, box, 1)
        
        # Gerar recompensas
        box_data = self.lootboxes[box]
        recompensas_config = self.box_recompensas.get(box, {})
        
        # Sortear souls
        souls_ganhas = random.randint(
            recompensas_config.get("souls_min", 100),
            recompensas_config.get("souls_max", 500)
        )
        self.add_almas(interaction.user.id, souls_ganhas)
        
        # Sortear itens
        itens_ganhos = []
        for item_config in recompensas_config.get("itens", []):
            # Verificar se ganha o item baseado na chance
            if random.random() <= item_config["chance"]:
                quantidade = random.randint(item_config["qtd_min"], item_config["qtd_max"])
                self.add_item(interaction.user.id, item_config["id"], quantidade)
                itens_ganhos.append(f"{item_config['nome']} x{quantidade}")
        
        # Animação de abertura
        embed_opening = discord.Embed(
            title=f"{box_data['emoji']} Abrindo {box_data['nome']}...",
            description="✨ *Revelando suas recompensas* ✨",
            color=self.get_cor_embed(box_data["raridade"])
        )
        await interaction.followup.send(embed=embed_opening)
        
        # Aguardar 2 segundos para criar suspense
        await asyncio.sleep(2)
        
        # Mostrar recompensas
        embed_result = discord.Embed(
            title=f"🎉 {box_data['nome']} Aberta!",
            description=f"Você ganhou as seguintes recompensas:",
            color=discord.Color.gold()
        )
        
        embed_result.add_field(
            name="💜 Souls",
            value=f"**+{souls_ganhas:,}** {self.emoji_alma}",
            inline=False
        )
        
        if itens_ganhos:
            embed_result.add_field(
                name="🎁 Itens",
                value="\n".join([f"• {item}" for item in itens_ganhos]),
                inline=False
            )
        else:
            embed_result.add_field(
                name="🎁 Itens",
                value="Nenhum item desta vez... Mais sorte na próxima!",
                inline=False
            )
        
        user_souls_total = self.get_almas(interaction.user.id)
        embed_result.set_footer(text=f"Total de Souls: {user_souls_total:,} {self.emoji_alma}")
        
        await interaction.followup.send(embed=embed_result)
    
    async def autocomplete_item_usar(self, interaction: discord.Interaction, current: str):
        """Autocomplete para mostrar itens consumíveis que o usuário possui"""
        user_inv = self.get_user_inventory(interaction.user.id)
        itens_inv = user_inv.get("itens", {})
        
        # Mapear nomes dos elixires
        item_names = {
            "elixir_xp": "✨ Elixir de XP (+500 XP)",
            "elixir_xp_grande": "✨ Grande Elixir de XP (+1.000 XP)",
            "elixir_lendario": "🌟 Elixir Lendário (+2.000 XP)",
            "elixir_ancestral": "🌠 Elixir Ancestral (+3.500 XP)",
            "pocao_vida": "🧪 Poção de Vida",
            "pocao_mana": "💙 Poção de Mana",
            "pocao_vida_grande": "🧪 Grande Poção de Vida"
        }
        
        # Filtrar apenas itens consumíveis que o usuário tem
        itens_disponiveis = []
        for item_id, quantidade in itens_inv.items():
            if quantidade > 0 and item_id in item_names:
                itens_disponiveis.append(
                    app_commands.Choice(
                        name=f"{item_names[item_id]} (x{quantidade})",
                        value=item_id
                    )
                )
        
        # Filtrar baseado no que o usuário está digitando
        if current:
            itens_disponiveis = [
                choice for choice in itens_disponiveis
                if current.lower() in choice.name.lower() or current.lower() in choice.value.lower()
            ]
        
        return itens_disponiveis[:25]  # Discord limita a 25 opções
    
    @app_commands.command(name="usar", description="Use um item consumível do inventário")
    @app_commands.describe(item="Escolha um item para usar", quantidade="Quantidade (padrão: 1)")
    @app_commands.autocomplete(item=autocomplete_item_usar)
    async def usar(self, interaction: discord.Interaction, item: str, quantidade: int = 1):
        """Usa um item consumível"""
        # Verificar se o usuário tem o item
        user_inv = self.get_user_inventory(interaction.user.id)
        itens_inv = user_inv.get("itens", {})
        
        if item not in itens_inv or itens_inv[item] < quantidade:
            await interaction.response.send_message(
                f"❌ Você não tem {quantidade}x desse item!",
                ephemeral=True
            )
            return
        
        # Verificar se é um elixir de XP
        if item in self.elixir_xp_values:
            xp_por_unidade = self.elixir_xp_values[item]
            xp_total = xp_por_unidade * quantidade
            
            # Remover itens do inventário
            self.remove_item(interaction.user.id, item, quantidade)
            
            # Adicionar XP ao usuário através do sistema de economia
            db = self.load_json()
            user_id_str = str(interaction.user.id)
            
            # Garantir que o usuário existe no sistema de economia
            if user_id_str not in db:
                db[user_id_str] = {
                    "soul": 0,
                    "xp": 0,
                    "level": 1
                }
            
            # Adicionar XP e recalcular nível
            old_level = db[user_id_str].get("level", 1)
            old_xp = db[user_id_str].get("xp", 0)
            new_xp = old_xp + xp_total
            db[user_id_str]["xp"] = new_xp
            
            # Calcular novo nível (usando a mesma lógica da economia)
            level = 1
            required_xp = 100
            current_xp = new_xp
            
            while current_xp >= required_xp:
                current_xp -= required_xp
                level += 1
                required_xp = int(required_xp * 1.5)
            
            db[user_id_str]["level"] = level
            self.save_json(db)
            
            # Criar embed de resposta
            nome_item = {
                "elixir_xp": "✨ Elixir de XP",
                "elixir_xp_grande": "✨ Grande Elixir de XP",
                "elixir_lendario": "🌟 Elixir Lendário",
                "elixir_ancestral": "🌠 Elixir Ancestral"
            }.get(item, item)
            
            embed = discord.Embed(
                title="✅ Item usado com sucesso!",
                description=f"Você usou **{quantidade}x {nome_item}**",
                color=discord.Color.green()
            )
            embed.add_field(name="⭐ XP Ganho", value=f"+{xp_total:,} XP", inline=True)
            embed.add_field(name="📊 Nível", value=f"Level {level}", inline=True)
            
            if level > old_level:
                embed.add_field(
                    name="🎉 LEVEL UP!",
                    value=f"Você subiu do nível {old_level} para {level}!",
                    inline=False
                )
                embed.color = discord.Color.gold()
            
            # Calcular XP para próximo nível
            required_for_next = 100
            for _ in range(1, level):
                required_for_next = int(required_for_next * 1.5)
            
            progress_xp = new_xp
            for _ in range(1, level):
                temp_required = 100
                for i in range(1, _ + 1):
                    if i > 1:
                        temp_required = int(temp_required * 1.5)
                progress_xp -= temp_required
            
            embed.set_footer(text=f"XP: {progress_xp}/{required_for_next} para o próximo nível")
            
            await interaction.response.send_message(embed=embed, ephemeral=False)
        else:
            # Item não é consumível ou não tem efeito implementado
            await interaction.response.send_message(
                f"❌ Este item não pode ser usado ainda!",
                ephemeral=True
            )
    
    @app_commands.command(name="craft", description="Crafta um item usando materiais")
    async def craft(self, interaction: discord.Interaction):
        """Crafta um item usando minérios"""
        # Receitas de craft
        receitas_craft = {
            "espada_cobre": {
                "nome": "⚔️ Espada de Cobre",
                "emoji": "⚔️",
                "raridade": "comum",
                "materiais": {"cobre_refinado": 3, "fragmento_comum": 2},
                "bonus": {"ataque": 5},
                "descricao": "Espada básica de cobre"
            },
            "espada_ferro": {
                "nome": "⚔️ Espada de Ferro",
                "emoji": "⚔️",
                "raridade": "raro",
                "materiais": {"ferro_refinado": 3, "fragmento_raro": 2},
                "bonus": {"ataque": 10},
                "descricao": "Espada resistente de ferro"
            },
            "espada_ouro": {
                "nome": "⚔️ Espada de Ouro",
                "emoji": "⚔️",
                "raridade": "epico",
                "materiais": {"ouro_refinado": 3, "fragmento_epico": 2, "gema_azul": 1},
                "bonus": {"ataque": 20, "soul_bonus": 0.05},
                "descricao": "Espada valiosa de ouro"
            },
            "armadura_ferro": {
                "nome": "🛡️ Armadura de Ferro",
                "emoji": "🛡️",
                "raridade": "raro",
                "materiais": {"ferro_refinado": 5, "fragmento_raro": 3},
                "bonus": {"defesa": 15},
                "descricao": "Armadura pesada de ferro"
            },
            "picareta_diamante": {
                "nome": "⛏️ Picareta de Diamante",
                "emoji": "⛏️",
                "raridade": "lendario",
                "materiais": {"diamante_refinado": 3, "fragmento_lendario": 2, "gema_dourada": 1},
                "bonus": {"mineracao_bonus": 0.25},
                "descricao": "Aumenta ganho de minérios em 25%"
            },
            "amuleto_obsidiana": {
                "nome": "🔮 Amuleto de Obsidiana",
                "emoji": "🔮",
                "raridade": "ancestral",
                "materiais": {"obsidiana_refinada": 2, "fragmento_ancestral": 3, "gema_ancestral": 2, "essencia_divina": 1},
                "bonus": {"xp_bonus": 0.35, "soul_bonus": 0.30},
                "descricao": "⚡ +35% XP | +30% Souls"
            }
        }
        
        user_inv = self.get_user_inventory(interaction.user.id)
        itens_inv = user_inv.get("itens", {})
        
        # Criar view com botões para cada receita
        class CraftView(discord.ui.View):
            def __init__(self, ctx_self, receitas, user_items):
                super().__init__(timeout=180)
                self.ctx = ctx_self
                self.receitas = receitas
                self.user_items = user_items
                self.current_page = 0
                self.items_per_page = 4
                self.update_buttons()
            
            def update_buttons(self):
                self.clear_items()
                receitas_list = list(self.receitas.items())
                start_idx = self.current_page * self.items_per_page
                end_idx = start_idx + self.items_per_page
                
                for item_id, receita in receitas_list[start_idx:end_idx]:
                    button = discord.ui.Button(
                        label=f"{receita['emoji']} {receita['nome'].split()[-1]}",
                        style=discord.ButtonStyle.primary,
                        custom_id=item_id
                    )
                    button.callback = self.create_craft_callback(item_id, receita)
                    self.add_item(button)
            
            def create_craft_callback(self, item_id, receita):
                async def callback(button_interaction: discord.Interaction):
                    if button_interaction.user.id != interaction.user.id:
                        await button_interaction.response.send_message("❌ Apenas quem usou o comando pode craftar!", ephemeral=True)
                        return
                    
                    # Verificar materiais
                    materiais = receita.get("materiais", {})
                    faltando = []
                    
                    for mat_id, qtd_necessaria in materiais.items():
                        qtd_user = self.user_items.get(mat_id, 0)
                        if qtd_user < qtd_necessaria:
                            faltando.append(f"• {mat_id}: tem {qtd_user}, precisa {qtd_necessaria}")
                    
                    if faltando:
                        embed_erro = discord.Embed(
                            title="❌ Materiais Insuficientes",
                            description="Você não tem todos os materiais:\n\n" + "\n".join(faltando),
                            color=discord.Color.red()
                        )
                        await button_interaction.response.send_message(embed=embed_erro, ephemeral=True)
                        return
                    
                    # Remover materiais
                    for mat_id, qtd in materiais.items():
                        self.ctx.remove_item(interaction.user.id, mat_id, qtd)
                    
                    # Adicionar item craftado
                    self.ctx.add_item(interaction.user.id, item_id, 1)
                    
                    # Mostrar resultado
                    embed_sucesso = discord.Embed(
                        title="✅ Item Craftado!",
                        description=f"Você craftou: {receita['emoji']} **{receita['nome']}**\n\n📜 {receita['descricao']}",
                        color=self.ctx.get_cor_embed(receita.get("raridade", "comum"))
                    )
                    
                    bonus_text = "\n".join([f"**{k.replace('_', ' ').title()}:** +{v}" for k, v in receita.get("bonus", {}).items()])
                    if bonus_text:
                        embed_sucesso.add_field(name="⚡ Bônus", value=bonus_text, inline=False)
                    
                    await button_interaction.response.send_message(embed=embed_sucesso, ephemeral=False)
                
                return callback
        
        # Criar embed inicial
        embed = discord.Embed(
            title="🔨 Sistema de Craft",
            description="Clique nos botões abaixo para craftar itens!\n\n**Receitas Disponíveis:**",
            color=0xFF9500
        )
        
        for item_id, receita in receitas_craft.items():
            materiais_text = "\n".join([f"• {mat}: {qtd}x" for mat, qtd in receita.get("materiais", {}).items()])
            embed.add_field(
                name=f"{receita['emoji']} {receita['nome']}",
                value=f"{receita['descricao']}\n**Materiais:**\n{materiais_text}",
                inline=True
            )
        
        view = CraftView(self, receitas_craft, itens_inv)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)
    
    @app_commands.command(name="forjar", description="Forja e aprimora minérios")
    async def forjar(self, interaction: discord.Interaction):
        """Forja para refinar minérios"""
        # Receitas de forja
        receitas_forja = {
            "cobre_refinado": {
                "nome": "🟤 Cobre Refinado",
                "emoji": "🟤",
                "raridade": "comum",
                "materiais": {"minerio_cobre": 5},
                "custo_souls": 100,
                "taxa_sucesso": 0.90,
                "descricao": "Cobre purificado e pronto para craft"
            },
            "ferro_refinado": {
                "nome": "⚪ Ferro Refinado",
                "emoji": "⚪",
                "raridade": "raro",
                "materiais": {"minerio_ferro": 5},
                "custo_souls": 300,
                "taxa_sucesso": 0.80,
                "descricao": "Ferro forjado com alta qualidade"
            },
            "ouro_refinado": {
                "nome": "🟡 Ouro Refinado",
                "emoji": "🟡",
                "raridade": "epico",
                "materiais": {"minerio_ouro": 5, "fragmento_raro": 1},
                "custo_souls": 800,
                "taxa_sucesso": 0.70,
                "descricao": "Ouro puro e valioso"
            },
            "diamante_refinado": {
                "nome": "💎 Diamante Refinado",
                "emoji": "💎",
                "raridade": "lendario",
                "materiais": {"minerio_diamante": 3, "fragmento_epico": 2},
                "custo_souls": 2000,
                "taxa_sucesso": 0.60,
                "descricao": "Diamante lapidado perfeitamente"
            },
            "obsidiana_refinada": {
                "nome": "🖤 Obsidiana Refinada",
                "emoji": "🖤",
                "raridade": "ancestral",
                "materiais": {"minerio_obsidiana": 3, "fragmento_lendario": 2, "gema_dourada": 1},
                "custo_souls": 5000,
                "taxa_sucesso": 0.50,
                "descricao": "Obsidiana forjada com poder ancestral"
            }
        }
        
        user_inv = self.get_user_inventory(interaction.user.id)
        itens_inv = user_inv.get("itens", {})
        user_almas = self.get_almas(interaction.user.id)
        
        # Criar view com botões
        class ForjaView(discord.ui.View):
            def __init__(self, ctx_self, receitas, user_items, user_souls):
                super().__init__(timeout=180)
                self.ctx = ctx_self
                self.receitas = receitas
                self.user_items = user_items
                self.user_souls = user_souls
                self.update_buttons()
            
            def update_buttons(self):
                self.clear_items()
                
                for item_id, receita in list(self.receitas.items())[:5]:
                    button = discord.ui.Button(
                        label=f"{receita['emoji']} {receita['nome'].split()[-1]}",
                        style=discord.ButtonStyle.success,
                        custom_id=item_id
                    )
                    button.callback = self.create_forja_callback(item_id, receita)
                    self.add_item(button)
            
            def create_forja_callback(self, item_id, receita):
                async def callback(button_interaction: discord.Interaction):
                    if button_interaction.user.id != interaction.user.id:
                        await button_interaction.response.send_message("❌ Apenas quem usou o comando pode forjar!", ephemeral=True)
                        return
                    
                    await button_interaction.response.defer()
                    
                    # Verificar souls
                    custo = receita.get("custo_souls", 0)
                    if self.user_souls < custo:
                        embed_erro = discord.Embed(
                            title="❌ Souls Insuficientes",
                            description=f"Você tem: **{self.user_souls}** {self.ctx.emoji_alma}\nNecessário: **{custo}** {self.ctx.emoji_alma}",
                            color=discord.Color.red()
                        )
                        await button_interaction.followup.send(embed=embed_erro, ephemeral=True)
                        return
                    
                    # Verificar materiais
                    materiais = receita.get("materiais", {})
                    faltando = []
                    
                    for mat_id, qtd_necessaria in materiais.items():
                        qtd_user = self.user_items.get(mat_id, 0)
                        if qtd_user < qtd_necessaria:
                            faltando.append(f"• {mat_id}: tem {qtd_user}, precisa {qtd_necessaria}")
                    
                    if faltando:
                        embed_erro = discord.Embed(
                            title="❌ Materiais Insuficientes",
                            description="Você não tem todos os materiais:\n\n" + "\n".join(faltando),
                            color=discord.Color.red()
                        )
                        await button_interaction.followup.send(embed=embed_erro, ephemeral=True)
                        return
                    
                    # Remover recursos
                    for mat_id, qtd in materiais.items():
                        self.ctx.remove_item(interaction.user.id, mat_id, qtd)
                    self.ctx.remove_almas(interaction.user.id, custo)
                    
                    # Aguardar 2 segundos
                    await asyncio.sleep(2)
                    
                    # Determinar sucesso
                    taxa_sucesso = receita.get("taxa_sucesso", 0.5)
                    sucesso = random.random() <= taxa_sucesso
                    
                    if sucesso:
                        # Adicionar item forjado
                        self.ctx.add_item(interaction.user.id, item_id, 1)
                        
                        embed_resultado = discord.Embed(
                            title="✨ FORJA BEM-SUCEDIDA! ✨",
                            description=f"Você criou: {receita['emoji']} **{receita['nome']}**\n\n📜 {receita['descricao']}",
                            color=discord.Color.gold()
                        )
                        embed_resultado.add_field(name="💰 Custo", value=f"{custo} {self.ctx.emoji_alma}", inline=True)
                        embed_resultado.add_field(name="📊 Taxa de Sucesso", value=f"{taxa_sucesso*100:.0f}%", inline=True)
                    else:
                        embed_resultado = discord.Embed(
                            title="💥 FALHA NA FORJA! 💥",
                            description=f"A forja de **{receita['nome']}** falhou!\nSeus materiais foram perdidos...",
                            color=discord.Color.red()
                        )
                        embed_resultado.add_field(name="📊 Taxa de Sucesso", value=f"{taxa_sucesso*100:.0f}%", inline=False)
                    
                    await button_interaction.followup.send(embed=embed_resultado, ephemeral=False)
                
                return callback
        
        # Criar embed inicial
        embed = discord.Embed(
            title="⚒️ Sistema de Forja",
            description=f"Refine seus minérios para criar itens poderosos!\n\n**Suas Souls:** {user_almas} {self.emoji_alma}\n\n**Receitas Disponíveis:**",
            color=0xFF4500
        )
        
        for item_id, receita in receitas_forja.items():
            materiais_text = "\n".join([f"• {mat}: {qtd}x" for mat, qtd in receita.get("materiais", {}).items()])
            taxa = receita.get("taxa_sucesso", 0.5) * 100
            embed.add_field(
                name=f"{receita['emoji']} {receita['nome']}",
                value=f"{receita['descricao']}\n**Materiais:**\n{materiais_text}\n**Custo:** {receita.get('custo_souls', 0)} {self.emoji_alma}\n**Taxa:** {taxa:.0f}%",
                inline=True
            )
        
        view = ForjaView(self, receitas_forja, itens_inv, user_almas)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)
    
    async def autocomplete_item_vender(self, interaction: discord.Interaction, current: str):
        """Autocomplete para mostrar itens que o usuário pode vender"""
        user_inv = self.get_user_inventory(interaction.user.id)
        itens_inv = user_inv.get("itens", {})
        
        # Pegar informações dos itens de todas as categorias
        db = self.load_json()
        itens_info = {}
        
        # Adicionar itens do BD (craft, forja, shop)
        for categoria in ["itens_craft", "itens_forja", "itens_passivos", "loja_items"]:
            cat_items = db.get(categoria, {})
            for item_id, item_data in cat_items.items():
                if item_id in itens_inv and itens_inv[item_id] > 0:
                    emoji = item_data.get("emoji", "⭐")
                    nome = self.display_name(item_data)
                    itens_info[item_id] = f"{emoji} {nome}"
        
        # Adicionar lootboxes (embutidos na classe)
        for box_id, box_data in self.lootboxes.items():
            if box_id in itens_inv and itens_inv[box_id] > 0:
                itens_info[box_id] = f"{box_data['emoji']} {box_data['nome']}"
        
        # Adicionar itens de RPG da loja (espada_madeira, etc)
        for item_id, item_data in self.itens_rpg_loja.items():
            if item_id in itens_inv and itens_inv[item_id] > 0:
                emoji = item_data.get("emoji", "⭐")
                nome = self.display_name(item_data)
                itens_info[item_id] = f"{emoji} {nome}"
        
        # Criar lista de escolhas
        itens_disponiveis = []
        for item_id, nome in itens_info.items():
            quantidade = itens_inv.get(item_id, 0)
            if quantidade > 0:
                itens_disponiveis.append(
                    app_commands.Choice(
                        name=f"{nome} (x{quantidade})",
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
    
    @app_commands.command(name="vender", description="Anuncie um item no mercado entre jogadores")
    @app_commands.describe(item="Escolha um item para vender", valor="Preço por unidade", quantidade="Quantidade (padrão: 1)")
    @app_commands.autocomplete(item=autocomplete_item_vender)
    async def vender(self, interaction: discord.Interaction, item: str, valor: int, quantidade: int = 1):
        """Cria um anúncio de venda no mercado com preço definido"""
        db = self.load_json()
        user_inv = self.get_user_inventory(interaction.user.id)
        itens_inv = user_inv.get("itens", {})

        if valor <= 0:
            await interaction.response.send_message("❌ Informe um valor válido maior que zero.", ephemeral=True)
            return

        # Validar se o item existe no mapeamento de itens conhecidos
        item_data = None
        # Procurar nas fontes conhecidas
        fontes = [self.lootboxes, self.itens_passivos, self.itens_rpg_loja, db.get("loja_items", {}), db.get("itens_craft", {}), db.get("itens_forja", {})]
        for fonte in fontes:
            if item in fonte:
                item_data = fonte[item]
                break

        if not item_data:
            await interaction.response.send_message("❌ Item não encontrado nas categorias conhecidas.", ephemeral=True)
            return

        if item not in itens_inv or itens_inv[item] < quantidade:
            await interaction.response.send_message(
                f"❌ Você não tem {quantidade}x desse item para anunciar.",
                ephemeral=True
            )
            return

        # Reservar itens do inventário (remover ao anunciar)
        reservado = self.remove_item(interaction.user.id, item, quantidade)
        if not reservado:
            await interaction.response.send_message("❌ Falha ao reservar itens para o anúncio.", ephemeral=True)
            return

        listing_id = self.add_market_listing(interaction.user.id, item, quantidade, valor)

        emoji = item_data.get("emoji", "⭐")
        nome = item_data.get("nome", item)
        embed = discord.Embed(
            title="✅ Anúncio Criado",
            description=f"Você anunciou **{quantidade}x** {emoji} **{nome}** por **{valor}** {self.emoji_alma} cada.",
            color=discord.Color.green()
        )
        embed.add_field(name="ID do anúncio", value=listing_id, inline=False)
        embed.set_footer(text="Use /mercado para ver e outras pessoas comprarem.")
        await interaction.response.send_message(embed=embed, ephemeral=False)
    
    @app_commands.command(name="mercado", description="Veja anúncios e compre de outros jogadores")
    async def mercado(self, interaction: discord.Interaction):
        """Lista anúncios do mercado e permite compra via botões"""
        db = self.load_json()
        db = self.ensure_mercado(db)
        listings = db["mercado"].get("listings", [])

        if not listings:
            embed_vazio = discord.Embed(
                title="🏪 Mercado Global",
                description="Nenhum anúncio no momento. Use `/vender` para anunciar seus itens.",
                color=0x2ECC71
            )
            await interaction.response.send_message(embed=embed_vazio, ephemeral=False)
            return

        # Renderizar primeira página de até 5 anúncios com botões de compra
        class MercadoView(discord.ui.View):
            def __init__(self, ctx_self, all_listings):
                super().__init__(timeout=300)
                self.ctx = ctx_self
                self.listings = all_listings[:5]
                for l in self.listings:
                    btn = discord.ui.Button(
                        label=f"Comprar {l['item_id']} ({l['quantidade']}x) - {l['valor']}",
                        style=discord.ButtonStyle.success,
                        custom_id=f"comprar_{l['id']}"
                    )
                    btn.callback = self._make_buy_callback(l)
                    self.add_item(btn)

            def _make_buy_callback(self, listing):
                async def callback(button_interaction: discord.Interaction):
                    if button_interaction.user.id == int(listing.get("seller_id")):
                        await button_interaction.response.send_message("❌ Você não pode comprar seu próprio anúncio.", ephemeral=True)
                        return

                    # Verificar saldo
                    total_price = int(listing.get("valor", 0)) * int(listing.get("quantidade", 1))
                    saldo = self.ctx.get_almas(button_interaction.user.id)
                    if saldo < total_price:
                        await button_interaction.response.send_message(
                            f"❌ Souls insuficientes. Você precisa de {total_price} {self.ctx.emoji_alma}.",
                            ephemeral=True
                        )
                        return

                    # Cobrar comprador
                    self.ctx.remove_almas(button_interaction.user.id, total_price)

                    # Calcular taxa e repasse
                    taxa = self.ctx.mercado_taxa
                    repasse = int(total_price * (1 - taxa))

                    # Pagar vendedor e entregar item
                    seller_id = int(listing.get("seller_id"))
                    self.ctx.add_almas(seller_id, repasse)
                    self.ctx.add_item(button_interaction.user.id, listing.get("item_id"), int(listing.get("quantidade", 1)))

                    # Remover anúncio
                    self.ctx.remove_market_listing(listing.get("id"))

                    # DM ao vendedor
                    try:
                        seller_user = self.ctx.bot.get_user(seller_id) or await self.ctx.bot.fetch_user(seller_id)
                        if seller_user:
                            dm_embed = discord.Embed(
                                title="📬 Venda Concluída",
                                description=(
                                    f"Seu anúncio foi comprado por <@{button_interaction.user.id}>!\n"
                                    f"Item: **{listing.get('item_id')}** x{listing.get('quantidade')}\n"
                                    f"Valor total: **{total_price}** {self.ctx.emoji_alma}\n"
                                    f"Taxa do mercado: **{int(total_price * taxa)}** {self.ctx.emoji_alma}\n"
                                    f"Você recebeu: **{repasse}** {self.ctx.emoji_alma}"
                                ),
                                color=discord.Color.blue()
                            )
                            await seller_user.send(embed=dm_embed)
                    except Exception:
                        pass

                    # Confirmação ao comprador
                    embed_ok = discord.Embed(
                        title="✅ Compra realizada",
                        description=(
                            f"Você comprou **{listing.get('item_id')}** x{listing.get('quantidade')} por **{total_price}** {self.ctx.emoji_alma}.\n"
                            f"O vendedor recebeu **{repasse}** {self.ctx.emoji_alma} (taxa {int(taxa*100)}%)."
                        ),
                        color=discord.Color.green()
                    )
                    await button_interaction.response.send_message(embed=embed_ok, ephemeral=False)

                return callback

        # Montar embed
        embed = discord.Embed(
            title="🏪 Mercado Global",
            description=f"Taxa do mercado: {int(self.mercado_taxa*100)}% por venda",
            color=0x2ECC71
        )
        for l in listings[:5]:
            seller_mention = f"<@{l.get('seller_id')}>"
            embed.add_field(
                name=f"{l.get('item_id')} x{l.get('quantidade')}",
                value=f"Preço: {l.get('valor')} {self.emoji_alma} cada\nVendedor: {seller_mention}\nID: `{l.get('id')}`",
                inline=False
            )

        view = MercadoView(self, listings)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)


async def setup(bot):
    if bot.get_cog("Loja") is None:
        await bot.add_cog(Loja(bot))
