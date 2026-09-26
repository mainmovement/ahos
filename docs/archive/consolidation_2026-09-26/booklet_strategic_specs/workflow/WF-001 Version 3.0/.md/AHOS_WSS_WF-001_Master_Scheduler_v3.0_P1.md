\# AHOS Workflow Specification Sheet

\# WF-001 — Master Scheduler

\#\# Version 3.0

\#\# Phase 1 — Core Runtime Architecture

\---

\# 1\. Runtime Realization

\#\# 1.1 Runtime Definition

WF-001 SHALL exist as the primary orchestration workflow executed within the n8n runtime deployed in Docker Compose.

WF-001 SHALL use n8n execution semantics while preserving the architectural responsibilities defined by this specification.

The scheduler service SHALL provide the persistent runtime required for:

\- Continuous scheduling.  
\- Runtime coordination.  
\- Dependency-aware orchestration in later phases.  
\- Execution request dispatch.  
\- Runtime health reporting.  
\- Controlled startup.  
\- Controlled shutdown.  
\- Communication with PostgreSQL and n8n.

The logical responsibility of WF-001 SHALL remain singular: orchestrating AHOS workflow execution.

The runtime MAY contain internally separated modules or companion processes where required, provided that all such components remain part of the single WF-001 responsibility boundary.

\#\# 1.2 Runtime Form

The Phase 1 runtime SHALL consist of:

1\. \*\*WF-001 Scheduler Service\*\*  
   \- Dedicated Docker Compose service.  
   \- Long-running process.  
   \- Owns the scheduler runtime.  
   \- Communicates with PostgreSQL and n8n through approved internal interfaces.

2\. \*\*PostgreSQL Service\*\*  
   \- Persistent system-of-record service.  
   \- Stores scheduler-owned persistent information according to approved database specifications.  
   \- Does not execute scheduler business logic.

3\. \*\*n8n Service\*\*  
   \- Workflow execution and automation service.  
   \- Executes registered AHOS workflows.  
   \- Does not own global AHOS scheduling authority.

4\. \*\*Notification Engine\*\*  
   \- Independent AHOS component.  
   \- Delivers approved operational notifications.  
   \- Does not control scheduler orchestration or execution.

5\. \*\*Operator Control Center\*\*  
   \- Independent AHOS workflow or service.  
   \- Receives and validates operator commands.  
   \- Sends approved control requests to WF-001.  
   \- Does not execute scheduler internals.

\#\# 1.3 Continuous Scheduler Behavior

The WF-001 Scheduler Service SHALL remain active during normal system operation.

It SHALL:

\- Maintain its runtime process.  
\- Maintain communication with required internal services.  
\- Evaluate approved scheduling inputs.  
\- Coordinate workflow execution requests.  
\- Publish runtime health information.  
\- Process approved runtime events.  
\- Respond to lifecycle signals.

The scheduler SHALL NOT depend on repeated short-lived n8n executions to preserve its primary runtime identity.

The scheduler SHALL NOT use an unbounded n8n workflow execution as a substitute for a dedicated scheduler process.

\#\# 1.4 Relationship Between WF-001, PostgreSQL, and n8n

\#\#\# WF-001 and PostgreSQL

WF-001 SHALL use PostgreSQL as the authoritative persistent coordination and operational data store for scheduler-owned information.

WF-001 SHALL:

\- Read approved scheduler configuration from PostgreSQL.  
\- Persist scheduler operational information through PostgreSQL.  
\- Use PostgreSQL-backed information for auditable coordination.  
\- Treat durable persistence as distinct from in-memory processing.

PostgreSQL SHALL NOT:

\- Select workflow priorities.  
\- Implement scheduler policy.  
\- Trigger n8n workflows independently.  
\- Replace the WF-001 scheduler process.

\#\#\# WF-001 and n8n

WF-001 SHALL be the orchestration authority for initiating approved AHOS workflow executions.

n8n SHALL be the workflow execution runtime.

WF-001 SHALL communicate execution requests to n8n through an approved internal interface.

n8n SHALL:

\- Receive execution requests.  
\- Execute the referenced workflow.  
\- Return execution-related events through the approved communication interface.  
\- Preserve its own execution behavior according to n8n capabilities and configuration.

