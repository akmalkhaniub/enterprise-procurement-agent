from langchain_core.messages import AIMessage, HumanMessage
from agents import parse_supervisor_route, extract_text


def test_parse_supervisor_route_exact_match():
    msgs = [HumanMessage(content="What is our spend on AWS?")]
    assert parse_supervisor_route("DataAnalyst", msgs) == "DataAnalyst"
    assert parse_supervisor_route("  'Researcher' ", msgs) == "Researcher"
    assert parse_supervisor_route("OpsEngineer.", msgs) == "OpsEngineer"
    assert parse_supervisor_route("FINISH", msgs) == "FINISH"


def test_parse_supervisor_route_multi_mention_takes_final_target():
    msgs = [
        HumanMessage(content="Check spend and then check SLA"),
        AIMessage(content="Total spend is $45,000", name="DataAnalyst"),
    ]
    # Previously, 'if "DataAnalyst" in next_step' would erroneously route back to DataAnalyst
    raw = "DataAnalyst has already answered; now route to Researcher"
    assert parse_supervisor_route(raw, msgs) == "Researcher"


def test_parse_supervisor_route_stagnation_guard():
    msgs = [
        HumanMessage(content="Check spend"),
        AIMessage(content="Total spend is $45,000", name="DataAnalyst"),
    ]
    # Repeating the exact same subagent that just responded halts the loop
    assert parse_supervisor_route("DataAnalyst", msgs) == "FINISH"


def test_extract_text_handles_structured_content_blocks():
    blocks = [{"type": "text", "text": "Hello"}, {"type": "text", "text": "World"}]
    assert extract_text(blocks) == "Hello World"
