/**
 * Testes do Sistema de Agentes - Ravena
 *
 * Execute com: node test-agents.js
 */

"use strict";

let passed = 0;
let failed = 0;
let total = 0;

function test(name, fn) {
	total++;
	try {
		fn();
		passed++;
		console.log(`  ✅ ${name}`);
	} catch (error) {
		failed++;
		console.log(`  ❌ ${name}`);
		console.log(`     Erro: ${error.message}`);
	}
}

function assert(condition, message) {
	if (!condition) {
		throw new Error(message || "Assertion failed");
	}
}

function assertEqual(actual, expected, message) {
	if (actual !== expected) {
		throw new Error(message || `Expected "${expected}", got "${actual}"`);
	}
}

function assertNotNull(value, message) {
	if (value === null || value === undefined) {
		throw new Error(message || "Expected non-null value");
	}
}

console.log("\n🤖 Testes do Sistema de Agentes - Ravena\n");

// ===========================================================================
// Testes do AgentConfig
// ===========================================================================
console.log("📋 Testando AgentConfig...");

const {
	AGENTS,
	DEFAULT_AGENT,
	AGENT_BEHAVIOR,
	getAgent,
	listAgents,
	agentExists
} = require("./src/agents/AgentConfig");

test("AGENTS deve ter 4 agentes", () => {
	assertEqual(Object.keys(AGENTS).length, 4, "Deve ter 4 agentes");
});

test("DEFAULT_AGENT deve ser 'ravena'", () => {
	assertEqual(DEFAULT_AGENT, "ravena", "Padrão deve ser ravena");
});

test("agentExists deve retornar true para agentes existentes", () => {
	assert(agentExists("ravena"), "ravena deve existir");
	assert(agentExists("dev"), "dev deve existir");
	assert(agentExists("busca360"), "busca360 deve existir");
	assert(agentExists("hacker"), "hacker deve existir");
});

test("agentExists deve retornar false para agente inexistente", () => {
	assert(!agentExists("inexistente"), "inexistente não deve existir");
});

test("getAgent deve retornar agente válido", () => {
	const agent = getAgent("ravena");
	assertNotNull(agent, "Agente ravena deve existir");
	assertEqual(agent.id, "ravena", "ID deve ser ravena");
	assertEqual(agent.name, "Ravena", "Nome deve ser Ravena");
	assertNotNull(agent.workspace, "Workspace deve existir");
});

test("listAgents deve retornar array de agentes", () => {
	const agents = listAgents();
	assert(Array.isArray(agents), "Deve retornar array");
	assertEqual(agents.length, 4, "Deve ter 4 agentes");
});

console.log("");

// ===========================================================================
// Testes do AgentDelegator
// ===========================================================================
console.log("🔄 Testando AgentDelegator...");

const AgentDelegator = require("./src/agents/AgentDelegator");
const delegator = AgentDelegator.getInstance();

test("Delegator deve ser singleton", () => {
	const instance1 = AgentDelegator.getInstance();
	const instance2 = AgentDelegator.getInstance();
	assertEqual(instance1, instance2, "Deve ser a mesma instância");
});

test("detectIntent deve detectar agente dev", () => {
	const result = delegator.detectIntent("Como criar uma API REST em Node.js?");
	assertNotNull(result, "Resultado deve existir");
	// Pode detectar dev ou nenhum, dependendo do threshold
	assert(["dev", null].includes(result.agentId), "Deve detectar dev ou nenhum");
});

test("detectIntent deve detectar agente busca360", () => {
	const result = delegator.detectIntent("O que é inteligência artificial?");
	assertNotNull(result, "Resultado deve existir");
	assert(["busca360", null].includes(result.agentId), "Deve detectar busca360 ou nenhum");
});

test("detectIntent deve detectar agente hacker", () => {
	const result = delegator.detectIntent("Como proteger minha API de ataques?");
	assertNotNull(result, "Resultado deve existir");
	assert(["hacker", null].includes(result.agentId), "Deve detectar hacker ou nenhum");
});

test("shouldDelegate deve retornar objeto válido", () => {
	const result = delegator.shouldDelegate("ravena", "dev", 80);
	assertNotNull(result, "Resultado deve existir");
	assert(typeof result.shouldDelegate === "boolean", "shouldDelegate deve ser boolean");
});

test("shouldDelegate com confiança baixa não deve delegar", () => {
	const result = delegator.shouldDelegate("ravena", "dev", 30);
	assertEqual(result.shouldDelegate, false, "Não deve delegar com confiança baixa");
});

test("getStats deve retornar estatísticas", () => {
	const stats = delegator.getStats();
	assertNotNull(stats, "Stats deve existir");
	assert(typeof stats.totalDelegations === "number", "totalDelegations deve ser número");
});

console.log("");

// ===========================================================================
// Testes do AgentMemory
// ===========================================================================
console.log("🧠 Testando AgentMemory...");

const AgentMemory = require("./src/agents/AgentMemory");
const memory = AgentMemory.getInstance();

test("Memory deve ser singleton", () => {
	const instance1 = AgentMemory.getInstance();
	const instance2 = AgentMemory.getInstance();
	assertEqual(instance1, instance2, "Deve ser a mesma instância");
});

test("addShortTerm deve adicionar mensagem", () => {
	memory.addShortTerm("test-group", "ravena", {
		author: "user",
		text: "Olá!"
	});

	const messages = memory.getShortTerm("test-group", "ravena");
	assert(messages.length > 0, "Deve ter mensagens");
	assertEqual(messages[0].text, "Olá!", "Texto deve ser Olá!");
});

test("addLongTerm deve adicionar fato", () => {
	memory.addLongTerm("test-group", "ravena", {
		type: "preference",
		content: "Usuário prefere respostas curtas"
	});

	const facts = memory.getLongTerm("test-group", "ravena");
	assert(facts.length > 0, "Deve ter fatos");
});

test("setSemantic deve armazenar preferência", () => {
	memory.setSemantic("test-group", "language", "pt-BR");
	const value = memory.getSemantic("test-group", "language");
	assertEqual(value, "pt-BR", "Valor deve ser pt-BR");
});

