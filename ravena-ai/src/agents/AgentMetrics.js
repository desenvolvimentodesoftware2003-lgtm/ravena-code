/**
 * AgentMetrics.js
 *
 * Sistema de métricas e dashboard para agentes.
 * Coleta, armazena e exibe métricas de desempenho dos agentes.
 *
 * Nível 3 - Dashboard de Métricas
 */

"use strict";

const Logger = require("../utils/Logger");
const { getAgent, listAgents } = require("./AgentConfig");

const logger = new Logger("agent-metrics");

/**
 * Tipos de métricas
 */
const METRIC_TYPES = {
	COUNTER: "counter", // Contador (ex: total de requisições)
	GAUGE: "gauge", // Valor atual (ex: memória usada)
	HISTOGRAM: "histogram", // Distribuição (ex: tempos de resposta)
	RATE: "rate" // Taxa (ex: requisições por minuto)
};

/**
 * Períodos de tempo
 */
const TIME_PERIODS = {
	MINUTE: 60 * 1000,
	HOUR: 60 * 60 * 1000,
	DAY: 24 * 60 * 60 * 1000,
	WEEK: 7 * 24 * 60 * 60 * 1000
};

/**
 * Class for agent metrics
 */
class AgentMetrics {
	constructor() {
		// Métricas por agente: agentId -> { metricName -> value }
		this.agentMetrics = new Map();

		// Métricas globais: metricName -> value
		this.globalMetrics = new Map();

		// Histórico de métricas: [timestamp, agentId, metricName, value]
		this.history = [];

		// Métricas em tempo real (última hora)
		this.realtimeMetrics = new Map();

		// Configurações
		this.config = {
			historyRetention: 7 * 24 * 60 * 60 * 1000, // 7 dias
			maxHistorySize: 10000,
			realtimeWindow: 60 * 60 * 1000, // 1 hora
			enableAggregation: true,
			aggregationInterval: 5 * 60 * 1000 // 5 minutos
		};

		// Estatísticas
		this.stats = {
			totalMetricsCollected: 0,
			totalMetricsAggregated: 0,
			historySize: 0
		};

		// Timer de agregação
		this.aggregationTimer = null;
		this.startAggregationTimer();
	}

	/**
	 * Get singleton instance
	 * @returns {AgentMetrics} - Singleton instance
	 */
	static getInstance() {
		if (!AgentMetrics.instance) {
			AgentMetrics.instance = new AgentMetrics();
		}
		return AgentMetrics.instance;
	}

	/**
	 * Inicia timer de agregação
	 */
	startAggregationTimer() {
		if (this.config.enableAggregation) {
			this.aggregationTimer = setInterval(() => {
				this.aggregateMetrics();
			}, this.config.aggregationInterval);
		}
	}

	/**
	 * Para timer de agregação
	 */
	stopAggregationTimer() {
		if (this.aggregationTimer) {
			clearInterval(this.aggregationTimer);
			this.aggregationTimer = null;
		}
	}

	// ===========================================================================
	// Coleta de Métricas
	// ===========================================================================

	/**
	 * Registra uma métrica
	 * @param {string} agentId - ID do agente
	 * @param {string} metricName - Nome da métrica
	 * @param {number} value - Valor
	 * @param {string} type - Tipo da métrica
	 */
	recordMetric(agentId, metricName, value, type = METRIC_TYPES.COUNTER) {
		const timestamp = Date.now();

		// Inicializar métricas do agente
		if (!this.agentMetrics.has(agentId)) {
			this.agentMetrics.set(agentId, new Map());
		}

		const agentMetrics = this.agentMetrics.get(agentId);

		// Atualizar métrica
		if (!agentMetrics.has(metricName)) {
			agentMetrics.set(metricName, {
				type,
				value: 0,
				min: Infinity,
				max: -Infinity,
				count: 0,
				sum: 0,
				lastUpdated: timestamp
			});
		}

		const metric = agentMetrics.get(metricName);

		// Atualizar valor baseado no tipo
		switch (type) {
			case METRIC_TYPES.COUNTER:
				metric.value += value;
				break;
			case METRIC_TYPES.GAUGE:
				metric.value = value;
				break;
			case METRIC_TYPES.HISTOGRAM:
				metric.value = value;
				metric.min = Math.min(metric.min, value);
				metric.max = Math.max(metric.max, value);
				metric.count++;
				metric.sum += value;
				break;
			case METRIC_TYPES.RATE:
				metric.value = value;
				break;
			default:
				metric.value = value;
		}

		metric.lastUpdated = timestamp;

		// Registrar no histórico
		this.addToHistory(timestamp, agentId, metricName, value, type);

		// Registrar em métricas em tempo real
		this.recordRealtime(agentId, metricName, value, timestamp);

		// Atualizar métricas globais
		this.updateGlobalMetric(metricName, value, type);

		this.stats.totalMetricsCollected++;
	}

