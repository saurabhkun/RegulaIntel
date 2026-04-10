# agents/__init__.py
"""
RegulaIntel Multi-Agent System Package

This package contains all agents for the Autonomous Compliance & Regulatory Intelligence System.
"""

# Import all agents for easy access
from .monitor import MonitorAgent
from .ingest import IngestAgent
from .diff import DiffAgent
from .impact import ImpactAgent
from .drafter import DrafterAgent
from .workflow import ComplianceWorkflow, create_workflow

# Define what gets exported with "from agents import *"
__all__ = [
    "MonitorAgent",
    "IngestAgent",
    "DiffAgent",
    "ImpactAgent",
    "DrafterAgent",
    "ComplianceWorkflow",
    "create_workflow",
]