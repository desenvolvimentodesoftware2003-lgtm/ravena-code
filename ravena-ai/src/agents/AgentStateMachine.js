/**
 * AgentStateMachine.js
 *
 * Máquina de estados para workflows de agentes.
 * Gerencia o fluxo de execução de workflows complexos
 * com suporte a estados, transições e handlers.
 *
 * Nível 3 - Máquina de Estados
 */

"use strict";

const Logger = require("../utils/Logger");

const logger = new Logger("agent-state-machine");

/**
 * Estados possíveis
 */
const STATES = {
	IDLE: "idle",
	INITIALIZING: "initializing",
	PROCESSING: "processing",
	WAITING_INPUT: "waiting-input",
	WAITING_EXTERNAL: "waiting-external",
	COMPLETED: "completed",
	FAILED: "failed",
	PAUSED: "paused",
	CANCELLED: "cancelled"
};

/**
 * Tipos de transição
 */
const TRANSITION_TYPES = {
	AUTOMATIC: "automatic", // Transição automática
	CONDITIONAL: "conditional", // Baseada em condição
	EVENT: "event" // Disparada por evento
};

/**
 * Class for state machine
 */
class AgentStateMachine {
	constructor() {
		// Workflows registrados: workflowId -> { states, transitions, handlers }
		this.workflows = new Map();

		// Instâncias ativas: instanceId -> { workflowId, currentState, context, history }
		this.instances = new Map();

		// Configurações
		this.config = {
			maxConcurrentInstances: 10,
			maxHistoryPerInstance: 50,
			autoCleanupAfterCompletion: true,
			cleanupDelay: 5 * 60 * 1000, // 5 minutos
			enableLogging: true
		};

		// Estatísticas
		this.stats = {
			totalWorkflows: 0,
			totalInstances: 0,
			completedInstances: 0,
			failedInstances: 0,
			avgExecutionTime: 0,
			byWorkflow: {}
		};

		// Inicializar workflows predefinidos
		this.initDefaultWorkflows();
	}

	/**
	 * Get singleton instance
	 * @returns {AgentStateMachine} - Singleton instance
	 */
	static getInstance() {
		if (!AgentStateMachine.instance) {
			AgentStateMachine.instance = new AgentStateMachine();
		}
		return AgentStateMachine.instance;
	}

