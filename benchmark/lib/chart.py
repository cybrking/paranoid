"""A small grouped bar chart as standalone SVG, no dependencies."""

from html import escape

COLORS = ("#9aa0a6", "#111111")


def bar_chart(metrics, series_labels, width=760):
    """metrics: [(label, [value or None per series])], values are percentages."""
    row_height, bar_height, left, right = 46, 14, 270, 70
    height = 60 + row_height * len(metrics)
    plot = width - left - right
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
        'font-family="-apple-system, Segoe UI, Helvetica, Arial, sans-serif" font-size="13">' % (width, height, width, height),
        '<rect width="100%" height="100%" fill="#ffffff"/>',
    ]
    for i, label in enumerate(series_labels):
        x = left + i * 180
        out.append('<rect x="%d" y="14" width="12" height="12" fill="%s"/>' % (x, COLORS[i % len(COLORS)]))
        out.append('<text x="%d" y="25" fill="#111">%s</text>' % (x + 18, escape(label)))
    for row, (label, values) in enumerate(metrics):
        y = 50 + row * row_height
        out.append('<text x="%d" y="%d" text-anchor="end" fill="#111">%s</text>' % (left - 12, y + bar_height + 4, escape(label)))
        for i, value in enumerate(values):
            by = y + i * (bar_height + 2)
            if value is None:
                out.append('<text x="%d" y="%d" fill="#666">n/a</text>' % (left + 4, by + 11))
                continue
            w = max(1, plot * max(0.0, min(100.0, value)) / 100.0)
            out.append('<rect x="%d" y="%d" width="%.1f" height="%d" fill="%s"/>' % (left, by, w, bar_height, COLORS[i % len(COLORS)]))
            out.append('<text x="%.1f" y="%d" fill="#111">%s%%</text>' % (left + w + 6, by + 11, ("%g" % value)))
    out.append("</svg>")
    return "\n".join(out) + "\n"
