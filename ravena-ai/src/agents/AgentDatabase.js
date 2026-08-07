/**
 * AgentDatabase.js
 *
 * Integração com banco de dados para persistência de dados de agentes.
 * Suporta SQLite (padrão) e pode ser estendido para outros bancos.
 *
 * Nível 4 - Integração com Banco de Dados
 */

"use strict";

const Logger = require("../utils/Logger");
const path = require("path");
const fs = require("fs");

const logger = new Logger("agent-database");

/**
 * Class for agent database integration
 */
class AgentDatabase {
	constructor() {
		// Configurações
		this.config = {
			dbPath: process.env.AGENT_DB_PATH || path.join(__dirname, "../../data/agents.db"),
			enableWAL: true,
			enableForeignKeys: true,
			busyTimeout: 5000,
			syncMode: "NORMAL"
		};

		// Conexão com o banco
		this.db = null;
		this.isConnected = false;

		// Estatísticas
		this.stats = {
			totalQueries: 0,
			successfulQueries: 0,
			failedQueries: 0,
			avgQueryTime: 0,
			tables: {}
		};

		// Cache de queries
		this.queryCache = new Map();
		this.cacheTTL = 5 * 60 * 1000; // 5 minutos
	}

	/**
	 * Get singleton instance
	 * @returns {AgentDatabase} - Singleton instance
	 */
	static getInstance() {
		if (!AgentDatabase.instance) {
			AgentDatabase.instance = new AgentDatabase();
		}
		return AgentDatabase.instance;
	}

	/**
	 * Conecta ao banco de dados
	 * @returns {Promise<boolean>} - Sucesso
	 */
	async connect() {
		try {
			// Verificar se better-sqlite3 está disponível
			let Database;
			try {
				Database = require("better-sqlite3");
			} catch (error) {
				logger.warn("[connect] better-sqlite3 not available, using mock database");
				this.db = new MockDatabase();
				this.isConnected = true;
				return true;
			}

			// Criar diretório se não existir
			const dbDir = path.dirname(this.config.dbPath);
			if (!fs.existsSync(dbDir)) {
				fs.mkdirSync(dbDir, { recursive: true });
			}

			// Conectar ao banco
			this.db = new Database(this.config.dbPath, {
				wal: this.config.enableWAL,
				foreignKeys: this.config.enableForeignKeys,
				busyTimeout: this.config.busyTimeout
			});

			// Configurar modo de sincronização
			this.db.pragma(`journal_mode = ${this.config.syncMode}`);

			this.isConnected = true;

			// Inicializar tabelas
			await this.initializeTables();

			logger.info(`[connect] Connected to database: ${this.config.dbPath}`);
			return true;
		} catch (error) {
			logger.error("[connect] Failed to connect to database:", error);
			this.isConnected = false;
			return false;
		}
	}

	/**
	 * Desconecta do banco
	 */
	disconnect() {
		if (this.db && this.isConnected) {
			try {
				this.db.close();
				this.isConnected = false;
				logger.info("[disconnect] Disconnected from database");
			} catch (error) {
				logger.error("[disconnect] Error disconnecting:", error);
			}
		}
	}

