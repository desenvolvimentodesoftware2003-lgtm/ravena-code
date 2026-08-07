/**
 * AgentPermissions.js
 *
 * Sistema de permissões avançado para agentes.
 * Controla acesso a recursos, ações e dados.
 *
 * Nível 4 - Sistema de Permissões
 */

"use strict";

const Logger = require("../utils/Logger");
const { getAgent } = require("./AgentConfig");

const logger = new Logger("agent-permissions");

/**
 * Níveis de permissão
 */
const PERMISSION_LEVELS = {
	NONE: 0,
	READ: 1,
	WRITE: 2,
	EXECUTE: 3,
	ADMIN: 4,
	SUPER_ADMIN: 5
};

/**
 * Categorias de permissão
 */
const PERMISSION_CATEGORIES = {
	AGENT: "agent",
	COMMAND: "command",
	DATA: "data",
	MEMORY: "memory",
	WORKFLOW: "workflow",
	SETTINGS: "settings",
	METRICS: "metrics",
	EXTERNAL: "external"
};

/**
 * Ações de permissão
 */
const PERMISSION_ACTIONS = {
	CREATE: "create",
	READ: "read",
	UPDATE: "update",
	DELETE: "delete",
	EXECUTE: "execute",
	APPROVE: "approve",
	MANAGE: "manage"
};

/**
 * Class for agent permissions
 */
class AgentPermissions {
	constructor() {
		// Papéis: roleId -> { permissions }
		this.roles = new Map();

		// Permissões de usuários: userId -> { roleId, overrides }
		this.userPermissions = new Map();

		// Permissões de agentes: agentId -> { permissions }
		this.agentPermissions = new Map();

		// Permissões de grupo: groupId -> { permissions }
		this.groupPermissions = new Map();

		// Configurações
		this.config = {
			defaultRole: "user",
			adminRole: "admin",
			superAdminRole: "super-admin",
			enableGroupPermissions: true,
			enableAgentPermissions: true,
			enableInheritance: true,
			auditLog: true
		};

		// Log de auditoria
		this.auditLog = [];

		// Estatísticas
		this.stats = {
			totalChecks: 0,
			allowed: 0,
			denied: 0,
			byRole: {},
			byCategory: {}
		};

		// Inicializar papéis padrão
		this.initDefaultRoles();
	}

	/**
	 * Get singleton instance
	 * @returns {AgentPermissions} - Singleton instance
	 */
	static getInstance() {
		if (!AgentPermissions.instance) {
			AgentPermissions.instance = new AgentPermissions();
		}
		return AgentPermissions.instance;
	}

	/**
	 * Inicializa papéis padrão
	 */
	initDefaultRoles() {
		// Papel: Usuário
		this.createRole("user", {
			name: "Usuário",
			description: "Papel padrão para usuários",
			permissions: [
				{ category: PERMISSION_CATEGORIES.AGENT, actions: [PERMISSION_ACTIONS.READ] },
				{
					category: PERMISSION_CATEGORIES.COMMAND,
					actions: [PERMISSION_ACTIONS.READ, PERMISSION_ACTIONS.EXECUTE]
				},
				{ category: PERMISSION_CATEGORIES.DATA, actions: [PERMISSION_ACTIONS.READ] },
				{ category: PERMISSION_CATEGORIES.MEMORY, actions: [PERMISSION_ACTIONS.READ] }
			]
		});

		// Papel: Admin
		this.createRole("admin", {
			name: "Administrador",
			description: "Administrador do grupo",
			permissions: [
				{ category: PERMISSION_CATEGORIES.AGENT, actions: Object.values(PERMISSION_ACTIONS) },
				{ category: PERMISSION_CATEGORIES.COMMAND, actions: Object.values(PERMISSION_ACTIONS) },
				{ category: PERMISSION_CATEGORIES.DATA, actions: Object.values(PERMISSION_ACTIONS) },
				{ category: PERMISSION_CATEGORIES.MEMORY, actions: Object.values(PERMISSION_ACTIONS) },
				{ category: PERMISSION_CATEGORIES.WORKFLOW, actions: Object.values(PERMISSION_ACTIONS) },
				{
					category: PERMISSION_CATEGORIES.SETTINGS,
					actions: [PERMISSION_ACTIONS.READ, PERMISSION_ACTIONS.UPDATE]
				},
				{ category: PERMISSION_CATEGORIES.METRICS, actions: [PERMISSION_ACTIONS.READ] }
			]
		});

		// Papel: Super Admin
		this.createRole("super-admin", {
			name: "Super Administrador",
			description: "Administrador do sistema",
			permissions: [{ category: "*", actions: ["*"] }]
		});

		// Papel: Agente
		this.createRole("agent", {
			name: "Agente",
			description: "Permissões para agentes",
			permissions: [
				{
					category: PERMISSION_CATEGORIES.DATA,
					actions: [PERMISSION_ACTIONS.READ, PERMISSION_ACTIONS.CREATE, PERMISSION_ACTIONS.UPDATE]
				},
				{ category: PERMISSION_CATEGORIES.MEMORY, actions: Object.values(PERMISSION_ACTIONS) },
				{ category: PERMISSION_CATEGORIES.EXTERNAL, actions: [PERMISSION_ACTIONS.READ] }
			]
		});
	}

