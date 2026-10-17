"""Provider selection and real SDK dispatch through a deterministic HTTP MCP peer."""

import asyncio
import json
import os
import unittest
from unittest.mock import patch

import httpx
from agents import Model, ModelResponse, RunConfig, Runner, Usage
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseOutputMessage,
    ResponseOutputText,
)

# Import configuration without reading local credentials or creating a real DB.
with patch.dict(os.environ, {
    "OPENAI_API_KEY": "test-openai-key",
    "GITHUB_PERSONAL_ACCESS_TOKEN": "test-github-token",
    "DB_PATH": "data/test-conversations.db",
}), patch("dotenv.load_dotenv"):
    from src.devmind import config
    from src.devmind.agents import web_research_agent as research
    from src.devmind.mcp.servers import parallel_search_mcp_server
    from src.devmind.tools.web_search import web_search


class MCPPeer:
    """A JSON-RPC peer behind the real MCP Streamable HTTP transport."""

    def __init__(self, failure=None):
        self.requests = []
        self.failure = failure
        self.call_started = asyncio.Event()
        self.client = None

    def client_factory(self, headers=None, timeout=None, auth=None):
        self.client = httpx.AsyncClient(
            headers=headers, timeout=timeout, auth=auth,
            transport=httpx.MockTransport(self.handle),
        )
        return self.client

    async def handle(self, request):
        body = json.loads(request.content) if request.content else {}
        self.requests.append((request, body))
        if request.method != "POST":
            return httpx.Response(405)
        if "id" not in body:
            return httpx.Response(202)
        method = body["method"]
        if method == "initialize":
            result = {
                "protocolVersion": body["params"]["protocolVersion"],
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "test-peer", "version": "1"},
            }
        elif method == "tools/list":
            result = {"tools": [
                {"name": "web_search", "description": "Search the web", "inputSchema": {
                    "type": "object", "properties": {
                        "objective": {"type": "string"},
                        "search_queries": {"type": "array", "items": {"type": "string"}},
                    }, "required": ["objective", "search_queries"],
                }},
                {"name": "web_fetch", "description": "Fetch a page", "inputSchema": {
                    "type": "object", "properties": {
                        "urls": {"type": "array", "items": {"type": "string"}},
                    }, "required": ["urls"],
                }},
            ]}
        elif method == "tools/call":
            self.call_started.set()
            if self.failure == "wait":
                await asyncio.Event().wait()
            if self.failure == "error":
                result = {"isError": True, "content": [
                    {"type": "text", "text": "Search unavailable; please retry later."},
                ]}
            else:
                text = (
                    "Handoff documentation: https://openai.github.io/openai-agents-python/handoffs/"
                    if body["params"]["name"] == "web_search"
                    else "Structured handoff data is declared with input_type."
                )
                result = {"content": [{"type": "text", "text": text}]}
        else:
            raise AssertionError(f"Unexpected method: {method}")
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": body["id"], "result": result})

    def assert_requests(self, test):
        test.assertTrue(self.requests)
        for request, _ in self.requests:
            test.assertEqual(str(request.url), "https://search.parallel.ai/mcp")
            test.assertIn("Devmind-AI-Dev-Assistant", request.headers["user-agent"])
            test.assertIn("github.com/muneeb-rashid-cyan/Devmind-AI-Dev-Assistant", request.headers["user-agent"])
            test.assertNotIn("authorization", request.headers)
            test.assertNotIn("cookie", request.headers)


class ResearchModel(Model):
    """Selects real SDK tools, then builds output from the tool results it sees."""

    def __init__(self, fetch=True):
        self.turn = 0
        self.fetch = fetch

    async def get_response(self, system_instructions, input, model_settings, tools, **kwargs):
        names = [tool.name for tool in tools]
        if names.count("web_search") != 1 or "web_fetch" not in names:
            raise AssertionError(f"Unexpected tools: {names}")
        self.turn += 1
        if self.turn == 1:
            output = [ResponseFunctionToolCall(
                type="function_call", name="web_search", call_id="search-1",
                arguments=json.dumps({
                    "objective": "Find current handoff documentation",
                    "search_queries": ["OpenAI Agents SDK handoffs"],
                }),
            )]
        elif self.turn == 2 and self.fetch:
            if "https://openai.github.io/" not in json.dumps(input):
                raise AssertionError("Search content did not reach the model")
            output = [ResponseFunctionToolCall(
                type="function_call", name="web_fetch", call_id="fetch-1",
                arguments=json.dumps({"urls": [
                    "https://openai.github.io/openai-agents-python/handoffs/",
                ]}),
            )]
        else:
            content = "\n".join(
                str(item["output"]) for item in input
                if isinstance(item, dict) and item.get("type") == "function_call_output"
            )
            output = [ResponseOutputMessage(
                type="message", id="answer", role="assistant", status="completed",
                content=[ResponseOutputText(type="output_text", text=content, annotations=[])],
            )]
        return ModelResponse(output=output, usage=Usage(), response_id=f"response-{self.turn}")

    async def stream_response(self, *args, **kwargs):
        raise NotImplementedError
        yield


