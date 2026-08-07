/**
 * AnythingLLMHelper.js
 *
 * Helper para interação com AnythingLLM com suporte a múltiplos agentes.
 *
 * Nível 2 - Comunicação Inter-Agentes
 * - Suporte a múltiplos workspaces (agentes)
 * - Integração com AgentRouter
 * - Delegação automática entre agentes
 * - Colaboração entre múltiplos agentes
 * - Fallback para workspace padrão
 */

const axios = require("axios");
const Logger = require("../utils/Logger");
const ReturnMessage = require("../models/ReturnMessage");
const Command = require("../models/Command");

const logger = new Logger("anythingllm-helper");

/**
 * Ask a question to AnythingLLM with specific workspace
 * @param {string} question - The question to ask
 * @param {string} sessionId - Optional session ID for context maintenance
 * @param {string} workspace - Workspace name (agent) to use
 * @param {Object} options - Additional options
 * @returns {Promise<string>} - The answer from AnythingLLM
 */
async function askAnythingLLM(question, sessionId = null, workspace = null, options = {}) {
	const host = process.env.ANYTHINGLLM_HOST;
	const apiKey = process.env.ANYTHINGLLM_API_KEY;

	// Se nenhum workspace foi especificado, usa o padrão
	if (!workspace) {
		workspace = process.env.ANYTHINGLLM_WORKSPACE || "ravena";
	}

	if (!host || !apiKey) {
		throw new Error("Configuração do AnythingLLM incompleta (host ou API key ausente).");
	}

	try {
		logger.debug(
			`[AnythingLLM] Sending question to workspace ${workspace} (Session: ${sessionId}): ${question}`
		);

		const payload = {
			message: question,
			mode: options.mode || "chat"
		};

		if (sessionId) {
			payload.sessionId = sessionId;
		}

		// Adiciona contexto do sistema se fornecido
		if (options.systemContext) {
			payload.systemContext = options.systemContext;
		}

		const response = await axios.post(`${host}/api/v1/workspace/${workspace}/chat`, payload, {
			headers: {
				Authorization: `Bearer ${apiKey}`,
				"Content-Type": "application/json"
			},
			timeout: options.timeout || 30000
		});

		let answer =
			response.data.textResponse ||
			response.data.text ||
			"Desculpe, não consegui obter uma resposta.";

		// Remover tags <think>...</think> (DeepSeek reasoning)
		// Regex case-insensitive e mais robusta (trata tags não fechadas)
		const thinkRegex = /<think>[\s\S]*?(?:<\/think>|$)/gi;
		if (thinkRegex.test(answer)) {
			answer = answer.replace(thinkRegex, "").trim();
		}

		return answer;
	} catch (error) {
		logger.error("Erro ao consultar AnythingLLM:", error.message);

		if (error.code === "ECONNREFUSED") {
			throw new Error("Não foi possível conectar ao servidor AnythingLLM (Conexão Recusada).");
		} else if (error.response?.status === 401 || error.response?.status === 403) {
			throw new Error("Erro de autenticação com a API do AnythingLLM.");
		} else if (error.response?.status === 404) {
			throw new Error(`Workspace '${workspace}' não encontrado no AnythingLLM.`);
		}
		throw error;
	}
}

/**
 * Ask a question using AgentRouter (roteamento automático)
 * @param {string} question - The question to ask
 * @param {string} groupId - Group ID for session management
 * @param {string} agentName - Specific agent to use (optional)
 * @param {Object} context - Additional context
 * @returns {Promise<Object>} - { response, agentId, responseTime }
 */
async function askWithAgent(question, groupId = null, agentName = null, context = {}) {
	const AgentRouter = require("../agents/AgentRouter");
	const agentRouter = AgentRouter.getInstance();

	// Cria uma instância mock do LLMService para usar com AnythingLLM
	const llmServiceMock = {
		getAnythingLLMCompletion: async (options) =>
			await askAnythingLLM(options.prompt, groupId, options.workspace, {
				systemContext: options.systemContext,
				timeout: options.timeout
			})
	};

	return await agentRouter.route({
		query: question,
		groupId,
		agentName,
		llmService: llmServiceMock,
		context
	});
}

