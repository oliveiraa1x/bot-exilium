"""
Módulo de gerenciamento do MongoDB para o Bot Exilium
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection


class MongoDB:
    """Gerenciador de conexão e operações do MongoDB"""
    
    def __init__(self, connection_string: str):
        """
        Inicializa a conexão com MongoDB com TLS
        A URI já contém todas as configurações de TLS e certificados
        
        Args:
            connection_string: URI de conexão do MongoDB completa
        """
        # Configurar opções adicionais de conexão
        connection_options = {
            "serverSelectionTimeoutMS": 5000,
            "connectTimeoutMS": 5000,
            "socketTimeoutMS": 5000,
            "maxPoolSize": 10,
            "minPoolSize": 2,
            "maxIdleTimeMS": 10000,
            "retryWrites": True,
            "w": "majority",
            "directConnection": False
        }
        
        print(f"🔄 Conectando ao MongoDB...")
        self.client: MongoClient = MongoClient(connection_string, **connection_options)
        
        # Testar conexão
        try:
            self.client.admin.command('ping')
            print("✅ Conexão com MongoDB estabelecida!")
        except Exception as e:
            print(f"⚠️ Aviso: Não foi possível verificar conexão: {e}")
        
        self.db: Database = self.client.exilium_bot
        self.users: Collection = self.db.users
        self.guild_config: Collection = self.db.guild_config
        
        # Criar índices para otimizar consultas
        self._create_indexes()
    
    def _create_indexes(self):
        """Cria índices no banco de dados para melhorar performance"""
        try:
            # Índice para buscar usuários rapidamente
            self.users.create_index("user_id", unique=True)
            
            # Índices para rankings
            self.users.create_index([("tempo_total", -1)])
            self.users.create_index([("soul", -1)])
            self.users.create_index([("xp", -1)])
            self.users.create_index([("level", -1)])
        except Exception as e:
            print(f"Erro ao criar índices: {e}")
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca dados de um usuário
        
        Args:
            user_id: ID do usuário no Discord
            
        Returns:
            Dicionário com dados do usuário ou None se não existir
        """
        return self.users.find_one({"user_id": str(user_id)})
    
    def create_user(self, user_id: int, initial_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Cria um novo usuário no banco de dados
        
        Args:
            user_id: ID do usuário no Discord
            initial_data: Dados iniciais opcionais
            
        Returns:
            Dicionário com dados do usuário criado
        """
        default_data = {
            "user_id": str(user_id),
            # Perfil
            "sobre": None,
            
            # Tempo em call
            "tempo_total": 0,
            
            # Economia
            "soul": 0,
            "xp": 0,
            "level": 1,
            
            # Daily
            "last_daily": None,
            "daily_streak": 0,
            
            # Mine
            "last_mine": None,
            "mine_streak": 0,
            
            # Caça
            "last_caca": None,
            "caca_streak": 0,
            "caca_longa_ativa": None,
            
            # Missões
            "missoes": [],
            "missoes_completas": [],
            
            # Trabalho
            "trabalho_atual": None,
            "last_trabalho": None,
            
            # Combate RPG
            "last_combate": None,
            
            # XP por mensagem
            "last_message_xp": None
        }
        
        if initial_data:
            default_data.update(initial_data)
        
        try:
            self.users.insert_one(default_data)
        except Exception as e:
            print(f"Erro ao criar usuário {user_id}: {e}")
        
        return default_data
    
    def update_user(self, user_id: int, update_data: Dict[str, Any]) -> bool:
        """
        Atualiza dados de um usuário
        
        Args:
            user_id: ID do usuário no Discord
            update_data: Dicionário com campos a serem atualizados
            
        Returns:
            True se atualizado com sucesso, False caso contrário
        """
        try:
            result = self.users.update_one(
                {"user_id": str(user_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0 or result.matched_count > 0
        except Exception as e:
            print(f"Erro ao atualizar usuário {user_id}: {e}")
            return False
    
    def ensure_user(self, user_id: int) -> Dict[str, Any]:
        """
        Garante que o usuário existe, criando se necessário
        
        Args:
            user_id: ID do usuário no Discord
            
        Returns:
            Dicionário com dados do usuário
        """
        user = self.get_user(user_id)
        if not user:
            user = self.create_user(user_id)
        else:
            # Garantir que campos novos existam para usuários antigos
            defaults = {
                "soul": 0,
                "xp": 0,
                "level": 1,
                "last_daily": None,
                "daily_streak": 0,
                "last_mine": None,
                "mine_streak": 0,
                "last_caca": None,
                "caca_streak": 0,
                "caca_longa_ativa": None,
                "missoes": [],
                "missoes_completas": [],
                "trabalho_atual": None,
                "last_trabalho": None,
                "last_combate": None,
                "last_message_xp": None
            }
            
            update_needed = False
            for key, value in defaults.items():
                if key not in user:
                    user[key] = value
                    update_needed = True
            
            if update_needed:
                self.update_user(user_id, user)
        
        return user
    
    def get_all_users(self) -> list:
        """
        Retorna todos os usuários do banco
        
        Returns:
            Lista de dicionários com dados dos usuários
        """
        return list(self.users.find({}))
    
    def get_ranking(self, field: str, limit: int = 10, filter_bots: bool = True) -> list:
        """
        Retorna ranking de usuários por um campo específico
        
        Args:
            field: Campo para ordenar (tempo_total, soul, xp, level)
            limit: Número máximo de resultados
            filter_bots: Se True, filtra bots do ranking
            
        Returns:
            Lista de usuários ordenados
        """
        query = {}
        if filter_bots:
            query["is_bot"] = {"$ne": True}
        
        return list(self.users.find(query).sort(field, -1).limit(limit))
    
    def increment_field(self, user_id: int, field: str, amount: int) -> bool:
        """
        Incrementa um campo numérico do usuário
        
        Args:
            user_id: ID do usuário
            field: Nome do campo
            amount: Valor a incrementar
            
        Returns:
            True se bem-sucedido
        """
        try:
            result = self.users.update_one(
                {"user_id": str(user_id)},
                {"$inc": {field: amount}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Erro ao incrementar {field} para usuário {user_id}: {e}")
            return False
    
    def get_inventory(self, user_id: int) -> Dict[str, Any]:
        """
        Retorna o inventário de um usuário
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dicionário com dados do inventário
        """
        inventory = self.db.inventories.find_one({"user_id": str(user_id)})
        if not inventory:
            default_inventory = {
                "user_id": str(user_id),
                "itens": {},
                "equipados": {},
                "arma": None,
                "armadura": None
            }
            self.db.inventories.insert_one(default_inventory)
            return default_inventory
        return inventory
    
    def update_inventory(self, user_id: int, inventory_data: Dict[str, Any]) -> bool:
        """
        Atualiza o inventário de um usuário
        
        Args:
            user_id: ID do usuário
            inventory_data: Dados do inventário
            
        Returns:
            True se bem-sucedido
        """
        try:
            result = self.db.inventories.update_one(
                {"user_id": str(user_id)},
                {"$set": inventory_data},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Erro ao atualizar inventário do usuário {user_id}: {e}")
            return False
    
    def close(self):
        """Fecha a conexão com o banco de dados"""
        if self.client:
            self.client.close()


# Instância global do MongoDB (será inicializada no main.py)
mongo_db: Optional[MongoDB] = None


def init_mongodb(connection_string: str) -> MongoDB:
    """
    Inicializa a conexão global com MongoDB
    
    Args:
        connection_string: URI de conexão do MongoDB
        
    Returns:
        Instância do MongoDB
    """
    global mongo_db
    mongo_db = MongoDB(connection_string)
    return mongo_db


def get_mongodb() -> MongoDB:
    """
    Retorna a instância global do MongoDB
    
    Returns:
        Instância do MongoDB
        
    Raises:
        RuntimeError: Se o MongoDB não foi inicializado
    """
    if mongo_db is None:
        raise RuntimeError("MongoDB não foi inicializado. Chame init_mongodb() primeiro.")
    return mongo_db
