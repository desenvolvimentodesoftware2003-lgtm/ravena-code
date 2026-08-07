/**
 * AgentMemory.js
 *
 * Sistema de memória de contexto para agentes.
 * Permite que os agentes lembrem de conversas anteriores
 * e mantenham contexto entre múltiplas interações.
 *
 * Nível 3 - Memória de Contexto
 */

"use strict";

const Logger = require("../utils/Logger");
const { getAgent } = require("./AgentConfig");

const logger = new Logger("agent-memory");

/**
 * Tipos de memória
 */
const MEMORY_TYPES = {
	SHORT_TERM: "short-term", // Últimas N mensagens (janela deslizante)
	LONG_TERM: "long-term", // Informações importantes persistidas
	EPISODIC: "episodic", // Interações específicas (por sessão)
	SEMANTIC: "semantic" // Conhecimento geral (fatos, preferências)
};

/**
 * Class for agent memory management
 */
class AgentMemory {
	constructor() {
		// Memória de curto prazo: groupId:agentId -> [messages]
		this.shortTermMemory = new Map();

		// Memória de longo prazo: groupId:agentId -> [facts]
		this.longTermMemory = new Map();

		// Memória episódica: sessionId -> { context, interactions }
		this.episodicMemory = new Map();

		// Memória semântica: groupId -> { preferences, facts }
		this.semanticMemory = new Map();

		// Configurações
		this.config = {
			shortTermMaxMessages: 20, // Máximo de mensagens na memória de curto prazo
			shortTermTTL: 30 * 60 * 1000, // 30 minutos
			longTermMaxFacts: 100, // Máximo de fatos por agente
			episodicMaxSessions: 50, // Máximo de sessões episódicas
			semanticMaxEntries: 200, // Máximo de entradas semânticas
			enableAutoSummarize: true, // Habilitar resumo automático
			summarizeThreshold: 10 // Resumir após N mensagens
		};

		// Estatísticas
		this.stats = {
			totalMemories: 0,
			shortTermHits: 0,
			longTermHits: 0,
			episodicHits: 0,
			semanticHits: 0,
			memoriesCreated: 0,
			memoriesEvicted: 0
		};

		// Timer para limpeza periódica
		this.cleanupInterval = null;
		this.startCleanupTimer();
	}

	/**
	 * Get singleton instance
	 * @returns {AgentMemory} - Singleton instance
	 */
	static getInstance() {
		if (!AgentMemory.instance) {
			AgentMemory.instance = new AgentMemory();
		}
		return AgentMemory.instance;
	}

	/**
	 * Inicia timer de limpeza periódica
	 */
	startCleanupTimer() {
		// Limpar a cada 5 minutos
		this.cleanupInterval = setInterval(
			() => {
				this.cleanup();
			},
			5 * 60 * 1000
		);
	}

	/**
	 * Para timer de limpeza
	 */
	stopCleanupTimer() {
		if (this.cleanupInterval) {
			clearInterval(this.cleanupInterval);
			this.cleanupInterval = null;
		}
	}

	// ===========================================================================
	// Memória de Curto Prazo
	// ===========================================================================

	/**
	 * Adiciona mensagem à memória de curto prazo
	 * @param {string} groupId - ID do grupo
	 * @param {string} agentId - ID do agente
	 * @param {Object} message - Dados da mensagem
	 */
	addShortTerm(groupId, agentId, message) {
		const key = `${groupId}:${agentId}`;

		if (!this.shortTermMemory.has(key)) {
			this.shortTermMemory.set(key, []);
		}

		const messages = this.shortTermMemory.get(key);

		// Adicionar mensagem com timestamp
		messages.push({
			...message,
			timestamp: Date.now()
		});

		// Limitar tamanho da memória
		if (messages.length > this.config.shortTermMaxMessages) {
			messages.shift(); // Remove a mais antiga
			this.stats.memoriesEvicted++;
		}

		this.stats.totalMemories++;
		this.stats.memoriesCreated++;

		// Verificar se deve resumir
		if (this.config.enableAutoSummarize && messages.length >= this.config.summarizeThreshold) {
			this.summarizeShortTerm(groupId, agentId);
		}
	}

