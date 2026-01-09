import datetime
import importlib
import json
import os
import random
from itertools import cycle
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands, tasks

# Importar database MongoDB
try:
    from database import init_mongodb, get_mongodb
    HAS_MONGODB = True
except ImportError:
    HAS_MONGODB = False
    print("⚠️ Módulo database não disponível")


# ==========================================
# JSON Encoder para tratar ObjectId e outros tipos
# ==========================================
class SafeJSONEncoder(json.JSONEncoder):
    """
    Encoder customizado que converte tipos não-serializáveis para JSON
    - ObjectId do MongoDB -> string
    - datetime -> ISO format string
    - set -> list
    - Outros tipos -> string
    """
    def default(self, obj):
        # ObjectId do MongoDB/PyMongo
        if type(obj).__name__ == 'ObjectId':
            return str(obj)
        # datetime objects
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        # Sets
        if isinstance(obj, set):
            return list(obj)
        # Bytes
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')
        # Tenta serializar normalmente, caso contrário converte para string
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)


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

# String de conexão do MongoDB com TLS e certificados
# Os certificados estão na pasta do projeto
MONGODB_URI = f"mongodb://default:Nlo0HoWFKDDr8jstdTr8BkXt@square-cloud-db-5219ec60d1f54ef49e10d88c86ce81cf.squareweb.app:7107/?authSource=admin&tls=true&tlsCAFile={BASE_DIR / 'certificate.pem'}&tlsCertificateKeyFile={BASE_DIR / 'certificate.pem'}"


def ensure_data_file() -> None:
    """Garante que o arquivo db.json existe"""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        DATA_PATH.write_text("{}", encoding="utf-8")


def load_db() -> dict:
    """
    Sistema híbrido: MongoDB + db.json
    - Tenta MongoDB primeiro
    - Se falhar, usa db.json
    - Sempre mantém db.json atualizado como backup
    """
    # Tentar MongoDB primeiro
    if bot._mongodb_enabled and HAS_MONGODB:
        try:
            # Verificar cache
            now = datetime.datetime.now()
            if (bot._db_cache_time and 
                (now - bot._db_cache_time).total_seconds() < bot._db_cache_ttl):
                return bot._db_cache.copy()
            
            mongo = get_mongodb()
            users = list(mongo.db.users.find({}, {"_id": 0}))
            
            # Converter para formato {user_id: dados}
            db_dict = {}
            for user in users:
                uid = user.get("user_id")
                if uid:
                    db_dict[uid] = user
            
            # Atualizar cache
            bot._db_cache = db_dict.copy()
            bot._db_cache_time = now
            
            # Salvar backup no db.json
            ensure_data_file()
            try:
                with DATA_PATH.open("w", encoding="utf-8") as fp:
                    json.dump(db_dict, fp, ensure_ascii=False, indent=2, cls=SafeJSONEncoder)
            except Exception as e:
                print(f"⚠️ Erro ao salvar backup db.json: {e}")
            
            return db_dict
            
        except Exception as e:
            print(f"⚠️ MongoDB falhou, usando db.json: {e}")
            bot._mongodb_enabled = False  # Desabilitar MongoDB temporariamente
    
    # Fallback: usar db.json
    ensure_data_file()
    try:
        with DATA_PATH.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
            # Atualizar cache
            bot._db_cache = data.copy()
            bot._db_cache_time = datetime.datetime.now()
            return data
    except json.JSONDecodeError:
        return {}
    except Exception as e:
        print(f"Erro ao carregar db.json: {e}")
        return {}


def save_db(data: dict) -> None:
    """
    Sistema híbrido: salva em MongoDB E db.json
    - Tenta salvar no MongoDB
    - Sempre salva no db.json (backup)
    - Se MongoDB falhar, continua com db.json
    """
    # Invalidar cache
    bot._db_cache_time = None
    
    # Salvar no MongoDB se disponível
    if bot._mongodb_enabled and HAS_MONGODB:
        try:
            mongo = get_mongodb()
            for user_id, user_data in data.items():
                if not user_id.isdigit():
                    continue
                
                if "user_id" not in user_data:
                    user_data["user_id"] = user_id
                
                try:
                    mongo.db.users.update_one(
                        {"user_id": user_id},
                        {"$set": user_data},
                        upsert=True
                    )
                except Exception as e:
                    print(f"⚠️ Erro MongoDB ao salvar {user_id}: {e}")
                    bot._mongodb_enabled = False  # Desabilitar se falhar
                    break
        except Exception as e:
            print(f"⚠️ MongoDB falhou ao salvar, usando apenas db.json: {e}")
            bot._mongodb_enabled = False
    
    # SEMPRE salvar no db.json como backup
    ensure_data_file()
    try:
        with DATA_PATH.open("w", encoding="utf-8") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=2, cls=SafeJSONEncoder)
    except Exception as e:
        print(f"❌ CRÍTICO: Erro ao salvar db.json: {e}")


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


TOKEN = resolve_token()


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

# Track last presence to avoid unnecessary change_presence calls
bot._last_presence = None  # Optional[str]

bot.call_times = {}  # Dict[int, datetime.datetime]
bot.active_users = set()  # Set[int]

# Cache para dados do DB
bot._db_cache = {}
bot._db_cache_time = None
bot._db_cache_ttl = 5  # Cache válido por 5 segundos
bot._mongodb_enabled = False  # Será ativado se conectar

bot.db = load_db
bot.save_db = save_db

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
    """
    Garante que o usuário existe no MongoDB
    Retorna (db_completo, user_id_str) para compatibilidade
    """
    try:
        mongo = get_mongodb()
        user = mongo.ensure_user(user_id)
        uid = str(user_id)
        
        # Retornar db completo para compatibilidade
        db = load_db()
        db[uid] = user
        
        return db, uid
    except Exception as e:
        print(f"Erro ao garantir registro do usuário {user_id}: {e}")
        # Fallback
        uid = str(user_id)
        db = load_db()
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
                "missoes_completas": []
            }
        return db, uid