	/**
	 * Inicializa tabelas do banco
	 */
	async initializeTables() {
		if (!this.isConnected) {
			return;
		}

		// Tabela de agentes
		this.db.exec(`
			CREATE TABLE IF NOT EXISTS agents (
				id TEXT PRIMARY KEY,
				name TEXT NOT NULL,
				workspace TEXT,
				description TEXT,
				config TEXT,
				created_at INTEGER DEFAULT (unixepoch('now')),
				updated_at INTEGER DEFAULT (unixepoch('now'))
			)
		`);

		// Tabela de sessões
		this.db.exec(`
			CREATE TABLE IF NOT EXISTS sessions (
				id TEXT PRIMARY KEY,
				group_id TEXT NOT NULL,
				agent_id TEXT NOT NULL,
				context TEXT,
				created_at INTEGER DEFAULT (unixepoch('now')),
				last_activity INTEGER DEFAULT (unixepoch('now')),
				FOREIGN KEY (agent_id) REFERENCES agents(id)
			)
		`);

		// Tabela de memória
		this.db.exec(`
			CREATE TABLE IF NOT EXISTS memory (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				group_id TEXT NOT NULL,
				agent_id TEXT NOT NULL,
				type TEXT NOT NULL,
				content TEXT NOT NULL,
				metadata TEXT,
				created_at INTEGER DEFAULT (unixepoch('now')),
				expires_at INTEGER,
				FOREIGN KEY (agent_id) REFERENCES agents(id)
			)
		`);

		// Tabela de aprendizados
		this.db.exec(`
			CREATE TABLE IF NOT EXISTS learnings (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				agent_id TEXT NOT NULL,
				type TEXT NOT NULL,
				signature TEXT,
				content TEXT NOT NULL,
				confidence REAL DEFAULT 0.5,
				occurrences INTEGER DEFAULT 1,
				metadata TEXT,
				created_at INTEGER DEFAULT (unixepoch('now')),
				last_seen INTEGER DEFAULT (unixepoch('now')),
				FOREIGN KEY (agent_id) REFERENCES agents(id)
			)
		`);

		// Tabela de histórico
		this.db.exec(`
			CREATE TABLE IF NOT EXISTS history (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				session_id TEXT,
				group_id TEXT NOT NULL,
				agent_id TEXT NOT NULL,
				user_id TEXT,
				message TEXT,
				response TEXT,
				metadata TEXT,
				created_at INTEGER DEFAULT (unixepoch('now')),
				FOREIGN KEY (agent_id) REFERENCES agents(id)
			)
		`);

		// Tabela de métricas
		this.db.exec(`
			CREATE TABLE IF NOT EXISTS metrics (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				agent_id TEXT NOT NULL,
				metric_name TEXT NOT NULL,
				value REAL NOT NULL,
				timestamp INTEGER DEFAULT (unixepoch('now')),
				FOREIGN KEY (agent_id) REFERENCES agents(id)
			)
		`);

		// Tabela de configurações
		this.db.exec(`
			CREATE TABLE IF NOT EXISTS settings (
				key TEXT PRIMARY KEY,
				value TEXT NOT NULL,
				description TEXT,
				created_at INTEGER DEFAULT (unixepoch('now')),
				updated_at INTEGER DEFAULT (unixepoch('now'))
			)
		`);

		// Criar índices
		this.db.exec(`
			CREATE INDEX IF NOT EXISTS idx_sessions_group ON sessions(group_id);
			CREATE INDEX IF NOT EXISTS idx_sessions_agent ON sessions(agent_id);
			CREATE INDEX IF NOT EXISTS idx_memory_group ON memory(group_id);
			CREATE INDEX IF NOT EXISTS idx_memory_agent ON memory(agent_id);
			CREATE INDEX IF NOT EXISTS idx_memory_type ON memory(type);
			CREATE INDEX IF NOT EXISTS idx_learnings_agent ON learnings(agent_id);
			CREATE INDEX IF NOT EXISTS idx_learnings_type ON learnings(type);
			CREATE INDEX IF NOT EXISTS idx_history_session ON history(session_id);
			CREATE INDEX IF NOT EXISTS idx_history_group ON history(group_id);
			CREATE INDEX IF NOT EXISTS idx_history_agent ON history(agent_id);
			CREATE INDEX IF NOT EXISTS idx_metrics_agent ON metrics(agent_id);
			CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name);
			CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp);
		`);

		logger.info("[initializeTables] Database tables initialized");
	}

	// ===========================================================================
	// Operações CRUD
	// ===========================================================================

	/**
	 * Executa query SQL
	 * @param {string} sql - Query SQL
	 * @param {Array} params - Parâmetros
	 * @returns {Promise<Object>} - Resultado
	 */
	async query(sql, params = []) {
		if (!this.isConnected) {
			throw new Error("Database not connected");
		}

		const startTime = Date.now();
		this.stats.totalQueries++;

		try {
			// Verificar cache
			const cacheKey = `${sql}:${JSON.stringify(params)}`;
			const cached = this.queryCache.get(cacheKey);
			if (cached && Date.now() - cached.timestamp < this.cacheTTL) {
				this.stats.successfulQueries++;
				return cached.result;
			}

			// Executar query
			const result = this.db.prepare(sql).all(...params);

			// Armazenar no cache
			this.queryCache.set(cacheKey, {
				result,
				timestamp: Date.now()
			});

			// Atualizar estatísticas
			const queryTime = Date.now() - startTime;
			this.stats.successfulQueries++;
			this.stats.avgQueryTime =
				(this.stats.avgQueryTime * (this.stats.successfulQueries - 1) + queryTime) /
				this.stats.successfulQueries;

			return result;
		} catch (error) {
			this.stats.failedQueries++;
			logger.error("[query] Query failed:", error);
			throw error;
		}
	}

