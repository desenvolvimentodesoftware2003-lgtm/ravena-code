/**
 * AgentRouter.js
 *
 * Roteador central de agentes do AnythingLLM.
 * Gerencia qual agente processa cada mensagem e mantém sessões por grupo.
 *
 * Nível 4 - IA Autônoma, Aprendizado e Permissões
 */

"use strict";

const Logger = require("../utils/Logger");
const {
	AGENTS,
	DEFAULT_AGENT,
	AGENT_BEHAVIOR,
	getAgent,
	listAgents,
	agentExists
} = require("./AgentConfig");
const AgentDelegator = require("./AgentDelegator");
const AgentCollaboration = require("./AgentCollaboration");
const AgentMemory = require("./AgentMemory");
const AgentStateMachine = require("./AgentStateMachine");
const AgentMetrics = require("./AgentMetrics");
const AgentAutonomy = require("./AgentAutonomy");
const AgentLearning = require("./AgentLearning");
const AgentDatabase = require("./AgentDatabase");
const AgentPermissions = require("./AgentPermissions");

/**
 * Singleton AgentRouter class
 */
class AgentRouter {
	/**
	 * Get Singleton Instance
	 * @returns {AgentRouter}
	 */
	static getInstance() {
		if (!AgentRouter.instance) {
			AgentRouter.instance = new AgentRouter();
		}
		return AgentRouter.instance;
	}

	constructor() {
		this.logger = new Logger("agent-router");

		// Sessões ativas: groupId -> { agentId, timestamp, context }
		this.sessions = new Map();

		// Cache de respostas: agentId:query -> { response, timestamp }
		this.responseCache = new Map();

		// Estatísticas de uso
		this.stats = {
			totalRequests: 0,
			byAgent: {},
			byGroup: {},
			errors: 0,
			delegations: 0,
			collaborations: 0
		};

		// Inicializa estatísticas por agente
		Object.keys(AGENTS).forEach((id) => {
			this.stats.byAgent[id] = { requests: 0, errors: 0, avgResponseTime: 0 };
		});

		// Instâncias de módulos
		this.delegator = AgentDelegator.getInstance();
		this.collaboration = AgentCollaboration.getInstance();
		this.memory = AgentMemory.getInstance();
		this.stateMachine = AgentStateMachine.getInstance();
		this.metrics = AgentMetrics.getInstance();
		this.autonomy = AgentAutonomy.getInstance();
		this.learning = AgentLearning.getInstance();
		this.database = AgentDatabase.getInstance();
		this.permissions = AgentPermissions.getInstance();

		// Configuração de delegação
		this.delegationConfig = {
			enabled: true,
			autoDelegate: true,
			minConfidence: 60,
			overrideAgent: true
		};

		// Configuração de memória
		this.memoryConfig = {
			enabled: true,
			useShortTerm: true,
			useLongTerm: true,
			useSemantic: true,
			contextWindowSize: 10
		};

		// Configuração de aprendizado
		this.learningConfig = {
			enabled: true,
			autoLearn: true,
			feedbackEnabled: true
		};

		// Configuração de autonomia
		this.autonomyConfig = {
			enabled: false, // Desativado por padrão (perigoso!)
			defaultLevel: 0,
			requireApproval: true
		};

		// Timer para limpeza periódica (a cada 5 minutos)
		this.cleanupInterval = null;
		this.startCleanupTimer();

		this.logger.info("AgentRouter inicializado (Nível 4 - Autonomia + Aprendizado + Permissões)");
	}