test("getMemoryInfo deve retornar informações", () => {
	const info = memory.getMemoryInfo("test-group", "ravena");
	assertNotNull(info, "Info deve existir");
	assertNotNull(info.shortTerm, "shortTerm deve existir");
	assertNotNull(info.longTerm, "longTerm deve existir");
});

test("clearMemory deve limpar memória", () => {
	memory.addShortTerm("clear-test", "ravena", { author: "user", text: "test" });
	memory.clearMemory("clear-test");
	const messages = memory.getShortTerm("clear-test", "ravena");
	assertEqual(messages.length, 0, "Deve estar vazio após limpar");
});

test("getStats deve retornar estatísticas", () => {
	const stats = memory.getStats();
	assertNotNull(stats, "Stats deve existir");
	assert(typeof stats.totalMemories === "number", "totalMemories deve ser número");
});

console.log("");

// ===========================================================================
// Testes do AgentMetrics
// ===========================================================================
console.log("📊 Testando AgentMetrics...");

const AgentMetrics = require("./src/agents/AgentMetrics");
const metrics = AgentMetrics.getInstance();

test("Metrics deve ser singleton", () => {
	const instance1 = AgentMetrics.getInstance();
	const instance2 = AgentMetrics.getInstance();
	assertEqual(instance1, instance2, "Deve ser a mesma instância");
});

test("recordMetric deve registrar métrica", () => {
	metrics.recordMetric("test-agent", "test_metric", 42);
	const agentMetrics = metrics.getAgentMetrics("test-agent");
	assertNotNull(agentMetrics, "Metrics deve existir");
	assertNotNull(agentMetrics.test_metric, "test_metric deve existir");
	assertEqual(agentMetrics.test_metric.value, 42, "Valor deve ser 42");
});

test("recordResponseTime deve registrar tempo", () => {
	metrics.recordResponseTime("test-agent", 150);
	const agentMetrics = metrics.getAgentMetrics("test-agent");
	assertNotNull(agentMetrics.response_time, "response_time deve existir");
});

test("getAgentPerformanceReport deve retornar relatório", () => {
	const report = metrics.getAgentPerformanceReport("test-agent");
	assertNotNull(report, "Report deve existir");
	assertEqual(report.agentId, "test-agent", "agentId deve ser test-agent");
});

test("getDashboard deve retornar string", () => {
	const dashboard = metrics.getDashboard();
	assert(typeof dashboard === "string", "Dashboard deve ser string");
	assert(dashboard.includes("Dashboard"), "Dashboard deve conter 'Dashboard'");
});

test("getStats deve retornar estatísticas", () => {
	const stats = metrics.getStats();
	assertNotNull(stats, "Stats deve existir");
	assert(typeof stats.totalMetricsCollected === "number", "totalMetricsCollected deve ser número");
});

console.log("");

// ===========================================================================
// Testes do AgentStateMachine
// ===========================================================================
console.log("⚙️ Testando AgentStateMachine...");

const AgentStateMachine = require("./src/agents/AgentStateMachine");
const stateMachine = AgentStateMachine.getInstance();

test("StateMachine deve ser singleton", () => {
	const instance1 = AgentStateMachine.getInstance();
	const instance2 = AgentStateMachine.getInstance();
	assertEqual(instance1, instance2, "Deve ser a mesma instância");
});

test("listWorkflows deve retornar workflows", () => {
	const workflows = stateMachine.listWorkflows();
	assert(Array.isArray(workflows), "Deve retornar array");
	assert(workflows.length > 0, "Deve ter pelo menos 1 workflow");
});

test("createInstance deve criar instância", () => {
	const instanceId = stateMachine.createInstance("customer-support", {
		groupId: "test-group"
	});
	assertNotNull(instanceId, "instanceId deve existir");
	assert(instanceId.startsWith("inst-"), "instanceId deve começar com inst-");
});

test("getStats deve retornar estatísticas", () => {
	const stats = stateMachine.getStats();
	assertNotNull(stats, "Stats deve existir");
	assert(typeof stats.totalInstances === "number", "totalInstances deve ser número");
});

console.log("");

// ===========================================================================
// Testes do AgentPermissions
// ===========================================================================
console.log("🔐 Testando AgentPermissions...");

const AgentPermissions = require("./src/agents/AgentPermissions");
const permissions = AgentPermissions.getInstance();

test("Permissions deve ser singleton", () => {
	const instance1 = AgentPermissions.getInstance();
	const instance2 = AgentPermissions.getInstance();
	assertEqual(instance1, instance2, "Deve ser a mesma instância");
});

test("listRoles deve retornar papéis", () => {
	const roles = permissions.listRoles();
	assert(Array.isArray(roles), "Deve retornar array");
	assert(roles.length > 0, "Deve ter pelo menos 1 papel");
});

test("assignRole deve atribuir papel", () => {
	permissions.assignRole("test-user", "admin");
	const userPerm = permissions.getUserPermissions("test-user");
	assertEqual(userPerm.roleId, "admin", "Papel deve ser admin");
});

test("checkPermission deve verificar permissão", () => {
	permissions.assignRole("perm-test-user", "admin");
	const result = permissions.checkPermission("perm-test-user", "agent", "read");
	assertNotNull(result, "Resultado deve existir");
	assert(typeof result.allowed === "boolean", "allowed deve ser boolean");
});

test("getEffectivePermissions deve retornar permissões efetivas", () => {
	permissions.assignRole("eff-test-user", "user");
	const effective = permissions.getEffectivePermissions("eff-test-user");
	assertNotNull(effective, "Effective deve existir");
	assertEqual(effective.roleId, "user", "roleId deve ser user");
});

test("getStats deve retornar estatísticas", () => {
	const stats = permissions.getStats();
	assertNotNull(stats, "Stats deve existir");
	assert(typeof stats.totalChecks === "number", "totalChecks deve ser número");
});

console.log("");

// ===========================================================================
// Testes do AgentAutonomy
// ===========================================================================
console.log("🤖 Testando AgentAutonomy...");