class WebResearchTests(unittest.IsolatedAsyncioTestCase):
    def server_for(self, peer):
        server = parallel_search_mcp_server()
        server.params["httpx_client_factory"] = peer.client_factory
        return server

    async def test_default_provider_never_starts_parallel(self):
        filesystem = object()
        with patch.object(config, "WEB_SEARCH_PROVIDER", "duckduckgo"), \
                patch.object(research, "parallel_search_mcp_server") as factory:
            async with research.open_web_research_agent(filesystem) as agent:
                self.assertEqual(agent.tools, [web_search])
                self.assertEqual(agent.mcp_servers, [filesystem])
                self.assertEqual(agent.model, config.SPECIALIST_MODEL)
                self.assertEqual(agent.instructions, research.WEB_RESEARCH_INSTRUCTIONS)
            factory.assert_not_called()

    async def test_unknown_provider_fails_explicitly(self):
        with patch.object(config, "WEB_SEARCH_PROVIDER", "typo"):
            with self.assertRaisesRegex(ValueError, "WEB_SEARCH_PROVIDER"):
                async with research.open_web_research_agent(object()):
                    self.fail("Invalid provider was accepted")

    async def run_research(self, peer, fetch=True, timeout=None):
        server = self.server_for(peer)
        if timeout is not None:
            server.client_session_timeout_seconds = timeout
        with patch.object(config, "WEB_SEARCH_PROVIDER", "parallel"), \
                patch.object(research, "parallel_search_mcp_server", return_value=server):
            async with research.open_web_research_agent(object()) as agent:
                self.assertEqual(agent.tools, [])
                self.assertIs(agent.mcp_servers[-1], server)
                # The unrelated filesystem server is not needed for these research calls.
                agent.mcp_servers = [server]
                agent.model = ResearchModel(fetch=fetch)
                result = await Runner.run(
                    agent, "Find the handoff documentation and explain it",
                    run_config=RunConfig(tracing_disabled=True),
                )
        self.assertTrue(peer.client.is_closed)
        peer.assert_requests(self)
        return result

    async def test_parallel_search_fetch_and_result_consumption(self):
        peer = MCPPeer()
        result = await self.run_research(peer)
        self.assertIn("https://openai.github.io/", result.final_output)
        self.assertIn("input_type", result.final_output)
        methods = [body.get("method") for _, body in peer.requests]
        self.assertIn("initialize", methods)
        self.assertEqual(methods.count("tools/list"), 1)
        calls = [body["params"] for _, body in peer.requests if body.get("method") == "tools/call"]
        self.assertEqual([call["name"] for call in calls], ["web_search", "web_fetch"])
        self.assertEqual(calls[0]["arguments"]["search_queries"], ["OpenAI Agents SDK handoffs"])
        self.assertEqual(calls[1]["arguments"]["urls"], [
            "https://openai.github.io/openai-agents-python/handoffs/",
        ])

    async def test_mcp_error_reaches_model_without_fake_results(self):
        result = await self.run_research(MCPPeer(failure="error"), fetch=False)
        self.assertIn("Search unavailable", result.final_output)
        self.assertNotIn("input_type", result.final_output)

    async def test_timeout_reaches_model_and_closes_client(self):
        peer = MCPPeer(failure="wait")
        result = await self.run_research(peer, fetch=False, timeout=0.05)
        self.assertIn("timed out", result.final_output.lower())

    async def test_connection_failure_does_not_fall_back(self):
        peer = MCPPeer()
        server = self.server_for(peer)

        async def unavailable(request):
            peer.requests.append((request, {}))
            return httpx.Response(503)

        peer.handle = unavailable
        with patch.object(config, "WEB_SEARCH_PROVIDER", "parallel"), \
                patch.object(research, "parallel_search_mcp_server", return_value=server):
            with self.assertRaisesRegex(Exception, "503"):
                async with research.open_web_research_agent(object()):
                    self.fail("Unavailable provider was silently replaced")
        self.assertTrue(peer.client.is_closed)
        peer.assert_requests(self)

    async def test_cancellation_propagates_and_closes_client(self):
        peer = MCPPeer(failure="wait")
        server = self.server_for(peer)
        with patch.object(config, "WEB_SEARCH_PROVIDER", "parallel"), \
                patch.object(research, "parallel_search_mcp_server", return_value=server):
            async with research.open_web_research_agent(object()) as agent:
                agent.mcp_servers = [server]
                agent.model = ResearchModel(fetch=False)
                task = asyncio.create_task(Runner.run(
                    agent, "Find handoff docs", run_config=RunConfig(tracing_disabled=True),
                ))
                await asyncio.wait_for(peer.call_started.wait(), timeout=2)
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task
        self.assertTrue(peer.client.is_closed)
        peer.assert_requests(self)


if __name__ == "__main__":
    unittest.main()