	/**
	 * Inicializa workflows predefinidos
	 */
	initDefaultWorkflows() {
		// Workflow: Atendimento ao cliente
		this.registerWorkflow("customer-support", {
			name: "Atendimento ao Cliente",
			description: "Workflow para atendimento ao cliente com aprovação",
			states: {
				[STATES.IDLE]: {
					enter: async (context) => {
						logger.debug("[customer-support] Entering idle state");
					}
				},
				[STATES.INITIALIZING]: {
					enter: async (context) => {
						context.ticket = {
							id: `TICKET-${Date.now()}`,
							status: "open",
							priority: "normal",
							createdAt: Date.now()
						};
						return { nextState: STATES.PROCESSING };
					}
				},
				[STATES.PROCESSING]: {
					enter: async (context) => {
						// Processar solicitação do cliente
						context.processingResult = await this.processCustomerRequest(context);

						// Verificar se precisa de aprovação
						if (context.processingResult.needsApproval) {
							return { nextState: STATES.WAITING_INPUT };
						}

						return { nextState: STATES.COMPLETED };
					}
				},
				[STATES.WAITING_INPUT]: {
					enter: async (context) => {
						// Aguardar aprovação do administrador
						context.approvalStatus = "pending";
						return { nextState: STATES.WAITING_EXTERNAL };
					}
				},
				[STATES.WAITING_EXTERNAL]: {
					enter: async (context) =>
						// Aguardar evento externo (aprovação)
						({ wait: true }),
					onEvent: async (event, context) => {
						if (event.type === "approval") {
							context.approvalStatus = event.approved ? "approved" : "rejected";

							if (event.approved) {
								return { nextState: STATES.COMPLETED };
							}
							return { nextState: STATES.FAILED };
						}
						return { wait: true };
					}
				},
				[STATES.COMPLETED]: {
					enter: async (context) => {
						context.ticket.status = "closed";
						context.completedAt = Date.now();
						return { final: true };
					}
				},
				[STATES.FAILED]: {
					enter: async (context) => {
						context.ticket.status = "failed";
						context.failedAt = Date.now();
						return { final: true };
					}
				}
			},
			transitions: [
				{ from: STATES.IDLE, to: STATES.INITIALIZING, type: TRANSITION_TYPES.AUTOMATIC },
				{ from: STATES.INITIALIZING, to: STATES.PROCESSING, type: TRANSITION_TYPES.AUTOMATIC },
				{
					from: STATES.PROCESSING,
					to: STATES.WAITING_INPUT,
					type: TRANSITION_TYPES.CONDITIONAL,
					condition: (context) => context.processingResult?.needsApproval
				},
				{ from: STATES.PROCESSING, to: STATES.COMPLETED, type: TRANSITION_TYPES.AUTOMATIC },
				{
					from: STATES.WAITING_INPUT,
					to: STATES.WAITING_EXTERNAL,
					type: TRANSITION_TYPES.AUTOMATIC
				},
				{ from: STATES.WAITING_EXTERNAL, to: STATES.COMPLETED, type: TRANSITION_TYPES.EVENT },
				{ from: STATES.WAITING_EXTERNAL, to: STATES.FAILED, type: TRANSITION_TYPES.EVENT }
			]
		});

		// Workflow: Análise multi-agente
		this.registerWorkflow("multi-agent-analysis", {
			name: "Análise Multi-Agente",
			description: "Workflow para análise com múltiplos agentes",
			states: {
				[STATES.IDLE]: {
					enter: async (context) => {
						logger.debug("[multi-agent-analysis] Entering idle state");
					}
				},
				[STATES.INITIALIZING]: {
					enter: async (context) => {
						context.analysis = {
							id: `ANALYSIS-${Date.now()}`,
							agents: [],
							results: {},
							status: "initializing"
						};
						return { nextState: STATES.PROCESSING };
					}
				},
				[STATES.PROCESSING]: {
					enter: async (context) => {
						// Processar com cada agente sequencialmente
						const agents = context.agents || ["dev", "busca360", "hacker"];

						for (const agentId of agents) {
							context.analysis.agents.push(agentId);
							context.analysis.currentAgent = agentId;
							context.analysis.status = `processing-${agentId}`;

							// Chamar agente
							const result = await this.callAgent(agentId, context.query, context);
							context.analysis.results[agentId] = result;
						}

						return { nextState: STATES.COMPLETED };
					}
				},
				[STATES.COMPLETED]: {
					enter: async (context) => {
						context.analysis.status = "completed";
						context.analysis.completedAt = Date.now();
						return { final: true };
					}
				},
				[STATES.FAILED]: {
					enter: async (context) => {
						context.analysis.status = "failed";
						context.analysis.failedAt = Date.now();
						return { final: true };
					}
				}
			},
			transitions: [
				{ from: STATES.IDLE, to: STATES.INITIALIZING, type: TRANSITION_TYPES.AUTOMATIC },
				{ from: STATES.INITIALIZING, to: STATES.PROCESSING, type: TRANSITION_TYPES.AUTOMATIC },
				{ from: STATES.PROCESSING, to: STATES.COMPLETED, type: TRANSITION_TYPES.AUTOMATIC },
				{ from: STATES.PROCESSING, to: STATES.FAILED, type: TRANSITION_TYPES.CONDITIONAL }
			]
		});

		logger.debug(`[StateMachine] Initialized ${this.workflows.size} default workflows`);
	}

	/**
	 * Registra um workflow
	 * @param {string} id - ID do workflow
	 * @param {Object} workflow - Configuração do workflow
	 */
	registerWorkflow(id, workflow) {
		if (!id || !workflow) {
			throw new Error("Workflow ID and configuration are required");
		}

		if (!workflow.states || Object.keys(workflow.states).length === 0) {
			throw new Error("Workflow must have at least one state");
		}

		this.workflows.set(id, {
			...workflow,
			id,
			createdAt: Date.now()
		});

		this.stats.totalWorkflows++;

		logger.info(`[StateMachine] Workflow registered: ${id} (${workflow.name})`);
	}

