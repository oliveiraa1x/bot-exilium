# 🤖 Rede Exilium Bot

Bot Discord completo para **Aeternum Exilium** com sistema de economia, níveis, perfil, loja, inventário e muito mais!

---

## ✨ Funcionalidades

- 💰 **Sistema de Economia** - Moeda (Souls), níveis e XP
- 🏪 **Loja & Inventário** - Compre lootboxes, itens e gerencie seu inventário
- 📦 **Sistema de Lootboxes** - Abra caixas e ganhe recompensas aleatórias
- ✨ **Itens Consumíveis** - Use elixires de XP para subir de nível
- 📊 **Rankings** - Top players em diferentes categorias
- 🎯 **Missões** - Complete missões e ganhe recompensas
- 🎧 **Tracking de Call** - Acompanhe tempo em chamadas de voz
- ⛏️ **Mineração** - Mine recursos e ganhe souls
- 🌲 **Sistema de Caça** - Caça rápida e caça longa por almas
- 💼 **Sistema de Trabalho** - Escolha uma profissão e trabalhe por recompensas
- ⚔️ **Mini Game — Combate RPG** - Combata mobs com botões (recompensa: +100 souls por vitória)
- 🔨 **Sistema de Craft & Forja** - Crie itens poderosos

---

## 🚀 Instalação Rápida

1. **Instale as dependências:**

```bash
pip install -r requirements.txt
```

2. **Configure o token:**

   - Crie um arquivo `.env` com: `TOKEN=seu_token_aqui`
   - Ou crie `config.json` com: `{"TOKEN": "seu_token_aqui"}`

3. **Execute:**

```bash
python main.py
```

---

## 📝 Comandos Principais

### 💰 Economia

| Comando             | Descrição                             | Cooldown |
| ------------------- | ------------------------------------- | -------- |
| `/daily`            | Recompensa diária (50-150 souls + XP) | 24h      |
| `/mine`             | Minerar e ganhar souls (10-50 souls)  | 60s      |
| `/caça`             | Caça rápida (15-60 souls)             | 2min     |
| `/caça-longa`       | Caça longa de 12h (200-500 souls)     | 12h      |
| `/escolher-trabalho`| Escolher profissão para trabalhar     | -        |
| `/trabalhar`        | Trabalhar e ganhar souls + XP         | 1h       |
| `/balance [membro]` | Ver saldo de souls, XP e profissão    | -        |
| `/pay`              | Pague outro membro (requer confirmação) | -        |
| `/top-souls`        | Ranking de souls                      | -        |
| `/top-level`        | Ranking de níveis                     | -        |

### 🏪 Loja & Inventário

| Comando              | Descrição                                    |
| -------------------- | -------------------------------------------- |
| `/loja`              | Ver loja com lootboxes e itens               |
| `/comprar`           | Comprar item da loja (autocomplete)          |
| `/inventario`        | Ver seu inventário completo                  |
| `/abrir`             | Abrir lootbox e ganhar recompensas (autocomplete) |
| `/usar`              | Usar elixir de XP para subir nível (autocomplete) |
| `/vender`            | Vender item para a loja (70% do valor)       |
| `/equipar`           | Equipar item passivo (autocomplete)          |
| `/desequipar`        | Remover item equipado (autocomplete)         |

### 📦 Lootboxes Disponíveis

| Lootbox           | Custo     | Souls      | Itens                |
| ----------------- | --------- | ---------- | -------------------- |
| 📦 Box Iniciante  | 500       | 50-125     | Fragmentos, Poções   |
| 🎁 Box Rara       | 3.000     | 300-750    | Elixires, Gemas      |
| 💎 Box Ultra      | 5.000     | 500-1.250  | Cristais, Fragmentos |
| ⚡ Box Mítica     | 8.000     | 800-2.000  | Essências, Runas     |
| 👑 Box Lendária   | 12.000    | 1.200-3.000| Itens Ancestrais     |

### ✨ Elixires de XP

| Item                 | XP     | Como Obter        |
| -------------------- | ------ | ----------------- |
| ✨ Elixir de XP      | +500   | Box Rara+         |
| ✨ Grande Elixir     | +1.000 | Box Ultra+        |
| 🌟 Elixir Lendário   | +2.000 | Box Mítica+       |
| 🌠 Elixir Ancestral  | +3.500 | Box Lendária      |

### 🎭 Itens Passivos Equipáveis

Compre na `/loja` e equipe com `/equipar` para ganhar bônus permanentes!