	/**
	 * Executa query de inserção
	 * @param {string} sql - Query SQL
	 * @param {Array} params - Parâmetros
	 * @returns {Promise<Object>} - Resultado
	 */
	async run(sql, params = []) {
		if (!this.isConnected) {
			throw new Error("Database not connected");
		}

		const startTime = Date.now();
		this.stats.totalQueries++;

		try {
			const result = this.db.prepare(sql).run(...params);

			// Limpar cache relevante
			this.clearQueryCache();

			const queryTime = Date.now() - startTime;
			this.stats.successfulQueries++;
			this.stats.avgQueryTime =
				(this.stats.avgQueryTime * (this.stats.successfulQueries - 1) + queryTime) /
				this.stats.successfulQueries;

			return result;
		} catch (error) {
			this.stats.failedQueries++;
			logger.error("[run] Query failed:", error);
			throw error;
		}
	}

	/**
	 * Obtém um registro
	 * @param {string} sql - Query SQL
	 * @param {Array} params - Parâmetros
	 * @returns {Promise<Object|null>} - Registro ou null
	 */
	async get(sql, params = []) {
		const results = await this.query(sql, params);
		return results[0] || null;
	}

	/**
	 * Obtém todos os registros
	 * @param {string} sql - Query SQL
	 * @param {Array} params - Parâmetros
	 * @returns {Promise<Array>} - Lista de registros
	 */
	async getAll(sql, params = []) {
		return this.query(sql, params);
	}

	// ===========================================================================
	// Operações de Agentes
	// ===========================================================================

	/**
	 * Salva agente
	 * @param {Object} agent - Dados do agente
	 * @returns {Promise<boolean>} - Sucesso
	 */
	async saveAgent(agent) {
		const sql = `
			INSERT OR REPLACE INTO agents (id, name, workspace, description, config, updated_at)
			VALUES (?, ?, ?, ?, ?, unixepoch('now'))
		`;

		await this.run(sql, [
			agent.id,
			agent.name,
			agent.workspace,
			agent.description,
			JSON.stringify(agent.config || {})
		]);

		return true;
	}

	/**
	 * Obtém agente por ID
	 * @param {string} agentId - ID do agente
	 * @returns {Promise<Object|null>} - Agente
	 */
	async getAgent(agentId) {
		const sql = "SELECT * FROM agents WHERE id = ?";
		const agent = await this.get(sql, [agentId]);

		if (agent && agent.config) {
			agent.config = JSON.parse(agent.config);
		}

		return agent;
	}

	/**
	 * Lista todos os agentes
	 * @returns {Promise<Array>} - Lista de agentes
	 */
	async listAgents() {
		const sql = "SELECT * FROM agents ORDER BY name";
		return this.query(sql);
	}

	// ===========================================================================
	// Operações de Sessões
	// ===========================================================================

	/**
	 * Salva sessão
	 * @param {Object} session - Dados da sessão
	 * @returns {Promise<boolean>} - Sucesso
	 */
	async saveSession(session) {
		const sql = `
			INSERT OR REPLACE INTO sessions (id, group_id, agent_id, context, last_activity)
			VALUES (?, ?, ?, ?, unixepoch('now'))
		`;

		await this.run(sql, [
			session.id,
			session.groupId,
			session.agentId,
			JSON.stringify(session.context || {})
		]);

		return true;
	}

	/**
	 * Obtém sessão por ID
	 * @param {string} sessionId - ID da sessão
	 * @returns {Promise<Object|null>} - Sessão
	 */
	async getSession(sessionId) {
		const sql = "SELECT * FROM sessions WHERE id = ?";
		const session = await this.get(sql, [sessionId]);

		if (session && session.context) {
			session.context = JSON.parse(session.context);
		}

		return session;
	}

	/**
	 * Obtém sessões de um grupo
	 * @param {string} groupId - ID do grupo
	 * @returns {Promise<Array>} - Lista de sessões
	 */
	async getGroupSessions(groupId) {
		const sql = `
			SELECT * FROM sessions 
			WHERE group_id = ? 
			ORDER BY last_activity DESC
		`;
		return this.query(sql, [groupId]);
	}

	// ===========================================================================
	// Operações de Memória
	// ===========================================================================

	/**
	 * Salva item de memória
	 * @param {Object} memory - Dados da memória
	 * @returns {Promise<number>} - ID do item
	 */
	async saveMemory(memory) {
		const sql = `
			INSERT INTO memory (group_id, agent_id, type, content, metadata, expires_at)
			VALUES (?, ?, ?, ?, ?, ?)
		`;

		const result = await this.run(sql, [
			memory.groupId,
			memory.agentId,
			memory.type,
			JSON.stringify(memory.content),
			JSON.stringify(memory.metadata || {}),
			memory.expiresAt || null
		]);

		return result.lastInsertRowid;
	}

