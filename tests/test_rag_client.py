# tests/test_rag_client.py
import pytest

# This tells pytest these tests are async
pytestmark = pytest.mark.asyncio

async def test_rag_returns_empty_string_when_server_down():
    """RAG being unavailable must never crash the agent."""
    from src.services.rag_client import retrieve_context
    
    # Point at a port nothing is running on
    import src.services.rag_client as rc
    original = rc.RAG_API_URL
    rc.RAG_API_URL = "http://localhost:9999/retrieve"  # nothing here
    
    result = await retrieve_context("test query", "majlis")
    
    rc.RAG_API_URL = original  # restore
    assert result == ""        # empty string, not an exception

async def test_rag_returns_string():
    """When server is up, result is a non-empty string."""
    from src.services.rag_client import retrieve_context
    result = await retrieve_context("ما هي الدلة؟", "majlis")
    assert isinstance(result, str)
    assert len(result) > 0

async def test_rag_handles_empty_query():
    from src.services.rag_client import retrieve_context
    result = await retrieve_context("", "majlis")
    assert isinstance(result, str)  # should not crash