"""
crew_config.py

Configures and creates the Crew (team of agents working together).

What's a Crew?
A Crew is a team of agents working on tasks. For now, we have just one agent
(the Explainer), but later we might add more (like a Recommender agent).
"""

from crewai import Crew, Process
from agents import create_explainer_agent
from tasks import create_explainer_task


def create_explainer_crew(context_str: str):
    """
    Create a Crew with the Explainer agent and task.
    
    Args:
        context_str: The formatted context with IBES, FUND, NEWS data
        
    Returns:
        Crew: A configured crew ready to run
    """
    
    # Step 1: Create the agent
    explainer_agent = create_explainer_agent()
    
    # Step 2: Create the task for this agent
    explainer_task = create_explainer_task(
        agent=explainer_agent,
        context_str=context_str
    )
    
    # Step 3: Assemble into a Crew
    crew = Crew(
        agents=[explainer_agent],
        tasks=[explainer_task],
        process=Process.sequential,  # Tasks run one after another
        verbose=True,  # Show detailed progress
    )
    
    return crew