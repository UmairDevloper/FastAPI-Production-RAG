import asyncio
import inspect
import traceback

from app.generation.rag_pipeline import build_rag_pipeline


async def main():
    print("Building pipeline...", flush=True)

    try:
        built = build_rag_pipeline()

        # Fix: await it if build_rag_pipeline is async.
        if inspect.isawaitable(built):
            pipeline = await built
        else:
            pipeline = built

        question = "How do I share a database session using dependencies?"
        print(f"Testing: {question}", flush=True)

        response = await pipeline.answer(question)

        print("\nANSWER:\n", response.answer, flush=True)

        supplied = {item.evidence_id for item in response.context.evidence}
        cited = {citation.evidence_id for citation in response.citations}

        print("\nSupplied evidence IDs:", sorted(supplied), flush=True)
        print("Cited evidence IDs:", sorted(cited), flush=True)
        print("Invalid citation IDs:", sorted(cited - supplied), flush=True)
        print("Citation validation:", "PASS" if cited.issubset(supplied) else "FAIL")

    except Exception:
        traceback.print_exc()

    finally:
        # Optional cleanup, only if your pipeline supports it.
        close = getattr(pipeline, "aclose", None) if "pipeline" in locals() else None
        if close:
            result = close()
            if inspect.isawaitable(result):
                await result


if __name__ == "__main__":
    asyncio.run(main())
