def capping(df, cap, weight_column='weight', tol=1e-3, inplace=False):
    if not inplace:
        df = df.copy()

    capped = df[weight_column] > (cap + tol)

    if not capped.any():
        return df

    df.loc[~capped, weight_column] *= 1 + \
        (df.loc[capped, weight_column]-cap).sum() / \
        df.loc[~capped, weight_column].sum()
    df.loc[capped, weight_column] = cap

    return capping(df, cap, weight_column, tol, inplace=True)
