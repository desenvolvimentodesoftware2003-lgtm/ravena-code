/**
 * AgentLearning.js
 *
 * Sistema de aprendizado para agentes.
 * Permite que agentes aprendam com interações anteriores,
 * identifiquem padrões e melhorem suas respostas.
 *
 * Nível 4 - Aprendizado
 */

"use strict";

const Logger = require("../utils/Logger");
const { getAgent } = require("./AgentConfig");

const logger = new Logger("agent-learning");

/**
 * Tipos de aprendizado
 */
const LEARNING_TYPES = {
	PATTERN: "pattern", // Padrões identificados
	PREFERENCE: "preference", // Preferências do usuário
	CORRECTION: "correction", // Correções de erros
	FEEDBACK: "feedback", // Feedback do usuário
	CONTEXTUAL: "contextual", // Informações contextuais
	BEHAVIORAL: "behavioral", // Padrões de comportamento
	KNOWLEDGE: "knowledge", // Novos conhecimentos
	OPTIMIZATION: "optimization", // Otimizações de performance
	SEQUENCE: "sequence", // Sequências de ações
	ASSOCIATION: "association" // Associações entre conceitos
};

/**
 * Class for agent learning
 */
class AgentLearning {
	constructor() {
		// Padrões aprendidos: agentId -> [patterns]
		this.patterns = new Map();

		// Preferências: agentId:userId -> { preferences }
		this.preferences = new Map();

		// Correções: agentId -> [corrections]
		this.corrections = new Map();

		// Feedback: agentId -> [feedback]
		this.feedback = new Map();

		// Conhecimento acumulado: agentId -> [knowledge]
		this.knowledge = new Map();

		// Associações: agentId -> { concept -> associations }
		this.associations = new Map();

		// Configurações
		this.config = {
			maxPatternsPerAgent: 100,
			maxPreferencesPerUser: 50,
			maxCorrectionsPerAgent: 200,
			maxFeedbackPerAgent: 500,
			maxKnowledgePerAgent: 1000,
			minConfidenceForPattern: 0.7,
			learningRate: 0.1,
			decayFactor: 0.95,
			enableAutoLearning: true
		};

		// Estatísticas
		this.stats = {
			totalLearnings: 0,
			patternsIdentified: 0,
			preferencesLearned: 0,
			correctionsApplied: 0,
			feedbackProcessed: 0,
			knowledgeAcquired: 0,
			byAgent: {},
			byType: {}
		};

		// Timer para limpeza periódica (a cada 10 minutos)
		this.cleanupInterval = null;
		this.startCleanupTimer();
	}

	/**
	 * Get singleton instance
	 * @returns {AgentLearning} - Singleton instance
	 */
	static getInstance() {
		if (!AgentLearning.instance) {
			AgentLearning.instance = new AgentLearning();
		}
		return AgentLearning.instance;
	}