@bot.tree.command(name="help", description="Lista os comandos disponíveis do Help Exilium.")
async def slash_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📖 Help Exilium",
        description="Comandos disponíveis:",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="<:membro:1456311222315253910> Perfil", value="/perfil [membro] - Mostra os detalhes do perfil", inline=False)
    embed.add_field(name="<:papel:1456311322319917198> Mensagens", value="/mensagem <título> <texto> - Cria uma embed simples\n/frase <frase> - Envia uma frase ou poesia", inline=False)
    embed.add_field(name="<:papel:1456311322319917198> Sobre Mim", value="/set-sobre <texto> - Define seu 'Sobre Mim'", inline=False)
    embed.add_field(name="<:microfone:1456311268439883920> Call", value="/top-tempo - Ranking de tempo em call\n/callstatus - Seu tempo atual em call", inline=False)
    embed.add_field(name="💰 Economia", value="/daily - Recompensa diária\n/mine - Minerar e ganhar souls\n/caça - Caça rápida (5s)\n/caça-longa - Caça longa (12h)\n/balance [membro] - Ver saldo de souls\n/top-souls - Ranking de souls\n/top-level - Ranking de níveis\n/pay - Transferir souls", inline=False)
    embed.add_field(name="🏪 Loja & Inventário", value="/loja - Ver loja com lootboxes\n/comprar - Comprar item da loja\n/abrir - Abrir lootbox\n/usar - Usar elixir de XP\n/inventario - Ver seu inventário\n/vender - Vender item\n/equipar - Equipar item passivo\n/desequipar - Remover item equipado", inline=False)
    embed.add_field(name="⚔️ RPG & Combate", value="/combate - Lutar contra mobs\n/equipar-rpg - Equipar armas/armaduras para combate\n/craft - Craftar itens com minérios\n/forjar - Refinar minérios", inline=False)
    embed.add_field(name="<:papel:1456311322319917198> Missões", value="/missoes - Ver suas missões\n/claim-missao <número> - Reivindicar recompensa", inline=False)
    embed.add_field(name="💼 Trabalho", value="/escolher-trabalho - Escolher profissão\n/trabalhar - Trabalhar e ganhar souls", inline=False)
    embed.add_field(name="ℹ️ Info", value="/uptime - Tempo online do bot", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=False)


# Comando /perfil foi movido para cogs/perfil.py
# para incluir o botão "Sobre" com estatísticas

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
    # Tentar conectar ao MongoDB
    if HAS_MONGODB:
        try:
            print("🔄 Tentando conectar ao MongoDB...")
            # Inicializar MongoDB primeiro
            mongo = init_mongodb(MONGODB_URI)
            # Testar conexão
            mongo.client.admin.command('ping')
            bot._mongodb_enabled = True
            print("✅ MongoDB conectado com sucesso!")
            
            # Tentar migração automática se db.json tiver dados
            try:
                ensure_data_file()
                with DATA_PATH.open("r", encoding="utf-8") as fp:
                    local_data = json.load(fp)
                
                if local_data:
                    print("🔄 Migrando dados do db.json para MongoDB...")
                    count = 0
                    for user_id, user_data in local_data.items():
                        if not user_id.isdigit():
                            continue
                        if "user_id" not in user_data:
                            user_data["user_id"] = user_id
                        
                        mongo.db.users.update_one(
                            {"user_id": user_id},
                            {"$set": user_data},
                            upsert=True
                        )
                        count += 1
                    print(f"✅ {count} usuários migrados para MongoDB")
            except Exception as e:
                print(f"⚠️ Erro na migração automática: {e}")
                
        except Exception as e:
            print(f"⚠️ Não foi possível conectar ao MongoDB: {e}")
            print("ℹ️  Usando db.json como principal")
            bot._mongodb_enabled = False
    else:
        print("ℹ️  pymongo não instalado - usando db.json")
    
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

    # Carregar cog de perfil
    try:
        perfil = importlib.import_module("cogs.perfil")
        await perfil.setup(bot)
    except Exception as e:
        print(f"Erro ao carregar cog perfil: {e}")

    # Carregar cog de combate RPG
    try:
        rpg = importlib.import_module("cogs.rpg_combate")
        # Evitar duplicar o cog em reloads
        if bot.get_cog("RPGCombate") is None:
            await rpg.setup(bot)
    except Exception as e:
        print(f"Erro ao carregar cog rpg_combate: {e}")

    # Carregar cog de loja
    try:
        loja = importlib.import_module("cogs.loja")
        if bot.get_cog("Loja") is None:
            await loja.setup(bot)
    except Exception as e:
        print(f"Erro ao carregar cog loja: {e}")

    # Carregar cog de inventário
    try:
        inventario = importlib.import_module("cogs.inventario")
        if bot.get_cog("Inventario") is None:
            await inventario.setup(bot)
    except Exception as e:
        print(f"Erro ao carregar cog inventario: {e}")
    
    # Carregar cog de migração administrativa
    try:
        admin_migration = importlib.import_module("cogs.admin_migration")
        if bot.get_cog("AdminMigration") is None:
            await admin_migration.setup(bot)
    except Exception as e:
        print(f"Erro ao carregar cog admin_migration: {e}")

    update_status.start()
    await bot.tree.sync()


@update_status.before_loop
async def before_update_status():
    await bot.wait_until_ready()


@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user} (ID: {bot.user.id})")


bot.run(TOKEN)