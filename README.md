# 🤖 Rede Exilium Bot

Bot Discord completo para **Aeternum Exilium** com sistema de economia, níveis, perfil e muito mais!

---

## ✨ Funcionalidades

- 💰 **Sistema de Economia** - Moeda (Souls), níveis e XP
- 📊 **Rankings** - Top players em diferentes categorias
- 🎯 **Missões** - Complete missões e ganhe recompensas
- 🎧 **Tracking de Call** - Acompanhe tempo em chamadas de voz
- ⛏️ **Mineração** - Mine recursos e ganhe souls
- 🌲 **Sistema de Caça** - Caça rápida e caça longa por almas
- 💼 **Sistema de Trabalho** - Escolha uma profissão e trabalhe por recompensas
- ⚔️ **Mini Game — Combate RPG** - Combata mobs com botões (recompensa: +100 souls por vitória)

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

### 🏪 Loja e Inventário

| Comando                 | Descrição                                      |
| ----------------------- | ---------------------------------------------- |
| `/loja`                 | Lista itens disponíveis por categoria          |
| `/comprar <item> [qtd]` | Compra itens usando souls                      |
| `/vender <item> [qtd]`  | Vende itens e recebe souls                     |
| `/inventario`           | Mostra seus itens e almas                      |
| `/craft <item>`         | (Em dev) Crafta itens com materiais            |
| `/forjar <item>`        | Forja armas usando almas e ingredientes        |
| `/abrir-lootbox`        | Abre uma lootbox que você já possui            |

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

### Moeda: Souls

Ganhe souls através de:

- ✅ Daily rewards
- ⛏️ Mineração
- 🌲 Caça (rápida e longa)
- 💼 Trabalho (profissões)
- 🎯 Missões completas

### Sistema de Níveis

Ganhe **XP** enviando mensagens, fazendo daily, minerando, caçando, trabalhando ou completando missões.

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

### Lootboxes na Loja

| ID               | Nome             | Raridade | Valor (souls) |
| ---------------- | ---------------- | -------- | ------------- |
| `lootbox_nivel1` | Baú Iniciante    | comum    | 500           |
| `lootbox_nivel2` | Baú Raro         | raro     | 2 000         |
| `lootbox_nivel3` | Baú Aventureiro  | épico    | 5 000         |
| `lootbox_nivel4` | Baú Lendário     | lendário | 10 000        |

Use `/comprar item:<id>` para adquirir e `/abrir-lootbox nivel:<n>` para abrir (nível = 1-4 conforme a tabela).

---

## 💼 Sistema de Trabalho

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

## 🕹️ Mini Game — Combate RPG

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