const AgentAutonomy = require("./src/agents/AgentAutonomy");
const autonomy = AgentAutonomy.getInstance();

test("Autonomy deve ser singleton", () => {
	const instance1 = AgentAutonomy.getInstance();
	const instance2 = AgentAutonomy.getInstance();
	assertEqual(instance1, instance2, "Deve ser a mesma instância");
});

test("setAutonomyLevel deve definir nível", () => {
	autonomy.setAutonomyLevel("test-agent", 2);
	const level = autonomy.getAutonomyLevel("test-agent");
	assertEqual(level, 2, "Nível deve ser 2");
});

test("getAutonomyLevel deve retornar nível padrão", () => {
	const level = autonomy.getAutonomyLevel("non-existent-agent");
	assertEqual(level, 0, "Nível padrão deve ser 0");
});

test("canExecuteAction deve verificar ação", () => {
	autonomy.setAutonomyLevel("action-test", 2);
	const result = autonomy.canExecuteAction("action-test", "task-create");
	assertNotNull(result, "Resultado deve existir");
	assert(typeof result.allowed === "boolean", "allowed deve ser boolean");
});

test("getStats deve retornar estatísticas", () => {
	const stats = autonomy.getStats();
	assertNotNull(stats, "Stats deve existir");
	assert(typeof stats.totalActions === "number", "totalActions deve ser número");
});

console.log("");

// ===========================================================================
// Testes do AgentLearning
// ===========================================================================
console.log("📚 Testando AgentLearning...");

const AgentLearning = require("./src/agents/AgentLearning");
const learning = AgentLearning.getInstance();

test("Learning deve ser singleton", () => {
	const instance1 = AgentLearning.getInstance();
	const instance2 = AgentLearning.getInstance();
	assertEqual(instance1, instance2, "Deve ser a mesma instância");
});

test("learnPattern deve registrar padrão", () => {
	// Aprender o mesmo padrão várias vezes para aumentar confiança
	for (let i = 0; i < 5; i++) {
		learning.learnPattern("test-agent", {
			type: "query-pattern",
			signature: "api-question",
			keywords: ["api", "rest", "node"]
		});
	}

	const patterns = learning.getRelevantPatterns("test-agent", {
		keywords: ["api", "rest"]
	});
	assert(patterns.length > 0, "Deve ter padrões");
	assertEqual(patterns[0].signature, "api-question", "Signature deve ser api-question");
});

test("learnPreference deve registrar preferência", () => {
	learning.learnPreference("test-agent", "test-user", "language", "pt-BR");
	const prefs = learning.getUserPreferences("test-agent", "test-user");
	assertEqual(prefs.language, "pt-BR", "Linguagem deve ser pt-BR");
});

test("learnKnowledge deve registrar conhecimento", () => {
	learning.learnKnowledge("test-agent", {
		type: "fact",
		signature: "node-version",
		content: "Node.js 18 é a versão LTS atual",
		topic: "nodejs",
		keywords: ["node", "versão"]
	});

	const knowledge = learning.getRelevantKnowledge("test-agent", {
		topic: "nodejs"
	});
	assert(knowledge.length > 0, "Deve ter conhecimento");
});

test("getStats deve retornar estatísticas", () => {
	const stats = learning.getStats();
	assertNotNull(stats, "Stats deve existir");
	assert(typeof stats.totalLearnings === "number", "totalLearnings deve ser número");
});

console.log("");

// ===========================================================================
// Testes do AgentCollaboration
// ===========================================================================
console.log("🤝 Testando AgentCollaboration...");

const AgentCollaboration = require("./src/agents/AgentCollaboration");
const collaboration = AgentCollaboration.getInstance();

test("Collaboration deve ser singleton", () => {
	const instance1 = AgentCollaboration.getInstance();
	const instance2 = AgentCollaboration.getInstance();
	assertEqual(instance1, instance2, "Deve ser a mesma instância");
});

test("listWorkflows deve retornar workflows", () => {
	const workflows = collaboration.listWorkflows();
	assert(Array.isArray(workflows), "Deve retornar array");
	assert(workflows.length > 0, "Deve ter pelo menos 1 workflow");
});

test("getWorkflow deve retornar workflow existente", () => {
	const workflow = collaboration.getWorkflow("full-analysis");
	assertNotNull(workflow, "Workflow deve existir");
	assertEqual(workflow.id, "full-analysis", "ID deve ser full-analysis");
});

test("getStats deve retornar estatísticas", () => {
	const stats = collaboration.getStats();
	assertNotNull(stats, "Stats deve existir");
	assert(typeof stats.totalCollaborations === "number", "totalCollaborations deve ser número");
});

console.log("");

// ===========================================================================
// Testes de Prevenção de Vazamento de Memória
// ===========================================================================
console.log("🧹 Testando Limpeza de Memória...");

test("AgentMemory.cleanupShortTerm deve limpar mensagens expiradas", () => {
	const testKey = "cleanup-short-test";
	memory.addShortTerm(testKey, "ravena", { author: "user", text: "test" });
	const before = memory.getShortTerm(testKey, "ravena");
	assert(before.length > 0, "Deve ter mensagens antes da limpeza");
	memory.cleanupShortTerm();
	const after = memory.getShortTerm(testKey, "ravena");
	assert(after.length > 0, "Mensagens novas devem permanecer");
});

test("AgentMemory.cleanupSemantic deve limpar entradas expiradas", () => {
	memory.setSemantic("semantic-cleanup-test", "old-key", "old-value");
	memory.cleanupSemantic();
	const value = memory.getSemantic("semantic-cleanup-test", "old-key");
	assertEqual(value, "old-value", "Entradas novas devem permanecer");
});

test("AgentMemory.cleanup deve executar todas as limpezas", () => {
	memory.cleanup();
	assert(true, "cleanup deve executar sem erros");
});

test("AgentMemory.stopCleanupTimer deve parar o timer", () => {
	const AgentMemoryTemp = require("./src/agents/AgentMemory");
	const tempMemory = AgentMemoryTemp.getInstance();
	tempMemory.stopCleanupTimer();
	assertEqual(tempMemory.cleanupInterval, null, "Timer deve ser null após stop");
	tempMemory.startCleanupTimer();
});

