// AHOS Arena Contract Validator
// Runtime validator with no external dependencies
// Invalid input => UNAVAILABLE, never throw to UI

import type {
  AHOSArenaContract,
  MessageHubSnapshot,
  SelfEvaluationSnapshot,
  IdeaShelfSnapshot,
  ResearchInstituteSnapshot,
  MissionMapSnapshot,
  BaseSnapshot,
  ExecutionMode,
  Source,
  GeneratedAt,
  RealTrading,
} from "./types";

// ============================================================================
// Validation Helpers
// ============================================================================

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function isNullOrString(value: unknown): value is string | null {
  return value === null || isNonEmptyString(value);
}

function isBoolean(value: unknown): value is boolean {
  return typeof value === "boolean";
}

function isNumber(value: unknown): value is number {
  return typeof value === "number" && !isNaN(value);
}

function isArray<T>(value: unknown, validator: (item: unknown) => item is T): value is T[] {
  return Array.isArray(value) && value.every(validator);
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isValidDateString(value: unknown): value is string {
  if (!isNonEmptyString(value)) return false;
  // Basic ISO 8601 check (simplified)
  const date = new Date(value);
  return !isNaN(date.getTime());
}

// ============================================================================
// Base Snapshot Validator
// ============================================================================

function validateBaseSnapshot(obj: unknown): obj is BaseSnapshot {
  if (!isObject(obj)) return false;
  
  const executionMode = obj.executionMode;
  const realTrading = obj.realTrading;
  const source = obj.source;
  const generatedAt = obj.generatedAt;
  
  if (!isNonEmptyString(executionMode)) return false;
  if (!isBoolean(realTrading)) return false;
  if (!isNonEmptyString(source)) return false;
  if (generatedAt !== null && !isValidDateString(generatedAt)) return false;
  
  return true;
}

// ============================================================================
// Message Hub Validator
// ============================================================================

function validateChannelType(value: unknown): value is import("./types").ChannelType {
  return ["Kian chat", "Telegram", "nightly report", "command router"].includes(value as string);
}

function validateStatus(value: unknown): value is import("./types").Status {
  return [
    "LIVE", "STALE", "UNKNOWN", "DEMO", "CONFLICT", "REJECTED",
    "UNAVAILABLE", "PARTIAL", "PLANNED", "MISSING", "ERROR"
  ].includes(value as string);
}

function validateBridgeState(value: unknown): value is import("./types").BridgeState {
  return ["CONNECTED", "DISCONNECTED", "UNKNOWN", "BLOCKED_OWNER"].includes(value as string);
}

function validateChannelStatus(obj: unknown): obj is import("./types").ChannelStatus {
  if (!isObject(obj)) return false;
  return (
    validateChannelType(obj.channel) &&
    validateStatus(obj.status) &&
    (obj.lastMessageTime === null || isValidDateString(obj.lastMessageTime)) &&
    (obj.queueDepth === null || isNumber(obj.queueDepth)) &&
    (obj.lastError === null || isNonEmptyString(obj.lastError))
  );
}

function validateTelegramStatus(obj: unknown): obj is import("./types").TelegramStatus {
  if (!isObject(obj)) return false;
  return (
    validateBridgeState(obj.bridgeState) &&
    isBoolean(obj.needsTokenRotation)
  );
}

function validateDeliveryState(value: unknown): value is import("./types").DeliveryState {
  return ["SENT", "NOT_SENT", "UNKNOWN"].includes(value as string);
}

function validateNightlyReportStatus(obj: unknown): obj is import("./types").NightlyReportStatus {
  if (!isObject(obj)) return false;
  return (
    (obj.lastReportTime === null || isValidDateString(obj.lastReportTime)) &&
    isNonEmptyString(obj.language) &&
    validateDeliveryState(obj.deliveryState) &&
    (obj.evidenceLink === null || isNonEmptyString(obj.evidenceLink))
  );
}

function validateHumanGateItem(obj: unknown): obj is import("./types").HumanGateItem {
  if (!isObject(obj)) return false;
  return (
    isNonEmptyString(obj.id) &&
    isNonEmptyString(obj.title) &&
    isNonEmptyString(obj.requestedByAgent) &&
    isNonEmptyString(obj.age) &&
    validateStatus(obj.state)
  );
}

function validateDirection(value: unknown): value is import("./types").Direction {
  return ["in", "out"].includes(value as string);
}

function validateMessageState(value: unknown): value is import("./types").MessageState {
  return ["DELIVERED", "FAILED", "PENDING", "UNKNOWN"].includes(value as string);
}

function validateMessageLogItem(obj: unknown): obj is import("./types").MessageLogItem {
  if (!isObject(obj)) return false;
  return (
    isValidDateString(obj.time) &&
    validateDirection(obj.direction) &&
    validateChannelType(obj.channel) &&
    isNonEmptyString(obj.summary) && obj.summary.length <= 120 &&
    validateMessageState(obj.deliveryState)
  );
}

function validateMessageHubSnapshot(obj: unknown): obj is MessageHubSnapshot {
  if (!isObject(obj)) return false;
  if (!validateBaseSnapshot(obj)) return false;
  
  const channels = obj.channels;
  const telegram = obj.telegram;
  const nightlyReport = obj.nightlyReport;
  const humanGateInbox = obj.humanGateInbox;
  const messageLog = obj.messageLog;
  
  if (!isArray(channels, validateChannelStatus)) return false;
  if (!validateTelegramStatus(telegram)) return false;
  if (!validateNightlyReportStatus(nightlyReport)) return false;
  if (!isArray(humanGateInbox, validateHumanGateItem)) return false;
  if (!isArray(messageLog, validateMessageLogItem)) return false;
  
  return true;
}

// ============================================================================
// Self Evaluation Validator
// ============================================================================

function validatePeriod(value: unknown): value is import("./types").Period {
  return ["week", "month"].includes(value as string);
}

function validateReviewState(value: unknown): value is import("./types").ReviewState {
  return ["REVIEWED", "PENDING", "UNKNOWN"].includes(value as string);
}

function validateOutcomeKnown(value: unknown): value is import("./types").OutcomeKnown {
  return ["yes", "no", "UNKNOWN"].includes(value as string);
}

function validateDecisionHighlight(obj: unknown): obj is import("./types").DecisionHighlight {
  if (!isObject(obj)) return false;
  return (
    isNonEmptyString(obj.id) &&
    isNonEmptyString(obj.market) &&
    isNonEmptyString(obj.rationaleSummary) &&
    validateOutcomeKnown(obj.outcomeKnown) &&
    validateReviewState(obj.reviewState)
  );
}

function validateScorecard(obj: unknown): obj is import("./types").Scorecard {
  if (!isObject(obj)) return false;
  return (
    validatePeriod(obj.period) &&
    (obj.decisionsReviewed === null || isNumber(obj.decisionsReviewed)) &&
    (obj.decisionsWithEvidence === null || isNumber(obj.decisionsWithEvidence)) &&
    (obj.decisionsWithUnseenCheck === null || isNumber(obj.decisionsWithUnseenCheck)) &&
    (obj.calibrationNote === null || isNonEmptyString(obj.calibrationNote)) &&
    (obj.unresolvedItems === null || isNumber(obj.unresolvedItems)) &&
    isArray(obj.highlights, validateDecisionHighlight) &&
    isArray(obj.allDecisions, validateDecisionHighlight)
  );
}

function validateSelfEvaluationSnapshot(obj: unknown): obj is SelfEvaluationSnapshot {
  if (!isObject(obj)) return false;
  if (!validateBaseSnapshot(obj)) return false;
  
  const scorecards = obj.scorecards;
  if (!isArray(scorecards, validateScorecard)) return false;
  
  return true;
}

// ============================================================================
// Idea Shelf Validator
// ============================================================================

function validateIdeaStatus(value: unknown): value is import("./types").IdeaStatus {
  return ["PROPOSED", "ACCEPTED", "REJECTED"].includes(value as string);
}

function validateIdeaOrigin(value: unknown): value is import("./types").IdeaOrigin {
  return ["agent", "university", "owner"].includes(value as string);
}

function validateUnseenTestResult(value: unknown): value is import("./types").UnseenTestResult {
  return ["PASS", "FAIL", "NOT_RUN"].includes(value as string);
}

function validateIdea(obj: unknown): obj is import("./types").Idea {
  if (!isObject(obj)) return false;
  return (
    isNonEmptyString(obj.id) &&
    isNonEmptyString(obj.title) &&
    validateIdeaOrigin(obj.origin) &&
    validateIdeaStatus(obj.status) &&
    (obj.reason === null || isNonEmptyString(obj.reason)) &&
    (obj.hardwareRequirement === null || (
      isObject(obj.hardwareRequirement) && 
      isNonEmptyString(obj.hardwareRequirement.minRAM)
    )) &&
    isArray(obj.flags, isNonEmptyString) &&
    (obj.unseenTest === null || (
      isObject(obj.unseenTest) &&
      (obj.unseenTest.datasetId === null || isNonEmptyString(obj.unseenTest.datasetId)) &&
      (obj.unseenTest.outOfSamplePeriod === null || isNonEmptyString(obj.unseenTest.outOfSamplePeriod)) &&
      (obj.unseenTest.sampleSize === null || isNumber(obj.unseenTest.sampleSize)) &&
      validateUnseenTestResult(obj.unseenTest.result)
    ))
  );
}

function validateIdeaShelfSnapshot(obj: unknown): obj is IdeaShelfSnapshot {
  if (!isObject(obj)) return false;
  if (!validateBaseSnapshot(obj)) return false;
  
  const ideas = obj.ideas;
  if (!isArray(ideas, validateIdea)) return false;
  
  return true;
}

// ============================================================================
// Research Institute Validator
// ============================================================================

function validateHypothesisStatus(value: unknown): value is import("./types").HypothesisStatus {
  return ["UNTESTED", "TESTED_UNSEEN", "REJECTED", "INCONCLUSIVE"].includes(value as string);
}

function validateHypothesisSource(value: unknown): value is import("./types").HypothesisSource {
  return ["university", "paper", "agent"].includes(value as string);
}

function validateHypothesis(obj: unknown): obj is import("./types").Hypothesis {
  if (!isObject(obj)) return false;
  return (
    isNonEmptyString(obj.id) &&
    isNonEmptyString(obj.statement) &&
    validateHypothesisSource(obj.source) &&
    isNonEmptyString(obj.market) &&
    validateHypothesisStatus(obj.status) &&
    (obj.inSampleResult === null || (
      isObject(obj.inSampleResult) && 
      isNonEmptyString(obj.inSampleResult.note)
    )) &&
    (obj.unseenTest === null || (
      isObject(obj.unseenTest) &&
      (obj.unseenTest.datasetId === null || isNonEmptyString(obj.unseenTest.datasetId)) &&
      (obj.unseenTest.period === null || isNonEmptyString(obj.unseenTest.period)) &&
      (obj.unseenTest.sampleSize === null || isNumber(obj.unseenTest.sampleSize)) &&
      (obj.unseenTest.costModelPresent === null || isBoolean(obj.unseenTest.costModelPresent)) &&
      validateUnseenTestResult(obj.unseenTest.result)
    ))
  );
}

function validateResearchInstituteSnapshot(obj: unknown): obj is ResearchInstituteSnapshot {
  if (!isObject(obj)) return false;
  if (!validateBaseSnapshot(obj)) return false;
  
  const hypotheses = obj.hypotheses;
  if (!isArray(hypotheses, validateHypothesis)) return false;
  
  if (obj.weeklyExam !== null) {
    const exam = obj.weeklyExam;
    if (!isObject(exam)) return false;
    if ((exam.lastExamTime !== null && !isValidDateString(exam.lastExamTime)) ||
        (exam.itemsExamined !== null && !isNumber(exam.itemsExamined)) ||
        (exam.itemsPassedUnseen !== null && !isNumber(exam.itemsPassedUnseen))) {
      return false;
    }
  }
  
  return true;
}

// ============================================================================
// Mission Map Validator
// ============================================================================

function validateMissionGroup(value: unknown): value is import("./types").MissionGroup {
  return ["M", "M-D", "M-PORT"].includes(value as string);
}

function validateMissionState(value: unknown): value is import("./types").MissionState {
  return ["DONE", "PARTIAL", "NOT_STARTED"].includes(value as string);
}

function validateMission(obj: unknown): obj is import("./types").Mission {
  if (!isObject(obj)) return false;
  return (
    isNonEmptyString(obj.id) &&
    isNonEmptyString(obj.title) &&
    validateMissionGroup(obj.group) &&
    validateMissionState(obj.state) &&
    isBoolean(obj.blockedOwner) &&
    (obj.evidence === null || isNonEmptyString(obj.evidence)) &&
    (obj.lastUpdate === null || isValidDateString(obj.lastUpdate)) &&
    (obj.caveat === null || isNonEmptyString(obj.caveat))
  );
}

function validateMissionMapSnapshot(obj: unknown): obj is MissionMapSnapshot {
  if (!isObject(obj)) return false;
  if (!validateBaseSnapshot(obj)) return false;
  
  const missions = obj.missions;
  if (!isArray(missions, validateMission)) return false;
  
  if (obj.summary !== null) {
    const summary = obj.summary;
    if (!isObject(summary)) return false;
    if ((summary.doneCount !== null && !isNumber(summary.doneCount)) ||
        (summary.partialCount !== null && !isNumber(summary.partialCount)) ||
        (summary.notStartedCount !== null && !isNumber(summary.notStartedCount))) {
      return false;
    }
  }
  
  if (!isArray(obj.highlightedMissions, validateMission)) return false;
  
  return true;
}

// ============================================================================
// Main Contract Validator
// ============================================================================

/**
 * Validates the entire AHOS Arena contract
 * Returns true if valid, false if invalid (which means UNAVAILABLE in UI)
 * NEVER throws - always returns false for invalid input
 */
export function validateContract(obj: unknown): obj is AHOSArenaContract {
  try {
    if (!isObject(obj)) return false;
    
    // Validate top-level fields
    const executionMode = obj.executionMode;
    const realTrading = obj.realTrading;
    const source = obj.source;
    const generatedAt = obj.generatedAt;
    
    if (!isNonEmptyString(executionMode)) return false;
    if (!isBoolean(realTrading)) return false;
    if (!isNonEmptyString(source)) return false;
    if (generatedAt !== null && !isValidDateString(generatedAt)) return false;
    
    // Validate each snapshot
    if (!validateMessageHubSnapshot(obj.messageHub)) return false;
    if (!validateSelfEvaluationSnapshot(obj.selfEvaluation)) return false;
    if (!validateIdeaShelfSnapshot(obj.ideaShelf)) return false;
    if (!validateResearchInstituteSnapshot(obj.researchInstitute)) return false;
    if (!validateMissionMapSnapshot(obj.missionMap)) return false;
    
    return true;
  } catch {
    // Any error during validation means invalid
    return false;
  }
}

/**
 * Validates a single snapshot by type
 * Used by adapters to validate their specific section
 */
export function validateSnapshot<T>(
  obj: unknown,
  validator: (obj: unknown) => obj is T
): obj is T {
  try {
    return validator(obj);
  } catch {
    return false;
  }
}

/**
 * Checks if a value is a valid snapshot (any type)
 * Returns the snapshot if valid, null otherwise
 */
export function getValidSnapshot<T>(
  obj: unknown,
  validator: (obj: unknown) => obj is T
): T | null {
  return validateSnapshot(obj, validator) ? obj : null;
}

// ============================================================================
// Helper to check if data is DEMO
// ============================================================================

export function isDemoData(snapshot: { demo?: boolean }): boolean {
  return snapshot.demo === true;
}

// ============================================================================
// Helper to get component state from snapshot
// ============================================================================

export function getComponentState(snapshot: (BaseSnapshot & { demo?: boolean }) | null): import("./types").ComponentState {
  if (snapshot === null) return "UNAVAILABLE";
  // Audit fix: a DEMO snapshot must never be reported LIVE (original returned LIVE for any PAPER_ONLY row with a timestamp).
  if (snapshot.demo === true) return "SIMULATED";
  if (snapshot.executionMode === "PAPER_ONLY" && !snapshot.realTrading) {
    if (snapshot.generatedAt === null) return "UNKNOWN";
    return "LIVE";
  }
  return "UNAVAILABLE";
}
