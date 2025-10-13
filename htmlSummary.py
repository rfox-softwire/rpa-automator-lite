from bs4 import BeautifulSoup, NavigableString, Tag, Comment
import re
from copy import deepcopy

# -----------------------------
# Helpers for HTML minimisation
# -----------------------------

# Attribute whitelist by tag (keep semantics; drop styling/noise). 'class' is always preserved; 'style' is always removed.
_ATTRS = {
    "table": {"role", "aria-label", "summary"},
    "caption": set(),
    "thead": set(),
    "tbody": set(),
    "tfoot": set(),
    "tr": {"role"},
    "th": {"scope", "colspan", "rowspan", "abbr", "headers"},
    "td": {"colspan", "rowspan", "headers"},
    "a": {"href", "title"},
}

def _strip_attrs(tag):
    # Always drop inline styles
    if "style" in tag.attrs:
        del tag.attrs["style"]
    keep = _ATTRS.get(tag.name, set())
    # Always preserve 'class' (semantic grouping), plus any whitelisted attrs
    for attr in list(tag.attrs):
        if attr == "class":
            continue
        if attr not in keep:
            del tag.attrs[attr]


def _collapse_whitespace(node: Tag):
    for text in node.find_all(string=True):
        if isinstance(text, NavigableString):
            if text.parent and text.parent.name == "pre":
                continue
            text.replace_with(" ".join(str(text).split()))

def _minify_within_cell(node):
    """
    Keep links (a[href]) and basic inline semantics (b/strong/em/code).
    Drop spans/divs/styles/scripts. Replace nested blocks with their text.
    """
    for el in list(node.descendants):
        if not isinstance(el, Tag) or not el.name:
            continue
        name = el.name.lower()
        if name in {"script", "style", "svg"}:
            el.decompose()
            continue
        if name in {"span", "div"}:
            el.unwrap()  # keep text but drop tag
            continue
        if name == "a":
            # Keep only href + text
            _strip_attrs(el)
            continue
        if name in {"strong", "b", "em", "i", "code"}:
            # keep tag but drop attributes
            el.attrs = {}
            continue
        if name == "img":
            # Keep only small/meaningful alt; replace big images with alt text
            alt = el.get("alt", "")
            if len(alt) <= 120:
                _strip_attrs(el)
            else:
                el.replace_with(alt)

def _table_visible_text(table):
    """Return TSV-like visible text for a table."""
    rows = []
    for tr in table.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        if not cells:
            continue
        vals = []
        for c in cells:
            t = " ".join(c.get_text(" ", strip=True).split())
            vals.append(t)
        rows.append("\t".join(vals))
    return "\n".join(rows)

def _minify_table_html(inTable):
    """
    Produce a compact, semantic-preserving HTML for a table:
      - keep caption/thead structure
      - strip non-semantic attributes
      - simplify cell contents (unwrap spans/divs, keep links and basic inline tags)
    """
    table = deepcopy(inTable)  # operate on a clone
    for el in table.find_all(["script", "style", "noscript", "svg"]):
        el.decompose()

    # Walk and strip attributes
    for tag in table.find_all(True):
        _strip_attrs(tag)
        if tag.name in {"th", "td"}:
            _minify_within_cell(tag)

    # Collapse whitespace in text nodes
    for text in table.find_all(string=True):
        if isinstance(text, NavigableString):
            # Keep whitespace in <pre> as-is
            if text.parent and text.parent.name == "pre":
                continue
            text.replace_with(" ".join(str(text).split()))

    return str(table)

def _clean_global_html(soup: BeautifulSoup) -> BeautifulSoup:
    """Return a deep-copied soup with superfluous content stripped but IDs/classes kept."""
    s2 = deepcopy(soup)

    # 1) drop noisy nodes globally
    for el in s2(["script", "style", "noscript", "svg"]):
        el.decompose()
    # remove HTML comments
    for c in s2.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()

    # 2) strip attributes according to policy
    for tag in s2.find_all(True):
        _strip_attrs(tag)

    # 3) shrink huge images: drop src (keep alt) to avoid data URLs
    for img in s2.find_all("img"):
        if "src" in img.attrs:
            del img.attrs["src"]

    # 4) collapse whitespace
    _collapse_whitespace(s2)

    return s2