	/**
	 * Obtém memória de curto prazo
	 * @param {string} groupId - ID do grupo
	 * @param {string} agentId - ID do agente
	 * @param {number} limit - Limite de mensagens
	 * @returns {Array} - Lista de mensagens
	 */
	getShortTerm(groupId, agentId, limit = 10) {
		const key = `${groupId}:${agentId}`;
		const messages = this.shortTermMemory.get(key) || [];

		this.stats.shortTermHits++;

		// Retornar as últimas N mensagens
		return messages.slice(-limit);
	}

	/**
	 * Limpa memória de curto prazo expirada
	 */
	cleanupShortTerm() {
		const now = Date.now();
		let cleaned = 0;

		for (const [key, messages] of this.shortTermMemory.entries()) {
			// Filtrar mensagens não expiradas
			const validMessages = messages.filter(
				(msg) => now - msg.timestamp < this.config.shortTermTTL
			);

			if (validMessages.length < messages.length) {
				this.shortTermMemory.set(key, validMessages);
				cleaned += messages.length - validMessages.length;
			}

			// Remover se vazio
			if (validMessages.length === 0) {
				this.shortTermMemory.delete(key);
			}
		}

		if (cleaned > 0) {
			logger.debug(`[cleanupShortTerm] Cleaned ${cleaned} expired messages`);
			this.stats.memoriesEvicted += cleaned;
		}
	}

	/**
	 * Resume memória de curto prazo
	 * @param {string} groupId - ID do grupo
	 * @param {string} agentId - ID do agente
	 */
	summarizeShortTerm(groupId, agentId) {
		const key = `${groupId}:${agentId}`;
		const messages = this.shortTermMemory.get(key) || [];

		if (messages.length < this.config.summarizeThreshold) {
			return;
		}

		// Criar resumo das mensagens
		const summary = this.createSummary(messages);

		// Adicionar à memória de longo prazo
		this.addLongTerm(groupId, agentId, {
			type: "summary",
			content: summary,
			timestamp: Date.now(),
			messageCount: messages.length
		});

		// Manter apenas as últimas 5 mensagens na memória de curto prazo
		const recentMessages = messages.slice(-5);
		this.shortTermMemory.set(key, recentMessages);

		logger.debug(`[summarizeShortTerm] Summarized ${messages.length} messages for ${key}`);
	}

	/**
	 * Cria resumo de um conjunto de mensagens
	 * @param {Array} messages - Mensagens
	 * @returns {string} - Resumo
	 */
	createSummary(messages) {
		// Extrair tópicos principais
		const topics = new Set();
		const keywords = new Set();

		for (const msg of messages) {
			if (msg.text) {
				// Extrair palavras-chave simples
				const words = msg.text
					.toLowerCase()
					.split(/\s+/)
					.filter((w) => w.length > 4);

				words.forEach((w) => keywords.add(w));
			}

			if (msg.topic) {
				topics.add(msg.topic);
			}
		}

		let summary = "Resumo da conversa:\n";

		if (topics.size > 0) {
			summary += `Tópicos: ${Array.from(topics).join(", ")}\n`;
		}

		if (keywords.size > 0) {
			const topKeywords = Array.from(keywords).slice(0, 10);
			summary += `Palavras-chave: ${topKeywords.join(", ")}\n`;
		}

		summary += `Total de mensagens: ${messages.length}`;

		return summary;
	}

	// ===========================================================================
	// Memória de Longo Prazo
	// ===========================================================================

