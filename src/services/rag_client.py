# rag_client.py
import httpx

# Your friend exposes this endpoint — agree on this spec together now
RAG_API_URL = "http://localhost:8001/retrieve"

async def retrieve_context(query: str, scene: str, top_k: int = 3) -> str:
    """
    Calls your friend's RAG service.
    Returns a string of relevant cultural facts to inject into the prompt.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(RAG_API_URL, json={
                "query": query,
                "scene": scene,        # helps filter to relevant documents
                "top_k": top_k
            })
            data = response.json()
            # Expect: { "results": ["fact 1", "fact 2", "fact 3"] }
            return "\n".join(data.get("results", []))
    except Exception as e:
        # If RAG is down, agent still works — just without grounding
        print(f"RAG unavailable: {e}")
        return ""