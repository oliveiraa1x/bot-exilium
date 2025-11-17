import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
import datetime
from itertools import cycle

# ==============================
# Carrega TOKEN
# ==============================
load_dotenv()
TOKEN = os.getenv("TOKEN")

# ==============================
# Cria o BOT
# ==============================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents)

# Salva horário de inicialização do bot
bot.start_time = datetime.datetime.now()

# ==============================
# Variáveis globais
# ==============================
call_times = {}
active_users = set()

# Disponibiliza para as cogs
bot.call_times = call_times
bot.active_users = active_users

status_list = [
    "Programando 5/10",
    "Aeternum Exilium 👑",
    "Em call com a rapaziada",
    "Monitorando o servidor",
    "/help pra lhe ajudar."
]

status_cycle = cycle(status_list)

# ==============================
# EVENTOS
# ==============================
@bot.event
async def on_ready():
    print(f"✔️ Bot logado como {bot.user}")

    # Inicia status rotativo
    if not update_status.is_running():
        update_status.start()

    # Carrega as COGS (forma correta)
    await bot.load_extension("cogs.help")
    await bot.load_extension("cogs.mensagem")
    await bot.load_extension("cogs.perfil")
    await bot.load_extension("cogs.callstatus")
    await bot.load_extension("cogs.uptime")

    # Sincroniza comandos slash
    try:
        synced = await bot.tree.sync()
        print(f"🔧 {len(synced)} comandos sincronizados.")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")


@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and not before.channel:
        call_times[member.id] = datetime.datetime.now()
        active_users.add(member.id)

    elif before.channel and not after.channel:
        call_times.pop(member.id, None)
        active_users.discard(member.id)

# ==============================
# STATUS ROTATIVO
# ==============================
@tasks.loop(seconds=10)
async def update_status():
    if active_users:
        # Pega tempo do primeiro usuário da call
        user_id = next(iter(active_users))
        start = call_times.get(user_id, datetime.datetime.now())
        elapsed = datetime.datetime.now() - start

        hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        tempo = f"{hours}:{minutes:02}:{seconds:02}"

        current_status = next(status_cycle) + f" | "
        await bot.change_presence(activity=discord.Game(name=current_status))

    else:
        current_status = next(status_cycle)
        await bot.change_presence(activity=discord.Game(name=current_status))


# ==============================
# INICIA O BOT
# ==============================
bot.run(TOKEN)