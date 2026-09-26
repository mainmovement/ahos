# AHOS Project Bible

Project Name

Artificial Hybrid Opportunity Scoring System (AHOS)

---

## Mission

Build a production-grade event-driven intelligence platform capable of observing, reasoning, learning, and evolving while maintaining deterministic, maintainable, and scalable software architecture.

The platform is engineered following strict architectural governance and disciplined software engineering practices.

---

# Engineering Principles

The project follows:

- Clean Architecture
- Domain Driven Design (DDD)
- Event-Driven Architecture
- SOLID Principles
- Strict Scope Discipline
- Anti-Overengineering Rule
- Deterministic Design
- Test-First Validation

---

# Authoritative Specifications

Implementation is controlled exclusively by approved specifications.

Current approved specifications:

- SPS v1.1
- DMS v1.0
- RAS v1.1
- DEB v1.0
- CAS v1.0

No implementation may introduce functionality outside these specifications.

---

# Project Workflow

Every implementation follows the same lifecycle:

Architecture Specification

↓

Implementation

↓

Independent Architecture Review

↓

Corrections (if required)

↓

Approved for Merge

↓

Frozen

↓

Archived

No frozen deliverable may be modified unless a blocking architectural issue is discovered.

---

# Repository Organization

docs/

Architecture

ADR

Implementation

Reports

Archive

project/

Project management

Roadmap

Milestones

Decision log

Status

records/

Engineering history

Testing

Release records

Merge history

Change history

resources/

Diagrams

Reference material

Images

Examples

deliverables/

Versioned implementation outputs

backups/

Project backups

sessions/

Conversation history

ChatGPT

Claude

Arena

Prompts

sandbox/

Temporary work

tools/

Development utilities

---

# Coding Rules

Every code artifact shall:

be typed

be deterministic

be documented

be tested

follow approved architecture

avoid unnecessary abstractions

avoid speculative development

avoid hidden side effects

---

# Review Policy

Every implementation is reviewed independently before merge.

A deliverable becomes immutable after approval.

Approved deliverables receive the status:

FROZEN

Future work must extend the architecture without modifying frozen artifacts whenever possible.

---

# Current Project Status

Current Phase:

Core Domain Implementation

Completed Deliverables:

Repository Scaffold

DomainError

BaseEvent

Domain Events

Current Deliverable:

CognitiveCycle

Deferred:

Value Objects (until explicitly specified)

---

# Long-Term Objective

Create a maintainable, scalable, production-ready intelligence platform capable of continuous evolution while preserving architectural integrity.

---

End of Document