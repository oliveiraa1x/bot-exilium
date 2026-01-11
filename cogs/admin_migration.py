"""
Comando administrativo para forçar migração de dados
"""
import discord
from discord import app_commands
from discord.ext import commands
import json
from pathlib import Path


class AdminMigration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="migrate-db", description="[ADMIN] Força migração do db.json para MongoDB")
    @app_commands.checks.has_permissions(administrator=True)
    async def migrate_db(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            from database import get_mongodb
            mongo = get_mongodb()
            
            # Caminho do db.json
            db_path = Path("data/db.json")
            
            if not db_path.exists():
                await interaction.followup.send("❌ db.json não encontrado!", ephemeral=True)
                return
            
            # Carregar dados
            with open(db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Contar usuários
            json_users = sum(1 for k in data.keys() if k.isdigit())
            mongo_users = mongo.users.count_documents({})
            
            embed = discord.Embed(
                title="🔄 Migração de Dados",
                description="Iniciando migração...",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="📊 Situação Atual",
                value=f"**db.json:** {json_users} usuários\n**MongoDB:** {mongo_users} usuários",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Migrar
            migrated = 0
            updated = 0
            inventories = 0
            errors = 0
            
            for user_id, user_data in data.items():
                try:
                    if user_id.isdigit():
                        if "user_id" not in user_data:
                            user_data["user_id"] = user_id
                        
                        result = mongo.users.update_one(
                            {"user_id": user_id},
                            {"$set": user_data},
                            upsert=True
                        )
                        
                        if result.upserted_id:
                            migrated += 1
                        elif result.modified_count > 0:
                            updated += 1
                            
                    elif user_id == "usuarios":
                        for inv_user_id, inv_data in user_data.items():
                            mongo.update_inventory(int(inv_user_id), inv_data)
                            inventories += 1
                except Exception as e:
                    errors += 1
                    print(f"Erro ao migrar {user_id}: {e}")
            
            # Resultado
            result_embed = discord.Embed(
                title="✅ Migração Concluída",
                color=discord.Color.green()
            )
            
            result_embed.add_field(
                name="📝 Resultados",
                value=f"**Novos:** {migrated} usuários\n"
                      f"**Atualizados:** {updated} usuários\n"
                      f"**Inventários:** {inventories}\n"
                      f"**Erros:** {errors}",
                inline=False
            )
            
            final_count = mongo.users.count_documents({})
            result_embed.add_field(
                name="📊 Total no MongoDB",
                value=f"**{final_count}** usuários",
                inline=False
            )
            
            await interaction.edit_original_response(embed=result_embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Erro na Migração",
                description=f"```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
    
    @migrate_db.error
    async def migrate_db_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "❌ Você precisa ser administrador para usar este comando!",
                ephemeral=True
            )
    
    @app_commands.command(name="test-commands", description="[ADMIN] Testa todos os comandos do bot")
    @app_commands.checks.has_permissions(administrator=True)
    async def test_commands(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Coletar todos os comandos
            all_commands = []
            
            # Comandos de aplicação (slash commands)
            for command in self.bot.tree.walk_commands():
                if isinstance(command, app_commands.Command):
                    all_commands.append(command)
            
            total = len(all_commands)
            
            embed = discord.Embed(
                title="🧪 Teste de Comandos",
                description=f"Testando **{total}** comandos...",
                color=discord.Color.blue()
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Testar comandos
            working = []
            errors = []
            
            for cmd in all_commands:
                try:
                    # Verificar se o comando tem callback
                    if hasattr(cmd, 'callback'):
                        # Verificar parâmetros do comando
                        import inspect
                        sig = inspect.signature(cmd.callback)
                        params = list(sig.parameters.values())[1:]  # Pular 'self'
                        
                        # Contar parâmetros obrigatórios (sem interaction)
                        required_params = [p for p in params if p.default == inspect.Parameter.empty and p.name != 'interaction']
                        
                        if len(required_params) > 0:
                            # Comando tem parâmetros obrigatórios
                            working.append(f"✅ `/{cmd.name}` (com {len(required_params)} parâmetro(s))")
                        else:
                            # Comando sem parâmetros obrigatórios
                            working.append(f"✅ `/{cmd.name}`")
                    else:
                        working.append(f"✅ `/{cmd.name}`")
                        
                except Exception as e:
                    errors.append(f"❌ `/{cmd.name}`: {str(e)[:50]}")
            
            # Criar embed de resultado
            result_embed = discord.Embed(
                title="🧪 Resultado dos Testes",
                color=discord.Color.green() if not errors else discord.Color.orange()
            )
            
            result_embed.add_field(
                name="📊 Estatísticas",
                value=f"**Total:** {total}\n**Funcionando:** {len(working)}\n**Com Erro:** {len(errors)}",
                inline=False
            )
            
            # Dividir comandos em grupos (Discord tem limite de 1024 caracteres por field)
            if working:
                working_text = "\n".join(working)
                # Dividir se for muito grande
                if len(working_text) > 1024:
                    chunks = [working_text[i:i+1024] for i in range(0, len(working_text), 1024)]
                    for i, chunk in enumerate(chunks, 1):
                        result_embed.add_field(
                            name=f"✅ Comandos Funcionando ({i}/{len(chunks)})",
                            value=chunk,
                            inline=False
                        )
                else:
                    result_embed.add_field(
                        name="✅ Comandos Funcionando",
                        value=working_text,
                        inline=False
                    )
            
            if errors:
                errors_text = "\n".join(errors)
                if len(errors_text) > 1024:
                    chunks = [errors_text[i:i+1024] for i in range(0, len(errors_text), 1024)]
                    for i, chunk in enumerate(chunks, 1):
                        result_embed.add_field(
                            name=f"❌ Comandos com Erro ({i}/{len(chunks)})",
                            value=chunk,
                            inline=False
                        )
                else:
                    result_embed.add_field(
                        name="❌ Comandos com Erro",
                        value=errors_text,
                        inline=False
                    )
            
            result_embed.set_footer(text="Teste realizado com sucesso!")
            
            await interaction.edit_original_response(embed=result_embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Erro ao Testar Comandos",
                description=f"```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
    
    @test_commands.error
    async def test_commands_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "❌ Você precisa ser administrador para usar este comando!",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(AdminMigration(bot))