	/**
	 * Inicia timer de limpeza periódica
	 */
	startCleanupTimer() {
		// Limpar a cada 10 minutos
		this.cleanupInterval = setInterval(
			() => {
				this.cleanup();
			},
			10 * 60 * 1000
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
	// Aprendizado de Padrões
	// ===========================================================================

	/**
	 * Registra um padrão identificado
	 * @param {string} agentId - ID do agente
	 * @param {Object} pattern - Dados do padrão
	 */
	learnPattern(agentId, pattern) {
		if (!this.patterns.has(agentId)) {
			this.patterns.set(agentId, []);
		}

		const patterns = this.patterns.get(agentId);

		// Verificar se padrão já existe
		const existingIndex = patterns.findIndex(
			(p) => p.type === pattern.type && p.signature === pattern.signature
		);

		if (existingIndex >= 0) {
			// Atualizar confiança
			patterns[existingIndex].confidence = Math.min(
				1,
				patterns[existingIndex].confidence + this.config.learningRate
			);
			patterns[existingIndex].occurrences++;
			patterns[existingIndex].lastSeen = Date.now();
		} else {
			// Novo padrão
			patterns.push({
				...pattern,
				id: `pattern-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`,
				confidence: 0.5,
				occurrences: 1,
				createdAt: Date.now(),
				lastSeen: Date.now()
			});
		}

		// Limitar tamanho
		if (patterns.length > this.config.maxPatternsPerAgent) {
			// Ordenar por confiança e occurrences
			patterns.sort((a, b) => {
				if (b.confidence !== a.confidence) {
					return b.confidence - a.confidence;
				}
				return b.occurrences - a.occurrences;
			});

			patterns.splice(this.config.maxPatternsPerAgent);
		}

		this.stats.totalLearnings++;
		this.stats.patternsIdentified++;

		this.updateAgentStats(agentId, LEARNING_TYPES.PATTERN);
	}

	/**
	 * Obtém padrões relevantes para um contexto
	 * @param {string} agentId - ID do agente
	 * @param {Object} context - Contexto
	 * @returns {Array} - Padrões relevantes
	 */
	getRelevantPatterns(agentId, context = {}) {
		const patterns = this.patterns.get(agentId) || [];

		// Filtrar por confiança mínima
		const confidentPatterns = patterns.filter(
			(p) => p.confidence >= this.config.minConfidenceForPattern
		);

		// Ordenar por relevância
		return confidentPatterns
			.sort((a, b) => {
				// Calcular relevância baseada no contexto
				const relevanceA = this.calculatePatternRelevance(a, context);
				const relevanceB = this.calculatePatternRelevance(b, context);
				return relevanceB - relevanceA;
			})
			.slice(0, 10);
	}

	/**
	 * Calcula relevância de um padrão
	 * @param {Object} pattern - Padrão
	 * @param {Object} context - Contexto
	 * @returns {number} - Score de relevância
	 */
	calculatePatternRelevance(pattern, context) {
		let score = pattern.confidence;

		// Bonus por recência
		const age = Date.now() - pattern.lastSeen;
		const recencyBonus = Math.max(0, 1 - age / (7 * 24 * 60 * 60 * 1000));
		score += recencyBonus * 0.2;

		// Bonus por ocorrências
		const occurrenceBonus = Math.min(1, pattern.occurrences / 10);
		score += occurrenceBonus * 0.1;

		// Bonus por contexto
		if (context.keywords && pattern.keywords) {
			const overlap = context.keywords.filter((k) => pattern.keywords.includes(k)).length;
			score += (overlap / pattern.keywords.length) * 0.3;
		}

		return score;
	}

	// ===========================================================================
	// Aprendizado de Preferências
	// ===========================================================================

	/**
	 * Aprende preferência do usuário
	 * @param {string} agentId - ID do agente
	 * @param {string} userId - ID do usuário
	 * @param {string} key - Chave da preferência
	 * @param {any} value - Valor
	 */
	learnPreference(agentId, userId, key, value) {
		const prefKey = `${agentId}:${userId}`;

		if (!this.preferences.has(prefKey)) {
			this.preferences.set(prefKey, {});
		}

		const userPrefs = this.preferences.get(prefKey);

		// Atualizar preferência
		const oldValue = userPrefs[key];
		userPrefs[key] = {
			value,
			confidence: 0.5,
			occurrences: (oldValue?.occurrences || 0) + 1,
			updatedAt: Date.now()
		};

		// Aumentar confiança com mais ocorrências
		if (userPrefs[key].occurrences > 3) {
			userPrefs[key].confidence = Math.min(1, userPrefs[key].confidence + this.config.learningRate);
		}

		this.stats.totalLearnings++;
		this.stats.preferencesLearned++;

		this.updateAgentStats(agentId, LEARNING_TYPES.PREFERENCE);
	}

	/**
	 * Obtém preferências do usuário
	 * @param {string} agentId - ID do agente
	 * @param {string} userId - ID do usuário
	 * @returns {Object} - Preferências
	 */
	getUserPreferences(agentId, userId) {
		const prefKey = `${agentId}:${userId}`;
		const userPrefs = this.preferences.get(prefKey) || {};

		// Filtrar apenas preferências com confiança alta
		const confidentPrefs = {};

		for (const [key, pref] of Object.entries(userPrefs)) {
			if (pref.confidence >= 0.5) {
				confidentPrefs[key] = pref.value;
			}
		}

		return confidentPrefs;
	}

	// ===========================================================================
	// Aprendizado de Correções
	// ===========================================================================

	/**
	 * Registra correção de erro
	 * @param {string} agentId - ID do agente
	 * @param {Object} correction - Dados da correção
	 */
	learnCorrection(agentId, correction) {
		if (!this.corrections.has(agentId)) {
			this.corrections.set(agentId, []);
		}

		const corrections = this.corrections.get(agentId);

		corrections.push({
			...correction,
			id: `correction-${Date.now()}`,
			timestamp: Date.now(),
			applied: false
		});

		// Limitar tamanho
		if (corrections.length > this.config.maxCorrectionsPerAgent) {
			corrections.splice(0, corrections.length - this.config.maxCorrectionsPerAgent);
		}

		this.stats.totalLearnings++;
		this.stats.correctionsApplied++;

		this.updateAgentStats(agentId, LEARNING_TYPES.CORRECTION);
	}

	/**
	 * Obtém correções relevantes
	 * @param {string} agentId - ID do agente
	 * @param {Object} context - Contexto
	 * @returns {Array} - Correções relevantes
	 */
	getRelevantCorrections(agentId, context = {}) {
		const corrections = this.corrections.get(agentId) || [];

		// Filtrar por relevância
		return corrections
			.filter((c) => {
				// Verificar se é relevante para o contexto atual
				if (context.topic && c.topic === context.topic) {
					return true;
				}
				if (context.keywords && c.keywords) {
					return c.keywords.some((k) => context.keywords.includes(k));
				}
				return false;
			})
			.sort((a, b) => b.timestamp - a.timestamp)
			.slice(0, 5);
	}

	// ===========================================================================
	// Aprendizado de Feedback
	// ===========================================================================

	/**
	 * Processa feedback do usuário
	 * @param {string} agentId - ID do agente
	 * @param {Object} feedback - Dados do feedback
	 */
	learnFeedback(agentId, feedback) {
		if (!this.feedback.has(agentId)) {
			this.feedback.set(agentId, []);
		}

		const feedbackList = this.feedback.get(agentId);

		feedbackList.push({
			...feedback,
			id: `feedback-${Date.now()}`,
			timestamp: Date.now()
		});

		// Limitar tamanho
		if (feedbackList.length > this.config.maxFeedbackPerAgent) {
			feedbackList.splice(0, feedbackList.length - this.config.maxFeedbackPerAgent);
		}

		// Aprender com o feedback
		this.processFeedback(agentId, feedback);

		this.stats.totalLearnings++;
		this.stats.feedbackProcessed++;

		this.updateAgentStats(agentId, LEARNING_TYPES.FEEDBACK);
	}

	/**
	 * Processa feedback para aprendizado
	 * @param {string} agentId - ID do agente
	 * @param {Object} feedback - Dados do feedback
	 */
	processFeedback(agentId, feedback) {
		// Se feedback negativo, registrar correção
		if (feedback.rating < 3) {
			this.learnCorrection(agentId, {
				type: "negative-feedback",
				content: feedback.comment || "Negative feedback",
				topic: feedback.topic,
				keywords: feedback.keywords
			});
		}

		// Se feedback positivo, reforçar padrão
		if (feedback.rating >= 4) {
			this.learnPattern(agentId, {
				type: "positive-interaction",
				signature: feedback.patternSignature,
				keywords: feedback.keywords,
				context: feedback.context
			});
		}
	}

	// ===========================================================================
	// Conhecimento Acumulado
	// ===========================================================================

	/**
	 * Adiciona conhecimento
	 * @param {string} agentId - ID do agente
	 * @param {Object} knowledge - Dados do conhecimento
	 */
	learnKnowledge(agentId, knowledge) {
		if (!this.knowledge.has(agentId)) {
			this.knowledge.set(agentId, []);
		}

		const knowledgeList = this.knowledge.get(agentId);

		// Verificar se conhecimento já existe
		const existingIndex = knowledgeList.findIndex(
			(k) => k.type === knowledge.type && k.signature === knowledge.signature
		);

		if (existingIndex >= 0) {
			// Atualizar existente
			knowledgeList[existingIndex].confidence = Math.min(
				1,
				knowledgeList[existingIndex].confidence + this.config.learningRate
			);
			knowledgeList[existingIndex].occurrences++;
			knowledgeList[existingIndex].lastSeen = Date.now();
		} else {
			// Novo conhecimento
			knowledgeList.push({
				...knowledge,
				id: `knowledge-${Date.now()}`,
				confidence: 0.3,
				occurrences: 1,
				createdAt: Date.now(),
				lastSeen: Date.now()
			});
		}

		// Limitar tamanho
		if (knowledgeList.length > this.config.maxKnowledgePerAgent) {
			// Ordenar por confiança
			knowledgeList.sort((a, b) => b.confidence - a.confidence);
			knowledgeList.splice(this.config.maxKnowledgePerAgent);
		}

		this.stats.totalLearnings++;
		this.stats.knowledgeAcquired++;

		this.updateAgentStats(agentId, LEARNING_TYPES.KNOWLEDGE);
	}

	/**
	 * Obtém conhecimento relevante
	 * @param {string} agentId - ID do agente
	 * @param {Object} query - Consulta
	 * @returns {Array} - Conhecimento relevante
	 */
	getRelevantKnowledge(agentId, query = {}) {
		const knowledge = this.knowledge.get(agentId) || [];

		return knowledge
			.filter((k) => {
				// Filtrar por relevância
				if (query.topic && k.topic === query.topic) {
					return true;
				}
				if (query.keywords && k.keywords) {
					return k.keywords.some((kw) => query.keywords.includes(kw));
				}
				return k.confidence >= 0.5;
			})
			.sort((a, b) => {
				// Ordenar por confiança e relevância
				if (b.confidence !== a.confidence) {
					return b.confidence - a.confidence;
				}
				return b.occurrences - a.occurrences;
			})
			.slice(0, 10);
	}

	// ===========================================================================
	// Associações
	// ===========================================================================

	/**
	 * Registra associação entre conceitos
	 * @param {string} agentId - ID do agente
	 * @param {string} concept - Conceito principal
	 * @param {string} association - Conceito associado
	 * @param {number} strength - Força da associação
	 */
	learnAssociation(agentId, concept, association, strength = 0.5) {
		if (!this.associations.has(agentId)) {
			this.associations.set(agentId, new Map());
		}

		const agentAssociations = this.associations.get(agentId);

		if (!agentAssociations.has(concept)) {
			agentAssociations.set(concept, new Map());
		}

		const conceptAssociations = agentAssociations.get(concept);

		// Atualizar força da associação
		const currentStrength = conceptAssociations.get(association) || 0;
		const newStrength = currentStrength + strength * this.config.learningRate;

		conceptAssociations.set(association, Math.min(1, newStrength));
	}

	/**
	 * Obtém associações de um conceito
	 * @param {string} agentId - ID do agente
	 * @param {string} concept - Conceito
	 * @param {number} minStrength - Força mínima
	 * @returns {Array} - Associações
	 */
	getAssociations(agentId, concept, minStrength = 0.3) {
		const agentAssociations = this.associations.get(agentId);
		if (!agentAssociations) {
			return [];
		}

		const conceptAssociations = agentAssociations.get(concept);
		if (!conceptAssociations) {
			return [];
		}

		const associations = [];

		for (const [assoc, strength] of conceptAssociations.entries()) {
			if (strength >= minStrength) {
				associations.push({ concept: assoc, strength });
			}
		}

		return associations.sort((a, b) => b.strength - a.strength);
	}

	// ===========================================================================
	// Construção de Contexto Enriquecido
	// ===========================================================================

	/**
	 * Constrói contexto enriquecido com aprendizados
	 * @param {string} agentId - ID do agente
	 * @param {Object} baseContext - Contexto base
	 * @returns {Object} - Contexto enriquecido
	 */
	buildEnrichedContext(agentId, baseContext = {}) {
		// Obter aprendizados relevantes
		const patterns = this.getRelevantPatterns(agentId, baseContext);
		const knowledge = this.getRelevantKnowledge(agentId, baseContext);
		const corrections = this.getRelevantCorrections(agentId, baseContext);

		// Obter preferências do usuário
		let userPreferences = {};
		if (baseContext.userId) {
			userPreferences = this.getUserPreferences(agentId, baseContext.userId);
		}

		// Montar contexto enriquecido
		const enrichedContext = {
			...baseContext,
			learnings: {
				patterns: patterns.map((p) => ({
					type: p.type,
					signature: p.signature,
					confidence: p.confidence
				})),
				knowledge: knowledge.map((k) => ({
					type: k.type,
					content: k.content,
					confidence: k.confidence
				})),
				corrections: corrections.map((c) => ({
					type: c.type,
					content: c.content,
					topic: c.topic
				})),
				preferences: userPreferences
			}
		};

		return enrichedContext;
	}

	/**
	 * Gera prompt com aprendizados
	 * @param {string} agentId - ID do agente
	 * @param {Object} context - Contexto
	 * @returns {string} - Prompt enriquecido
	 */
	buildPromptWithLearnings(agentId, context = {}) {
		const enrichedContext = this.buildEnrichedContext(agentId, context);

		let prompt = "";

		// Adicionar preferências do usuário
		if (Object.keys(enrichedContext.learnings.preferences).length > 0) {
			prompt += "Preferências do usuário:\n";
			for (const [key, value] of Object.entries(enrichedContext.learnings.preferences)) {
				prompt += `- ${key}: ${value}\n`;
			}
			prompt += "\n";
		}

		// Adicionar conhecimento relevante
		if (enrichedContext.learnings.knowledge.length > 0) {
			prompt += "Conhecimento relevante:\n";
			for (const k of enrichedContext.learnings.knowledge.slice(0, 3)) {
				prompt += `- ${k.content}\n`;
			}
			prompt += "\n";
		}

		// Adicionar correções a evitar
		if (enrichedContext.learnings.corrections.length > 0) {
			prompt += "Evitar erros anteriores:\n";
			for (const c of enrichedContext.learnings.corrections.slice(0, 2)) {
				prompt += `- ${c.content}\n`;
			}
			prompt += "\n";
		}

		// Adicionar padrões identificados
		if (enrichedContext.learnings.patterns.length > 0) {
			prompt += "Padrões identificados:\n";
			for (const p of enrichedContext.learnings.patterns.slice(0, 3)) {
				prompt += `- ${p.type}: ${p.signature}\n`;
			}
			prompt += "\n";
		}

		return prompt;
	}

	// ===========================================================================
	// Utilitários
	// ===========================================================================

	/**
	 * Atualiza estatísticas do agente
	 * @param {string} agentId - ID do agente
	 * @param {string} type - Tipo de aprendizado
	 */
	updateAgentStats(agentId, type) {
		if (!this.stats.byAgent[agentId]) {
			this.stats.byAgent[agentId] = {};
		}

		if (!this.stats.byAgent[agentId][type]) {
			this.stats.byAgent[agentId][type] = 0;
		}

		this.stats.byAgent[agentId][type]++;

		if (!this.stats.byType[type]) {
			this.stats.byType[type] = 0;
		}

		this.stats.byType[type]++;
	}

	/**
	 * Obtém estatísticas
	 * @returns {Object} - Estatísticas
	 */
	getStats() {
		return {
			...this.stats,
			patternsSize: Array.from(this.patterns.values()).reduce((sum, p) => sum + p.length, 0),
			preferencesSize: this.preferences.size,
			correctionsSize: Array.from(this.corrections.values()).reduce((sum, c) => sum + c.length, 0),
			feedbackSize: Array.from(this.feedback.values()).reduce((sum, f) => sum + f.length, 0),
			knowledgeSize: Array.from(this.knowledge.values()).reduce((sum, k) => sum + k.length, 0)
		};
	}

	/**
	 * Limpa dados antigos
	 */
	cleanup() {
		const now = Date.now();
		const maxAge = 30 * 24 * 60 * 60 * 1000; // 30 dias

		// Limpar padrões antigos
		for (const [agentId, patterns] of this.patterns.entries()) {
			const validPatterns = patterns.filter((p) => now - p.lastSeen < maxAge);
			this.patterns.set(agentId, validPatterns);
		}

		// Limpar correções antigas
		for (const [agentId, corrections] of this.corrections.entries()) {
			const validCorrections = corrections.filter((c) => now - c.timestamp < maxAge);
			this.corrections.set(agentId, validCorrections);
		}

		// Limpar feedback antigo
		for (const [agentId, feedbackList] of this.feedback.entries()) {
			const validFeedback = feedbackList.filter((f) => now - f.timestamp < maxAge);
			this.feedback.set(agentId, validFeedback);
		}

		// Limpar conhecimento antigo
		for (const [agentId, knowledgeList] of this.knowledge.entries()) {
			const validKnowledge = knowledgeList.filter(
				(k) => now - (k.lastSeen || k.createdAt) < maxAge
			);
			this.knowledge.set(agentId, validKnowledge);
		}

		// Limpar preferências antigas (mais de 90 dias)
		const prefMaxAge = 90 * 24 * 60 * 60 * 1000;
		for (const [prefKey, prefs] of this.preferences.entries()) {
			const validPrefs = {};
			for (const [key, pref] of Object.entries(prefs)) {
				if (now - pref.updatedAt < prefMaxAge) {
					validPrefs[key] = pref;
				}
			}
			if (Object.keys(validPrefs).length === 0) {
				this.preferences.delete(prefKey);
			} else {
				this.preferences.set(prefKey, validPrefs);
			}
		}

		logger.debug("[cleanup] Old learning data cleaned");
	}

	/**
	 * Reseta todos os dados de aprendizado
	 */
	resetAll() {
		this.stopCleanupTimer();
		this.patterns.clear();
		this.preferences.clear();
		this.corrections.clear();
		this.feedback.clear();
		this.knowledge.clear();
		this.associations.clear();

		this.stats = {
			totalLearnings: 0,
			patternsIdentified: 0,
			preferencesLearned: 0,
			correctionsApplied: 0,
			feedbackProcessed: 0,
			knowledgeAcquired: 0,
			byAgent: {},
			byType: {}
		};

		logger.info("[resetAll] All learning data reset");
	}
}

// Singleton
AgentLearning.instance = null;

module.exports = AgentLearning;
