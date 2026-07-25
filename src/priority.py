"""優先度判定。LLM の軸スコアから priority / drop_candidate を決定論的に導出する。

LLM に "high / medium / low" を直接選ばせると、ブックマーク済み記事は
「そもそも多少は興味がある」ものばかりなので判定が high に偏る。
そこで LLM には 4 軸の採点（PriorityScores）だけをさせ、
priority への変換はこのモジュールの閾値で行う。閾値を変えれば
プロンプトを触らずに仕分けの厳しさを調整できる。
"""

from src.models import Priority, PriorityScores

# 4 軸 × 0〜3 = 合計 0〜12。
# high は「今すぐ本文を読む」枠なので上位の一部だけに絞る。
#
# MEDIUM_TOTAL_MIN は実測に基づく値。LLM は各軸に 2 を付けたがるため、
# 実際の合計は 0〜12 に散らず 5〜10 に固まる（15 件の実測で中央値 8、
# 軸別平均 1.8〜2.2）。理論値の中間（5）を境界にすると low が一件も出ないため、
# 実測レンジの中央に合わせて 8 にしている。
# プロンプトの採点基準を変えるとこの分布も動くので、両者はセットで調整すること。
HIGH_TOTAL_MIN = 10
MEDIUM_TOTAL_MIN = 8

# high は「要約では足りず本文を読む価値がある」ものに限定する。
# 新規性・関心が高くても要約で足りる記事は medium に落とす。
HIGH_DEPTH_MIN = 2

# 合計がここ以下なら「捨てる候補」として扱う。
# 現状のスコア分布（最小 5）ではまず発火しない。スコアが下側に散るようになるか、
# LLM が drop_candidate を直接 true で返した場合に効く。
DROP_TOTAL_MAX = 2


def decide_priority(scores: PriorityScores) -> Priority:
    """軸スコアから優先度を決定する。"""
    total = scores.total
    if total >= HIGH_TOTAL_MIN and scores.depth >= HIGH_DEPTH_MIN:
        return Priority.high
    if total >= MEDIUM_TOTAL_MIN:
        return Priority.medium
    return Priority.low


def is_drop_candidate(scores: PriorityScores) -> bool:
    """軸スコアから「捨てる候補」かどうかを判定する。"""
    return scores.total <= DROP_TOTAL_MAX
