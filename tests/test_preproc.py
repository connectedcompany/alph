from datetime import date, datetime, timedelta

import pandas as pd
from gralt.preproc import ensure_non_serializable_datetime_types_absent
from pytest import mark, raises


@mark.parametrize(
    "df, problem_cols",
    [
        (pd.DataFrame(), None),
        (pd.DataFrame(columns=["a", "b"], data=[("a", 1), ("b", 2)]), None),
        (
            pd.DataFrame(columns=["a", "b"], data=[(datetime.utcnow(), 1), ("b", 2)]),
            ["a"],
        ),
        (
            pd.DataFrame(
                columns=["a", "b"], data=[(date.today(), timedelta(days=1)), ("b", 2)]
            ),
            ["a", "b"],
        ),
        (
            pd.DataFrame(
                columns=["a", "b"],
                data=[
                    (pd.to_datetime(date.today()), 1),
                    (pd.to_datetime(datetime.now()), 2),
                ],
            ),
            None,
        ),
        (
            pd.DataFrame(
                columns=["a", "b"],
                data=[(pd.NaT, pd.to_timedelta(timedelta(seconds=1))), ("string", 2)],
            ),
            ["b"],
        ),
    ],
)
def test_ensure_non_serializable_datetime_types_absent(df, problem_cols):
    if problem_cols:
        with raises(ValueError, match=f": {', '.join(problem_cols)}$"):
            ensure_non_serializable_datetime_types_absent(df)
    else:
        ensure_non_serializable_datetime_types_absent(df)