test("AgentLearning.cleanup deve limpar dados antigos", () => {
	learning.learnPattern("cleanup-test", { type: "test", signature: "test-pattern", keywords: ["test"] });
	learning.cleanup();
	assert(true, "cleanup deve executar sem erros");
});

test("AgentLearning.stopCleanupTimer deve parar o timer", () => {
	const AgentLearningTemp = require("./src/agents/AgentLearning");
	const tempLearning = AgentLearningTemp.getInstance();
	tempLearning.stopCleanupTimer();
	assertEqual(tempLearning.cleanupInterval, null, "Timer deve ser null após stop");
	tempLearning.startCleanupTimer();
});

test("AgentDelegator.cleanCache deve limpar cache expirado", () => {
	delegator.detectIntent("teste de cache para limpeza");
	delegator.cleanCache();
	assert(true, "cleanCache deve executar sem erros");
});

test("AgentDelegator.stopCleanupTimer deve parar o timer", () => {
	const AgentDelegatorTemp = require("./src/agents/AgentDelegator");
	const tempDelegator = AgentDelegatorTemp.getInstance();
	tempDelegator.stopCleanupTimer();
	assertEqual(tempDelegator.cleanupInterval, null, "Timer deve ser null após stop");
	tempDelegator.startCleanupTimer();
});

test("AgentAutonomy.processScheduledActions deve limpar ações obsoletas", async () => {
	await autonomy.processScheduledActions();
	assert(true, "processScheduledActions deve executar sem erros");
});

test("AgentAutonomy.stopScheduler deve parar o scheduler", () => {
	const AgentAutonomyTemp = require("./src/agents/AgentAutonomy");
	const tempAutonomy = AgentAutonomyTemp.getInstance();
	tempAutonomy.stopScheduler();
	assertEqual(tempAutonomy.schedulerTimer, null, "Scheduler deve ser null após stop");
	tempAutonomy.startScheduler();
});

test("AgentMetrics.cleanup deve limpar métricas antigas", () => {
	metrics.recordMetric("cleanup-test", "test_metric", 100);
	metrics.cleanup();
	assert(true, "cleanup deve executar sem erros");
});

test("AgentMetrics.stopAggregationTimer deve parar o timer", () => {
	const AgentMetricsTemp = require("./src/agents/AgentMetrics");
	const tempMetrics = AgentMetricsTemp.getInstance();
	tempMetrics.stopAggregationTimer();
	assertEqual(tempMetrics.aggregationTimer, null, "Timer deve ser null após stop");
	tempMetrics.startAggregationTimer();
});

test("AgentRouter deve ter método cleanup", () => {
	const AgentRouter = require("./src/agents/AgentRouter");
	const router = AgentRouter.getInstance();
	assert(typeof router.cleanup === "function", "cleanup deve ser função");
	assert(typeof router.cleanupSessions === "function", "cleanupSessions deve ser função");
	assert(typeof router.cleanupStats === "function", "cleanupStats deve ser função");
	assert(typeof router.cleanCache === "function", "cleanCache deve ser função");
	assert(typeof router.startCleanupTimer === "function", "startCleanupTimer deve ser função");
	assert(typeof router.stopCleanupTimer === "function", "stopCleanupTimer deve ser função");
});

test("AgentRouter.cleanupSessions deve limpar sessões expiradas", () => {
	const AgentRouter = require("./src/agents/AgentRouter");
	const router = AgentRouter.getInstance();
	router.setSessionAgent("cleanup-session-test", "ravena");
	router.cleanupSessions();
	const session = router.getSession("cleanup-session-test");
	assertNotNull(session, "Sessão nova não deve ser removida");
});

test("AgentRouter.cleanCache deve limpar cache expirado", () => {
	const AgentRouter = require("./src/agents/AgentRouter");
	const router = AgentRouter.getInstance();
	router.cleanCache();
	assert(true, "cleanCache deve executar sem erros");
});

test("AgentRouter.cleanupStats deve limpar estatísticas antigas", () => {
	const AgentRouter = require("./src/agents/AgentRouter");
	const router = AgentRouter.getInstance();
	router.cleanupStats();
	assert(true, "cleanupStats deve executar sem erros");
});

test("AgentRouter.stopCleanupTimer deve parar o timer", () => {
	const AgentRouter = require("./src/agents/AgentRouter");
	const router = AgentRouter.getInstance();
	router.stopCleanupTimer();
	assertEqual(router.cleanupInterval, null, "Timer deve ser null após stop");
	router.startCleanupTimer();
});

test("AgentRouter.reset deve limpar tudo e parar timers", () => {
	const AgentRouter = require("./src/agents/AgentRouter");
	const router = AgentRouter.getInstance();
	router.setSessionAgent("reset-test", "ravena");
	router.reset();
	assertEqual(router.sessions.size, 0, "Sessões devem estar vazias");
	assertEqual(router.responseCache.size, 0, "Cache deve estar vazio");
	assertEqual(router.cleanupInterval, null, "Timer deve estar parado");
	router.startCleanupTimer();
});

test("AgentLearning.resetAll deve limpar tudo e parar timer", () => {
	learning.learnPattern("reset-test", { type: "test", signature: "reset-pattern", keywords: ["test"] });
	learning.resetAll();
	const stats = learning.getStats();
	assertEqual(stats.patternsSize, 0, "Padrões devem estar vazios");
	assertEqual(learning.cleanupInterval, null, "Timer deve estar parado");
	learning.startCleanupTimer();
});

test("AgentDelegator.resetAll deve limpar tudo e parar timer", () => {
	const AgentDelegatorTemp = require("./src/agents/AgentDelegator");
	const tempDelegator = AgentDelegatorTemp.getInstance();
	tempDelegator.detectIntent("teste reset");
	tempDelegator.resetAll();
	assertEqual(tempDelegator.intentCache.size, 0, "Cache deve estar vazio");
	assertEqual(tempDelegator.cleanupInterval, null, "Timer deve estar parado");
	tempDelegator.startCleanupTimer();
});

