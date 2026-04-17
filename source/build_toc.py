import os
import argparse
import re
from pathlib import Path

def get_first_line(filepath):
    """Reads the first non-empty line of a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    return line
    except Exception as e:
        return f"Error reading file: {e}"
    return ""

def clean_header(header):
    """Removes Markdown header symbols and extra whitespace."""
    # Matches #, ##, ###, etc. followed by whitespace
    return re.sub(r'^#+\s*', '', header).strip()

def main():
    parser = argparse.ArgumentParser(description="Generate a Table of Contents for a specific tab of Markdown files.")
    parser.add_argument("tab", help="The tab prefix of the files (e.g., Experiences, Educations, About, Garage)")
    parser.add_argument("--dir", default=".", help="Directory to search (defaults to current directory)")
    parser.add_argument("--output", help="File to write the TOC to (optional)")
    args = parser.parse_args()

    source_path = Path(args.dir)
    if not source_path.exists():
        print(f"Error: Directory '{args.dir}' does not exist.")
        return

    # Find matching files starting with the tab prefix
    # Pattern: TabName_*.md
    pattern = f"{args.tab}_*.md"
    matching_files = list(source_path.glob(pattern))

    if not matching_files:
        print(f"No files found matching the pattern: {pattern}")
        print("Note: The script searches for files starting with '{args.tab}_'.")
        return

    # Sorting logic (Borrowing from build_site.py)
    # Filename format: Tab_Priority_Description.md
    def get_sort_key(file_path):
        parts = file_path.stem.split("_", 2)
        priority_val = parts[1] if len(parts) > 1 else "0"
        try:
            # Sort numerically if possible (e.g., 2026 > 2025)
            # We use zfill to ensure strings sort correctly if we mix types, 
            # but usually they are all years or sequences.
            return int(priority_val)
        except ValueError:
            return priority_val

    # Sort descending by priority (standard for the portfolio site)
    matching_files.sort(key=get_sort_key, reverse=True)

    #toc_lines = [f"## {args.tab}", ""]
    #toc_lines = [f"## {args.tab}s", ""]
    toc_lines = []
    
    for f in matching_files:
        first_line = get_first_line(f)
        # Use the header content as the title; fallback to filename if empty
        title = clean_header(first_line) if first_line else f.stem
        
        # Format as a Markdown list item
        toc_lines.append(f"- {title}")

    toc_content = "\n".join(toc_lines)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as out:
            out.write(toc_content)
        print(f"Success! TOC written to {args.output}")
    else:
        print(toc_content)

if __name__ == "__main__":
    main()
