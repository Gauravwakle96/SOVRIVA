"""Render the pitch's lightweight PPT-style visual cards as SVG files.

The cards are deliberately dependency-free so the pitch can be rebuilt on Windows
without a slide-rendering package. Product footage remains the source of truth for
working features; these cards summarize the story for judges.
"""

from pathlib import Path


OUT = Path(__file__).with_name("innovatex_cards")
W, H = 1920, 1080
NAVY, NAVY2, WHITE, MUTED = "#06142e", "#102a56", "#f3f7ff", "#9fb1d2"
BLUE, VIOLET, GREEN, ORANGE, RED = "#5f8dff", "#9b7cff", "#31c38d", "#ffb65c", "#ef6d78"


def esc(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def t(x: int, y: int, value: str, size: int = 30, color: str = WHITE, weight: int = 400, anchor: str = "start") -> str:
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial,Segoe UI,sans-serif" font-size="{size}px" font-weight="{weight}" text-anchor="{anchor}">{esc(value)}</text>'


def lines(x: int, y: int, values: list[str], size: int = 28, color: str = WHITE, weight: int = 400, gap: int = 42) -> str:
    return "".join(t(x, y + index * gap, value, size, color, weight) for index, value in enumerate(values))


def shell(kicker: str, title: str, subtitle: str) -> str:
    title_lines = title.split("\n")
    title_size = 58 if len(title_lines) > 1 else 55
    title_svg = lines(105, 335, title_lines, title_size, WHITE, 800, 66)
    subtitle_y = 430 if len(title_lines) > 1 else 405
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<rect width="100%" height="100%" fill="{NAVY}"/>
<circle cx="1770" cy="85" r="300" fill="#102958" opacity=".72"/><circle cx="1850" cy="120" r="210" fill="#244787" opacity=".24"/>
<g transform="translate(100 70) skewX(-18)"><rect width="12" height="55" rx="6" fill="{BLUE}"/><rect x="24" y="-17" width="12" height="72" rx="6" fill="{VIOLET}"/><rect x="48" y="-42" width="12" height="97" rx="6" fill="{BLUE}"/></g>
{t(190, 95, "SOVRIVA", 27, WHITE, 800)}{t(190, 126, "NEXUS INNOVATEX 2026  •  IDEA PITCH", 13, MUTED, 700)}
{t(105, 255, kicker.upper(), 21, BLUE, 800)}{title_svg}{t(105, subtitle_y, subtitle, 27, MUTED, 400)}
'''


def card(title: str, x: int, y: int, width: int, height: int, accent: str, body: str, detail: str = "") -> str:
    return f'''<g transform="translate({x} {y})"><rect width="{width}" height="{height}" rx="18" fill="{NAVY2}" stroke="{accent}" stroke-opacity=".75"/>
{t(28, 50, title.upper(), 18, accent, 800)}{t(28, 94, body, 25, WHITE, 700)}{t(28, 140, detail, 19, MUTED, 400)}</g>'''


def finish() -> str:
    return "</svg>"


def write(name: str, body: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.svg").write_text(body, encoding="utf-8")


write("01_problem", shell("01 / THE PROBLEM", "People can download data.\nUnderstanding is the hard part.", "The gap is not access. It is making exported evidence understandable, comparable and verifiable.") +
      card("Fragmented exports", 105, 570, 500, 220, ORANGE, "Different folders", "Labels and file structures vary across platforms.") +
      card("No trustworthy history", 710, 570, 500, 220, VIOLET, "Missing ≠ deleted", "A later export may have incomplete coverage.") +
      card("Disconnected tools", 1315, 570, 500, 220, RED, "Blockers or viewers", "Users still need one evidence-led workflow.") + finish())

write("02_solution", shell("02 / PROPOSED SOLUTION", "One local workflow:\nimport → understand → verify.", "SOVRIVA turns supported Google and Meta exports into a traceable local history.") +
      "<g transform=\"translate(105 575)\">" +
      card("01  IMPORT", 0, 0, 295, 210, BLUE, "Google / Meta ZIP", "User-authorized data") +
      card("02  VALIDATE", 330, 0, 295, 210, VIOLET, "Safety + SHA-256", "Path checks, duplicates") +
      card("03  UNDERSTAND", 660, 0, 295, 210, GREEN, "Normalize + classify", "Original labels preserved") +
      card("04  COMPARE", 990, 0, 295, 210, ORANGE, "Drift + matching", "Uncertainty stays visible") +
      card("05  VERIFY", 1320, 0, 295, 210, BLUE, "Action + evidence", "Observable outcome only") + "</g>" +
      t(105, 885, "LOCAL-FIRST BY DESIGN", 18, GREEN, 800) + t(410, 885, "Loopback FastAPI  •  SQLite  •  Chrome / Edge MV3 companion", 23, WHITE, 600) + finish())

write("03_profile_drift", shell("03 / INNOVATION ONE", "Profile Drift\nIntelligence.", "A missing record is not automatically a deletion. Coverage controls the conclusion.") +
      card("Example", 105, 575, 440, 225, BLUE, "Technology • Fitness • Travel", "Before snapshot") +
      t(590, 685, "→", 55, MUTED, 700, "middle") +
      card("Later export", 660, 575, 440, 225, VIOLET, "Technology • Travel", "Fitness is absent") +
      t(1160, 635, "OUTCOMES", 18, BLUE, 800) +
      lines(1160, 690, ["ADDED", "RETAINED", "SUPPORTED REMOVED", "UNCERTAIN ABSENCE"], 25, WHITE, 700, 48) +
      lines(1470, 690, ["Newly reported", "Still reported", "Explicit coverage", "Insufficient coverage"], 18, MUTED, 400, 48) + finish())

write("04_provenance", shell("04 / INNOVATION TWO", "Evidence\nProvenance.", "Every conclusion keeps a source-level trail that a user or judge can inspect.") +
      card("FINDING", 105, 600, 330, 190, GREEN, "Sports", "Trail running") +
      t(485, 700, "→", 45, BLUE, 700, "middle") + card("SOURCE FILE", 540, 600, 355, 190, BLUE, "Meta export ZIP", "Original filename preserved") +
      t(945, 700, "→", 45, BLUE, 700, "middle") + card("RECORD PATH", 1000, 600, 355, 190, VIOLET, "interests[2]", "Original record remains available") +
      t(1405, 700, "→", 45, BLUE, 700, "middle") + card("METHOD", 1460, 600, 355, 190, ORANGE, "taxonomy v0.1", "Explainable classification") + finish())

write("05_action", shell("05 / INNOVATION THREE", "Privacy Action\nVerification.", "Record an action. Import a later snapshot. Report only what the evidence supports.") +
      t(155, 625, "01", 24, BLUE, 800) + t(155, 670, "RECORD ACTION", 18, WHITE, 800) + t(155, 710, "User describes the privacy change", 19, MUTED) +
      t(720, 625, "02", 24, VIOLET, 800) + t(720, 670, "IMPORT LATER EXPORT", 18, WHITE, 800) + t(720, 710, "Coverage is inspected locally", 19, MUTED) +
      t(1285, 625, "03", 24, GREEN, 800) + t(1285, 670, "COMPARE EVIDENCE", 18, WHITE, 800) + t(1285, 710, "Observable outcome is reported", 19, MUTED) +
      card("OBSERVED CHANGE", 105, 805, 500, 130, GREEN, "Later export changed", "Supported by explicit coverage") +
      card("NO CHANGE OBSERVED", 710, 805, 500, 130, BLUE, "Label remains", "Same normalized record") +
      card("NOT VERIFIABLE", 1315, 805, 500, 130, ORANGE, "Evidence is incomplete", "No deletion claim") + finish())

write("06_browser", shell("06 / BROWSER COMPANION", "Privacy protection\nalongside identity intelligence.", "A Chrome / Edge Manifest V3 extension adds metadata observation and supported rules.") +
      card("INTEREST", 105, 600, 500, 190, BLUE, "Ads off", "Tracker setting remains independent") +
      card("BALANCED", 710, 600, 500, 190, VIOLET, "Default mode", "Supported ad + tracker rules") +
      card("PRIVACY", 1315, 600, 500, 190, GREEN, "Expanded corpus", "Documented privacy mode") +
      t(105, 885, "OBSERVE  →  CLASSIFY  →  APPLY MV3 DNR  →  MEASURE", 22, WHITE, 700) +
      t(105, 925, "Configured rule count ≠ verified blocked-request count. Controlled tests establish the difference.", 18, ORANGE, 500) + finish())

write("07_technology", shell("07 / TECHNOLOGY + AI", "Explainable foundations\nnow. Measured AI next.", "The current intelligence baseline is deterministic and inspectable—not presented as unsupported machine learning.") +
      card("FASTAPI", 105, 600, 380, 205, BLUE, "Loopback service", "Local API + dashboard") +
      card("SQLITE", 540, 600, 380, 205, VIOLET, "Evidence store", "Source paths + rationale") +
      card("MANIFEST V3", 975, 600, 380, 205, GREEN, "Browser companion", "Metadata + supported rules") +
      card("AI ROADMAP", 1410, 600, 405, 205, ORANGE, "Planned, not shipped", "Labelled evaluation • precision • recall • macro-F1") + finish())

write("08_market", shell("08 / MARKET + FUTURE", "Built for clarity—not\nmore privacy alerts.", "Start with focused users who need evidence-linked analysis and local processing.") +
      card("TARGET USERS", 105, 600, 500, 205, BLUE, "Individuals", "Students • educators • researchers") +
      card("PROPOSED MODEL", 710, 600, 500, 205, VIOLET, "Free local core", "Premium reports • institutional solutions") +
      card("ROADMAP", 1315, 600, 500, 205, GREEN, "Scale responsibly", "More platforms • advanced intelligence • local AI") +
      t(105, 900, "No revenue or pilot outcome is claimed yet. Validate demand, comprehension, trust and task completion next.", 18, MUTED, 500) + finish())

write("09_close", shell("THE PROMISE", "Understand the profile.\nTrace the evidence. Verify the change.", "SOVRIVA is not a claim to know everything about a user. It is a practical path to accessible evidence.") +
      "<rect x=\"105\" y=\"615\" width=\"1710\" height=\"165\" rx=\"24\" fill=\"#123d3c\" stroke=\"" + GREEN + "\"/>" +
      t(960, 685, "LOCAL-FIRST", 20, GREEN, 800, "middle") + t(960, 730, "EVIDENCE-LED  •  USER-CONTROLLED", 25, WHITE, 700, "middle") +
      t(960, 742, "SOVRIVA", 48, WHITE, 800, "middle") + t(960, 775, "Your Digital Identity. Your Control.", 23, GREEN, 700, "middle") + finish())

print(f"Rendered {len(list(OUT.glob('*.svg')))} cards to {OUT}")
