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

def convert_md_to_html(content):
    # Pre-process content to treat multiple blank lines as literal empty lines
    content = re.sub(r'\n\s*\n', '\n\n&nbsp;\n\n', content)

    # Use a set of extensions that are robust for math
    # arithmatex is best if available, but we'll stick to 'extra' and rely on MathJax configuration
    # unless we want to try importing it.
    extensions = ['extra', 'tables', 'fenced_code', 'attr_list', 'nl2br']
    
    return markdown.markdown(content, extensions=extensions)

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
    <!-- MathJax for Equation Rendering -->
    <script>
    window.MathJax = {{
      tex: {{
        inlineMath: [['$', '$'], ['\\(', '\\)']],
        displayMath: [['$$', '$$'], ['\\[', '\\]']],
        processEscapes: true,
        processEnvironments: true
      }},
      options: {{
        skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre']
      }}
    }};
    </script>
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
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

        # Points to the same folder where the Markdown files and assets are
        body_html = convert_md_to_html(content)

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
    parser.add_argument("--output", default=None, help="Output directory (defaults to source)")
    args = parser.parse_args()

    source_path = Path(args.source)
    output_path = Path(args.output) if args.output else source_path

    md_files = get_md_files(args.source)
    tabs = {}
    for f in md_files:
        tabs.setdefault(f['tab'], []).append(f)

    all_tabs = list(tabs.keys())
    for tab_name, files in tabs.items():
        generate_tab_page(tab_name, files, args.source, output_path, all_tabs)

if __name__ == "__main__":
    main()
