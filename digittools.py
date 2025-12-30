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
    """Return a DataFrame with subdigit repeats for a given number of digits."""
    initial_df = pl.DataFrame(
        ((1, ndigits),),
        dict.fromkeys(("subndigits", "repeats"), dtype),
        orient="row",
    )
    if possible_factors := range(2, math.isqrt(ndigits) + 1):
        initial_df.extend(
            divisors := pl.LazyFrame(
                {
                    "factors": possible_factors,
                },
                {"factors": dtype},
            )
            .with_columns(
                coefficient=ndigits // pl.col.factors,
                mod=ndigits % pl.col.factors,
            )
            .filter(mod=0)
            .select(subndigits="factors", repeats="coefficient")
            .collect()
        )
        inverted = divisors.filter(c.subndigits != c.repeats)[:, ::-1]
        inverted.columns = initial_df.columns
        if not inverted.is_empty():
            initial_df.extend(inverted)

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
    print(subdigit_repeats(12))
    print(ndigits(1234567890))
