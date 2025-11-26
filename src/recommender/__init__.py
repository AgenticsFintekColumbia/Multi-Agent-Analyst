"""
Recommender team: Multi-agent system to generate model recommendations.
"""

from .agents import (
    fundamental_agent,
    technical_agent,
    news_agent,
    recommender_manager,
)

from .tasks import (
    fundamental_task,
    technical_task,
    news_task,
    create_recommender_manager_task,
)

from .orchestrator import run_multi_analyst_recommendation

__all__ = [
    'fundamental_agent',
    'technical_agent',
    'news_agent',
    'recommender_manager',
    'fundamental_task',
    'technical_task',
    'news_task',
    'create_recommender_manager_task',
    'run_multi_analyst_recommendation',
]