| Item                          | Custo     | Raridade    | Bônus                           |
| ----------------------------- | --------- | ----------- | ------------------------------- |
| ⏰ Anel da Velocidade | 5.000 | 🔵 Raro | -10% Cooldowns |
| 💰 Anel da Fortuna | 8.000 | 🟣 Épico | +15% Souls |
| 📿 Amuleto da Sabedoria | 7.000 | 🟣 Épico | +20% XP |
| 👢 Botas de Hermes | 10.000 | 🟡 Lendário | -20% Cooldowns + 10% Souls |
| 👑 Coroa de Exilium | 25.000 | 🔴 Ancestral | +25% Souls + 25% XP - 15% Cooldowns |
| 🏅 Medalhão Membro Elite | 15.000 | 🟡 Lendário | +30% XP |
| 💎 Bracelete do Administrador | 20.000 | 🔴 Ancestral | +20% Souls - 25% Cooldowns |
| 🎤 Colar do Orador | 6.000 | 🔵 Raro | +12% XP por mensagens |

**Como usar:**
1. Compre o item na `/loja` (aba "Itens Passivos")
2. Use `/equipar` e selecione o item
3. Os bônus são aplicados automaticamente!
4. Use `/desequipar` para remover

### 👤 Perfil

| Comando              | Descrição                            |
| -------------------- | ------------------------------------ |
| `/perfil [membro]`   | Perfil completo com stats e rankings |
| `/set-sobre <texto>` | Definir seu "Sobre Mim"              |

### 🎯 Missões

| Comando                  | Descrição                    |
| ------------------------ | ---------------------------- |
| `/missoes`               | Ver missões ativas           |
| `/claim-missao <número>` | Reivindicar recompensa (1-3) |

### 🎧 Call

| Comando       | Descrição                |
| ------------- | ------------------------ |
| `/callstatus` | Tempo atual em call      |
| `/top-tempo`  | Ranking de tempo em call |

### 🔧 Utilitários

| Comando                      | Descrição                 |
| ---------------------------- | ------------------------- |
| `/help`                      | Lista todos os comandos   |
| `/mensagem <título> <texto>` | Criar embed personalizada |
| `/uptime`                    | Tempo online do bot       |

---

## 💎 Sistema de Economia

### Moeda: Souls <:alma:1456309061057511535>

Ganhe souls através de:

- ✅ Daily rewards (50-150 souls)
- ⛏️ Mineração (10-50 souls a cada 60s)
- 🌲 Caça rápida (15-60 souls a cada 2min)
- 🌲 Caça longa (200-500 souls a cada 12h)
- 💼 Trabalho (50-150 souls + XP a cada 1h)
- ⚔️ Combate RPG (100 souls por vitória)
- 📦 Lootboxes (50-3.000 souls aleatórios)
- 💱 Vender itens (70% do valor base)

### Sistema de Lootboxes

1. **Compre lootboxes** na `/loja` usando suas souls
2. **Abra com** `/abrir` e escolha a box do popup
3. **Ganhe recompensas:**
   - Souls (25% do valor da box)
   - Elixires de XP (para subir de nível)
   - Fragmentos, Gemas, Cristais
   - Itens raros e lendários
4. **Use elixires** com `/usar` para ganhar XP instantâneo
5. **Gerencie tudo** no `/inventario`

### Autocomplete Inteligente

Todos os comandos de itens possuem **autocomplete** que mostra apenas o que você tem:

- `/abrir` - Mostra suas lootboxes
- `/usar` - Mostra seus consumíveis  
- `/vender` - Mostra todos seus itens
- `/equipar` - Mostra itens passivos
- `/desequipar` - Mostra itens equipados

Não precisa decorar IDs! 🎯

### Sistema de Níveis

Ganhe **XP** através de:

- 📨 Mensagens no servidor
- ✅ Daily rewards  
- ⛏️ Mineração
- 🌲 Caça (rápida e longa)
- 💼 Trabalho (profissões)
- 🎯 Missões completas
- ✨ **Elixires de XP** (novo!)

**Fórmula:** XP necessária aumenta 50% a cada nível

### Recompensas

**Daily:**

- 50-150 souls + 20-50 XP
- Bônus de streak (+10% por dia)

**Mineração:**

- 10-50 souls + 5-15 XP
- Chance de itens raros (5-10%)

**Caça Rápida:**

- 15-60 souls + 8-20 XP
- Duração: 5 segundos
- Chance de almas raras (4-8%)

**Caça Longa:**

- 200-500 souls + 100-250 XP
- Duração: 12 horas
- Notificação automática ao terminar
- Maiores chances de itens raros (15-20%)

**Trabalho:**

- 50-150 souls + 40-130 XP (varia por profissão)
- Cooldown: 1 hora
- 10 profissões diferentes disponíveis

---

## � Sistema de Trabalho

Escolha uma profissão e trabalhe para ganhar souls e XP regularmente!

### Profissões Disponíveis

