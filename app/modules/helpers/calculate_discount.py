from decimal import Decimal


def calculate_discounted_price(precio: Decimal, descuento: Decimal) -> Decimal:
    """
    Calcula el precio final aplicando un porcentaje de descuento.

    Args:
        precio: Precio original.
        descuento: Porcentaje de descuento (0-100).

    Returns:
        Precio final como entero.
    """
    return (precio - (precio * descuento / 100))