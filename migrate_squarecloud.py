"""
Script de migração SIMPLIFICADO para executar na SquareCloud
Este script migra dados do db.json para MongoDB quando executado no ambiente da SquareCloud
"""
import json
import os
from pathlib import Path

# Tentar importar pymongo
try:
    from pymongo import MongoClient
    HAS_PYMONGO = True
except ImportError:
    HAS_PYMONGO = False
    print("⚠️ PyMongo não instalado. Execute: pip install pymongo")

# MongoDB URI (já está no main.py)
MONGODB_URI = "mongodb://default:Nlo0HoWFKDDr8jstdTr8BkXt@square-cloud-db-5219ec60d1f54ef49e10d88c86ce81cf.squareweb.app:7107"

def migrate():
    """Migração simplificada"""
    if not HAS_PYMONGO:
        return
    
    print("🔄 Iniciando migração na SquareCloud...")
    
    # Carregar db.json
    db_path = Path("data/db.json")
    if not db_path.exists():
        print("❌ db.json não encontrado!")
        return
    
    with open(db_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📊 {len(data)} registros encontrados")
    
    # Conectar MongoDB
    try:
        client = MongoClient(
            MONGODB_URI,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=30000
        )
        db = client.exilium_bot
        print("✅ Conectado ao MongoDB!")
    except Exception as e:
        print(f"❌ Erro: {e}")
        return
    
    # Migrar usuários
    migrated = 0
    for user_id, user_data in data.items():
        if not user_id.isdigit():
            # Inventários ou outras estruturas
            if user_id == "usuarios":
                for inv_user_id, inv_data in user_data.items():
                    try:
                        db.inventories.update_one(
                            {"user_id": inv_user_id},
                            {"$set": inv_data},
                            upsert=True
                        )
                    except Exception as e:
                        print(f"⚠️ Erro inventário {inv_user_id}: {e}")
            continue
        
        # Migrar usuário
        try:
            if "user_id" not in user_data:
                user_data["user_id"] = user_id
            
            db.users.update_one(
                {"user_id": user_id},
                {"$set": user_data},
                upsert=True
            )
            migrated += 1
            
            if migrated % 10 == 0:
                print(f"📝 {migrated} usuários migrados...")
                
        except Exception as e:
            print(f"❌ Erro {user_id}: {e}")
    
    print(f"\n✅ Migração concluída! {migrated} usuários migrados")
    client.close()

if __name__ == "__main__":
    migrate()
