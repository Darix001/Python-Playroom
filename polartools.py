import polars as pl


def expr_namespace(**exprs: pl.Expr) -> dict[str, pl.Expr]:
    for alias, expr in exprs.items():
        exprs[alias] = expr.alias(alias)
    return exprs