# -----------------------------
# Main summariser
# -----------------------------

def summarise_html(html_content: str, max_length: int = 8000) -> str:
    """
    Summarise key interactive parts of an HTML page, preferring original HTML.
    Order: forms, buttons, tables, nav menus, links.

    Tables strategy to respect tight budgets while retaining HTML:
      1) Try MINIFIED HTML for the first table (not raw outerHTML).
      2) If still over budget, degrade to CAPTION+THEAD only (minified).
      3) If still over, degrade to TSV text (inside <pre>).
      4) For subsequent tables, include only TSV text (<pre>) to save space.

    Other sections keep original outerHTML (with budget checks).
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove global noise
    for el in soup(["script", "style", "noscript", "svg"]):
        el.decompose()

    parts: list[str] = []
    budget = max_length

    def add(label: str, content: str, force: bool = False) -> bool:
        nonlocal budget
        if not content:
            return True
        block = f"\n<!-- {label} -->\n{content}\n"
        if force or len(block) <= budget:
            parts.append(block)
            budget -= len(block)
            return True
        return False

    # -------- FORMS --------
    for form in soup.find_all("form"):
        if not add("form", str(form)):
            break

    # -------- BUTTONS (unique) --------
    seen_btn = set()
    for btn in soup.find_all("button"):
        h = str(btn).strip()
        if h and h not in seen_btn:
            if not add("button", h):
                break
            seen_btn.add(h)

    # -------- TABLES --------
    tables = soup.find_all("table")
    if tables:
        # First table: try a minified HTML version first
        t0 = deepcopy(tables[0])
        min_html = _minify_table_html(t0)
        if len(min_html) <= budget or budget == max_length:  # allow first block to lead
            if not add("table (minified HTML)", min_html, force=len(min_html) > budget):
                # shouldn't happen because of force, but keep safe
                pass
        else:
            # If even minified is too big, try caption+thead only
            t_head_only = deepcopy(t0)
            for node in t_head_only.find_all(True):
                if node.name not in {"table", "caption", "thead", "tr", "th"}:
                    node.decompose()
            head_min = _minify_table_html(t_head_only)
            if not add("table (caption+thead)", head_min):
                # Last resort: TSV
                tsv = _table_visible_text(t0)
                add("table (text only)", f"<pre>{tsv}</pre>", force=True)

        # Subsequent tables → TSV only
        for t in tables[1:]:
            tsv = _table_visible_text(t)
            if not add("table (text only)", f"<pre>{tsv}</pre>"):
                break

    # -------- NAV MENUS --------
    nav_candidates = soup.find_all(["nav"])
    nav_candidates += soup.find_all(["ul", "div"], class_=re.compile(r"(nav|menu)", re.I))
    seen_nav = set()
    for nav in nav_candidates:
        h = str(nav).strip()
        if h and h not in seen_nav:
            if not add("nav", h):
                break
            seen_nav.add(h)

    # -------- LINKS --------
    for section_tag in ["header", "footer", "main", "article", "section", "aside"]:
        section = soup.find(section_tag)
        if not section:
            continue
        links = []
        for a in section.find_all("a", href=True):
            if a.get_text(strip=True):
                links.append(str(a))
        if links:
            if not add(f"links in <{section_tag}>", "\n".join(links)):
                break

    if budget > 0:
        remainder = _clean_global_html(soup)

        # Avoid duplicating already-extracted blocks: remove forms/buttons/tables/nav from remainder
        for node in remainder.find_all(["form", "button", "table", "nav"]):
            node.decompose()
        # Optionally keep anchor tags but you've already added key links; so keep them in remainder
        # but they are now cleaned (attrs stripped per policy).

        remainder_html = str(remainder).lstrip()
        # Cap to the remaining budget exactly
        if len(remainder_html) > budget:
            remainder_html = remainder_html[:budget]
        add("remainder (cleaned HTML)", remainder_html, force=True)
    
    summary = "".join(parts).strip()
    if not summary:
        body = soup.find("body")
        summary = (str(body) if body else soup.get_text("\n")).strip()
        if len(summary) > max_length:
            summary = summary[:max_length]
    return summary
