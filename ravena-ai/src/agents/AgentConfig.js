/**
 * AgentConfig.js
 *
 * Configuração centralizada dos agentes disponíveis no AnythingLLM.
 * Cada agente representa um workspace com personalidade e conhecimento específicos.
 */

"use strict";

/**
 * Configuração dos agentes
 * Cada agente mapeia para um workspace no AnythingLLM
 */
const AGENTS = {
	ravena: {
		id: "ravena",
		name: "Ravena",
		workspace: process.env.ANYTHINGLLM_WORKSPACE || "ravena",
		description: "Assistente geral do bot - responde dúvidas sobre o Ravena e ajuda comandos",
		emoji: "🤖",
		priority: 0, // Prioridade padrão
		commands: ["ajuda", "ai", "ia", "help"],
		systemContext:
			"Você é a Ravena, um bot de WhatsApp inteligente e prestativo. Responda de forma clara e objetiva.",
		maxTokens: 2000,
		temperature: 0.7
	},

	dev: {
		id: "dev",
		name: "Dev Assistant",
		workspace: process.env.ANYTHINGLLM_WORKSPACE_DEV || "dev",
		description: "Especialista em programação, código e desenvolvimento de software",
		emoji: "💻",
		priority: 1,
		commands: ["code", "debug", "review", "dev"],
		systemContext:
			"Você é um desenvolvedor sênior especialista em múltiplas linguagens e frameworks. Ajude com código, debug, revisão e boas práticas de desenvolvimento.",
		maxTokens: 3000,
		temperature: 0.5
	},

	busca360: {
		id: "busca360",
		name: "Busca 360",
		workspace: process.env.ANYTHINGLLM_WORKSPACE_BUSCA || "busca360",
		description: "Especialista em pesquisa e análise de informações",
		emoji: "🔍",
		priority: 1,
		commands: ["pesquisar", "analise", "resumo-web", "busca"],
		systemContext:
			"Você é um pesquisador especialista em encontrar e analisar informações. Forneça respostas precisas e bem fundamentadas.",
		maxTokens: 2500,
		temperature: 0.6
	},

	hacker: {
		id: "hacker",
		name: "Security Expert",
		workspace: process.env.ANYTHINGLLM_WORKSPACE_HACKER || "hacker",
		description: "Especialista em segurança cibernética e hacking ético",
		emoji: "🛡️",
		priority: 2,
		commands: ["vulnerabilidade", "pentest", "seguranca", "hack"],
		systemContext:
			"Você é um especialista em segurança cibernética. Ajude com análise de vulnerabilidades, testes de penetração e boas práticas de segurança. SEMPRE responda de forma ética e legal.",
		maxTokens: 2500,
		temperature: 0.5
	}
};

/**
 * Configuração padrão do agente
 */
const DEFAULT_AGENT = "ravena";

/**
 * Configurações de comportamento dos agentes
 */
const AGENT_BEHAVIOR = {
	// Timeout padrão para respostas (ms)
	defaultTimeout: 30000,

	// Número máximo de tentativas em caso de falha
	maxRetries: 2,

	// Habilitar cache de respostas
	enableCache: true,

	// TTL do cache (ms) - 5 minutos
	cacheTTL: 5 * 60 * 1000,

	// Habilitar delegação entre agentes
	enableDelegation: false, // Nível 2

	// Habilitar memória de contexto
	enableContextMemory: false, // Nível 3

	// Máximo de tokens no histórico de contexto
	maxContextTokens: 4000,

	// Tempo máximo de uma sessão de agente (ms) - 30 minutos
	sessionTimeout: 30 * 60 * 1000
};

/**
 * Mapeamento de comandos para agentes
 * Usado para roteamento automático baseado no comando
 */
const COMMAND_AGENT_MAP = {};

// Constrói o mapeamento a partir dos agentes
Object.values(AGENTS).forEach((agent) => {
	agent.commands.forEach((cmd) => {
		COMMAND_AGENT_MAP[cmd] = agent.id;
	});
});

/**
 * Obtém a configuração de um agente
 * @param {string} agentId - ID do agente
 * @returns {Object|null} - Configuração do agente ou null se não encontrado
 */
function getAgent(agentId) {
	return AGENTS[agentId] || null;
}

/**
 * Lista todos os agentes disponíveis
 * @returns {Array} - Array de objetos de agente
 */
function listAgents() {
	return Object.values(AGENTS);
}

/**
 * Obtém o ID do agente baseado no comando
 * @param {string} command - Nome do comando
 * @returns {string|null} - ID do agente ou null se não mapeado
 */
function getAgentByCommand(command) {
	return COMMAND_AGENT_MAP[command] || null;
}

/**
 * Verifica se um agente existe
 * @param {string} agentId - ID do agente
 * @returns {boolean}
 */
function agentExists(agentId) {
	return agentId in AGENTS;
}

/**
 * Obtém o workspace do AnythingLLM para um agente
 * @param {string} agentId - ID do agente
 * @returns {string|null} - Nome do workspace ou null
 */
function getWorkspace(agentId) {
	const agent = AGENTS[agentId];
	return agent ? agent.workspace : null;
}

module.exports = {
	AGENTS,
	DEFAULT_AGENT,
	AGENT_BEHAVIOR,
	COMMAND_AGENT_MAP,
	getAgent,
	listAgents,
	getAgentByCommand,
	agentExists,
	getWorkspace
};
