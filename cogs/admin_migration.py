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


async def setup(bot):
    await bot.add_cog(AdminMigration(bot))
