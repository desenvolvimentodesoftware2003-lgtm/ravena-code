/**
 * AgentDelegator.js
 *
 * Sistema de delegação automática entre agentes.
 * Permite que o agente "ravena" detecte a intenção do usuário
 * e delegue para o agente especializado mais adequado.
 *
 * Nível 2 - Comunicação Inter-Agentes
 */

"use strict";

const Logger = require("../utils/Logger");
const { getAgent, listAgents, AGENTS } = require("./AgentConfig");

const logger = new Logger("agent-delegator");

/**
 * Padrões de detecção de intenção por agente
 */
const INTENT_PATTERNS = {
	dev: {
		keywords: [
			"codigo",
			"código",
			"programar",
			"programação",
			"programacao",
			"javascript",
			"node",
			"nodejs",
			"python",
			"java",
			"typescript",
			"react",
			"vue",
			"angular",
			"html",
			"css",
			"sql",
			"mongodb",
			"api",
			"rest",
			"graphql",
			"backend",
			"frontend",
			"fullstack",
			"bug",
			"erro",
			"debug",
			"compilar",
			"compilação",
			"build",
			"npm",
			"yarn",
			"pip",
			"git",
			"github",
			"repositorio",
			"repositório",
			"deploy",
			"docker",
			"kubernetes",
			"servidor",
			"server",
			"função",
			"funcao",
			"classe",
			"objeto",
			"variavel",
			"variável",
			"array",
			"loop",
			"for",
			"while",
			"if",
			"else",
			"switch",
			"async",
			"await",
			"promise",
			"callback",
			"event",
			"banco de dados",
			"database",
			"tabela",
			"coluna",
			"linha",
			"query",
			"select",
			"insert",
			"update",
			"delete",
			"framework",
			"biblioteca",
			"lib",
			"pacote",
			"package"
		],
		patterns: [
			/como\s+(?:criar|fazer|implementar|desenvolver|programar|criar|escrever)/i,
			/qual\s+(?:a\s+)?(?:função|classe|metodo|metódo|api)/i,
			/por\s+que\s+(?:não\s+)?(?:funciona|roda|compila|executa)/i,
			/preciso\s+(?:de\s+)?(?:ajuda|ajudar|programar|criar|implementar)/i,
			/\b(?:error|erro|exception|bug|fail|falha)\b/i,
			/como\s+(?:usar|utilizar|empregar|aplicar)\s+(?:o|a|as|os)?\s*\w+/i,
			/exemplo\s+(?:de|do|da)\s+(?:código|programa|função|classe)/i
		],
		scoreThreshold: 0.6
	},
	busca360: {
		keywords: [
			"pesquisar",
			"pesquisa",
			"buscar",
			"busca",
			"encontrar",
			"o que é",
			"o que sao",
			"quem é",
			"quem foi",
			"onde é",
			"quando",
			"como",
			"por que",
			"qual",
			"quais",
			"noticia",
			"noticias",
			"atualidade",
			"atualidades",
			"informação",
			"informacao",
			"dados",
			"estatistica",
			"estatística",
			"comparar",
			"comparação",
			"comparacao",
			"diferença",
			"diferenca",
			"análise",
			"analise",
			"avaliar",
			"avaliação",
			"avaliacao",
			"explicar",
			"explicação",
			"explicacao",
			"entender",
			"compreender",
			"história",
			"historia",
			"conceito",
			"definição",
			"definicao",
			"pesquisa",
			"estudo",
			"artigo",
			"publicação",
			"publicacao",
			"pesquisar no google",
			"buscar na web",
			"procure por"
		],
		patterns: [
			/o\s+que\s+(?:é|e|são|sao)/i,
			/quem\s+(?:é|e|foi|foram)/i,
			/onde\s+(?:é|e|está|esta|fica)/i,
			/quando\s+(?:foi|nasceu|aconteceu|ocorreu)/i,
			/por\s+que\s+(?:é|e|acontece|ocorre)/i,
			/qual\s+(?:é|e|a|o|as|os)\s+\w+/i,
			/como\s+funciona/i,
			/explique?\s+(?:sobre|a respeito de|o que)/i,
			/me\s+(?:diga|fale|conte|explique)/i,
			/pesquis(?:e|ar|ando)\s+(?:sobre|a respeito de)/i,
			/busque?\s+(?:por|informações?|dados?|notícias?)/i
		],
		scoreThreshold: 0.5
	},
	hacker: {
		keywords: [
			"segurança",
			"seguranca",
			"security",
			"hacker",
			"hacking",
			"vulnerabilidade",
			"vulnerabilidade",
			"exploit",
			"exploitation",
			"penetration",
			"pentest",
			"pentesting",
			"cybersecurity",
			"firewall",
			"antivírus",
			"antivirus",
			"malware",
			"virus",
			"vírus",
			"criptografia",
			"criptografar",
			"descriptografar",
			"hash",
			"ataque",
			"ataques",
			"defesa",
			"proteção",
			"protecao",
			"autenticação",
			"autenticacao",
			"autorização",
			"autorizacao",
			"token",
			"senha",
			"password",
			"credenciais",
			"credenciais",
			"sql injection",
			"xss",
			"csrf",
			"rfi",
			"lfi",
			"rce",
			"brute force",
			"ddos",
			"dos",
			"phishing",
			"social engineering",
			"pentest",
			"red team",
			"blue team",
			"white hat",
			"black hat",
			"cyber",
			"infosec",
			"opsec",
			"hardening",
			"加固",
			"vulnerability",
			"threat",
			"risk",
			"risk assessment",
			"backup",
			"recuperação",
			"recuperacao",
			"contingência",
			"contingencia",
			"rgpd",
			"lgpd",
			"compliance",
			"regulamentação",
			"regulamentacao"
		],
		patterns: [
			/como\s+(?:proteger|defender|blindar|segurar|proteger)/i,
			/qual\s+(?:a\s+)?(?:melhor\s+)?(?:prática|pratica|forma|jeito|modo)\s+de\s+(?:proteger|segurar|defender)/i,
			/(?:é\s+)?(?:possível|possivel|viável|viavel)\s+(?:hackear|invadir|comprometer|explorar)/i,
			/como\s+(?:detectar|identificar|descobrir|encontrar)\s+(?:uma\s+)?(?:vulnerabilidade|brecha|falha)/i,
			/(?:me|eu)\s+(?:ensine|ajude|ajuda)\s+(?:a|hacker|hackear|penetrar)/i,
			/(?:tem|existe|possui)\s+(?:alguma|uma|algumas)\s+(?:vulnerabilidade|falha|brecha)/i,
			/como\s+(?:fazer|realizar|executar)\s+(?:um\s+)?(?:pentest|penetration test)/i,
			/segurança\s+(?:da\s+)?(?:informação|informacao|dados|sistema)/i
		],
		scoreThreshold: 0.55
	}
};