	/**
	 * Cria uma nova instância de workflow
	 * @param {string} workflowId - ID do workflow
	 * @param {Object} context - Contexto inicial
	 * @returns {string} - ID da instância
	 */
	createInstance(workflowId, context = {}) {
		const workflow = this.workflows.get(workflowId);
		if (!workflow) {
			throw new Error(`Workflow "${workflowId}" not found`);
		}

		// Verificar limite de instâncias concorrentes
		if (this.instances.size >= this.config.maxConcurrentInstances) {
			throw new Error("Maximum concurrent instances reached");
		}

		const instanceId = `inst-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

		const instance = {
			id: instanceId,
			workflowId,
			workflow,
			currentState: STATES.IDLE,
			context: {
				...context,
				instanceId,
				workflowId,
				createdAt: Date.now()
			},
			history: [],
			startTime: Date.now(),
			lastActivity: Date.now(),
			status: "running"
		};

		this.instances.set(instanceId, instance);
		this.stats.totalInstances++;

		logger.info(`[StateMachine] Instance created: ${instanceId} (workflow: ${workflowId})`);

		return instanceId;
	}

	/**
	 * Executa uma instância de workflow
	 * @param {string} instanceId - ID da instância
	 * @returns {Promise<Object>} - Resultado da execução
	 */
	async executeInstance(instanceId) {
		const instance = this.instances.get(instanceId);
		if (!instance) {
			throw new Error(`Instance "${instanceId}" not found`);
		}

		const startTime = Date.now();

		try {
			logger.info(`[StateMachine] Executing instance: ${instanceId}`);

			// Executar estados até chegar a um estado final ou de espera
			let maxIterations = 100; // Proteção contra loops infinitos

			while (maxIterations > 0) {
				maxIterations--;

				const state = instance.workflow.states[instance.currentState];
				if (!state) {
					throw new Error(`State "${instance.currentState}" not found`);
				}

				// Executar handler de entrada do estado
				if (state.enter) {
					const result = await state.enter(instance.context);

					// Registrar no histórico
					this.addToHistory(instance, {
						state: instance.currentState,
						action: "enter",
						timestamp: Date.now(),
						result
					});

					// Verificar se é estado final
					if (result.final) {
						instance.status = "completed";
						instance.endTime = Date.now();
						instance.duration = instance.endTime - instance.startTime;

						this.stats.completedInstances++;
						this.updateExecutionStats(instance);

						logger.info(
							`[StateMachine] Instance completed: ${instanceId} in ${instance.duration}ms`
						);

						return {
							instanceId,
							workflowId: instance.workflowId,
							status: "completed",
							result: instance.context,
							duration: instance.duration
						};
					}

					// Verificar se precisa de transição
					if (result.nextState) {
						const transition = this.findTransition(
							instance.workflow,
							instance.currentState,
							result.nextState
						);

						if (transition) {
							// Registrar transição
							this.addToHistory(instance, {
								state: instance.currentState,
								action: "transition",
								to: result.nextState,
								timestamp: Date.now()
							});

							instance.currentState = result.nextState;
							instance.lastActivity = Date.now();
						} else {
							// Transição direta
							instance.currentState = result.nextState;
							instance.lastActivity = Date.now();
						}
					}

					// Verificar se precisa esperar
					if (result.wait) {
						instance.status = "waiting";
						logger.info(`[StateMachine] Instance waiting: ${instanceId}`);

						return {
							instanceId,
							workflowId: instance.workflowId,
							status: "waiting",
							currentState: instance.currentState
						};
					}
				}
			}

			// Se chegou aqui, pode ter sido um loop infinito
			throw new Error("Maximum iterations exceeded (possible infinite loop)");
		} catch (error) {
			instance.status = "failed";
			instance.endTime = Date.now();
			instance.duration = instance.endTime - instance.startTime;
			instance.error = error.message;

			this.stats.failedInstances++;
			this.updateExecutionStats(instance);

			logger.error(`[StateMachine] Instance failed: ${instanceId} - ${error.message}`);

			throw error;
		}
	}

	/**
	 * Processa evento em uma instância
	 * @param {string} instanceId - ID da instância
	 * @param {Object} event - Evento
	 * @returns {Promise<Object>} - Resultado
	 */
	async processEvent(instanceId, event) {
		const instance = this.instances.get(instanceId);
		if (!instance) {
			throw new Error(`Instance "${instanceId}" not found`);
		}

		const state = instance.workflow.states[instance.currentState];
		if (!state || !state.onEvent) {
			throw new Error(`No event handler for state "${instance.currentState}"`);
		}

		logger.info(`[StateMachine] Processing event in instance ${instanceId}: ${event.type}`);

		// Registrar evento
		this.addToHistory(instance, {
			state: instance.currentState,
			action: "event",
			event: event.type,
			timestamp: Date.now()
		});

		// Processar evento
		const result = await state.onEvent(event, instance.context);

		// Verificar se precisa de transição
		if (result.nextState) {
			instance.currentState = result.nextState;
			instance.lastActivity = Date.now();

			// Se não está esperando, continuar execução
			if (!result.wait) {
				return this.executeInstance(instanceId);
			}
		}

		return {
			instanceId,
			currentState: instance.currentState,
			status: instance.status
		};
	}

	/**
	 * Pausa uma instância
	 * @param {string} instanceId - ID da instância
	 */
	pauseInstance(instanceId) {
		const instance = this.instances.get(instanceId);
		if (!instance) {
			throw new Error(`Instance "${instanceId}" not found`);
		}

		instance.status = "paused";
		instance.pausedAt = Date.now();

		this.addToHistory(instance, {
			state: instance.currentState,
			action: "pause",
			timestamp: Date.now()
		});

		logger.info(`[StateMachine] Instance paused: ${instanceId}`);
	}

	/**
	 * Resume uma instância pausada
	 * @param {string} instanceId - ID da instância
	 * @returns {Promise<Object>} - Resultado
	 */
	async resumeInstance(instanceId) {
		const instance = this.instances.get(instanceId);
		if (!instance) {
			throw new Error(`Instance "${instanceId}" not found`);
		}

		if (instance.status !== "paused") {
			throw new Error("Instance is not paused");
		}

		instance.status = "running";
		instance.resumedAt = Date.now();
		instance.lastActivity = Date.now();

		this.addToHistory(instance, {
			state: instance.currentState,
			action: "resume",
			timestamp: Date.now()
		});

		logger.info(`[StateMachine] Instance resumed: ${instanceId}`);

		return this.executeInstance(instanceId);
	}

	/**
	 * Cancela uma instância
	 * @param {string} instanceId - ID da instância
	 */
	cancelInstance(instanceId) {
		const instance = this.instances.get(instanceId);
		if (!instance) {
			throw new Error(`Instance "${instanceId}" not found`);
		}

		instance.status = "cancelled";
		instance.endTime = Date.now();
		instance.duration = instance.endTime - instance.startTime;

		this.addToHistory(instance, {
			state: instance.currentState,
			action: "cancel",
			timestamp: Date.now()
		});

		logger.info(`[StateMachine] Instance cancelled: ${instanceId}`);

		// Limpar após um tempo
		if (this.config.autoCleanupAfterCompletion) {
			setTimeout(() => {
				this.instances.delete(instanceId);
			}, this.config.cleanupDelay);
		}
	}

	/**
	 * Encontra transição válida
	 * @param {Object} workflow - Workflow
	 * @param {string} from - Estado de origem
	 * @param {string} to - Estado de destino
	 * @returns {Object|null} - Transição encontrada
	 */
	findTransition(workflow, from, to) {
		if (!workflow.transitions) {
			return null;
		}

		return workflow.transitions.find((t) => t.from === from && t.to === to);
	}

	/**
	 * Adiciona entrada ao histórico
	 * @param {Object} instance - Instância
	 * @param {Object} entry - Entrada
	 */
	addToHistory(instance, entry) {
		instance.history.push(entry);

		// Limitar tamanho do histórico
		if (instance.history.length > this.config.maxHistoryPerInstance) {
			instance.history = instance.history.slice(-this.config.maxHistoryPerInstance);
		}
	}

	/**
	 * Atualiza estatísticas de execução
	 * @param {Object} instance - Instância
	 */
	updateExecutionStats(instance) {
		const workflowId = instance.workflowId;

		if (!this.stats.byWorkflow[workflowId]) {
			this.stats.byWorkflow[workflowId] = {
				total: 0,
				completed: 0,
				failed: 0,
				avgDuration: 0
			};
		}

		const workflowStats = this.stats.byWorkflow[workflowId];
		workflowStats.total++;

		if (instance.status === "completed") {
			workflowStats.completed++;
		} else if (instance.status === "failed") {
			workflowStats.failed++;
		}

		// Atualizar duração média
		if (instance.duration) {
			const totalTime = workflowStats.avgDuration * (workflowStats.total - 1);
			workflowStats.avgDuration = (totalTime + instance.duration) / workflowStats.total;
		}

		// Atualizar estatísticas gerais
		const totalTime = this.stats.avgExecutionTime * (this.stats.totalInstances - 1);
		this.stats.avgExecutionTime =
			(totalTime + (instance.duration || 0)) / this.stats.totalInstances;
	}

	/**
	 * Processa solicitação de cliente (mock)
	 * @param {Object} context - Contexto
	 * @returns {Promise<Object>} - Resultado
	 */
	async processCustomerRequest(context) {
		// Simular processamento
		await new Promise((resolve) => setTimeout(resolve, 100));

		return {
			processed: true,
			needsApproval: context.priority === "high",
			timestamp: Date.now()
		};
	}

	/**
	 * Chama um agente (mock)
	 * @param {string} agentId - ID do agente
	 * @param {string} query - Pergunta
	 * @param {Object} context - Contexto
	 * @returns {Promise<string>} - Resposta
	 */
	async callAgent(agentId, query, context) {
		// Simular chamada ao agente
		await new Promise((resolve) => setTimeout(resolve, 100));

		return `Resposta do agente ${agentId} para: "${query}"`;
	}

	// ===========================================================================
	// Consultas
	// ===========================================================================

	/**
	 * Obtém lista de workflows
	 * @returns {Array} - Lista de workflows
	 */
	listWorkflows() {
		return Array.from(this.workflows.values()).map((w) => ({
			id: w.id,
			name: w.name,
			description: w.description,
			states: Object.keys(w.states),
			transitions: w.transitions?.length || 0
		}));
	}

	/**
	 * Obtém detalhes de um workflow
	 * @param {string} workflowId - ID do workflow
	 * @returns {Object|null} - Workflow
	 */
	getWorkflow(workflowId) {
		return this.workflows.get(workflowId) || null;
	}

	/**
	 * Obtém lista de instâncias ativas
	 * @returns {Array} - Lista de instâncias
	 */
	listInstances() {
		return Array.from(this.instances.values()).map((i) => ({
			id: i.id,
			workflowId: i.workflowId,
			workflowName: i.workflow.name,
			status: i.status,
			currentState: i.currentState,
			startTime: i.startTime,
			lastActivity: i.lastActivity,
			duration: i.duration || Date.now() - i.startTime
		}));
	}

	/**
	 * Obtém detalhes de uma instância
	 * @param {string} instanceId - ID da instância
	 * @returns {Object|null} - Instância
	 */
	getInstance(instanceId) {
		const instance = this.instances.get(instanceId);
		if (!instance) {
			return null;
		}

		return {
			id: instance.id,
			workflowId: instance.workflowId,
			workflowName: instance.workflow.name,
			status: instance.status,
			currentState: instance.currentState,
			context: instance.context,
			history: instance.history,
			startTime: instance.startTime,
			lastActivity: instance.lastActivity,
			duration: instance.duration || Date.now() - instance.startTime,
			error: instance.error
		};
	}

	/**
	 * Obtém estatísticas
	 * @returns {Object} - Estatísticas
	 */
	getStats() {
		return {
			...this.stats,
			activeInstances: this.instances.size,
			totalWorkflows: this.workflows.size
		};
	}

	/**
	 * Reseta estatísticas
	 */
	resetStats() {
		this.stats = {
			totalWorkflows: this.workflows.size,
			totalInstances: 0,
			completedInstances: 0,
			failedInstances: 0,
			avgExecutionTime: 0,
			byWorkflow: {}
		};
		logger.debug("[StateMachine] Stats reset");
	}
}

// Singleton
AgentStateMachine.instance = null;

module.exports = AgentStateMachine;
