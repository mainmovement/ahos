\# WF-001 Version 3.0

\#\# Phase 3 — Queue Scheduling & Dispatch Specification

\#\#\# \*\*Part 1 (Sections 22–24)\*\*

\*\*Status:\*\* Production Frozen Draft

\---

\# 22\. Phase 3 Purpose

\#\# 22.1 Objective

Phase 3 defines the scheduler queue responsible for selecting accepted executions, determining dispatch eligibility, coordinating execution claiming, enforcing execution limits, and initiating workflow dispatch.

Phase 3 SHALL operate entirely within the scheduler domain and SHALL NOT redefine execution lifecycle states established in Phase 2\.

\---

\#\# 22.2 Production Responsibilities

Phase 3 resolves the following production requirements:

\* Queue construction.  
\* Queue persistence.  
\* Execution eligibility evaluation.  
\* Priority ordering.  
\* Resource-aware scheduling.  
\* Queue processing.  
\* Atomic execution claiming.  
\* Duplicate-dispatch prevention.  
\* Queue starvation prevention.  
\* Queue overflow handling.  
\* Execution window enforcement.  
\* Queue recovery after restart.  
\* Queue observability.

\---

\#\# 22.3 Scope

Phase 3 begins after an execution has been accepted and persisted.

Phase 3 ends immediately before dispatch processing defined by the Phase 2 Dispatch Protocol.

Execution state transitions after dispatch SHALL remain exclusively governed by Phase 2\.

\---

\#\# 22.4 Out of Scope

The following responsibilities are explicitly excluded from Phase 3:

\* Workflow execution.  
\* Implementation of n8n workflows remains outside the scope of this specification.  
\* Retry execution logic.  
\* Failure recovery state transitions.  
\* Dependency graph evaluation (introduced in Phase 4).  
\* Historical analytics.

\---

\# 23\. Queue Logical Model

\#\# 23.1 Queue Definition

