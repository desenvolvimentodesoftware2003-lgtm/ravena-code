# 🤖 Sistema de Agentes - Ravena

## Visão Geral

O Sistema de Agentes permite que o Ravena utilize múltiplos "especialistas" (agentes) para responder diferentes tipos de perguntas. Cada agente é um workspace separado no AnythingLLM com personalidade e conhecimento específicos.

**Nível 4** - IA Autônoma, Aprendizado e Permissões

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                RAVENA BOT                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Comando do Usuário                                                             │
│         ↓                                                                       │
│  AgentRouter.js ← ← ← AgentConfig.js                                          │
│         ↓                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        Módulos de Nível 4                               │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │   │
│  │  │ AgentAutonomy.js │  │ AgentLearning.js │  │ AgentDatabase.js│       │   │
│  │  │                  │  │                  │  │                 │       │   │
│  │  │ • Ações autônomas│  │ • Padrões        │  │ • SQLite        │       │   │
│  │  │ • Aprovação      │  │ • Preferências   │  │ • Persistência  │       │   │
│  │  │ • Níveis         │  │ • Correções      │  │ • Cache         │       │   │
│  │  │ • Auditoria      │  │ • Conhecimento   │  │ • Backup        │       │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘       │   │
│  │  ┌─────────────────┐                                                 │   │
│  │  │AgentPermissions.js│                                                │   │
│  │  │                  │                                                │   │
│  │  │ • Papéis         │                                                │   │
│  │  │ • Herança        │                                                │   │
│  │  │ • Auditoria      │                                                │   │
│  │  └─────────────────┘                                                 │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│         ↓                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        Módulos de Nível 3                               │   │
│  │  AgentMemory.js │  AgentStateMachine.js │  AgentMetrics.js              │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│         ↓                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        Módulos de Nível 2                               │   │
│  │  AgentDelegator.js  │  AgentCollaboration.js                            │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│         ↓                                                                       │
│  AnythingLLMHelper.js                                                           │
│         ↓                                                                       │
│  AnythingLLM API                                                                │
│         ↓                                                                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                         │
│  │ ravena  │  │   dev   │  │ busca360│  │  hacker │                         │
│  │(padrão) │  │(código) │  │(pesquisa│  │(seguran.)│                         │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘                         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Agentes Disponíveis

| Agente | Workspace | Descrição | Comandos |
|--------|-----------|-----------|----------|
| 🤖 **ravena** | `ravena` | Assistente geral | `!ajuda`, `!ai`, `!ia` |
| 💻 **dev** | `dev` | Programação e código | `!dev`, `!code` |
| 🔍 **busca360** | `busca360` | Pesquisa e análise | `!busca`, `!pesquisar` |
| 🛡️ **hacker** | `hacker` | Segurança cibernética | `!hack`, `!seguranca` |

## Comandos

### Gerenciamento de Agentes

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `!agent` | Mostra agente ativo | `!agent` |
| `!agent <nome>` | Ativa um agente | `!agent dev` |
| `!agent reset` | Volta ao padrão | `!agent reset` |
| `!agent-list` | Lista todos os agentes | `!agent-list` |
| `!agent-info` | Info do agente ativo | `!agent-info` |
| `!agent-info <nome>` | Info de um agente | `!agent-info dev` |
| `!agent-stats` | Estatísticas de uso | `!agent-stats` |

### Comandos de Agentes (Aliases)

| Comando | Agente | Descrição |
|---------|--------|-----------|
| `!ai <pergunta>` | ravena | Pergunta à IA geral |
| `!ia <pergunta>` | ravena | Alias para !ai |
| `!dev <pergunta>` | dev | Pergunta sobre código |
| `!busca <termo>` | busca360 | Busca informação |
| `!hack <pergunta>` | hacker | Pergunta sobre segurança |

### Comandos de Delegação (Nível 2)

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `!delegate <agente> <pergunta>` | Delega para outro agente | `!delegate dev Como criar uma API?` |
| `!delegation` | Mostra status da delegação | `!delegation` |
| `!delegation on/off` | Ativa/desativa delegação | `!delegation on` |
| `!delegation reset` | Reseta estatísticas | `!delegation reset` |

### Comandos de Colaboração (Nível 2)

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `!collab <workflow> <pergunta>` | Executa colaboração | `!collab full-analysis Analise minha API` |
| `!collab-list` | Lista workflows disponíveis | `!collab-list` |

### Comandos de Memória (Nível 3)

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `!memory` | Mostra status da memória | `!memory` |
| `!memory clear` | Limpa memória do grupo | `!memory clear` |
| `!memory info [agente]` | Info de memória de um agente | `!memory info dev` |

### Comandos de Métricas (Nível 3)

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `!dashboard` | Mostra dashboard completo | `!dashboard` |

### Comandos de Workflow (Nível 3)

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `!workflow` | Lista workflows de estado | `!workflow` |
| `!workflow create <id>` | Cria instância de workflow | `!workflow create customer-support` |
| `!workflow run <id>` | Executa instância | `!workflow run inst-123` |

### Comandos de Autonomia (Nível 4)

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `!autonomy` | Mostra status da autonomia | `!autonomy` |
| `!autonomy level <agente> <0-4>` | Define nível de autonomia | `!autonomy level dev 2` |
| `!autonomy approve <id>` | Aprova ação pendente | `!autonomy approve action-123` |
| `!autonomy reject <id>` | Rejeita ação pendente | `!autonomy reject action-123` |

### Comandos de Aprendizado (Nível 4)

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `!learning` | Mostra status do aprendizado | `!learning` |
| `!learning feedback <1-5> [texto]` | Envia feedback | `!learning feedback 5 Ótimo!` |
| `!learning patterns [agente]` | Mostra padrões aprendidos | `!learning patterns dev` |

### Comandos de Permissões (Nível 4)

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `!permissions` | Mostra suas permissões | `!permissions` |
| `!permissions roles` | Lista papéis disponíveis | `!permissions roles` |
| `!permissions check <cat> <ação>` | Verifica permissão | `!permissions check agent create` |
| `!permissions assign <user> <role>` | Atribui papel (admin) | `!permissions assign @user admin` |

## Configuração

### Variáveis de Ambiente

Adicione ao seu arquivo `.env`:

```bash
# AnythingLLM (configuração existente)
ANYTHINGLLM_HOST=http://localhost:3001
ANYTHINGLLM_API_KEY=sua-chave-aqui
ANYTHINGLLM_WORKSPACE=ravena

# Workspaces dos agentes (opcional - padrão: nome do agente)
ANYTHINGLLM_WORKSPACE_DEV=dev
ANYTHINGLLM_WORKSPACE_BUSCA=busca360
ANYTHINGLLM_WORKSPACE_HACKER=hacker
```

### Workspaces no AnythingLLM

1. **Crie os workspaces** no painel do AnythingLLM:
   - `ravena` (já existe)
   - `dev`
   - `busca360`
   - `hacker`

2. **Configure cada workspace** com:
   - Documentos de conhecimento específicos
   - Prompt de sistema adequado
   - Modelo de IA apropriado

## Exemplos de Uso

### Exemplo 1: Ativar agente dev

```
Usuário: !agent dev
Bot: ✅ *Agente Ativado!*

💻 *Dev Assistant*
Ajuda com programação e código

_Agora todas as perguntas serão direcionadas a este agente._
_Use *!agent reset* para voltar ao padrão._
```

### Exemplo 2: Perguntar ao agente dev

```
Usuário: !dev Como criar uma API REST em Node.js?
Bot: 💻 *Dev Assistant*

Para criar uma API REST em Node.js, você pode usar o Express...

[Resposta detalhada sobre APIs REST]
```

### Exemplo 3: Delegação automática

```
Usuário: Como proteger minha API de ataques?
Bot: 🛡️ *Hacker* (delegado)

Para proteger sua API de ataques, você deve implementar...

[Resposta detalhada sobre segurança]
```

### Exemplo 4: Delegação manual

```
Usuário: !delegate dev Como criar uma API REST?
Bot: 💻 *Dev* (delegado)

Para criar uma API REST, você pode usar o Express...

[Resposta detalhada sobre APIs REST]
```

### Exemplo 5: Colaboração entre agentes

```
Usuário: !collab full-analysis Analise minha API
Bot: 🤝 *Colaboração Concluída*

Workflow: *Análise Completa*
Tempo: 45.232ms
Agentes: 💻 🔍 🛡️

## Respostas dos Especialistas

### 💻 Dev
[Análise técnica do código]

### 🔍 Busca 360
[Pesquisa de melhores práticas]

### 🛡️ Hacker
[Análise de segurança]
```

### Exemplo 6: Ver estatísticas

```
Usuário: !agent-stats
Bot: 📊 *Estatísticas do Orquestrador de Agentes*

📈 *Total de requisições:* 1.234
❌ *Total de erros:* 12
🔗 *Sessões ativas:* 5
💾 *Cache:* 45 entradas

*Por Agente:*
🤖 *Ravena:* 800 usos | 5 erros | 45ms média
💻 *Dev:* 300 usos | 3 erros | 120ms média
🔍 *Busca 360:* 100 usos | 2 erros | 89ms média
🛡️ *Security:* 34 usos | 2 erros | 150ms média
```

## Fluxo de Roteamento

```
1. Usuário envia mensagem
        ↓
2. AgentRouter.resolveAgent()
   ├── Override manual? → Usa agente especificado
   ├── Comando mapeado? → Usa agente do comando
   ├── Sessão ativa? → Usa agente da sessão
   └── Padrão → Usa "ravena"
        ↓
3. AgentRouter.route()
   ├── Verifica se deve delegar (AgentDelegator)
   │   ├── Detecta intenção do usuário
   │   ├── Calcula confiança
   │   └── Delega se confiança > 60%
   ├── Verifica cache
   ├── Monta prompt com contexto
   ├── Chama AnythingLLM
   └── Retorna resposta
        ↓
4. Resposta enviada ao usuário
```

## Fluxo de Delegação

```
1. Usuário envia mensagem
        ↓
2. AgentDelegator.detectIntent()
   ├── Analisa palavras-chave
   ├── Verifica padrões regex
   └── Retorna agente detectado + confiança
        ↓
3. AgentDelegator.shouldDelegate()
   ├── Delegação habilitada?
   ├── Agente detectado diferente do atual?
   ├── Confiança > mínimo (60%)?
   └── Sim → Delega
        ↓
4. AgentDelegator.delegate()
   ├── Monta prompt de delegação
   ├── Chama agente alvo
   └── Retorna resposta
```

## Estrutura de Arquivos

```
src/
├── agents/
│   ├── index.js                 # Índice do módulo
│   ├── AgentConfig.js           # Configuração dos agentes
│   ├── AgentRouter.js           # Roteador central (Nível 4)
│   ├── AgentDelegator.js        # Sistema de delegação (Nível 2)
│   ├── AgentCollaboration.js    # Sistema de colaboração (Nível 2)
│   ├── AgentMemory.js           # Sistema de memória (Nível 3)
│   ├── AgentStateMachine.js     # Máquina de estados (Nível 3)
│   ├── AgentMetrics.js          # Dashboard de métricas (Nível 3)
│   ├── AgentAutonomy.js         # IA autônoma (Nível 4)
│   ├── AgentLearning.js         # Sistema de aprendizado (Nível 4)
│   ├── AgentDatabase.js         # Integração com banco de dados (Nível 4)
│   ├── AgentPermissions.js      # Sistema de permissões (Nível 4)
│   └── README.md                # Esta documentação
├── functions/
│   ├── AgentCommands.js         # Comandos de gerenciamento
│   └── AnythingLLMHelper.js     # Integração com AnythingLLM
└── ...
```

## Próximos Passos (Nível 5+)

- [ ] Suporte a múltiplos idiomas
- [ ] API REST para integração externa
- [ ] Interface web para gerenciamento
- [ ] Integração com serviços externos (Slack, Discord, etc.)
- [ ] Sistema de plugins

## Workflows de Colaboração

### Workflows Predefinidos

| Workflow | Nome | Tipo | Descrição | Agentes |
|----------|------|------|-----------|---------|
| `full-analysis` | Análise Completa | ⚡ Paralelo | Análise técnica completa | dev, busca360, hacker |
| `secure-dev` | Desenvolvimento Seguro | ➡️ Sequencial | Desenvolve e verifica segurança | dev, hacker |
| `research-implement` | Pesquisa e Implementação | 🔄 Pipeline | Pesquisa e implementa melhor opção | busca360, dev |
| `full-audit` | Auditoria Completa | 🗳️ Consenso | Auditoria técnica e de segurança | dev, hacker, busca360 |

### Tipos de Workflow

| Tipo | Descrição | Uso |
|------|-----------|-----|
| `sequential` ➡️ | Agentes trabalham em sequência | Cada agente adiciona sua especialidade |
| `parallel` ⚡ | Agentes trabalham em paralelo | Múltiplas perspectivas simultâneas |
| `pipeline` 🔄 | Saída de um é entrada do próximo | Análise progressiva |
| `consensus` 🗳️ | Múltiplos agentes votam | Tomada de decisão |

### Criando Workflows Personalizados

```javascript
const AgentCollaboration = require("../agents/AgentCollaboration");

const collaboration = AgentCollaboration.getInstance();

collaboration.registerWorkflow("my-workflow", {
	name: "Meu Workflow",
	description: "Descrição do workflow",
	type: "sequential", // sequential, parallel, pipeline, consensus
	agents: ["dev", "busca360"],
	timeout: 120000,
	prompt: (query) => `Analise: ${query}`
});
```

## Solução de Problemas

### Erro: "Workspace não encontrado"

Verifique se o workspace foi criado no AnythingLLM e se o nome está correto no `.env`.

### Erro: "Configuração incompleta"

Verifique se as variáveis `ANYTHINGLLM_HOST` e `ANYTHINGLLM_API_KEY` estão definidas no `.env`.

### Agente não responde

1. Verifique se o AnythingLLM está rodando
2. Teste com `!ajuda` (agente padrão)
3. Verifique os logs: `make logs-bot`

## Licença

Mesma licença do projeto Ravena.
