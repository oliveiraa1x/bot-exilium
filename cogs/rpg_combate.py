# rpg_combate.py - Mini game de RPG com combate contra mobs integrado com economia

import discord
import json
import random
import datetime
from pathlib import Path
from discord.ext import commands
from discord import app_commands

# ==============================
# Sistema de Banco de Dados para Economia
# ==============================
DB_PATH = Path(__file__).parent.parent / "data" / "db.json"


def ensure_db_file() -> None:
    """Garante que o arquivo de banco de dados existe"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        DB_PATH.write_text("{}", encoding="utf-8")


def load_economia_db() -> dict:
    """Carrega o banco de dados de economia"""
    ensure_db_file()
    try:
        with DB_PATH.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except json.JSONDecodeError:
        return {}


def save_economia_db(data: dict) -> None:
    """Salva o banco de dados de economia"""
    ensure_db_file()
    with DB_PATH.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)


def ensure_user_economia(user_id: int):
    """Garante que o usuário existe no banco de dados de economia"""
    uid = str(user_id)
    db = load_economia_db()
    if uid not in db:
        db[uid] = {
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
            "missoes": [],
            "missoes_completas": []
        }
        save_economia_db(db)
    return uid


def add_soul(user_id: int, amount: int):
    """Adiciona almas (soul) ao usuário"""
    uid = ensure_user_economia(user_id)
    db = load_economia_db()
    db[uid]["soul"] = db[uid].get("soul", 0) + amount
    save_economia_db(db)


# ==============================
# Dados dos Mobs
# ==============================
MOBS = {
    "lobo": {
        "emoji": "🐺",
        "nome": "Lobo Selvagem",
        "vida": 3,
        "ataques": ["Mordida", "Arranho", "Investida"],
        "recompensa_souls": 100,
        "recompensa_xp": 50,
        "gif_ataque": "https://media.giphy.com/media/3o6ZsYq8d0pgLRZQXm/giphy.gif",
        "gif_morte": "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif"
    },
    "urso": {
        "emoji": "🐻",
        "nome": "Urso Feroz",
        "vida": 3,
        "ataques": ["Golpe de Garra", "Investida Poderosa", "Urro"],
        "recompensa_souls": 150,
        "recompensa_xp": 75,
        "gif_ataque": "https://media.giphy.com/media/l0HlDtKo5lWXtKlVm/giphy.gif",
        "gif_morte": "https://media.giphy.com/media/l0MYtKKzpmxvH4XbS/giphy.gif"
    },
    "ogro": {
        "emoji": "👹",
        "nome": "Ogro Guerreiro",
        "vida": 5,
        "ataques": ["Pancada Brutal", "Esmagamento", "Grito de Guerra"],
        "recompensa_souls": 300,
        "recompensa_xp": 150,
        "gif_ataque": "https://media.giphy.com/media/3o7TKB3oifq46DDhOE/giphy.gif",
        "gif_morte": "https://media.giphy.com/media/3o7TKVu6vYMN7rlMhW/giphy.gif"
    },
    "dragao": {
        "emoji": "🐉",
        "nome": "Dragão Ancião",
        "vida": 8,
        "ataques": ["Baforada de Fogo", "Golpe de Cauda", "Voo Rasante"],
        "recompensa_souls": 800,
        "recompensa_xp": 400,
        "gif_ataque": "https://media.giphy.com/media/l0HlNaQ6gWfllcjDO/giphy.gif",
        "gif_morte": "https://media.giphy.com/media/3o6Ztl7RvfNGzgWQ5a/giphy.gif"
    },
    "boss_sombrio": {
        "emoji": "👿",
        "nome": "Lorde das Sombras",
        "vida": 12,
        "ataques": ["Lâmina das Trevas", "Correntes Sombrias", "Explosão Negra"],
        "recompensa_souls": 2000,
        "recompensa_xp": 1000,
        "gif_ataque": "https://media.giphy.com/media/3o7TKVuY3bXKOKU6u4/giphy.gif",
        "gif_morte": "https://media.giphy.com/media/3o7TKOVq7xZT3VRHMs/giphy.gif"
    }
}

# ==============================
# Dados dos Equipamentos RPG
# ==============================
EQUIPAMENTOS_RPG = {
    # Armas
    "espada_madeira": {"nome": "🪵 Espada de Madeira", "tipo": "arma", "ataque": 2, "bonus_fracionario": 0.5},
    "espada_cobre": {"nome": "⚔️ Espada de Cobre", "tipo": "arma", "ataque": 5},
    "espada_ferro": {"nome": "⚔️ Espada de Ferro", "tipo": "arma", "ataque": 10},
    "espada_ouro": {"nome": "⚔️ Espada de Ouro", "tipo": "arma", "ataque": 20},
    # Armaduras
    "armadura_ferro": {"nome": "🛡️ Armadura de Ferro", "tipo": "armadura", "defesa": 15}
}


# ==============================
# View com os Botões de Combate
# ==============================
class CombateButtons(discord.ui.View):
    def __init__(self, user_id: int, mob_type: str, arma_equipada: dict = None, armadura_equipada: dict = None, timeout: float = 600.0):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.mob_type = mob_type
        self.mob = MOBS[mob_type].copy()
        self.arma_equipada = arma_equipada or {"nome": "Punhos", "ataque": 0}
        self.armadura_equipada = armadura_equipada or {"nome": "Sem Armadura", "defesa": 0}
        # bônus fracionário da arma (ex.: 0.5 = meio coração por ataque em média)
        self.bonus_fracionario = float(self.arma_equipada.get("bonus_fracionario", 0.0))
        self.frac_bonus_acumulado = 0.0
        self.player_vida = 3
        self.mob_vida = self.mob["vida"]
        self.turno_atual = "jogador"
        self.jogador_derrotado = False
        self.mob_derrotado = False
        self.historico = []
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Apenas o jogador original pode interagir!",
                ephemeral=True
            )
            return False
        
        if self.mob_derrotado or self.jogador_derrotado:
            await interaction.response.send_message(
                "❌ O combate já terminou!",
                ephemeral=True
            )
            return False
        
        return True

    @discord.ui.button(label="🗡️ Ataque", style=discord.ButtonStyle.danger)
    async def atacar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.interaction_check(interaction):
            return
        
        # Defer a interação imediatamente
        await interaction.response.defer()
        
        # Jogador ataca (dano base + bônus da arma)
        dano_base = random.randint(1, 2)
        bonus_int = self.arma_equipada.get("ataque", 0) // 5  # Cada 5 de ataque = +1 dano
        # Acumular bônus fracionário e converter em dano inteiro adicional quando atingir 1.0
        self.frac_bonus_acumulado += self.bonus_fracionario
        extra = int(self.frac_bonus_acumulado)
        if extra > 0:
            self.frac_bonus_acumulado -= extra
        dano_jogador = dano_base + bonus_int + extra
        self.mob_vida -= dano_jogador
        arma_nome = self.arma_equipada.get("nome", "Punhos")
        self.historico.append(f"⚔️ Você atacou com **{arma_nome}**! Causou **{dano_jogador} de dano**!")
        
        if self.mob_vida <= 0:
            self.mob_derrotado = True
            await self.enviar_resultado_vitoria(interaction)
            return
        
        # Mob ataca (dano reduzido pela armadura)
        ataque_mob = random.choice(self.mob["ataques"])
        dano_mob_base = random.randint(1, 2)
        reducao_armadura = self.armadura_equipada.get("defesa", 0) // 15  # Cada 15 de defesa = -1 dano
        dano_mob = max(1, dano_mob_base - reducao_armadura)
        self.player_vida -= dano_mob
        self.historico.append(f"🐾 {self.mob['nome']} usou **{ataque_mob}**! Causou **{dano_mob} de dano**!")
        
        if self.player_vida <= 0:
            self.jogador_derrotado = True
            await self.enviar_resultado_derrota(interaction)
            return
        
        await self.atualizar_combate(interaction)

    @discord.ui.button(label="🛡️ Defesa", style=discord.ButtonStyle.primary)
    async def defender(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.interaction_check(interaction):
            return
        
        # Defer a interação imediatamente
        await interaction.response.defer()
        
        # Jogador se defende
        armadura_nome = self.armadura_equipada.get("nome", "Braços")
        self.historico.append(f"🛡️ Você se protegeu com **{armadura_nome}**! Reduzindo dano.")
        
        # Mob ataca com dano reduzido
        ataque_mob = random.choice(self.mob["ataques"])
        dano_mob_base = random.randint(1, 2)
        reducao_total = 1 + (self.armadura_equipada.get("defesa", 0) // 15)
        dano_mob = max(0, dano_mob_base - reducao_total)
        self.player_vida -= dano_mob
        self.historico.append(f"🐾 {self.mob['nome']} usou **{ataque_mob}**! Causou **{dano_mob} de dano**!")
        
        if self.player_vida <= 0:
            self.jogador_derrotado = True
            await self.enviar_resultado_derrota(interaction)
            return
        
        await self.atualizar_combate(interaction)

    @discord.ui.button(label="⚔️ Ataque Duplo", style=discord.ButtonStyle.danger)
    async def ataque_duplo(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.interaction_check(interaction):
            return
        
        # Defer a interação imediatamente
        await interaction.response.defer()
        
        # Jogador faz ataque duplo
        dano_jogador = random.randint(2, 3)
        # Aplicar bônus da arma também no ataque duplo
        bonus_int = self.arma_equipada.get("ataque", 0) // 5
        self.frac_bonus_acumulado += self.bonus_fracionario
        extra = int(self.frac_bonus_acumulado)
        if extra > 0:
            self.frac_bonus_acumulado -= extra
        dano_jogador += (bonus_int + extra)
        self.mob_vida -= dano_jogador
        self.historico.append(f"⚔️ Você atacou com **Ataques Rápidos**! Causou **{dano_jogador} de dano**!")
        
        if self.mob_vida <= 0:
            self.mob_derrotado = True
            await self.enviar_resultado_vitoria(interaction)
            return
        
        # Mob contra-ataca
        ataque_mob = random.choice(self.mob["ataques"])
        dano_mob = random.randint(1, 2)
        self.player_vida -= dano_mob
        self.historico.append(f"🐾 {self.mob['nome']} usou **{ataque_mob}**! Causou **{dano_mob} de dano**!")
        
        if self.player_vida <= 0:
            self.jogador_derrotado = True
            await self.enviar_resultado_derrota(interaction)
            return
        
        await self.atualizar_combate(interaction)

    async def atualizar_combate(self, interaction: discord.Interaction):
        """Atualiza a mensagem de combate"""
        embed = self.criar_embed_combate()
        try:
            await interaction.edit_original_response(embed=embed, view=self)
        except discord.NotFound:
            # Se a mensagem foi deletada ou expirou, usar follow_up
            await interaction.followup.send(embed=embed, view=self)

    def criar_embed_combate(self) -> discord.Embed:
        """Cria o embed com o status do combate"""
        embed = discord.Embed(
            title="⚔️ COMBATE RPG ⚔️",
            color=discord.Color.gold()
        )
        
        # Barra de vida do jogador
        vida_jogador_str = "❤️ " * self.player_vida + "🖤 " * (3 - self.player_vida)
        arma_info = f"⚔️ {self.arma_equipada['nome']} (+{self.arma_equipada.get('ataque', 0)} ATK)"
        armadura_info = f"🛡️ {self.armadura_equipada['nome']} (+{self.armadura_equipada.get('defesa', 0)} DEF)"
        embed.add_field(
            name="<:membro:1456311222315253910> Sua Vida",
            value=f"{vida_jogador_str} ({self.player_vida}/3)\n{arma_info}\n{armadura_info}",
            inline=False
        )
        
        # Barra de vida do mob
        vida_mob_max = self.mob["vida"]
        vida_mob_str = "❤️ " * max(0, self.mob_vida) + "🖤 " * max(0, vida_mob_max - self.mob_vida)
        embed.add_field(
            name=f"{self.mob['emoji']} {self.mob['nome']}",
            value=f"{vida_mob_str} ({max(0, self.mob_vida)}/{vida_mob_max})",
            inline=False
        )
        
        # Histórico dos últimos ataques
        historico_texto = "\n".join(self.historico[-3:]) if self.historico else "Combate iniciado!"
        embed.add_field(
            name="📜 Histórico",
            value=historico_texto,
            inline=False
        )
        
        # Adicionar GIF do mob atacando
        embed.set_image(url=self.mob.get("gif_ataque", ""))
        
        return embed

    async def enviar_resultado_vitoria(self, interaction: discord.Interaction):
        """Envia o resultado da vitória"""
        # Calcular recompensas
        recompensa_souls = self.mob.get("recompensa_souls", 100)
        recompensa_xp = self.mob.get("recompensa_xp", 50)
        
        embed = discord.Embed(
            title="🎉 VITÓRIA! 🎉",
            description=f"Você derrotou o **{self.mob['nome']}**!",
            color=discord.Color.green()
        )
        
        # Adiciona souls e XP ao jogador no DB principal do bot
        try:
            db = interaction.client.db()
            uid = str(self.user_id)
            if uid not in db:
                db[uid] = {
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
                    "missoes": [],
                    "missoes_completas": []
                }
            
            # Adicionar souls
            db[uid]["soul"] = db[uid].get("soul", 0) + recompensa_souls
            
            # Adicionar XP e calcular level
            old_xp = db[uid].get("xp", 0)
            new_xp = old_xp + recompensa_xp
            db[uid]["xp"] = new_xp
            
            # Calcular novo nível
            level = 1
            required_xp = 100
            current_xp = new_xp
            while current_xp >= required_xp:
                current_xp -= required_xp
                level += 1
                required_xp = int(required_xp * 1.5)
            
            old_level = db[uid].get("level", 1)
            db[uid]["level"] = level
            
            interaction.client.save_db(db)
            
            # Mostrar level up se houver
            level_up_msg = ""
            if level > old_level:
                level_up_msg = f"\n🎉 **LEVEL UP! {old_level} → {level}**"
                
        except Exception:
            # Fallback
            try:
                add_soul(self.user_id, recompensa_souls)
            except Exception:
                pass
        
        embed.add_field(
            name="💰 Recompensas",
            value=f"✨ **+{recompensa_souls:,} Souls**\n⭐ **+{recompensa_xp:,} XP**{level_up_msg}",
            inline=False
        )
        
        # Mostra estatísticas finais
        embed.add_field(
            name="📊 Resultado Final",
            value=f"Sua Vida: {self.player_vida}/3\n{self.mob['emoji']} Vida do Inimigo: 0/3",
            inline=False
        )
        
        # Adicionar GIF de morte do mob
        embed.set_image(url=self.mob.get("gif_morte", ""))
        
        # Remove os buttons
        self.clear_items()
        
        try:
            await interaction.edit_original_response(embed=embed, view=self)
        except discord.NotFound:
            await interaction.followup.send(embed=embed, view=self)

    async def enviar_resultado_derrota(self, interaction: discord.Interaction):
        """Envia o resultado da derrota"""
        embed = discord.Embed(
            title="💀 DERROTA! 💀",
            description=f"Você foi derrotado pelo **{self.mob['nome']}**!",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="⚠️ Resultado",
            value="Nenhuma recompensa foi obtida...",
            inline=False
        )
        
        # Mostra estatísticas finais
        embed.add_field(
            name="📊 Resultado Final",
            value=f"Sua Vida: {self.player_vida}/3\n{self.mob['emoji']} Vida do Inimigo: {max(0, self.mob_vida)}/3",
            inline=False
        )
        
        # Adicionar GIF de morte do mob
        embed.set_image(url=self.mob.get("gif_morte", ""))
        
        # Remove os buttons
        self.clear_items()
        
        try:
            await interaction.edit_original_response(embed=embed, view=self)
        except discord.NotFound:
            await interaction.followup.send(embed=embed, view=self)


# ==============================
# Cog com os Comandos
# ==============================
class RPGCombate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    def get_user_rpg_equipment(self, user_id: int):
        """Obtém equipamento RPG do usuário, garantindo defaults se não equipado"""
        arma = None
        armadura = None
        try:
            # Tentar pegar do cog Loja
            loja_cog = self.bot.get_cog("Loja")
            if loja_cog:
                user_inv = loja_cog.get_user_inventory(user_id)
                arma_id = user_inv.get("arma_equipada_rpg")
                armadura_id = user_inv.get("armadura_equipada_rpg")
                if arma_id and arma_id in EQUIPAMENTOS_RPG:
                    arma = EQUIPAMENTOS_RPG[arma_id]
                if armadura_id and armadura_id in EQUIPAMENTOS_RPG:
                    armadura = EQUIPAMENTOS_RPG[armadura_id]
        except Exception:
            # Ignorar falhas e usar defaults
            pass

        # Garantir que sempre exista um equipamento padrão
        if not arma:
            arma = {"nome": "Punhos", "tipo": "arma", "ataque": 0}
        if not armadura:
            armadura = {"nome": "Sem Armadura", "tipo": "armadura", "defesa": 0}
        return arma, armadura
    
    @app_commands.command(name="equipar-rpg", description="Equipe armas e armaduras para combate")
    async def equipar_rpg(self, interaction: discord.Interaction):
        """Equipa armas e armaduras craftadas para usar no combate"""
        loja_cog = self.bot.get_cog("Loja")
        if not loja_cog:
            await interaction.response.send_message("❌ Sistema de inventário indisponível!", ephemeral=True)
            return
        
        user_inv = loja_cog.get_user_inventory(interaction.user.id)
        itens_inv = user_inv.get("itens", {})
        
        # Filtrar armas e armaduras que o usuário possui
        armas_disponiveis = []
        armaduras_disponiveis = []
        
        for item_id, qtd in itens_inv.items():
            if qtd > 0 and item_id in EQUIPAMENTOS_RPG:
                equip = EQUIPAMENTOS_RPG[item_id]
                if equip["tipo"] == "arma":
                    armas_disponiveis.append((item_id, equip))
                elif equip["tipo"] == "armadura":
                    armaduras_disponiveis.append((item_id, equip))
        
        if not armas_disponiveis and not armaduras_disponiveis:
            await interaction.response.send_message(
                "❌ Você não possui armas ou armaduras craftadas!\nUse `/craft` para criar equipamentos.",
                ephemeral=True
            )
            return
        
        # Criar view com botões
        class EquiparRPGView(discord.ui.View):
            def __init__(self, cog_instance, armas, armaduras):
                super().__init__(timeout=180)
                self.cog = cog_instance
                self.armas = armas
                self.armaduras = armaduras
                self.update_buttons()
            
            def update_buttons(self):
                self.clear_items()
                
                # Botões para armas
                for item_id, equip in self.armas[:5]:
                    button = discord.ui.Button(
                        label=f"{equip['nome']} (+{equip['ataque']} ATK)",
                        style=discord.ButtonStyle.danger,
                        custom_id=f"arma_{item_id}"
                    )
                    button.callback = self.create_equipar_callback(item_id, equip, "arma")
                    self.add_item(button)
                
                # Botões para armaduras
                for item_id, equip in self.armaduras[:5]:
                    button = discord.ui.Button(
                        label=f"{equip['nome']} (+{equip['defesa']} DEF)",
                        style=discord.ButtonStyle.primary,
                        custom_id=f"armadura_{item_id}"
                    )
                    button.callback = self.create_equipar_callback(item_id, equip, "armadura")
                    self.add_item(button)
            
            def create_equipar_callback(self, item_id, equip, tipo):
                async def callback(button_interaction: discord.Interaction):
                    if button_interaction.user.id != interaction.user.id:
                        await button_interaction.response.send_message("❌ Apenas quem usou o comando pode equipar!", ephemeral=True)
                        return
                    
                    # Equipar item no inventário unificado: db[uid]['inventario']
                    db = self.cog.bot.db()
                    user_id_str = str(interaction.user.id)
                    if user_id_str not in db:
                        db[user_id_str] = {}
                    inv = db[user_id_str].get("inventario") or {"itens": {}, "equipados": {}}
                    if tipo == "arma":
                        inv["arma_equipada_rpg"] = item_id
                    else:
                        inv["armadura_equipada_rpg"] = item_id
                    db[user_id_str]["inventario"] = inv
                    self.cog.bot.save_db(db)

                    embed_sucesso = discord.Embed(
                        title="✅ Equipamento Atualizado!",
                        description=f"Você equipou: **{equip['nome']}**\n\nAgora use `/combate` para lutar!",
                        color=discord.Color.green()
                    )
                    await button_interaction.response.send_message(embed=embed_sucesso, ephemeral=False)
                
                return callback
        
        # Criar embed
        arma_atual, armadura_atual = self.get_user_rpg_equipment(interaction.user.id)
        arma_texto = arma_atual["nome"] if arma_atual else "❌ Nenhuma"
        armadura_texto = armadura_atual["nome"] if armadura_atual else "❌ Nenhuma"
        
        embed = discord.Embed(
            title="⚔️ Equipar para Combate",
            description=f"**Equipamento Atual:**\n⚔️ Arma: {arma_texto}\n🛡️ Armadura: {armadura_texto}\n\nClique nos botões para equipar:",
            color=0xFF6B00
        )
        
        view = EquiparRPGView(self, armas_disponiveis, armaduras_disponiveis)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

    @app_commands.command(name="combate", description="Inicie um combate contra um mob de RPG!")
    async def combate(self, interaction: discord.Interaction):
        """Inicia um combate contra um mob aleatório (lobo ou urso)"""
        # Cooldown de 30 minutos por usuário
        try:
            uid = str(interaction.user.id)
            db = self.bot.db() if hasattr(self, 'bot') else interaction.client.db()
            now = datetime.datetime.now()
            cooldown = 30 * 60  # 30 minutos em segundos
            last = None
            if uid in db:
                last = db[uid].get("last_combate")

            if last:
                try:
                    last_dt = datetime.datetime.fromisoformat(last)
                    elapsed = (now - last_dt).total_seconds()
                    if elapsed < cooldown:
                        remaining = int(cooldown - elapsed)
                        minutes = remaining // 60
                        seconds = remaining % 60
                        embed = discord.Embed(
                            title="⏳ Cooldown de Combate",
                            description=f"Você precisa aguardar **{minutes}m {seconds}s** para iniciar outro combate.",
                            color=discord.Color.orange()
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                except Exception:
                    # se falhar ao parsear, ignore e permita o combate
                    pass

            # Registrar início do combate (prevenindo race conditions de starts simultâneos)
            if uid not in db:
                db[uid] = {
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
                    "missoes": [],
                    "missoes_completas": []
                }
            db[uid]["last_combate"] = now.isoformat()
            # salvar imediatamente
            if hasattr(self, 'bot'):
                self.bot.save_db(db)
            else:
                interaction.client.save_db(db)

        except Exception:
            # Se algo falhar no check de cooldown, permitir o combate mas não bloquear
            pass

        # Escolhe aleatoriamente entre lobo e urso
        mob_type = random.choice(list(MOBS.keys()))
        mob_info = MOBS[mob_type].copy()
        
        # Pegar equipamentos do usuário
        arma, armadura = self.get_user_rpg_equipment(interaction.user.id)
        
        # Cria a view com os botões passando equipamentos
        view = CombateButtons(
            interaction.user.id,
            mob_type,
            arma_equipada=arma,
            armadura_equipada=armadura
        )
        
        # Criar embed inicial a partir da view
        embed = view.criar_embed_combate()
        
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
    # Evitar carregamento duplicado do cog
    if bot.get_cog("RPGCombate") is None:
        await bot.add_cog(RPGCombate(bot))