The scheduler queue SHALL be the logical set of executions stored in the PostgreSQL \`executions\` table that have not reached terminal states.

The queue is a logical representation derived by filtering execution state.

No dedicated queue table SHALL exist.

\---

\#\# 23.2 Queue Membership

Every accepted execution SHALL automatically become eligible for queue membership according to its execution state.

Queue membership SHALL always be computed from the current execution state.

\---

\#\# 23.3 Active Queue

The active queue SHALL include only non-terminal executions.

The following terminal states SHALL be excluded immediately upon transition:

\* \`completed\`  
\* \`failed\_terminal\`  
\* \`cancelled\`  
\* \`blocked\`  
\* \`dropped\`  
\* \`window\_missed\`  
\* \`expired\`

Terminal executions SHALL NOT participate in queue processing.

\---

\#\# 23.4 Queue Persistence

Every queue entry SHALL be persisted in PostgreSQL before the acceptance transaction commits and the execution becomes visible to queue processing.

Queue processing SHALL operate only on committed database records.

\---

\#\# 23.5 Queue Ordering

The queue SHALL NOT persist ordering.

Ordering SHALL be computed dynamically during every scheduler cycle.

No permanent ordering metadata SHALL exist.

Queue ordering SHALL be deterministic for identical execution states and scheduler configuration.

\---

\# 24\. Execution Eligibility

\#\# 24.1 Principle

Eligibility SHALL be evaluated independently during every scheduler orchestration cycle.

Eligibility SHALL be computed from current execution state, configuration, resource conditions, scheduling constraints, and workflow status.

Eligibility SHALL NEVER be assumed from previous evaluations.

\---

\#\# 24.2 Eligibility Prerequisites

An execution SHALL be eligible only if all of the following conditions are satisfied.

\#\#\# 1\. State Requirement

Execution state SHALL equal:

\`ready\`

\---

\#\#\# 2\. Schedule Requirement

Current scheduler time SHALL be greater than or equal to the scheduled execution time.

\---

\#\#\# 3\. Dependency Requirement

All required dependencies SHALL be satisfied in accordance with Phase 4 — Dependency Management.

Executions with unresolved or permanently unsatisfied dependencies SHALL NOT become eligible.  
\---

\#\#\# 4\. Resource Requirement

Sufficient execution capacity exists.

Execution capacity is defined strictly as the combination of:

\* Global concurrency limit not exceeded.  
\* Workflow concurrency limit not exceeded.  
\* Current resource mode permits execution of the execution priority.

\---

\#\#\# 5\. Queue Requirement

The execution SHALL NOT currently be owned by another active claim transaction or already be in the dispatching state.  
\---

\#\#\# 6\. Workflow Requirement

The workflow is enabled and no active operational policy prohibits dispatch.

Examples include:

\* Workflow disabled.  
\* Emergency stop.  
\* Manual pause.  
Operational policies SHALL be evaluated using the current workflow configuration.

The scheduler SHALL NOT maintain independent policy state.  
\---

\#\#\# 7\. Cancellation Requirement

Execution has not entered any cancellation state.

\---

\#\#\# 8\. Window Requirement

If an execution window is configured, the current scheduler time SHALL fall within the permitted execution window.

If no execution window is configured, this prerequisite SHALL be considered satisfied.

\---

\#\# 24.3 Re-evaluation

Eligibility SHALL be recalculated during every scheduler cycle.

Changes in configuration, execution state, scheduling constraints, or resources SHALL immediately affect eligibility.

\---

\#\# 24.4 Computed Property

Eligibility is a computed property.

Eligibility SHALL NOT be persisted as:

\* Database columns.  
\* Boolean flags.  
\* Cached eligibility indicators.  
\* Derived execution states.

Eligibility SHALL exist only during scheduler evaluation.

No persistent eligibility state SHALL exist.

\---

\#\# 24.5 Determinism

Given identical:

\* Execution state  
\* Scheduler time  
\* Configuration  
\* Resource observations  
\* Queue contents

WF-001 SHALL always produce identical eligibility decisions.  
Eligibility evaluation SHALL be free of side effects and SHALL NOT modify persistent execution state.

\---

عالی. در ادامه نسخه \*\*Production Frozen Draft\*\* را با همان سبک حقوقی و مهندسی ارائه می‌کنم.

\---

\# WF-001 Version 3.0

\#\# Phase 3 — Queue Scheduling & Dispatch Specification

\#\#\# \*\*Part 2A (Section 25)\*\*

\*\*Status:\*\* Production Frozen Draft

\---

\# 25\. Execution Priority

\---

\#\# 25.1 Objective

Execution priority defines the deterministic scheduling precedence used by WF-001 whenever multiple eligible executions compete for limited dispatch capacity.

Priority influences only dispatch selection order.

Priority SHALL NOT modify execution state transitions, execution ownership, retry behavior, timeout handling, reconciliation procedures, or workflow execution semantics.

\---

\#\# 25.2 Approved Priority Levels

WF-001 SHALL recognize only the following priority levels:

| Level      | Relative Order |  
| \---------- | \-------------- |  
| \`critical\` | Highest        |  
| \`high\`     | High           |  
| \`normal\`   | Default        |  
| \`low\`      | Lowest         |

No additional priority levels SHALL exist unless explicitly introduced by a future approved specification revision.

\---

\#\# 25.3 Priority Assignment

Every logical execution SHALL possess exactly one base priority.

Priority SHALL be assigned using the following precedence order:

1\. Explicit priority supplied during execution creation.  
2\. Workflow configuration field \`default\_priority\`.  
3\. Scheduler global default priority.

If none are specified, the priority SHALL default to:

\`\`\`  
normal  
\`\`\`

Priority SHALL be immutable unless modified by an approved operator action.

\---

\#\# 25.4 Priority Modification

An execution priority MAY be modified only through an approved operator command issued by the AHOS Operator Control Center.

Priority modification SHALL:

\* be logged,  
\* include timestamp,  
\* include operator identity,  
\* include previous priority,  
\* include new priority,  
\* take effect immediately,  
\* participate in the next scheduler cycle.

Priority modification SHALL NOT reset execution age, scheduling timestamps, or queue history.

\---

\#\# 25.5 Deterministic Dispatch Ordering

Whenever multiple executions are simultaneously eligible, WF-001 SHALL compute dispatch order using the following deterministic comparison sequence.

\#\#\# Comparison Level 1

Higher priority precedes lower priority.

\`\`\`  
critical  
↓

high  
↓

normal  
↓

low  
\`\`\`

\---

\#\#\# Comparison Level 2

Within identical priority levels,

earlier scheduled execution time SHALL take precedence.

\`\`\`  
scheduled\_time ASC  
\`\`\`

\---

\#\#\# Comparison Level 3

If scheduled execution times are identical,

earlier acceptance timestamp SHALL take precedence.

\`\`\`  
accepted\_at ASC  
\`\`\`

\---

\#\#\# Comparison Level 4

If acceptance timestamps are identical,

logical execution identifier SHALL be used as the deterministic final tie-breaker.

Identifier comparison SHALL follow the ordering rules defined by Phase 2\.

\---

\#\# 25.6 Stable Ordering

Scheduler ordering SHALL remain stable throughout an orchestration cycle.

No execution SHALL change relative position during the same cycle unless:

\* execution state changes,  
\* priority changes,  
\* execution becomes ineligible,  
\* execution is claimed,  
\* execution is cancelled.

Stable ordering SHALL be recomputed only at the beginning of the next scheduler orchestration cycle.

\---

\#\# 25.7 Priority Persistence

Only the base priority SHALL be stored in PostgreSQL.

Computed scheduling priority SHALL NOT be persisted.

Temporary scheduling calculations SHALL exist only during queue evaluation.

\---

\#\# 25.8 Priority Independence

Priority SHALL NOT override:

\* workflow enablement,  
\* execution windows,  
\* dependency requirements,  
\* resource restrictions,  
\* cancellation requests,  
\* queue ownership,  
\* concurrency limits.

Priority influences only dispatch ordering after all eligibility requirements have been satisfied.

\---

\#\# 25.9 Scheduler Determinism

Given identical:

\* queue contents,  
\* priorities,  
\* scheduler time,  
\* configuration,  
\* resource observations,

WF-001 SHALL always generate identical dispatch ordering.

No randomization SHALL be introduced.

No probabilistic ordering SHALL be permitted.

\---

\#\# 25.10 Compliance

All scheduler implementations SHALL produce identical ordering when provided identical execution sets and identical scheduler conditions.

Deviation from this ordering SHALL constitute non-compliance with the WF-001 Phase 3 specification.

\---  
WF-001 Version 3.0  
Phase 3 — Queue Scheduling & Dispatch Specification  
Part 2B (Section 26\)

Status: Production Frozen Draft

26\. Resource-Aware Execution Control  
26.1 Objective

WF-001 SHALL continuously evaluate system resource availability before initiating execution dispatch.

Resource-aware scheduling prevents system overload while maintaining deterministic dispatch behavior.

Resource evaluation SHALL occur before every dispatch decision.

26.2 Resource Observation

WF-001 SHALL receive resource observations from an approved observation source.

For the Phase 1 reference implementation, resource observations SHALL be read from the scheduler resource repository.

The repository MAY be implemented as a PostgreSQL table, external monitoring service, or another persistent source.

Each observation SHALL include the latest validated resource values available to the scheduler.

Resource observations SHALL be read-only.

WF-001 SHALL NOT directly modify resource measurements.

26.3 Required Resource Metrics

The following metrics SHALL be available for every scheduler cycle:

CPU utilization  
Memory utilization  
Disk utilization  
Database availability  
Scheduler heartbeat age

Additional metrics MAY be introduced by future specification revisions.

Unknown metrics SHALL NOT affect scheduler decisions.

26.4 Missing Resource Metrics

If any required metric is unavailable, NULL, stale, or cannot be validated:

That metric SHALL be considered unavailable.  
Missing observations SHALL NEVER be interpreted as healthy capacity.  
Scheduler decisions SHALL always use the most restrictive interpretation.

If resource observations cannot be obtained from the configured scheduler resource repository, the scheduler SHALL immediately enter the unavailable resource mode.

26.5 Resource Modes

WF-001 SHALL operate in exactly one global resource mode.

The effective resource mode SHALL equal the most restrictive mode produced by any required resource metric.

The approved resource modes are:

Mode	Meaning  
normal	All required resources are within normal operating limits.  
constrained	Resources remain operational but dispatch capacity is reduced.  
critical	Resources approach unsafe operating limits. Only high-priority dispatch is permitted.  
unavailable	Resource observations cannot be trusted or scheduler safety cannot be validated.

No additional modes SHALL exist.

26.6 Resource Mode Behavior  
Normal

Scheduler SHALL operate without dispatch restrictions.

All eligible executions MAY be dispatched.

Constrained

Scheduler SHALL reduce dispatch throughput according to configured concurrency limits.

Low-priority executions MAY be delayed.

Higher priorities retain precedence.

Critical

Scheduler SHALL permit dispatch only when explicitly allowed by the configured priority policy.

Default behavior SHALL permit only:

critical  
high

priority executions.

Normal and low priorities SHALL remain queued.

Unavailable

Scheduler SHALL initiate no new dispatches.

Existing executions SHALL continue independently.

The scheduler SHALL repeatedly attempt resource recovery during each orchestration cycle.

26.7 Resource Mode Determination

Each required resource metric SHALL independently evaluate its own operating condition.

The scheduler SHALL compute the effective mode using the following precedence:

unavailable  
      ↑  
critical  
      ↑  
constrained  
      ↑  
normal

The highest restriction SHALL always win.

Example:

CPU	Memory	Database	Effective Mode  
normal	constrained	normal	constrained  
normal	critical	constrained	critical  
unavailable	normal	normal	unavailable  
26.8 Mode Transition Stability

To prevent oscillation between resource modes, WF-001 SHALL apply hysteresis.

Mode transitions SHALL use the following configuration parameters:

resource\_entry\_threshold  
resource\_recovery\_threshold  
resource\_minimum\_dwell\_seconds

A resource mode SHALL NOT change until all transition conditions remain satisfied for at least the configured minimum dwell period.

Hysteresis SHALL be evaluated independently for each required resource metric before computing the effective global resource mode.

26.9 Global Concurrent Execution Limit

WF-001 SHALL enforce a global concurrent execution limit.

The maximum number of concurrent executions SHALL be defined by:

global\_max\_concurrent\_executions

No additional execution SHALL be dispatched once the limit has been reached.

26.10 Workflow Concurrent Execution Limit

Each workflow MAY define its own maximum concurrent execution limit.

The workflow limit SHALL NEVER exceed the global limit.

If either concurrency limit is reached, the execution SHALL remain in the ready state until capacity becomes available.

26.11 Concurrent Execution Definition

An execution SHALL be considered concurrent whenever its execution state is one of the following:

dispatching  
dispatch\_unknown  
running  
completion\_pending  
timeout\_observed  
termination\_pending  
cancel\_requested  
reconciliation\_required

All remaining states SHALL NOT contribute to concurrency calculations.

26.12 Dispatch Capacity Evaluation

Before every dispatch attempt, WF-001 SHALL verify all of the following:

Global concurrency limit not exceeded.  
Workflow concurrency limit not exceeded.  
Current resource mode permits the execution priority.  
Scheduler is not operating in unavailable mode.

Failure of any single condition SHALL make the execution temporarily ineligible.

Dispatch capacity evaluation SHALL be performed immediately before execution claiming to ensure decisions are based on the latest committed scheduler state.

26.13 Resource Evaluation Determinism

Given identical:

resource observations,  
execution set,  
configuration,  
scheduler time,

WF-001 SHALL always produce identical dispatch decisions.

No probabilistic evaluation SHALL be permitted.

26.14 Configuration Parameters

The following configuration parameters SHALL govern resource-aware scheduling:

Parameter	Purpose  
global\_max\_concurrent\_executions	Maximum concurrent executions across all workflows  
resource\_entry\_threshold	Threshold for entering a more restrictive resource mode  
resource\_recovery\_threshold	Threshold for returning to a less restrictive mode  
resource\_minimum\_dwell\_seconds	Minimum duration before changing resource mode  
system\_resources\_refresh\_seconds	Maximum age of valid resource observations

All configuration parameters SHALL be centrally managed and SHALL be applied during every scheduler cycle.

26.15 Compliance

A compliant implementation SHALL:

produce identical resource decisions for identical observations,  
enforce concurrency limits consistently,  
honor the most restrictive resource mode,  
never dispatch while operating in unavailable,  
evaluate resource conditions before every dispatch cycle.

Deviation from these rules SHALL constitute non-compliance with the WF-001 Phase 3 specification.

WF-001 Version 3.0  
Phase 3 — Queue Scheduling & Dispatch Specification  
Part 3A (Section 27\)

Status: Production Frozen Draft

27\. Queue Processing  
27.1 Scheduler Orchestration Cycle

WF-001 SHALL execute one deterministic scheduler orchestration cycle for each scheduler trigger.

The scheduler trigger MAY be implemented using a cron-based trigger, timer, external scheduler, or equivalent orchestration mechanism.

The orchestration mechanism is implementation-specific and outside the scope of this specification.

For the Phase 1 reference implementation, scheduler triggers SHALL be generated by the n8n Scheduler Trigger.

Each scheduler cycle SHALL execute independently.

A scheduler cycle SHALL NOT begin until the previous cycle has completed.

Concurrent scheduler cycles SHALL NOT be permitted.

27.2 Queue Processing Sequence

Each scheduler orchestration cycle SHALL execute the following steps in the specified order.

Failure of one step SHALL NOT modify the execution order of subsequent cycles.

Step 1 — Load Scheduler Configuration

WF-001 SHALL load the active scheduler configuration.

The configuration SHALL include, at minimum:

Scheduler cycle interval.  
Concurrency limits.  
Resource thresholds.  
Queue overflow policy.  
Priority aging configuration.  
Window policy configuration.

If configuration cannot be loaded, the scheduler SHALL abort the current cycle, log the failure, and retry during the next scheduler cycle.

Step 2 — Load Resource Observations

WF-001 SHALL retrieve the most recent validated resource observations.

The effective resource mode SHALL be computed according to Section 26\.

If the effective resource mode is unavailable, the scheduler SHALL continue queue observation and monitoring but SHALL NOT initiate any execution dispatch during the current scheduler cycle.  
Step 3 — Load Active Queue

WF-001 SHALL retrieve all non-terminal executions from the PostgreSQL executions table.

Only executions whose state is not terminal SHALL participate in queue processing.

Queue loading SHALL use committed database data only.

Step 4 — Evaluate Eligibility

Each execution SHALL be evaluated independently.

An execution SHALL remain eligible only if all requirements defined in Section 24 are satisfied.

These evaluations SHALL include:

State validation.  
Schedule validation.  
Resource validation.  
Workflow enablement validation.  
Cancellation validation.  
Execution window validation.  
Concurrency validation.

Dependency validation SHALL be performed in accordance with Phase 4 — Dependency Management.

Executions with unresolved or permanently unsatisfied dependencies SHALL NOT become eligible for dispatch.

The scheduler SHALL consume only the dependency eligibility result produced by the dependency management subsystem.

Executions failing any prerequisite SHALL remain in the queue unless another provision of this specification explicitly requires an execution state transition.

Step 5 — Build Dispatch Candidate List

Eligible executions SHALL be inserted into an in-memory dispatch candidate list.

This list SHALL exist only for the duration of the current scheduler cycle.

The dispatch candidate list SHALL NOT be persisted.

Executions SHALL then be ordered according to Section 25\.

Step 6 — Claim Selected Executions

Each execution SHALL be claimed independently.

Each claim SHALL execute within its own PostgreSQL transaction.

No transaction SHALL claim more than one execution.

Claiming SHALL follow the protocol defined in Section 28\.

Only successfully committed claims SHALL be considered claimed by the scheduler.

Successful execution claims SHALL immediately remove the execution from further claim consideration during the current scheduler cycle.

Step 7 — Initiate Dispatch

After a successful claim:

Dispatch SHALL be initiated according to the Phase 2 Dispatch Protocol.  
Queue processing SHALL NOT directly execute workflows.  
Queue processing SHALL only initiate dispatch.

Dispatch outcomes SHALL be processed according to Phase 2\.

Step 8 — Complete Cycle

After all dispatch candidates have been processed:

Scheduler metrics SHALL be updated.  
Queue metrics SHALL be persisted.  
Health information SHALL be refreshed.  
The scheduler SHALL wait until the next configured cycle interval.  
27.3 Deterministic Queue Ordering

Dispatch candidates SHALL always be processed in deterministic order.

Ordering SHALL follow:

Priority.  
Scheduled execution time.  
Acceptance timestamp.  
Logical execution identifier.

No execution SHALL bypass another execution with higher precedence.

27.4 Queue Processing Atomicity

Each claimed execution SHALL be processed independently.

Failure during processing of one execution SHALL NOT interrupt processing of remaining dispatch candidates.

Each execution SHALL either:

complete claiming successfully, or  
roll back completely.

Partial claim completion SHALL NOT occur.

27.5 Scheduler Failure Handling

If an unexpected processing error occurs during a scheduler cycle:

The current execution transaction SHALL be rolled back.  
The failure SHALL be logged.  
Scheduler metrics SHALL record the processing error.  
Remaining dispatch candidates SHALL continue processing whenever safe.

The scheduler SHALL continue with the next orchestration cycle unless a fatal scheduler activation failure prevents operation.

27.6 Queue Visibility

Queue processing SHALL operate exclusively on committed execution records.

Uncommitted database changes SHALL NEVER be visible to queue evaluation.

Executions accepted after queue loading SHALL become visible during the next scheduler cycle.

27.7 Dispatch Independence

Queue processing SHALL NOT assume successful workflow execution.

Dispatch initiation and workflow completion are independent operations governed by Phase 2\.

Queue processing responsibility ends immediately after successful dispatch initiation.

27.8 Scheduler Determinism

Given identical:

Queue contents,  
Configuration,  
Resource observations,  
Scheduler time,

WF-001 SHALL always generate the identical dispatch candidate list and identical dispatch order.

No randomization SHALL be introduced.

Deterministic processing SHALL remain independent of database retrieval order.

27.9 Compliance

A compliant implementation SHALL:

Execute exactly one orchestration cycle at a time.  
Evaluate every execution independently.  
Build a temporary dispatch candidate list.  
Claim executions independently.  
Never dispatch without a successful claim.  
Continue processing after recoverable errors.  
Preserve deterministic dispatch ordering.

Deviation from these requirements SHALL constitute non-compliance with the WF-001 Phase 3 specification.

WF-001 Version 3.0  
Phase 3 — Queue Scheduling & Dispatch Specification  
Part 3B (Section 28\)

Status: Production Frozen Draft

28\. Queue Claiming & Concurrency  
28.1 Objective

Before any execution is dispatched, WF-001 SHALL establish exclusive ownership of the logical execution.

Queue claiming guarantees that a logical execution SHALL be dispatched at most once during a scheduler cycle.

Claiming SHALL eliminate duplicate-dispatch conditions while preserving deterministic scheduler behavior.

28.2 Claiming Protocol

Each execution claim SHALL be performed independently.

The following procedure SHALL be executed for every selected execution.

Step 1 — Begin Transaction

WF-001 SHALL begin a PostgreSQL transaction using the READ COMMITTED isolation level.

Each claim SHALL use a separate and independent transaction.

No transaction SHALL claim more than one execution.

Step 2 — Acquire Row Ownership

WF-001 SHALL retrieve the execution row using:

SELECT ...  
FOR UPDATE SKIP LOCKED;

The selected row SHALL become exclusively owned by the current transaction until commit or rollback.

Rows already locked by another transaction SHALL be skipped automatically.

Waiting for locked rows SHALL NOT occur.

Step 3 — Validate Current State

Immediately after acquiring the row lock, WF-001 SHALL verify that the execution remains eligible for dispatch.

The following SHALL be revalidated:

Current execution state.  
Cancellation status.  
Resource eligibility.  
Workflow enablement.  
Execution window.  
Concurrency limits.

If any validation fails, the transaction SHALL be rolled back.

No dispatch SHALL occur.

Step 4 — Claim Execution

If validation succeeds:

The execution SHALL transition atomically from:

ready

to

dispatching

The claim timestamp SHALL be recorded.

The claiming scheduler instance SHALL be recorded if applicable.

Step 5 — Commit Transaction

After the state transition has been successfully persisted:

The transaction SHALL commit.

Only after a successful commit MAY dispatch begin.

28.3 Duplicate-Dispatch Prevention

Duplicate dispatch SHALL be prevented through PostgreSQL row-level locking.

The locking mechanism SHALL use:

SELECT ... FOR UPDATE SKIP LOCKED

Only the transaction holding the row lock MAY transition an execution into the dispatching state.

Any scheduler cycle encountering a locked execution SHALL silently skip that execution and continue processing remaining candidates.

28.4 Claim Transaction Timeout

Claim transactions SHALL complete within the duration defined by:

claim\_transaction\_timeout\_seconds

If the timeout is exceeded:

the transaction SHALL be rolled back,  
the execution SHALL remain unchanged,  
the timeout SHALL be logged,  
queue processing SHALL continue with the next execution.  
28.5 Transaction Rollback

Rollback SHALL restore the execution to its pre-claim state.

No partial claim SHALL remain visible after rollback.

Rollback SHALL occur whenever:

validation fails,  
transaction timeout occurs,  
database error occurs,  
commit fails,  
unexpected exception occurs.  
28.6 Claim Atomicity

Claiming SHALL be fully atomic.

Exactly one of the following outcomes SHALL occur:

Successful claim and committed state transition.  
Complete rollback with no observable modification.

Intermediate claim states SHALL NOT exist.

28.7 Concurrency Safety

The specification permits concurrent scheduler instances in future deployments.

The Phase 1 reference implementation assumes a single scheduler instance.

Concurrency guarantees SHALL remain valid if multiple scheduler instances are introduced in future versions. 

However:

only one worker MAY successfully claim a specific execution,  
duplicate claims SHALL NOT occur,  
duplicate dispatches SHALL NOT occur.

Concurrency safety SHALL rely solely on PostgreSQL transactional guarantees.

The reference deployment consists of a single n8n instance with PostgreSQL coordination.  
28.8 Dispatch Authorization

Successful claiming SHALL be the sole authorization required to initiate dispatch.

WF-001 SHALL NOT dispatch any execution that has not been successfully claimed.

The dispatch process SHALL verify that the execution state is dispatching before initiating workflow execution.

28.9 Failure Recovery

If the scheduler terminates after a successful claim but before dispatch completion:

The execution SHALL remain in the dispatching state.

Recovery SHALL be performed exclusively during the scheduler startup reconciliation procedure defined in Phase 2 and Section 32 of this specification before normal scheduler processing resumes.

The queue SHALL NOT automatically reclaim such executions during ordinary scheduler cycles.

28.10 Deterministic Claim Behavior

Given identical:

queue contents,  
scheduler configuration,  
transaction ordering,  
resource observations,

WF-001 SHALL always produce identical claim outcomes.

Database locking SHALL ensure exclusive ownership of each execution.

Deterministic scheduler behavior SHALL be defined in terms of execution correctness and duplicate-dispatch prevention rather than scheduler worker identity.

28.11 Compliance

A compliant implementation SHALL:

use READ COMMITTED transaction isolation,  
use SELECT ... FOR UPDATE SKIP LOCKED,  
claim exactly one execution per transaction,  
commit before dispatch,  
never dispatch without a successful claim,  
roll back completely upon failure,  
prevent duplicate dispatch under concurrent scheduler execution.

Failure to satisfy these requirements SHALL constitute non-compliance with the WF-001 Phase 3 specification.  
Phase 3 — Queue Scheduling & Dispatch Specification  
Section 29 — Queue Starvation Prevention

Status: Production Frozen Draft

29\. Queue Starvation Prevention  
29.1 Objective

WF-001 SHALL ensure that eligible executions are not indefinitely prevented from dispatch due to continuous arrival of higher-priority executions.

The starvation prevention mechanism SHALL preserve deterministic scheduling while maintaining priority-based execution order.

Starvation prevention SHALL NOT override critical safety constraints, execution eligibility, concurrency limits, or resource restrictions.

29.2 Principles

Starvation prevention SHALL satisfy the following principles:

Priority ordering remains the primary scheduling rule.  
Long-waiting executions SHALL gradually gain dispatch preference.  
No execution SHALL bypass eligibility validation.  
Aging SHALL never alter the stored execution priority.  
Aging SHALL remain deterministic.  
Starvation handling SHALL be repeatable under identical scheduler conditions.  
29.3 Starvation Detection

An execution SHALL be considered starved only if all of the following conditions are simultaneously satisfied:

The execution is currently in the ready state.  
The execution satisfies all eligibility requirements defined in Section 24\.  
The execution has remained continuously in the ready state longer than the configuration parameter:  
starvation\_threshold\_seconds  
The execution has not previously entered any dispatch attempt.

Executions that temporarily leave the ready state SHALL restart starvation timing upon re-entering the ready state.

29.4 Dynamic Priority Aging

Priority aging SHALL be calculated dynamically during every scheduler cycle.

No aging value SHALL be persisted in PostgreSQL.

No execution SHALL contain an "aged priority" field.

The scheduler SHALL compute an effective scheduling priority using:

Base Priority  
Ready State Duration

The computed priority SHALL exist only during scheduler evaluation.

After dispatch evaluation completes, the computed value SHALL cease to exist.

Aging Rules

Low priority executions SHALL become equivalent to Normal priority after:

low\_priority\_aging\_seconds

Normal priority executions SHALL become equivalent to High priority after:

normal\_priority\_aging\_seconds

High priority executions SHALL NOT age into Critical priority.

Critical priority SHALL remain immutable.

29.5 Effective Scheduling Priority

Dispatch ordering SHALL always use:

Effective Priority (after aging computation)  
Scheduled Time  
Acceptance Timestamp  
Logical Execution ID

The stored Base Priority SHALL never be modified.

29.6 Aging Calculation

During each scheduler cycle:

DynamicAgingAdjustment SHALL be computed deterministically from the ready state duration and the configured aging thresholds defined in Section 29.4.

The adjustment SHALL be deterministic and SHALL NOT exceed one priority level promotion.

DynamicAgingAdjustment SHALL be computed exclusively from:

Ready state duration

Configured aging thresholds

No additional inputs SHALL influence aging.

29.7 Aging Reset

Priority aging SHALL automatically reset whenever an execution leaves the ready state.

Examples include:

dispatching  
cancelled  
blocked  
waiting\_dependency  
completed

Re-entering ready SHALL begin a completely new aging period.

Previous waiting duration SHALL NOT be reused.

29.8 Reserved Capacity

WF-001 MAY optionally reserve dispatch capacity for lower priority executions.

If enabled:

Reserved capacity SHALL be applied only after execution eligibility evaluation and before final dispatch candidate selection.

The reserved dispatch ratio SHALL be defined by configuration.

Reservation SHALL never reduce dispatch opportunities for Critical priority executions.

If reserved capacity is disabled, standard priority scheduling SHALL apply without reservation.

29.9 Fair Dispatch

Fair dispatch SHALL satisfy all of the following:

Higher priority executions SHALL continue to receive preference.  
Lower priority executions SHALL eventually receive dispatch opportunities.  
Scheduler determinism SHALL remain unchanged.  
Starvation prevention SHALL never violate execution eligibility.  
29.10 Observability

WF-001 SHALL expose starvation-related metrics including:

Current starved execution count.  
Longest ready duration.  
Average ready duration.  
Number of aging promotions computed.  
Dispatches influenced by aging.

These metrics SHALL be recorded for operational monitoring.

29.11 Failure Conditions

Starvation prevention SHALL NOT:

dispatch ineligible executions,  
ignore resource restrictions,  
ignore concurrency limits,  
modify stored execution priority,  
create additional execution states,  
persist temporary aging calculations.

Violation of any requirement SHALL constitute non-compliance with this specification.

29.12 Compliance

A compliant implementation SHALL:

compute aging dynamically,  
never persist aged priorities,  
detect starvation using starvation\_threshold\_seconds,  
apply deterministic ordering,  
reset aging after leaving ready,  
preserve stored base priority,  
maintain repeatable scheduling behavior.

Failure to satisfy these requirements SHALL constitute non-compliance with WF-001 Phase 3\.

Phase 3 — Queue Scheduling & Dispatch Specification  
Section 30 — Queue Overflow Handling

Status: Production Frozen Draft

30\. Queue Overflow Handling  
30.1 Objective

WF-001 SHALL continuously monitor active queue capacity to prevent uncontrolled queue growth.

Queue overflow handling SHALL preserve scheduler stability, deterministic behavior, and predictable resource utilization.

Overflow handling SHALL never compromise execution integrity or transactional consistency.

30.2 Queue Size Calculation

Queue capacity SHALL be calculated exclusively from logical executions currently in non-terminal states.

The active queue size SHALL equal:

COUNT(executions)  
WHERE state NOT IN (  
    completed,  
    failed\_terminal,  
    cancelled,  
    blocked,  
    dropped,  
    window\_missed,  
    expired  
)

The following states SHALL contribute to active queue capacity:

accepted  
waiting\_dependency  
ready  
dispatching  
dispatch\_unknown  
running  
completion\_pending  
timeout\_observed  
termination\_pending  
cancel\_requested  
reconciliation\_required

Terminal executions SHALL be excluded immediately upon entering a terminal state.

No archival retention period SHALL affect queue size calculations.

30.3 Overflow Detection

Queue overflow SHALL be detected whenever:

ActiveQueueSize \>= max\_active\_queue\_size

where:

max\_active\_queue\_size

is a mandatory scheduler configuration parameter.

For the Version 1 implementation, overflow detection SHALL be evaluated during each n8n scheduler workflow execution.  
Overflow SHALL NOT interrupt executions already in progress.

30.4 Overflow Policies

The scheduler SHALL apply the policy defined by:

queue\_overflow\_policy

The following policy values are permitted.

reject\_new

New execution requests SHALL be rejected immediately.

Existing queued executions SHALL continue normally.

Rejected requests SHALL be logged with rejection reason:

queue\_full

reject\_low\_priority

New executions having priority:

low

SHALL be rejected.

Normal, High, and Critical priority execution requests SHALL continue to be accepted only if capacity becomes available before their admission is evaluated.

drop\_oldest\_low\_priority

The oldest execution SHALL be determined by accepted\_at in ascending order.

If accepted\_at values are identical, execution\_id SHALL be used as the deterministic tie-breaker.

If overflow occurs:

The scheduler MAY remove the oldest execution satisfying all of the following conditions:

• priority \= low  
• state \= accepted

The drop operation and the admission of the new execution SHALL occur within the same PostgreSQL transaction to preserve queue consistency and prevent transient capacity violations.

Dropped executions SHALL transition to:

dropped

The drop reason SHALL be recorded.

Only one execution SHALL be dropped for each newly accepted execution.

block\_new\_until\_capacity

New execution requests SHALL NOT be accepted while overflow exists.

The requester SHALL receive a temporary rejection indicating:

queue\_full\_retry\_later

No additional queue state SHALL be introduced.

The requester MAY retry after capacity becomes available.  
30.5 Overflow Recovery

Overflow mode SHALL terminate automatically when:

ActiveQueueSize \< max\_active\_queue\_size

No manual intervention SHALL be required.

Previously rejected executions SHALL NOT be automatically recreated.

30.6 Overflow Logging

Each overflow event SHALL record:

Timestamp  
Queue size  
Configured capacity  
Overflow policy  
Number of rejected executions  
Number of dropped executions  
Recovery timestamp

Overflow events SHALL be persisted for operational analysis.

30.7 Dispatch During Overflow

Dispatch SHALL continue through the approved n8n workflow execution mechanism.

Overflow SHALL affect only admission of new executions unless the selected overflow policy explicitly removes queued executions.

Dispatch ordering SHALL remain unchanged.

30.8 Overflow Metrics

WF-001 SHALL expose at least the following metrics:

Current queue size  
Maximum queue capacity  
Overflow state  
Overflow event count  
Rejected execution count  
Dropped execution count  
Overflow duration

These metrics SHALL be available to scheduler observability.

30.9 Failure Conditions

Overflow handling SHALL NOT:

terminate running executions,  
violate execution ordering,  
corrupt queue consistency,  
bypass transaction safety,  
create undefined execution states.

Queue overflow SHALL affect admission control only.

30.10 Compliance

A compliant implementation SHALL:

calculate queue size exclusively from non-terminal executions,  
detect overflow using max\_active\_queue\_size,  
apply the configured queue\_overflow\_policy,  
exclude terminal executions immediately,  
preserve deterministic dispatch ordering,  
log all overflow events,  
recover automatically when capacity becomes available.

Failure to satisfy these requirements SHALL constitute non-compliance with the WF-001 Phase 3 specification.

Phase 3 — Queue Scheduling & Dispatch Specification  
Section 31 — Execution Window Policy

Status: Production Frozen Draft

31\. Execution Window Policy  
31.1 Objective

WF-001 SHALL support execution windows that restrict when a workflow is permitted to dispatch.

Execution windows SHALL be evaluated immediately before dispatch eligibility is confirmed.

Execution windows SHALL control dispatch timing only.

Acceptance, queue persistence, scheduling, priority calculation, starvation detection, and recovery SHALL remain unaffected.

31.2 Window Definition

A workflow MAY define one or more execution windows.

Each execution window SHALL specify:

permitted weekdays,  
permitted time ranges,  
evaluation timezone,  
activation status.

Window configuration SHALL be stored as part of the workflow configuration.

The internal configuration format is outside the scope of Phase 3\.

Phase 3 requires only that window evaluation deterministically returns either:

Allowed  
Not Allowed  
31.3 Time Source

Window evaluation SHALL use the current scheduler time.

If a timezone is explicitly configured for the workflow, evaluation SHALL use that timezone.

Otherwise, evaluation SHALL use UTC.

All window evaluations SHALL use the same scheduler clock during a scheduler cycle.

31.4 Window Eligibility

An execution SHALL satisfy the window requirement when:

no execution window is configured,

OR

the current scheduler time falls within a permitted execution window.

Executions outside a permitted window SHALL remain in the ready state.

The scheduler SHALL reevaluate window eligibility during every scheduler orchestration cycle until the execution becomes eligible or reaches a terminal state defined by this specification.

They SHALL NOT transition to another execution state solely because of an unavailable execution window.

Window evaluation SHALL be repeated during every scheduler cycle.

31.5 Emergency Override

Critical priority executions MAY bypass execution window restrictions.

Emergency override SHALL be permitted only when:

allow\_critical\_window\_override \= true

is configured for the workflow.

Every emergency override SHALL be audited.

The audit record SHALL include at minimum:

Execution ID  
Workflow ID  
Timestamp  
The audit record SHALL include at minimum: Execution ID, Workflow ID, Timestamp, Override Initiator (operator or system), and Override Reason.  
Override reason

Logging MAY additionally be performed for operational diagnostics.

Emergency override SHALL affect window validation only.

All other eligibility requirements SHALL remain mandatory.

31.6 Window Miss Handling

An execution waiting for a valid execution window SHALL continue remaining in the ready state until:

a valid execution window becomes available,

OR

the execution exceeds the maximum permitted scheduling delay.

If the execution exceeds:

max\_schedule\_delay

it SHALL transition to the terminal state:

window\_missed

The transition SHALL be permanent.

31.7 Delayed Schedule Handling

Scheduler downtime or delayed scheduler recovery MAY cause execution evaluation to occur after the scheduled dispatch time.

After scheduler recovery:

Executions SHALL be evaluated immediately.

If:

CurrentTime \- ScheduledTime \> max\_schedule\_delay

the execution SHALL transition to:

expired

Otherwise:

the execution SHALL continue normal eligibility evaluation.

31.8 Window Evaluation Order

Window validation SHALL occur only after:

State validation  
Dependency validation (when Phase 4 is available)  
Resource validation  
Concurrency validation

Window validation SHALL be the final eligibility validation performed before execution claiming begins.

31.9 Window Logging

The scheduler SHOULD log at least the following window-related decisions:

window accepted,  
window rejected,  
emergency override,  
window\_missed transition,  
expired transition.

Logging SHALL NOT modify scheduling behavior.

31.10 Failure Conditions

Window evaluation SHALL NOT:

alter execution priority,  
modify scheduling order,  
bypass concurrency limits,  
bypass resource restrictions,  
bypass dependency validation,  
bypass state validation.

Window handling SHALL affect dispatch eligibility only.

31.11 Compliance

A compliant implementation SHALL:

evaluate windows every scheduler cycle,  
use deterministic scheduler time,  
support workflow-specific timezones,  
leave executions in ready while waiting for a valid window,  
transition overdue executions to window\_missed,  
transition excessively delayed executions to expired,  
support optional critical emergency override,  
preserve deterministic scheduling behavior.

Failure to satisfy these requirements SHALL constitute non-compliance with the WF-001 Phase 3 specification.

Phase 3 — Queue Scheduling & Dispatch Specification  
Section 32 — Queue Recovery After Restart

Status: Production Frozen Draft

32\. Queue Recovery After Restart  
32.1 Objective

WF-001 SHALL automatically recover queue processing following any scheduler restart.

Recovery SHALL restore deterministic scheduler operation without introducing duplicate dispatches, skipped executions, or inconsistent execution states.

Recovery SHALL complete before normal queue processing resumes.

32.2 Startup Recovery Sequence

Immediately before the first scheduler orchestration cycle following process startup or deployment initialization, recovery SHALL execute. WF-001 SHALL execute the following recovery sequence exactly once.

No scheduler cycle, including eligibility evaluation or dispatch processing, SHALL begin until the entire recovery sequence has completed successfully.

Recovery SHALL execute sequentially in the following order:

Verify PostgreSQL connectivity.  
Load scheduler configuration.  
Load workflow configuration.  
Complete Phase 2 crash reconciliation for every unresolved execution attempt.  
Wait until reconciliation has completed successfully.

If dependency management is enabled (Phase 4), dependency recovery SHALL complete before execution eligibility is recalculated.

Recalculate execution eligibility.

Recalculate resource mode.

Resume normal queue processing.

No dispatch cycle SHALL begin before recovery completes.

Recovery SHALL be single-threaded.

32.3 Crash Reconciliation

Crash reconciliation SHALL be performed exclusively according to Phase 2\.

Phase 3 SHALL NOT modify reconciliation logic.

Phase 3 SHALL wait until reconciliation reports completion.

Executions requiring reconciliation SHALL remain unavailable for dispatch until reconciliation finishes.

The scheduler SHALL NOT dispatch any execution currently in:

reconciliation\_required  
dispatch\_unknown  
termination\_pending  
completion\_pending

32.4 Queue Reconstruction

The scheduler SHALL reconstruct the active queue directly from the executions table.

No queue snapshot SHALL be restored.

No serialized queue image SHALL be loaded.

The reconstructed queue SHALL include every execution whose current state is a non-terminal execution state as defined in Section 23.3.

Terminal executions SHALL remain excluded.

Queue ordering SHALL be recalculated using the standard dispatch ordering rules.

32.5 Eligibility Recalculation

After queue reconstruction:

Eligibility SHALL be recomputed for every execution.

Previously cached eligibility SHALL NOT be reused.

Eligibility SHALL be determined solely from:

current execution state,  
dependency status,  
resource mode,  
execution window,  
workflow configuration,  
scheduler configuration.

Eligibility SHALL NOT be persisted.

32.6 Delayed Scheduled Executions

Executions whose scheduled dispatch time has already passed SHALL be evaluated immediately after recovery.

If:

CurrentTime \- ScheduledTime \<= max\_schedule\_delay

the execution SHALL continue normal eligibility evaluation.

Otherwise:

the execution SHALL transition immediately to:

expired

Expired executions SHALL become terminal immediately.

32.7 Running Executions

Executions already confirmed as:

running

SHALL remain counted as concurrent executions.

Their lifecycle SHALL continue exclusively under Phase 2\.

Phase 3 SHALL NOT attempt to redispatch them.

32.8 Ready Executions

Executions currently in:

ready

SHALL immediately participate in the first scheduler cycle after recovery.

Their priority SHALL be recalculated.

Priority aging SHALL be recalculated dynamically.

Window validation SHALL be repeated.

Resource validation SHALL be repeated.

32.9 Recovery Failure

If recovery cannot complete successfully:

WF-001 SHALL remain unavailable for queue dispatch.

The scheduler SHALL repeatedly retry recovery.

Dispatch SHALL remain disabled until:

PostgreSQL connectivity exists,  
configuration is valid,  
reconciliation completes.

Partial recovery SHALL NOT permit dispatch.

32.10 Recovery Logging

Recovery SHALL record at minimum:

startup timestamp,  
recovery start,  
recovery completion,  
recovery duration,  
reconciliation duration,  
reconstructed queue size,  
expired executions,  
recovery failures.

Recovery logging SHALL NOT modify scheduler behavior.

32.11 Recovery Consistency Guarantees

Recovery SHALL guarantee:

no duplicate dispatch,  
no lost execution,  
deterministic queue reconstruction,  
deterministic priority recalculation,  
deterministic eligibility recalculation,  
deterministic dispatch ordering.

Recovery SHALL be idempotent.

Repeated scheduler restarts SHALL produce identical reconstructed queue state when the underlying database has not changed.

32.12 Compliance

A compliant implementation SHALL:

reconstruct the queue directly from PostgreSQL,  
complete crash reconciliation before dispatch,  
avoid restoring serialized queue snapshots,  
recalculate eligibility after every restart,  
recalculate priority dynamically,  
expire excessively delayed executions,  
prevent dispatch until recovery succeeds,  
guarantee deterministic recovery.

Failure to satisfy these requirements SHALL constitute non-compliance with the WF-001 Phase 3 specification.

Phase 3 — Queue Scheduling & Dispatch Specification  
Section 33 — Queue Observability

Status: Production Frozen Draft

33\. Queue Observability  
33.1 Objective

WF-001 SHALL continuously expose operational information describing the current condition and historical behavior of the scheduler queue.

Observability SHALL support monitoring, diagnostics, troubleshooting, capacity planning, and operational auditing.

Observability SHALL NOT influence scheduling decisions, execution eligibility, dispatch ordering, or transaction behavior.

33.2 Queue Metrics

WF-001 SHALL collect and persist queue metrics after every completed scheduler cycle.

The metrics SHALL be stored in the PostgreSQL table:

scheduler\_metrics

Each metrics record SHALL include at minimum:

Collection timestamp  
Scheduler cycle number  
Scheduler cycle duration  
Active queue size  
Ready execution count  
Running execution count  
Concurrent execution count  
Waiting dependency count  
Dispatch attempts  
Successful dispatches  
Failed dispatches  
Queue overflow state  
Current resource mode

The scheduler SHALL attempt to persist one metrics record for each scheduler cycle.

Failure to persist scheduler metrics SHALL NOT affect scheduler correctness. If metrics persistence is operational, failed scheduler cycles SHALL also produce a metrics record indicating cycle failure.

33.3 Scheduler Health

WF-001 SHALL continuously expose the current scheduler health.

Health SHALL include at minimum:

Current scheduler state  
PostgreSQL connectivity  
Current resource mode  
Queue size  
Active dispatch count  
Current scheduler cycle duration  
Recovery status  
Last successful scheduler cycle timestamp

Scheduler health SHALL always represent the most recent completed scheduler cycle.

33.4 Processing Error Metrics

WF-001 SHALL maintain processing error statistics.

A processing error SHALL include failures occurring during:

queue reconstruction,  
eligibility evaluation,  
queue claiming,  
dispatch initiation,  
metrics persistence,  
scheduler recovery.

Processing error metrics SHALL include:

Error timestamp  
Error category  
Execution ID (if applicable)  
Scheduler cycle number  
Error description

The scheduler SHALL also maintain:

recent\_processing\_error\_count

representing the number of processing errors occurring during the previous:

100 completed scheduler cycles

or

the previous 1 hour,

whichever interval is shorter.

33.5 Queue Performance Metrics

WF-001 SHALL expose performance information including:

Average scheduler cycle duration  
Maximum scheduler cycle duration  
Average dispatch latency  
Maximum dispatch latency  
Queue throughput  
Average queue size  
Peak queue size

Performance metrics SHALL be derived from completed scheduler cycles only.

33.6 Resource Metrics

WF-001 SHALL expose the resource information currently used by scheduling decisions.

At minimum:

CPU utilization  
Memory utilization  
Disk utilization  
Resource mode  
Timestamp of latest resource observation

Missing resource observations SHALL be explicitly reported.

33.7 Recovery Metrics

Recovery operations SHALL produce metrics including:

Recovery start timestamp  
Recovery completion timestamp  
Recovery duration  
Queue reconstruction duration  
Crash reconciliation duration  
Number of recovered executions  
Number of expired executions  
Recovery success status

33.8 Queue Event Logging

The scheduler SHOULD log significant queue events.

Events include:

Queue overflow  
Queue recovery  
Dispatch initiated  
Dispatch completed  
Dispatch failed  
Resource mode change  
Window miss  
Execution expiration  
Emergency override  
Scheduler startup  
Scheduler shutdown

Event logging SHALL be chronological.

Each event SHALL include:

Timestamp  
Event type  
Event severity  
Related execution ID (if applicable)  
Related workflow ID (if applicable)

Event logging SHALL NOT replace immutable audit records required elsewhere in this specification.

Logging and auditing SHALL remain independent mechanisms serving different operational purposes.

33.9 Observability Isolation

Observability components SHALL operate independently from scheduling logic.

Failure to collect, calculate, or persist observability data SHALL NOT:

block scheduler cycles,  
delay dispatch,  
modify execution state,  
alter execution priority,  
change queue ordering,  
prevent recovery.

Observability failures SHALL be logged separately.

33.10 Compliance

A compliant implementation SHALL:

persist scheduler metrics after every completed cycle,  
expose current scheduler health,  
maintain processing error statistics,  
expose queue performance metrics,  
expose resource metrics,  
expose recovery metrics,  
isolate observability from scheduling logic,  
ensure observability never changes scheduler behavior.

Failure to satisfy these requirements SHALL constitute non-compliance with the WF-001 Phase 3 specification.  
Phase 3 — Queue Scheduling & Dispatch Specification  
Section 34 — Phase 3 Completion Criteria

Status: Production Frozen Draft

34\. Phase 3 Completion Criteria  
34.1 Objective

Phase 3 SHALL be considered complete only when all queue scheduling, dispatch coordination, concurrency control, recovery, and observability requirements defined in this specification have been fully implemented and verified.

Partial implementation SHALL NOT satisfy Phase 3 completion.

34.2 Functional Requirements

A compliant implementation SHALL demonstrate all of the following capabilities:

Construction of the scheduler queue directly from the PostgreSQL executions table.  
Deterministic execution eligibility evaluation.  
Deterministic priority ordering.  
Resource-aware dispatch selection.  
Queue claiming using PostgreSQL row-level locking.  
Duplicate-dispatch prevention.  
Queue overflow handling.  
Starvation prevention.  
Dynamic priority aging.  
Execution window enforcement.  
Queue recovery after restart.  
Queue observability.

Every capability SHALL operate according to the corresponding specification section.

34.3 Transaction Requirements

The implementation SHALL satisfy all transaction guarantees.

Specifically:

Every execution claim SHALL execute inside one independent PostgreSQL transaction.  
Transaction isolation SHALL use READ COMMITTED.  
Execution claiming SHALL use SELECT ... FOR UPDATE SKIP LOCKED.  
Duplicate claims SHALL be impossible.  
Failed claim transactions SHALL NOT corrupt queue state.  
Queue consistency SHALL remain preserved after every committed transaction.  
34.4 State Consistency Requirements

The scheduler SHALL preserve complete execution state consistency.

The implementation SHALL guarantee:

valid state transitions only,  
terminal states are never re-entered,  
terminal executions never return to the active queue,  
concurrent execution states are counted correctly,  
queue reconstruction produces identical results from identical database contents.

State consistency SHALL remain deterministic across scheduler restarts.

34.5 Configuration Requirements

Every configurable scheduler behavior SHALL be controlled exclusively through named configuration parameters.

Configuration SHALL include at minimum:

scheduler\_cycle\_interval\_seconds  
claim\_transaction\_timeout\_seconds  
max\_ready\_wait\_seconds  
starvation\_threshold\_seconds  
low\_priority\_aging\_seconds  
normal\_priority\_aging\_seconds  
queue\_overflow\_policy  
max\_active\_queue\_size  
max\_schedule\_delay  
system\_resources\_refresh\_seconds  
resource\_entry\_threshold  
resource\_recovery\_threshold  
resource\_minimum\_dwell\_seconds  
global\_max\_concurrent\_executions  
allow\_critical\_window\_override  
default\_priority

Configuration values SHALL NOT require source code modification.  
Configuration parameters SHALL be obtained from the scheduler configuration repository.

The repository MAY be implemented as database configuration, environment variables, or another deployment-specific configuration source.

The storage mechanism is outside the scope of this specification.

34.6 Recovery Requirements

Scheduler recovery SHALL satisfy all recovery guarantees.

Recovery SHALL:

complete crash reconciliation before dispatch,  
reconstruct the queue directly from PostgreSQL,  
recalculate eligibility,  
recalculate priority,  
recalculate resource mode,  
prevent dispatch until recovery completes,  
expire excessively delayed executions,  
remain deterministic.

Repeated recovery SHALL produce identical scheduler state whenever the database contents are unchanged.

34.7 Observability Requirements

Observability SHALL satisfy all monitoring requirements.

The implementation SHALL:

persist scheduler metrics,  
expose scheduler health,  
record queue events,  
maintain processing error metrics,  
expose resource metrics,  
expose recovery metrics.

Observability SHALL NOT modify scheduler behavior.

34.8 Determinism Requirements

The scheduler SHALL be deterministic.

Given:

identical configuration,  
identical PostgreSQL contents,  
identical resource observations,  
identical scheduler time,

the scheduler SHALL produce:

identical eligibility decisions,  
identical queue ordering,  
identical execution selection,  
identical dispatch ordering,  
identical recovery behavior.

Non-deterministic scheduling behavior SHALL constitute specification non-compliance.

34.9 Compliance Requirements

An implementation SHALL be considered Phase 3 compliant only if:

every SHALL requirement in Sections 22–34 is satisfied,  
every state transition conforms to the Phase 2 state machine,  
every transaction guarantee is preserved,  
every recovery guarantee is preserved,  
every observability guarantee is preserved,  
every configuration parameter is implemented,  
no undefined scheduler behavior remains, and  
all Phase 3 verification scenarios have completed successfully.

34.10 Phase 3 Certification

Phase 3 SHALL be certified only after successful verification of:

Queue construction  
Eligibility evaluation  
Priority ordering  
Resource-aware scheduling  
Queue claiming  
Duplicate-dispatch prevention  
Queue overflow handling  
Starvation prevention  
Execution window enforcement  
Restart recovery  
Scheduler observability  
Transaction consistency  
Deterministic execution ordering

Certification SHALL require successful execution of all Phase 3 verification scenarios without specification violations.

34.11 Freeze Conditions

Phase 3 SHALL be eligible for specification freeze only when:

all specification ambiguities have been resolved,  
all configuration parameters have explicit names,  
all scheduler states are fully defined,  
all transaction semantics are explicit,  
all recovery behavior is deterministic,  
all queue behavior is fully specified,  
all audit findings have been resolved.

After freeze, modifications SHALL be permitted only through a formally approved specification revision.

s  
