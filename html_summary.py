from bs4 import BeautifulSoup, NavigableString, Tag, Comment
import re
from copy import deepcopy

retained_attributes = {
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

removed_elements = ["script", "style", "noscript", "svg", "img"]

def keep_retained_attributes(tag):
    if tag.attributes is None:
        return
    if "style" in tag.attributes:
        del tag.attributes["style"]
    keep = retained_attributes.get(tag.name, set())
    for attribute in list(tag.attributes):
        if attribute == "class":
            continue
        if attribute not in keep:
            del tag.attributes[attribute]


def remove_leading_whitespace(node):
    for text in node.find_all(string=True):
        if isinstance(text, NavigableString):
            if text.parent and text.parent.name == "pre":
                continue
            text.replace_with(" ".join(str(text).split()))

def minify_text_within_table_cell(node):
    for html_element in list(node.descendants):
        if not isinstance(html_element, Tag) or not html_element.name:
            continue
        name = html_element.name.lower()
        if name in removed_elements:
            html_element.decompose()
            continue
        if name in {"span", "div"}:
            html_element.unwrap()
            continue
        if name == "a":
            keep_retained_attributes(html_element)
            continue
        if name in {"strong", "b", "em", "i", "code"}:
            html_element.attributes = {}
            continue

def summarise_table(inTable):
    table = deepcopy(inTable)
    for element in table.find_all(removed_elements):
        element.decompose()

    for tag in table.find_all(True):
        keep_retained_attributes(tag)
        if tag.name in {"th", "td"}:
            minify_text_within_table_cell(tag)

    remove_leading_whitespace(table)
    return str(table)

def strip_full_html(inSoup):
    soup = deepcopy(inSoup)

    for html_element in soup(removed_elements):
        html_element.decompose()
    
    for tag in soup.find_all(True):
        if isinstance(tag, Comment):
            tag.extract()
        else:
            keep_retained_attributes(tag)

    remove_leading_whitespace(soup)
    return soup

def summarise_html(html_content, max_length = 15000):
    soup = BeautifulSoup(html_content, "html.parser")

    for html_element in soup(removed_elements):
        html_element.decompose()

    html_summary_array = []
    budget = max_length

    def add_to_summary(label, content, force = False):
        block = f"\n<!-- {label} -->\n{content}\n"
        if force or len(block) <= budget:
            html_summary_array.append(block)
            return len(block)
        return 0

    for form in soup.find_all("form"):
        budget -= add_to_summary("form", str(form))
    
    seen_buttons = set()
    for button in soup.find_all("button"):
        button_text = str(button).strip()
        if button_text and button_text not in seen_buttons:
            budget -= add_to_summary("button", button_text)
            seen_buttons.add(button_text)

    tables = soup.find_all("table")
    if tables:
        first_table = deepcopy(tables[0])
        first_table_html = summarise_table(first_table)
        budget -= add_to_summary("table", first_table_html, force=True)         
            
        for table in tables[1:]:
            table_html = summarise_table(table)
            budget -= add_to_summary("table", table_html)

    nav_elements = soup.find_all(["nav"])
    nav_elements += soup.find_all(["ul", "div"], class_=re.compile(r"(nav|menu)", re.I))
    seen_nav_elements = set()
    for nav_element in nav_elements:
        nav_element_text = str(nav_element).strip()
        if nav_element_text and nav_element_text not in seen_nav_elements:
            budget -= add_to_summary("nav", nav_element_text)
            seen_nav_elements.add(nav_element_text)

    for section_tag in ["header", "footer", "main", "article", "section", "aside"]:
        section = soup.find(section_tag)
        if section:
            links = []
            for a in section.find_all("a", href=True):
                if a.get_text(strip=True):
                    links.append(str(a))
            if links:
                budget -= add_to_summary(f"links in <{section_tag}>", "\n".join(links))

    if budget > 0:
        full_html_stripped = strip_full_html(soup)
        full_html_stripped_text = str(full_html_stripped).lstrip()
        if len(full_html_stripped_text) > budget:
            full_html_stripped_text = full_html_stripped_text[:budget]
        add_to_summary("remainder (cleaned HTML)", full_html_stripped_text, force=True)
    
    html_summary = "".join(html_summary_array).strip()

    return html_summary