| Profissão      | Souls/Trabalho | XP/Trabalho | Descrição                                |
| -------------- | -------------- | ----------- | ---------------------------------------- |
| 💻 Programador | 80-120         | 70-100      | Desenvolva sistemas e ganhe boas recompensas! |
| ⚕️ Médico      | 100-150        | 80-120      | Cure os feridos e seja bem recompensado! |
| 🔧 Engenheiro  | 85-130         | 75-110      | Construa e projete grandes obras!        |
| 📚 Professor   | 70-110         | 90-130      | Ensine e ganhe muita experiência!        |
| 🎨 Pintor      | 60-100         | 50-80       | Crie obras de arte e seja recompensado!  |
| 🚪 Porteiro    | 50-80          | 40-70       | Proteja a entrada e ganhe sua recompensa! |
| 👨‍🍳 Cozinheiro | 65-105         | 55-85       | Prepare deliciosas refeições!            |
| 🚗 Motorista   | 55-90          | 45-75       | Transporte pessoas e mercadorias!        |
| 🎵 Músico      | 60-95          | 70-100      | Encante com sua música!                  |
| 🏪 Comerciante | 75-115         | 60-90       | Venda produtos e lucre!                  |

### Como Funciona

1. **Escolha sua Profissão:** Use `/escolher-trabalho` para ver todas as opções e escolher
2. **Trabalhe:** Use `/trabalhar` para trabalhar e receber suas recompensas
3. **Cooldown:** Aguarde 1 hora entre cada trabalho
4. **Mudança:** Pode trocar de profissão a qualquer momento

### Benefícios

- ⏰ **Rendimento Passivo** - Ganhe souls regularmente
- ⭐ **Experiência** - Suba de nível mais rápido
- 💼 **Diversidade** - 10 profissões com recompensas diferentes
- 🎯 **Estratégia** - Escolha a profissão que melhor se adapta ao seu estilo

---
## 🗂️ Armazenamento de Dados

Todos os dados são salvos em um único arquivo: **`data/db.json`**

**Estrutura:**
```json
{
  "user_id": {
    "soul": 1000,
    "xp": 500,
    "level": 5,
    "sobre": "Texto do perfil",
    "tempo_total": 3600,
    "last_daily": "timestamp",
    "trabalho_atual": "programador",
    "missoes": []
  },
  "usuarios": {
    "user_id": {
      "itens": {
        "elixir_xp": 5,
        "box_rara": 2
      },
      "equipados": {
        "item_passivo": true
      }
    }
  }
}
```

- **Economia e XP**: Raiz do JSON por user_id
- **Inventário**: Dentro de `usuarios[user_id]`  
- **Backup automático**: Recomendado configurar backup do arquivo db.json

---
## �🕹️ Mini Game — Combate RPG

- Comando: `/combate`
- Descrição: Inicia um combate contra um mob (lobo ou urso). O combate usa uma View com botões interativos para `Ataque`, `Defesa` e `Ataque Duplo`.
- Recompensa: +100 Souls ao derrotar o mob. A recompensa é gravada no DB principal (`data/db.json`) e aparece no `/balance`.
- Observações: apenas o jogador que iniciou o combate pode interagir com os botões.

---

## 🔁 Transferências — Comando `/pay`

- Comando: `/pay membro valor`
- Descrição: Permite enviar souls para outro membro. O destinatário precisa confirmar a transferência clicando em um botão dentro de 2 minutos.
- Validações:
   - Não é possível enviar para bots.
   - Não é possível enviar para si mesmo.
   - O valor deve ser maior que zero.
   - O bot verifica o saldo do remetente antes de criar a solicitação e novamente quando o destinatário confirma, evitando transferências que excedam o saldo.
- Comportamento: Ao confirmar, o bot debita o remetente e credita o destinatário no DB principal (`data/db.json`) e envia uma notificação de sucesso.

---

## 🎯 Tipos de Missões

| Tipo        | Objetivo            | Recompensa       |
| ----------- | ------------------- | ---------------- |
| Daily       | Coletar daily       | 25 souls + 15 XP |
| Mineração   | Minerar 5 vezes     | 50 souls + 30 XP |
| Comunicador | Enviar 20 mensagens | 40 souls + 25 XP |
| Social      | 30min em call       | 60 souls + 40 XP |

---

## 📁 Estrutura

```
help-exillium/
├── main.py              # Bot principal
├── cogs/                # Módulos
│   ├── economia.py      # Sistema de economia
│   ├── perfil.py        # Sistema de perfil
│   └── ...
└── data/db.json         # Banco de dados
```

---

## 🛠️ Tecnologias

- **Python 3.10+**
- **discord.py 2.3.2**
- **python-dotenv 1.0.1**

---

## 📊 Rankings

O perfil mostra automaticamente seu ranking em:

- 🏆 **Top Call** - Tempo total em call
- 💎 **Top Souls** - Quantidade de souls
- ⭐ **Top XP** - Experiência total

---

## 📝 Notas

- Bot precisa de permissões adequadas no servidor
- Banco de dados criado automaticamente
- XP ganha automaticamente ao enviar mensagens (cooldown: 30s)

---

**Desenvolvido para Aeternum Exilium** 🎮
