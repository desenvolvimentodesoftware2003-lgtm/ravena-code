/**
 * AgentAutonomy.js
 *
 * Sistema de IA autônoma para agentes.
 * Permite que agentes tomem ações independentes,
 * como criar tarefas, agendar eventos e executar workflows.
 *
 * Nível 4 - IA Autônoma
 */

"use strict";

const Logger = require("../utils/Logger");
const { getAgent } = require("./AgentConfig");

const logger = new Logger("agent-autonomy");

/**
 * Tipos de ação autônoma
 */
const ACTION_TYPES = {
	TASK_CREATE: "task-create",
	TASK_UPDATE: "task-update",
	TASK_COMPLETE: "task-complete",
	SCHEDULE_EVENT: "schedule-event",
	CANCEL_EVENT: "cancel-event",
	SEND_NOTIFICATION: "send-notification",
	EXECUTE_WORKFLOW: "execute-workflow",
	CALL_EXTERNAL_API: "call-external-api",
	MODIFY_DATA: "modify-data",
	REQUEST_APPROVAL: "request-approval"
};

/**
 * Status de ação
 */
const ACTION_STATUS = {
	PENDING: "pending",
	APPROVED: "approved",
	REJECTED: "rejected",
	IN_PROGRESS: "in-progress",
	COMPLETED: "completed",
	FAILED: "failed",
	CANCELLED: "cancelled"
};

/**
 * Níveis de autonomia
 */
const AUTONOMY_LEVELS = {
	NONE: 0, // Sem autonomia - sempre precisa de aprovação
	LOW: 1, // Baixa - apenas ações de leitura
	MEDIUM: 2, // Média - ações de escrita simples
	HIGH: 3, // Alta - ações complexas
	FULL: 4 // Total - controle total (perigoso!)
};

/**
 * Class for agent autonomy
 */
class AgentAutonomy {
	constructor() {
		// Níveis de autonomia por agente
		this.autonomyLevels = new Map();

		// Ações pendentes de aprovação
		this.pendingActions = new Map();

		// Histórico de ações
		this.actionHistory = [];

		// Ações agendadas
		this.scheduledActions = new Map();

		// Configurações
		this.config = {
			maxPendingActions: 50,
			actionHistoryRetention: 30 * 24 * 60 * 60 * 1000, // 30 dias
			maxActionsPerHour: 20,
			requireApprovalAbove: AUTONOMY_LEVELS.MEDIUM,
			enableAutoApproval: false,
			autoApprovalRules: []
		};

		// Estatísticas
		this.stats = {
			totalActions: 0,
			approvedActions: 0,
			rejectedActions: 0,
			failedActions: 0,
			autoApprovedActions: 0,
			pendingActions: 0,
			byAgent: {},
			byType: {}
		};

		// Timer para processar ações agendadas
		this.schedulerTimer = null;
		this.startScheduler();
	}

	/**
	 * Get singleton instance
	 * @returns {AgentAutonomy} - Singleton instance
	 */
	static getInstance() {
		if (!AgentAutonomy.instance) {
			AgentAutonomy.instance = new AgentAutonomy();
		}
		return AgentAutonomy.instance;
	}

	/**
	 * Inicia scheduler de ações agendadas
	 */
	startScheduler() {
		this.schedulerTimer = setInterval(() => {
			this.processScheduledActions();
		}, 60 * 1000); // Verificar a cada minuto
	}

	/**
	 * Para scheduler
	 */
	stopScheduler() {
		if (this.schedulerTimer) {
			clearInterval(this.schedulerTimer);
			this.schedulerTimer = null;
		}
	}

	// ===========================================================================
	// Gerenciamento de Níveis de Autonomia
	// ===========================================================================

	/**
	 * Define nível de autonomia de um agente
	 * @param {string} agentId - ID do agente
	 * @param {number} level - Nível de autonomia (0-4)
	 */
	setAutonomyLevel(agentId, level) {
		if (level < AUTONOMY_LEVELS.NONE || level > AUTONOMY_LEVELS.FULL) {
			throw new Error(`Invalid autonomy level: ${level}`);
		}

		this.autonomyLevels.set(agentId, level);
		logger.info(`[Autonomy] Level set for ${agentId}: ${level}`);
	}

	/**
	 * Obtém nível de autonomia de um agente
	 * @param {string} agentId - ID do agente
	 * @returns {number} - Nível de autonomia
	 */
	getAutonomyLevel(agentId) {
		return this.autonomyLevels.get(agentId) || AUTONOMY_LEVELS.NONE;
	}

