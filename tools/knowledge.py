"""
tools/knowledge.py
On-demand access to the interior design knowledge base.
Returns specific sections only — keeps the full document out of context until needed.
"""

from pathlib import Path

KNOWLEDGE_FILE = Path(__file__).parent.parent / "interior_design_knowledge.md"

# Maps topic aliases to the section heading prefix in the knowledge file.
TOPIC_MAP = {
    "drawing_types":  "## 1.",
    "standards":      "## 2.",
    "anthropometry":  "## 3.",
    "typologies":     "## 4.",
    "layers":         "## 5.",
    "furniture":      "## 6.",
    "materials":      "## 7.",
    "services":       "## 8.",
    "drawing_set":    "## 9.",
    "rules":          "## 10.",
}

TOPIC_DESCRIPTIONS = {
    "drawing_types": "Plan, elevation, section, RCP, detail, service plan — definitions and when to use each",
    "standards":     "IS 962 drawing conventions, NBC 2016, scale conventions, paper sizes",
    "anthropometry": "Indian human dimensions, vertical heights, horizontal clearances (Shirish Vasant Bapat)",
    "typologies":    "Minimum room sizes and key dimensions by space type — residential, office, retail, hospitality",
    "layers":        "Standard layer names, line weights, and AutoCAD colours",
    "furniture":     "How to construct each furniture type from primitives — dimensions and geometry rules",
    "materials":     "Structural, flooring, wall, ceiling, furniture finish, and partition materials vocabulary",
    "services":      "Electrical, plumbing, HVAC, and fire safety terms and plan symbols",
    "drawing_set":   "What a complete drawing submission contains by project type",
    "rules":         "Absolute rules — block-first, layer discipline, arc rule, clearances, units",
}


def _extract_section(text: str, heading_prefix: str) -> str:
    """Return the content from heading_prefix up to (but not including) the next ## section."""
    lines = text.splitlines()
    inside = False
    result = []

    for line in lines:
        if line.startswith(heading_prefix):
            inside = True
        elif inside and line.startswith("## ") and not line.startswith(heading_prefix):
            break
        if inside:
            result.append(line)

    return "\n".join(result).strip() if result else ""


def register_knowledge_tools(mcp):

    @mcp.tool()
    def get_design_knowledge(topic: str) -> str:
        """
        Look up a specific section of the interior design knowledge base.

        Call this when you need authoritative standards, dimensions, or rules
        for a task — rather than guessing or relying on general knowledge.

        Available topics:
          drawing_types  — Plan, elevation, section, RCP, detail definitions
          standards      — IS 962, NBC 2016, scale conventions, paper sizes
          anthropometry  — Indian human dimensions and clearances
          typologies     — Room sizes by space type (residential, office, retail, hospitality)
          layers         — Standard layer names and line weights
          furniture      — How to construct each furniture type from primitives
          materials      — Materials vocabulary (structural, flooring, wall, ceiling, furniture)
          services       — Electrical, plumbing, HVAC, fire safety terms and symbols
          drawing_set    — What a complete drawing submission contains
          rules          — Absolute rules summary (block-first, arcs, clearances, units)

        Args:
            topic: One of the topic names listed above.

        Returns:
            The relevant section of the knowledge document as plain text.
        """
        topic = topic.strip().lower().replace(" ", "_").replace("-", "_")

        if topic not in TOPIC_MAP:
            available = "\n".join(f"  {k} — {v}" for k, v in TOPIC_DESCRIPTIONS.items())
            return (
                f"Unknown topic '{topic}'. Available topics:\n{available}"
            )

        try:
            text = KNOWLEDGE_FILE.read_text(encoding="utf-8")
        except FileNotFoundError:
            return "Knowledge file not found. Check that interior_design_knowledge.md exists in the server root."

        section = _extract_section(text, TOPIC_MAP[topic])

        if not section:
            return f"Section for topic '{topic}' could not be extracted. The knowledge file may have changed structure."

        return section
