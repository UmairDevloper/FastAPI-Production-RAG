
from langchain_core.documents import Document

from app.retrieval.context_assembly import assemble_context
from app.retrieval.fusion import reciprocal_rank_fusion


def test_assembled_context_preserves_fusion_score():
    first = Document(
        page_content="FastAPI reads JSON request bodies.",
        metadata={
            "chunk_id": "chunk-1",
            "url": "https://fastapi.tiangolo.com/",
            "dense_score": 0.8,
        },
    )
    second = Document(
        page_content="FastAPI supports path parameters.",
        metadata={
            "chunk_id": "chunk-2",
            "url": "https://fastapi.tiangolo.com/tutorial/",
            "dense_score": 0.7,
        },
    )

    fused = reciprocal_rank_fusion([[first, second]])

    result = assemble_context(fused)

    assert len(result.evidence) == 2
    assert result.evidence[0].evidence_id == "chunk_id:chunk-1"
    assert result.evidence[0].score is not None
    assert result.evidence[0].score > result.evidence[1].score
    assert "https://fastapi.tiangolo.com/" in result.context



def test_assembly_respects_document_limit():
    documents = [
        Document(
            page_content=f"Useful documentation content {i}.",
            metadata={"chunk_id": f"chunk-{i}"},
        )
        for i in range(4)
    ]

    result = assemble_context(documents, max_documents=2)

    assert len(result.evidence) == 2
    assert result.omitted_documents == 2


def test_assembly_rejects_invalid_budget():
    try:
        assemble_context([], max_tokens=0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")