	// ===========================================================================
	// Gerenciamento de Papéis
	// ===========================================================================

	/**
	 * Cria um papel
	 * @param {string} roleId - ID do papel
	 * @param {Object} roleData - Dados do papel
	 */
	createRole(roleId, roleData) {
		this.roles.set(roleId, {
			id: roleId,
			...roleData,
			createdAt: Date.now()
		});

		logger.info(`[Permissions] Role created: ${roleId}`);
	}

	/**
	 * Obtém papel por ID
	 * @param {string} roleId - ID do papel
	 * @returns {Object|null} - Papel
	 */
	getRole(roleId) {
		return this.roles.get(roleId) || null;
	}

	/**
	 * Lista todos os papéis
	 * @returns {Array} - Lista de papéis
	 */
	listRoles() {
		return Array.from(this.roles.values());
	}

	/**
	 * Remove papel
	 * @param {string} roleId - ID do papel
	 * @returns {boolean} - Sucesso
	 */
	removeRole(roleId) {
		// Verificar se há usuários com este papel
		for (const [userId, userPerm] of this.userPermissions.entries()) {
			if (userPerm.roleId === roleId) {
				throw new Error(`Cannot remove role: ${roleId} is assigned to users`);
			}
		}

		return this.roles.delete(roleId);
	}

	// ===========================================================================
	// Gerenciamento de Permissões de Usuário
	// ===========================================================================

	/**
	 * Atribui papel a usuário
	 * @param {string} userId - ID do usuário
	 * @param {string} roleId - ID do papel
	 * @param {Object} overrides - Sobrescritas de permissão
	 */
	assignRole(userId, roleId, overrides = {}) {
		const role = this.getRole(roleId);
		if (!role) {
			throw new Error(`Role not found: ${roleId}`);
		}

		this.userPermissions.set(userId, {
			roleId,
			overrides,
			assignedAt: Date.now(),
			assignedBy: "system"
		});

		logger.info(`[Permissions] Role ${roleId} assigned to user ${userId}`);
	}

	/**
	 * Obtém permissões do usuário
	 * @param {string} userId - ID do usuário
	 * @returns {Object} - Permissões
	 */
	getUserPermissions(userId) {
		const userPerm = this.userPermissions.get(userId);
		if (!userPerm) {
			// Retornar papel padrão
			const defaultRole = this.getRole(this.config.defaultRole);
			return {
				roleId: this.config.defaultRole,
				role: defaultRole,
				overrides: {}
			};
		}

		return {
			...userPerm,
			role: this.getRole(userPerm.roleId)
		};
	}

	/**
	 * Remove papel de usuário
	 * @param {string} userId - ID do usuário
	 * @returns {boolean} - Sucesso
	 */
	removeUserRole(userId) {
		return this.userPermissions.delete(userId);
	}

	// ===========================================================================
	// Gerenciamento de Permissões de Agente
	// ===========================================================================

	/**
	 * Define permissões de um agente
	 * @param {string} agentId - ID do agente
	 * @param {Array} permissions - Lista de permissões
	 */
	setAgentPermissions(agentId, permissions) {
		this.agentPermissions.set(agentId, {
			permissions,
			updatedAt: Date.now()
		});

		logger.info(`[Permissions] Permissions set for agent ${agentId}`);
	}