	/**
	 * Verifica se agente pode executar ação
	 * @param {string} agentId - ID do agente
	 * @param {string} actionType - Tipo da ação
	 * @returns {Object} - { allowed, reason, requiresApproval }
	 */
	canExecuteAction(agentId, actionType) {
		const level = this.getAutonomyLevel(agentId);
		const requiredLevel = this.getRequiredLevel(actionType);

		// Verificar se o nível é suficiente
		if (level < requiredLevel) {
			return {
				allowed: false,
				reason: `Autonomy level ${level} < required ${requiredLevel}`,
				requiresApproval: true
			};
		}

		// Verificar se precisa de aprovação
		const requiresApproval =
			level < this.config.requireApprovalAbove || this.requiresSpecificApproval(actionType);

		// Verificar limite de ações por hora
		if (this.hasExceededRateLimit(agentId)) {
			return {
				allowed: false,
				reason: "Rate limit exceeded",
				requiresApproval: false
			};
		}

		return {
			allowed: true,
			reason: "OK",
			requiresApproval
		};
	}

	/**
	 * Obtém nível necessário para uma ação
	 * @param {string} actionType - Tipo da ação
	 * @returns {number} - Nível necessário
	 */
	getRequiredLevel(actionType) {
		const levelMap = {
			[ACTION_TYPES.TASK_CREATE]: AUTONOMY_LEVELS.LOW,
			[ACTION_TYPES.TASK_UPDATE]: AUTONOMY_LEVELS.LOW,
			[ACTION_TYPES.TASK_COMPLETE]: AUTONOMY_LEVELS.LOW,
			[ACTION_TYPES.SCHEDULE_EVENT]: AUTONOMY_LEVELS.MEDIUM,
			[ACTION_TYPES.CANCEL_EVENT]: AUTONOMY_LEVELS.MEDIUM,
			[ACTION_TYPES.SEND_NOTIFICATION]: AUTONOMY_LEVELS.LOW,
			[ACTION_TYPES.EXECUTE_WORKFLOW]: AUTONOMY_LEVELS.HIGH,
			[ACTION_TYPES.CALL_EXTERNAL_API]: AUTONOMY_LEVELS.HIGH,
			[ACTION_TYPES.MODIFY_DATA]: AUTONOMY_LEVELS.HIGH,
			[ACTION_TYPES.REQUEST_APPROVAL]: AUTONOMY_LEVELS.NONE
		};

		return levelMap[actionType] || AUTONOMY_LEVELS.HIGH;
	}

	/**
	 * Verifica se ação requer aprovação específica
	 * @param {string} actionType - Tipo da ação
	 * @returns {boolean}
	 */
	requiresSpecificApproval(actionType) {
		// Ações que sempre precisam de aprovação
		const alwaysRequireApproval = [ACTION_TYPES.CALL_EXTERNAL_API, ACTION_TYPES.MODIFY_DATA];

		return alwaysRequireApproval.includes(actionType);
	}

	/**
	 * Verifica se agente excedeu limite de taxas
	 * @param {string} agentId - ID do agente
	 * @returns {boolean}
	 */
	hasExceededRateLimit(agentId) {
		const oneHourAgo = Date.now() - 60 * 60 * 1000;

		const recentActions = this.actionHistory.filter(
			(a) =>
				a.agentId === agentId && a.timestamp > oneHourAgo && a.status !== ACTION_STATUS.REJECTED
		);

		return recentActions.length >= this.config.maxActionsPerHour;
	}

	// ===========================================================================
	// Execução de Ações
	// ===========================================================================