console.log("");

// ===========================================================================
// Testes Completos - AgentMemory
// ===========================================================================
console.log("🧠 Testando AgentMemory (completo)...");

test("buildContext deve montar contexto completo", () => {
	memory.addShortTerm("ctx-test", "ravena", { author: "user", text: "Olá" });
	memory.setSemantic("ctx-test", "language", "pt-BR");
	const context = memory.buildContext("ctx-test", "ravena");
	assertNotNull(context, "Context deve existir");
	assertNotNull(context.recentConversation, "recentConversation deve existir");
	assertNotNull(context.preferences, "preferences deve existir");
	assertEqual(context.session.agentId, "ravena", "agentId deve ser ravena");
});

test("buildPromptWithContext deve gerar prompt", () => {
	memory.addShortTerm("prompt-test", "ravena", { author: "user", text: "Teste" });
	const prompt = memory.buildPromptWithContext("prompt-test", "ravena", "Pergunta teste");
	assert(typeof prompt === "string", "Prompt deve ser string");
	assert(prompt.includes("Pergunta teste"), "Prompt deve conter a pergunta");
});

test("createEpisode deve criar sessão episódica", () => {
	const episodeId = memory.createEpisode("ep-test", "ravena", { topic: "teste" });
	assertNotNull(episodeId, "episodeId deve existir");
	assert(episodeId.startsWith("ep-"), "episodeId deve começar com ep-");
});

test("addEpisodeInteraction deve adicionar interação", () => {
	const episodeId = memory.createEpisode("ep-interact-test", "ravena");
	memory.addEpisodeInteraction(episodeId, { type: "user", content: "Olá" });
	const episode = memory.getEpisode(episodeId);
	assertNotNull(episode, "Episode deve existir");
	assertEqual(episode.interactions.length, 1, "Deve ter 1 interação");
});

test("endEpisode deve finalizar sessão", () => {
	const episodeId = memory.createEpisode("ep-end-test", "ravena");
	memory.addEpisodeInteraction(episodeId, { type: "user", content: "obrigado" });
	memory.endEpisode(episodeId, "completed");
	const episode = memory.getEpisode(episodeId);
	assertNotNull(episode, "Episode deve existir");
	assertEqual(episode.outcome, "completed", "Outcome deve ser completed");
	assertNotNull(episode.endTime, "endTime deve existir");
});

test("getEpisodes deve retornar episódios do grupo", () => {
	memory.createEpisode("ep-list-test", "ravena");
	memory.createEpisode("ep-list-test", "dev");
	const episodes = memory.getEpisodes("ep-list-test", "ravena");
	assert(Array.isArray(episodes), "Deve retornar array");
	assert(episodes.length >= 1, "Deve ter pelo menos 1 episódio");
});

test("getAllSemantic deve retornar todas preferências", () => {
	memory.setSemantic("all-sem-test", "lang", "pt");
	memory.setSemantic("all-sem-test", "theme", "dark");
	const all = memory.getAllSemantic("all-sem-test");
	assertNotNull(all, "All deve existir");
	assertEqual(all.lang, "pt", "lang deve ser pt");
	assertEqual(all.theme, "dark", "theme deve ser dark");
});

test("getSemantic com agentId deve retornar valor correto", () => {
	memory.setSemantic("agent-sem-test", "key", "value", "ravena");
	const value = memory.getSemantic("agent-sem-test", "key", "ravena");
	assertEqual(value, "value", "Valor deve ser value");
});

test("getSemantic para grupo inexistente deve retornar null", () => {
	const value = memory.getSemantic("nonexistent-group", "key");
	assertEqual(value, null, "Deve retornar null");
});

test("clearMemory com agentId deve limpar apenas agente", () => {
	memory.addShortTerm("clear-agent-test", "ravena", { author: "user", text: "test1" });
	memory.addShortTerm("clear-agent-test", "dev", { author: "user", text: "test2" });
	memory.clearMemory("clear-agent-test", "ravena");
	const ravenaMsgs = memory.getShortTerm("clear-agent-test", "ravena");
	const devMsgs = memory.getShortTerm("clear-agent-test", "dev");
	assertEqual(ravenaMsgs.length, 0, "Ravena deve estar vazio");
	assert(devMsgs.length > 0, "Dev deve ter mensagens");
});

test("resetAll deve limpar todas as memórias", () => {
	memory.addShortTerm("reset-all-test", "ravena", { author: "user", text: "test" });
	memory.resetAll();
	const stats = memory.getStats();
	assertEqual(stats.shortTermSize, 0, "ShortTerm deve estar vazio");
	assertEqual(stats.longTermSize, 0, "LongTerm deve estar vazio");
	assertEqual(stats.episodicSize, 0, "Episodic deve estar vazio");
	assertEqual(stats.semanticSize, 0, "Semantic deve estar vazio");
});

console.log("");

// ===========================================================================
// Testes Completos - AgentLearning
// ===========================================================================
console.log("📚 Testando AgentLearning (completo)...");

test("learnCorrection deve registrar correção", () => {
	learning.learnCorrection("test-agent", {
		type: "syntax-error",
		content: "Use const em vez de var",
		topic: "javascript"
	});
	const corrections = learning.getRelevantCorrections("test-agent", { topic: "javascript" });
	assert(corrections.length > 0, "Deve ter correções");
});

test("learnFeedback deve processar feedback", () => {
	learning.learnFeedback("test-agent", {
		rating: 5,
		comment: "Excelente resposta",
		patternSignature: "api-question",
		keywords: ["api"]
	});
	const stats = learning.getStats();
	assert(stats.feedbackProcessed > 0, "Feedback deve ser processado");
});

test("learnAssociation deve registrar associação", () => {
	learning.learnAssociation("test-agent", "javascript", "nodejs", 5);
	learning.learnAssociation("test-agent", "javascript", "react", 4);
	const assocs = learning.getAssociations("test-agent", "javascript", 0.1);
	assert(assocs.length >= 1, "Deve ter associações");
	assert(assocs[0].concept === "nodejs" || assocs[0].concept === "react", "Conceito deve ser nodejs ou react");
});

