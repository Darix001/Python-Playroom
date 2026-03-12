import polars as pl


def expr_namespace(**exprs: pl.Expr) -> dict[str, pl.Expr]:
    for alias, expr in exprs.items():
        exprs[alias] = expr.alias(alias)
    return exprs


def join_range(
    *args, dtype: pl.DataType | pl.DataTypeExpr | type = pl.UInt64, sep: str = " "
) -> str:
    return pl.select(
        pl.int_range(*args, dtype=dtype, eager=False).cast(str).str.join(sep)
    ).item()
