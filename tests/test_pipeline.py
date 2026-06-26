"""Tests for the agent pipeline — individual agents, full flow, and PipelineQueue."""

import json
import sys
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from backend.core.gemini_queue import GeminiRequestQueue
from backend.core.pipeline_queue import PipelineQueue
from backend.agents.gemini_agent import GeminiAgent
from backend.agents.interaction_agent import InteractionAgent
from backend.agents.request_handler_agent import RequestHandlerAgent
from backend.agents.validation_agent import ValidationAgent


# ---------------------------------------------------------------------------
#  Mock helpers
# ---------------------------------------------------------------------------

def _make_gemini_response(text: str):
    """Build a MagicMock that mimics a genai response with the given text."""
    resp = MagicMock()
    candidate = MagicMock()
    part = MagicMock()
    part.text = text
    candidate.content.parts = [part]
    resp.candidates = [candidate]
    return resp


class MockMCPClient:
    """Synchronous mock MCP client returning canned responses."""

    def __init__(self):
        self.call_log: list[tuple[str, dict | None]] = []
        self._responses = {
            "kapruka_search_products": json.dumps({
                "products": [
                    {"id": "123", "name": "Chocolate Birthday Cake", "price": 3500, "currency": "LKR", "in_stock": True},
                    {"id": "456", "name": "Vanilla Birthday Cake", "price": 4200, "currency": "LKR", "in_stock": True},
                ],
                "total": 2, "page": 1,
            }),
            "kapruka_get_product": json.dumps({
                "id": "123", "name": "Chocolate Birthday Cake", "price": 3500,
                "currency": "LKR", "in_stock": True,
            }),
            "kapruka_list_categories": json.dumps({"categories": [{"name": "Cakes & Flowers"}]}),
            "kapruka_check_delivery": json.dumps({
                "available": True, "city": "Colombo", "delivery_charge_lkr": 350,
            }),
            "kapruka_create_order": json.dumps({"order_id": "ORD-12345", "status": "pending_payment"}),
            "kapruka_track_order": json.dumps({"order_number": "ORD-12345", "status": "in_transit"}),
            "kapruka_list_delivery_cities": json.dumps({"cities": [{"name": "Colombo"}]}),
        }

    def call_tool(self, name: str, arguments: dict | None = None) -> str:
        self.call_log.append((name, arguments))
        return self._responses.get(name, json.dumps({"error": "Unknown tool"}))


@pytest.fixture
def mock_gemini():
    """Fixture that patches genai.Client in all three agent modules.

    Yields a callable ``set_response(text)`` that controls what the next
    Gemini call returns.
    """
    patchers = [
        patch("backend.agents.interaction_agent.genai.Client"),
        patch("backend.agents.request_handler_agent.genai.Client"),
        patch("backend.agents.validation_agent.genai.Client"),
    ]
    for p in patchers:
        p.start()

    _response_container = [""]

    def _make_mock_client(*args, **kwargs):
        client = MagicMock()
        client.models.generate_content.side_effect = lambda *a, **kw: _make_gemini_response(
            _response_container[0]
        )
        return client

    for mod_name in ("interaction_agent", "request_handler_agent", "validation_agent"):
        patcher = patch(
            f"backend.agents.{mod_name}.genai.Client",
            side_effect=_make_mock_client,
        )
        patcher.start()
        patchers.append(patcher)

    def set_response(text: str):
        _response_container[0] = text

    yield set_response

    for p in patchers:
        p.stop()


@pytest.fixture
def queue():
    return GeminiRequestQueue(max_concurrency=1, min_delay_ms=0)


@pytest.fixture
def interaction(queue):
    return InteractionAgent(queue)


@pytest.fixture
def request_handler(queue):
    return RequestHandlerAgent(queue)


@pytest.fixture
def validation(queue):
    return ValidationAgent(queue)


@pytest.fixture
def agent(queue):
    return GeminiAgent(queue)


# ---------------------------------------------------------------------------
#  InteractionAgent tests
# ---------------------------------------------------------------------------

