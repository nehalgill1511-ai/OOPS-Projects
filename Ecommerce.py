# ===== Starter Template: E-Commerce Cart System =====
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict


class PricingStrategy(ABC):

    @abstractmethod
    def calculate(self, subtotal: float) -> float:
        pass


class NoDiscount(PricingStrategy):
    def calculate(self, subtotal: float) -> float:
        # return subtotal unchanged
        return subtotal


class PercentageDiscount(PricingStrategy):
    def __init__(self, percent: float):
        # validate 0..100
        if not (0 <= percent <= 100):
            raise ValueError("Percent must be between 0 and 100")
        self.percent = percent

    def calculate(self, subtotal: float) -> float:
        # apply percent discount
        discount = subtotal * (self.percent / 100)
        return subtotal - discount


@dataclass(frozen=True)
class Product:
    sku: str
    name: str
    price: float


@dataclass
class CartItem:
    product: Product
    qty: int = 1

    def subtotal(self) -> float:
        # price * qty
        return self.product.price * self.qty


class ShoppingCart:
    def __init__(self, strategy: PricingStrategy):
        self._items: Dict[str, CartItem] = {}
        self.strategy = strategy

    def add(self, product: Product, qty: int = 1) -> None:
        # validate qty >= 1, add or increase quantity
        if qty < 1:
            raise ValueError("Quantity must be at least 1")

        if product.sku in self._items:
            self._items[product.sku].qty += qty
        else:
            self._items[product.sku] = CartItem(product, qty)

    def remove(self, sku: str) -> None:
        # remove item if exists else raise KeyError
        if sku not in self._items:
            raise KeyError(f"Product with SKU '{sku}' not found in cart")
        del self._items[sku]

    def subtotal(self) -> float:
        # sum of CartItem.subtotal()
        return sum(item.subtotal() for item in self._items.values())

    def total(self) -> float:
        # apply strategy.calculate(subtotal)
        return self.strategy.calculate(self.subtotal())


# ===== Example Usage =====
if __name__ == "__main__":
    # Create products
    p1 = Product("SKU1", "Laptop", 1000.0)
    p2 = Product("SKU2", "Mouse", 50.0)

    # Create cart with 10% discount
    cart = ShoppingCart(PercentageDiscount(10))

    cart.add(p1, 1)
    cart.add(p2, 2)

    print("Subtotal:", cart.subtotal())  # 1100.0
    print("Total after discount:", cart.total())  # 990.0

    cart.remove("SKU2")

    print("Subtotal after removal:", cart.subtotal())
    print("Final total:", cart.total())