	/**
	 * Executa uma ação autônoma
	 * @param {Object} action - Dados da ação
	 * @returns {Promise<Object>} - Resultado da ação
	 */
	async executeAction(action) {
		const { agentId, type, parameters = {}, context = {}, forceApproval = false } = action;

		const actionId = `action-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

		// Verificar se pode executar
		const canExecute = this.canExecuteAction(agentId, type);

		if (!canExecute.allowed) {
			logger.warn(`[Autonomy] Action blocked for ${agentId}: ${canExecute.reason}`);
			throw new Error(`Action blocked: ${canExecute.reason}`);
		}

		// Criar registro da ação
		const actionRecord = {
			id: actionId,
			agentId,
			type,
			parameters,
			context,
			status: ACTION_STATUS.PENDING,
			createdAt: Date.now(),
			updatedAt: Date.now()
		};

		// Se requer aprovação
		if (canExecute.requiresApproval || forceApproval) {
			this.pendingActions.set(actionId, actionRecord);
			this.stats.pendingActions++;

			logger.info(`[Autonomy] Action requires approval: ${actionId} (${type})`);

			return {
				actionId,
				status: "pending-approval",
				message: "Action requires approval before execution"
			};
		}

		// Executar ação automaticamente
		return this.processAction(actionRecord);
	}

	/**
	 * Processa uma ação (executa)
	 * @param {Object} actionRecord - Registro da ação
	 * @returns {Promise<Object>} - Resultado
	 */
	async processAction(actionRecord) {
		const startTime = Date.now();

		try {
			actionRecord.status = ACTION_STATUS.IN_PROGRESS;
			actionRecord.startedAt = startTime;

			// Executar baseado no tipo
			let result;

			switch (actionRecord.type) {
				case ACTION_TYPES.TASK_CREATE:
					result = await this.executeTaskCreate(actionRecord);
					break;
				case ACTION_TYPES.TASK_UPDATE:
					result = await this.executeTaskUpdate(actionRecord);
					break;
				case ACTION_TYPES.TASK_COMPLETE:
					result = await this.executeTaskComplete(actionRecord);
					break;
				case ACTION_TYPES.SCHEDULE_EVENT:
					result = await this.executeScheduleEvent(actionRecord);
					break;
				case ACTION_TYPES.SEND_NOTIFICATION:
					result = await this.executeSendNotification(actionRecord);
					break;
				case ACTION_TYPES.EXECUTE_WORKFLOW:
					result = await this.executeWorkflow(actionRecord);
					break;
				default:
					throw new Error(`Unknown action type: ${actionRecord.type}`);
			}

			// Atualizar registro
			actionRecord.status = ACTION_STATUS.COMPLETED;
			actionRecord.result = result;
			actionRecord.completedAt = Date.now();
			actionRecord.duration = actionRecord.completedAt - startTime;

			// Atualizar estatísticas
			this.updateStats(actionRecord, true);

			// Adicionar ao histórico
			this.addToHistory(actionRecord);

			logger.info(`[Autonomy] Action completed: ${actionRecord.id} in ${actionRecord.duration}ms`);

			return {
				actionId: actionRecord.id,
				status: "completed",
				result,
				duration: actionRecord.duration
			};
		} catch (error) {
			// Atualizar registro com erro
			actionRecord.status = ACTION_STATUS.FAILED;
			actionRecord.error = error.message;
			actionRecord.completedAt = Date.now();
			actionRecord.duration = actionRecord.completedAt - startTime;

			// Atualizar estatísticas
			this.updateStats(actionRecord, false);

			// Adicionar ao histórico
			this.addToHistory(actionRecord);

			logger.error(`[Autonomy] Action failed: ${actionRecord.id} - ${error.message}`);

			throw error;
		}
	}

	// ===========================================================================
	// Executores de Ação
	// ===========================================================================

	/**
	 * Executa criação de tarefa
	 * @param {Object} actionRecord - Registro da ação
	 * @returns {Promise<Object>} - Resultado
	 */
	async executeTaskCreate(actionRecord) {
		const { title, description, priority, dueDate } = actionRecord.parameters;

		// Simular criação de tarefa
		const task = {
			id: `task-${Date.now()}`,
			title: title || "Untitled Task",
			description: description || "",
			priority: priority || "normal",
			dueDate: dueDate || null,
			createdBy: actionRecord.agentId,
			createdAt: Date.now(),
			status: "pending"
		};

		logger.debug(`[Autonomy] Task created: ${task.id}`);

		return { task };
	}

	/**
	 * Executa atualização de tarefa
	 * @param {Object} actionRecord - Registro da ação
	 * @returns {Promise<Object>} - Resultado
	 */
	async executeTaskUpdate(actionRecord) {
		const { taskId, updates } = actionRecord.parameters;

		// Simular atualização
		logger.debug(`[Autonomy] Task updated: ${taskId}`);

		return { taskId, updates, updatedAt: Date.now() };
	}

	/**
	 * Executa conclusão de tarefa
	 * @param {Object} actionRecord - Registro da ação
	 * @returns {Promise<Object>} - Resultado
	 */
	async executeTaskComplete(actionRecord) {
		const { taskId } = actionRecord.parameters;

		// Simular conclusão
		logger.debug(`[Autonomy] Task completed: ${taskId}`);

		return { taskId, completedAt: Date.now() };
	}

	/**
	 * Executa agendamento de evento
	 * @param {Object} actionRecord - Registro da ação
	 * @returns {Promise<Object>} - Resultado
	 */
	async executeScheduleEvent(actionRecord) {
		const { eventName, scheduledTime, payload } = actionRecord.parameters;

		const eventId = `event-${Date.now()}`;

		// Armazenar evento agendado
		this.scheduledActions.set(eventId, {
			id: eventId,
			action: actionRecord,
			scheduledTime: new Date(scheduledTime).getTime(),
			payload,
			createdAt: Date.now()
		});

		logger.debug(`[Autonomy] Event scheduled: ${eventId} for ${scheduledTime}`);

		return { eventId, scheduledTime };
	}

	/**
	 * Executa envio de notificação
	 * @param {Object} actionRecord - Registro da ação
	 * @returns {Promise<Object>} - Resultado
	 */
	async executeSendNotification(actionRecord) {
		const { recipient, message, channel } = actionRecord.parameters;

		// Simular envio de notificação
		logger.debug(`[Autonomy] Notification sent to ${recipient}: ${message.substring(0, 50)}...`);

		return { sent: true, recipient, timestamp: Date.now() };
	}

	/**
	 * Executa workflow
	 * @param {Object} actionRecord - Registro da ação
	 * @returns {Promise<Object>} - Resultado
	 */
	async executeWorkflow(actionRecord) {
		const { workflowId, parameters } = actionRecord.parameters;

		// Simular execução de workflow
		logger.debug(`[Autonomy] Workflow executed: ${workflowId}`);

		return { workflowId, executedAt: Date.now() };
	}

	// ===========================================================================
	// Aprovação de Ações
	// ===========================================================================

	/**
	 * Aprova uma ação pendente
	 * @param {string} actionId - ID da ação
	 * @param {string} approverId - ID de quem aprovou
	 * @param {string} comment - Comentário
	 * @returns {Promise<Object>} - Resultado
	 */
	async approveAction(actionId, approverId, comment = "") {
		const action = this.pendingActions.get(actionId);
		if (!action) {
			throw new Error(`Action not found: ${actionId}`);
		}

		// Atualizar registro
		action.status = ACTION_STATUS.APPROVED;
		action.approvedBy = approverId;
		action.approvedAt = Date.now();
		action.approvalComment = comment;
		action.updatedAt = Date.now();

		// Remover de pendentes
		this.pendingActions.delete(actionId);
		this.stats.pendingActions--;
		this.stats.approvedActions++;

		logger.info(`[Autonomy] Action approved: ${actionId} by ${approverId}`);

		// Processar ação
		return this.processAction(action);
	}

	/**
	 * Rejeita uma ação pendente
	 * @param {string} actionId - ID da ação
	 * @param {string} rejectorId - ID de quem rejeitou
	 * @param {string} reason - Motivo
	 * @returns {Object} - Resultado
	 */
	rejectAction(actionId, rejectorId, reason = "") {
		const action = this.pendingActions.get(actionId);
		if (!action) {
			throw new Error(`Action not found: ${actionId}`);
		}

		// Atualizar registro
		action.status = ACTION_STATUS.REJECTED;
		action.rejectedBy = rejectorId;
		action.rejectedAt = Date.now();
		action.rejectionReason = reason;
		action.updatedAt = Date.now();

		// Remover de pendentes
		this.pendingActions.delete(actionId);
		this.stats.pendingActions--;
		this.stats.rejectedActions++;

		// Adicionar ao histórico
		this.addToHistory(action);

		logger.info(`[Autonomy] Action rejected: ${actionId} by ${rejectorId} - ${reason}`);

		return {
			actionId,
			status: "rejected",
			reason
		};
	}

	/**
	 * Obtém ações pendentes
	 * @param {string} agentId - ID do agente (opcional)
	 * @returns {Array} - Lista de ações pendentes
	 */
	getPendingActions(agentId = null) {
		const actions = Array.from(this.pendingActions.values());

		if (agentId) {
			return actions.filter((a) => a.agentId === agentId);
		}

		return actions;
	}

	// ===========================================================================
	// Ações Agendadas
	// ===========================================================================

	/**
	 * Processa ações agendadas
	 */
	async processScheduledActions() {
		const now = Date.now();

		// Limpar ações agendadas expiradas (mais de 24 horas)
		const maxAge = 24 * 60 * 60 * 1000;
		for (const [eventId, scheduled] of this.scheduledActions.entries()) {
			if (now - scheduled.createdAt > maxAge) {
				logger.info(`[Autonomy] Removing expired scheduled action: ${eventId}`);
				this.scheduledActions.delete(eventId);
			}
		}

		// Limpar ações pendentes antigas (mais de 7 dias)
		const pendingMaxAge = 7 * 24 * 60 * 60 * 1000;
		for (const [actionId, action] of this.pendingActions.entries()) {
			if (now - action.createdAt > pendingMaxAge) {
				logger.info(`[Autonomy] Removing stale pending action: ${actionId}`);
				action.status = ACTION_STATUS.CANCELLED;
				this.addToHistory(action);
				this.pendingActions.delete(actionId);
			}
		}

		for (const [eventId, scheduled] of this.scheduledActions.entries()) {
			if (now >= scheduled.scheduledTime) {
				logger.info(`[Autonomy] Processing scheduled action: ${eventId}`);

				try {
					await this.processAction(scheduled.action);
					this.scheduledActions.delete(eventId);
				} catch (error) {
					logger.error(`[Autonomy] Failed to process scheduled action: ${eventId}`, error);
					this.scheduledActions.delete(eventId);
				}
			}
		}
	}

	/**
	 * Cancela ação agendada
	 * @param {string} eventId - ID do evento
	 * @returns {boolean} - Sucesso
	 */
	cancelScheduledAction(eventId) {
		return this.scheduledActions.delete(eventId);
	}

	// ===========================================================================
	// Histórico e Estatísticas
	// ===========================================================================

	/**
	 * Adiciona ao histórico
	 * @param {Object} actionRecord - Registro da ação
	 */
	addToHistory(actionRecord) {
		this.actionHistory.push({
			...actionRecord,
			historyTimestamp: Date.now()
		});

		// Limitar tamanho do histórico
		if (this.actionHistory.length > 1000) {
			this.actionHistory = this.actionHistory.slice(-1000);
		}
	}

	/**
	 * Atualiza estatísticas
	 * @param {Object} actionRecord - Registro da ação
	 * @param {boolean} success - Se teve sucesso
	 */
	updateStats(actionRecord, success) {
		this.stats.totalActions++;

		if (success) {
			this.stats.approvedActions++;
		} else {
			this.stats.failedActions++;
		}

		// Por agente
		if (!this.stats.byAgent[actionRecord.agentId]) {
			this.stats.byAgent[actionRecord.agentId] = {
				total: 0,
				success: 0,
				failed: 0
			};
		}

		const agentStats = this.stats.byAgent[actionRecord.agentId];
		agentStats.total++;
		if (success) {
			agentStats.success++;
		} else {
			agentStats.failed++;
		}

		// Por tipo
		if (!this.stats.byType[actionRecord.type]) {
			this.stats.byType[actionRecord.type] = {
				total: 0,
				success: 0,
				failed: 0
			};
		}

		const typeStats = this.stats.byType[actionRecord.type];
		typeStats.total++;
		if (success) {
			typeStats.success++;
		} else {
			typeStats.failed++;
		}
	}

	/**
	 * Obtém estatísticas
	 * @returns {Object} - Estatísticas
	 */
	getStats() {
		return {
			...this.stats,
			scheduledActions: this.scheduledActions.size,
			historySize: this.actionHistory.length
		};
	}

	/**
	 * Obtém histórico de ações
	 * @param {Object} filters - Filtros
	 * @returns {Array} - Histórico
	 */
	getHistory(filters = {}) {
		const { agentId, type, limit = 50 } = filters;

		let history = [...this.actionHistory];

		if (agentId) {
			history = history.filter((h) => h.agentId === agentId);
		}

		if (type) {
			history = history.filter((h) => h.type === type);
		}

		// Ordenar por timestamp
		history.sort((a, b) => b.createdAt - a.createdAt);

		return history.slice(0, limit);
	}

	/**
	 * Reseta estatísticas
	 */
	resetStats() {
		this.stats = {
			totalActions: 0,
			approvedActions: 0,
			rejectedActions: 0,
			failedActions: 0,
			autoApprovedActions: 0,
			pendingActions: this.pendingActions.size,
			byAgent: {},
			byType: {}
		};
	}
}

// Singleton
AgentAutonomy.instance = null;

module.exports = AgentAutonomy;
