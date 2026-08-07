/**
 * AgentCollaboration.js
 *
 * Sistema de colaboração entre agentes.
 * Permite que múltiplos agentes trabalhem juntos em problemas complexos.
 * Suporta workflows sequenciais e paralelos.
 *
 * Nível 2 - Comunicação Inter-Agentes
 */

"use strict";

const Logger = require("../utils/Logger");
const { getAgent, listAgents } = require("./AgentConfig");

const logger = new Logger("agent-collaboration");

/**
 * Tipos de workflow
 */
const WORKFLOW_TYPES = {
	SEQUENTIAL: "sequential", // Agentes trabalham em sequência
	PARALLEL: "parallel", // Agentes trabalham em paralelo
	PIPELINE: "pipeline", // Saída de um é entrada do próximo
	CONSENSUS: "consensus" // Múltiplos agentes votam em uma resposta
};

/**
 * Status de uma colaboração
 */
const COLLABORATION_STATUS = {
	PENDING: "pending",
	IN_PROGRESS: "in_progress",
	COMPLETED: "completed",
	FAILED: "failed",
	TIMEOUT: "timeout"
};

/**
 * Class for agent collaboration
 */
class AgentCollaboration {
	constructor() {
		// Colaborações ativas
		this.activeCollaborations = new Map();

		// Histórico de colaborações
		this.history = [];

		// Workflows predefinidos
		this.workflows = new Map();

		// Configurações
		this.config = {
			maxConcurrentCollaborations: 3,
			defaultTimeout: 120000, // 2 minutos
			maxAgentsPerCollaboration: 4,
			historyLimit: 100
		};

		// Estatísticas
		this.stats = {
			totalCollaborations: 0,
			successfulCollaborations: 0,
			failedCollaborations: 0,
			avgResponseTime: 0,
			byWorkflowType: {}
		};

		// Inicializar workflows predefinidos
		this.initDefaultWorkflows();
	}

	/**
	 * Get singleton instance
	 * @returns {AgentCollaboration} - Singleton instance
	 */
	static getInstance() {
		if (!AgentCollaboration.instance) {
			AgentCollaboration.instance = new AgentCollaboration();
		}
		return AgentCollaboration.instance;
	}

	/**
	 * Inicializa workflows predefinidos
	 */
	initDefaultWorkflows() {
		// Workflow: Análise completa (dev + busca + hacker)
		this.registerWorkflow("full-analysis", {
			name: "Análise Completa",
			description: "Análise técnica completa com múltiplos especialistas",
			type: WORKFLOW_TYPES.PARALLEL,
			agents: ["dev", "busca360", "hacker"],
			timeout: 180000,
			prompt: (query) => `Analise a seguinte questão sob múltiplos aspectos:\n\n${query}`
		});

		// Workflow: Segurança do código
		this.registerWorkflow("secure-dev", {
			name: "Desenvolvimento Seguro",
			description: "Desenvolve e verifica segurança do código",
			type: WORKFLOW_TYPES.SEQUENTIAL,
			agents: ["dev", "hacker"],
			timeout: 150000,
			prompt: (query) => `Desenvolva uma solução segura para:\n\n${query}`
		});

		// Workflow: Pesquisa e implementação
		this.registerWorkflow("research-implement", {
			name: "Pesquisa e Implementação",
			description: "Pesquisa soluções e implementa a melhor opção",
			type: WORKFLOW_TYPES.PIPELINE,
			agents: ["busca360", "dev"],
			timeout: 150000,
			prompt: (query) => `Pesquisa e implemente a melhor solução para:\n\n${query}`
		});

		// Workflow: Auditoria completa
		this.registerWorkflow("full-audit", {
			name: "Auditoria Completa",
			description: "Auditoria técnica e de segurança abrangente",
			type: WORKFLOW_TYPES.CONSENSUS,
			agents: ["dev", "hacker", "busca360"],
			timeout: 180000,
			prompt: (query) => `Realize uma auditoria completa da seguinte questão:\n\n${query}`
		});

		logger.debug(`[Collaboration] Initialized ${this.workflows.size} default workflows`);
	}