	/**
	 * Obtém permissões de um agente
	 * @param {string} agentId - ID do agente
	 * @returns {Array} - Lista de permissões
	 */
	getAgentPermissions(agentId) {
		const agentPerm = this.agentPermissions.get(agentId);
		return agentPerm?.permissions || [];
	}

	// ===========================================================================
	// Gerenciamento de Permissões de Grupo
	// ===========================================================================

	/**
	 * Define permissões de um grupo
	 * @param {string} groupId - ID do grupo
	 * @param {Object} permissions - Permissões
	 */
	setGroupPermissions(groupId, permissions) {
		this.groupPermissions.set(groupId, {
			...permissions,
			updatedAt: Date.now()
		});

		logger.info(`[Permissions] Permissions set for group ${groupId}`);
	}

	/**
	 * Obtém permissões de um grupo
	 * @param {string} groupId - ID do grupo
	 * @returns {Object} - Permissões
	 */
	getGroupPermissions(groupId) {
		return this.groupPermissions.get(groupId) || {};
	}

	// ===========================================================================
	// Verificação de Permissões
	// ===========================================================================

	/**
	 * Verifica se usuário tem permissão
	 * @param {string} userId - ID do usuário
	 * @param {string} category - Categoria
	 * @param {string} action - Ação
	 * @param {Object} context - Contexto adicional
	 * @returns {Object} - { allowed, reason, details }
	 */
	checkPermission(userId, category, action, context = {}) {
		this.stats.totalChecks++;

		const userPerm = this.getUserPermissions(userId);
		const role = userPerm.role;

		if (!role) {
			this.stats.denied++;
			this.logAudit(userId, category, action, false, "Role not found");
			return { allowed: false, reason: "Role not found" };
		}

		// Verificar sobrescritas do usuário
		if (userPerm.overrides[category]) {
			const override = userPerm.overrides[category];
			if (override.includes(action) || override.includes("*")) {
				this.stats.allowed++;
				this.logAudit(userId, category, action, true, "Override");
				return { allowed: true, reason: "Override" };
			}
			if (override.includes(`-${action}`)) {
				this.stats.denied++;
				this.logAudit(userId, category, action, false, "Override denied");
				return { allowed: false, reason: "Override denied" };
			}
		}

		// Verificar permissões do papel
		const hasPermission = role.permissions.some((perm) => {
			// Verificar se a categoria corresponde
			if (perm.category !== "*" && perm.category !== category) {
				return false;
			}

			// Verificar se a ação está permitida
			return perm.actions.includes("*") || perm.actions.includes(action);
		});

		if (hasPermission) {
			this.stats.allowed++;
			this.logAudit(userId, category, action, true, "Role permission");
			return { allowed: true, reason: "Role permission" };
		}

		this.stats.denied++;
		this.logAudit(userId, category, action, false, "No matching permission");
		return { allowed: false, reason: "No matching permission" };
	}

	/**
	 * Verifica se agente tem permissão
	 * @param {string} agentId - ID do agente
	 * @param {string} category - Categoria
	 * @param {string} action - Ação
	 * @returns {Object} - { allowed, reason }
	 */
	checkAgentPermission(agentId, category, action) {
		const permissions = this.getAgentPermissions(agentId);

		const hasPermission = permissions.some((perm) => {
			if (perm.category !== "*" && perm.category !== category) {
				return false;
			}
			return perm.actions.includes("*") || perm.actions.includes(action);
		});

		return {
			allowed: hasPermission,
			reason: hasPermission ? "Agent permission granted" : "No matching permission"
		};
	}

	/**
	 * Verifica se usuário pode acessar recurso
	 * @param {string} userId - ID do usuário
	 * @param {string} resource - Recurso
	 * @param {string} action - Ação
	 * @param {Object} context - Contexto
	 * @returns {boolean} - Pode acessar
	 */
	canAccess(userId, resource, action, context = {}) {
		// Mapear recursos para categorias
		const categoryMap = {
			agent: PERMISSION_CATEGORIES.AGENT,
			command: PERMISSION_CATEGORIES.COMMAND,
			data: PERMISSION_CATEGORIES.DATA,
			memory: PERMISSION_CATEGORIES.MEMORY,
			workflow: PERMISSION_CATEGORIES.WORKFLOW,
			settings: PERMISSION_CATEGORIES.SETTINGS,
			metrics: PERMISSION_CATEGORIES.METRICS
		};

		const category = categoryMap[resource] || resource;
		const result = this.checkPermission(userId, category, action, context);

		return result.allowed;
	}

