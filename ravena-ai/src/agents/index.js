/**
 * agents/index.js
 *
 * Índice do módulo de agentes.
 * Exporta todos os componentes principais para facilitar importações.
 */

"use strict";

const AgentConfig = require("./AgentConfig");
const AgentRouter = require("./AgentRouter");
const AgentDelegator = require("./AgentDelegator");
const AgentCollaboration = require("./AgentCollaboration");
const AgentMemory = require("./AgentMemory");
const AgentStateMachine = require("./AgentStateMachine");
const AgentMetrics = require("./AgentMetrics");
const AgentAutonomy = require("./AgentAutonomy");
const AgentLearning = require("./AgentLearning");
const AgentDatabase = require("./AgentDatabase");
const AgentPermissions = require("./AgentPermissions");

module.exports = {
	// Configuração
	...AgentConfig,

	// Router (singleton)
	AgentRouter: AgentRouter.getInstance(),

	// Delegator (singleton)
	AgentDelegator: AgentDelegator.getInstance(),

	// Collaboration (singleton)
	AgentCollaboration: AgentCollaboration.getInstance(),

	// Memory (singleton)
	AgentMemory: AgentMemory.getInstance(),

	// State Machine (singleton)
	AgentStateMachine: AgentStateMachine.getInstance(),

	// Metrics (singleton)
	AgentMetrics: AgentMetrics.getInstance(),

	// Autonomy (singleton)
	AgentAutonomy: AgentAutonomy.getInstance(),

	// Learning (singleton)
	AgentLearning: AgentLearning.getInstance(),

	// Database (singleton)
	AgentDatabase: AgentDatabase.getInstance(),

	// Permissions (singleton)
	AgentPermissions: AgentPermissions.getInstance(),

	// Classes
	AgentRouterClass: AgentRouter,
	AgentDelegatorClass: AgentDelegator,
	AgentCollaborationClass: AgentCollaboration,
	AgentMemoryClass: AgentMemory,
	AgentStateMachineClass: AgentStateMachine,
	AgentMetricsClass: AgentMetrics,
	AgentAutonomyClass: AgentAutonomy,
	AgentLearningClass: AgentLearning,
	AgentDatabaseClass: AgentDatabase,
	AgentPermissionsClass: AgentPermissions
};