	/**
	 * Registra um workflow personalizado
	 * @param {string} id - ID único do workflow
	 * @param {Object} workflow - Configuração do workflow
	 */
	registerWorkflow(id, workflow) {
		if (!id || !workflow) {
			throw new Error("Workflow ID and configuration are required");
		}

		if (!workflow.type || !Object.values(WORKFLOW_TYPES).includes(workflow.type)) {
			throw new Error(`Invalid workflow type: ${workflow.type}`);
		}

		if (!workflow.agents || !Array.isArray(workflow.agents) || workflow.agents.length === 0) {
			throw new Error("Workflow must have at least one agent");
		}

		// Validar que todos os agentes existem
		for (const agentId of workflow.agents) {
			if (!getAgent(agentId)) {
				throw new Error(`Agent "${agentId}" not found`);
			}
		}

		this.workflows.set(id, {
			...workflow,
			id,
			createdAt: Date.now()
		});

		logger.info(`[Collaboration] Workflow registered: ${id} (${workflow.name})`);
	}

	/**
	 * Inicia uma colaboração
	 * @param {Object} params - Parâmetros da colaboração
	 * @returns {Promise<Object>} - Resultado da colaboração
	 */
	async startCollaboration(params) {
		const { workflowId, query, groupId, llmService, context = {}, agents: overrideAgents } = params;

		// Verificar limite de colaborações concorrentes
		if (this.activeCollaborations.size >= this.config.maxConcurrentCollaborations) {
			throw new Error("Maximum concurrent collaborations reached. Please wait.");
		}

		// Obter workflow
		const workflow = this.workflows.get(workflowId);
		if (!workflow) {
			throw new Error(`Workflow "${workflowId}" not found`);
		}

		// Criar ID da colaboração
		const collaborationId = `collab-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

		// Agents para usar (override ou do workflow)
		const agentsToUse = overrideAgents || workflow.agents;

		// Validar limite de agentes
		if (agentsToUse.length > this.config.maxAgentsPerCollaboration) {
			throw new Error(
				`Too many agents (${agentsToUse.length}). Maximum: ${this.config.maxAgentsPerCollaboration}`
			);
		}

		// Criar objeto de colaboração
		const collaboration = {
			id: collaborationId,
			workflowId,
			workflow,
			query,
			groupId,
			context,
			agents: agentsToUse,
			status: COLLABORATION_STATUS.IN_PROGRESS,
			startTime: Date.now(),
			responses: [],
			finalResult: null,
			error: null
		};

		// Registrar colaboração ativa
		this.activeCollaborations.set(collaborationId, collaboration);

		logger.info(
			`[Collaboration] Started: ${collaborationId} (${workflow.name}) with ${agentsToUse.length} agents`
		);

		try {
			// Executar workflow baseado no tipo
			let result;

			switch (workflow.type) {
				case WORKFLOW_TYPES.SEQUENTIAL:
					result = await this.executeSequential(collaboration, llmService);
					break;
				case WORKFLOW_TYPES.PARALLEL:
					result = await this.executeParallel(collaboration, llmService);
					break;
				case WORKFLOW_TYPES.PIPELINE:
					result = await this.executePipeline(collaboration, llmService);
					break;
				case WORKFLOW_TYPES.CONSENSUS:
					result = await this.executeConsensus(collaboration, llmService);
					break;
				default:
					throw new Error(`Unknown workflow type: ${workflow.type}`);
			}

			// Atualizar colaboração
			collaboration.status = COLLABORATION_STATUS.COMPLETED;
			collaboration.finalResult = result;
			collaboration.endTime = Date.now();
			collaboration.duration = collaboration.endTime - collaboration.startTime;

			// Atualizar estatísticas
			this.updateStats(collaboration, true);

			// Adicionar ao histórico
			this.addToHistory(collaboration);

			// Remover das colaborações ativas
			this.activeCollaborations.delete(collaborationId);

			logger.info(`[Collaboration] Completed: ${collaborationId} in ${collaboration.duration}ms`);

			return {
				collaborationId,
				workflow: workflow.name,
				type: workflow.type,
				result,
				agents: agentsToUse,
				duration: collaboration.duration,
				agentResponses: collaboration.responses
			};
		} catch (error) {
			// Atualizar colaboração com erro
			collaboration.status = COLLABORATION_STATUS.FAILED;
			collaboration.error = error.message;
			collaboration.endTime = Date.now();
			collaboration.duration = collaboration.endTime - collaboration.startTime;

			// Atualizar estatísticas
			this.updateStats(collaboration, false);

			// Adicionar ao histórico
			this.addToHistory(collaboration);

			// Remover das colaborações ativas
			this.activeCollaborations.delete(collaborationId);

			logger.error(`[Collaboration] Failed: ${collaborationId} - ${error.message}`);

			throw error;
		}
	}

	/**
	 * Executa workflow sequencial
	 */
	async executeSequential(collaboration, llmService) {
		const { query, agents, workflow, context } = collaboration;
		let currentInput = query;
		const responses = [];

		for (const agentId of agents) {
			const agent = getAgent(agentId);
			if (!agent) {
				throw new Error(`Agent "${agentId}" not found`);
			}

			logger.debug(`[Collaboration] Sequential step: ${agentId}`);

			const prompt = workflow.prompt ? workflow.prompt(currentInput) : currentInput;

			const response = await llmService.getAnythingLLMCompletion({
				prompt,
				workspace: agent.workspace,
				systemContext: agent.systemPrompt,
				timeout: workflow.timeout || this.config.defaultTimeout
			});

			const agentResponse = {
				agentId,
				agentName: agent.name,
				input: currentInput,
				output: response,
				timestamp: Date.now()
			};

			responses.push(agentResponse);
			collaboration.responses.push(agentResponse);

			// Usar saída como entrada para o próximo agente
			currentInput = `Resposta do especialista anterior (${agent.name}):\n${response}\n\nContinue a análise com base nesta informação.`;
		}

		// Retornar a resposta final
		return responses[responses.length - 1]?.output || "No response generated";
	}

	/**
	 * Executa workflow paralelo
	 */
	async executeParallel(collaboration, llmService) {
		const { query, agents, workflow, context } = collaboration;
		const responses = [];

		// Criar promises para todos os agentes
		const promises = agents.map(async (agentId) => {
			const agent = getAgent(agentId);
			if (!agent) {
				throw new Error(`Agent "${agentId}" not found`);
			}

			logger.debug(`[Collaboration] Parallel step: ${agentId}`);

			const prompt = workflow.prompt ? workflow.prompt(query) : query;

			const response = await llmService.getAnythingLLMCompletion({
				prompt,
				workspace: agent.workspace,
				systemContext: agent.systemPrompt,
				timeout: workflow.timeout || this.config.defaultTimeout
			});

			return {
				agentId,
				agentName: agent.name,
				input: query,
				output: response,
				timestamp: Date.now()
			};
		});

		// Executar todas as promises
		const results = await Promise.allSettled(promises);

		// Coletar respostas
		for (const result of results) {
			if (result.status === "fulfilled") {
				responses.push(result.value);
				collaboration.responses.push(result.value);
			} else {
				logger.error(`[Collaboration] Agent failed: ${result.reason}`);
			}
		}

		// Combinar todas as respostas
		if (responses.length === 0) {
			throw new Error("All agents failed to respond");
		}

		// Criar resposta consolidada
		let consolidated = `## Respostas dos Especialistas\n\n`;

		for (const resp of responses) {
			consolidated += `### ${resp.agentName}\n${resp.output}\n\n---\n\n`;
		}

		return consolidated;
	}

