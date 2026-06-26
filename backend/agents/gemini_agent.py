import json
from pathlib import Path

from google.genai.errors import ServerError as GeminiServerError

from backend.agents.base import BaseAgent
from backend.agents.interaction_agent import InteractionAgent
from backend.agents.request_handler_agent import RequestHandlerAgent
from backend.agents.validation_agent import ValidationAgent
from backend.core.config import settings
from backend.core.gemini_queue import GeminiRequestQueue
from backend.core.product_store import (
    add_search_results,
    format_products_context,
    get_latest_products,
    clear_search_history,
)
from backend.mcp_client.parsers import parse_tool_response
from backend.services.image_service import ImageService

MAX_RETRIES = 2


def _load_system_prompt() -> str:
    path = Path(__file__).resolve().parent.parent / "prompts" / "system.md"
    return path.read_text(encoding="utf-8")


def _parse_products_from_mcp(tool_name: str, mcp_response: str) -> list[dict]:
    return parse_tool_response(tool_name, mcp_response)


class GeminiAgent(BaseAgent):
    def __init__(self, queue: GeminiRequestQueue, image_service: ImageService | None = None):
        self._system_prompt = _load_system_prompt()
        self._interaction = InteractionAgent(queue)
        self._request_handler = RequestHandlerAgent(queue)
        self._validation = ValidationAgent(queue)
        self._image_service = image_service or ImageService(settings.image_storage_dir)
        print("[ORCHESTRATOR] Initialised with 3 sub-agents + product store")

    def process_message(
        self,
        user_message: str,
        history: list[dict],
        mcp_client,
        send_status=None,
        send_agent_output=None,
        send_products=None,
        user_id=None,
    ) -> str:
        print(f"\n{'='*60}")
        print(f"[ORCHESTRATOR] Received user message: {user_message[:80]}...")
        print(f"[ORCHESTRATOR] History entries: {len(history)}, user_id: {user_id}")

        if send_status:
            send_status("interacting", "Understanding your request...")

        try:
            return self._process(user_message, history, mcp_client, send_status, send_agent_output, send_products, user_id)
        except GeminiServerError as e:
            print(f"[ORCHESTRATOR] Gemini API error: {e.code} - {e.message[:100]}")
            if send_status:
                send_status("done", "Service temporarily unavailable")
            return (
                "I'm sorry, the AI service is temporarily overloaded. "
                "Please try again in a moment."
            )

    def _process(
        self, user_message, history, mcp_client, send_status, send_agent_output, send_products=None, user_id=None,
    ) -> str:
        enriched_history = self._enrich_history_with_product_context(history, user_id)

        print("[ORCHESTRATOR] >> Sending to InteractionAgent.chat()...")
        chat_response = self._interaction.chat(user_message, enriched_history, send_agent_output)
        print(f"[ORCHESTRATOR] << InteractionAgent response ({len(chat_response)} chars)")
        if send_agent_output:
            send_agent_output("Conversation Analysis", chat_response, "info")

        requirements = self._extract_requirements(chat_response)
        if requirements is None:
            print("[ORCHESTRATOR] No structured requirements found, returning raw response")
            return chat_response

        print(f"[ORCHESTRATOR] Extracted requirements: {json.dumps(requirements, indent=2)[:200]}...")

        for attempt in range(1, MAX_RETRIES + 1):
            print(f"\n[ORCHESTRATOR] --- Attempt {attempt}/{MAX_RETRIES} ---")
            if send_status:
                send_status("building_request", f"Building request (attempt {attempt}/{MAX_RETRIES})...")

            req_text = json.dumps(requirements, indent=2)
            print(f"[ORCHESTRATOR] >> Sending to RequestHandlerAgent.build_request()...")
            tool_call = self._request_handler.build_request(req_text, send_agent_output)
            if tool_call is None:
                print("[ORCHESTRATOR] RequestHandlerAgent returned None")
                return self._interaction.explain_limitations(
                    "Could not build a valid request from the requirements.", enriched_history
                )

            tool_name = tool_call.get("tool")
            tool_args = tool_call.get("arguments", {})
            tool_call_str = json.dumps(tool_call, indent=2)
            print(f"[ORCHESTRATOR] Tool call: {tool_name}({json.dumps(tool_args)[:150]})")
            if send_agent_output:
                send_agent_output("Request Builder", tool_call_str, "success")

            if send_status:
                detail = tool_name.replace("kapruka_", "").replace("_", " ")
                send_status("searching", f"{detail}... (attempt {attempt}/{MAX_RETRIES})")

            print(f"[ORCHESTRATOR] >> Calling MCP tool: {tool_name}...")
            mcp_response = mcp_client.call_tool(tool_name, tool_args)
            print(f"[ORCHESTRATOR] << MCP response ({len(mcp_response)} chars)")
            print(f"[ORCHESTRATOR] MCP response preview: {mcp_response[:200]}")

            if tool_name in ("kapruka_search_products", "kapruka_get_product") and user_id:
                products = _parse_products_from_mcp(tool_name, mcp_response)
                if products:
                    print(f"[ORCHESTRATOR] Storing {len(products)} products in product_store for user {user_id}")
                    add_search_results(user_id, tool_call, mcp_response, products)

            if send_status:
                send_status("validating", f"Checking results (attempt {attempt}/{MAX_RETRIES})...")

            user_req_text = user_message
            if isinstance(requirements, dict):
                user_req_text = json.dumps(requirements, indent=2)

            print(f"[ORCHESTRATOR] >> Sending to ValidationAgent.validate()...")
            verdict = self._validation.validate(
                user_req_text, tool_call, mcp_response, send_agent_output
            )
            verdict_satisfied = verdict.get("satisfied")
            print(f"[ORCHESTRATOR] << Validation verdict: satisfied={verdict_satisfied}")
            print(f"[ORCHESTRATOR]    Feedback: {verdict.get('feedback', '')[:150]}")
            if send_agent_output:
                status = "success" if verdict_satisfied else ("retry" if attempt < MAX_RETRIES else "failure")
                send_agent_output("Validation", json.dumps(verdict, indent=2), status)

            if verdict_satisfied:
                print("[ORCHESTRATOR] Validation PASSED - presenting results")

                if send_products and tool_name in ("kapruka_search_products", "kapruka_get_product"):
                    print("[ORCHESTRATOR] Processing product images...")
                    try:
                        products_data = self._image_service.process_search_response(tool_name, mcp_response)
                        if products_data:
                            print(f"[ORCHESTRATOR] Emitting {len(products_data)} products with images")
                            send_products(products_data)

                            if user_id:
                                stored = get_latest_products(user_id)
                                if stored:
                                    add_search_results(user_id, tool_call, mcp_response, stored, image_results=products_data)
                        else:
                            print("[ORCHESTRATOR] No products with images retrieved")
                    except Exception as e:
                        print(f"[ORCHESTRATOR] Image processing error: {e}")

                if send_status:
                    send_status("done", "Found matching results!")
                final = self._interaction.present_results(mcp_response, enriched_history)
                if send_agent_output:
                    send_agent_output("Final Response", final, "success")
                return final

            if attempt < MAX_RETRIES:
                refined = verdict.get("refined_request")
                if refined and isinstance(refined, dict):
                    requirements = refined
                    print(f"[ORCHESTRATOR] Retry with refined request: {json.dumps(refined)[:200]}")
                    if send_status:
                        fb = verdict.get("feedback", "Refining search...")
                        send_status("retrying", f"{fb} (retry {attempt + 1}/{MAX_RETRIES})")
                    continue

            fb = verdict.get("feedback", "Could not find suitable results.")
            print(f"[ORCHESTRATOR] No retry possible, explaining limitations: {fb[:150]}")
            limitation = self._interaction.explain_limitations(fb, enriched_history)
            if send_agent_output:
                send_agent_output("Unable to Fulfill", limitation, "failure")
            return limitation

        print("[ORCHESTRATOR] Max retries exhausted")
        limitation = self._interaction.explain_limitations(
            "Could not find suitable results after multiple attempts.", enriched_history
        )
        if send_agent_output:
            send_agent_output("Unable to Fulfill", limitation, "failure")
        return limitation

    def _enrich_history_with_product_context(self, history, user_id):
        if not user_id:
            return history
        product_context = format_products_context(user_id)
        if not product_context:
            return history

        enriched = list(history)
        enriched.append({
            "role": "system",
            "content": (
                "The following products were previously shown to the customer in this session.\n"
                "If the customer refers to a product they saw earlier (e.g., 'that cake', 'the first one', 'the chocolate one'), "
                "use this information to identify which product they mean.\n\n"
                f"{product_context}"
            ),
        })
        print(f"[ORCHESTRATOR] Injected product context ({len(product_context)} chars) into history")
        return enriched

    def _extract_requirements(self, text: str) -> dict | None:
        import re
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except (ValueError, json.JSONDecodeError):
                return None
        return None
