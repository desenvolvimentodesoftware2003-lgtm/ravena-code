/**
 * AgentCommands.js
 *
 * Comandos para gerenciamento e uso de agentes.
 *
 * Comandos disponíveis:
 *   !agent <nome>       - Ativa um agente para o grupo
 *   !agent-list         - Lista todos os agentes disponíveis
 *   !agent-reset        - Reseta para o agente padrão (ravena)
 *   !agent-info         - Mostra informações do agente ativo
 *   !agent-stats        - Mostra estatísticas de uso
 *   !delegate <agente> <pergunta> - Delega para outro agente
 *   !delegation         - Gerencia delegação automática
 *   !collab <workflow> <pergunta> - Executa colaboração entre agentes
 *   !collab-list        - Lista workflows disponíveis
 *   !memory             - Gerencia memória de contexto
 *   !dashboard          - Mostra dashboard de métricas
 *   !workflow           - Gerencia workflows de estado
 *   !autonomy           - Gerencia autonomia de agentes
 *   !learning           - Gerencia aprendizado de agentes
 *   !permissions        - Gerencia permissões
 *
 * Nível 4 - IA Autônoma, Aprendizado e Permissões
 */

"use strict";

const Logger = require("../utils/Logger");
const Command = require("../models/Command");
const ReturnMessage = require("../models/ReturnMessage");
const AgentRouter = require("../agents/AgentRouter");
const { listAgents, getAgent, agentExists, DEFAULT_AGENT } = require("../agents/AgentConfig");
const AgentDelegator = require("../agents/AgentDelegator");
const AgentCollaboration = require("../agents/AgentCollaboration");
const AgentMemory = require("../agents/AgentMemory");
const AgentStateMachine = require("../agents/AgentStateMachine");
const AgentMetrics = require("../agents/AgentMetrics");
const AgentAutonomy = require("../agents/AgentAutonomy");
const AgentLearning = require("../agents/AgentLearning");
const AgentPermissions = require("../agents/AgentPermissions");

const logger = new Logger("agent-commands");
const agentRouter = AgentRouter.getInstance();
const delegator = AgentDelegator.getInstance();
const collaboration = AgentCollaboration.getInstance();
const memory = AgentMemory.getInstance();
const stateMachine = AgentStateMachine.getInstance();
const metrics = AgentMetrics.getInstance();
const autonomy = AgentAutonomy.getInstance();
const learning = AgentLearning.getInstance();
const permissions = AgentPermissions.getInstance();

/**
 * Comando !agent - Ativa um agente para o grupo
 * @param {Object} bot - Instância do bot
 * @param {Object} message - Dados da mensagem
 * @param {Array} args - Argumentos do comando
 * @param {Object} group - Dados do grupo
 * @returns {Promise<ReturnMessage>}
 */