	/**
	 * Executa workflow pipeline
	 */
	async executePipeline(collaboration, llmService) {
		const { query, agents, workflow, context } = collaboration;
		const pipelineData = { query, intermediateResults: [] };
		const responses = [];

		for (let i = 0; i < agents.length; i++) {
			const agentId = agents[i];
			const agent = getAgent(agentId);
			if (!agent) {
				throw new Error(`Agent "${agentId}" not found`);
			}

			logger.debug(`[Collaboration] Pipeline step ${i + 1}: ${agentId}`);

			// Montar prompt baseado no estágio do pipeline
			let prompt;
			if (i === 0) {
				// Primeiro agente recebe a query original
				prompt = workflow.prompt ? workflow.prompt(query) : query;
			} else {
				// Agentes seguintes recebem os resultados intermediários
				const prevResult = pipelineData.intermediateResults[i - 1];
				prompt = `Baseado na análise anterior:\n\n${prevResult.output}\n\n`;
				prompt += `Agora, aplique sua especialidade (${agent.name.toLowerCase()}) para: ${query}`;
			}

			const response = await llmService.getAnythingLLMCompletion({
				prompt,
				workspace: agent.workspace,
				systemContext: agent.systemPrompt,
				timeout: workflow.timeout || this.config.defaultTimeout
			});

			const agentResponse = {
				agentId,
				agentName: agent.name,
				stage: i + 1,
				input: i === 0 ? query : pipelineData.intermediateResults[i - 1]?.output,
				output: response,
				timestamp: Date.now()
			};

			responses.push(agentResponse);
			collaboration.responses.push(agentResponse);

			// Armazenar resultado intermediário
			pipelineData.intermediateResults.push({
				agentId,
				output: response
			});
		}

		// Retornar a resposta final do pipeline
		return responses[responses.length - 1]?.output || "No response generated";
	}