class TestInteractionAgent:
    def test_chat_returns_text(self, interaction, mock_gemini):
        mock_gemini("Hello! How can I help you?")
        result = interaction.chat("hi", [])
        assert result == "Hello! How can I help you?"

    def test_chat_with_history(self, interaction, mock_gemini):
        mock_gemini("I see you asked about cakes before. What else?")
        history = [{"role": "user", "content": "I want a cake"}, {"role": "assistant", "content": "Sure!"}]
        result = interaction.chat("tell me more", history)
        assert "cakes" in result

    def test_chat_empty_response(self, interaction, mock_gemini):
        mock_gemini("")
        result = interaction.chat("hi", [])
        assert result == ""

    def test_present_results(self, interaction, mock_gemini):
        mock_gemini("Here are the results...")
        result = interaction.present_results('{"data": "ok"}', [])
        assert "results" in result

    def test_explain_limitations(self, interaction, mock_gemini):
        mock_gemini("Sorry, I couldn't find that.")
        result = interaction.explain_limitations("No stock available", [])
        assert len(result) > 0


# ---------------------------------------------------------------------------
#  RequestHandlerAgent tests
# ---------------------------------------------------------------------------

class TestRequestHandlerAgent:
    def test_returns_tool_call(self, request_handler, mock_gemini):
        mock_gemini('```json\n{"tool": "kapruka_search_products", "arguments": {"q": "cake"}}\n```')
        result = request_handler.build_request("search for cake")
        assert result is not None
        assert result["tool"] == "kapruka_search_products"
        assert result["arguments"]["q"] == "cake"

    def test_returns_none_on_bad_json(self, request_handler, mock_gemini):
        mock_gemini("I don't understand what tool to use")
        result = request_handler.build_request("do something")
        assert result is None

    def test_returns_none_on_empty(self, request_handler, mock_gemini):
        mock_gemini("")
        result = request_handler.build_request("test")
        assert result is None

    def test_handles_json_without_code_block(self, request_handler, mock_gemini):
        mock_gemini('{"tool": "kapruka_search_products", "arguments": {}}')
        result = request_handler.build_request("search")
        assert result is not None
        assert result["tool"] == "kapruka_search_products"


# ---------------------------------------------------------------------------
#  ValidationAgent tests
# ---------------------------------------------------------------------------

class TestValidationAgent:
    def test_validation_satisfied(self, validation, mock_gemini):
        mock_gemini('```json\n{"satisfied": true, "feedback": "All good"}\n```')
        verdict = validation.validate("find cake", {"tool": "search"}, '{"products": []}')
        assert verdict["satisfied"] is True

    def test_validation_not_satisfied(self, validation, mock_gemini):
        mock_gemini('```json\n{"satisfied": false, "feedback": "No results", "refined_request": {"q": "chocolate"}}\n```')
        verdict = validation.validate("find cake", {"tool": "search"}, '{"products": []}')
        assert verdict["satisfied"] is False
        assert verdict["refined_request"] == {"q": "chocolate"}

    def test_validation_no_refined_request(self, validation, mock_gemini):
        mock_gemini('```json\n{"satisfied": false, "feedback": "No results", "refined_request": null}\n```')
        verdict = validation.validate("find cake", {"tool": "search"}, '{"products": []}')
        assert verdict["satisfied"] is False
        assert verdict.get("refined_request") is None

    def test_validation_bad_json_fallback(self, validation, mock_gemini):
        mock_gemini("I can't validate this properly")
        verdict = validation.validate("find cake", {"tool": "search"}, '{"products": []}')
        assert verdict["satisfied"] is False
        assert len(verdict["feedback"]) > 0

    def test_validation_empty_response(self, validation, mock_gemini):
        mock_gemini("")
        verdict = validation.validate("find cake", {"tool": "search"}, '{"products": []}')
        assert verdict["satisfied"] is False


# ---------------------------------------------------------------------------
#  GeminiAgent (orchestrator) tests  —  full pipeline
# ---------------------------------------------------------------------------

