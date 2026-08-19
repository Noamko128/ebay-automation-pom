"""A tiny Flask app that mimics just enough of eBay's UI/URLs to drive real Playwright
interactions: search with a price filter, paginated results, an item page with variant
selects, and a session-backed cart with a subtotal.

This exists because real ebay.com returns HTTP 403 to non-interactive and much automated
browser traffic (bot/CAPTCHA protection - confirmed while building this project) which would
make the suite flaky/unrunnable in CI. Running against this mock keeps the *automation code*
(POM classes, locator strategy, price parsing, pagination handling) realistic and testable
without depending on a third-party site's availability or anti-bot heuristics. Swapping to the
real site is a one-line config change (TEST_ENV=live) - see README "Limitations".
"""
from __future__ import annotations

from flask import Flask, redirect, render_template, request, session, url_for

from mock_site.catalog import get_item, search

app = Flask(__name__)
app.secret_key = "mock-ebay-dev-only-secret"  # local test double only, never a real secret

PAGE_SIZE = 3


def _parse_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


@app.context_processor
def inject_cart_count():
    return {"cart_count": len(session.get("cart", []))}


@app.route("/")
def home():
    return render_template("home.html", guest=session.get("guest", False))


@app.post("/guest")
def continue_as_guest():
    session["guest"] = True
    return redirect(url_for("home"))


@app.route("/sch/i.html")
def search_results():
    query = request.args.get("_nkw", "")
    price_low = _parse_float(request.args.get("_udlo"))
    price_high = _parse_float(request.args.get("_udhi"))
    page = max(1, int(request.args.get("_pgn", 1) or 1))

    matches = search(query, price_low, price_high)
    start = (page - 1) * PAGE_SIZE
    page_items = matches[start : start + PAGE_SIZE]
    has_next = start + PAGE_SIZE < len(matches)

    return render_template(
        "search.html",
        query=query,
        items=page_items,
        page=page,
        has_next=has_next,
        price_low=request.args.get("_udlo", ""),
        price_high=request.args.get("_udhi", ""),
    )


@app.route("/itm/<item_id>")
def item_detail(item_id: str):
    item = get_item(item_id)
    if item is None:
        return "Item not found", 404
    added = request.args.get("added") == "1"
    return render_template("item.html", item=item, added=added)


@app.post("/itm/<item_id>/cart")
def add_to_cart(item_id: str):
    item = get_item(item_id)
    if item is None:
        return "Item not found", 404

    selections = {variant: request.form.get(variant, options[0]) for variant, options in item.variants.items()}
    price = item.price_for_selection(selections)

    cart = session.get("cart", [])
    cart.append({"id": item.id, "title": item.title, "price": price, "selections": selections})
    session["cart"] = cart

    return redirect(url_for("item_detail", item_id=item_id, added=1))


@app.route("/cart")
def cart_view():
    cart = session.get("cart", [])
    subtotal = round(sum(line["price"] for line in cart), 2)
    return render_template("cart.html", cart=cart, subtotal=subtotal)


if __name__ == "__main__":
    app.run(port=5057)