	/**
	 * Registra métrica de tempo de resposta
	 * @param {string} agentId - ID do agente
	 * @param {number} responseTime - Tempo de resposta (ms)
	 */
	recordResponseTime(agentId, responseTime) {
		this.recordMetric(agentId, "response_time", responseTime, METRIC_TYPES.HISTOGRAM);
		this.recordMetric(agentId, "total_requests", 1, METRIC_TYPES.COUNTER);
	}

	/**
	 * Registra métrica de erro
	 * @param {string} agentId - ID do agente
	 * @param {string} errorType - Tipo do erro
	 */
	recordError(agentId, errorType = "unknown") {
		this.recordMetric(agentId, "total_errors", 1, METRIC_TYPES.COUNTER);
		this.recordMetric(agentId, `error_${errorType}`, 1, METRIC_TYPES.COUNTER);
	}

	/**
	 * Registra métrica de cache hit/miss
	 * @param {string} agentId - ID do agente
	 * @param {boolean} hit - Se foi hit
	 */
	recordCacheMetric(agentId, hit) {
		const metricName = hit ? "cache_hits" : "cache_misses";
		this.recordMetric(agentId, metricName, 1, METRIC_TYPES.COUNTER);
	}

	/**
	 * Registra métrica de delegação
	 * @param {string} fromAgent - Agente de origem
	 * @param {string} toAgent - Agente de destino
	 */
	recordDelegation(fromAgent, toAgent) {
		this.recordMetric(fromAgent, "delegations_out", 1, METRIC_TYPES.COUNTER);
		this.recordMetric(toAgent, "delegations_in", 1, METRIC_TYPES.COUNTER);
	}

	/**
	 * Registra métrica de memória
	 * @param {string} agentId - ID do agente
	 * @param {string} memoryType - Tipo de memória
	 * @param {number} size - Tamanho
	 */
	recordMemoryUsage(agentId, memoryType, size) {
		this.recordMetric(agentId, `memory_${memoryType}`, size, METRIC_TYPES.GAUGE);
	}

	// ===========================================================================
	// Métricas em Tempo Real
	// ===========================================================================

	/**
	 * Registra métrica em tempo real
	 * @param {string} agentId - ID do agente
	 * @param {string} metricName - Nome da métrica
	 * @param {number} value - Valor
	 * @param {number} timestamp - Timestamp
	 */
	recordRealtime(agentId, metricName, value, timestamp) {
		const key = `${agentId}:${metricName}`;

		if (!this.realtimeMetrics.has(key)) {
			this.realtimeMetrics.set(key, []);
		}

		const metrics = this.realtimeMetrics.get(key);

		metrics.push({ value, timestamp });

		// Manter apenas métricas da última hora
		const cutoff = timestamp - this.config.realtimeWindow;
		const validMetrics = metrics.filter((m) => m.timestamp > cutoff);

		this.realtimeMetrics.set(key, validMetrics);
	}

