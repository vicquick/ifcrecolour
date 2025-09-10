def is_white_rgb(col, eps=1e-6):
    return col and abs(col.Red-1)<eps and abs(col.Green-1)<eps and abs(col.Blue-1)<eps