	/**
	 * Obtém memória de um grupo/agente
	 * @param {string} groupId - ID do grupo
	 * @param {string} agentId - ID do agente
	 * @param {string} type - Tipo de memória
	 * @param {number} limit - Limite
	 * @returns {Promise<Array>} - Lista de memórias
	 */
	async getMemory(groupId, agentId, type = null, limit = 50) {
		let sql = `
			SELECT * FROM memory 
			WHERE group_id = ? AND agent_id = ?
		`;
		const params = [groupId, agentId];

		if (type) {
			sql += " AND type = ?";
			params.push(type);
		}

		sql += " ORDER BY created_at DESC LIMIT ?";
		params.push(limit);

		const memories = await this.query(sql, params);

		return memories.map((m) => ({
			...m,
			content: JSON.parse(m.content),
			metadata: JSON.parse(m.metadata)
		}));
	}

	/**
	 * Remove memória expirada
	 * @returns {Promise<number>} - Itens removidos
	 */
	async cleanExpiredMemory() {
		const sql = `
			DELETE FROM memory 
			WHERE expires_at IS NOT NULL AND expires_at < unixepoch('now')
		`;

		const result = await this.run(sql);
		return result.changes;
	}

	// ===========================================================================
	// Operações de Aprendizados
	// ===========================================================================

	/**
	 * Salva aprendizado
	 * @param {Object} learning - Dados do aprendizado
	 * @returns {Promise<number>} - ID do aprendizado
	 */
	async saveLearning(learning) {
		const sql = `
			INSERT INTO learnings (agent_id, type, signature, content, confidence, occurrences, metadata)
			VALUES (?, ?, ?, ?, ?, ?, ?)
		`;

		const result = await this.run(sql, [
			learning.agentId,
			learning.type,
			learning.signature,
			JSON.stringify(learning.content),
			learning.confidence || 0.5,
			learning.occurrences || 1,
			JSON.stringify(learning.metadata || {})
		]);

		return result.lastInsertRowid;
	}

	/**
	 * Obtém aprendizados de um agente
	 * @param {string} agentId - ID do agente
	 * @param {string} type - Tipo de aprendizado
	 * @param {number} limit - Limite
	 * @returns {Promise<Array>} - Lista de aprendizados
	 */
	async getLearnings(agentId, type = null, limit = 100) {
		let sql = "SELECT * FROM learnings WHERE agent_id = ?";
		const params = [agentId];

		if (type) {
			sql += " AND type = ?";
			params.push(type);
		}

		sql += " ORDER BY confidence DESC, occurrences DESC LIMIT ?";
		params.push(limit);

		const learnings = await this.query(sql, params);

		return learnings.map((l) => ({
			...l,
			content: JSON.parse(l.content),
			metadata: JSON.parse(l.metadata)
		}));
	}

	// ===========================================================================
	// Operações de Histórico
	// ===========================================================================

	/**
	 * Salva mensagem no histórico
	 * @param {Object} message - Dados da mensagem
	 * @returns {Promise<number>} - ID da mensagem
	 */
	async saveHistory(message) {
		const sql = `
			INSERT INTO history (session_id, group_id, agent_id, user_id, message, response, metadata)
			VALUES (?, ?, ?, ?, ?, ?, ?)
		`;

		const result = await this.run(sql, [
			message.sessionId,
			message.groupId,
			message.agentId,
			message.userId,
			message.message,
			message.response,
			JSON.stringify(message.metadata || {})
		]);

		return result.lastInsertRowid;
	}

	/**
	 * Obtém histórico de um grupo
	 * @param {string} groupId - ID do grupo
	 * @param {number} limit - Limite
	 * @returns {Promise<Array>} - Lista de mensagens
	 */
	async getGroupHistory(groupId, limit = 50) {
		const sql = `
			SELECT * FROM history 
			WHERE group_id = ? 
			ORDER BY created_at DESC 
			LIMIT ?
		`;

		const history = await this.query(sql, [groupId, limit]);

		return history.map((h) => ({
			...h,
			metadata: JSON.parse(h.metadata)
		}));
	}

	// ===========================================================================
	// Operações de Métricas
	// ===========================================================================

