"""
Módulo de banco de dados com suporte a MongoDB e fallback para JSON.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "db.json"


class CompatibleDB(dict):
    """
    Dicionário compatível com a API antiga que sincroniza automaticamente com MongoDB.
    """

    def __init__(self, db_manager: 'DatabaseManager', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_manager = db_manager
        # Carrega todos os dados
        self.update(db_manager.get_all_users())

    def __setitem__(self, key: str, value: Dict[str, Any]) -> None:
        super().__setitem__(key, value)
        # Sincroniza com o banco de dados
        try:
            user_id = int(key)
            self.db_manager.set_user(user_id, value)
        except (ValueError, TypeError):
            pass

    def __delitem__(self, key: str) -> None:
        super().__delitem__(key)
        try:
            user_id = int(key)
            self.db_manager.delete_user(user_id)
        except (ValueError, TypeError):
            pass

    def update(self, *args, **kwargs) -> None:
        super().update(*args, **kwargs)
        # Sincroniza todas as mudanças
        for key, value in self.items():
            try:
                user_id = int(key)
                self.db_manager.set_user(user_id, value)
            except (ValueError, TypeError):
                pass


class DatabaseManager:
    """Gerenciador de banco de dados com suporte a MongoDB e JSON."""

    def __init__(self, mongodb_uri: Optional[str] = None):
        self.mongodb_uri = mongodb_uri
        self.client: Optional[MongoClient] = None
        self.db = None
        self.collection = None
        self.use_mongodb = False
        self.json_data: Dict[str, Any] = {}
        self.retry_count = 0
        self.max_retries = 5

        # Detecta se está rodando na Square Cloud
        self.is_square_cloud = self._is_running_on_square_cloud()

        # Tenta conectar ao MongoDB apenas se estiver na Square Cloud
        if self.is_square_cloud and mongodb_uri and PYMONGO_AVAILABLE:
            self._connect_mongodb()
        else:
            if not self.is_square_cloud:
                print("ℹ️  Ambiente local detectado - Usando JSON")
            self._load_json()

    def _is_running_on_square_cloud(self) -> bool:
        """Detecta se está rodando na Square Cloud pelo ambiente."""
        return os.getenv("SQUARE_CLOUD_REALTIME") is not None

    def _connect_mongodb(self) -> bool:
        """Conecta ao MongoDB com retry automático."""
        try:
            # Verifica se o certificado existe
            cert_path = BASE_DIR / "certificate.pem"
            kwargs = {
                "serverSelectionTimeoutMS": 5000,  # 5 segundos (reduzido)
                "connectTimeoutMS": 5000,
                "socketTimeoutMS": 5000,
                "retryWrites": False,
                "tlsAllowInvalidCertificates": True,
                "maxPoolSize": 1,
                "directConnection": True,  # Conexão direta
            }
            
            if cert_path.exists():
                print("📜 Usando certificado local...")
                kwargs["tlsCertificateKeyFile"] = str(cert_path)
            
            db_host = self.mongodb_uri.split('@')[1].split('/')[0] if '@' in self.mongodb_uri else '...'
            print(f"🔄 Tentativa {self.retry_count + 1}/{self.max_retries} - Conectando ao MongoDB: {db_host}")
            
            self.client = MongoClient(self.mongodb_uri, **kwargs)
            
            # Testa a conexão com timeout curto
            self.client.admin.command("ping", maxTimeMS=3000)
            self.db = self.client["exilium"]
            self.collection = self.db["users"]
            self.use_mongodb = True
            self.retry_count = 0
            print("✅ Conectado ao MongoDB com sucesso!")
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            self.retry_count += 1
            if self.retry_count < self.max_retries:
                print(f"⚠️  Erro na tentativa {self.retry_count}: Será retentado automaticamente...")
            else:
                print(f"❌ Falha ao conectar ao MongoDB após {self.max_retries} tentativas")
                print("⚠️  Usando JSON local como fallback permanentemente")
                self._load_json()
            return False
            
        except Exception as e:
            print(f"❌ Erro inesperado: {type(e).__name__}: {e}")
            print("⚠️  Usando JSON local como fallback")
            self._load_json()
            return False
            return False
        except Exception as e:
            print(f"✗ Erro inesperado ao conectar ao MongoDB: {type(e).__name__}: {e}")
            print("  Usando JSON local como fallback...")
            self._load_json()
            return False

    def retry_mongodb_connection(self) -> bool:
        """Tenta reconectar ao MongoDB se ainda não estiver conectado."""
        if self.use_mongodb:
            return True  # Já está conectado
        
        if not self.is_square_cloud or self.retry_count >= self.max_retries:
            return False  # Não tente se não for Square Cloud ou atingiu limite
        
        return self._connect_mongodb()

    def _load_json(self) -> None:
        """Carrega dados do arquivo JSON."""
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        if DATA_PATH.exists():
            try:
                with DATA_PATH.open("r", encoding="utf-8") as fp:
                    self.json_data = json.load(fp)
            except json.JSONDecodeError:
                self.json_data = {}
        else:
            self.json_data = {}

    def _save_json(self) -> None:
        """Salva dados no arquivo JSON."""
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        with DATA_PATH.open("w", encoding="utf-8") as fp:
            json.dump(self.json_data, fp, ensure_ascii=False, indent=2)

    def get_user(self, user_id: int) -> Dict[str, Any]:
        """Obtém dados do usuário."""
        user_id_str = str(user_id)

        if self.use_mongodb:
            user = self.collection.find_one({"_id": user_id_str})
            if user:
                user.pop("_id", None)
                return user
            return {}
        else:
            return self.json_data.get(user_id_str, {})

    def set_user(self, user_id: int, data: Dict[str, Any]) -> None:
        """Salva dados do usuário."""
        user_id_str = str(user_id)

        if self.use_mongodb:
            self.collection.update_one(
                {"_id": user_id_str},
                {"$set": data},
                upsert=True
            )
        else:
            self.json_data[user_id_str] = data
            self._save_json()

    def update_user(self, user_id: int, data: Dict[str, Any]) -> None:
        """Atualiza dados do usuário (merge)."""
        user_id_str = str(user_id)

        if self.use_mongodb:
            self.collection.update_one(
                {"_id": user_id_str},
                {"$set": data},
                upsert=True
            )
        else:
            if user_id_str not in self.json_data:
                self.json_data[user_id_str] = {}
            self.json_data[user_id_str].update(data)
            self._save_json()

    def get_all_users(self) -> Dict[str, Dict[str, Any]]:
        """Obtém todos os usuários."""
        if self.use_mongodb:
            users = {}
            for user in self.collection.find():
                user_id = user.pop("_id")
                users[user_id] = user
            return users
        else:
            return self.json_data.copy()

    def delete_user(self, user_id: int) -> None:
        """Deleta um usuário."""
        user_id_str = str(user_id)

        if self.use_mongodb:
            self.collection.delete_one({"_id": user_id_str})
        else:
            self.json_data.pop(user_id_str, None)
            self._save_json()

    def get_compatible_db(self) -> CompatibleDB:
        """Retorna um dicionário compatível com a API antiga."""
        return CompatibleDB(self)

    def sync_economia(self, economia_data: Dict[str, Any]) -> None:
        """Sincroniza dados de economia (raridades, loja, etc) com MongoDB."""
        if self.use_mongodb:
            try:
                config_collection = self.db["config"]
                config_collection.update_one(
                    {"_id": "economia"},
                    {"$set": {"data": economia_data}},
                    upsert=True
                )
            except Exception as e:
                print(f"⚠️ Erro ao sincronizar economia: {e}")
        else:
            # Salva no JSON
            self.json_data["_economia"] = economia_data
            self._save_json()

    def get_economia(self) -> Dict[str, Any]:
        """Obtém dados de economia do banco."""
        if self.use_mongodb:
            try:
                config_collection = self.db["config"]
                result = config_collection.find_one({"_id": "economia"})
                if result:
                    return result.get("data", {})
            except Exception as e:
                print(f"⚠️ Erro ao buscar economia: {e}")
            return {}
        else:
            return self.json_data.get("_economia", {})

    def close(self) -> None:
        """Fecha a conexão com o banco de dados."""
        if self.client:
            self.client.close()
            print("✓ Conexão com MongoDB fechada.")
