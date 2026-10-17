"""Paper execution gateway. No live orders."""

from architecture.execution.gateway import PaperOrder, submit_paper

__all__ = ["PaperOrder", "submit_paper"]