	/**
	 * Registra métrica
	 * @param {string} agentId - ID do agente
	 * @param {string} metricName - Nome da métrica
	 * @param {number} value - Valor
	 * @returns {Promise<boolean>} - Sucesso
	 */
	async saveMetric(agentId, metricName, value) {
		const sql = `
			INSERT INTO metrics (agent_id, metric_name, value)
			VALUES (?, ?, ?)
		`;

		await this.run(sql, [agentId, metricName, value]);
		return true;
	}

	/**
	 * Obtém métricas de um agente
	 * @param {string} agentId - ID do agente
	 * @param {string} metricName - Nome da métrica
	 * @param {number} startTime - Timestamp inicial
	 * @param {number} endTime - Timestamp final
	 * @returns {Promise<Array>} - Lista de métricas
	 */
	async getMetrics(agentId, metricName = null, startTime = null, endTime = null) {
		let sql = "SELECT * FROM metrics WHERE agent_id = ?";
		const params = [agentId];

		if (metricName) {
			sql += " AND metric_name = ?";
			params.push(metricName);
		}

		if (startTime) {
			sql += " AND timestamp >= ?";
			params.push(startTime);
		}

		if (endTime) {
			sql += " AND timestamp <= ?";
			params.push(endTime);
		}

		sql += " ORDER BY timestamp DESC";

		return this.query(sql, params);
	}

	// ===========================================================================
	// Operações de Configurações
	// ===========================================================================

	/**
	 * Salva configuração
	 * @param {string} key - Chave
	 * @param {any} value - Valor
	 * @param {string} description - Descrição
	 * @returns {Promise<boolean>} - Sucesso
	 */
	async saveSetting(key, value, description = "") {
		const sql = `
			INSERT OR REPLACE INTO settings (key, value, description, updated_at)
			VALUES (?, ?, ?, unixepoch('now'))
		`;

		await this.run(sql, [key, JSON.stringify(value), description]);
		return true;
	}

	/**
	 * Obtém configuração
	 * @param {string} key - Chave
	 * @returns {Promise<any>} - Valor
	 */
	async getSetting(key) {
		const sql = "SELECT value FROM settings WHERE key = ?";
		const setting = await this.get(sql, [key]);

		if (setting && setting.value) {
			return JSON.parse(setting.value);
		}

		return null;
	}

	/**
	 * Lista todas as configurações
	 * @returns {Promise<Object>} - Configurações
	 */
	async listSettings() {
		const sql = "SELECT * FROM settings ORDER BY key";
		const settings = await this.query(sql);

		const result = {};
		for (const setting of settings) {
			result[setting.key] = {
				value: JSON.parse(setting.value),
				description: setting.description
			};
		}

		return result;
	}

	// ===========================================================================
	// Utilitários
	// ===========================================================================

	/**
	 * Limpa cache de queries
	 */
	clearQueryCache() {
		this.queryCache.clear();
	}

	/**
	 * Obtém estatísticas do banco
	 * @returns {Object} - Estatísticas
	 */
	getStats() {
		return {
			...this.stats,
			isConnected: this.isConnected,
			dbPath: this.config.dbPath,
			cacheSize: this.queryCache.size
		};
	}

	/**
	 * Verifica integridade do banco
	 * @returns {Promise<boolean>} - Integridade OK
	 */
	async checkIntegrity() {
		try {
			const result = await this.query("PRAGMA quick_check");
			return result[0]?.quick_check === "ok";
		} catch (error) {
			logger.error("[checkIntegrity] Integrity check failed:", error);
			return false;
		}
	}

	/**
	 * Faz backup do banco
	 * @param {string} backupPath - Caminho do backup
	 * @returns {Promise<boolean>} - Sucesso
	 */
	async backup(backupPath) {
		try {
			if (this.db && this.db.backup) {
				await this.db.backup(backupPath);
				logger.info(`[backup] Database backed up to: ${backupPath}`);
				return true;
			}
			logger.warn("[backup] Backup not supported by database driver");
			return false;
		} catch (error) {
			logger.error("[backup] Backup failed:", error);
			return false;
		}
	}
}

/**
 * Mock Database for when better-sqlite3 is not available
 */
class MockDatabase {
	constructor() {
		this.data = {};
	}

	prepare(sql) {
		return {
			all: () => [],
			run: () => ({ changes: 0, lastInsertRowid: 0 }),
			get: () => null
		};
	}

	exec(sql) {
		// No-op
	}

	pragma(pragma) {
		// No-op
	}

	close() {
		// No-op
	}

	backup(path) {
		return Promise.resolve();
	}
}

// Singleton
AgentDatabase.instance = null;

module.exports = AgentDatabase;