/**
 * Handle AnythingLLM chat command
 * @param {Object} bot - Bot instance
 * @param {Object} message - Message object
 * @param {Array} args - Command arguments
 * @param {Object} group - Group data
 * @returns {Promise<ReturnMessage>} - Return message
 */
async function handleAjuda(bot, message, args, group) {
	const chatId = message.group ?? message.author;
	const question = args.length > 0 ? args.join(" ") : (message.caption ?? message.content);

	if (!question || question.trim().length < 2) {
		return new ReturnMessage({
			chatId,
			content: "O que você quer saber? Exemplo: !ajuda como adicionar comandos",
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}

	try {
		// Usa AgentRouter para rotear (agente padrão: ravena)
		const result = await askWithAgent(question, message.group, null, {
			groupName: message.groupName,
			authorName: message.authorName
		});

		const agentInfo = result.agentId ? ` (${result.agentId})` : "";

		return new ReturnMessage({
			chatId,
			content: `🤖 *Ajuda${agentInfo}*\n\n${result.response}`,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	} catch (error) {
		return new ReturnMessage({
			chatId,
			content: `❌ ${error.message}`,
			options: {
				quotedMessageId: message.origin.id._serialized,
				goReply: message.origin
			}
		});
	}
}

/**
 * Handle agent-specific chat command
 * @param {string} agentId - Agent ID to use
 * @returns {Function} - Command handler function
 */
function createAgentHandler(agentId) {
	return async function (bot, message, args, group) {
		const chatId = message.group ?? message.author;
		const question = args.length > 0 ? args.join(" ") : (message.caption ?? message.content);

		if (!question || question.trim().length < 2) {
			const { getAgent } = require("../agents/AgentConfig");
			const agent = getAgent(agentId);

			return new ReturnMessage({
				chatId,
				content: `❓ O que você quer perguntar ao agente *${agent ? agent.name : agentId}*?`,
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		}

		try {
			const result = await askWithAgent(question, message.group, agentId, {
				groupName: message.groupName,
				authorName: message.authorName
			});

			const { getAgent } = require("../agents/AgentConfig");
			const agent = getAgent(result.agentId);
			const emoji = agent ? agent.emoji : "🤖";
			const name = agent ? agent.name : result.agentId;
			const cacheInfo = result.fromCache ? " (cacheado)" : "";

			return new ReturnMessage({
				chatId,
				content: `${emoji} *${name}*${cacheInfo}\n\n${result.response}`,
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		} catch (error) {
			return new ReturnMessage({
				chatId,
				content: `❌ Erro ao processar: ${error.message}`,
				options: {
					quotedMessageId: message.origin.id._serialized,
					goReply: message.origin
				}
			});
		}
	};
}

// Define the commands
const commands = [];

// Comando !ajuda (usa agente padrão)
if (process.env.ANYTHINGLLM_API_KEY && process.env.ANYTHINGLLM_HOST) {
	commands.push(
		new Command({
			name: "ajuda",
			description: "Consulta a base de conhecimento no AnythingLLM",
			category: "geral",
			usage: "!ajuda [sua pergunta]",
			reactions: {
				before: process.env.LOADING_EMOJI ?? "⌛️",
				after: "🤖",
				error: "❌"
			},
			method: handleAjuda
		})
	);

	// Comandos de agentes específicos (aliases)
	// Estes são registrados apenas se o AnythingLLM estiver configurado
	const agentAliases = [
		{ name: "ai", agent: "ravena", description: "Pergunta à IA geral" },
		{ name: "ia", agent: "ravena", description: "Alias para !ai" },
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
				method: createAgentHandler(alias.agent)
			})
		);
	});
}

module.exports = {
	commands,
	handleAjuda,
	askAnythingLLM,
	askWithAgent,
	createAgentHandler
};
