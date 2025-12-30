import math

import polars as pl

c = pl.col


def string_lit(value) -> pl.Expr:
    return pl.lit(value, pl.String)


def mul_string(expr: pl.Expr, n: pl.Expr | int) -> pl.Expr:
    return expr.repeat_by(n).list.join("")


KEY_COLUMN = mul_string(string_lit(1).str.zfill(c.subndigits), c.repeats).alias("key")


def subdigit_repeats(
    ndigits: int,
    /,
    gen_keys: bool = False,
    dtype: type | pl.DataType = pl.UInt8,
    keys_type: type | pl.DataType = pl.UInt64,
) -> pl.DataFrame:
    """Return a DataFrame with subdigit repeats for a given number of digits.

    Parameters:
        ndigits (int): The number of digits to generate subdigit repeats for.
        gen_keys (bool): Whether to generate keys for each subdigit repeat.
        dtype (type | pl.DataType): The data type to use for the subdigit and repeat columns.
        keys_type (type | pl.DataType): The data type to use for the key column.

        the keys represents the lowest possible subdigit repeat,
        which is the smallest number that can be repeated to form the given number of digits.
        This column is by default casted to UInt64.
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
    initial_df = pl.DataFrame(
        ((1, ndigits),),
        dict.fromkeys(("subndigits", "repeats"), dtype),
        orient="row",
    )
    initial_df.extend(
        (
            initial_df.lazy()
            .select(
                pl.int_range(2, c.repeats.first().sqrt() + 1, dtype=dtype).alias(
                    "subndigits"
                )
            )
            .with_columns(
                repeats=ndigits // c.subndigits,
            )
            .filter((ndigits % c.subndigits) == 0)
            .select(pl.all().append(pl.nth(1, 0).filter(c.subndigits != c.repeats)))
        ).collect()
    )

    if gen_keys:
        initial_df = initial_df.with_columns(KEY_COLUMN.cast(keys_type))

    return initial_df


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
    print(subdigit_repeats(6, gen_keys=True, keys_type=str))
    print(ndigits(1234567890))
    print(digit_range(5))
