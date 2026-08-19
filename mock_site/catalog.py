"""Static product catalog for the mock eBay site.

Deliberately static (no randomness) so runs are reproducible across environments/graders.
Prices and quantities were chosen to exercise specific robustness cases:
  - "shoes" has 15 items and a price ceiling of 220 that straddles the catalog, so
    searchItemsByNameUnderPrice must paginate ("Next") to collect 5 matches.
  - "watch" has only one item <= 50, so a limit=5 search must exhaust all pages and still
    correctly return a short (1-item) result instead of erroring.
  - Two shoe listings are price *ranges* ("$60.00 to $75.00"), the way eBay shows an item whose
    variants (e.g. size) are priced differently - see Item.price_for_selection below.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Item:
    id: str
    title: str
    category: str
    price_low: float
    price_high: float | None  # None => single fixed price, not a range
    variants: dict[str, list[str]] = field(default_factory=dict)

    @property
    def is_range(self) -> bool:
        return self.price_high is not None

    @property
    def price_text(self) -> str:
        if self.is_range:
            return f"${self.price_low:,.2f} to ${self.price_high:,.2f}"
        return f"${self.price_low:,.2f}"

    def price_for_selection(self, selections: dict[str, str]) -> float:
        """Resolves the concrete charged price for a chosen combination of variants.

        For ranged items, the first declared variant (e.g. "Size") linearly drives the price
        from price_low to price_high across its option list - mirroring how eBay listings with
        size-dependent pricing behave. Non-ranged items always charge price_low regardless of
        which variant values were picked.
        """
        if not self.is_range:
            return self.price_low
        price_variant = next(iter(self.variants))
        options = self.variants[price_variant]
        selected = selections.get(price_variant, options[0])
        idx = options.index(selected) if selected in options else 0
        if len(options) == 1:
            return self.price_low
        fraction = idx / (len(options) - 1)
        return round(self.price_low + fraction * (self.price_high - self.price_low), 2)


_SHOE_VARIANTS = {"Size": ["7", "8", "9", "10", "11"], "Color": ["Black", "White", "Red"]}
_HEADPHONE_VARIANTS = {"Color": ["Black", "White", "Blue"]}
_WATCH_VARIANTS = {"Band Color": ["Black", "Silver", "Brown"]}

CATALOG: list[Item] = [
    Item("shoe-1", "Nike Air Zoom Running Shoes", "shoes", 89.99, None, _SHOE_VARIANTS),
    Item("shoe-2", "Adidas Ultraboost Shoes", "shoes", 245.00, None, _SHOE_VARIANTS),
    Item("shoe-3", "Puma RS-X Sneaker Shoes", "shoes", 199.99, None, _SHOE_VARIANTS),
    Item("shoe-4", "New Balance 990 Shoes", "shoes", 310.50, None, _SHOE_VARIANTS),
    Item("shoe-5", "Reebok Classic Shoes", "shoes", 150.00, None, _SHOE_VARIANTS),
    Item("shoe-6", "Under Armour Trainer Shoes", "shoes", 275.99, None, _SHOE_VARIANTS),
    Item("shoe-7", "Vans Old Skool Shoes", "shoes", 60.00, 75.00, _SHOE_VARIANTS),
    Item("shoe-8", "Converse Chuck 70 Limited Shoes", "shoes", 500.00, None, _SHOE_VARIANTS),
    Item("shoe-9", "Asics Gel Kayano Shoes", "shoes", 210.00, None, _SHOE_VARIANTS),
    Item("shoe-10", "Balenciaga Triple S Designer Shoes", "shoes", 1199.00, None, _SHOE_VARIANTS),
    Item("shoe-11", "Skechers Go Walk Shoes", "shoes", 45.50, None, _SHOE_VARIANTS),
    Item("shoe-12", "Salomon Trail Shoes", "shoes", 320.00, None, _SHOE_VARIANTS),
    Item("shoe-13", "Brooks Ghost Running Shoes", "shoes", 199.00, 259.00, _SHOE_VARIANTS),
    Item("shoe-14", "Fila Disruptor Shoes", "shoes", 80.00, None, _SHOE_VARIANTS),
    Item("shoe-15", "Hoka Bondi Shoes", "shoes", 260.00, None, _SHOE_VARIANTS),
    Item("hp-1", "Sony WH Wireless Headphones", "headphones", 29.99, None, _HEADPHONE_VARIANTS),
    Item("hp-2", "Bose QuietComfort Headphones", "headphones", 199.99, None, _HEADPHONE_VARIANTS),
    Item("hp-3", "Sennheiser Studio Headphones", "headphones", 349.00, None, _HEADPHONE_VARIANTS),
    Item("hp-4", "JBL Tune Headphones", "headphones", 15.50, None, _HEADPHONE_VARIANTS),
    Item("hp-5", "Beats Solo Headphones", "headphones", 89.99, None, _HEADPHONE_VARIANTS),
    Item("hp-6", "Audio-Technica Pro Headphones", "headphones", 120.00, None, _HEADPHONE_VARIANTS),
    Item("hp-7", "AKG Reference Headphones", "headphones", 499.99, None, _HEADPHONE_VARIANTS),
    Item("hp-8", "Skullcandy Sport Headphones", "headphones", 59.99, None, _HEADPHONE_VARIANTS),
    Item("watch-1", "Casio Digital Watch", "watch", 60.00, None, _WATCH_VARIANTS),
    Item("watch-2", "Fossil Chronograph Watch", "watch", 75.00, None, _WATCH_VARIANTS),
    Item("watch-3", "Rolex Submariner Luxury Watch", "watch", 1299.99, None, _WATCH_VARIANTS),
    Item("watch-4", "Fitbit Sense Smart Watch", "watch", 90.00, None, _WATCH_VARIANTS),
    Item("watch-5", "Timex Classic Watch", "watch", 45.00, None, _WATCH_VARIANTS),
    Item("watch-6", "Garmin Fenix Sport Watch", "watch", 999.00, None, _WATCH_VARIANTS),
    Item("watch-7", "Casio Vintage Watch", "watch", 55.00, None, _WATCH_VARIANTS),
]

_BY_ID = {item.id: item for item in CATALOG}


def get_item(item_id: str) -> Item | None:
    return _BY_ID.get(item_id)


def search(query: str, price_low: float | None, price_high: float | None) -> list[Item]:
    q = (query or "").strip().lower()
    results = [item for item in CATALOG if q in item.title.lower()]
    if price_low is not None:
        results = [item for item in results if item.price_low >= price_low]
    if price_high is not None:
        results = [item for item in results if item.price_low <= price_high]
    return results
