"""Fail-closed error types. Unknown/illegal operations raise; they never become ALLOW."""


class OrgError(Exception):
    """Base error for the Agent Organization control plane."""


class ValidationError(OrgError):
    """Invalid input rejected by fail-closed validation."""


class IllegalTransitionError(OrgError):
    """Task lifecycle transition that is not in the explicit legal set."""


class UnknownIdentityError(OrgError):
    """Referenced agent, task, or resource does not exist."""


class TamperDetectedError(OrgError):
    """Audit chain integrity check failed."""


class AppendOnlyViolationError(OrgError):
    """Attempt to rewrite or delete historical audit events."""