class TestGeminiAgentPipeline:
    """Tests the full orchestration flow through all sub-agents and MCP."""

    def test_no_requirements_returns_raw_chat(self, agent, mock_gemini):
        """When InteractionAgent returns plain text (no JSON), return it directly."""
        mock_gemini("Hello! How can I help you today?")
        mcp = MockMCPClient()
        result = agent.process_message("hi", [], mcp)
        assert result == "Hello! How can I help you today?"
        assert len(mcp.call_log) == 0

    def test_full_successful_pipeline(self, agent, mock_gemini):
        """Happy path: chat → request → MCP → validate → present results."""
        responses = iter([
            # 1. InteractionAgent.chat()
            'I can help with that.\n```json\n{"intent": "search", "requirements": {"q": "cake"}}\n```',
            # 2. RequestHandlerAgent.build_request()
            '```json\n{"tool": "kapruka_search_products", "arguments": {"q": "cake"}}\n```',
            # 3. ValidationAgent.validate()
            '```json\n{"satisfied": true, "feedback": "Results match the request"}\n```',
            # 4. InteractionAgent.present_results()
            "I found some great cakes for you!",
        ])

        def next_response(*args, **kwargs):
            text = next(responses)
            return _make_gemini_response(text)

        with patch("backend.agents.interaction_agent.genai.Client") as ci, \
             patch("backend.agents.request_handler_agent.genai.Client") as cr, \
             patch("backend.agents.validation_agent.genai.Client") as cv:

            def mkclient(resp_gen):
                def _create(*a, **kw):
                    c = MagicMock()
                    c.models.generate_content = resp_gen
                    return c
                return _create

            ci.side_effect = mkclient(lambda *a, **kw: next_response())
            cr.side_effect = mkclient(lambda *a, **kw: next_response())
            cv.side_effect = mkclient(lambda *a, **kw: next_response())

            mcp = MockMCPClient()
            statuses = []
            outputs = []

            def send_status(s, d=""):
                statuses.append((s, d))

            def send_agent_output(label, content, status="info"):
                outputs.append((label, status))

            result = agent.process_message(
                "find me a cake", [], mcp,
                send_status=send_status,
                send_agent_output=send_agent_output,
            )

        assert "cake" in result or "great" in result
        assert len(mcp.call_log) == 1
        assert mcp.call_log[0][0] == "kapruka_search_products"

        assert len(statuses) > 0
        assert len(outputs) >= 3
        labels = [o[0] for o in outputs]
        assert "Conversation Analysis" in labels
        assert "Request Builder" in labels
        assert "Validation" in labels
        assert "Final Response" in labels

    def test_validation_retry_then_success(self, agent, mock_gemini):
        """Validation fails on first attempt, retries with refined request, succeeds."""
        responses = iter([
            # 1. chat
            '```json\n{"intent": "search", "requirements": {"q": "cake"}}\n```',
            # 2. build_request (attempt 1)
            '```json\n{"tool": "kapruka_search_products", "arguments": {"q": "cake"}}\n```',
            # 3. validate (attempt 1 — fails, gives refined)
            '```json\n{"satisfied": false, "feedback": "Try chocolate", "refined_request": {"q": "chocolate cake"}}\n```',
            # 4. build_request (attempt 2)
            '```json\n{"tool": "kapruka_search_products", "arguments": {"q": "chocolate cake"}}\n```',
            # 5. validate (attempt 2 — passes)
            '```json\n{"satisfied": true, "feedback": "Found chocolate cakes"}\n```',
            # 6. present_results
            "Here are the chocolate cakes!",
        ])

        def next_response(*a, **kw):
            return _make_gemini_response(next(responses))

        with patch("backend.agents.interaction_agent.genai.Client") as ci, \
             patch("backend.agents.request_handler_agent.genai.Client") as cr, \
             patch("backend.agents.validation_agent.genai.Client") as cv:

            ci.side_effect = lambda *a, **kw: MagicMock(
                models=MagicMock(generate_content=next_response)
            )
            cr.side_effect = lambda *a, **kw: MagicMock(
                models=MagicMock(generate_content=next_response)
            )
            cv.side_effect = lambda *a, **kw: MagicMock(
                models=MagicMock(generate_content=next_response)
            )

            mcp = MockMCPClient()
            result = agent.process_message("find cake", [], mcp)

        assert "chocolate" in result.lower()
        assert len(mcp.call_log) == 2
        assert mcp.call_log[0][1] == {"q": "cake"}
        assert mcp.call_log[1][1] == {"q": "chocolate cake"}

    def test_all_retries_exhausted(self, agent, mock_gemini):
        """Validation keeps failing, no refined request → explain_limitations."""
        responses = iter([
            # 1. chat
            '```json\n{"requirements": {"q": "cake"}}\n```',
            # 2. build_request (attempt 1)
            '```json\n{"tool": "kapruka_search_products", "arguments": {"q": "cake"}}\n```',
            # 3. validate (attempt 1 — fails, no refined)
            '```json\n{"satisfied": false, "feedback": "Nope", "refined_request": null}\n```',
            # 4. explain_limitations → chat (internal call)
            "Sorry, I couldn't find what you're looking for.",
        ])

        with patch("backend.agents.interaction_agent.genai.Client") as ci, \
             patch("backend.agents.request_handler_agent.genai.Client") as cr, \
             patch("backend.agents.validation_agent.genai.Client") as cv:

            def mk_static(text):
                return lambda *a, **kw: _make_gemini_response(text)

            ci.side_effect = lambda *a, **kw: MagicMock(
                models=MagicMock(generate_content=mk_static(next(responses)))
            )
            cr.side_effect = lambda *a, **kw: MagicMock(
                models=MagicMock(generate_content=mk_static(next(responses)))
            )
            cv.side_effect = lambda *a, **kw: MagicMock(
                models=MagicMock(generate_content=mk_static(next(responses)))
            )

            mcp = MockMCPClient()
            result = agent.process_message("find cake", [], mcp)

        assert len(result) > 0
        assert len(mcp.call_log) == 1

    def test_build_request_returns_none(self, agent, mock_gemini):
        """When build_request returns None, pipeline explains limitations."""
        responses = iter([
            '```json\n{"requirements": {"q": "cake"}}\n```',
            "I don't know what tool to use",
            "Sorry, I couldn't process your request.",
        ])

        with patch("backend.agents.interaction_agent.genai.Client") as ci, \
             patch("backend.agents.request_handler_agent.genai.Client") as cr:

            ci.side_effect = lambda *a, **kw: MagicMock(
                models=MagicMock(generate_content=lambda *a, **kw: _make_gemini_response(next(responses)))
            )
            cr.side_effect = lambda *a, **kw: MagicMock(
                models=MagicMock(generate_content=lambda *a, **kw: _make_gemini_response(next(responses)))
            )

            mcp = MockMCPClient()
            result = agent.process_message("find cake", [], mcp)

        assert len(result) > 0
        assert len(mcp.call_log) == 0

    def test_pipeline_with_mcp_error(self, agent, mock_gemini):
        """MCP returns an error response (unknown tool) — validation handles it."""
        responses = iter([
            '```json\n{"requirements": {"q": "cake"}}\n```',
            '```json\n{"tool": "kapruka_bad_tool", "arguments": {}}\n```',
            '```json\n{"satisfied": false, "feedback": "Tool failed", "refined_request": null}\n```',
            "The tool returned an error. Please try a different approach.",
        ])

        with patch("backend.agents.interaction_agent.genai.Client") as ci, \
             patch("backend.agents.request_handler_agent.genai.Client") as cr, \
             patch("backend.agents.validation_agent.genai.Client") as cv:

            ci.side_effect = lambda *a, **kw: MagicMock(
                models=MagicMock(generate_content=lambda *a, **kw: _make_gemini_response(next(responses)))
            )
            cr.side_effect = lambda *a, **kw: MagicMock(
                models=MagicMock(generate_content=lambda *a, **kw: _make_gemini_response(next(responses)))
            )
            cv.side_effect = lambda *a, **kw: MagicMock(
                models=MagicMock(generate_content=lambda *a, **kw: _make_gemini_response(next(responses)))
            )

            mcp = MockMCPClient()
            result = agent.process_message("do something", [], mcp)

        assert len(result) > 0
        assert mcp.call_log[0][0] == "kapruka_bad_tool"

    def test_agent_output_callbacks(self, agent, mock_gemini):
        """send_agent_output is called with correct labels throughout pipeline."""
        responses = iter([
            '```json\n{"requirements": {"q": "cake"}}\n```',
            '```json\n{"tool": "kapruka_search_products", "arguments": {"q": "cake"}}\n```',
            '```json\n{"satisfied": false, "feedback": "No", "refined_request": null}\n```',
            "I'm unable to find what you're looking for.",
        ])

        with patch("backend.agents.interaction_agent.genai.Client") as ci, \
             patch("backend.agents.request_handler_agent.genai.Client") as cr, \
             patch("backend.agents.validation_agent.genai.Client") as cv:

            ci.side_effect = lambda *a, **kw: MagicMock(
                models=MagicMock(generate_content=lambda *a, **kw: _make_gemini_response(next(responses)))
            )
            cr.side_effect = lambda *a, **kw: MagicMock(
                models=MagicMock(generate_content=lambda *a, **kw: _make_gemini_response(next(responses)))
            )
            cv.side_effect = lambda *a, **kw: MagicMock(
                models=MagicMock(generate_content=lambda *a, **kw: _make_gemini_response(next(responses)))
            )

            outputs = []

            def capture(label, content, status="info"):
                outputs.append((label, status))

            mcp = MockMCPClient()
            agent.process_message("test", [], mcp, send_agent_output=capture)

        labels = [o[0] for o in outputs]
        assert "Conversation Analysis" in labels
        assert "Request Builder" in labels
        assert "Validation" in labels
        assert any("Unable to Fulfill" in l for l in labels)