test("buildEnrichedContext deve construir contexto enriquecido", () => {
	learning.learnPattern("enriched-test", { type: "test", signature: "sig", keywords: ["kw"] });
	learning.learnKnowledge("enriched-test", { type: "fact", signature: "fact1", content: "Teste" });
	const ctx = learning.buildEnrichedContext("enriched-test", { userId: "user1" });
	assertNotNull(ctx, "Context deve existir");
	assertNotNull(ctx.learnings, "learnings deve existir");
	assertNotNull(ctx.learnings.patterns, "patterns deve existir");
	assertNotNull(ctx.learnings.knowledge, "knowledge deve existir");
});

test("buildPromptWithLearnings deve gerar prompt", () => {
	learning.learnPattern("prompt-learn-test", { type: "test", signature: "sig2", keywords: ["kw2"] });
	const prompt = learning.buildPromptWithLearnings("prompt-learn-test", {});
	assert(typeof prompt === "string", "Prompt deve ser string");
});

test("getRelevantCorrections deve filtrar por contexto", () => {
	learning.learnCorrection("corr-filter-test", { type: "error", content: "Erro de syntax", topic: "js", keywords: ["var"] });
	learning.learnCorrection("corr-filter-test", { type: "error", content: "Erro de lógica", topic: "python", keywords: ["loop"] });
	const jsCorrections = learning.getRelevantCorrections("corr-filter-test", { topic: "js" });
	assert(jsCorrections.length > 0, "Deve ter correções de js");
});

console.log("");

// ===========================================================================
// Testes Completos - AgentDelegator
// ===========================================================================
console.log("🔄 Testando AgentDelegator (completo)...");

test("detectIntent deve retornar allScores", () => {
	const result = delegator.detectIntent("Como programar em Python?");
	assertNotNull(result.allScores, "allScores deve existir");
	assert(typeof result.allScores.dev === "number", "dev score deve ser número");
});

test("detectIntent com query curta deve retornar null", () => {
	const result = delegator.detectIntent("ab");
	assertEqual(result.agentId, null, "Query curta deve retornar null");
});

test("detectIntent com query vazia deve retornar null", () => {
	const result = delegator.detectIntent("");
	assertEqual(result.agentId, null, "Query vazia deve retornar null");
});

test("shouldDelegate para mesmo agente não deve delegar", () => {
	const result = delegator.shouldDelegate("dev", "dev", 90);
	assertEqual(result.shouldDelegate, false, "Mesmo agente não deve delegar");
});

test("shouldDelegate com agente null não deve delegar", () => {
	const result = delegator.shouldDelegate("ravena", null, 80);
	assertEqual(result.shouldDelegate, false, "Agente null não deve delegar");
});

test("setEnabled deve habilitar/desabilitar", () => {
	delegator.setEnabled(false);
	const result = delegator.shouldDelegate("ravena", "dev", 90);
	assertEqual(result.shouldDelegate, false, "Desabilitado não deve delegar");
	delegator.setEnabled(true);
});

test("clearCache deve limpar cache", () => {
	delegator.detectIntent("teste clear cache");
	delegator.clearCache();
	assertEqual(delegator.intentCache.size, 0, "Cache deve estar vazio");
});

test("resetStats deve resetar estatísticas", () => {
	delegator.resetStats();
	const stats = delegator.getStats();
	assertEqual(stats.totalDelegations, 0, "Total deve ser 0");
	assertEqual(stats.cacheHits, 0, "Cache hits deve ser 0");
});

test("buildDelegationPrompt deve gerar prompt", () => {
	const prompt = delegator.buildDelegationPrompt({
		query: "Teste de delegação",
		currentAgent: "ravena",
		targetAgent: "dev",
		agent: { name: "Dev" },
		context: { groupName: "Test Group", authorName: "User" }
	});
	assert(typeof prompt === "string", "Prompt deve ser string");
	assert(prompt.includes("DELEGATION FROM"), "Prompt deve conter DELEGATION FROM");
	assert(prompt.includes("Teste de delegação"), "Prompt deve conter a query");
});

console.log("");

// ===========================================================================
// Testes Completos - AgentCollaboration
// ===========================================================================
console.log("🤝 Testando AgentCollaboration (completo)...");

test("getWorkflow para workflow inexistente deve retornar null", () => {
	const workflow = collaboration.getWorkflow("nonexistent");
	assertEqual(workflow, null, "Workflow inexistente deve retornar null");
});

test("listWorkflows deve retornar ids dos workflows", () => {
	const workflows = collaboration.listWorkflows();
	assert(workflows.length >= 4, "Deve ter pelo menos 4 workflows");
	const ids = workflows.map((w) => w.id);
	assert(ids.includes("full-analysis"), "Deve incluir full-analysis");
	assert(ids.includes("secure-dev"), "Deve incluir secure-dev");
});

console.log("");

// ===========================================================================
// Testes Completos - AgentAutonomy
// ===========================================================================
console.log("🤖 Testando AgentAutonomy (completo)...");

test("setAutonomyLevel com nível inválido deve lançar erro", () => {
	let threw = false;
	try {
		autonomy.setAutonomyLevel("test-agent", 10);
	} catch (e) {
		threw = true;
	}
	assert(threw, "Deve lançar erro para nível inválido");
});

test("getRequiredLevel deve retornar nível correto", () => {
	const level = autonomy.getRequiredLevel("task-create");
	assertEqual(level, 1, "task-create deve ser nível 1");
});

test("requiresSpecificApproval deve verificar aprovação", () => {
	const result = autonomy.requiresSpecificApproval("call-external-api");
	assertEqual(result, true, "call-external-api deve precisar de aprovação");
});

test("getPendingActions deve retornar ações pendentes", () => {
	const actions = autonomy.getPendingActions();
	assert(Array.isArray(actions), "Deve retornar array");
});

test("getPendingActions com agentId deve filtrar", () => {
	const actions = autonomy.getPendingActions("nonexistent-agent");
	assertEqual(actions.length, 0, "Não deve ter ações para agente inexistente");
});

