# Migração para MongoDB - Bot Exilium

Este documento descreve o processo de migração do banco de dados JSON para MongoDB.

## 📋 Pré-requisitos

1. Python 3.9+
2. Dependências instaladas (execute: `pip install -r requirements.txt`)
3. Acesso ao MongoDB configurado

## 🚀 Como Migrar

### Passo 1: Instalar Dependências

```bash
pip install -r requirements.txt
```

Isso instalará:
- `pymongo==4.6.1` - Driver do MongoDB
- `dnspython==2.4.2` - Necessário para conexões MongoDB

### Passo 2: Executar Script de Migração

```bash
python migrate_to_mongodb.py
```

O script irá:
- ✅ Ler todos os dados do `data/db.json`
- ✅ Conectar ao MongoDB
- ✅ Migrar todos os usuários e seus dados
- ✅ Migrar inventários
- ✅ Criar backup do `db.json` como `db.json.backup`

### Passo 3: Testar o Bot

```bash
python main.py
```

## 🔧 Configuração

A string de conexão do MongoDB está configurada em `main.py`:

```python
MONGODB_URI = "mongodb://default:Nlo0HoWFKDDr8jstdTr8BkXt@square-cloud-db-5219ec60d1f54ef49e10d88c86ce81cf.squareweb.app:7107/?authSource=admin&tls=true"
```

## 📊 Estrutura do MongoDB

### Database: `exilium_bot`

#### Collection: `users`
Armazena dados dos usuários:
```json
{
  "user_id": "123456789",
  "sobre": "Texto sobre mim",
  "tempo_total": 3600,
  "soul": 1000,
  "xp": 500,
  "level": 5,
  "last_daily": "2026-01-08T12:00:00",
  "last_mine": "2026-01-08T11:30:00",
  "mine_streak": 3,
  "last_caca": "2026-01-08T10:00:00",
  "caca_streak": 2,
  "caca_longa_ativa": null,
  "missoes": [],
  "missoes_completas": [],
  "trabalho": null,
  "last_trabalho": null
}
```

#### Collection: `inventories`
Armazena inventários dos usuários:
```json
{
  "user_id": "123456789",
  "itens": {
    "item_id": quantidade
  },
  "equipados": {
    "slot": "item_id"
  },
  "arma": "espada_ferro",
  "armadura": "armadura_couro"
}
```

#### Collection: `guild_config`
Armazena configurações do servidor (futuro).

## 📈 Índices Criados

Para otimizar consultas, os seguintes índices são criados automaticamente:

- `user_id` (único) - Busca rápida de usuários
- `tempo_total` (decrescente) - Ranking de tempo em call
- `soul` (decrescente) - Ranking de souls
- `xp` (decrescente) - Ranking de XP
- `level` (decrescente) - Ranking de níveis

## 🔄 Compatibilidade

O código foi modificado para manter compatibilidade com a estrutura antiga:

- `bot.db()` - Agora retorna dados do MongoDB no mesmo formato
- `bot.save_db(data)` - Salva dados no MongoDB
- `ensure_user_record()` - Funciona com MongoDB

Todos os cogs existentes continuarão funcionando sem modificações!

## 🆘 Troubleshooting

### Erro de Conexão ao MongoDB

```
❌ Erro ao conectar ao MongoDB: ...
```

**Solução**: Verifique se:
1. A string de conexão está correta
2. O MongoDB está acessível
3. As credenciais são válidas

### Erros Durante Migração

O script continua mesmo com erros em usuários específicos. Verifique os logs para identificar problemas.

### Bot Usa Fallback JSON

Se a conexão MongoDB falhar, o bot automaticamente usa o sistema JSON antigo como fallback.

## ✅ Vantagens do MongoDB

1. **Performance**: Consultas mais rápidas com índices
2. **Escalabilidade**: Suporta milhões de usuários
3. **Confiabilidade**: Sistema de banco de dados robusto
4. **Queries Avançadas**: Rankings e filtros otimizados
5. **Backup Automático**: Via Square Cloud DB

## 🎯 Próximos Passos

Após a migração bem-sucedida:

1. ✅ Testar todos os comandos do bot
2. ✅ Verificar rankings (`/top-tempo`, `/top-souls`, `/top-level`)
3. ✅ Testar economia (`/daily`, `/mine`, `/balance`)
4. ✅ Testar inventário (`/inventario`, `/loja`, `/comprar`)
5. ✅ Monitorar logs do bot

## 📝 Notas

- O arquivo `db.json` é mantido como backup
- A migração pode ser executada múltiplas vezes (atualiza dados existentes)
- Recomenda-se fazer backup manual do `db.json` antes da migração