# ---------------------------------------------------------------------------
#  PipelineQueue tests
# ---------------------------------------------------------------------------

class TestPipelineQueue:
    def test_passes_through_to_agent(self):
        """process_message delegates to the wrapped agent."""
        agent = MagicMock()
        agent.process_message.return_value = "hello"

        pq = PipelineQueue(agent, max_concurrency=1, pipeline_interval_ms=0)
        result = pq.process_message("hi", [], None)

        agent.process_message.assert_called_once()
        assert result == "hello"

    def test_semaphore_prevents_concurrent_calls(self):
        """Only max_concurrency pipelines run simultaneously."""
        inside = threading.Event()
        can_exit = threading.Event()
        results = []
        errors = []

        class BlockingAgent:
            def process_message(self, *args, **kwargs):
                inside.set()
                can_exit.wait(timeout=5)
                return "done"

        pq = PipelineQueue(BlockingAgent(), max_concurrency=1, pipeline_interval_ms=0)

        def run():
            try:
                r = pq.process_message("x", [], None)
                results.append(r)
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=run)
        t2 = threading.Thread(target=run)
        t2.daemon = True

        t1.start()
        assert inside.wait(timeout=2), "First call should enter pipeline"
        time.sleep(0.3)

        t2.start()
        time.sleep(0.3)

        assert len(results) == 0, "Second call should be blocked by semaphore"

        can_exit.set()
        t1.join(timeout=5)
        t2.join(timeout=5)

        assert len(results) == 2
        assert all(r == "done" for r in results)

    def test_min_interval_enforced(self):
        """PipelineQueue sleeps if last pipeline finished too recently."""
        agent = MagicMock()
        agent.process_message.return_value = "ok"

        pq = PipelineQueue(agent, max_concurrency=1, pipeline_interval_ms=200)
        pq.process_message("a", [], None)
        t0 = time.monotonic()
        pq.process_message("b", [], None)
        elapsed = time.monotonic() - t0

        assert elapsed >= 0.15

    def test_interval_applied_even_on_exception(self):
        """PipelineQueue updates timestamp in finally block."""
        class FailingAgent:
            def process_message(self, *args, **kwargs):
                raise RuntimeError("boom")

        pq = PipelineQueue(FailingAgent(), max_concurrency=1, pipeline_interval_ms=200)
        with pytest.raises(RuntimeError):
            pq.process_message("a", [], None)
        t0 = time.monotonic()
        with pytest.raises(RuntimeError):
            pq.process_message("b", [], None)
        elapsed = time.monotonic() - t0

        assert elapsed >= 0.15

    def test_forwards_callbacks(self):
        """send_status and send_agent_output are passed through."""
        agent = MagicMock()
        agent.process_message.return_value = "ok"

        pq = PipelineQueue(agent, max_concurrency=1, pipeline_interval_ms=0)

        def status(s, d):
            pass

        def output(l, c, s):
            pass

        pq.process_message("hi", [], None, send_status=status, send_agent_output=output)
        agent.process_message.assert_called_with(
            "hi", [], None,
            send_status=status,
            send_agent_output=output,
        )


# ---------------------------------------------------------------------------
#  helpers / standalone runner
# ---------------------------------------------------------------------------

def run_all():
    """Run tests via pytest with verbose output."""
    import pytest as _pytest
    sys.exit(_pytest.main([__file__, "-v", "--tb=short"]))


if __name__ == "__main__":
    run_all()