	/**
	 * Obtém métricas em tempo real
	 * @param {string} agentId - ID do agente
	 * @param {string} metricName - Nome da métrica
	 * @param {number} window - Janela de tempo (ms)
	 * @returns {Object} - Métricas agregadas
	 */
	getRealtimeMetrics(agentId, metricName, window = this.config.realtimeWindow) {
		const key = `${agentId}:${metricName}`;
		const metrics = this.realtimeMetrics.get(key) || [];

		const now = Date.now();
		const cutoff = now - window;

		const recentMetrics = metrics.filter((m) => m.timestamp > cutoff);

		if (recentMetrics.length === 0) {
			return {
				count: 0,
				sum: 0,
				avg: 0,
				min: 0,
				max: 0,
				rate: 0
			};
		}

		const values = recentMetrics.map((m) => m.value);
		const sum = values.reduce((a, b) => a + b, 0);

		return {
			count: values.length,
			sum,
			avg: sum / values.length,
			min: Math.min(...values),
			max: Math.max(...values),
			rate: values.length / (window / 1000) // Por segundo
		};
	}

	// ===========================================================================
	// Histórico
	// ===========================================================================

	/**
	 * Adiciona entrada ao histórico
	 * @param {number} timestamp - Timestamp
	 * @param {string} agentId - ID do agente
	 * @param {string} metricName - Nome da métrica
	 * @param {number} value - Valor
	 * @param {string} type - Tipo
	 */
	addToHistory(timestamp, agentId, metricName, value, type) {
		this.history.push({
			timestamp,
			agentId,
			metricName,
			value,
			type
		});

		// Limitar tamanho do histórico
		if (this.history.length > this.config.maxHistorySize) {
			const toRemove = this.history.splice(0, this.history.length - this.config.maxHistorySize);
			this.stats.historySize -= toRemove.length;
		}

		this.stats.historySize++;
	}

	/**
	 * Obtém histórico de métricas
	 * @param {Object} filters - Filtros
	 * @returns {Array} - Histórico filtrado
	 */
	getHistory(filters = {}) {
		const { agentId, metricName, startTime, endTime, limit = 100 } = filters;

		let history = [...this.history];

		// Aplicar filtros
		if (agentId) {
			history = history.filter((h) => h.agentId === agentId);
		}

		if (metricName) {
			history = history.filter((h) => h.metricName === metricName);
		}

		if (startTime) {
			history = history.filter((h) => h.timestamp >= startTime);
		}

		if (endTime) {
			history = history.filter((h) => h.timestamp <= endTime);
		}

		// Ordenar por timestamp
		history.sort((a, b) => b.timestamp - a.timestamp);

		return history.slice(0, limit);
	}

	// ===========================================================================
	// Agregação
	// ===========================================================================

	/**
	 * Agrega métricas antigas
	 */
	aggregateMetrics() {
		const now = Date.now();
		const cutoff = now - this.config.historyRetention;

		// Remover métricas antigas do histórico
		const beforeSize = this.history.length;
		this.history = this.history.filter((h) => h.timestamp > cutoff);

		const removed = beforeSize - this.history.length;
		if (removed > 0) {
			this.stats.historySize -= removed;
			logger.debug(`[aggregateMetrics] Removed ${removed} old metrics`);
		}

		// Agregar métricas em tempo real
		for (const [key, metrics] of this.realtimeMetrics.entries()) {
			const validMetrics = metrics.filter((m) => m.timestamp > cutoff);
			this.realtimeMetrics.set(key, validMetrics);
		}

		this.stats.totalMetricsAggregated++;
	}

	// ===========================================================================
	// Métricas Globais
	// ===========================================================================

	/**
	 * Atualiza métrica global
	 * @param {string} metricName - Nome da métrica
	 * @param {number} value - Valor
	 * @param {string} type - Tipo
	 */
	updateGlobalMetric(metricName, value, type) {
		if (!this.globalMetrics.has(metricName)) {
			this.globalMetrics.set(metricName, {
				type,
				value: 0,
				count: 0,
				sum: 0,
				min: Infinity,
				max: -Infinity
			});
		}

		const metric = this.globalMetrics.get(metricName);

		switch (type) {
			case METRIC_TYPES.COUNTER:
				metric.value += value;
				break;
			case METRIC_TYPES.GAUGE:
				metric.value = value;
				break;
			case METRIC_TYPES.HISTOGRAM:
				metric.min = Math.min(metric.min, value);
				metric.max = Math.max(metric.max, value);
				metric.count++;
				metric.sum += value;
				metric.value = metric.sum / metric.count;
				break;
			default:
				metric.value = value;
		}
	}

