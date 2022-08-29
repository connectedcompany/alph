from datetime import date, datetime, timedelta

import pandas as pd
from pandas.api.types import (
    is_datetime64_any_dtype,
    is_timedelta64_dtype,
    is_timedelta64_ns_dtype,
)

PYTHON_DT_TYPES = (datetime, date, timedelta)
PANDAS_DT_TYPES = (pd.Timestamp, pd.Timedelta)


def get_non_serializable_datetime_type_columns(
    df, types, ignore_pandas_dt_cols=True, ignore_na=True
):
    """ "
    Given a dataframe and undesired types, return columns in df that
    have one or more values of those types. This is used to help
    deal with serialisation issues that altair and pandas frame
    serialisaiton via pickle may have, amongst others.

    :param ignore_pandas_dt_cols:   if true, do not inspect columns that
                                    have pandas datetime types - this is
                                    useful for serialising frames
    :param ignore_na:               if true, do not check empty / nan / nat
                                    types; this is useful for pandas
                                    serialisation, which can serialise these
                                    types - and altair plots, which can't

    """
    assert isinstance(types, tuple)

    res = []
    for col in df.columns:
        if ignore_pandas_dt_cols and (
            is_datetime64_any_dtype(df[col])
            or is_timedelta64_dtype(df[col])
            or is_timedelta64_ns_dtype(df[col])
        ):
            continue

        if (
            df[col]
            .pipe(lambda x: x.dropna() if ignore_na else x)
            .apply(lambda x: isinstance(x, types))
            .any()
        ):
            res.append(col)
    return res


def ensure_non_serializable_datetime_types_absent(df, types=None):
    """Raise if any value in each column is a non-serializable type,
    to avoid downstream problems
    """
    types = types or PYTHON_DT_TYPES

    problem_cols = get_non_serializable_datetime_type_columns(df, types)

    if problem_cols:
        raise ValueError(
            f"The following column(s) had instances of {types}, potentially causing serialization problems: "
            f"{', '.join(problem_cols)}"
        )
