# Explanation pipeline

Router, retrieval, generation, validation, fallback. Requirements R1 and R3.

**Rules:** The LLM has no tools and writes no numbers. Clinical questions and distress go to humans.

**Status:** stubs only. No code until requested.

## Sub-folders

- `lexicon/`
- `prompts/`
- `templates/`
- `validators/`

## Files

| File | Purpose | Phase | Issues |
|---|---|---|---|
| `context.py` | Requester's fact set. | 4.3 | C7 |
| `graph.py` | LangGraph pipeline. | 4.3 | C5, H9, M1, M4 |
| `llm.py` | LLM adapter. | 4.3 | H9 |
| `retriever.py` | RAG retrieval. | 4.3 | H15 |
| `router.py` | Boundary classification. | 4.3 | C6, C10 |
| `state.py` | Graph state. | 4.3 |  |