	/**
	 * Obtém métricas globais
	 * @returns {Object} - Métricas globais
	 */
	getGlobalMetrics() {
		const metrics = {};

		for (const [name, metric] of this.globalMetrics.entries()) {
			metrics[name] = {
				...metric,
				avg: metric.count > 0 ? metric.sum / metric.count : 0
			};
		}

		return metrics;
	}

	// ===========================================================================
	// Consultas e Relatórios
	// ===========================================================================

	/**
	 * Obtém métricas de um agente
	 * @param {string} agentId - ID do agente
	 * @returns {Object} - Métricas do agente
	 */
	getAgentMetrics(agentId) {
		const agentMetrics = this.agentMetrics.get(agentId);
		if (!agentMetrics) {
			return {};
		}

		const metrics = {};

		for (const [name, metric] of agentMetrics.entries()) {
			metrics[name] = {
				...metric,
				avg: metric.count > 0 ? metric.sum / metric.count : 0
			};
		}

		return metrics;
	}

	/**
	 * Obtém relatório de desempenho de um agente
	 * @param {string} agentId - ID do agente
	 * @returns {Object} - Relatório
	 */
	getAgentPerformanceReport(agentId) {
		const agent = getAgent(agentId);
		const metrics = this.getAgentMetrics(agentId);
		const realtime = {
			responseTime: this.getRealtimeMetrics(agentId, "response_time"),
			totalRequests: this.getRealtimeMetrics(agentId, "total_requests")
		};

		const responseTime = metrics.response_time || { count: 0, avg: 0, min: 0, max: 0 };
		const totalRequests = metrics.total_requests?.value || 0;
		const totalErrors = metrics.total_errors?.value || 0;
		const cacheHits = metrics.cache_hits?.value || 0;
		const cacheMisses = metrics.cache_misses?.value || 0;

		return {
			agentId,
			agentName: agent ? agent.name : agentId,
			agentEmoji: agent ? agent.emoji : "❓",

			// Métricas acumuladas
			totalRequests,
			totalErrors,
			errorRate: totalRequests > 0 ? (totalErrors / totalRequests) * 100 : 0,

			// Tempo de resposta
			avgResponseTime: Math.round(responseTime.avg),
			minResponseTime: responseTime.min === Infinity ? 0 : Math.round(responseTime.min),
			maxResponseTime: responseTime.max === -Infinity ? 0 : Math.round(responseTime.max),

			// Cache
			cacheHitRate:
				cacheHits + cacheMisses > 0 ? Math.round((cacheHits / (cacheHits + cacheMisses)) * 100) : 0,

			// Métricas em tempo real
			realtime,

			// Timestamp
			generatedAt: Date.now()
		};
	}

	/**
	 * Obtém relatório geral do sistema
	 * @returns {Object} - Relatório
	 */
	getSystemReport() {
		const agents = listAgents();
		const agentReports = {};

		for (const agent of agents) {
			agentReports[agent.id] = this.getAgentPerformanceReport(agent.id);
		}

		// Calcular totais
		let totalRequests = 0;
		let totalErrors = 0;
		let totalResponseTime = 0;
		let responseTimeCount = 0;

		for (const report of Object.values(agentReports)) {
			totalRequests += report.totalRequests;
			totalErrors += report.totalErrors;

			if (report.avgResponseTime > 0) {
				totalResponseTime += report.avgResponseTime * report.totalRequests;
				responseTimeCount += report.totalRequests;
			}
		}

		return {
			summary: {
				totalRequests,
				totalErrors,
				errorRate: totalRequests > 0 ? (totalErrors / totalRequests) * 100 : 0,
				avgResponseTime:
					responseTimeCount > 0 ? Math.round(totalResponseTime / responseTimeCount) : 0,
				activeAgents: agents.length
			},
			agents: agentReports,
			global: this.getGlobalMetrics(),
			memory: {
				historySize: this.history.size,
				realtimeSize: this.realtimeMetrics.size
			},
			generatedAt: Date.now()
		};
	}

