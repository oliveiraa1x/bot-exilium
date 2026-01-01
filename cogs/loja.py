import asyncio
import json
import random
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands


class Loja(commands.Cog):
    """Sistema de Loja, Compra e Venda de Items (dados em db.json)"""
    
    def __init__(self, bot):
        self.bot = bot

    def get_economia_data(self) -> dict:
        """Obtém dados de economia com fallback para o JSON local."""
        economia = {}

        db_manager = getattr(self.bot, "db_manager", None)
        if db_manager:
            economia = db_manager.get_economia() or {}

        if not economia:
            try:
                economia = self.bot.db().get("_economia", {})
            except Exception:
                economia = {}

        if not economia:
            try:
                data_path = Path(__file__).parent.parent / "data" / "db.json"
                with data_path.open("r", encoding="utf-8") as fp:
                    economia = json.load(fp).get("_economia", {})
            except Exception:
                economia = {}

        return economia

    # ==================== HELPERS ====================

    def ensure_user(self, user_id: int) -> str:
        """Garante o registro do usuário no db.json."""
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
        db = self.bot.db()
        uid = self.ensure_user(user_id)
        user_data = db.get(uid, {})
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
        db = self.bot.db()
        uid = self.ensure_user(user_id)
        user_inv = db.get(uid, {})
        itens = user_inv.setdefault("itens", {})
        itens[item_id] = itens.get(item_id, 0) + quantidade
        user_inv["itens"] = itens
        db[uid] = user_inv
        self.bot.save_db(db)

    def remove_item(self, user_id: int, item_id: str, quantidade: int = 1) -> bool:
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

    def get_almas(self, user_id: int) -> int:
        uid = self.ensure_user(user_id)
        return self.bot.db().get(uid, {}).get("soul", 0)

    def add_almas(self, user_id: int, quantidade: int):
        db = self.bot.db()
        uid = self.ensure_user(user_id)
        user_inv = db.get(uid, {})
        user_inv["soul"] = user_inv.get("soul", 0) + quantidade
        db[uid] = user_inv
        self.bot.save_db(db)

    def remove_almas(self, user_id: int, quantidade: int) -> bool:
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
    
    @app_commands.command(name="loja", description="Acesse a loja e compre itens com almas")
    async def loja(self, interaction: discord.Interaction):
        """Mostra loja de itens (dados em db.json->_economia.loja_items)."""
        economia = self.get_economia_data()

        loja_items = economia.get("loja_items", {})
        user_almas = self.get_almas(interaction.user.id)

        # Categoriza os items
        categorias = {"consumivel": [], "lootbox": [], "especial": []}
        
        for item_id, item_data in loja_items.items():
            tipo = item_data.get("tipo", "consumivel")
            if tipo in categorias:
                categorias[tipo].append((item_id, item_data))

        # View com dropdown para selecionar items
        class LojaView(discord.ui.View):
            def __init__(self, parent, items_dict, loja_ref, user_almas_val):
                super().__init__(timeout=300)
                self.parent = parent
                self.items_dict = items_dict
                self.loja_ref = loja_ref
                self.user_almas_val = user_almas_val
                self.current_category = "consumivel"

            async def show_category(self, interaction: discord.Interaction, category: str):
                """Mostra a categoria selecionada."""
                self.current_category = category
                items_list = self.items_dict.get(category, [])
                
                embed = discord.Embed(
                    title=f"🏪 Loja - {category.upper()}",
                    description=f"Suas almas: **{self.user_almas_val}** <:alma:1456309061057511535>",
                    color=0xFF6B9D
                )
                
                if not items_list:
                    embed.add_field(name="Status", value="Nenhum item disponível nesta categoria.", inline=False)
                else:
                    items_text = ""
                    for idx, (item_id, item_data) in enumerate(items_list, 1):
                        emoji = item_data.get("emoji", "⭐")
                        nome = item_data.get("nome", "Item")
                        valor = item_data.get("valor", 0)
                        items_text += f"**{idx}.** {emoji} {nome} ({valor} <:alma:1456309061057511535>)\n"
                    
                    embed.add_field(name="Items disponíveis:", value=items_text, inline=False)
                
                # Limpa e reconstrói view
                self.clear_items()
                
                # Botões de categoria
                btn_consumivel = discord.ui.Button(label="Consumíveis", style=discord.ButtonStyle.primary)
                btn_lootbox = discord.ui.Button(label="Lootboxes", style=discord.ButtonStyle.primary)
                btn_especial = discord.ui.Button(label="Especiais", style=discord.ButtonStyle.danger)
                
                async def callback_consumivel(i: discord.Interaction):
                    await self.show_category(i, "consumivel")
                
                async def callback_lootbox(i: discord.Interaction):
                    await self.show_category(i, "lootbox")
                
                async def callback_especial(i: discord.Interaction):
                    await self.show_category(i, "especial")
                
                btn_consumivel.callback = callback_consumivel
                btn_lootbox.callback = callback_lootbox
                btn_especial.callback = callback_especial
                
                self.add_item(btn_consumivel)
                self.add_item(btn_lootbox)
                self.add_item(btn_especial)
                
                # Select para escolher item
                if items_list:
                    options = [
                        discord.SelectOption(
                            label=f"{item_data.get('nome', 'Item')[:50]}",
                            value=item_id,
                            emoji=item_data.get('emoji', '⭐')
                        )
                        for item_id, item_data in items_list
                    ]
                    select = discord.ui.Select(placeholder="Escolha um item", options=options)
                    
                    async def callback_select(i: discord.Interaction):
                        await self.show_item_detail(i)
                    
                    select.callback = callback_select
                    self.add_item(select)
                
                await interaction.response.edit_message(embed=embed, view=self)

            async def show_item_detail(self, interaction: discord.Interaction):
                """Mostra detalhes do item selecionado."""
                item_id = interaction.data["values"][0]
                item_data = self.loja_ref.get(item_id, {})
                
                emoji = item_data.get("emoji", "⭐")
                nome = item_data.get("nome", "Item")
                valor = item_data.get("valor", 0)
                descricao = item_data.get("descricao", "Sem descrição")
                
                embed = discord.Embed(
                    title=f"{emoji} {nome}",
                    description=descricao,
                    color=0xFF6B9D
                )
                embed.add_field(name="Custo", value=f"**{valor}** <:alma:1456309061057511535>", inline=True)
                embed.add_field(name="Suas Almas", value=f"**{self.user_almas_val}** <:alma:1456309061057511535>", inline=True)
                
                self.clear_items()
                
                # Botões de categoria
                btn_consumivel = discord.ui.Button(label="Consumíveis", style=discord.ButtonStyle.primary)
                btn_lootbox = discord.ui.Button(label="Lootboxes", style=discord.ButtonStyle.primary)
                btn_especial = discord.ui.Button(label="Especiais", style=discord.ButtonStyle.danger)
                
                async def callback_consumivel(i: discord.Interaction):
                    await self.show_category(i, "consumivel")
                
                async def callback_lootbox(i: discord.Interaction):
                    await self.show_category(i, "lootbox")
                
                async def callback_especial(i: discord.Interaction):
                    await self.show_category(i, "especial")
                
                btn_consumivel.callback = callback_consumivel
                btn_lootbox.callback = callback_lootbox
                btn_especial.callback = callback_especial
                
                self.add_item(btn_consumivel)
                self.add_item(btn_lootbox)
                self.add_item(btn_especial)
                
                # Select para escolher item
                items_list = self.items_dict.get(self.current_category, [])
                if items_list:
                    options = [
                        discord.SelectOption(
                            label=f"{it_data.get('nome', 'Item')[:50]}",
                            value=it_id,
                            emoji=it_data.get('emoji', '⭐')
                        )
                        for it_id, it_data in items_list
                    ]
                    select = discord.ui.Select(placeholder="Escolha um item", options=options)
                    
                    async def callback_select(i: discord.Interaction):
                        await self.show_item_detail(i)
                    
                    select.callback = callback_select
                    self.add_item(select)
                
                # Botão comprar
                if self.user_almas_val >= valor:
                    embed.color = discord.Color.green()
                    btn_comprar = discord.ui.Button(label="💳 Comprar", style=discord.ButtonStyle.success)
                    
                    async def callback_comprar(i: discord.Interaction):
                        user_almas_check = self.parent.get_almas(i.user.id)
                        
                        if user_almas_check < valor:
                            embed_err = discord.Embed(
                                title="❌ Almas insuficientes",
                                description=f"Você tem: **{user_almas_check}** almas\nNecessário: **{valor}** almas",
                                color=discord.Color.red()
                            )
                            await i.response.send_message(embed=embed_err, ephemeral=True)
                            return
                        
                        self.parent.remove_almas(i.user.id, valor)
                        self.parent.add_item(i.user.id, item_id, 1)
                        
                        embed_success = discord.Embed(
                            title="✅ Compra realizada!",
                            description=f"Você comprou {emoji} **{nome}**",
                            color=discord.Color.green()
                        )
                        embed_success.add_field(name="Custo", value=f"{valor} <:alma:1456309061057511535>", inline=False)
                        embed_success.set_footer(text=f"Almas restantes: {user_almas_check - valor}")
                        
                        await i.response.send_message(embed=embed_success, ephemeral=True)
                    
                    btn_comprar.callback = callback_comprar
                    self.add_item(btn_comprar)
                else:
                    embed.color = discord.Color.red()
                    embed.add_field(name="Status", value="❌ Almas insuficientes", inline=False)
                
                await interaction.response.edit_message(embed=embed, view=self)

        view = LojaView(self, categorias, loja_items, user_almas)
        
        # Mostra a primeira categoria
        items_consumivel = categorias["consumivel"]
        embed = discord.Embed(
            title="🏪 Loja - CONSUMÍVEIS",
            description=f"Suas almas: **{user_almas}** <:alma:1456309061057511535>",
            color=0xFF6B9D
        )
        
        if not items_consumivel:
            embed.add_field(name="Status", value="Nenhum item disponível nesta categoria.", inline=False)
        else:
            items_text = ""
            for idx, (item_id, item_data) in enumerate(items_consumivel, 1):
                emoji = item_data.get("emoji", "⭐")
                nome = item_data.get("nome", "Item")
                valor = item_data.get("valor", 0)
                items_text += f"**{idx}.** {emoji} {nome} ({valor} <:alma:1456309061057511535>)\n"
            
            embed.add_field(name="Items disponíveis:", value=items_text, inline=False)
        
        # Cria o view com botões
        view.clear_items()
        
        btn_consumivel = discord.ui.Button(label="Consumíveis", style=discord.ButtonStyle.primary)
        btn_lootbox = discord.ui.Button(label="Lootboxes", style=discord.ButtonStyle.primary)
        btn_especial = discord.ui.Button(label="Especiais", style=discord.ButtonStyle.danger)
        
        async def callback_consumivel(i: discord.Interaction):
            await view.show_category(i, "consumivel")
        
        async def callback_lootbox(i: discord.Interaction):
            await view.show_category(i, "lootbox")
        
        async def callback_especial(i: discord.Interaction):
            await view.show_category(i, "especial")
        
        btn_consumivel.callback = callback_consumivel
        btn_lootbox.callback = callback_lootbox
        btn_especial.callback = callback_especial
        
        view.add_item(btn_consumivel)
        view.add_item(btn_lootbox)
        view.add_item(btn_especial)
        
        # Select para escolher item
        if items_consumivel:
            options = [
                discord.SelectOption(
                    label=f"{item_data.get('nome', 'Item')[:50]}",
                    value=item_id,
                    emoji=item_data.get('emoji', '⭐')
                )
                for item_id, item_data in items_consumivel
            ]
            select = discord.ui.Select(placeholder="Escolha um item", options=options)
            
            async def callback_select(i: discord.Interaction):
                await view.show_item_detail(i)
            
            select.callback = callback_select
            view.add_item(select)
        
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="comprar", description="Compre um item da loja")
    @app_commands.describe(item="ID do item para comprar", quantidade="Quantidade (padrão: 1)")
    async def comprar(self, interaction: discord.Interaction, item: str, quantidade: int = 1):
        """Compra um item da loja usando almas (soul)."""
        economia = self.get_economia_data()
        loja_items = economia.get("loja_items", {})

        if item not in loja_items:
            await interaction.response.send_message("❌ Item não existe na loja!", ephemeral=True)
            return

        item_data = loja_items[item]
        valor_unitario = item_data.get("valor", 0)
        custo_total = valor_unitario * max(1, quantidade)

        user_almas = self.get_almas(interaction.user.id)

        if user_almas < custo_total:
            embed = discord.Embed(
                title="❌ Almas insuficientes",
                description=f"Você tem: **{user_almas}** almas\nNecessário: **{custo_total}** almas",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        self.remove_almas(interaction.user.id, custo_total)
        self.add_item(interaction.user.id, item, quantidade)

        embed = discord.Embed(
            title="✅ Compra realizada!",
            description=f"Você comprou **{quantidade}x** {item_data.get('emoji', '')} **{item_data.get('nome', 'Item')}**",
            color=discord.Color.green()
        )
        embed.add_field(name="Custo", value=f"{custo_total} almas", inline=False)
        embed.set_footer(text=f"Almas restantes: {user_almas - custo_total}")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="craft", description="Crafta um item usando materiais")
    @app_commands.describe(item="ID do item para craftar")
    async def craft(self, interaction: discord.Interaction, item: str):
        """Crafta um item"""
        economia = self.get_economia_data()
        itens_craft = economia.get("itens_craft", {})

        if item not in itens_craft:
            embed = discord.Embed(
                title="🔨 Craft - Items Disponíveis",
                description="Use `/craft item:nome_do_item`",
                color=0xFF9500
            )
            for craft_id, craft_data in list(itens_craft.items())[:10]:
                emoji = craft_data.get("emoji", "⭐")
                nome = craft_data.get("nome", craft_id)
                raridade = craft_data.get("raridade", "comum")
                embed.add_field(
                    name=f"{emoji} {nome}",
                    value=f"ID: `{craft_id}`\nRaridade: {raridade}",
                    inline=False
                )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        item_data = itens_craft[item]
        nome_item = item_data.get("nome", item)
        emoji = item_data.get("emoji", "⭐")

        embed = discord.Embed(
            title=f"🔨 Crafting: {emoji} {nome_item}",
            color=self.get_cor_embed(item_data.get("raridade", "comum"))
        )
        embed.description = f"Sistema de craft em desenvolvimento para: `{item}`"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="forjar", description="Forja uma arma poderosa")
    @app_commands.describe(item="ID da arma para forjar")
    async def forjar(self, interaction: discord.Interaction, item: str):
        """Forja uma arma usando recursos do inventário."""
        await interaction.response.defer()

        economia = self.get_economia_data()
        itens_forja = economia.get("itens_forja", {})
        user_inv = self.get_user_inventory(interaction.user.id)
        user_almas = self.get_almas(interaction.user.id)

        if item not in itens_forja:
            embed = discord.Embed(
                title="⚒️ Forja - Armas Disponíveis",
                description="Use `/forjar item:nome_da_arma`",
                color=0xFF9500
            )
            for forja_id, forja_data in itens_forja.items():
                emoji = forja_data.get("emoji", "⚔️")
                nome = forja_data.get("nome", forja_id)
                custo = forja_data.get("custo_almas", 0)
                taxa_falha = forja_data.get("taxa_falha", 0) * 100
                embed.add_field(
                    name=f"{emoji} {nome}",
                    value=f"ID: `{forja_id}`\nCusto: {custo} almas | Falha: {taxa_falha:.0f}%",
                    inline=False
                )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        arma_data = itens_forja[item]
        nome_arma = arma_data.get("nome", item)
        emoji = arma_data.get("emoji", "⚔️")
        custo = arma_data.get("custo_almas", 0)
        ingredientes = arma_data.get("ingredientes", {})
        taxa_falha = arma_data.get("taxa_falha", 0.15)

        if user_almas < custo:
            embed = discord.Embed(
                title="❌ Almas insuficientes",
                description=f"Você tem: **{user_almas}** almas\nNecessário: **{custo}** almas",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        itens_inv = user_inv.get("itens", {})
        faltando = []
        for ing_id, ing_qtd in ingredientes.items():
            qtd_user = itens_inv.get(ing_id, 0)
            if qtd_user < ing_qtd:
                faltando.append(f"{ing_id}: você tem {qtd_user}, precisa de {ing_qtd}")

        if faltando:
            embed = discord.Embed(
                title="❌ Ingredientes insuficientes",
                description="Você não tem todos os materiais necessários:\n\n" + "\n".join(faltando),
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        for ing_id, ing_qtd in ingredientes.items():
            self.remove_item(interaction.user.id, ing_id, ing_qtd)
        self.remove_almas(interaction.user.id, custo)

        await asyncio.sleep(2)

        sucesso = random.random() > taxa_falha

        if sucesso:
            self.add_item(interaction.user.id, item, 1)
            embed = discord.Embed(
                title="✨ FORJA BEM-SUCEDIDA! ✨",
                description=f"Você criou: **{emoji} {nome_arma}**",
                color=discord.Color.gold()
            )
            embed.add_field(name="Custo", value=f"{custo} almas", inline=True)
            embed.add_field(name="Taxa de Falha", value=f"{taxa_falha*100:.0f}%", inline=True)
        else:
            embed = discord.Embed(
                title="💥 FALHA NA FORJA! 💥",
                description=f"A forja de **{nome_arma}** falhou e seus materiais foram perdidos!",
                color=discord.Color.red()
            )
            embed.add_field(name="Taxa de Falha", value=f"{taxa_falha*100:.0f}%", inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="vender", description="Venda um item para a loja")
    @app_commands.describe(item="ID do item para vender", quantidade="Quantidade (padrão: 1)")
    async def vender(self, interaction: discord.Interaction, item: str, quantidade: int = 1):
        """Vende um item para a loja e converte em almas."""
        economia = getattr(self.bot, "db_manager", None)
        economia = economia.get_economia() if economia else {}
        user_inv = self.get_user_inventory(interaction.user.id)
        itens_inv = user_inv.get("itens", {})

        item_data = None
        valor_unitario = 0

        for categoria in ["itens_craft", "itens_forja", "itens_passivos", "loja_items"]:
            cat_items = economia.get(categoria, {})
            if item in cat_items:
                item_data = cat_items[item]
                raridade = item_data.get("raridade", "comum")
                valor_base = item_data.get("valor_base", item_data.get("valor", 0))
                multiplicador = economia.get("raridades", {}).get(raridade, {}).get("valor_multiplicador", 1.0)
                valor_unitario = int(valor_base * multiplicador * 0.7)
                break

        if not item_data:
            await interaction.response.send_message("❌ Item não encontrado!", ephemeral=True)
            return

        if item not in itens_inv or itens_inv[item] < quantidade:
            await interaction.response.send_message(
                f"❌ Você não tem {quantidade}x desse item!",
                ephemeral=True
            )
            return

        valor_total = valor_unitario * quantidade

        self.remove_item(interaction.user.id, item, quantidade)
        self.add_almas(interaction.user.id, valor_total)

        emoji = item_data.get("emoji", "⭐")
        nome = item_data.get("nome", item)

        embed = discord.Embed(
            title="✅ Venda realizada!",
            description=f"Você vendeu **{quantidade}x** {emoji} **{nome}**",
            color=discord.Color.green()
        )
        embed.add_field(name="Valor unitário", value=f"{valor_unitario} almas", inline=True)
        embed.add_field(name="Valor total", value=f"{valor_total} almas", inline=True)
        embed.set_footer(text="Você recebeu 70% do valor base do item")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="mercado", description="Sistema de mercado entre players")
    async def mercado(self, interaction: discord.Interaction):
        """Mercado entre players (em desenvolvimento)"""
        embed = discord.Embed(
            title="🏪 Mercado Global",
            description="""
**Mercado em desenvolvimento!**

Este será um sistema onde você pode:
- 📤 Colocar itens à venda
- 📥 Comprar itens de outros players
- 💰 Negociar preços
- 📊 Ver histórico de vendas

**Funcionalidades:**
- Taxa de imposto: 5% das vendas
- Sistema de oferta/contra-oferta
- Ranking de vendedores
- Histórico de transações
            """,
            color=0x2ECC71
        )
        embed.set_footer(text="Volte em breve!")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="abrir-lootbox", description="Abra uma lootbox e ganhe recompensas")
    @app_commands.describe(nivel="Nível da lootbox (1, 2 ou 3)")
    async def abrir_lootbox(self, interaction: discord.Interaction, nivel: int = 1):
        """Abre uma lootbox e revela as recompensas"""
        await interaction.response.defer()

        if nivel not in [1, 2, 3]:
            embed = discord.Embed(
                title="❌ Nível inválido",
                description="Use nível 1, 2 ou 3",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=False)
            return

        economia = self.get_economia_data()
        lootbox_recompensas = economia.get("lootbox_recompensas", {})
        
        if f"nivel{nivel}" not in lootbox_recompensas:
            embed = discord.Embed(
                title="❌ Lootbox não encontrada",
                description=f"Nível {nivel} não está configurado",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=False)
            return

        # Verifica se tem a lootbox no inventário
        user_inv = self.get_user_inventory(interaction.user.id)
        itens_inv = user_inv.get("itens", {})
        lootbox_id = f"lootbox_nivel{nivel}"

        if itens_inv.get(lootbox_id, 0) <= 0:
            embed = discord.Embed(
                title="❌ Você não tem essa lootbox",
                description=(
                    f"Compre uma **Baú Nível {nivel}** na loja primeiro.\n"
                    f"Use `/loja` para ver a loja ou `/comprar item:{lootbox_id}`."
                ),
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=False)
            return

        # Remove a lootbox do inventário
        self.remove_item(interaction.user.id, lootbox_id, 1)

        # Define as raridades possíveis e suas chances
        raridades_disponiveis = list(lootbox_recompensas[f"nivel{nivel}"].keys())
        raridade_chances = {
            "comum": 60 if nivel == 1 else 40 if nivel == 2 else 25,
            "raro": 30 if nivel == 1 else 40 if nivel == 2 else 40,
            "epico": 10 if nivel >= 2 else 0,
            "lendario": 0 if nivel < 3 else 20
        }

        # Sorteia a raridade
        import random
        total = sum(raridade_chances.values())
        aleatorio = random.random() * total
        raridade_sorteada = None
        acumulado = 0
        
        for raro, chance in raridade_chances.items():
            acumulado += chance
            if aleatorio <= acumulado and raro in raridades_disponiveis:
                raridade_sorteada = raro
                break
        
        if not raridade_sorteada:
            raridade_sorteada = raridades_disponiveis[0]

        # Sorteia a recompensa da raridade
        recompensas_raridade = lootbox_recompensas[f"nivel{nivel}"][raridade_sorteada]
        recompensa = random.choice(recompensas_raridade)

        # Processa a recompensa
        embed_color = self.get_cor_embed(raridade_sorteada)
        recompensa_texto = ""
        moedas_ganhas = 0

        if recompensa["tipo"] == "moeda":
            moedas_ganhas = random.randint(recompensa["min"], recompensa["max"])
            self.add_almas(interaction.user.id, moedas_ganhas)
            recompensa_texto = f"**{moedas_ganhas}** 💰 almas"
        elif recompensa["tipo"] == "item":
            item_id = recompensa["id"]
            loja_items = economia.get("loja_items", {})
            item_data = loja_items.get(item_id, {})
            emoji = item_data.get("emoji", "⭐")
            nome = item_data.get("nome", item_id)
            self.add_item(interaction.user.id, item_id, 1)
            recompensa_texto = f"{emoji} **{nome}**"

        # Cria a embed com o resultado
        emoji_lootbox = "📦" if nivel == 1 else "🎁" if nivel == 2 else "⭐"
        
        embed = discord.Embed(
            title=f"✨ {emoji_lootbox} LOOTBOX ABERTA! ✨",
            description=f"Você abriu uma **Baú Nível {nivel}** e ganhou:",
            color=embed_color
        )

        # Mapeia raridades para emojis
        emoji_raridade = {
            "comum": "⚪",
            "raro": "🔵",
            "epico": "🟣",
            "lendario": "🟡",
            "ancestral": "🔴"
        }

        embed.add_field(
            name=f"{emoji_raridade.get(raridade_sorteada, '⭐')} {raridade_sorteada.upper()}",
            value=recompensa_texto,
            inline=False
        )

        embed.set_footer(text=f"Parabéns! Você ganhou uma ótima recompensa!")
        await interaction.followup.send(embed=embed, ephemeral=False)

    @app_commands.command(name="ranking", description="Veja o ranking de almas")
    async def ranking(self, interaction: discord.Interaction):
        """Mostra ranking de almas (soul) usando db.json"""
        await interaction.response.defer()

        db = self.bot.db()
        ranking = []
        for uid, user_data in db.items():
            try:
                user_id_int = int(uid)
            except ValueError:
                continue
            almas = user_data.get("soul", 0)
            ranking.append((user_id_int, almas))

        ranking = sorted(ranking, key=lambda x: x[1], reverse=True)[:10]

        embed = discord.Embed(
            title="🏆 Ranking de Almas",
            description="Top 10 mais ricos",
            color=0xFFD700
        )

        if not ranking:
            embed.description = "Ainda não há registros."
        else:
            for idx, (user_id_int, almas) in enumerate(ranking, 1):
                try:
                    user = await self.bot.fetch_user(user_id_int)
                    nome = user.name
                except Exception:
                    nome = f"User {user_id_int}"

                medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"#{idx}"
                embed.add_field(
                    name=f"{medal} {nome}",
                    value=f"**{almas:,}** almas",
                    inline=False
                )

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Loja(bot))