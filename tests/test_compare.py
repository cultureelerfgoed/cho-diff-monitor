from chodiff.compare import compare_days, compare_week, deviations, week_deviations

A, B, C = "https://ex.org/A", "https://ex.org/B", "https://ex.org/C"


def test_compare_days_includes_new_and_disappeared_items():
    rows = {r.item: r for r in compare_days({A: 10, B: 5}, {A: 7, C: 3})}
    assert set(rows) == {A, B, C}
    assert rows[A].diff == 3
    assert rows[B].is_new and rows[B].diff == 5
    assert rows[C].is_gone and rows[C].diff == -3


def test_compare_days_sorted_by_diff_descending_then_item():
    rows = compare_days({A: 1, B: 1, C: 9}, {A: 1, B: 0, C: 10})
    assert [r.item for r in rows] == [B, A, C]


def test_deviations_largest_absolute_first_and_zero_excluded():
    rows = compare_days({A: 1, B: 0, C: 5}, {A: 1, B: 10, C: 4})
    assert [r.item for r in deviations(rows)] == [B, C]


def test_compare_week_items_appearing_midweek_are_kept():
    days = [{A: 1}, {A: 1}, {A: 2, B: 4}, {A: 2, B: 4}, {A: 2, B: 4}, {A: 2, B: 4}, {A: 3}]
    rows = {r.item: r for r in compare_week(days)}
    assert rows[B].counts == (0, 0, 4, 4, 4, 4, 0)
    assert rows[B].total == 0
    assert rows[B].changed  # netto 0, maar wel veranderd
    assert rows[A].diffs == (0, 1, 0, 0, 0, 1)
    assert rows[A].total == 2
    assert not rows[A].is_new and not rows[B].is_new  # B kwam én ging binnen de week


def test_week_new_and_gone():
    rows = {r.item: r for r in compare_week([{A: 1}] * 6 + [{B: 2}])}
    assert rows[A].is_gone and rows[B].is_new


def test_week_deviations_excludes_unchanged():
    days = [{A: 1, B: 2}] * 7
    assert week_deviations(compare_week(days)) == []
