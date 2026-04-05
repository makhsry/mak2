import os
import re
import argparse
import markdown
import shutil
from pathlib import Path

def get_md_files(source_dir):
    md_files = []
    source_path = Path(source_dir)
    if not source_path.exists():
        return []

    for file in source_path.glob("*.md"):
        if file.name.startswith("TEMPLATE"):
            continue
        parts = file.stem.split("_", 2)
        if len(parts) >= 1:
            tab = parts[0]
            priority_val = parts[1] if len(parts) > 1 else "0"
            try:
                priority = int(priority_val)
            except ValueError:
                priority = priority_val
            md_files.append({
                "tab": tab,
                "priority": priority,
                "filename": file.name,
                "filepath": file,
                "basename": file.stem
            })
    return md_files

def convert_md_to_html(content, images_rel_path):
    # Fix both image and regular links: find any ](url) where url is local 
    # and prefix it with the assets path.
    def fix_path(match):
        url = match.group(1)
        if not url.startswith(("http://", "https://", "/", "mailto:", "#")):
            return f']({images_rel_path}/{url})'
        return match.group(0)

    content = re.sub(r'\]\((.*?)\)', fix_path, content)
    
    # Pre-process content to treat multiple blank lines as literal empty lines
    content = re.sub(r'\n\s*\n', '\n\n&nbsp;\n\n', content)

    return markdown.markdown(content, extensions=['extra', 'tables', 'fenced_code', 'attr_list', 'nl2br'])

    return markdown.markdown(content, extensions=['extra', 'tables', 'fenced_code', 'attr_list', 'nl2br'])

def generate_tab_page(tab_name, files, source_dir, output_dir, all_tabs):
    def sort_key(x):
        p = x['priority']
        if isinstance(p, int):
            return str(p).zfill(20)
        return str(p)

    files.sort(key=sort_key, reverse=True)

    # Use local CSS path for the generated HTML
    css_filename = "main.css"

    # Create Navigation Links
    nav_links = ""
    # Create Navigation Links
    nav_links = ""
    for t in sorted(all_tabs):
        is_active = (t == tab_name)
        active_class = ' class="active"' if is_active else ""
        # Link to index.html if it's the 'About' tab, otherwise lowercase filename
        target_filename = "index.html" if t.lower() == "about" else f"{t.lower()}.html"
        nav_links += f'            <a href="{target_filename}"{active_class}>{t}</a>\n'

    # HTML Template
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{tab_name}</title>
    <link rel="stylesheet" href="{css_filename}">
</head>
<body>
    <nav>
        <div class="nav-container">
{nav_links}
        </div>
    </nav>
    <div class="container">
"""

    for i, file_info in enumerate(files):
        with open(file_info['filepath'], 'r', encoding='utf-8') as f:
            content = f.read()

        # Points to the 'assets' folder in the final view directory
        body_html = convert_md_to_html(content, "assets")

        # Alternating A/B Grid Layout
        if i % 2 == 0:
            html_content += f"""
        <section class="card span-2">
            <div class="card-content">{body_html}</div>
        </section>
        <section class="card span-1 empty"></section>
"""
        else:
            html_content += f"""
        <section class="card span-1 empty"></section>
        <section class="card span-2">
            <div class="card-content">{body_html}</div>
        </section>
"""

    html_content += """
    </div>
</body>
</html>
"""

    # Rename 'About' output to index.html for GitHub Pages entry point
    actual_name = "index" if tab_name.lower() == "about" else tab_name.lower()
    output_path = Path(output_dir) / f"{actual_name}.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Generated {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Portfolio Site Generator - Alternating Layout")
    parser.add_argument("--source", default=".", help="Source directory")
    parser.add_argument("--output", default="../view", help="Output directory")
    args = parser.parse_args()

    source_path = Path(args.source)
    output_path = Path(args.output)
    if output_path.exists():
        shutil.rmtree(output_path)
        print(f"Cleaned output directory: {output_path}")
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. Copy main.css to output directory
    css_source = source_path / "main.css"
    if css_source.exists():
        shutil.copy(css_source, output_path / "main.css")
        print(f"Copied {css_source} to {output_path}/main.css")

    # 2. Copy images/assets to view/assets
    assets_output = output_path / "assets"
    assets_output.mkdir(exist_ok=True)
    
    # Copy images and other assets to view/assets
    asset_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ipynb', '.pdf', '.zip', '.xlsx', '.csv', '.docx', '.pptx')
    for asset_file in source_path.iterdir():
        if asset_file.suffix.lower() in asset_extensions:
            shutil.copy(asset_file, assets_output / asset_file.name)
            print(f"Copied asset: {asset_file.name}")

    md_files = get_md_files(args.source)
    tabs = {}
    for f in md_files:
        tabs.setdefault(f['tab'], []).append(f)

    all_tabs = list(tabs.keys())
    for tab_name, files in tabs.items():
        generate_tab_page(tab_name, files, args.source, args.output, all_tabs)

if __name__ == "__main__":
    main()
