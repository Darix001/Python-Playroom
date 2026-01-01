import math
import operator as op

import polars as pl

cols: tuple[pl.Expr, ...] = tuple(map(pl.col, col_names := ("subndigits", "repeats")))
minv_col = pl.lit("1").str.zfill(cols[0]).repeat_by(cols[1]).list.join("").alias("minv")
repeat_type = pl.dtype_of("repeats")
fact_range = pl.int_range(
    2, cols[1].first().sqrt().cast(repeat_type) + 1, dtype=repeat_type
).alias("subndigits")
with_inverted_ne = pl.all().append(pl.col(*col_names[::-1])).filter(op.ne(*cols))


def subdigit_repeats(
    ndigits: int,
    dtype: type | pl.DataType | pl.DataTypeExpr = pl.UInt8,
    /,
    minv: bool = False,
    minv_dtype: type | pl.DataType | pl.DataTypeExpr = pl.UInt64,
) -> pl.DataFrame:
    """Return a DataFrame with subdigit repeats for a given number of digits.

    Parameters:
        ndigits (int): The number of digits to generate subdigit repeats for.
        dtype (type | pl.DataType | pl.DataTypeExpr): main dtype of the dataframe
        minv (bool): Whether to generate the minimum value for each subdigit repeat.
        minv_dtype (type | pl.DataType | pl.DataTypeExpr): The data type to use for the minv column.

    Returns:
        pl.DataFrame: A DataFrame with subdigit repeats for the given number of digits.

    Example:
        >>> subdigit_repeats(4)
        ┌────────────┬─────────┐
        │ subndigits ┆ repeats │
        │ ---        ┆ ---     │
        │ u8         ┆ u8      │
        ╞════════════╪═════════╡
        │ 1          ┆ 4       │
        │ 2          ┆ 2       │
        └────────────┴─────────┘

        >>>subdigit_repeats(6, gen_keys=True, keys_type=str)
        ┌────────────┬─────────┬────────┐
        │ subndigits ┆ repeats ┆ key    │
        │ ---        ┆ ---     ┆ ---    │
        │ u8         ┆ u8      ┆ str    │
        ╞════════════╪═════════╪════════╡
        │ 1          ┆ 6       ┆ 111111 │
        │ 2          ┆ 3       ┆ 010101 │
        │ 3          ┆ 2       ┆ 001001 │
        └────────────┴─────────┴────────┘
    """
    initial_df = pl.LazyFrame(
        ((1, ndigits),), dict.fromkeys(col_names, dtype), orient="row"
    )
    new_df = (
        initial_df.select(fact_range)
        .with_columns(
            repeats=ndigits // cols[0],
        )
        .filter((ndigits % cols[0]) == 0)
        .select(with_inverted_ne)
    )
    initial_df = pl.concat((initial_df, new_df))

    if minv:
        initial_df = initial_df.with_columns(minv_col.cast(minv_dtype))

    return initial_df.collect()


def digit_range(ndigits: int, /) -> range:
    if ndigits < 1:
        raise ValueError("ndigits must be positive")
    x = 10 ** (ndigits - 1)
    return range(x, x * 10)


# Source - https://stackoverflow.com/a
# Posted by Simply Beautiful Art, modified by community. See post 'Timeline' for change history
# Retrieved 2025-12-30, License - CC BY-SA 4.0


def ndigits(n: int) -> int:
    assert n > 0
    i = math.trunc(0.30102999566398114 * (n.bit_length() - 1)) + 1
    return (10**i <= n) + i


if __name__ == "__main__":
    print(subdigit_repeats(6, minv=True, minv_dtype=str))
    print(ndigits(1234567890))
    print(digit_range(5))