	/**
	 * Adiciona fato à memória de longo prazo
	 * @param {string} groupId - ID do grupo
	 * @param {string} agentId - ID do agente
	 * @param {Object} fact - Fato para memorizar
	 */
	addLongTerm(groupId, agentId, fact) {
		const key = `${groupId}:${agentId}`;

		if (!this.longTermMemory.has(key)) {
			this.longTermMemory.set(key, []);
		}

		const facts = this.longTermMemory.get(key);

		// Verificar se o fato já existe (deduplicação)
		const existingIndex = facts.findIndex(
			(f) => f.content === fact.content && f.type === fact.type
		);

		if (existingIndex >= 0) {
			// Atualizar timestamp
			facts[existingIndex].timestamp = Date.now();
			facts[existingIndex].accessCount = (facts[existingIndex].accessCount || 0) + 1;
		} else {
			// Adicionar novo fato
			facts.push({
				...fact,
				timestamp: Date.now(),
				accessCount: 0
			});
		}

		// Limitar tamanho da memória
		if (facts.length > this.config.longTermMaxFacts) {
			// Ordenar por timestamp e acesso, remover os mais antigos
			facts.sort((a, b) => {
				// Primeiro por accessCount (descendente)
				if (b.accessCount !== a.accessCount) {
					return b.accessCount - a.accessCount;
				}
				// Depois por timestamp (descendente)
				return b.timestamp - a.timestamp;
			});

			// Manter apenas os mais relevantes
			const removed = facts.splice(this.config.longTermMaxFacts);
			this.stats.memoriesEvicted += removed.length;
		}

		this.stats.totalMemories++;
		this.stats.memoriesCreated++;
	}

	/**
	 * Obtém memória de longo prazo
	 * @param {string} groupId - ID do grupo
	 * @param {string} agentId - ID do agente
	 * @param {number} limit - Limite de fatos
	 * @returns {Array} - Lista de fatos
	 */
	getLongTerm(groupId, agentId, limit = 10) {
		const key = `${groupId}:${agentId}`;
		const facts = this.longTermMemory.get(key) || [];

		this.stats.longTermHits++;

		// Ordenar por relevância (timestamp + acesso)
		const sorted = [...facts].sort((a, b) => {
			// Calcular score de relevância
			const scoreA = this.calculateRelevance(a);
			const scoreB = this.calculateRelevance(b);
			return scoreB - scoreA;
		});

		// Atualizar contagem de acesso
		for (const fact of sorted.slice(0, limit)) {
			fact.accessCount = (fact.accessCount || 0) + 1;
		}

		return sorted.slice(0, limit);
	}

	/**
	 * Calcula relevância de um fato
	 * @param {Object} fact - Fato
	 * @returns {number} - Score de relevância
	 */
	calculateRelevance(fact) {
		const age = Date.now() - fact.timestamp;
		const accessCount = fact.accessCount || 0;

		// Fator de tempo (mais recente = mais relevante)
		const timeFactor = Math.max(0, 1 - age / (24 * 60 * 60 * 1000)); // 24h

		// Fator de acesso (mais acessado = mais relevante)
		const accessFactor = Math.min(1, accessCount / 10);

		return timeFactor * 0.7 + accessFactor * 0.3;
	}

	// ===========================================================================
	// Memória Episódica
	// ===========================================================================

