from app.services import copilot


def test_relevant_question_matches_knowledge_base():
    result = copilot.ask("What is the maximum team size?")
    assert result.matched_question is not None
    assert "members" in result.answer.lower() or "team" in result.answer.lower()


def test_unrelated_question_falls_back_honestly():
    result = copilot.ask("Can you write my college essay for me?")
    assert result.matched_question is None
    assert "don't have an answer" in result.answer.lower()


def test_empty_question_handled_gracefully():
    result = copilot.ask("")
    assert result.confidence == 0.0
    assert result.matched_question is None