	/**
	 * Executa workflow de consenso
	 */
	async executeConsensus(collaboration, llmService) {
		const { query, agents, workflow, context } = collaboration;
		const responses = [];
		const votes = {};

		// Coletar respostas de todos os agentes
		for (const agentId of agents) {
			const agent = getAgent(agentId);
			if (!agent) {
				throw new Error(`Agent "${agentId}" not found`);
			}

			logger.debug(`[Collaboration] Consensus step: ${agentId}`);

			const prompt = workflow.prompt ? workflow.prompt(query) : query;

			// Adicionar instrução para votar
			const consensusPrompt = `${prompt}\n\n---\nApós analisar, vote em uma das opções abaixo (responda APENAS com o número):\n1. Aprovar (aprovar a ideia/solução)\n2. Rejeitar (rejeitar a ideia/solução)\n3. Modificar (sugerir modificações)\n4. Abster (não opiniar)\n\nTambém inclua uma justificativa curta.`;

			const response = await llmService.getAnythingLLMCompletion({
				prompt: consensusPrompt,
				workspace: agent.workspace,
				systemContext: agent.systemPrompt,
				timeout: workflow.timeout || this.config.defaultTimeout
			});

			// Extrair voto da resposta
			const voteMatch = response.match(/\b([1-4])\b/);
			const vote = voteMatch ? parseInt(voteMatch[1]) : 4; // Padrão: abster

			votes[agentId] = vote;

			const agentResponse = {
				agentId,
				agentName: agent.name,
				input: query,
				output: response,
				vote,
				voteLabel: ["", "Aprovar", "Rejeitar", "Modificar", "Abster"][vote],
				timestamp: Date.now()
			};

			responses.push(agentResponse);
			collaboration.responses.push(agentResponse);
		}

		// Calcular resultado do consenso
		const voteCounts = { 1: 0, 2: 0, 3: 0, 4: 0 };
		for (const vote of Object.values(votes)) {
			voteCounts[vote]++;
		}

		// Encontrar voto majoritário
		let majorityVote = 4;
		let maxCount = 0;

		for (const [vote, count] of Object.entries(voteCounts)) {
			if (count > maxCount) {
				maxCount = count;
				majorityVote = parseInt(vote);
			}
		}

		const voteLabel = ["", "Aprovado", "Rejeitado", "Modificação Necessária", "Abstenção"][
			majorityVote
		];

		// Montar resposta consolidada
		let consolidated = `## Resultado do Consenso\n\n`;
		consolidated += `**Decisão:** ${voteLabel}\n`;
		consolidated += `**Votos:** Aprovar: ${voteCounts[1]} | Rejeitar: ${voteCounts[2]} | Modificar: ${voteCounts[3]} | Abster: ${voteCounts[4]}\n\n`;

		consolidated += `### Votos dos Especialistas\n\n`;
		for (const resp of responses) {
			consolidated += `**${resp.agentName}:** ${resp.voteLabel}\n`;
		}

		consolidated += `\n### Justificativas\n\n`;
		for (const resp of responses) {
			consolidated += `**${resp.agentName}:** ${resp.output}\n\n`;
		}

		return consolidated;
	}

