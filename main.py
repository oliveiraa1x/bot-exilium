from __future__ import annotations

import datetime
import importlib
import json
import os
import random
from itertools import cycle
from pathlib import Path
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands, tasks

from database import DatabaseManager


def _resolve_load_dotenv():
    try:
        return importlib.import_module("dotenv").load_dotenv
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Dependência ausente: python-dotenv. "
            "Instale-a conforme descrito no requirements.txt."
        ) from exc
  

load_dotenv = _resolve_load_dotenv()


# ==============================
# Configurações básicas
# ==============================
BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "db.json"
CONFIG_PATH = BASE_DIR / "config.json"


def ensure_data_file() -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        DATA_PATH.write_text("{}", encoding="utf-8")


def load_db() -> dict:
    ensure_data_file()
    with DATA_PATH.open("r", encoding="utf-8") as fp:
        try:
            return json.load(fp)
        except json.JSONDecodeError:
            # Corrige arquivos corrompidos
            return {}


def save_db(data: dict) -> None:
    ensure_data_file()
    with DATA_PATH.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)


def resolve_token() -> str:
    load_dotenv()
    token = os.getenv("TOKEN")

    if token:
        return token

    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as fp:
            try:
                cfg = json.load(fp)
            except json.JSONDecodeError:
                cfg = {}
        token = cfg.get("TOKEN")

    if not token:
        raise RuntimeError(
            "TOKEN não encontrado. Configure a variável de ambiente ou o arquivo config.json."
        )

    return token


def resolve_mongodb_uri() -> str | None:
    """Resolve a URI do MongoDB a partir do ambiente ou config.json."""
    load_dotenv()
    uri = os.getenv("MONGODB_URI")

    if uri:
        return uri

    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as fp:
            try:
                cfg = json.load(fp)
            except json.JSONDecodeError:
                cfg = {}
        uri = cfg.get("MONGODB_URI")

    return uri


TOKEN = resolve_token()
MONGODB_URI = resolve_mongodb_uri()


# ==============================
# Cria o BOT e variáveis globais
# ==============================
intents = discord.Intents.all()
# Usar o prefixo do servidor conforme pedido: "sprt!"
bot = commands.Bot(command_prefix="sprt!", intents=intents)
bot.start_time = datetime.datetime.now()

# Remove default help command so custom `sprt!help` can be registered without collision
try:
    bot.remove_command('help')
except Exception:
    pass

# Inicializa o gerenciador de banco de dados
db_manager = DatabaseManager(MONGODB_URI)

# Sincroniza dados de economia (raridades, loja, etc) com MongoDB
def sync_economia_to_db():
    """Sincroniza dados de economia do db.json para MongoDB."""
    try:
        with open(Path(__file__).parent / "data" / "db.json", "r", encoding="utf-8") as fp:
            local_data = json.load(fp)
            economia = local_data.get("_economia", {})
            if economia:
                db_manager.sync_economia(economia)
                print("✅ Dados de economia sincronizados com MongoDB")
    except Exception as e:
        print(f"⚠️ Erro ao sincronizar economia: {e}")

# Cria funções compatíveis com a API antiga
def load_db() -> dict:
    return db_manager.get_compatible_db()

def save_db(data: dict) -> None:
    # A sincronização é feita automaticamente pelo CompatibleDB
    pass

bot.db_manager = db_manager
bot.db = load_db
bot.save_db = save_db

# Track last presence to avoid unnecessary change_presence calls
bot._last_presence: Optional[str] = None

bot.call_times: dict = {}
bot.active_users: set = set()

status_messages = [
    "Aeternum Exilium",
    "Suporte",
    "Olhando as calls do servidor",
    "Monitorando o servidor",
    "Bot Principal."
]
status_cycle = cycle(status_messages)


def format_elapsed(delta: datetime.timedelta) -> str:
    seconds = int(delta.total_seconds())
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{secs:02}"


def format_time(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}h {minutes}m {secs}s"


