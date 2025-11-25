"""
crew_config.py

Configures and creates the Crews (teams of agents and tasks).

- Explainer crew: explains why the analyst gave a rating.
- Recommender crew: issues the model's own rating.
"""

from crewai import Crew, Process

from agents import create_explainer_agent, create_recommender_agent
from tasks import create_explainer_task, create_recommender_task


def create_explainer_crew(context_str: str) -> Crew:
    """
    Create a Crew with the Explainer agent and task.
    """
    explainer_agent = create_explainer_agent()
    explainer_task = create_explainer_task(
        agent=explainer_agent,
        context_str=context_str,
    )

    crew = Crew(
        agents=[explainer_agent],
        tasks=[explainer_task],
        process=Process.sequential,
        verbose=True,
    )
    return crew


def create_recommender_crew(context_str: str) -> Crew:
    """
    Create a Crew with the Recommender agent and task.
    """
    recommender_agent = create_recommender_agent()
    recommender_task = create_recommender_task(
        agent=recommender_agent,
        context_str=context_str,
    )

    crew = Crew(
        agents=[recommender_agent],
        tasks=[recommender_task],
        process=Process.sequential,
        verbose=True,
    )
    return crew