	/**
	 * Obtém dashboard formatado
	 * @returns {string} - Dashboard em texto
	 */
	getDashboard() {
		const report = this.getSystemReport();

		let dashboard = "📊 *Dashboard de Métricas - Agentes*\n\n";

		// Resumo
		dashboard += `📈 *Resumo Geral*\n`;
		dashboard += `   Total de requisições: ${report.summary.totalRequests}\n`;
		dashboard += `   Total de erros: ${report.summary.totalErrors}\n`;
		dashboard += `   Taxa de erro: ${report.summary.errorRate.toFixed(1)}%\n`;
		dashboard += `   Tempo médio de resposta: ${report.summary.avgResponseTime}ms\n`;
		dashboard += `   Agentes ativos: ${report.summary.activeAgents}\n\n`;

		// Por agente
		dashboard += `*Desempenho por Agente:*\n`;

		for (const [agentId, agentReport] of Object.entries(report.agents)) {
			if (agentReport.totalRequests > 0) {
				dashboard += `\n${agentReport.agentEmoji} *${agentReport.agentName}*\n`;
				dashboard += `   Requisições: ${agentReport.totalRequests}\n`;
				dashboard += `   Erros: ${agentReport.totalErrors} (${agentReport.errorRate.toFixed(1)}%)\n`;
				dashboard += `   Tempo médio: ${agentReport.avgResponseTime}ms\n`;
				dashboard += `   Cache hit rate: ${agentReport.cacheHitRate}%\n`;
			}
		}

		// Métricas em tempo real
		dashboard += `\n⚡ *Métricas em Tempo Real (última hora):*\n`;

		for (const agent of listAgents()) {
			const realtime = report.agents[agent.id]?.realtime;
			if (realtime && realtime.totalRequests.count > 0) {
				dashboard += `${agent.emoji} *${agent.name}:* ${realtime.totalRequests.count} req/min\n`;
			}
		}

		dashboard += `\n_Gerado em: ${new Date(report.generatedAt).toLocaleString("pt-BR")}_`;

		return dashboard;
	}

	// ===========================================================================
	// Limpeza e Manutenção
	// ===========================================================================

	/**
	 * Limpa métricas antigas
	 */
	cleanup() {
		const now = Date.now();
		const cutoff = now - this.config.historyRetention;

		// Limpar histórico
		const beforeSize = this.history.length;
		this.history = this.history.filter((h) => h.timestamp > cutoff);

		const removed = beforeSize - this.history.length;
		if (removed > 0) {
			logger.debug(`[cleanup] Removed ${removed} old metrics from history`);
		}

		// Limpar métricas em tempo real
		for (const [key, metrics] of this.realtimeMetrics.entries()) {
			const validMetrics = metrics.filter((m) => m.timestamp > cutoff);

			if (validMetrics.length === 0) {
				this.realtimeMetrics.delete(key);
			} else {
				this.realtimeMetrics.set(key, validMetrics);
			}
		}
	}

	/**
	 * Reseta todas as métricas
	 */
	resetAll() {
		this.agentMetrics.clear();
		this.globalMetrics.clear();
		this.history = [];
		this.realtimeMetrics.clear();

		this.stats = {
			totalMetricsCollected: 0,
			totalMetricsAggregated: 0,
			historySize: 0
		};

		logger.info("[resetAll] All metrics reset");
	}

	/**
	 * Obtém estatísticas do módulo
	 * @returns {Object} - Estatísticas
	 */
	getStats() {
		return {
			...this.stats,
			agentMetricsSize: this.agentMetrics.size,
			globalMetricsSize: this.globalMetrics.size,
			realtimeMetricsSize: this.realtimeMetrics.size
		};
	}
}

// Singleton
AgentMetrics.instance = null;

module.exports = AgentMetrics;