def ensure_user_record(user_id: int) -> tuple[dict, str]:
    uid = str(user_id)
    db = bot.db()
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
            "last_caca": None,
            "caca_streak": 0,
            "caca_longa_ativa": None,
            "missoes": [],
            "missoes_completas": [],
            "itens": {},
            "equipados": {},
            "last_combate": None,
        }
        bot.save_db(db)
    else:
        # Garantir que campos novos existam para usuários antigos
        defaults = {
            "soul": 0,
            "xp": 0,
            "level": 1,
            "last_daily": None,
            "last_mine": None,
            "mine_streak": 0,
            "last_caca": None,
            "caca_streak": 0,
            "caca_longa_ativa": None,
            "missoes": [],
            "missoes_completas": [],
            "itens": {},
            "equipados": {},
            "last_combate": None,
        }
        for key, value in defaults.items():
            if key not in db[uid]:
                db[uid][key] = value
        bot.save_db(db)
    return db, uid


@bot.tree.command(name="help", description="Lista os comandos disponíveis do Help Exilium.")
async def slash_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📖 Help Exilium",
        description="Você tem 10 categorias e 35+ comandos para explorar.",
        color=discord.Color.blurple(),
    )
    
    # Coluna 1
    col1 = (
        "**<:membro:1456311222315253910> Perfil**\n"
        "/perfil\n\n"
        "**<:papel:1456311222319971998> Mensagens**\n"
        "/mensagem\n"
        "/frase\n\n"
        "**<:papel:1456311222319971998> Sobre Mim**\n"
        "/set-sobre\n\n"
        "**<:microfone:1456311268439883920> Call**\n"
        "/top-tempo\n"
        "/callstatus"
    )
    
    # Coluna 2
    col2 = (
        "**💰 Economia**\n"
        "/daily\n"
        "/mine\n"
        "/caça\n"
        "/caça-longa\n"
        "/balance\n"
        "/top-souls\n"
        "/top-level\n\n"
        "**<:papel:1456311222319971998> Missões**\n"
        "/missoes\n"
        "/claim-missao"
    )
    
    # Coluna 3
    col3 = (
        "**🎒 Inventário**\n"
        "/inventario\n"
        "/usar\n"
        "/descartar\n\n"
        "**🛍️ Loja**\n"
        "/loja\n"
        "/comprar\n"
        "/vender\n"
        "/abrir-lootbox\n\n"
        "**⚔️ Combate**\n"
        "/combate\n"
        "/ranking-combate\n\n"
        "**ℹ️ Informações**\n"
        "/uptime"
    )
    
    embed.add_field(name="📋 Categorias", value=col1, inline=True)
    embed.add_field(name="　", value=col2, inline=True)
    embed.add_field(name="　", value=col3, inline=True)
    
    embed.set_footer(text="Aeternum Exilium • Use /[comando] para mais detalhes")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="perfil", description="Mostra um perfil completo do usuário.")
@app_commands.describe(membro="Membro que terá o perfil exibido")
async def slash_perfil(interaction: discord.Interaction, membro: discord.Member | None = None):
    membro = membro or interaction.user
    db, uid = ensure_user_record(membro.id)

    sobre = db[uid].get("sobre") or "❌ Nenhum Sobre Mim definido ainda."
    tempo_total = db[uid].get("tempo_total", 0)
    tempo_total_fmt = format_time(tempo_total)

    if membro.id in bot.active_users:
        start = bot.call_times.get(membro.id, datetime.datetime.now())
        elapsed = datetime.datetime.now() - start
        tempo_atual = format_time(int(elapsed.total_seconds()))
    else:
        tempo_atual = "❌ Não está em call"

    embed = discord.Embed(
        title=f"<:membro:1456311222315253910> Perfil de {membro.display_name}",
        color=discord.Color.red(),
    )
    embed.set_thumbnail(url=(membro.avatar.url if membro.avatar else membro.display_avatar.url))
    embed.add_field(name="<:ponto1:1430319216787066962> Conta criada em:", value=membro.created_at.strftime("%d/%m/%Y"), inline=True)
    joined_at = membro.joined_at.strftime("%d/%m/%Y") if membro.joined_at else "Desconhecido"
    embed.add_field(name="<:evento:1456311189352091671>  Entrou no servidor:", value=joined_at, inline=True)
    embed.add_field(name="<:papel:1456311222319971998> Sobre Mim:", value=sobre, inline=False)
    embed.add_field(name="<:microfone:1456311268439883920> Tempo atual em call:", value=tempo_atual, inline=True)
    embed.add_field(name="<:relogio:1456311245018759230> Tempo total acumulado:", value=tempo_total_fmt, inline=True)

    try:
        user = await bot.fetch_user(membro.id)
        if user.banner:
            embed.set_image(url=user.banner.url)
    except discord.HTTPException:
        pass

    embed.set_footer(text="Aeternum Exilium • Sistema de Perfil")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="mensagem", description="Cria mensagens personalizadas.")
