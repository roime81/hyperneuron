os_import = "os"
import os
from langchain_core.messages import SystemMessage, HumanMessage
from backend.config import get_llm
from backend.state import HyperneuronState, ResearchPlan, SpecialistReport
from backend.tools import web_search

def orchestrator_plan_node(state: HyperneuronState) -> dict:
    llm = get_llm("ORCHESTRATOR_MODEL", "deepseek-v4.1-flash", temperature=0.1)
    structured_llm = llm.with_structured_output(ResearchPlan)
    system = SystemMessage(content="You are the Chief Orchestrator of Hyperneuron AI Deep Lab. Quantify the research request into three parallel briefs.")
    plan: ResearchPlan = structured_llm.invoke([system, HumanMessage(content=state["user_prompt"])])
    return {"plan": plan.model_dump(), "iteration": state.get("iteration", 0) + 1}

def deep_thinking_node(state: HyperneuronState) -> dict:
    model_id = os.getenv("THINKING_MODEL", "gemma4:31b")
    llm = get_llm("THINKING_MODEL", "gemma4:31b", temperature=0.3)
    structured_llm = llm.with_structured_output(SpecialistReport)
    plan = state["plan"]
    prompt = f"User Request: {state['user_prompt']}\nDomain: {plan['domain']}\nBrief: {plan['thinking_brief']}\nPerform deep first-principles reasoning and identify risks."
    report: SpecialistReport = structured_llm.invoke([SystemMessage(content="You are Deep Thinking Researcher."), HumanMessage(content=prompt)])
    report.agent_name = "Deep Thinking Researcher"
    report.model_used = model_id
    return {"specialist_reports": [report.model_dump()]}

def deep_citation_node(state: HyperneuronState) -> dict:
    model_id = os.getenv("CITATION_MODEL", "llama4:scout")
    llm = get_llm("CITATION_MODEL", "llama4:scout", temperature=0.1)
    structured_llm = llm.with_structured_output(SpecialistReport)
    plan = state["plan"]
    raw_sources = web_search(plan["citation_queries"])
    prompt = f"User Request: {state['user_prompt']}\nSources:\n{raw_sources}\nExtract verifiable facts and exact URLs."
    report: SpecialistReport = structured_llm.invoke([SystemMessage(content="You are Deep Citation Researcher."), HumanMessage(content=prompt)])
    report.agent_name = "Deep Citation Researcher"
    report.model_used = model_id
    return {"specialist_reports": [report.model_dump()]}

def quantified_researcher_node(state: HyperneuronState) -> dict:
    model_id = os.getenv("QUANT_MODEL", "qwen3.6:27b")
    llm = get_llm("QUANT_MODEL", "qwen3.6:27b", temperature=0.1)
    structured_llm = llm.with_structured_output(SpecialistReport)
    plan = state["plan"]
    quant_sources = web_search([f"{state['user_prompt']} statistics metrics"])
    prompt = f"User Request: {state['user_prompt']}\nBrief: {plan['quant_brief']}\nData:\n{quant_sources}\nProvide concrete numbers and tables."
    report: SpecialistReport = structured_llm.invoke([SystemMessage(content="You are Qualified Quantified Researcher."), HumanMessage(content=prompt)])
    report.agent_name = "Qualified Quantified Researcher"
    report.model_used = model_id
    return {"specialist_reports": [report.model_dump()]}

def orchestrator_synthesize_node(state: HyperneuronState) -> dict:
    llm = get_llm("ORCHESTRATOR_MODEL", "deepseek-v4.1-flash", temperature=0.2)
    plan = state["plan"]
    if plan.get("needs_clarification"):
        return {"final_report": f"**Clarification Needed:** {plan.get('clarification_question')}"}
    reports_text = "\n\n".join(
        f"### {r['agent_name']} (Model: {r['model_used']})\nSummary: {r['summary']}\nKey Findings:\n- " + "\n- ".join(r["key_findings"])
        for r in state["specialist_reports"]
    )
    prompt = f"User Prompt: {state['user_prompt']}\nReports:\n{reports_text}\nSynthesize an executive Markdown report."
    response = llm.invoke([SystemMessage(content="Synthesize reports."), HumanMessage(content=prompt)])
    return {"final_report": response.content}
