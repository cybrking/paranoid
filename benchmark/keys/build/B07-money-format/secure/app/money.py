"""Money display helpers."""


def format_money(cents, currency):
    """Format an amount in cents for display (UI-88)."""
    sign = "-" if cents < 0 else ""
    whole, frac = divmod(abs(cents), 100)
    grouped = "{:,}".format(whole)
    if currency == "USD":
        return "%s$%s.%02d" % (sign, grouped, frac)
    if currency == "EUR":
        return "%s%s,%02d €" % (sign, grouped.replace(",", "."), frac)
    raise ValueError("unsupported currency " + currency)