@app_commands.describe(titulo="Título da embed", texto="Texto principal da embed")
async def slash_mensagem(interaction: discord.Interaction, titulo: str, texto: str):

    # Deferir para ocultar totalmente o uso do comando
    await interaction.response.defer(ephemeral=True)

    embed = discord.Embed(
        title=titulo,
        description=texto,
        color=discord.Color.blurple(),
    )

    # Envia a embed no canal sem mostrar que veio do comando
    await interaction.channel.send(embed=embed)

    # NÃO enviar followup para permanecer invisível



@bot.tree.command(name="set-sobre", description="Define o seu 'Sobre Mim'.")
@app_commands.describe(texto="Conteúdo do seu Sobre Mim")
async def slash_set_sobre(interaction: discord.Interaction, texto: str):
    db, uid = ensure_user_record(interaction.user.id)
    db[uid]["sobre"] = texto
    bot.save_db(db)
    await interaction.response.send_message("✅ Sobre Mim atualizado!")


@bot.tree.command(name="top-tempo", description="Mostra o ranking de tempo em call.")
async def slash_top_tempo(interaction: discord.Interaction):
    db = bot.db()
    
    # Filtrar apenas membros reais (não bots)
    ranking_items = []
    for uid, data in db.items():
        try:
            user_id = int(uid)
            # Tenta buscar o membro no servidor
            member = interaction.guild.get_member(user_id) if interaction.guild else None
            if member:
                # Se encontrou o membro, verifica se não é bot
                if not member.bot:
                    ranking_items.append((uid, data.get("tempo_total", 0)))
            else:
                # Se não encontrou no servidor, tenta buscar o usuário globalmente
                user = await bot.fetch_user(user_id)
                if not user.bot:
                    ranking_items.append((uid, data.get("tempo_total", 0)))
        except (ValueError, discord.NotFound, discord.HTTPException):
            # Se não conseguir buscar, pula este usuário
            continue

    ranking = sorted(
        ranking_items,
        key=lambda item: item[1],
        reverse=True,
    )[:10]

    embed = discord.Embed(title="🏆 Top 10 — Tempo em Call", color=discord.Color.gold())
    if not ranking:
        embed.description = "Ainda não há registros."
    else:
        for pos, (uid, seconds) in enumerate(ranking, start=1):
            member = interaction.guild.get_member(int(uid)) if interaction.guild else None
            if member:
                nome = member.display_name
            else:
                try:
                    user = await bot.fetch_user(int(uid))
                    nome = user.name
                except:
                    nome = f"Usuário {uid}"
            embed.add_field(name=f"{pos}. {nome}", value=format_time(seconds), inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="callstatus", description="Mostra seu tempo atual na call.")