	/**
	 * Atualiza estatísticas
	 */
	updateStats(collaboration, success) {
		this.stats.totalCollaborations++;

		if (success) {
			this.stats.successfulCollaborations++;
		} else {
			this.stats.failedCollaborations++;
		}

		// Atualizar tempo médio de resposta
		const totalTime = this.stats.avgResponseTime * (this.stats.totalCollaborations - 1);
		this.stats.avgResponseTime =
			(totalTime + collaboration.duration) / this.stats.totalCollaborations;

		// Atualizar estatísticas por tipo de workflow
		const workflowType = collaboration.workflow.type;
		if (!this.stats.byWorkflowType[workflowType]) {
			this.stats.byWorkflowType[workflowType] = {
				total: 0,
				successful: 0,
				failed: 0
			};
		}

		this.stats.byWorkflowType[workflowType].total++;
		if (success) {
			this.stats.byWorkflowType[workflowType].successful++;
		} else {
			this.stats.byWorkflowType[workflowType].failed++;
		}
	}

	/**
	 * Adiciona ao histórico
	 */
	addToHistory(collaboration) {
		this.history.push({
			id: collaboration.id,
			workflowId: collaboration.workflowId,
			workflowName: collaboration.workflow.name,
			type: collaboration.workflow.type,
			query: collaboration.query,
			status: collaboration.status,
			duration: collaboration.duration,
			agents: collaboration.agents,
			startTime: collaboration.startTime,
			endTime: collaboration.endTime
		});

		// Manter apenas os últimos N registros
		if (this.history.length > this.config.historyLimit) {
			this.history = this.history.slice(-this.config.historyLimit);
		}
	}

	/**
	 * Obtém lista de workflows disponíveis
	 * @returns {Array} - Lista de workflows
	 */
	listWorkflows() {
		return Array.from(this.workflows.values()).map((w) => ({
			id: w.id,
			name: w.name,
			description: w.description,
			type: w.type,
			agents: w.agents,
			timeout: w.timeout
		}));
	}

	/**
	 * Obtém detalhes de um workflow
	 * @param {string} workflowId - ID do workflow
	 * @returns {Object} - Detalhes do workflow
	 */
	getWorkflow(workflowId) {
		return this.workflows.get(workflowId) || null;
	}

	/**
	 * Obtém colaborações ativas
	 * @returns {Array} - Lista de colaborações ativas
	 */
	getActiveCollaborations() {
		return Array.from(this.activeCollaborations.values()).map((c) => ({
			id: c.id,
			workflowId: c.workflowId,
			workflowName: c.workflow.name,
			status: c.status,
			agents: c.agents,
			startTime: c.startTime,
			duration: Date.now() - c.startTime
		}));
	}

	/**
	 * Obtém histórico de colaborações
	 * @param {number} limit - Limite de registros
	 * @returns {Array} - Histórico
	 */
	getHistory(limit = 20) {
		return this.history.slice(-limit).reverse();
	}

	/**
	 * Obtém estatísticas
	 * @returns {Object} - Estatísticas
	 */
	getStats() {
		return {
			...this.stats,
			activeCollaborations: this.activeCollaborations.size,
			totalWorkflows: this.workflows.size
		};
	}

	/**
	 * Cancela uma colaboração ativa
	 * @param {string} collaborationId - ID da colaboração
	 * @returns {boolean} - Sucesso
	 */
	cancelCollaboration(collaborationId) {
		const collaboration = this.activeCollaborations.get(collaborationId);
		if (!collaboration) {
			return false;
		}

		collaboration.status = COLLABORATION_STATUS.FAILED;
		collaboration.error = "Cancelled by user";
		collaboration.endTime = Date.now();
		collaboration.duration = collaboration.endTime - collaboration.startTime;

		// Adicionar ao histórico
		this.addToHistory(collaboration);

		// Remover das colaborações ativas
		this.activeCollaborations.delete(collaborationId);

		logger.info(`[Collaboration] Cancelled: ${collaborationId}`);

		return true;
	}

	/**
	 * Reseta estatísticas
	 */
	resetStats() {
		this.stats = {
			totalCollaborations: 0,
			successfulCollaborations: 0,
			failedCollaborations: 0,
			avgResponseTime: 0,
			byWorkflowType: {}
		};
		logger.debug("[Collaboration] Stats reset");
	}
}

// Singleton
AgentCollaboration.instance = null;

module.exports = AgentCollaboration;