async function handleAgent(bot, message, args, group) {
	const chatId = message.group ?? message.author;

	// Verifica se é admin (apenas admins podem mudar o agente)
	if (message.group) {
		const isAdmin = group && (group.admins || []).includes(message.author);
		const isSuperAdmin = (process.env.SUPER_ADMINS || "").includes(message.author);

		if (!isAdmin && !isSuperAdmin) {
			return new ReturnMessage({
				chatId,
				content: "❌ Apenas administradores podem alterar o agente do grupo.",
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		}
	}

	// Sem argumentos: mostra agente ativo
	if (!args || args.length === 0) {
		const active = agentRouter.getActiveAgent(message.group);
		const agent = getAgent(active.agentId);

		return new ReturnMessage({
			chatId,
			content: `🤖 *Agente Ativo*\n\n${agent ? agent.emoji : "🤖"} *${active.agentName}*${active.isDefault ? " (padrão)" : ""}\n${agent ? agent.description : ""}`,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	const agentName = args[0].toLowerCase().replace("!", "");

	// Comando especial: reset
	if (agentName === "reset" || agentName === "default") {
		agentRouter.clearSession(message.group);
		return new ReturnMessage({
			chatId,
			content: `✅ Agente resetado para o padrão: 🤖 *Ravena*`,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	// Verifica se o agente existe
	if (!agentExists(agentName)) {
		const agentList = listAgents()
			.map((a) => `${a.emoji} *${a.id}* - ${a.description}`)
			.join("\n");

		return new ReturnMessage({
			chatId,
			content: `❌ Agente "${agentName}" não encontrado.\n\n*Agentes disponíveis:*\n${agentList}`,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	// Ativa o agente
	agentRouter.setSessionAgent(message.group, agentName);
	const agent = getAgent(agentName);

	return new ReturnMessage({
		chatId,
		content: `✅ *Agente Ativado!*\n\n${agent.emoji} *${agent.name}*\n${agent.description}\n\n_Agora todas as perguntas serão direcionadas a este agente._\n_Use *!agent reset* para voltar ao padrão._`,
		options: {
			quotedMessageId: message.origin.id._serialized,
			goReply: message.origin
		}
	});
}

/**
 * Comando !agent-list - Lista todos os agentes disponíveis
 * @param {Object} bot - Instância do bot
 * @param {Object} message - Dados da mensagem
 * @param {Array} args - Argumentos do comando
 * @param {Object} group - Dados do grupo
 * @returns {Promise<ReturnMessage>}
 */
async function handleAgentList(bot, message, args, group) {
	const chatId = message.group ?? message.author;
	const agents = agentRouter.getAvailableAgents();

	const active = agentRouter.getActiveAgent(message.group);

	let content = "🤖 *Agentes Disponíveis*\n\n";

	agents.forEach((agent) => {
		const isActive = agent.id === active.agentId;
		const status = isActive ? " ✅ (ativo)" : "";
		const stats = agent.stats;

		content += `${agent.emoji} *${agent.id}*${status}\n`;
		content += `   ${agent.description}\n`;
		content += `   Comandos: ${agent.commands.map((c) => `!${c}`).join(", ")}\n`;
		if (stats.requests > 0) {
			content += `   📊 ${stats.requests} usos | ${Math.round(stats.avgResponseTime)}ms média\n`;
		}
		content += "\n";
	});

	content += `_Use *!agent <nome>* para ativar um agente._`;

	return new ReturnMessage({
		chatId,
		content,
		options: {
			quotedMessageId: message.origin.id._serialized,
			goReply: message.origin
		}
	});
}

/**
 * Comando !agent-info - Mostra informações detalhadas do agente ativo
 * @param {Object} bot - Instância do bot
 * @param {Object} message - Dados da mensagem
 * @param {Array} args - Argumentos do comando
 * @param {Object} group - Dados do grupo
 * @returns {Promise<ReturnMessage>}
 */
async function handleAgentInfo(bot, message, args, group) {
	const chatId = message.group ?? message.author;

	// Se passou argumento, mostra info de um agente específico
	const agentId = args && args.length > 0 ? args[0].toLowerCase().replace("!", "") : null;

	if (agentId && agentExists(agentId)) {
		const agent = getAgent(agentId);
		const stats = agentRouter.getAgentStats(agentId);

		let content = `${agent.emoji} *${agent.name}*\n\n`;
		content += `📝 *Descrição:* ${agent.description}\n`;
		content += `🗄️ *Workspace:* ${agent.workspace}\n`;
		content += `⚡ *Prioridade:* ${agent.priority}\n`;
		content += `🌡️ *Temperatura:* ${agent.temperature}\n`;
		content += `📏 *Max Tokens:* ${agent.maxTokens}\n`;
		content += `📋 *Comandos:* ${agent.commands.map((c) => `!${c}`).join(", ")}\n`;

		if (stats) {
			content += `\n📊 *Estatísticas:*\n`;
			content += `   Total de requisições: ${stats.requests}\n`;
			content += `   Erros: ${stats.errors}\n`;
			content += `   Tempo médio: ${Math.round(stats.avgResponseTime)}ms\n`;
		}

		return new ReturnMessage({
			chatId,
			content,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	// Info do agente ativo
	const active = agentRouter.getActiveAgent(message.group);
	const agent = getAgent(active.agentId);

	if (!agent) {
		return new ReturnMessage({
			chatId,
			content: "❌ Nenhum agente ativo.",
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	const stats = agentRouter.getAgentStats(active.agentId);

	let content = `${agent.emoji} *${agent.name}*${active.isDefault ? " (padrão)" : ""}\n\n`;
	content += `📝 *Descrição:* ${agent.description}\n`;
	content += `🗄️ *Workspace:* ${agent.workspace}\n`;
	content += `⚡ *Prioridade:* ${agent.priority}\n`;
	content += `🌡️ *Temperatura:* ${agent.temperature}\n`;
	content += `📏 *Max Tokens:* ${agent.maxTokens}\n`;
	content += `📋 *Comandos:* ${agent.commands.map((c) => `!${c}`).join(", ")}\n`;

	if (stats) {
		content += `\n📊 *Estatísticas deste grupo:*\n`;
		content += `   Total de requisições: ${stats.requests}\n`;
		content += `   Erros: ${stats.errors}\n`;
		content += `   Tempo médio: ${Math.round(stats.avgResponseTime)}ms\n`;
	}

	return new ReturnMessage({
		chatId,
		content,
		options: {
			quotedMessageId: message.origin.id._serialized,
			goReply: message.origin
		}
	});
}

/**
 * Comando !agent-stats - Mostra estatísticas gerais
 * @param {Object} bot - Instância do bot
 * @param {Object} message - Dados da mensagem
 * @param {Array} args - Argumentos do comando
 * @param {Object} group - Dados do grupo
 * @returns {Promise<ReturnMessage>}
 */
async function handleAgentStats(bot, message, args, group) {
	const chatId = message.group ?? message.author;
	const stats = agentRouter.getStats();

	let content = "📊 *Estatísticas do Orquestrador de Agentes*\n\n";

	content += `📈 *Total de requisições:* ${stats.totalRequests}\n`;
	content += `❌ *Total de erros:* ${stats.errors}\n`;
	content += `🔗 *Sessões ativas:* ${stats.sessions}\n`;
	content += `💾 *Cache:* ${stats.cacheSize} entradas\n\n`;

	content += `*Por Agente:*\n`;
	Object.entries(stats.byAgent).forEach(([id, agentStats]) => {
		const agent = getAgent(id);
		const emoji = agent ? agent.emoji : "❓";
		const name = agent ? agent.name : id;
		content += `${emoji} *${name}:* ${agentStats.requests} usos | ${agentStats.errors} erros | ${Math.round(agentStats.avgResponseTime)}ms média\n`;
	});

	if (Object.keys(stats.byGroup).length > 0) {
		content += `\n*Por Grupo (Top 5):*\n`;
		const sortedGroups = Object.entries(stats.byGroup)
			.sort((a, b) => b[1].requests - a[1].requests)
			.slice(0, 5);

		sortedGroups.forEach(([id, groupStats]) => {
			content += `   ${id.substring(0, 15)}...: ${groupStats.requests} msgs | último: ${groupStats.lastAgent || "N/A"}\n`;
		});
	}

	return new ReturnMessage({
		chatId,
		content,
		options: {
			quotedMessageId: message.origin.id._serialized,
			goReply: message.origin
		}
	});
}

/**
 * Função auxiliar para processar mensagens com agentes
 * Chamada pelo AnythingLLMHelper ou CommandHandler
 * @param {Object} bot - Instância do bot
 * @param {Object} message - Dados da mensagem
 * @param {string} query - Pergunta do usuário
 * @param {string} agentName - Nome do agente (opcional)
 * @returns {Promise<ReturnMessage>}
 */
async function processWithAgent(bot, message, query, agentName = null) {
	const chatId = message.group ?? message.author;

	try {
		const LLMService = require("../services/LLMService");
		const llmService = LLMService.getInstance();

		const result = await agentRouter.route({
			query,
			groupId: message.group,
			agentName,
			llmService,
			context: {
				groupName: message.groupName,
				authorName: message.authorName
			}
		});

		const agent = getAgent(result.agentId);
		const cacheInfo = result.fromCache ? " (cacheado)" : "";

		return new ReturnMessage({
			chatId,
			content: `${agent ? agent.emoji : "🤖"} *${agent ? agent.name : "AI"}*${cacheInfo}\n\n${result.response}`,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin,
				delay: 1000
			}
		});
	} catch (error) {
		logger.error(`[processWithAgent] Erro ao processar com agente:`, error);

		return new ReturnMessage({
			chatId,
			content: `❌ Erro ao processar com agente: ${error.message}`,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}
}

/**
 * Comando !delegate - Delega uma pergunta para outro agente
 * @param {Object} bot - Instância do bot
 * @param {Object} message - Dados da mensagem
 * @param {Array} args - Argumentos do comando
 * @param {Object} group - Dados do grupo
 * @returns {Promise<ReturnMessage>}
 */
async function handleDelegate(bot, message, args, group) {
	const chatId = message.group ?? message.author;

	// Verificar argumentos
	if (!args || args.length < 2) {
		return new ReturnMessage({
			chatId,
			content: "❓ Uso: !delegate <agente> <pergunta>\n\nExemplo: !dev Como criar uma API?",
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	const agentName = args[0].toLowerCase().replace("!", "");
	const query = args.slice(1).join(" ");

	// Verificar se o agente existe
	if (!agentExists(agentName)) {
		const agentList = listAgents()
			.map((a) => `${a.emoji} *${a.id}*`)
			.join("\n");

		return new ReturnMessage({
			chatId,
			content: `❌ Agente "${agentName}" não encontrado.\n\n*Agentes disponíveis:*\n${agentList}`,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	try {
		const LLMService = require("../services/LLMService");
		const llmService = LLMService.getInstance();

		const result = await agentRouter.routeWithDelegation({
			query,
			groupId: message.group,
			targetAgent: agentName,
			llmService,
			context: {
				groupName: message.groupName,
				authorName: message.authorName
			}
		});

		const agent = getAgent(result.delegatedTo);

		return new ReturnMessage({
			chatId,
			content: `${agent ? agent.emoji : "🤖"} *${agent ? agent.name : agentName}* (delegado)\n\n${result.response}`,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin,
				delay: 1000
			}
		});
	} catch (error) {
		logger.error(`[handleDelegate] Erro ao delegar:`, error);

		return new ReturnMessage({
			chatId,
			content: `❌ Erro ao delegar para o agente: ${error.message}`,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}
}

/**
 * Comando !delegation - Gerencia delegação automática
 * @param {Object} bot - Instância do bot
 * @param {Object} message - Dados da mensagem
 * @param {Array} args - Argumentos do comando
 * @param {Object} group - Dados do grupo
 * @returns {Promise<ReturnMessage>}
 */
async function handleDelegation(bot, message, args, group) {
	const chatId = message.group ?? message.author;

	// Sem argumentos: mostra status
	if (!args || args.length === 0) {
		const stats = delegator.getStats();
		const enabled = agentRouter.delegationConfig.enabled;

		let content = "🔄 *Status da Delegação*\n\n";
		content += `*Estado:* ${enabled ? "✅ Ativada" : "❌ Desativada"}\n`;
		content += `*Confiança mínima:* ${agentRouter.delegationConfig.minConfidence}%\n\n`;

		content += `*Estatísticas:*\n`;
		content += `   Total de delegações: ${stats.totalDelegations}\n`;
		content += `   Delegações com falha: ${stats.failedDelegations}\n`;
		content += `   Cache hits: ${stats.cacheHits}\n`;
		content += `   Cache misses: ${stats.cacheMisses}\n`;
		content += `   Taxa de acerto do cache: ${stats.cacheHitRate}%\n\n`;

		content += `*Por Agente:*\n`;
		Object.entries(stats.delegationsByAgent).forEach(([agentId, count]) => {
			const agent = getAgent(agentId);
			const emoji = agent ? agent.emoji : "❓";
			content += `   ${emoji} *${agentId}:* ${count} delegações\n`;
		});

		content += `\n_Use !delegation on/off para ativar/desativar._`;

		return new ReturnMessage({
			chatId,
			content,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	// Comando: on/off
	const action = args[0].toLowerCase();

	if (action === "on" || action === "enable" || action === "ativar") {
		agentRouter.delegationConfig.enabled = true;
		delegator.setEnabled(true);

		return new ReturnMessage({
			chatId,
			content:
				"✅ *Delegação Automática Ativada*\n\nAgora o Ravena pode delegar automaticamente para agentes especializados quando detectar uma pergunta relevante.",
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	if (action === "off" || action === "disable" || action === "desativar") {
		agentRouter.delegationConfig.enabled = false;
		delegator.setEnabled(false);

		return new ReturnMessage({
			chatId,
			content:
				"❌ *Delegação Automática Desativada*\n\nAs perguntas serão processadas apenas pelo agente ativo.",
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	if (action === "reset") {
		delegator.resetStats();
		delegator.clearCache();

		return new ReturnMessage({
			chatId,
			content: "🔄 *Estatísticas de Delegação Resetadas*",
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	return new ReturnMessage({
		chatId,
		content: "❓ Uso: !delegation [on|off|reset]",
		options: {
			quotedMessageId: message.origin.id._serialized,
			goReply: message.origin
		}
	});
}

/**
 * Comando !collab - Executa colaboração entre agentes
 * @param {Object} bot - Instância do bot
 * @param {Object} message - Dados da mensagem
 * @param {Array} args - Argumentos do comando
 * @param {Object} group - Dados do grupo
 * @returns {Promise<ReturnMessage>}
 */
async function handleCollab(bot, message, args, group) {
	const chatId = message.group ?? message.author;

	// Verificar argumentos
	if (!args || args.length < 2) {
		return new ReturnMessage({
			chatId,
			content:
				"❓ Uso: !collab <workflow> <pergunta>\n\nExemplo: !collab full-analysis Como melhorar a segurança da minha API?",
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	const workflowId = args[0].toLowerCase();
	const query = args.slice(1).join(" ");

	// Verificar se o workflow existe
	const workflow = collaboration.getWorkflow(workflowId);
	if (!workflow) {
		const workflows = collaboration.listWorkflows();
		let content = `❌ Workflow "${workflowId}" não encontrado.\n\n*Workflows disponíveis:*\n`;

		workflows.forEach((w) => {
			content += `\n🔹 *${w.id}* - ${w.name}\n`;
			content += `   ${w.description}\n`;
			content += `   Agentes: ${w.agents.map((a) => getAgent(a)?.emoji || a).join(" ")}\n`;
		});

		return new ReturnMessage({
			chatId,
			content,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	try {
		const LLMService = require("../services/LLMService");
		const llmService = LLMService.getInstance();

		// Enviar mensagem de carregamento
		const loadingMsg = new ReturnMessage({
			chatId,
			content: `🔄 *Iniciando Colaboração*\n\nWorkflow: *${workflow.name}*\nAgentes: ${workflow.agents.map((a) => getAgent(a)?.emoji || a).join(" ")}\n\nAguarde, isso pode levar alguns minutos...`,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});

		// Enviar mensagem de carregamento
		if (bot.sendMessage) {
			await bot.sendMessage(chatId, loadingMsg.content, {
				quotedMessageId: message.origin.id._serialized
			});
		}

		const result = await agentRouter.routeCollaboration({
			workflowId,
			query,
			groupId: message.group,
			llmService,
			context: {
				groupName: message.groupName,
				authorName: message.authorName
			}
		});

		let content = `✅ *Colaboração Concluída*\n\n`;
		content += `📋 *Workflow:* ${result.workflow}\n`;
		content += `⏱️ *Tempo:* ${result.duration}ms\n`;
		content += `👥 *Agentes:* ${result.agents.map((a) => getAgent(a)?.emoji || a).join(" ")}\n\n`;
		content += `---\n\n`;
		content += result.result;

		return new ReturnMessage({
			chatId,
			content,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin,
				delay: 2000
			}
		});
	} catch (error) {
		logger.error(`[handleCollab] Erro na colaboração:`, error);

		return new ReturnMessage({
			chatId,
			content: `❌ Erro ao executar colaboração: ${error.message}`,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}
}

/**
 * Comando !collab-list - Lista workflows disponíveis
 * @param {Object} bot - Instância do bot
 * @param {Object} message - Dados da mensagem
 * @param {Array} args - Argumentos do comando
 * @param {Object} group - Dados do grupo
 * @returns {Promise<ReturnMessage>}
 */
async function handleCollabList(bot, message, args, group) {
	const chatId = message.group ?? message.author;
	const workflows = collaboration.listWorkflows();
	const stats = collaboration.getStats();

	let content = "🤝 *Workflows de Colaboração*\n\n";

	workflows.forEach((w) => {
		const typeEmoji = {
			sequential: "➡️",
			parallel: "⚡",
			pipeline: "🔄",
			consensus: "🗳️"
		};

		content += `🔹 *${w.id}* - ${w.name}\n`;
		content += `   ${w.description}\n`;
		content += `   Tipo: ${typeEmoji[w.type] || "❓"} ${w.type}\n`;
		content += `   Agentes: ${w.agents.map((a) => getAgent(a)?.emoji || a).join(" ")}\n`;
		content += `   Timeout: ${w.timeout / 1000}s\n\n`;
	});

	content += `📊 *Estatísticas:*\n`;
	content += `   Total de colaborações: ${stats.totalCollaborations}\n`;
	content += `   Sucesso: ${stats.successfulCollaborations}\n`;
	content += `   Falhas: ${stats.failedCollaborations}\n`;
	content += `   Tempo médio: ${Math.round(stats.avgResponseTime)}ms\n\n`;

	content += `_Use !collab <workflow> <pergunta> para iniciar uma colaboração._`;

	return new ReturnMessage({
		chatId,
		content,
		options: {
			quotedMessageId: message.origin.id._serialized,
			goReply: message.origin
		}
	});
}

/**
 * Comando !memory - Gerencia memória de contexto
 * @param {Object} bot - Instância do bot
 * @param {Object} message - Dados da mensagem
 * @param {Array} args - Argumentos do comando
 * @param {Object} group - Dados do grupo
 * @returns {Promise<ReturnMessage>}
 */
async function handleMemory(bot, message, args, group) {
	const chatId = message.group ?? message.author;

	// Sem argumentos: mostra status
	if (!args || args.length === 0) {
		const stats = memory.getStats();
		const memoryInfo = memory.getMemoryInfo(message.group, DEFAULT_AGENT);

		let content = "🧠 *Status da Memória*\n\n";

		content += `*Tamanhos:*\n`;
		content += `   Curto prazo: ${memoryInfo.shortTerm.size}/${memoryInfo.shortTerm.maxSize}\n`;
		content += `   Longo prazo: ${memoryInfo.longTerm.size}/${memoryInfo.longTerm.maxSize}\n`;
		content += `   Episódica: ${memoryInfo.episodic.size}/${memoryInfo.episodic.maxSize}\n`;
		content += `   Semântica: ${memoryInfo.semantic.size}/${memoryInfo.semantic.maxSize}\n\n`;

		content += `*Estatísticas:*\n`;
		content += `   Total de memórias: ${stats.totalMemories}\n`;
		content += `   Hits curto prazo: ${stats.shortTermHits}\n`;
		content += `   Hits longo prazo: ${stats.longTermHits}\n`;
		content += `   Memórias criadas: ${stats.memoriesCreated}\n`;
		content += `   Memórias removidas: ${stats.memoriesEvicted}\n\n`;

		content += `_Use !memory clear para limpar a memória._`;

		return new ReturnMessage({
			chatId,
			content,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	const action = args[0].toLowerCase();

	if (action === "clear" || action === "limpar") {
		memory.clearMemory(message.group);
		return new ReturnMessage({
			chatId,
			content: "🧠 *Memória Limpa*\n\nToda a memória de contexto deste grupo foi removida.",
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	if (action === "info") {
		const agentId = args[1] || DEFAULT_AGENT;
		const memoryInfo = memory.getMemoryInfo(message.group, agentId);
		const agent = getAgent(agentId);

		let content = `🧠 *Informações de Memória*\n\n`;
		content += `Agente: ${agent ? `${agent.emoji} ${agent.name}` : agentId}\n\n`;

		content += `*Curto Prazo:*\n`;
		content += `   Tamanho atual: ${memoryInfo.shortTerm.size}\n`;
		content += `   Máximo: ${memoryInfo.shortTerm.maxSize}\n\n`;

		content += `*Longo Prazo:*\n`;
		content += `   Tamanho atual: ${memoryInfo.longTerm.size}\n`;
		content += `   Máximo: ${memoryInfo.longTerm.maxSize}\n\n`;

		return new ReturnMessage({
			chatId,
			content,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	return new ReturnMessage({
		chatId,
		content: "❓ Uso: !memory [clear|info [agente]]",
		options: {
			quotedMessageId: message.origin.id._serialized,
			goReply: message.origin
		}
	});
}

/**
 * Comando !dashboard - Mostra dashboard de métricas
 * @param {Object} bot - Instância do bot
 * @param {Object} message - Dados da mensagem
 * @param {Array} args - Argumentos do comando
 * @param {Object} group - Dados do grupo
 * @returns {Promise<ReturnMessage>}
 */
async function handleDashboard(bot, message, args, group) {
	const chatId = message.group ?? message.author;

	const dashboard = metrics.getDashboard();

	return new ReturnMessage({
		chatId,
		content: dashboard,
		options: {
			quotedMessageId: message.origin.id._serialized,
			goReply: message.origin,
			delay: 1000
		}
	});
}

/**
 * Comando !workflow - Gerencia workflows de estado
 * @param {Object} bot - Instância do bot
 * @param {Object} message - Dados da mensagem
 * @param {Array} args - Argumentos do comando
 * @param {Object} group - Dados do grupo
 * @returns {Promise<ReturnMessage>}
 */
async function handleWorkflow(bot, message, args, group) {
	const chatId = message.group ?? message.author;

	// Sem argumentos: lista workflows
	if (!args || args.length === 0) {
		const workflows = stateMachine.listWorkflows();
		const instances = stateMachine.listInstances();
		const stats = stateMachine.getStats();

		let content = "⚙️ *Workflows de Estado*\n\n";

		content += `*Workflows Disponíveis:*\n`;
		workflows.forEach((w) => {
			content += `\n🔹 *${w.id}* - ${w.name}\n`;
			content += `   ${w.description}\n`;
			content += `   Estados: ${w.states.length} | Transições: ${w.transitions}\n`;
		});

		if (instances.length > 0) {
			content += `\n*Instâncias Ativas:*\n`;
			instances.forEach((i) => {
				const statusEmoji = {
					running: "▶️",
					paused: "⏸️",
					completed: "✅",
					failed: "❌",
					waiting: "⏳"
				};

				content += `\n${statusEmoji[i.status] || "❓"} *${i.id}*\n`;
				content += `   Workflow: ${i.workflowName}\n`;
				content += `   Estado: ${i.currentState}\n`;
				content += `   Duração: ${i.duration}ms\n`;
			});
		}

		content += `\n📊 *Estatísticas:*\n`;
		content += `   Instâncias criadas: ${stats.totalInstances}\n`;
		content += `   Concluídas: ${stats.completedInstances}\n`;
		content += `   Falhas: ${stats.failedInstances}\n`;
		content += `   Tempo médio: ${Math.round(stats.avgExecutionTime)}ms\n`;

		return new ReturnMessage({
			chatId,
			content,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	const action = args[0].toLowerCase();

	if (action === "create" || action === "criar") {
		const workflowId = args[1];
		if (!workflowId) {
			return new ReturnMessage({
				chatId,
				content: "❓ Uso: !workflow create <workflowId>",
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		}

		try {
			const instanceId = stateMachine.createInstance(workflowId, {
				groupId: message.group,
				authorName: message.authorName
			});

			return new ReturnMessage({
				chatId,
				content: `⚙️ *Instância Criada*\n\nID: ${instanceId}\nWorkflow: ${workflowId}`,
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		} catch (error) {
			return new ReturnMessage({
				chatId,
				content: `❌ Erro ao criar instância: ${error.message}`,
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		}
	}

	if (action === "run" || action === "executar") {
		const instanceId = args[1];
		if (!instanceId) {
			return new ReturnMessage({
				chatId,
				content: "❓ Uso: !workflow run <instanceId>",
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		}

		try {
			const result = await stateMachine.executeInstance(instanceId);

			return new ReturnMessage({
				chatId,
				content: `⚙️ *Instância Executada*\n\nID: ${instanceId}\nStatus: ${result.status}\nDuração: ${result.duration || 0}ms`,
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		} catch (error) {
			return new ReturnMessage({
				chatId,
				content: `❌ Erro ao executar instância: ${error.message}`,
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		}
	}

	return new ReturnMessage({
		chatId,
		content: "❓ Uso: !workflow [create|run] <id>",
		options: {
			quotedMessageId: message.origin.id._serialized,
			goReply: message.origin
		}
	});
}

// Lista de comandos usando a classe Command
const commands = [];

// Comando !agent (funciona tanto para definir quanto para ver)
commands.push(
	new Command({
		name: "agent",
		description: "Gerencia o agente ativo no grupo",
		category: "ia",
		usage: "!agent [nome|reset|info]",
		reactions: {
			before: process.env.LOADING_EMOJI ?? "⌛️",
			after: "🤖",
			error: "❌"
		},
		method: handleAgent
	})
);

// Comando !agent-list
commands.push(
	new Command({
		name: "agent-list",
		description: "Lista todos os agentes disponíveis",
		category: "ia",
		reactions: {
			before: process.env.LOADING_EMOJI ?? "⌛️",
			after: "📋"
		},
		method: handleAgentList
	})
);

// Comando !agent-info
commands.push(
	new Command({
		name: "agent-info",
		description: "Mostra informações do agente ativo ou de um agente específico",
		category: "ia",
		usage: "!agent-info [nome]",
		reactions: {
			before: process.env.LOADING_EMOJI ?? "⌛️",
			after: "ℹ️"
		},
		method: handleAgentInfo
	})
);

// Comando !agent-stats
commands.push(
	new Command({
		name: "agent-stats",
		description: "Mostra estatísticas de uso dos agentes",
		category: "ia",
		reactions: {
			before: process.env.LOADING_EMOJI ?? "⌛️",
			after: "📊"
		},
		method: handleAgentStats
	})
);

// Comando !delegate
commands.push(
	new Command({
		name: "delegate",
		description: "Delega uma pergunta para outro agente",
		category: "ia",
		usage: "!delegate <agente> <pergunta>",
		reactions: {
			before: process.env.LOADING_EMOJI ?? "⌛️",
			after: "🔄"
		},
		method: handleDelegate
	})
);

// Comando !delegation
commands.push(
	new Command({
		name: "delegation",
		description: "Gerencia delegação automática",
		category: "ia",
		usage: "!delegation [on|off|reset]",
		reactions: {
			before: process.env.LOADING_EMOJI ?? "⌛️",
			after: "🔄"
		},
		method: handleDelegation
	})
);

// Comando !collab
commands.push(
	new Command({
		name: "collab",
		description: "Executa colaboração entre agentes",
		category: "ia",
		usage: "!collab <workflow> <pergunta>",
		reactions: {
			before: process.env.LOADING_EMOJI ?? "⌛️",
			after: "🤝"
		},
		method: handleCollab
	})
);

// Comando !collab-list
commands.push(
	new Command({
		name: "collab-list",
		description: "Lista workflows de colaboração disponíveis",
		category: "ia",
		reactions: {
			before: process.env.LOADING_EMOJI ?? "⌛️",
			after: "📋"
		},
		method: handleCollabList
	})
);

// Comando !memory
commands.push(
	new Command({
		name: "memory",
		description: "Gerencia memória de contexto dos agentes",
		category: "ia",
		usage: "!memory [clear|info [agente]]",
		reactions: {
			before: process.env.LOADING_EMOJI ?? "⌛️",
			after: "🧠"
		},
		method: handleMemory
	})
);

// Comando !dashboard
commands.push(
	new Command({
		name: "dashboard",
		description: "Mostra dashboard de métricas dos agentes",
		category: "ia",
		reactions: {
			before: process.env.LOADING_EMOJI ?? "⌛️",
			after: "📊"
		},
		method: handleDashboard
	})
);

// Comando !workflow
commands.push(
	new Command({
		name: "workflow",
		description: "Gerencia workflows de estado",
		category: "ia",
		usage: "!workflow [create|run] <id>",
		reactions: {
			before: process.env.LOADING_EMOJI ?? "⌛️",
			after: "⚙️"
		},
		method: handleWorkflow
	})
);

/**
 * Comando !autonomy - Gerencia autonomia de agentes
 * @param {Object} bot - Instância do bot
 * @param {Object} message - Dados da mensagem
 * @param {Array} args - Argumentos do comando
 * @param {Object} group - Dados do grupo
 * @returns {Promise<ReturnMessage>}
 */
async function handleAutonomy(bot, message, args, group) {
	const chatId = message.group ?? message.author;

	// Verificar se é super admin
	const isSuperAdmin = (process.env.SUPER_ADMINS || "").includes(message.author);
	if (!isSuperAdmin) {
		return new ReturnMessage({
			chatId,
			content: "❌ Apenas super administradores podem gerenciar autonomia de agentes.",
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	// Sem argumentos: mostra status
	if (!args || args.length === 0) {
		const stats = autonomy.getStats();
		const pendingActions = autonomy.getPendingActions();

		let content = "🤖 *Autonomia de Agentes*\n\n";

		content += `*Status:*\n`;
		content += `   Total de ações: ${stats.totalActions}\n`;
		content += `   Ações aprovadas: ${stats.approvedActions}\n`;
		content += `   Ações rejeitadas: ${stats.rejectedActions}\n`;
		content += `   Ações com falha: ${stats.failedActions}\n`;
		content += `   Ações pendentes: ${pendingActions.length}\n\n`;

		if (pendingActions.length > 0) {
			content += `*Ações Pendentes:*\n`;
			pendingActions.slice(0, 5).forEach((action) => {
				content += `   • ${action.type} (${action.agentId})\n`;
			});
		}

		content += `\n_Use !autonomy level <agente> <0-4> para definir nível._`;

		return new ReturnMessage({
			chatId,
			content,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	const action = args[0].toLowerCase();

	if (action === "level") {
		const agentId = args[1];
		const level = parseInt(args[2]);

		if (!agentId || isNaN(level)) {
			return new ReturnMessage({
				chatId,
				content:
					"❓ Uso: !autonomy level <agente> <0-4>\n\n0: Sem autonomia\n1: Baixa\n2: Média\n3: Alta\n4: Total (perigoso!)",
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		}

		if (!agentExists(agentId)) {
			return new ReturnMessage({
				chatId,
				content: `❌ Agente "${agentId}" não encontrado.`,
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		}

		try {
			autonomy.setAutonomyLevel(agentId, level);
			const agent = getAgent(agentId);

			return new ReturnMessage({
				chatId,
				content: `✅ *Nível de Autonomia Definido*\n\n${agent.emoji} *${agent.name}*: Nível ${level}`,
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		} catch (error) {
			return new ReturnMessage({
				chatId,
				content: `❌ Erro ao definir nível: ${error.message}`,
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		}
	}

	if (action === "approve") {
		const actionId = args[1];
		if (!actionId) {
			return new ReturnMessage({
				chatId,
				content: "❓ Uso: !autonomy approve <actionId>",
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		}

		try {
			await autonomy.approveAction(actionId, message.author);
			return new ReturnMessage({
				chatId,
				content: `✅ *Ação Aprovada*\n\nID: ${actionId}`,
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		} catch (error) {
			return new ReturnMessage({
				chatId,
				content: `❌ Erro ao aprovar: ${error.message}`,
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		}
	}

	if (action === "reject") {
		const actionId = args[1];
		const reason = args.slice(2).join(" ");
		if (!actionId) {
			return new ReturnMessage({
				chatId,
				content: "❓ Uso: !autonomy reject <actionId> [motivo]",
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		}

		try {
			autonomy.rejectAction(actionId, message.author, reason);
			return new ReturnMessage({
				chatId,
				content: `❌ *Ação Rejeitada*\n\nID: ${actionId}`,
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		} catch (error) {
			return new ReturnMessage({
				chatId,
				content: `❌ Erro ao rejeitar: ${error.message}`,
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		}
	}

	return new ReturnMessage({
		chatId,
		content: "❓ Uso: !autonomy [level|approve|reject] <args>",
		options: {
			quotedMessageId: message.origin.id._serialized,
			goReply: message.origin
		}
	});
}

/**
 * Comando !learning - Gerencia aprendizado de agentes
 * @param {Object} bot - Instância do bot
 * @param {Object} message - Dados da mensagem
 * @param {Array} args - Argumentos do comando
 * @param {Object} group - Dados do grupo
 * @returns {Promise<ReturnMessage>}
 */
async function handleLearning(bot, message, args, group) {
	const chatId = message.group ?? message.author;

	// Sem argumentos: mostra status
	if (!args || args.length === 0) {
		const stats = learning.getStats();

		let content = "📚 *Aprendizado de Agentes*\n\n";

		content += `*Estatísticas:*\n`;
		content += `   Total de aprendizados: ${stats.totalLearnings}\n`;
		content += `   Padrões identificados: ${stats.patternsIdentified}\n`;
		content += `   Preferências aprendidas: ${stats.preferencesLearned}\n`;
		content += `   Correções aplicadas: ${stats.correctionsApplied}\n`;
		content += `   Feedback processado: ${stats.feedbackProcessed}\n`;
		content += `   Conhecimento adquirido: ${stats.knowledgeAcquired}\n\n`;

		content += `*Tamanhos:*\n`;
		content += `   Padrões: ${stats.patternsSize}\n`;
		content += `   Preferências: ${stats.preferencesSize}\n`;
		content += `   Correções: ${stats.correctionsSize}\n`;
		content += `   Feedback: ${stats.feedbackSize}\n`;
		content += `   Conhecimento: ${stats.knowledgeSize}\n`;

		return new ReturnMessage({
			chatId,
			content,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	const action = args[0].toLowerCase();

	if (action === "feedback") {
		const rating = parseInt(args[1]);
		const comment = args.slice(2).join(" ");

		if (isNaN(rating) || rating < 1 || rating > 5) {
			return new ReturnMessage({
				chatId,
				content: "❓ Uso: !learning feedback <1-5> [comentário]",
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		}

		const agentId = agentRouter.getActiveAgent(message.group).agentId;

		learning.learnFeedback(agentId, {
			rating,
			comment,
			userId: message.author,
			groupId: message.group,
			timestamp: Date.now()
		});

		return new ReturnMessage({
			chatId,
			content: `✅ *Feedback Registrado*\n\nNota: ${rating}/5\nAgente: ${agentId}`,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	if (action === "patterns") {
		const agentId = args[1] || agentRouter.getActiveAgent(message.group).agentId;
		const patterns = learning.getRelevantPatterns(agentId);

		let content = `📚 *Padrões de ${agentId}*\n\n`;

		if (patterns.length === 0) {
			content += "Nenhum padrão identificado ainda.";
		} else {
			patterns.slice(0, 10).forEach((p) => {
				content += `• ${p.type}: ${p.signature}\n`;
				content += `  Confiança: ${(p.confidence * 100).toFixed(0)}% | Ocorrências: ${p.occurrences}\n`;
			});
		}

		return new ReturnMessage({
			chatId,
			content,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	return new ReturnMessage({
		chatId,
		content: "❓ Uso: !learning [feedback|patterns] <args>",
		options: {
			quotedMessageId: message.origin.id._serialized,
			goReply: message.origin
		}
	});
}

/**
 * Comando !permissions - Gerencia permissões
 * @param {Object} bot - Instância do bot
 * @param {Object} message - Dados da mensagem
 * @param {Array} args - Argumentos do comando
 * @param {Object} group - Dados do grupo
 * @returns {Promise<ReturnMessage>}
 */
async function handlePermissions(bot, message, args, group) {
	const chatId = message.group ?? message.author;

	// Verificar se é admin
	const isAdmin = group && (group.admins || []).includes(message.author);
	const isSuperAdmin = (process.env.SUPER_ADMINS || "").includes(message.author);

	if (!isAdmin && !isSuperAdmin) {
		return new ReturnMessage({
			chatId,
			content: "❌ Apenas administradores podem gerenciar permissões.",
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	// Sem argumentos: mostra permissões do usuário
	if (!args || args.length === 0) {
		const userPerm = permissions.getUserPermissions(message.author);
		const effective = permissions.getEffectivePermissions(message.author, message.group);

		let content = "🔐 *Suas Permissões*\n\n";

		content += `*Papel:* ${effective.roleName}\n\n`;

		content += `*Permissões:*\n`;
		effective.permissions.forEach((perm) => {
			content += `   • ${perm.category}: ${perm.actions.join(", ")}\n`;
		});

		return new ReturnMessage({
			chatId,
			content,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	const action = args[0].toLowerCase();

	if (action === "roles") {
		const roles = permissions.listRoles();

		let content = "👥 *Papéis Disponíveis*\n\n";

		roles.forEach((role) => {
			content += `*${role.name}* (${role.id})\n`;
			content += `   ${role.description}\n`;
			content += `   Permissões: ${role.permissions.length} categorias\n\n`;
		});

		return new ReturnMessage({
			chatId,
			content,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	if (action === "check") {
		const category = args[1];
		const actionToCheck = args[2];

		if (!category || !actionToCheck) {
			return new ReturnMessage({
				chatId,
				content: "❓ Uso: !permissions check <categoria> <ação>",
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		}

		const result = permissions.checkPermission(message.author, category, actionToCheck);

		return new ReturnMessage({
			chatId,
			content: result.allowed
				? `✅ *Permissão Concedida*\n\nCategoria: ${category}\nAção: ${actionToCheck}`
				: `❌ *Permissão Negada*\n\nCategoria: ${category}\nAção: ${actionToCheck}\nMotivo: ${result.reason}`,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	if (action === "assign" && isSuperAdmin) {
		const userId = args[1];
		const roleId = args[2];

		if (!userId || !roleId) {
			return new ReturnMessage({
				chatId,
				content: "❓ Uso: !permissions assign <userId> <roleId>",
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		}

		try {
			permissions.assignRole(userId, roleId);
			return new ReturnMessage({
				chatId,
				content: `✅ *Papel Atribuído*\n\nUsuário: ${userId}\nPapel: ${roleId}`,
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		} catch (error) {
			return new ReturnMessage({
				chatId,
				content: `❌ Erro ao atribuir papel: ${error.message}`,
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		}
	}

	return new ReturnMessage({
		chatId,
		content: "❓ Uso: !permissions [roles|check|assign] <args>",
		options: {
			quotedMessageId: message.origin.id._serialized,
			goReply: message.origin
		}
	});
}

// Comando !autonomy
commands.push(
	new Command({
		name: "autonomy",
		description: "Gerencia autonomia de agentes",
		category: "ia",
		usage: "!autonomy [level|approve|reject] <args>",
		reactions: {
			before: process.env.LOADING_EMOJI ?? "⌛️",
			after: "🤖"
		},
		method: handleAutonomy
	})
);

// Comando !learning
commands.push(
	new Command({
		name: "learning",
		description: "Gerencia aprendizado de agentes",
		category: "ia",
		usage: "!learning [feedback|patterns] <args>",
		reactions: {
			before: process.env.LOADING_EMOJI ?? "⌛️",
			after: "📚"
		},
		method: handleLearning
	})
);

// Comando !permissions
commands.push(
	new Command({
		name: "permissions",
		description: "Gerencia permissões de agentes",
		category: "ia",
		usage: "!permissions [roles|check|assign] <args>",
		reactions: {
			before: process.env.LOADING_EMOJI ?? "⌛️",
			after: "🔐"
		},
		method: handlePermissions
	})
);

// Comandos diretos por agente (aliases)
// !dev <pergunta> → usa agente dev
// !busca <pergunta> → usa agente busca360
// !hack <pergunta> → usa agente hacker

const agentAliases = [
	{ name: "dev", agent: "dev", description: "Pergunta ao agente de programação" },
	{ name: "busca", agent: "busca360", description: "Busca com agente de pesquisa" },
	{ name: "hack", agent: "hacker", description: "Pergunta ao agente de segurança" }
];

agentAliases.forEach((alias) => {
	commands.push(
		new Command({
			name: alias.name,
			description: alias.description,
			category: "ia",
			usage: `!${alias.name} [pergunta]`,
			reactions: {
				before: process.env.LOADING_EMOJI ?? "⌛️",
				after: "💬"
			},
			method: async (bot, message, args, group) => {
				const query = args.join(" ");
				if (!query) {
					return new ReturnMessage({
						chatId: message.group ?? message.author,
						content: `❓ O que você quer perguntar ao agente *${alias.agent}*?`,
						options: {
							quotedMessageId: message.origin.id._serialized,
							goReply: message.origin
						}
					});
				}
				return await processWithAgent(bot, message, query, alias.agent);
			}
		})
	);
});

module.exports = {
	commands,
	handleAgent,
	handleAgentList,
	handleAgentInfo,
	handleAgentStats,
	handleDelegate,
	handleDelegation,
	handleCollab,
	handleCollabList,
	handleMemory,
	handleDashboard,
	handleWorkflow,
	handleAutonomy,
	handleLearning,
	handlePermissions,
	processWithAgent
};