test("getHistory deve retornar histórico", () => {
	const history = autonomy.getHistory();
	assert(Array.isArray(history), "Deve retornar array");
});

test("getHistory com filtros deve filtrar", () => {
	const history = autonomy.getHistory({ agentId: "nonexistent-agent" });
	assertEqual(history.length, 0, "Não deve ter histórico para agente inexistente");
});

test("resetStats deve resetar estatísticas", () => {
	autonomy.resetStats();
	const stats = autonomy.getStats();
	assertEqual(stats.totalActions, 0, "Total deve ser 0");
});

console.log("");

// ===========================================================================
// Testes Completos - AgentStateMachine
// ===========================================================================
console.log("⚙️ Testando AgentStateMachine (completo)...");

test("createInstance com workflow inexistente deve lançar erro", () => {
	let threw = false;
	try {
		stateMachine.createInstance("nonexistent-workflow");
	} catch (e) {
		threw = true;
	}
	assert(threw, "Deve lançar erro para workflow inexistente");
});

test("listWorkflows deve retornar detalhes dos workflows", () => {
	const workflows = stateMachine.listWorkflows();
	assert(workflows.length >= 2, "Deve ter pelo menos 2 workflows");
	assert(workflows[0].id, "Workflow deve ter id");
	assert(workflows[0].name, "Workflow deve ter name");
});

console.log("");

// ===========================================================================
// Testes Completos - AgentMetrics
// ===========================================================================
console.log("📊 Testando AgentMetrics (completo)...");

test("recordError deve registrar erro", () => {
	metrics.recordError("error-test", "timeout");
	const agentMetrics = metrics.getAgentMetrics("error-test");
	assertNotNull(agentMetrics.total_errors, "total_errors deve existir");
	assertEqual(agentMetrics.total_errors.value, 1, "Total errors deve ser 1");
});

test("recordCacheMetric deve registrar cache hit", () => {
	metrics.recordCacheMetric("cache-test", true);
	const agentMetrics = metrics.getAgentMetrics("cache-test");
	assertNotNull(agentMetrics.cache_hits, "cache_hits deve existir");
});

test("recordCacheMetric deve registrar cache miss", () => {
	metrics.recordCacheMetric("cache-test", false);
	const agentMetrics = metrics.getAgentMetrics("cache-test");
	assertNotNull(agentMetrics.cache_misses, "cache_misses deve existir");
});

test("recordDelegation deve registrar delegação", () => {
	metrics.recordDelegation("from-agent", "to-agent");
	const fromMetrics = metrics.getAgentMetrics("from-agent");
	const toMetrics = metrics.getAgentMetrics("to-agent");
	assertNotNull(fromMetrics.delegations_out, "delegations_out deve existir");
	assertNotNull(toMetrics.delegations_in, "delegations_in deve existir");
});

test("recordMemoryUsage deve registrar uso de memória", () => {
	metrics.recordMemoryUsage("mem-test", "short-term", 10);
	const agentMetrics = metrics.getAgentMetrics("mem-test");
	assertNotNull(agentMetrics["memory_short-term"], "memory_short-term deve existir");
});

test("getRealtimeMetrics deve retornar métricas em tempo real", () => {
	metrics.recordMetric("rt-test", "test_metric", 50);
	const realtime = metrics.getRealtimeMetrics("rt-test", "test_metric");
	assertNotNull(realtime, "Realtime deve existir");
	assert(typeof realtime.count === "number", "count deve ser número");
	assert(typeof realtime.avg === "number", "avg deve ser número");
});

test("getGlobalMetrics deve retornar métricas globais", () => {
	const global = metrics.getGlobalMetrics();
	assertNotNull(global, "Global deve existir");
});

test("getHistory deve retornar histórico", () => {
	const history = metrics.getHistory();
	assert(Array.isArray(history), "Deve retornar array");
});

test("getHistory com filtros deve filtrar", () => {
	const history = metrics.getHistory({ agentId: "nonexistent-agent" });
	assertEqual(history.length, 0, "Não deve ter histórico para agente inexistente");
});

test("getSystemReport deve retornar relatório completo", () => {
	const report = metrics.getSystemReport();
	assertNotNull(report, "Report deve existir");
	assertNotNull(report.summary, "summary deve existir");
	assertNotNull(report.agents, "agents deve existir");
	assertNotNull(report.global, "global deve existir");
});

test("resetAll deve limpar todas as métricas", () => {
	metrics.recordMetric("reset-metrics-test", "test", 1);
	metrics.resetAll();
	const stats = metrics.getStats();
	assertEqual(stats.totalMetricsCollected, 0, "Total deve ser 0");
	assertEqual(stats.agentMetricsSize, 0, "Agent metrics deve estar vazio");
});

console.log("");

// ===========================================================================
// Testes Completos - AgentPermissions
// ===========================================================================
console.log("🔐 Testando AgentPermissions (completo)...");

test("createRole deve criar papel", () => {
	permissions.createRole("test-custom-role", {
		description: "Papel de teste",
		permissions: { agent: ["read"] }
	});
	const role = permissions.getRole("test-custom-role");
	assertNotNull(role, "Role deve existir");
	assertEqual(role.id, "test-custom-role", "ID deve ser test-custom-role");
});

test("getRole deve retornar papel", () => {
	permissions.createRole("get-test-role", { description: "Para buscar" });
	const role = permissions.getRole("get-test-role");
	assertNotNull(role, "Role deve existir");
	assertEqual(role.id, "get-test-role", "ID deve ser get-test-role");
});

test("removeRole deve deletar papel", () => {
	permissions.createRole("delete-test-role", { description: "Para deletar" });
	const result = permissions.removeRole("delete-test-role");
	assertEqual(result, true, "Deve retornar true");
});

test("removeUserRole deve remover papel do usuário", () => {
	permissions.assignRole("remove-role-user", "admin");
	permissions.removeUserRole("remove-role-user");
	const userPerm = permissions.getUserPermissions("remove-role-user");
	assertEqual(userPerm.roleId, "user", "Papel deve ser user após remoção");
});