	// ===========================================================================
	// Herança de Permissões
	// ===========================================================================

	/**
	 * Obtém permissões efetivas (com herança)
	 * @param {string} userId - ID do usuário
	 * @param {string} groupId - ID do grupo
	 * @returns {Object} - Permissões efetivas
	 */
	getEffectivePermissions(userId, groupId = null) {
		const userPerm = this.getUserPermissions(userId);
		const role = userPerm.role;

		if (!role) {
			return { permissions: [] };
		}

		let permissions = [...role.permissions];

		// Adicionar permissões do grupo
		if (groupId && this.config.enableGroupPermissions) {
			const groupPerm = this.getGroupPermissions(groupId);
			if (groupPerm.permissions) {
				permissions = [...permissions, ...groupPerm.permissions];
			}
		}

		// Adicionar sobrescritas
		if (userPerm.overrides.permissions) {
			permissions = [...permissions, ...userPerm.overrides.permissions];
		}

		return {
			roleId: userPerm.roleId,
			roleName: role.name,
			permissions,
			overrides: userPerm.overrides
		};
	}

	// ===========================================================================
	// Auditoria
	// ===========================================================================

	/**
	 * Registra ação de auditoria
	 * @param {string} userId - ID do usuário
	 * @param {string} category - Categoria
	 * @param {string} action - Ação
	 * @param {boolean} allowed - Se foi permitido
	 * @param {string} reason - Motivo
	 */
	logAudit(userId, category, action, allowed, reason) {
		if (!this.config.auditLog) {
			return;
		}

		this.auditLog.push({
			userId,
			category,
			action,
			allowed,
			reason,
			timestamp: Date.now()
		});

		// Limitar tamanho do log
		if (this.auditLog.length > 10000) {
			this.auditLog = this.auditLog.slice(-10000);
		}

		// Atualizar estatísticas
		if (!this.stats.byRole[userId]) {
			this.stats.byRole[userId] = { allowed: 0, denied: 0 };
		}

		if (allowed) {
			this.stats.byRole[userId].allowed++;
		} else {
			this.stats.byRole[userId].denied++;
		}

		if (!this.stats.byCategory[category]) {
			this.stats.byCategory[category] = { allowed: 0, denied: 0 };
		}

		if (allowed) {
			this.stats.byCategory[category].allowed++;
		} else {
			this.stats.byCategory[category].denied++;
		}
	}

	/**
	 * Obtém log de auditoria
	 * @param {Object} filters - Filtros
	 * @returns {Array} - Log de auditoria
	 */
	getAuditLog(filters = {}) {
		const { userId, category, allowed, limit = 100 } = filters;

		let log = [...this.auditLog];

		if (userId) {
			log = log.filter((l) => l.userId === userId);
		}

		if (category) {
			log = log.filter((l) => l.category === category);
		}

		if (allowed !== undefined) {
			log = log.filter((l) => l.allowed === allowed);
		}

		return log.sort((a, b) => b.timestamp - a.timestamp).slice(0, limit);
	}

	// ===========================================================================
	// Utilitários
	// ===========================================================================

	/**
	 * Obtém estatísticas
	 * @returns {Object} - Estatísticas
	 */
	getStats() {
		return {
			...this.stats,
			totalRoles: this.roles.size,
			totalUsers: this.userPermissions.size,
			totalAgents: this.agentPermissions.size,
			totalGroups: this.groupPermissions.size,
			auditLogSize: this.auditLog.length
		};
	}

	/**
	 * Reseta permissões
	 */
	reset() {
		this.userPermissions.clear();
		this.agentPermissions.clear();
		this.groupPermissions.clear();
		this.auditLog = [];

		this.stats = {
			totalChecks: 0,
			allowed: 0,
			denied: 0,
			byRole: {},
			byCategory: {}
		};

		// Recriar papéis padrão
		this.roles.clear();
		this.initDefaultRoles();

		logger.info("[reset] Permissions reset");
	}
}

// Singleton
AgentPermissions.instance = null;

module.exports = AgentPermissions;
