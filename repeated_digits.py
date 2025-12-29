from math import isqrt

import polars as pl

c = pl.col


def string_lit(value) -> pl.Expr:
    return pl.lit(value, pl.String)


def mul_string(expr: pl.Expr, n: pl.Expr | int) -> pl.Expr:
    return expr.repeat_by(n).list.join("")


ndigitssub1 = c.subndigits - 1
KEY_COLUMN = pl.concat_str(
    one := string_lit(1),
    mul_string(
        pl.concat_str(mul_string(string_lit(0), ndigitssub1), one), c.repeats - 1
    ),
).alias("key")
del ndigitssub1


def get_divisors(ndigits: int, /, dtype=pl.UInt8, keys_type=pl.UInt64) -> pl.DataFrame:
    initial_df = pl.DataFrame(
        ((1, ndigits),),
        dict.fromkeys(("subndigits", "repeats"), dtype),
        orient="row",
    )
    if possible_factors := range(2, isqrt(ndigits) + 1):
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
        divisors: pl.DataFrame
        inverted = divisors.filter(c.subndigits != c.repeats)[:, ::-1]
        inverted.columns = initial_df.columns
        if not inverted.is_empty():
            initial_df.extend(inverted)

    initial_df = initial_df.with_columns(KEY_COLUMN.cast(keys_type)).shrink_to_fit()
    return initial_df


if __name__ == "__main__":
    from sys import argv

    print(get_divisors(int(argv[1])).estimated_size())
