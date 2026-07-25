"""priority.py のテスト。スコアから優先度を導出する仕分けロジックを保証する。"""

import pytest

from src.models import Priority, PriorityScores
from src.priority import decide_priority, is_drop_candidate


def _scores(novelty=0, relevance=0, depth=0, actionability=0) -> PriorityScores:
    return PriorityScores(
        novelty=novelty, relevance=relevance, depth=depth, actionability=actionability
    )


class TestPriorityScores:
    def test_total(self):
        assert _scores(3, 2, 1, 0).total == 6

    def test_clamps_out_of_range(self):
        """LLM が範囲外の値を返しても 0〜3 に丸める。"""
        s = PriorityScores(novelty=9, relevance=-4, depth=3, actionability=0)
        assert s.novelty == 3
        assert s.relevance == 0
        assert s.total == 6

    def test_defaults_to_zero(self):
        assert PriorityScores().total == 0


class TestDecidePriority:
    @pytest.mark.parametrize(
        "scores,expected",
        [
            # 満点は high
            (_scores(3, 3, 3, 3), Priority.high),
            # 合計 10 かつ depth 2 以上 → high
            (_scores(3, 3, 2, 2), Priority.high),
            # 合計 9 は high に届かない
            (_scores(3, 3, 2, 1), Priority.medium),
            # 平均的な記事（合計 5〜9）は medium
            (_scores(2, 2, 1, 2), Priority.medium),
            (_scores(1, 2, 1, 1), Priority.medium),
            # 合計 4 以下は low
            (_scores(1, 1, 1, 1), Priority.low),
            (_scores(1, 1, 0, 0), Priority.low),
            (_scores(0, 0, 0, 0), Priority.low),
        ],
    )
    def test_thresholds(self, scores, expected):
        assert decide_priority(scores) == expected

    def test_high_requires_depth(self):
        """新規性・関心・活用度が満点でも、要約で足りる（depth<2）なら high にしない。"""
        scores = _scores(novelty=3, relevance=3, depth=1, actionability=3)
        assert scores.total == 10
        assert decide_priority(scores) == Priority.medium

    def test_high_is_not_the_default(self):
        """既定値（全 0）が high に倒れないことの回帰テスト。"""
        assert decide_priority(PriorityScores()) == Priority.low


class TestIsDropCandidate:
    @pytest.mark.parametrize(
        "scores,expected",
        [
            (_scores(0, 0, 0, 0), True),
            (_scores(1, 1, 0, 0), True),
            (_scores(1, 1, 1, 0), False),
            (_scores(2, 2, 2, 2), False),
        ],
    )
    def test_drop_threshold(self, scores, expected):
        assert is_drop_candidate(scores) is expected
