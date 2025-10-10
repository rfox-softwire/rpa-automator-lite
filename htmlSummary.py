from bs4 import BeautifulSoup
import re

def summarise_html(html_content, max_length=3000):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script, style, and other non-essential elements
    for element in soup(["script", "style", "noscript", "svg", "img", "meta", "link"]):
        element.decompose()
    
    # Find all interactive elements
    interactive_elements = {
        'forms': [],
        'buttons': [],
        'inputs': [],
        'tables': [],
        'nav_menus': [],
        'important_links': []
    }
    
    # Extract forms and their inputs
    for form in soup.find_all('form'):
        form_data = {
            'id': form.get('id', ''),
            'class': form.get('class', []),
            'action': form.get('action', ''),
            'method': form.get('method', ''),
            'inputs': []
        }
        for inp in form.find_all(['input', 'select', 'textarea', 'button']):
            form_data['inputs'].append({
                'tag': inp.name,
                'type': inp.get('type', ''),
                'name': inp.get('name', ''),
                'id': inp.get('id', ''),
                'class': inp.get('class', []),
                'placeholder': inp.get('placeholder', '')
            })
        interactive_elements['forms'].append(form_data)
    
    # Find all buttons (including those not in forms)
    for btn in soup.find_all('button'):
        interactive_elements['buttons'].append({
            'text': btn.get_text(strip=True),
            'id': btn.get('id', ''),
            'class': btn.get('class', []),
            'type': btn.get('type', '')
        })
    
    # Find all input elements not in forms
    for inp in soup.find_all('input'):
        if not inp.find_parent('form'):
            interactive_elements['inputs'].append({
                'tag': 'input',
                'type': inp.get('type', ''),
                'name': inp.get('name', ''),
                'id': inp.get('id', ''),
                'class': inp.get('class', []),
                'placeholder': inp.get('placeholder', '')
            })
    
    # Extract tables and their structure
    for table in soup.find_all('table'):
        table_data = {
            'id': table.get('id', ''),
            'class': table.get('class', []),
            'headers': [],
            'rows': []
        }
        
        # Get headers (th elements)
        headers = table.find_all('th')
        if headers:
            table_data['headers'] = [h.get_text(strip=True) for h in headers]
        else:
            # If no th elements, use first row of td elements as headers
            first_row = table.find('tr')
            if first_row:
                table_data['headers'] = [cell.get_text(strip=True) for cell in first_row.find_all(['td', 'th'])]
        
        # Get table rows
        rows = table.find_all('tr')
        for row in rows:
            # Skip header row if it was used for headers
            if row.find('th') and not table_data['headers']:
                continue
                
            cells = row.find_all('td')
            if cells:  # Only add rows with data cells
                row_data = {
                    'cells': [cell.get_text(strip=True) for cell in cells],
                    'rowspan': [int(cell.get('rowspan', 1)) for cell in cells],
                    'colspan': [int(cell.get('colspan', 1)) for cell in cells]
                }
                table_data['rows'].append(row_data)
        
        if table_data['headers'] or table_data['rows']:
            interactive_elements['tables'].append(table_data)

    # Find navigation menus (common nav patterns)
    for nav in soup.find_all(['nav', 'ul', 'div'], class_=re.compile(r'nav|menu', re.I)):
        links = []
        for a in nav.find_all('a', href=True):
            links.append({
                'text': a.get_text(strip=True),
                'href': a['href'],
                'class': a.get('class', [])
            })
        if links:
            interactive_elements['nav_menus'].append({
                'element': nav.name,
                'class': nav.get('class', []),
                'id': nav.get('id', ''),
                'links': links
            })
    
    # Find other important links (header, footer, etc.)
    for section in ['header', 'footer', 'main', 'article', 'section', 'aside']:
        section_el = soup.find(section)
        if section_el:
            links = []
            for a in section_el.find_all('a', href=True):
                if a.get_text(strip=True):
                    links.append({
                        'text': a.get_text(strip=True),
                        'href': a['href'],
                        'class': a.get('class', [])
                    })
            if links:
                interactive_elements['important_links'].append({
                    'section': section,
                    'links': links
                })
    
    # Convert to a structured text representation
    summary = f"# Page Structure Summary\n\n"
    
    if interactive_elements['forms']:
        summary += "## Forms\n"
        for i, form in enumerate(interactive_elements['forms'], 1):
            summary += f"\n### Form {i}\n"
            if form['id']:
                summary += f"- ID: {form['id']}\n"
            if form['action']:
                summary += f"- Action: {form['action']}\n"
            if form['inputs']:
                summary += "  Inputs:\n"
                for inp in form['inputs']:
                    summary += f"  - {inp['tag']}"
                    if inp['type']:
                        summary += f" (type: {inp['type']})"
                    if inp['name']:
                        summary += f" [name: {inp['name']}]"
                    if inp['id']:
                        summary += f" [id: {inp['id']}]"
                    summary += "\n"
    
    if interactive_elements['buttons']:
        summary += "\n## Buttons\n"
        for btn in interactive_elements['buttons']:
            if btn['text']:  # Only include buttons with visible text
                summary += f"- {btn['text']}"
                if btn['id']:
                    summary += f" [id: {btn['id']}]"
                summary += "\n"
    
    if interactive_elements['tables']:
        summary += "\n## Tables\n"
        for i, table in enumerate(interactive_elements['tables'], 1):
            summary += f"\n### Table {i}\n"
            if table['id']:
                summary += f"- ID: {table['id']}\n"
            
            if table['headers']:
                summary += "  Headers: " + " | ".join(table['headers']) + "\n"
            
            if table['rows']:
                summary += "  Rows:\n"
                for row in table['rows'][:10]:  # Limit to first 10 rows to save space
                    summary += "  - " + " | ".join(cell for cell in row['cells']) + "\n"
                if len(table['rows']) > 10:
                    summary += f"  - ... and {len(table['rows']) - 10} more rows\n"
    
    if interactive_elements['nav_menus']:
        summary += "\n## Navigation Menus\n"
        for i, menu in enumerate(interactive_elements['nav_menus'], 1):
            summary += f"\n### Menu {i}\n"
            for link in menu['links']:
                summary += f"- {link['text']} -> {link['href']}\n"
    
    if interactive_elements['important_links']:
        summary += "\n## Important Links by Section\n"
        for section in interactive_elements['important_links']:
            summary += f"\n### {section['section'].title()}\n"
            for link in section['links']:
                summary += f"- {link['text']} -> {link['href']}\n"
    
    # Ensure we don't exceed the maximum length
    if len(summary) > max_length:
        summary = summary[:max_length] + "\n\n[...content truncated due to length...]"
    
    return summary