/**
 * Class for agent delegation
 */
class AgentDelegator {
	constructor() {
		this.enabled = true;
		this.stats = {
			totalDelegations: 0,
			delegationsByAgent: {},
			failedDelegations: 0
		};

		// Cache de intenções analisadas
		this.intentCache = new Map();
		this.CACHE_TTL = 5 * 60 * 1000; // 5 minutos

		// Padrões de cache
		this.cacheHits = 0;
		this.cacheMisses = 0;

		// Timer para limpeza periódica do cache (a cada 2 minutos)
		this.cleanupInterval = null;
		this.startCleanupTimer();
	}

	/**
	 * Get singleton instance
	 * @returns {AgentDelegator} - Singleton instance
	 */
	static getInstance() {
		if (!AgentDelegator.instance) {
			AgentDelegator.instance = new AgentDelegator();
		}
		return AgentDelegator.instance;
	}

	/**
	 * Inicia timer de limpeza periódica do cache
	 */
	startCleanupTimer() {
		this.cleanupInterval = setInterval(
			() => {
				this.cleanCache();
			},
			2 * 60 * 1000
		); // A cada 2 minutos
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
	 * Analisa a intenção do usuário e retorna o agente mais adequado
	 * @param {string} query - Texto da pergunta do usuário
	 * @param {Object} context - Contexto adicional (grupo, autor, etc.)
	 * @returns {Object} - { agentId, confidence, reasons }
	 */
	detectIntent(query, context = {}) {
		if (!query || query.trim().length < 3) {
			return { agentId: null, confidence: 0, reasons: [] };
		}

		const normalizedQuery = query
			.toLowerCase()
			.normalize("NFD")
			.replace(/[\u0300-\u036f]/g, "")
			.trim();

		// Verificar cache
		const cacheKey = normalizedQuery;
		const cached = this.intentCache.get(cacheKey);
		if (cached && Date.now() - cached.timestamp < this.CACHE_TTL) {
			this.cacheHits++;
			logger.debug(`[Delegator] Cache hit for query: "${query.substring(0, 30)}..."`);
			return cached.result;
		}

		this.cacheMisses++;

		// Calcular pontuação para cada agente
		const scores = {};

		for (const [agentId, patterns] of Object.entries(INTENT_PATTERNS)) {
			scores[agentId] = {
				keywordScore: 0,
				patternScore: 0,
				totalScore: 0,
				reasons: []
			};

			// Verificar palavras-chave
			const matchedKeywords = patterns.keywords.filter((kw) => normalizedQuery.includes(kw));

			if (matchedKeywords.length > 0) {
				scores[agentId].keywordScore = (matchedKeywords.length / patterns.keywords.length) * 0.6;
				scores[agentId].reasons.push(`keywords: ${matchedKeywords.slice(0, 3).join(", ")}`);
			}

			// Verificar padrões regex
			const matchedPatterns = patterns.patterns.filter((p) => p.test(query));

			if (matchedPatterns.length > 0) {
				scores[agentId].patternScore = (matchedPatterns.length / patterns.patterns.length) * 0.4;
				scores[agentId].reasons.push(`patterns: ${matchedPatterns.length} match(es)`);
			}

			// Calcular pontuação total
			scores[agentId].totalScore = scores[agentId].keywordScore + scores[agentId].patternScore;
		}

		// Encontrar o agente com maior pontuação
		let bestAgent = null;
		let bestScore = 0;
		let bestReasons = [];

		for (const [agentId, score] of Object.entries(scores)) {
			if (score.totalScore > bestScore) {
				bestScore = score.totalScore;
				bestAgent = agentId;
				bestReasons = score.reasons;
			}
		}

		// Se nenhum agente atingir o threshold, retornar null
		const threshold = bestAgent ? INTENT_PATTERNS[bestAgent].scoreThreshold : 0;

		if (bestScore < threshold) {
			bestAgent = null;
			bestScore = 0;
			bestReasons = [];
		}

		const result = {
			agentId: bestAgent,
			confidence: Math.round(bestScore * 100),
			reasons: bestReasons,
			allScores: Object.fromEntries(
				Object.entries(scores).map(([id, s]) => [id, Math.round(s.totalScore * 100)])
			)
		};

		// Armazenar no cache
		this.intentCache.set(cacheKey, {
			result,
			timestamp: Date.now()
		});

		// Limpar cache antigo (a cada 100 consultas)
		if (this.cacheHits + (this.cacheMisses % 100) === 0) {
			this.cleanCache();
		}

		logger.debug(
			`[Delegator] Intent detected: ${bestAgent || "none"} (${bestScore * 100}%) for "${query.substring(0, 30)}..."`
		);

		return result;
	}

	/**
	 * Determina se deve delegar para outro agente
	 * @param {string} currentAgent - Agente atualmente ativo
	 * @param {string} detectedAgent - Agente detectado pela análise
	 * @param {number} confidence - Confiança da detecção (0-100)
	 * @param {Object} options - Opções adicionais
	 * @returns {Object} - { shouldDelegate, targetAgent, reason }
	 */
	shouldDelegate(currentAgent, detectedAgent, confidence, options = {}) {
		// Se delegação está desativada
		if (!this.enabled) {
			return {
				shouldDelegate: false,
				targetAgent: currentAgent,
				reason: "Delegation is disabled"
			};
		}

		// Se não detectou nenhum agente
		if (!detectedAgent) {
			return {
				shouldDelegate: false,
				targetAgent: currentAgent,
				reason: "No agent detected"
			};
		}

		// Se o agente detectado é o mesmo que o atual
		if (detectedAgent === currentAgent) {
			return {
				shouldDelegate: false,
				targetAgent: currentAgent,
				reason: "Same agent"
			};
		}

		// Se a confiança é muito baixa
		const minConfidence = options.minConfidence || 60;
		if (confidence < minConfidence) {
			return {
				shouldDelegate: false,
				targetAgent: currentAgent,
				reason: `Confidence too low (${confidence}% < ${minConfidence}%)`
			};
		}

		// Delegar!
		const agent = getAgent(detectedAgent);
		return {
			shouldDelegate: true,
			targetAgent: detectedAgent,
			reason: `Detected ${agent.emoji} ${agent.name} intent with ${confidence}% confidence`
		};
	}

	/**
	 * Executa a delegação e retorna a resposta
	 * @param {Object} params - Parâmetros da delegação
	 * @returns {Promise<Object>} - { response, delegatedFrom, delegatedTo }
	 */
	async delegate(params) {
		const { query, currentAgent, targetAgent, groupId, llmService, context = {} } = params;

		const startTime = Date.now();

		try {
			// Registrar delegação
			this.stats.totalDelegations++;
			this.stats.delegationsByAgent[targetAgent] =
				(this.stats.delegationsByAgent[targetAgent] || 0) + 1;

			const agent = getAgent(targetAgent);
			if (!agent) {
				throw new Error(`Agent "${targetAgent}" not found`);
			}

			logger.info(
				`[Delegator] Delegating from ${currentAgent} to ${targetAgent}: "${query.substring(0, 30)}..."`
			);

			// Montar prompt com contexto de delegação
			const delegationPrompt = this.buildDelegationPrompt({
				query,
				currentAgent,
				targetAgent,
				agent,
				context
			});

			// Chamar o agente alvo
			const response = await llmService.getAnythingLLMCompletion({
				prompt: delegationPrompt,
				workspace: agent.workspace,
				systemContext: agent.systemPrompt,
				timeout: context.timeout || 30000
			});

			const responseTime = Date.now() - startTime;

			logger.info(
				`[Delegator] Delegation completed in ${responseTime}ms (${currentAgent} → ${targetAgent})`
			);

			return {
				response,
				delegatedFrom: currentAgent,
				delegatedTo: targetAgent,
				responseTime,
				confidence: context.confidence
			};
		} catch (error) {
			this.stats.failedDelegations++;

			logger.error(`[Delegator] Delegation failed: ${error.message}`);

			throw error;
		}
	}

	/**
	 * Monta o prompt para delegação
	 * @param {Object} params - Parâmetros
	 * @returns {string} - Prompt formatado
	 */
	buildDelegationPrompt({ query, currentAgent, targetAgent, agent, context }) {
		const agentFrom = getAgent(currentAgent);

		let prompt = `[DELEGATION FROM ${agentFrom.name}]\n\n`;

		prompt += `O usuário fez uma pergunta que foi detectada como sendo do seu domínio de expertise.\n`;
		prompt += `Originalmente, a pergunta foi recebida pelo agente "${agentFrom.name}".\n\n`;

		if (context.groupName) {
			prompt += `Grupo: ${context.groupName}\n`;
		}

		if (context.authorName) {
			prompt += `Usuário: ${context.authorName}\n`;
		}

		prompt += `\n--- PERGUNTA DO USUÁRIO ---\n${query}\n--- FIM DA PERGUNTA ---\n\n`;

		prompt += `Por favor, responda como o especialista em ${agent.name.toLowerCase()}. `;
		prompt += `Mantenha o estilo e a personalidade do agente "${agent.name}".\n`;

		return prompt;
	}

	/**
	 * Limpa entradas antigas do cache
	 */
	cleanCache() {
		const now = Date.now();
		let cleaned = 0;

		for (const [key, value] of this.intentCache.entries()) {
			if (now - value.timestamp > this.CACHE_TTL) {
				this.intentCache.delete(key);
				cleaned++;
			}
		}

		if (cleaned > 0) {
			logger.debug(`[Delegator] Cleaned ${cleaned} cache entries`);
		}
	}

	/**
	 * Obtém estatísticas do delegador
	 * @returns {Object} - Estatísticas
	 */
	getStats() {
		return {
			...this.stats,
			cacheSize: this.intentCache.size,
			cacheHits: this.cacheHits,
			cacheMisses: this.cacheMisses,
			cacheHitRate:
				this.cacheHits + this.cacheMisses > 0
					? Math.round((this.cacheHits / (this.cacheHits + this.cacheMisses)) * 100)
					: 0
		};
	}

	/**
	 * Habilita/desabilita delegação automática
	 * @param {boolean} enabled - Estado
	 */
	setEnabled(enabled) {
		this.enabled = enabled;
		logger.info(`[Delegator] Delegation ${enabled ? "enabled" : "disabled"}`);
	}

	/**
	 * Limpa todo o cache
	 */
	clearCache() {
		this.intentCache.clear();
		logger.debug("[Delegator] Cache cleared");
	}

	/**
	 * Reseta estatísticas
	 */
	resetStats() {
		this.stats = {
			totalDelegations: 0,
			delegationsByAgent: {},
			failedDelegations: 0
		};
		this.cacheHits = 0;
		this.cacheMisses = 0;
		logger.debug("[Delegator] Stats reset");
	}

	/**
	 * Reseta tudo (limpa cache e para timers)
	 */
	resetAll() {
		this.stopCleanupTimer();
		this.clearCache();
		this.resetStats();
		logger.debug("[Delegator] All reset");
	}
}

// Singleton
AgentDelegator.instance = null;

module.exports = AgentDelegator;
