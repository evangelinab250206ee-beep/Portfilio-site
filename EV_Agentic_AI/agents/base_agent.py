"""Base agent helpers.

CrewAI is optional at runtime. When installed, the metadata here can be used to
wrap these deterministic tools in CrewAI tasks; when absent, the app still runs.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentProfile:
    role: str
    goal: str
    backstory: str


class BaseEVAgent:
    profile: AgentProfile

    def crew_profile(self):
        try:
            from crewai import Agent

            return Agent(role=self.profile.role, goal=self.profile.goal, backstory=self.profile.backstory, verbose=False)
        except Exception:
            return None
