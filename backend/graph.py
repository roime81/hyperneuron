from langgraph.graph import StateGraph, START, END
from backend.state import HyperneuronState
from backend.agents import (
    orchestrator_plan_node, deep_thinking_node, deep_citation_node,
    quantified_researcher_node, orchestrator_synthesize_node,
)


def route_after_planning(state: HyperneuronState):
    if state["plan"].get("needs_clarification"):
        return "orchestrator_synthesize"
    return ["deep_thinking", "deep_citation", "quantified_researcher"]


def build_hyperneuron_graph():
    workflow = StateGraph(HyperneuronState)
    workflow.add_node("orchestrator_plan", orchestrator_plan_node)
    workflow.add_node("deep_thinking", deep_thinking_node)
    workflow.add_node("deep_citation", deep_citation_node)
    workflow.add_node("quantified_researcher", quantified_researcher_node)
    workflow.add_node("orchestrator_synthesize", orchestrator_synthesize_node)
    workflow.add_edge(START, "orchestrator_plan")
    workflow.add_conditional_edges(
        "orchestrator_plan",
        route_after_planning,
        ["deep_thinking", "deep_citation", "quantified_researcher", "orchestrator_synthesize"],
    )
    # Fan-in barrier: synthesis starts only after all specialist workers finish.
    workflow.add_edge(["deep_thinking", "deep_citation", "quantified_researcher"], "orchestrator_synthesize")
    workflow.add_edge("orchestrator_synthesize", END)
    return workflow.compile()