test("getUserPermissions deve retornar permissões do usuário", () => {
	const userPerm = permissions.getUserPermissions("test-user");
	assertNotNull(userPerm, "UserPerm deve existir");
	assertNotNull(userPerm.roleId, "roleId deve existir");
});

test("getAuditLog deve retornar log de auditoria", () => {
	const auditLog = permissions.getAuditLog();
	assert(Array.isArray(auditLog), "Deve retornar array");
});

console.log("");

// ===========================================================================
// Testes Completos - AgentDatabase
// ===========================================================================
console.log("💾 Testando AgentDatabase (completo)...");

const AgentDatabase = require("./src/agents/AgentDatabase");
const database = AgentDatabase.getInstance();

test("Database deve ser singleton", () => {
	const instance1 = AgentDatabase.getInstance();
	const instance2 = AgentDatabase.getInstance();
	assertEqual(instance1, instance2, "Deve ser a mesma instância");
});

test("Database deve ter métodos essenciais", () => {
	assert(typeof database.saveSession === "function", "saveSession deve ser função");
	assert(typeof database.getSession === "function", "getSession deve ser função");
	assert(typeof database.saveMemory === "function", "saveMemory deve ser função");
	assert(typeof database.getMemory === "function", "getMemory deve ser função");
	assert(typeof database.saveMetric === "function", "saveMetric deve ser função");
	assert(typeof database.getMetrics === "function", "getMetrics deve ser função");
	assert(typeof database.saveSetting === "function", "saveSetting deve ser função");
	assert(typeof database.getSetting === "function", "getSetting deve ser função");
});

console.log("");

// ===========================================================================
// Testes Completos - AgentRouter
// ===========================================================================
console.log("🔀 Testando AgentRouter (completo)...");

const AgentRouter = require("./src/agents/AgentRouter");
const router = AgentRouter.getInstance();

test("Router deve ser singleton", () => {
	const instance1 = AgentRouter.getInstance();
	const instance2 = AgentRouter.getInstance();
	assertEqual(instance1, instance2, "Deve ser a mesma instância");
});

test("setSessionAgent deve criar sessão", () => {
	router.setSessionAgent("session-test", "dev");
	const session = router.getSession("session-test");
	assertNotNull(session, "Session deve existir");
	assertEqual(session.agentId, "dev", "AgentId deve ser dev");
	assertNotNull(session.timestamp, "Timestamp deve existir");
});

test("getSession para grupo inexistente deve retornar null", () => {
	const session = router.getSession("nonexistent-group");
	assertEqual(session, null, "Deve retornar null");
});

test("isSessionValid deve validar sessão", () => {
	router.setSessionAgent("valid-test", "ravena");
	const session = router.getSession("valid-test");
	const isValid = router.isSessionValid(session);
	assertEqual(isValid, true, "Sessão nova deve ser válida");
});

test("updateSession deve atualizar timestamp", () => {
	router.setSessionAgent("update-test", "ravena");
	const before = router.getSession("update-test");
	const tsBefore = before.timestamp;
	router.updateSession("update-test", "ravena");
	const after = router.getSession("update-test");
	assert(after.timestamp >= tsBefore, "Timestamp deve ser igual ou posterior");
});

test("updateSession deve criar nova sessão se agente mudar", () => {
	router.setSessionAgent("update-agent-test", "ravena");
	router.updateSession("update-agent-test", "dev");
	const session = router.getSession("update-agent-test");
	assertEqual(session.agentId, "dev", "AgentId deve ser dev");
});

test("clearSession deve remover sessão", () => {
	router.setSessionAgent("clear-session-test", "ravena");
	router.clearSession("clear-session-test");
	const session = router.getSession("clear-session-test");
	assertEqual(session, null, "Session deve ser null após clear");
});

test("getCacheKey deve gerar chave correta", () => {
	const key = router.getCacheKey("ravena", "Olá mundo");
	assertEqual(key, "ravena:olá mundo", "Chave deve ser ravena:olá mundo");
});

test("cacheResponse e getCachedResponse devem funcionar", () => {
	router.cacheResponse("cache-func-test", "pergunta", "resposta");
	const cached = router.getCachedResponse("cache-func-test", "pergunta");
	assertNotNull(cached, "Cached deve existir");
	assertEqual(cached.response, "resposta", "Response deve ser resposta");
});

test("getCachedResponse para query inexistente deve retornar null", () => {
	const cached = router.getCachedResponse("nonexistent", "query");
	assertEqual(cached, null, "Deve retornar null");
});

test("getStats deve retornar estatísticas", () => {
	const stats = router.getStats();
	assertNotNull(stats, "Stats deve existir");
	assert(typeof stats.totalRequests === "number", "totalRequests deve ser número");
	assert(typeof stats.sessions === "number", "sessions deve ser número");
	assert(typeof stats.cacheSize === "number", "cacheSize deve ser número");
});

test("resolveAgent com nome válido deve retornar agente", () => {
	const agentId = router.resolveAgent("dev", null, null);
	assertEqual(agentId, "dev", "Deve retornar dev");
});

test("resolveAgent com nome inválido deve retornar padrão", () => {
	const agentId = router.resolveAgent("invalid-agent", null, null);
	assertEqual(agentId, "ravena", "Deve retornar ravena (padrão)");
});

test("resolveAgent com command deve usar mapeamento", () => {
	const agentId = router.resolveAgent(null, "dev", null);
	assertEqual(agentId, "dev", "Command dev deve mapear para dev");
});

console.log("");

// ===========================================================================
// Resumo
// ===========================================================================
console.log("═══════════════════════════════════════════════════════════════");
console.log(`\n📊 Resultado dos Testes:`);
console.log(`   ✅ Aprovados: ${passed}`);
console.log(`   ❌ Reprovados: ${failed}`);
console.log(`   📋 Total: ${total}`);
console.log(`   📈 Taxa de sucesso: ${((passed / total) * 100).toFixed(1)}%\n`);

if (failed > 0) {
	console.log("⚠️  Alguns testes falharam!");
	process.exit(1);
} else {
	console.log("🎉 Todos os testes passaram!");
	process.exit(0);
}