async def slash_callstatus(interaction: discord.Interaction):
    user = interaction.user
    if user.id not in bot.active_users:
        embed = discord.Embed(
            title="❌ Não está em call",
            description="Você precisa estar em uma call de voz para usar este comando.",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=(user.avatar.url if user.avatar else user.display_avatar.url))
        embed.set_footer(text="Aeternum Exilium • Sistema de Call Status")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    start = bot.call_times.get(user.id, datetime.datetime.now())
    elapsed = int((datetime.datetime.now() - start).total_seconds())
    tempo_formatado = format_time(elapsed)

    embed = discord.Embed(
        title="<:microfone:1456311268439883920> Status da Call",
        description=f"**{user.mention}** está em call!",
        color=discord.Color.blue()
    )
    
    embed.set_thumbnail(url=(user.avatar.url if user.avatar else user.display_avatar.url))
    
    embed.add_field(
        name="<:relogio:1456311245018759230> Tempo na call:",
        value=f"**{tempo_formatado}**",
        inline=False
    )
    
    embed.set_footer(text="Aeternum Exilium • Sistema de Call Status")
    embed.timestamp = datetime.datetime.now()

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="uptime", description="Mostra há quanto tempo o bot está online.")
async def slash_uptime(interaction: discord.Interaction):
    diff = datetime.datetime.now() - bot.start_time
    hours, remainder = divmod(int(diff.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    tempo_formatado = f"{hours}h {minutes}m {seconds}s"

    embed = discord.Embed(
        title="⏳ Uptime do Bot",
        description=f"**{bot.user.name}** está online!",
        color=discord.Color.green()
    )
    
    embed.set_thumbnail(url=(bot.user.avatar.url if bot.user.avatar else bot.user.display_avatar.url))
    
    embed.add_field(
        name="<:relogio:1456311245018759230> Tempo online:",
        value=f"**{tempo_formatado}**",
        inline=False
    )
    
    embed.add_field(
        name="<:evento:1456311189352091671>  Iniciado em:",
        value=f"<t:{int(bot.start_time.timestamp())}:F>",
        inline=False
    )
    
    embed.set_footer(text="Aeternum Exilium • Sistema de Uptime")
    embed.timestamp = datetime.datetime.now()

    await interaction.response.send_message(embed=embed)


@tasks.loop(seconds=60)
async def update_status():
    if not bot.is_ready():
        return
    base_status = next(status_cycle)

    if bot.active_users:
        user_id = next(iter(bot.active_users))
        start = bot.call_times.get(user_id, datetime.datetime.now())
        tempo = format_elapsed(datetime.datetime.now() - start)
        desired = f"{base_status} "
        if getattr(bot, '_last_presence', None) != desired:
            try:
                await bot.change_presence(activity=discord.Game(name=desired))
                bot._last_presence = desired
            except Exception:
                # Ignore errors (rate limits will be handled by Discord library)
                pass
        return

    desired = base_status
    if getattr(bot, '_last_presence', None) != desired:
        try:
            await bot.change_presence(activity=discord.Game(name=base_status))
            bot._last_presence = desired
        except Exception:
            pass


@tasks.loop(minutes=5)
async def retry_mongodb_connection():
    """Tenta reconectar ao MongoDB a cada 5 minutos."""
    if not bot.is_ready():
        return
    
    if db_manager.retry_mongodb_connection():
        print("✅ Reconexão com MongoDB bem-sucedida!")



@bot.event
async def on_message(message):
    # Ignorar mensagens de bots
    if message.author.bot:
        return
    
    # Não ignorar mensagens que começam com o prefixo — deixamos o processamento
    # de comandos para `bot.process_commands(message)` abaixo.
    
    # Ganhar XP por mensagem
    db, uid = ensure_user_record(message.author.id)
    
    # Cooldown de XP por mensagem (30 segundos)
    last_message_xp = db[uid].get("last_message_xp")
    now = datetime.datetime.now()
    
    if not last_message_xp or (now - datetime.datetime.fromisoformat(last_message_xp)).total_seconds() >= 30:
        # Ganhar XP aleatória (1-5 XP)
        xp_gain = random.randint(1, 5)
        
        # Calcular nível antigo
        old_xp = db[uid].get("xp", 0)
        old_level = calculate_level_from_xp(old_xp)
        
        # Adicionar XP
        db[uid]["xp"] = old_xp + xp_gain
        db[uid]["last_message_xp"] = now.isoformat()
        
        # Calcular novo nível
        new_level = calculate_level_from_xp(db[uid]["xp"])
        db[uid]["level"] = new_level
        
        # Atualizar progresso de missões
        update_missao_progresso(db, uid, "mensagens", 1)
        
        bot.save_db(db)
    
    await bot.process_commands(message)


def calculate_level_from_xp(xp: int) -> int:
    """Calcula o nível baseado na XP"""
    level = 1
    required_xp = 100
    current_xp = xp
    
    while current_xp >= required_xp:
        current_xp -= required_xp
        level += 1
        required_xp = int(required_xp * 1.5)
    
    return level


def update_missao_progresso(db: dict, uid: str, tipo: str, quantidade: int = 1):
    """Atualiza o progresso de missões"""
    missoes = db[uid].get("missoes", [])
    for missao in missoes:
        if missao.get("tipo") == tipo:
            missao["progresso"] = missao.get("progresso", 0) + quantidade


@bot.event
async def on_voice_state_update(member, before, after):
    joined_channel = after.channel and not before.channel
    left_channel = before.channel and not after.channel

    if joined_channel:
        bot.active_users.add(member.id)
        bot.call_times[member.id] = datetime.datetime.now()
        return

    if left_channel:
        bot.active_users.discard(member.id)
        start = bot.call_times.pop(member.id, None)
        if start is None:
            return

        delta = datetime.datetime.now() - start
        elapsed = int(delta.total_seconds())
        if elapsed <= 0:
            return

        db, uid = ensure_user_record(member.id)
        db[uid]["tempo_total"] = db[uid].get("tempo_total", 0) + elapsed
        
        # Atualizar progresso de missão de call
        update_missao_progresso(db, uid, "call", elapsed)
        
        bot.save_db(db)


@bot.event
async def setup_hook():
    # Carregar cogs (import dinâmico para evitar problemas de importação)
    import importlib
    try:
        economia = importlib.import_module("cogs.economia")
        await economia.setup(bot)
    except Exception as e:
        print(f"Erro ao carregar cog economia: {e}")
    # voice_time_display removido - não carregar mais
    try:
        mod = importlib.import_module("cogs.mod")
        await mod.setup(bot)
    except Exception as e:
        print(f"Erro ao carregar cog mod: {e}")
    try:
        frase = importlib.import_module("cogs.frase")
        await frase.setup(bot)
    except Exception as e:
        print(f"Erro ao carregar cog frase: {e}")

    # Carregar cog de combate RPG
    try:
        rpg = importlib.import_module("cogs.rpg_combate")
        await rpg.setup(bot)
    except Exception as e:
        print(f"Erro ao carregar cog rpg_combate: {e}")

    try:
        inventario = importlib.import_module("cogs.inventario")
        await inventario.setup(bot)
    except Exception as e:
        print(f"Erro ao carregar cog inventario: {e}")

    try:
        loja = importlib.import_module("cogs.loja")
        await loja.setup(bot)
    except Exception as e:
        print(f"Erro ao carregar cog loja: {e}")

    update_status.start()
    retry_mongodb_connection.start()
    await bot.tree.sync()


@update_status.before_loop
async def before_update_status():
    await bot.wait_until_ready()


@retry_mongodb_connection.before_loop
async def before_retry_mongodb():
    await bot.wait_until_ready()


@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user} (ID: {bot.user.id})")
    
    # Verifica conexão com MongoDB
    if db_manager.client:
        try:
            db_manager.client.admin.command('ping')
            print("🟢 [MONGODB] Conectado com sucesso ao banco de dados MongoDB")
        except Exception as e:
            print(f"🔴 [MONGODB] Erro ao conectar com MongoDB: {e}")
            print("⚠️  [MONGODB] Usando fallback JSON (data/db.json)")
    else:
        print("⚠️  [MONGODB] Nenhuma URI configurada - Usando fallback JSON (data/db.json)")
    
    # Sincroniza dados de economia com MongoDB na inicialização
    sync_economia_to_db()


@bot.event
async def on_error(event, *args, **kwargs):
    """Trata erros gerais do bot."""
    print(f"Erro no evento {event}:", exc_info=True)


def shutdown_handler():
    """Handler para desligar o bot e fechar a conexão com o banco."""
    db_manager.close()
    print("Bot desligando...")


import atexit
atexit.register(shutdown_handler)

bot.run(TOKEN)