import os
import re
from pathlib import Path

def slugify(text):
    """Convert text to a URL-friendly slug."""
    # Remove HTML tags if any (unlikely for TOC text but safe)
    text = re.sub(r'<[^>]*>', '', text)
    # Convert to lowercase and replace non-alphanumeric characters with hyphens
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', text).strip('-').lower()
    return slug

def process_html_file(filepath):
    """Post-process HTML to link list items to headings."""
    print(f"Processing {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    # Find the first <ul> which is our TOC
    toc_match = re.search(r'<ul>(.*?)</ul>', html, re.DOTALL)
    if not toc_match:
        return

    toc_content = toc_match.group(1)
    
    # Extract all list items
    li_items = re.findall(r'<li>(.*?)</li>', toc_content)
    if not li_items:
        return

    # To avoid double linking or messing up existing links, we check if they already have <a>
    updated_html = html
    links_added = 0

    for item_text in li_items:
        # Skip if already linked
        if '<a ' in item_text:
            continue
            
        # Clean text for matching (remove tags for comparison)
        clean_item_text = re.sub(r'<[^>]*>', '', item_text).strip()
        slug = slugify(clean_item_text)
        
        # Find all h2 and h3 headers
        # We search for the whole tag to avoid matching text outside headings
        headers = re.finditer(r'(<(h[23])[^>]*>)(.*?)(</\2>)', updated_html, re.DOTALL)
        matching_header = None
        
        for match in headers:
            full_tag = match.group(0)
            opening_tag = match.group(1)
            header_content = match.group(3)
            tag_name = match.group(2)
            
            # Clean header content for comparison
            clean_header_content = re.sub(r'<[^>]*>', '', header_content).strip()
            
            if clean_header_content == clean_item_text:
                matching_header = {
                    'full': full_tag,
                    'opening': opening_tag,
                    'content': header_content,
                    'tag': tag_name
                }
                break # Take the first match
        
        if matching_header:
            # If header doesn't have an ID, add it
            if 'id="' not in matching_header['opening']:
                new_opening = matching_header['opening'].replace('>', f' id="{slug}">')
                new_full_header = new_opening + matching_header['content'] + f'</{matching_header["tag"]}>'
                updated_html = updated_html.replace(matching_header['full'], new_full_header)
            else:
                # Extract existing ID
                id_match = re.search(r'id="([^"]+)"', matching_header['opening'])
                if id_match:
                    slug = id_match.group(1)

            # Update the list item in TOC
            # We must be careful to only replace the first occurrence of this item in the TOC
            old_li = f'<li>{item_text}</li>'
            new_li = f'<li><a href="#{slug}">{item_text}</a></li>'
            updated_html = updated_html.replace(old_li, new_li, 1)
            links_added += 1

    if links_added > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(updated_html)
        print(f"Added {links_added} links to {filepath}")
    else:
        print(f"No new links added to {filepath}")

def main():
    # Process all html files in the current directory (which should be 'source')
    html_files = list(Path('.').glob('*.html'))
    for f in html_files:
        # Skip index.html if you want, but it might have TOC too
        process_html_file(f)

if __name__ == "__main__":
    main()