	/**
	 * Inicia timer de limpeza periódica
	 */
	startCleanupTimer() {
		this.cleanupInterval = setInterval(
			() => {
				this.cleanup();
			},
			5 * 60 * 1000
		); // A cada 5 minutos
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

	/**
	 * Executa limpeza periódica de sessões e cache expirados
	 */
	cleanup() {
		this.cleanupSessions();
		this.cleanCache();
		this.cleanupStats();
	}

	/**
	 * Remove sessões expiradas
	 */
	cleanupSessions() {
		const now = Date.now();
		let cleaned = 0;

		for (const [groupId, session] of this.sessions.entries()) {
			if (!this.isSessionValid(session)) {
				this.sessions.delete(groupId);
				cleaned++;
			}
		}

		if (cleaned > 0) {
			this.logger.debug(`[cleanupSessions] ${cleaned} sessões expiradas removidas`);
		}
	}

	/**
	 * Limpa estatísticas de grupos antigos (mais de 30 dias sem atividade)
	 */
	cleanupStats() {
		const now = Date.now();
		const maxAge = 30 * 24 * 60 * 60 * 1000; // 30 dias
		let cleaned = 0;

		for (const [groupId, stats] of Object.entries(this.stats.byGroup)) {
			if (now - stats.lastActivity > maxAge) {
				delete this.stats.byGroup[groupId];
				cleaned++;
			}
		}

		if (cleaned > 0) {
			this.logger.debug(`[cleanupStats] ${cleaned} grupos antigos removidos das estatísticas`);
		}
	}

	/**
	 * Roteia uma mensagem para o agente apropriado
	 * @param {Object} options - Opções de roteamento
	 * @param {string} options.query - A pergunta/mensagem do usuário
	 * @param {string} options.groupId - ID do grupo (null para PV)
	 * @param {string} options.agentName - Nome do agente (opcional, override manual)
	 * @param {string} options.command - Comando que disparou (opcional, para roteamento automático)
	 * @param {Object} options.llmService - Instância do LLMService
	 * @param {Object} options.context - Contexto adicional (opcional)
	 * @returns {Promise<Object>} - { response, agentId, responseTime, fromCache, delegated }
	 */
	async route(options) {
		const {
			query,
			groupId = null,
			agentName = null,
			command = null,
			llmService,
			context = {}
		} = options;

		const startTime = Date.now();
		this.stats.totalRequests++;

		try {
			// 1. Determina qual agente usar (antes da delegação)
			const initialAgentId = this.resolveAgent(agentName, command, groupId);

			// 2. Verifica se deve delegar automaticamente
			let agentId = initialAgentId;
			let delegated = false;
			let delegationInfo = null;

			if (this.delegationConfig.enabled && this.delegationConfig.autoDelegate) {
				// Detecta intenção do usuário
				const intent = this.delegator.detectIntent(query, context);

				// Verifica se deve delegar
				const delegationResult = this.delegator.shouldDelegate(
					initialAgentId,
					intent.agentId,
					intent.confidence,
					{
						minConfidence: this.delegationConfig.minConfidence
					}
				);

				if (delegationResult.shouldDelegate) {
					agentId = delegationResult.targetAgent;
					delegated = true;
					delegationInfo = {
						from: initialAgentId,
						to: agentId,
						confidence: intent.confidence,
						reasons: intent.reasons,
						reason: delegationResult.reason
					};

					this.stats.delegations++;
					this.metrics.recordDelegation(initialAgentId, agentId);
					this.logger.info(
						`[route] Delegação detectada: ${initialAgentId} → ${agentId} (${intent.confidence}%)`
					);
				}
			}

			// 3. Obtém configuração do agente
			const agent = getAgent(agentId);
			if (!agent) {
				throw new Error(`Agente não encontrado: ${agentId}`);
			}

			this.logger.info(
				`[route] Roteando para agente: ${agent.name}${delegated ? " (delegado)" : ""} | Grupo: ${groupId || "PV"} | Query: ${query.substring(0, 50)}...`
			);

			// 4. Verifica cache (se habilitado)
			if (AGENT_BEHAVIOR.enableCache) {
				const cached = this.getCachedResponse(agentId, query);
				if (cached) {
					this.logger.debug(`[route] Cache hit para agente ${agentId}`);
					this.metrics.recordCacheMetric(agentId, true);
					return {
						response: cached.response,
						agentId,
						responseTime: Date.now() - startTime,
						fromCache: true,
						delegated,
						delegationInfo
					};
				}
				this.metrics.recordCacheMetric(agentId, false);
			}

			// 5. Monta o prompt com contexto (usando memória se habilitada)
			let prompt;
			if (this.memoryConfig.enabled && groupId) {
				// Usar memória para construir contexto
				prompt = this.memory.buildPromptWithContext(groupId, agentId, query);

				// Registrar na memória de curto prazo
				this.memory.addShortTerm(groupId, agentId, {
					author: "user",
					text: query,
					timestamp: Date.now()
				});
			} else {
				prompt = this.buildPrompt(query, agent, context);
			}

			// 6. Chama o LLM com o workspace do agente
			const completionOptions = {
				prompt,
				workspace: agent.workspace,
				maxTokens: agent.maxTokens,
				temperature: agent.temperature,
				priority: agent.priority,
				debugPrompt: false,
				...context.completionOptions
			};

			const response = await llmService.getAnythingLLMCompletion(completionOptions);

			// 7. Armazena no cache
			if (AGENT_BEHAVIOR.enableCache && response) {
				this.cacheResponse(agentId, query, response);
			}

			// 8. Atualiza memória de curto prazo com resposta do bot
			if (this.memoryConfig.enabled && groupId) {
				this.memory.addShortTerm(groupId, agentId, {
					author: "bot",
					text: response,
					timestamp: Date.now()
				});

				// Registrar uso de memória
				const memoryInfo = this.memory.getMemoryInfo(groupId, agentId);
				this.metrics.recordMemoryUsage(agentId, "short_term", memoryInfo.shortTerm.size);
				this.metrics.recordMemoryUsage(agentId, "long_term", memoryInfo.longTerm.size);
			}

			// 9. Atualiza estatísticas e métricas
			const responseTime = Date.now() - startTime;
			this.updateStats(agentId, groupId, responseTime, false);
			this.metrics.recordResponseTime(agentId, responseTime);

			// 10. Atualiza sessão do grupo
			if (groupId) {
				this.updateSession(groupId, agentId);
			}

			this.logger.info(
				`[route] Resposta do agente ${agent.name} em ${responseTime}ms | Tamanho: ${response.length}${delegated ? " (delegado)" : ""}`
			);

			return {
				response,
				agentId,
				responseTime,
				fromCache: false,
				delegated,
				delegationInfo
			};
		} catch (error) {
			this.stats.errors++;
			this.metrics.recordError(error.constructor.name || "unknown");
			this.updateStats(null, null, Date.now() - startTime, true);

			this.logger.error(`[route] Erro ao rotear para agente:`, error);
			throw error;
		}
	}

	/**
	 * Roteia uma mensagem com delegação forçada
	 * @param {Object} options - Opções de roteamento
	 * @returns {Promise<Object>} - Resultado da delegação
	 */
	async routeWithDelegation(options) {
		const { query, groupId = null, targetAgent, llmService, context = {} } = options;

		const startTime = Date.now();

		try {
			// Detectar agente atual
			const currentAgent = this.resolveAgent(null, null, groupId);

			// Delegar diretamente
			const result = await this.delegator.delegate({
				query,
				currentAgent,
				targetAgent,
				groupId,
				llmService,
				context: {
					...context,
					confidence: 100 // Delegação manual = confiança máxima
				}
			});

			this.stats.delegations++;

			const responseTime = Date.now() - startTime;

			return {
				...result,
				responseTime,
				delegated: true,
				delegationInfo: {
					from: currentAgent,
					to: targetAgent,
					confidence: 100,
					reason: "Manual delegation"
				}
			};
		} catch (error) {
			this.stats.errors++;
			this.logger.error(`[routeWithDelegation] Erro na delegação:`, error);
			throw error;
		}
	}

	/**
	 * Executa uma colaboração entre múltiplos agentes
	 * @param {Object} options - Opções da colaboração
	 * @returns {Promise<Object>} - Resultado da colaboração
	 */
	async routeCollaboration(options) {
		const {
			workflowId,
			query,
			groupId = null,
			llmService,
			context = {},
			agents: overrideAgents
		} = options;

		try {
			this.stats.collaborations++;

			const result = await this.collaboration.startCollaboration({
				workflowId,
				query,
				groupId,
				llmService,
				context,
				agents: overrideAgents
			});

			return result;
		} catch (error) {
			this.stats.errors++;
			this.logger.error(`[routeCollaboration] Erro na colaboração:`, error);
			throw error;
		}
	}

	/**
	 * Resolve qual agente deve processar a mensagem
	 * @param {string|null} agentName - Nome do agente (override manual)
	 * @param {string|null} command - Comando que disparou
	 * @param {string|null} groupId - ID do grupo
	 * @returns {string} - ID do agente
	 */
	resolveAgent(agentName, command, groupId) {
		// 1. Override manual tem prioridade máxima
		if (agentName && agentExists(agentName)) {
			return agentName;
		}

		// 2. Verifica se o comando mapeia para um agente
		if (command) {
			const agentByCommand = this.getAgentByCommand(command);
			if (agentByCommand) {
				return agentByCommand;
			}
		}

		// 3. Verifica sessão do grupo
		if (groupId) {
			const session = this.getSession(groupId);
			if (session && this.isSessionValid(session)) {
				return session.agentId;
			}
		}

		// 4. Retorna agente padrão
		return DEFAULT_AGENT;
	}

	/**
	 * Obtém o agente associado a um comando
	 * @param {string} command - Nome do comando
	 * @returns {string|null} - ID do agente ou null
	 */
	getAgentByCommand(command) {
		for (const agent of Object.values(AGENTS)) {
			if (agent.commands.includes(command)) {
				return agent.id;
			}
		}
		return null;
	}

	/**
	 * Monta o prompt com contexto do agente
	 * @param {string} query - Pergunta do usuário
	 * @param {Object} agent - Configuração do agente
	 * @param {Object} context - Contexto adicional
	 * @returns {string} - Prompt formatado
	 */
	buildPrompt(query, agent, context = {}) {
		let prompt = "";

		// Adiciona contexto do agente se disponível
		if (agent.systemContext) {
			prompt += `${agent.systemContext}\n\n`;
		}

		// Adiciona contexto de grupo se disponível
		if (context.groupName) {
			prompt += `Grupo: ${context.groupName}\n`;
		}

		// Adiciona histórico se disponível
		if (context.history && context.history.length > 0) {
			prompt += "Histórico da conversa:\n";
			context.history.slice(-5).forEach((msg) => {
				prompt += `${msg.author}: ${msg.text}\n`;
			});
			prompt += "\n";
		}

		// Adiciona a pergunta do usuário
		prompt += `Pergunta: ${query}`;

		return prompt;
	}

	// ===========================================================================
	// Sessões
	// ===========================================================================

	/**
	 * Define o agente ativo para um grupo
	 * @param {string} groupId - ID do grupo
	 * @param {string} agentId - ID do agente
	 */
	setSessionAgent(groupId, agentId) {
		if (!agentExists(agentId)) {
			this.logger.warn(`[setSessionAgent] Agente inválido: ${agentId}`);
			return;
		}

		this.sessions.set(groupId, {
			agentId,
			timestamp: Date.now(),
			context: {}
		});

		this.logger.info(`[setSessionAgent] Agente ${agentId} definido para grupo ${groupId}`);
	}

	/**
	 * Obtém o agente da sessão de um grupo
	 * @param {string} groupId - ID do grupo
	 * @returns {Object|null} - Dados da sessão ou null
	 */
	getSession(groupId) {
		return this.sessions.get(groupId) || null;
	}

	/**
	 * Verifica se a sessão ainda é válida
	 * @param {Object} session - Dados da sessão
	 * @returns {boolean}
	 */
	isSessionValid(session) {
		const age = Date.now() - session.timestamp;
		return age < AGENT_BEHAVIOR.sessionTimeout;
	}

	/**
	 * Atualiza a sessão de um grupo
	 * @param {string} groupId - ID do grupo
	 * @param {string} agentId - ID do agente
	 */
	updateSession(groupId, agentId) {
		const existing = this.getSession(groupId);
		if (existing && existing.agentId === agentId) {
			// Apenas atualiza o timestamp
			existing.timestamp = Date.now();
		} else {
			// Cria nova sessão
			this.setSessionAgent(groupId, agentId);
		}
	}

	/**
	 * Remove a sessão de um grupo (reseta para agente padrão)
	 * @param {string} groupId - ID do grupo
	 */
	clearSession(groupId) {
		this.sessions.delete(groupId);
		this.logger.info(`[clearSession] Sessão removida para grupo ${groupId}`);
	}

	// ===========================================================================
	// Cache
	// ===========================================================================

	/**
	 * Gera a chave do cache
	 * @param {string} agentId - ID do agente
	 * @param {string} query - Query do usuário
	 * @returns {string} - Chave do cache
	 */
	getCacheKey(agentId, query) {
		// Normaliza a query (lowercase, sem espaços extras)
		const normalized = query.toLowerCase().trim().replace(/\s+/g, " ");
		return `${agentId}:${normalized}`;
	}

	/**
	 * Obtém resposta do cache
	 * @param {string} agentId - ID do agente
	 * @param {string} query - Query do usuário
	 * @returns {Object|null} - Resposta cacheada ou null
	 */
	getCachedResponse(agentId, query) {
		const key = this.getCacheKey(agentId, query);
		const cached = this.responseCache.get(key);

		if (!cached) return null;

		// Verifica se o cache ainda é válido
		const age = Date.now() - cached.timestamp;
		if (age > AGENT_BEHAVIOR.cacheTTL) {
			this.responseCache.delete(key);
			return null;
		}

		return cached;
	}

	/**
	 * Armazena resposta no cache
	 * @param {string} agentId - ID do agente
	 * @param {string} query - Query do usuário
	 * @param {string} response - Resposta do agente
	 */
	cacheResponse(agentId, query, response) {
		const key = this.getCacheKey(agentId, query);
		this.responseCache.set(key, {
			response,
			timestamp: Date.now()
		});

		// Limpa cache antigo periodicamente
		if (this.responseCache.size > 1000) {
			this.cleanCache();
		}
	}

	/**
	 * Limpa entradas expiradas do cache
	 */
	cleanCache() {
		const now = Date.now();
		let cleaned = 0;

		for (const [key, cached] of this.responseCache.entries()) {
			if (now - cached.timestamp > AGENT_BEHAVIOR.cacheTTL) {
				this.responseCache.delete(key);
				cleaned++;
			}
		}

		if (cleaned > 0) {
			this.logger.debug(`[cleanCache] ${cleaned} entradas removidas do cache`);
		}
	}

	// ===========================================================================
	// Estatísticas
	// ===========================================================================

	/**
	 * Atualiza estatísticas de uso
	 * @param {string|null} agentId - ID do agente
	 * @param {string|null} groupId - ID do grupo
	 * @param {number} responseTime - Tempo de resposta (ms)
	 * @param {boolean} isError - Se foi erro
	 */
	updateStats(agentId, groupId, responseTime, isError) {
		if (agentId && this.stats.byAgent[agentId]) {
			const agentStats = this.stats.byAgent[agentId];
			if (!isError) {
				agentStats.requests++;
				// Média móvel simples
				agentStats.avgResponseTime =
					(agentStats.avgResponseTime * (agentStats.requests - 1) + responseTime) /
					agentStats.requests;
			} else {
				agentStats.errors++;
			}
		}

		if (groupId) {
			if (!this.stats.byGroup[groupId]) {
				this.stats.byGroup[groupId] = { requests: 0, lastAgent: null, lastActivity: Date.now() };
			}
			this.stats.byGroup[groupId].requests++;
			this.stats.byGroup[groupId].lastActivity = Date.now();
			if (agentId) {
				this.stats.byGroup[groupId].lastAgent = agentId;
			}
		}
	}

	/**
	 * Obtém estatísticas de uso
	 * @returns {Object} - Estatísticas
	 */
	getStats() {
		return {
			...this.stats,
			sessions: this.sessions.size,
			cacheSize: this.responseCache.size,
			delegatorStats: this.delegator.getStats(),
			collaborationStats: this.collaboration.getStats()
		};
	}

	/**
	 * Obtém estatísticas de um agente específico
	 * @param {string} agentId - ID do agente
	 * @returns {Object|null} - Estatísticas do agente
	 */
	getAgentStats(agentId) {
		return this.stats.byAgent[agentId] || null;
	}

	// ===========================================================================
	// Utilitários
	// ===========================================================================

	/**
	 * Lista todos os agentes com suas configurações
	 * @returns {Array} - Lista de agentes
	 */
	getAvailableAgents() {
		return listAgents().map((agent) => ({
			id: agent.id,
			name: agent.name,
			description: agent.description,
			emoji: agent.emoji,
			commands: agent.commands,
			stats: this.stats.byAgent[agent.id] || { requests: 0, errors: 0, avgResponseTime: 0 }
		}));
	}

	/**
	 * Obtém o agente ativo para um grupo
	 * @param {string} groupId - ID do grupo
	 * @returns {Object} - { agentId, agentName, isDefault }
	 */
	getActiveAgent(groupId) {
		const session = this.getSession(groupId);

		if (session && this.isSessionValid(session)) {
			const agent = getAgent(session.agentId);
			return {
				agentId: session.agentId,
				agentName: agent ? agent.name : session.agentId,
				isDefault: false
			};
		}

		const defaultAgent = getAgent(DEFAULT_AGENT);
		return {
			agentId: DEFAULT_AGENT,
			agentName: defaultAgent ? defaultAgent.name : DEFAULT_AGENT,
			isDefault: true
		};
	}

	/**
	 * Força reset de todas as sessões e cache
	 */
	reset() {
		this.stopCleanupTimer();
		this.sessions.clear();
		this.responseCache.clear();
		this.stats = {
			totalRequests: 0,
			byAgent: {},
			byGroup: {},
			errors: 0,
			delegations: 0,
			collaborations: 0
		};
		this.logger.info("[reset] Todas as sessões, cache e estatísticas foram limpos");
	}
}

module.exports = AgentRouter;