	/**
	 * Cria sessão episódica
	 * @param {string} groupId - ID do grupo
	 * @param {string} agentId - ID do agente
	 * @param {Object} context - Contexto inicial
	 * @returns {string} - ID da sessão
	 */
	createEpisode(groupId, agentId, context = {}) {
		const episodeId = `ep-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

		this.episodicMemory.set(episodeId, {
			groupId,
			agentId,
			startTime: Date.now(),
			lastActivity: Date.now(),
			context,
			interactions: [],
			outcome: null
		});

		this.stats.totalMemories++;
		this.stats.memoriesCreated++;

		// Limitar número de sessões
		if (this.episodicMemory.size > this.config.episodicMaxSessions) {
			this.evictOldestEpisodes();
		}

		return episodeId;
	}

	/**
	 * Adiciona interação à sessão episódica
	 * @param {string} episodeId - ID da sessão
	 * @param {Object} interaction - Dados da interação
	 */
	addEpisodeInteraction(episodeId, interaction) {
		const episode = this.episodicMemory.get(episodeId);
		if (!episode) {
			return;
		}

		episode.interactions.push({
			...interaction,
			timestamp: Date.now()
		});

		episode.lastActivity = Date.now();
	}

	/**
	 * Finaliza sessão episódica
	 * @param {string} episodeId - ID da sessão
	 * @param {string} outcome - Resultado da sessão
	 */
	endEpisode(episodeId, outcome = "completed") {
		const episode = this.episodicMemory.get(episodeId);
		if (!episode) {
			return;
		}

		episode.endTime = Date.now();
		episode.duration = episode.endTime - episode.startTime;
		episode.outcome = outcome;

		// Extrair aprendizados da sessão
		const learnings = this.extractLearnings(episode);

		// Adicionar à memória de longo prazo
		if (learnings.length > 0) {
			for (const learning of learnings) {
				this.addLongTerm(episode.groupId, episode.agentId, {
					type: "learning",
					content: learning,
					episodeId,
					timestamp: Date.now()
				});
			}
		}
	}

	/**
	 * Extrai aprendizados de uma sessão
	 * @param {Object} episode - Sessão
	 * @returns {Array} - Aprendizados
	 */
	extractLearnings(episode) {
		const learnings = [];

		// Analisar interações para encontrar padrões
		const userMessages = episode.interactions
			.filter((i) => i.type === "user")
			.map((i) => i.content);

		const botMessages = episode.interactions.filter((i) => i.type === "bot").map((i) => i.content);

		// Extrair tópicos de interesse do usuário
		if (userMessages.length > 0) {
			const topics = this.extractTopics(userMessages);
			if (topics.length > 0) {
				learnings.push(`Usuário demonstrou interesse em: ${topics.join(", ")}`);
			}
		}

		// Verificar se houve problemas
		const hasErrors = botMessages.some(
			(m) => m.toLowerCase().includes("erro") || m.toLowerCase().includes("error")
		);

		if (hasErrors) {
			learnings.push("Houve erros durante a interação");
		}

		// Verificar se a sessão foi bem-sucedida
		const successIndicators = ["obrigado", "obrigada", "perfeito", "excelente", "resolvido"];

		const hasSuccess = userMessages.some((m) =>
			successIndicators.some((indicator) => m.toLowerCase().includes(indicator))
		);

		if (hasSuccess) {
			learnings.push("Sessão concluída com sucesso");
		}

		return learnings;
	}

	/**
	 * Extrai tópicos de um conjunto de mensagens
	 * @param {Array} messages - Mensagens
	 * @returns {Array} - Tópicos
	 */
	extractTopics(messages) {
		const topics = new Set();

		// Padrões simples de extração de tópicos
		const topicPatterns = [
			{ pattern: /api|rest|endpoint/i, topic: "API" },
			{ pattern: /segurança|security|hacker/i, topic: "segurança" },
			{ pattern: /código|code|programação/i, topic: "programação" },
			{ pattern: /banco de dados|database|sql/i, topic: "banco de dados" },
			{ pattern: /deploy|docker|servidor/i, topic: "infraestrutura" },
			{ pattern: /erro|error|bug/i, topic: "debugging" },
			{ pattern: /pesquisa|search|buscar/i, topic: "pesquisa" }
		];

		for (const message of messages) {
			for (const { pattern, topic } of topicPatterns) {
				if (pattern.test(message)) {
					topics.add(topic);
				}
			}
		}

		return Array.from(topics);
	}

	/**
	 * Obtém sessão episódica
	 * @param {string} episodeId - ID da sessão
	 * @returns {Object|null} - Sessão
	 */
	getEpisode(episodeId) {
		return this.episodicMemory.get(episodeId) || null;
	}

	/**
	 * Obtém episódios de um grupo/agente
	 * @param {string} groupId - ID do grupo
	 * @param {string} agentId - ID do agente
	 * @param {number} limit - Limite de episódios
	 * @returns {Array} - Lista de episódios
	 */
	getEpisodes(groupId, agentId, limit = 10) {
		const episodes = [];

		for (const [id, episode] of this.episodicMemory.entries()) {
			if (episode.groupId === groupId && episode.agentId === agentId) {
				episodes.push({ id, ...episode });
			}
		}

		// Ordenar por atividade mais recente
		episodes.sort((a, b) => b.lastActivity - a.lastActivity);

		return episodes.slice(0, limit);
	}

	/**
	 * Remove episódios mais antigos
	 */
	evictOldestEpisodes() {
		const episodes = Array.from(this.episodicMemory.entries()).sort(
			(a, b) => a[1].lastActivity - b[1].lastActivity
		);

		const toRemove = episodes.slice(0, episodes.length - this.config.episodicMaxSessions);

		for (const [id] of toRemove) {
			this.episodicMemory.delete(id);
			this.stats.memoriesEvicted++;
		}
	}

	// ===========================================================================
	// Memória Semântica
	// ===========================================================================

	/**
	 * Adiciona preferência/fato semântico
	 * @param {string} groupId - ID do grupo
	 * @param {string} key - Chave (ex: "preferred_language")
	 * @param {any} value - Valor
	 * @param {string} agentId - ID do agente (opcional)
	 */
	setSemantic(groupId, key, value, agentId = null) {
		if (!this.semanticMemory.has(groupId)) {
			this.semanticMemory.set(groupId, new Map());
		}

		const groupMemory = this.semanticMemory.get(groupId);
		const semanticKey = agentId ? `${agentId}:${key}` : key;

		groupMemory.set(semanticKey, {
			value,
			timestamp: Date.now(),
			agentId
		});

		this.stats.totalMemories++;
		this.stats.memoriesCreated++;

		// Limitar tamanho
		if (groupMemory.size > this.config.semanticMaxEntries) {
			const entries = Array.from(groupMemory.entries()).sort(
				(a, b) => a[1].timestamp - b[1].timestamp
			);

			const toRemove = entries.slice(0, entries.length - this.config.semanticMaxEntries);

			for (const [key] of toRemove) {
				groupMemory.delete(key);
				this.stats.memoriesEvicted++;
			}
		}
	}

	/**
	 * Obtém preferência/fato semântico
	 * @param {string} groupId - ID do grupo
	 * @param {string} key - Chave
	 * @param {string} agentId - ID do agente (opcional)
	 * @returns {any} - Valor
	 */
	getSemantic(groupId, key, agentId = null) {
		const groupMemory = this.semanticMemory.get(groupId);
		if (!groupMemory) {
			return null;
		}

		const semanticKey = agentId ? `${agentId}:${key}` : key;
		const entry = groupMemory.get(semanticKey);

		if (!entry) {
			return null;
		}

		this.stats.semanticHits++;
		return entry.value;
	}

	/**
	 * Obtém todas as preferências semânticas de um grupo
	 * @param {string} groupId - ID do grupo
	 * @returns {Object} - Preferências
	 */
	getAllSemantic(groupId) {
		const groupMemory = this.semanticMemory.get(groupId);
		if (!groupMemory) {
			return {};
		}

		const preferences = {};
		for (const [key, entry] of groupMemory.entries()) {
			preferences[key] = entry.value;
		}

		return preferences;
	}

	// ===========================================================================
	// Contexto Integrado
	// ===========================================================================

	/**
	 * Monta contexto completo para o agente
	 * @param {string} groupId - ID do grupo
	 * @param {string} agentId - ID do agente
	 * @param {Object} currentMessage - Mensagem atual
	 * @returns {Object} - Contexto completo
	 */
	buildContext(groupId, agentId, currentMessage = {}) {
		// Obter memórias
		const shortTerm = this.getShortTerm(groupId, agentId, 10);
		const longTerm = this.getLongTerm(groupId, agentId, 5);
		const semantic = this.getAllSemantic(groupId);

		// Montar contexto
		const context = {
			// Memória de curto prazo (conversa recente)
			recentConversation: shortTerm.map((m) => ({
				role: m.author === "bot" ? "assistant" : "user",
				content: m.text || m.content
			})),

			// Memória de longo prazo (aprendizados)
			learnings: longTerm.map((f) => f.content),

			// Preferências semânticas
			preferences: semantic,

			// Informações da sessão atual
			session: {
				groupId,
				agentId,
				timestamp: Date.now()
			}
		};

		return context;
	}

	/**
	 * Gera prompt com contexto para o agente
	 * @param {string} groupId - ID do grupo
	 * @param {string} agentId - ID do agente
	 * @param {string} query - Pergunta do usuário
	 * @returns {string} - Prompt com contexto
	 */
	buildPromptWithContext(groupId, agentId, query) {
		const context = this.buildContext(groupId, agentId);
		const agent = getAgent(agentId);

		let prompt = "";

		// Adicionar contexto do agente
		if (agent && agent.systemContext) {
			prompt += `${agent.systemContext}\n\n`;
		}

		// Adicionar preferências
		if (Object.keys(context.preferences).length > 0) {
			prompt += "Preferências do usuário:\n";
			for (const [key, value] of Object.entries(context.preferences)) {
				prompt += `- ${key}: ${value}\n`;
			}
			prompt += "\n";
		}

		// Adicionar aprendizados
		if (context.learnings.length > 0) {
			prompt += "Aprendizados anteriores:\n";
			for (const learning of context.learnings.slice(0, 3)) {
				prompt += `- ${learning}\n`;
			}
			prompt += "\n";
		}

		// Adicionar conversa recente
		if (context.recentConversation.length > 0) {
			prompt += "Conversa recente:\n";
			for (const msg of context.recentConversation.slice(-5)) {
				const role = msg.role === "assistant" ? "Bot" : "Usuário";
				prompt += `${role}: ${msg.content}\n`;
			}
			prompt += "\n";
		}

		// Adicionar pergunta atual
		prompt += `Pergunta: ${query}`;

		return prompt;
	}

	// ===========================================================================
	// Limpeza e Manutenção
	// ===========================================================================

	/**
	 * Limpa todas as memórias expiradas
	 */
	cleanup() {
		this.cleanupShortTerm();
		this.cleanupLongTerm();
		this.cleanupEpisodic();
		this.cleanupSemantic();

		logger.debug("[cleanup] Memory cleanup completed");
	}

	/**
	 * Limpa memória semântica expirada
	 */
	cleanupSemantic() {
		const now = Date.now();
		const maxAge = 90 * 24 * 60 * 60 * 1000; // 90 dias
		let cleaned = 0;

		for (const [groupId, groupMemory] of this.semanticMemory.entries()) {
			const entries = Array.from(groupMemory.entries());
			let groupCleaned = 0;

			for (const [key, entry] of entries) {
				if (now - entry.timestamp > maxAge) {
					groupMemory.delete(key);
					groupCleaned++;
				}
			}

			if (groupCleaned > 0) {
				cleaned += groupCleaned;
				// Remover grupo se vazio
				if (groupMemory.size === 0) {
					this.semanticMemory.delete(groupId);
				}
			}
		}

		if (cleaned > 0) {
			logger.debug(`[cleanupSemantic] Cleaned ${cleaned} old semantic entries`);
			this.stats.memoriesEvicted += cleaned;
		}
	}

	/**
	 * Limpa memória de longo prazo expirada
	 */
	cleanupLongTerm() {
		const now = Date.now();
		const maxAge = 30 * 24 * 60 * 60 * 1000; // 30 dias
		let cleaned = 0;

		for (const [key, facts] of this.longTermMemory.entries()) {
			const validFacts = facts.filter((f) => now - f.timestamp < maxAge);

			if (validFacts.length < facts.length) {
				this.longTermMemory.set(key, validFacts);
				cleaned += facts.length - validFacts.length;
			}

			if (validFacts.length === 0) {
				this.longTermMemory.delete(key);
			}
		}

		if (cleaned > 0) {
			logger.debug(`[cleanupLongTerm] Cleaned ${cleaned} expired facts`);
			this.stats.memoriesEvicted += cleaned;
		}
	}

	/**
	 * Limpa memória episódica expirada
	 */
	cleanupEpisodic() {
		const now = Date.now();
		const maxAge = 7 * 24 * 60 * 60 * 1000; // 7 dias
		let cleaned = 0;

		for (const [id, episode] of this.episodicMemory.entries()) {
			if (now - episode.lastActivity > maxAge) {
				this.episodicMemory.delete(id);
				cleaned++;
			}
		}

		if (cleaned > 0) {
			logger.debug(`[cleanupEpisodic] Cleaned ${cleaned} old episodes`);
			this.stats.memoriesEvicted += cleaned;
		}
	}

	// ===========================================================================
	// Estatísticas e Informações
	// ===========================================================================

	/**
	 * Obtém estatísticas da memória
	 * @returns {Object} - Estatísticas
	 */
	getStats() {
		return {
			...this.stats,
			shortTermSize: this.shortTermMemory.size,
			longTermSize: this.longTermMemory.size,
			episodicSize: this.episodicMemory.size,
			semanticSize: this.semanticMemory.size
		};
	}

	/**
	 * Obtém informações de memória de um grupo/agente
	 * @param {string} groupId - ID do grupo
	 * @param {string} agentId - ID do agente
	 * @returns {Object} - Informações de memória
	 */
	getMemoryInfo(groupId, agentId) {
		const shortTermKey = `${groupId}:${agentId}`;
		const longTermKey = `${groupId}:${agentId}`;

		return {
			shortTerm: {
				size: (this.shortTermMemory.get(shortTermKey) || []).length,
				maxSize: this.config.shortTermMaxMessages
			},
			longTerm: {
				size: (this.longTermMemory.get(longTermKey) || []).length,
				maxSize: this.config.longTermMaxFacts
			},
			episodic: {
				size: this.getEpisodes(groupId, agentId, 100).length,
				maxSize: this.config.episodicMaxSessions
			},
			semantic: {
				size: Object.keys(this.getAllSemantic(groupId)).length,
				maxSize: this.config.semanticMaxEntries
			}
		};
	}

	/**
	 * Limpa memória de um grupo/agente específico
	 * @param {string} groupId - ID do grupo
	 * @param {string} agentId - ID do agente
	 */
	clearMemory(groupId, agentId) {
		if (agentId) {
			// Limpar apenas um agente específico
			this.shortTermMemory.delete(`${groupId}:${agentId}`);
			this.longTermMemory.delete(`${groupId}:${agentId}`);
		} else {
			// Limpar todo o grupo
			const keysToDelete = [];

			for (const key of this.shortTermMemory.keys()) {
				if (key.startsWith(`${groupId}:`)) {
					keysToDelete.push(key);
				}
			}

			keysToDelete.forEach((key) => this.shortTermMemory.delete(key));

			const longTermKeysToDelete = [];

			for (const key of this.longTermMemory.keys()) {
				if (key.startsWith(`${groupId}:`)) {
					longTermKeysToDelete.push(key);
				}
			}

			longTermKeysToDelete.forEach((key) => this.longTermMemory.delete(key));

			this.semanticMemory.delete(groupId);
		}

		logger.info(
			`[clearMemory] Memory cleared for group ${groupId}${agentId ? `, agent ${agentId}` : ""}`
		);
	}

	/**
	 * Reseta todas as memórias
	 */
	resetAll() {
		this.shortTermMemory.clear();
		this.longTermMemory.clear();
		this.episodicMemory.clear();
		this.semanticMemory.clear();

		this.stats = {
			totalMemories: 0,
			shortTermHits: 0,
			longTermHits: 0,
			episodicHits: 0,
			semanticHits: 0,
			memoriesCreated: 0,
			memoriesEvicted: 0
		};

		logger.info("[resetAll] All memories cleared");
	}
}

// Singleton
AgentMemory.instance = null;

module.exports = AgentMemory;
