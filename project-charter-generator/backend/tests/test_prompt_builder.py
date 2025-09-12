from app.services import prompt_builder


def test_build_context_block_basic():
    docs = [
        {"id": "d1", "content": "First doc"},
        {"id": "d2", "content": "Second doc"}
    ]
    ctx = prompt_builder.build_context_block(docs)

    # Expect numbered lines in the returned context
    assert "1. First doc" in ctx
    assert "2. Second doc" in ctx
    # There should be exactly one newline between the two lines
    assert ctx.count("\n") == 1


def test_build_context_block_with_text_fallback():
    # If 'content' missing but 'text' exists, it should fall back to text
    docs = [
        {"id": "d1", "text": "Fallback text"},
        {"id": "d2"}  # no content or text
    ]
    ctx = prompt_builder.build_context_block(docs)

    assert "1. Fallback text" in ctx
    # second doc had no text => should not produce a "2." line with empty content
    assert "2." not in ctx


def test_build_prompt_fills_template():
    # Provide a tiny docs list and instructions, then ensure pieces appear in the final prompt
    docs = [{"content": "Example content"}]
    prompt = prompt_builder.build_prompt("What is this?", docs, questionnaire="Be brief")

    assert "What is this?" in prompt
    assert "Example content" in prompt
    assert "Be brief" in prompt