n8n SHALL NOT independently decide the global AHOS scheduling order or override WF-001 orchestration policy.

\#\#\# PostgreSQL and n8n

PostgreSQL and n8n SHALL NOT be treated as a single atomic runtime component.

A PostgreSQL operation and an n8n operation SHALL be considered separate operations unless a later approved phase explicitly defines their coordination protocol.

WF-001 SHALL remain responsible for coordinating the interaction between them.

\#\# 1.5 Runtime Topology

The Phase 1 runtime topology SHALL be:

\`\`\`text  
                         ┌──────────────────────────┐  
                         │      Single Operator     │  
                         └────────────┬─────────────┘  
                                      │  
                                      ▼  
                         ┌──────────────────────────┐  
                         │   Operator Control Center│  
                         └────────────┬─────────────┘  
                                      │  
                                      ▼  
┌──────────────────┐       ┌──────────────────────────┐  
│ Notification     │◄──────│   WF-001 Scheduler       │  
│ Engine           │       │   Dedicated Runtime       │  
└──────────────────┘       └──────────┬───────┬───────┘  
                                      │       │  
                                      ▼       ▼  
                         ┌────────────────┐ ┌──────────┐  
                         │   PostgreSQL   │ │   n8n    │  
                         │ Persistent     │ │ Workflow │  
                         │ Coordination   │ │ Runtime  │  
                         └────────────────┘ └──────────┘  
\`\`\`

All services SHALL run within the approved Docker Compose deployment unless an approved architectural change specifies otherwise.

Internal service communication SHALL use the local Docker network whenever practical.

Core scheduler operation SHALL NOT require public exposure of WF-001, PostgreSQL, or n8n.

\#\# 1.6 Runtime Identity

The WF-001 Scheduler Service SHALL have a stable logical identity independent of:

\- Docker container restart.  
\- Hostname changes.  
\- n8n execution identifiers.  
\- PostgreSQL connection identifiers.  
\- Process identifiers.

Each runtime process SHALL also have a distinct runtime instance identity for operational observability.

Runtime identity and runtime instance identity SHALL not be conflated.

\---

\# 2\. Component Boundaries

\#\# 2.1 Scheduler

The Scheduler is the sole runtime owner of WF-001 orchestration responsibility.

The Scheduler SHALL be responsible for:

\- Maintaining the continuous scheduler runtime.  
\- Loading approved scheduler configuration.  
\- Receiving approved scheduling inputs.  
\- Determining when orchestration actions are eligible.  
\- Coordinating workflow execution requests.  
\- Communicating with n8n.  
\- Reading and writing scheduler-owned operational data through PostgreSQL.  
\- Publishing scheduler health information.  
\- Communicating critical operational events to the Notification Engine.  
\- Accepting approved control requests from the Operator Control Center.  
\- Executing startup and shutdown procedures.

The Scheduler SHALL NOT:

\- Analyze tokens.  
\- Evaluate market conditions.  
\- Perform security analysis.  
\- Perform AI inference.  
\- Generate trading recommendations.  
\- Manage portfolio decisions.  
\- Process raw operator commands directly.  
\- Deliver general market or portfolio reports.  
\- Modify its own approved production configuration autonomously.

\#\# 2.2 n8n

n8n is the AHOS workflow execution platform.

n8n SHALL be responsible for:

\- Hosting approved AHOS workflows.  
\- Executing workflow logic.  
\- Executing n8n-native nodes.  
\- Connecting workflow-specific external services.  
\- Returning workflow execution events through approved interfaces.  
\- Reporting workflow execution results to the scheduler interface.

n8n SHALL NOT be responsible for:

\- Owning global scheduler authority.  
\- Making global workflow-priority decisions.  
\- Replacing PostgreSQL persistence.  
\- Replacing WF-001 lifecycle coordination.  
\- Approving production configuration changes.  
\- Interpreting operator governance decisions.

n8n workflows SHALL remain independently specified according to their own Workflow Specification Sheets.

\#\# 2.3 PostgreSQL

PostgreSQL is the persistent data service used by WF-001.

PostgreSQL SHALL be responsible for:

\- Durable storage of scheduler-owned information.  
\- Transactional persistence.  
\- Retrieval of approved configuration.  
\- Persistence of operational records.  
\- Persistence of runtime health information.  
\- Supporting durable, auditable historical records.

PostgreSQL SHALL NOT be responsible for:

\- Executing scheduler policy.  
\- Starting n8n workflows without WF-001 coordination.  
\- Determining workflow priority.  
\- Sending operator notifications.  
\- Replacing the Scheduler runtime.  
\- Performing autonomous recovery decisions.

The exact PostgreSQL schema SHALL be governed by the approved AHOS Database Design Specification and subsequent approved database documents.

\#\# 2.4 Notification Engine

The Notification Engine SHALL be responsible for delivery of approved notifications to the operator.

It SHALL:

\- Receive notification requests from authorized AHOS components.  
\- Deliver notifications through configured channels.  
\- Report delivery status where supported.  
\- Handle provider-specific notification behavior.  
\- Preserve notification traceability according to its own specification.

The Notification Engine SHALL NOT:

\- Start or stop WF-001.  
\- Change scheduler state.  
\- Approve configuration.  
\- Reorder workflow executions.  
\- Interpret scheduler policy.  
\- Replace scheduler health monitoring.

WF-001 SHALL publish only scheduler-related operational notification requests.

General market intelligence, portfolio reports, simulation reports, and learning reports SHALL be handled by their responsible components.

\#\# 2.5 Operator Control Center

The Operator Control Center SHALL be the independent interface for operator-initiated scheduler control.

It SHALL be responsible for:

\- Receiving operator commands.  
\- Authenticating and authorizing operator requests.  
\- Validating command structure.  
\- Requesting confirmation where required.  
\- Translating approved commands into scheduler control requests.  
\- Recording operator identity and request traceability.  
\- Reporting command acceptance or rejection.

The Operator Control Center SHALL NOT:

\- Modify WF-001 internal runtime state directly.  
\- Bypass scheduler interfaces.  
\- Write scheduler-owned state without authorization.  
\- Execute workflow orchestration logic.  
\- Replace PostgreSQL transaction rules.  
\- Acquire runtime authority independently of WF-001.

WF-001 SHALL receive only validated and authorized control requests from the Operator Control Center.

Telegram command handling SHALL remain outside WF-001.

\#\# 2.6 Boundary Enforcement

Component boundaries SHALL be enforced through explicit interfaces.

No component may depend on the internal implementation details of another component.

The following direct bypasses are prohibited:

\- n8n directly changing scheduler-owned operational state without an approved event interface.  
\- PostgreSQL independently triggering n8n.  
\- Operator Control Center directly modifying scheduler runtime memory.  
\- Notification Engine changing scheduler state.  
\- WF-001 directly implementing market, portfolio, or AI logic.

\---

\# 3\. Runtime Processes

\#\# 3.1 Process Ownership

WF-001 SHALL own the scheduler runtime process.

The scheduler SHALL be deployed as the primary orchestration workflow within the n8n service running in Docker Compose.

The scheduler runtime SHALL not require multiple scheduler instances for Phase One operation.

\#\# 3.2 Scheduler Runtime Process

The primary WF-001 process SHALL be a long-running process responsible for:

\- Initializing the scheduler runtime.  
\- Establishing approved internal communication channels.  
\- Loading approved configuration.  
\- Maintaining runtime operational status.  
\- Executing the scheduler orchestration cycle.  
\- Receiving approved internal events.  
\- Publishing health information.  
\- Coordinating controlled shutdown.

Resource consumption SHALL remain bounded according to configured deployment constraints.

\#\# 3.3 Internal Runtime Modules

The Scheduler Process MAY contain internally separated modules for:

\- Configuration access.  
\- PostgreSQL access.  
\- n8n communication.  
\- Event reception.  
\- Health publication.  
\- Notification publication.  
\- Lifecycle management.  
\- Orchestration evaluation.

These modules SHALL remain internal implementation units of WF-001.

They SHALL not become independently authoritative runtime components.

They SHALL not independently modify scheduler policy.

\#\# 3.4 Event Reception Capability

WF-001 SHALL provide an approved internal mechanism for receiving:

\- n8n execution events.  
\- Operator Control Center requests.  
\- Internal health events.  
\- Runtime lifecycle signals.

The event-reception capability MAY be implemented:

\- Within the Scheduler Process.  
\- As an internal companion process in the same WF-001 Docker service.  
\- As a separate internal service registered as part of WF-001.

The selected implementation SHALL preserve one logical WF-001 responsibility and SHALL use explicit authenticated interfaces.

The event-reception capability SHALL not independently make scheduling decisions.

\#\# 3.5 Notification Publication Capability

WF-001 SHALL publish scheduler notification requests to the Notification Engine through an approved internal interface.

Notification publication MAY be implemented within the Scheduler Process or as an internal WF-001 module.

It SHALL not become an independent notification policy owner.

\#\# 3.6 Process Count

Phase One SHALL operate with exactly one authoritative long-running Scheduler Process.

Additional WF-001 companion processes SHALL be introduced only when required by runtime, networking, or platform constraints.

Any companion process SHALL:

\- Have one clearly defined runtime responsibility.  
\- Share the same WF-001 lifecycle.  
\- Use explicit internal communication.  
\- Be included in Docker Compose deployment and health management.  
\- Remain subordinate to the Scheduler Process.  
\- Not create a second scheduling authority.

\#\# 3.7 No Long-Running n8n Scheduler Execution

WF-001 SHALL NOT require an indefinitely running n8n execution to maintain scheduler operation.

n8n SHALL execute bounded workflow runs initiated through the approved scheduler interface.

\---

\# 4\. Internal Communication Model

\#\# 4.1 Communication Principles

Internal communication SHALL be:

\- Explicit.  
\- Authenticated where state or control is affected.  
\- Traceable.  
\- Deterministic.  
\- Failure-aware.  
\- Suitable for local Docker Compose networking.  
\- Independent of external cloud infrastructure.

Communication contracts SHALL identify:

\- Sender.  
\- Receiver.  
\- Message purpose.  
\- Correlation identity.  
\- Required fields.  
\- Response behavior.  
\- Failure behavior.  
\- Authentication requirements.  
\- Version compatibility.

\#\# 4.2 Communication Paths

\#\#\# Scheduler to PostgreSQL

The Scheduler SHALL communicate with PostgreSQL using the approved database connection interface.

This path SHALL be used for:

\- Reading approved configuration.  
\- Persisting scheduler-owned operational information.  
\- Reading required runtime information.  
\- Publishing scheduler health information.

\#\#\# Scheduler to n8n

The Scheduler SHALL communicate with n8n through an approved internal execution interface.

This path SHALL be used for:

\- Sending workflow execution requests.  
\- Transmitting execution context.  
\- Receiving dispatch acknowledgements where supported.  
\- Receiving execution events.

The interface SHALL be internal to the Docker Compose deployment unless an approved external integration is required.

\#\#\# n8n to Scheduler

n8n SHALL return execution events through an approved internal event interface.

The event interface SHALL identify the originating workflow and execution context.

The event interface SHALL not permit n8n to directly alter unrelated scheduler policy.

\#\#\# Operator Control Center to Scheduler

The Operator Control Center SHALL send validated control requests to WF-001 through an approved internal interface.

Requests SHALL include:

\- Request identity.  
\- Operator identity or authorization reference.  
\- Request type.  
\- Request timestamp.  
\- Correlation identity.  
\- Requested target.  
\- Request version.

WF-001 SHALL validate that the request is structurally and operationally acceptable before processing it.

\#\#\# Scheduler to Notification Engine

The Scheduler SHALL publish operational notification requests to the Notification Engine.

Requests SHALL include:

\- Notification identity.  
\- Severity.  
\- Event type.  
\- Correlation identity.  
\- Timestamp.  
\- Affected component or workflow reference.  
\- Human-readable summary.  
\- Structured diagnostic context where permitted.

The Notification Engine SHALL return delivery status where supported.

Notification delivery status SHALL not be interpreted as scheduler execution status.

\#\# 4.3 Communication Reliability

A communication failure SHALL be distinguishable from a business or workflow failure.

WF-001 SHALL preserve the distinction between:

\-Message not sent.

\-Message sent but not acknowledged.

\-Message acknowledged by the receiver.

\-Message accepted for processing.

\-Message processed by the receiver.

\-Message processing result unavailable.

The specific persistence, retry, and reconciliation behavior for these conditions SHALL be defined in later approved sections.

\#\# 4.4 Correlation

Every inter-component request or event SHALL carry a correlation identity.

The correlation identity SHALL allow an operator or engineer to trace an event across:

\- WF-001 logs.  
\- PostgreSQL operational records.  
\- n8n execution records.  
\- Notification records.  
\- Operator Control Center records.

Correlation identity SHALL remain stable for the related logical operation.

Runtime instance identity SHALL be included where operational attribution is required.

\#\# 4.5 Interface Versioning

Internal interfaces SHALL be versioned.

A receiver SHALL reject or quarantine incompatible messages rather than silently interpreting them under an incompatible contract.

Interface version changes SHALL be traceable through approved version control.

\#\# 4.6 Network Boundaries

PostgreSQL, n8n, WF-001, Notification Engine, and Operator Control Center SHALL communicate over the Docker Compose internal network whenever practical.

Public exposure of internal endpoints SHALL be prohibited unless explicitly approved.

Internal endpoints SHALL use service-level authentication and authorization appropriate to the operation.

\#\# 4.7 No Direct Database Bypass

n8n, Notification Engine, and Operator Control Center SHALL not directly modify WF-001 runtime-owned records unless an approved contract explicitly authorizes that operation.

Database access does not by itself grant component authority.

\---

\# 5\. Startup Sequence

\#\# 5.1 Startup Responsibility

WF-001 SHALL perform a controlled startup sequence before entering active scheduler operation.

No workflow orchestration action SHALL be initiated before startup validation succeeds.

\#\# 5.2 Startup Stages

\#\#\# Stage 1 — Process Initialization

The Scheduler Process SHALL:

\- Start within its assigned Docker Compose service.  
\- Establish its runtime instance identity.  
\- Load only the minimum bootstrap information required for startup.  
\- Initialize structured logging.  
\- Mark its internal lifecycle status as \`initializing\`.

\#\#\# Stage 2 — Environment Validation

WF-001 SHALL validate:

\- Required runtime configuration availability.  
\- Required internal service addresses.  
\- Required authentication material availability.  
\- Time source availability.  
\- Local filesystem paths required for runtime operation.  
\- Compatibility of the deployed runtime version.

Missing or invalid mandatory bootstrap requirements SHALL prevent active operation.

\#\#\# Stage 3 — PostgreSQL Connectivity

WF-001 SHALL establish and validate PostgreSQL connectivity.

It SHALL verify:

\- The database is reachable.  
\- Authentication succeeds.  
\- The connection is usable.  
\- The deployed database contract is compatible with WF-001.  
\- Required scheduler-owned persistence capabilities are available.

WF-001 SHALL not begin active operation if PostgreSQL cannot serve as the authoritative persistence service required by the scheduler.

\#\#\# Stage 4 — n8n Connectivity

WF-001 SHALL establish and validate communication with n8n.

It SHALL verify:

\- The n8n service is reachable through the approved internal interface.  
\- Authentication succeeds where required.  
\- The interface version is compatible.  
\- The scheduler can identify the required n8n execution interface.

Failure to reach n8n SHALL place the scheduler in a non-active startup condition unless an approved startup policy explicitly permits controlled waiting.

\#\#\# Stage 5 — Notification Engine Connectivity

WF-001 SHALL validate the Notification Engine interface when the Notification Engine is required for startup operation.

If the Notification Engine is unavailable:

\- The condition SHALL be logged.  
\- The condition SHALL be exposed through health information.  
\- Startup behavior SHALL follow approved critical-notification availability policy.  
\- WF-001 SHALL not silently assume that alerts are being delivered.

\#\#\# Stage 6 — Operator Control Center Interface Validation

WF-001 SHALL validate the control-request interface when the Operator Control Center is deployed.

The absence of the Operator Control Center SHALL not prevent normal scheduled operation unless explicitly required by an approved deployment policy.

WF-001 SHALL reject unauthenticated or incompatible control requests.

\#\#\# Stage 7 — Configuration Loading

WF-001 SHALL load the approved scheduler configuration.

The configuration SHALL be treated as a coherent approved runtime configuration.

WF-001 SHALL validate configuration compatibility before active operation.

WF-001 SHALL not silently substitute undocumented operational limits for missing configuration.

\#\#\# Stage 8 — Runtime Readiness

WF-001 SHALL:

\- Publish an initial health status.  
\- Record startup completion.  
\- Expose the active runtime instance identity.  
\- Confirm that required interfaces are operational.  
\- Enter the approved active runtime condition only after all mandatory startup validation succeeds.

\#\#\# Stage 9 — Startup Notification

WF-001 SHALL publish a scheduler startup notification request through the Notification Engine when notification delivery is available.

The notification SHALL identify:

\- Scheduler identity.  
\- Runtime instance identity.  
\- Startup timestamp.  
\- Runtime version.  
\- Startup result.  
\- Any degraded or unavailable dependency.

Failure to deliver the startup notification SHALL be recorded separately from startup success.

\#\# 5.3 Startup Failure

If a mandatory startup requirement fails, WF-001 SHALL:

\- Record the failure.  
\- Publish health information where possible.  
\- Avoid initiating workflow orchestration.  
\- Exit or remain in a controlled non-active runtime condition according to the approved deployment policy.  
\- Allow Docker health checks and external watchdog mechanisms to determine restart behavior.

WF-001 SHALL not restart itself.

\#\# 5.4 Startup Idempotence

Repeated startup attempts SHALL not create multiple independent scheduling authorities.

Startup SHALL be safe after:

\- Container restart.  
\- Host restart.  
\- Unexpected process termination.  
\- Temporary dependency unavailability.  
\- Delayed Docker service readiness.

Detailed persistence recovery, execution reconciliation, and retry behavior are outside this phase and SHALL be specified separately.  
The mechanism enforcing single active scheduler authority SHALL be defined in a later approved phase.  
\---

\# 6\. Shutdown Sequence

\#\# 6.1 Shutdown Responsibility

WF-001 SHALL support controlled shutdown initiated by the Docker runtime or an approved internal lifecycle signal.

WF-001 SHALL distinguish controlled shutdown from unexpected process termination.

\#\# 6.2 Shutdown Stages

\#\#\# Stage 1 — Signal Reception

Upon receiving an approved shutdown signal, WF-001 SHALL:

\- Record the signal.  
\- Record the shutdown initiation timestamp.  
\- Set the scheduler lifecycle condition to \`shutting\_down\`.  
\- Stop accepting new orchestration requests for execution.

\#\#\# Stage 2 — Stop New Runtime Activity

WF-001 SHALL:

\- Stop initiating new n8n workflow execution requests.  
\- Stop accepting new scheduler control operations except those required for shutdown.  
\- Stop accepting new runtime registrations.  
\- Continue processing only lifecycle activity required for safe shutdown.

\#\#\# Stage 3 — Coordinate Internal Components

WF-001 SHALL notify relevant internal components that scheduler shutdown has begun.

This may include:

\- n8n execution coordination.  
\- Notification Engine shutdown notification.  
\- Operator Control Center status publication.  
\- Health-state publication.

WF-001 SHALL not assume that notifying another component proves that the component has stopped.

\#\#\# Stage 4 — Persist Shutdown State

WF-001 SHALL persist the scheduler shutdown initiation and final runtime condition through PostgreSQL before closing the database connection.

The persisted information SHALL include, where available:

\- Scheduler identity.  
\- Runtime instance identity.  
\- Shutdown reason.  
\- Shutdown initiation timestamp.  
\- Shutdown completion timestamp.  
\- Final operational condition.

\#\#\# Stage 5 — Final Health Publication

WF-001 SHALL publish its final durable health state before PostgreSQL connectivity is closed.

A final health record SHALL not depend on a database connection that has already been closed.

\#\#\# Stage 6 — Notification

WF-001 SHALL publish a shutdown notification request through the Notification Engine when the interface remains available.

Notification failure SHALL be logged and SHALL not prevent the remaining shutdown sequence.

\#\#\# Stage 7 — Communication Closure

WF-001 SHALL close internal communication channels in a controlled order.

The scheduler SHALL close:

\- n8n communication.  
\- Notification Engine communication.  
\- Operator Control Center communication.  
\- PostgreSQL connections.

PostgreSQL SHALL be closed only after required scheduler-owned state has been persisted.

\#\#\# Stage 8 — Process Termination

WF-001 SHALL terminate with a status that accurately indicates whether shutdown completed normally.

The process SHALL not remain indefinitely active after the configured shutdown period expires.

\#\# 6.3 Unexpected Termination

If WF-001 terminates without completing the shutdown sequence:

\- Docker health checks and external watchdog mechanisms SHALL detect the absence of healthy runtime information.  
\- The next startup SHALL identify that the previous shutdown was incomplete through persisted runtime information.  
\- Detailed recovery behavior SHALL be defined in the later execution-recovery phase.

WF-001 SHALL not claim a graceful shutdown when the final shutdown state was not durably persisted.

\#\# 6.4 Shutdown Idempotence

Repeated shutdown signals SHALL not create conflicting shutdown operations.

After shutdown begins:

\- Additional shutdown signals SHALL be recorded.  
\- The first valid shutdown sequence SHALL remain authoritative.  
\- New orchestration activity SHALL not resume.  
\- Finalization steps SHALL be safe to repeat where technically required.

\---

\# 7\. Runtime Assumptions

The Phase 1 runtime SHALL rely on the following assumptions.

\#\# 7.1 Deployment Assumptions

\- AHOS SHALL run through Docker Compose.  
\- The initial deployment SHALL target one laptop.  
\- The initial deployment SHALL target one operator.  
\- PostgreSQL SHALL run as the persistent database service.  
\- n8n SHALL run as the workflow execution service.  
\- WF-001 SHALL run as a dedicated Docker Compose service.  
\- Docker service names and internal networking SHALL be available.  
\- Required persistent volumes SHALL be configured outside the scheduler specification.  
\- The host SHALL provide sufficient resources for the configured deployment profile.

\#\# 7.2 Runtime Authority Assumptions

\- WF-001 SHALL be the sole scheduler authority.  
\- n8n SHALL not independently replace WF-001 scheduling authority.  
\- PostgreSQL SHALL be the authoritative persistence service for scheduler-owned information.  
\- The Notification Engine SHALL be the notification delivery authority.  
\- The Operator Control Center SHALL be the operator-command authority.

\#\# 7.3 Time Assumptions

\- Runtime timestamps SHALL use a consistent time standard.  
\- PostgreSQL and WF-001 SHALL use compatible time interpretation.  
\- Scheduling and lifecycle decisions SHALL not depend on an unverified local clock.  
\- Clock behavior, time zones, and execution timing policies SHALL be defined in the approved configuration and later scheduling sections.

\#\# 7.4 Network Assumptions

\- Internal Docker Compose communication SHALL normally be available.  
\- Temporary external internet loss SHALL not by itself invalidate local scheduler runtime.  
\- External provider availability SHALL not be assumed for core scheduler operation.  
\- Telegram availability SHALL not be assumed to be continuous.  
\- Notification failure SHALL remain distinct from scheduler failure.

\#\# 7.5 Persistence Assumptions

\- PostgreSQL data SHALL be persisted through an approved Docker volume.  
\- PostgreSQL backup and restore SHALL be governed by the AHOS backup policy.  
\- WF-001 SHALL not use process memory as the sole authoritative source of scheduler operation.  
\- Runtime memory MAY be used for temporary operational data, but durable scheduler-owned information SHALL be persisted through approved storage.

\#\# 7.6 Provider Independence Assumptions

WF-001 SHALL not depend on a single external provider for core scheduling.

The scheduler communication model SHALL permit replacement of:

\- Notification providers.  
\- n8n interface mechanisms.  
\- Database connection mechanisms.  
\- External monitoring mechanisms.

Provider-specific implementation details SHALL remain outside the scheduler’s core orchestration policy.

\#\# 7.7 Monitoring Assumptions

\- Docker health checks SHALL be available to observe WF-001 health.  
\- External watchdog mechanisms MAY be used to request container restart.  
\- WF-001 SHALL expose health information but SHALL not restart itself.  
\- Health monitoring SHALL remain separate from scheduler orchestration authority.

\#\# 7.8 Security Assumptions

\- Internal service communication SHALL use protected credentials or equivalent authentication.  
\- Secrets SHALL be supplied through approved secure configuration.  
\- Internal endpoints SHALL not be publicly exposed by default.  
\- The operator SHALL be the final authority for production control.  
\- WF-001 SHALL not possess or manage private trading-wallet keys.

\#\# 7.9 Resource Assumptions

\- CPU, RAM, disk, timeout, and communication thresholds SHALL be provided through approved configuration.  
\- WF-001 SHALL not assume a fixed hardware profile.  
\- Resource observations MAY be supplied by Docker or an approved monitoring component.  
\- Missing resource observations SHALL be treated as an explicit unavailable condition, not silently interpreted as normal capacity.

\---

\# 8\. Explicit Non-Responsibilities

WF-001 SHALL not perform the following responsibilities.

\#\# 8.1 Intelligence and Analysis

WF-001 SHALL not:

\- Discover tokens.  
\- Collect market intelligence.  
\- Analyze blockchain activity.  
\- Analyze social activity.  
\- Perform security analysis.  
\- Evaluate project quality.  
\- Calculate opportunity scores.  
\- Perform simulations.  
\- Generate AI-based interpretations.  
\- Produce trading recommendations.

\#\# 8.2 Portfolio and Trading

WF-001 SHALL not:

\- Manage portfolio positions.  
\- Calculate position sizes.  
\- Allocate capital.  
\- Execute trades.  
\- Manage wallet keys.  
\- Interact with trading wallets.  
\- Approve financial decisions.  
\- Replace the human operator.

\#\# 8.3 Workflow Business Logic

WF-001 SHALL not:

\- Implement the internal business logic of another workflow.  
\- Validate the analytical correctness of workflow outputs.  
\- Transform domain data into intelligence.  
\- Decide whether a token is safe or attractive.  
\- Modify workflow prompts or analytical rules autonomously.

\#\# 8.4 Operator Interface

WF-001 SHALL not:

\- Process Telegram commands directly.  
\- Authenticate raw operator messages.  
\- Interpret natural-language operator requests.  
\- Replace the Operator Control Center.  
\- Bypass operator approval requirements.  
\- Independently approve production modifications.

\#\# 8.5 Notification Delivery

WF-001 SHALL not:

\- Own Telegram delivery implementation.  
\- Own email delivery implementation.  
\- Generate general-purpose AHOS reports.  
\- Replace the Notification Engine.  
\- Treat notification delivery as proof of scheduler success.

\#\# 8.6 Database Administration

WF-001 SHALL not:

\- Own PostgreSQL installation.  
\- Perform database backup administration.  
\- Perform database migration administration.  
\- Redesign the AHOS database architecture autonomously.  
\- Delete historical scheduler records outside approved retention policy.  
\- Treat PostgreSQL as an autonomous scheduler.

\#\# 8.7 Infrastructure Recovery

WF-001 SHALL not:

\- Restart itself.  
\- Restart Docker.  
\- Restart PostgreSQL.  
\- Restart n8n.  
\- Replace Docker health checks.  
\- Replace external watchdog mechanisms.  
\- Assume that a service restart proves execution recovery.

\#\# 8.8 Distributed Deployment

Phase One WF-001 SHALL not:

\- Require Kubernetes.  
\- Require a cloud control plane.  
\- Require a distributed cluster.  
\- Require multiple laptops.  
\- Require enterprise message brokers.  
\- Require enterprise service discovery.  
\- Assume high-availability infrastructure beyond the approved Docker Compose deployment.

\#\# 8.9 Later-Phase Responsibilities

The following responsibilities are explicitly excluded from Phase 1:

\- Queue policy definition.  
\- Execution state-machine definition.  
\- Scheduler lock implementation.  
\- Retry policy definition.  
\- Timeout policy definition.  
\- Dependency resolution rules.  
\- Crash-recovery execution rules.  
\- Completion-event reconciliation rules.  
\- Database schema definition.  
\- Resource scheduling algorithms.  
\- Distributed fencing or leader-election implementation.

These responsibilities SHALL be defined in later approved sections of WF-001 Version 3.0.

\---

\# End of Phase 1 — Core Runtime Architecture

