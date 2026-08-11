def calculate_product_ammount(product: dict) -> float:
    """
    Calculates the expected product amount of a recipe product.
    """

    amount = product["amount"]

    if "extra_count_fraction" in product:
        return amount + product["extra_count_fraction"]

    if "independent_probability" in product:
        return amount * product["independent_probability"]

    return float(amount)
