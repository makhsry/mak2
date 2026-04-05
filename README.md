# Portfolio Site Generator

A Python-based static site generator that converts structured Markdown files into a professional, multi-page portfolio website with an alternating grid layout.

- **`source/`**: Contains all Markdown content, CSS, and the build script.
  - `build_site.py`: The Python generator script.
  - `main.css`: The primary styling file.

The python script `build_site.py` will parse all `.md` files, apply an **alternating A/B grid layout** (where content cards span 2 columns and empty cards span 1), and output the results to the same directory. 

The `markdown` library is used to parse the `.md` files.

To ensure content is correctly grouped and sorted, this naming pattern is followed for Markdown files in the `source/` directory:

`Tab_Priority_Title.md`

- **Tab**: The name of the navigation tab (e.g., `About`, `Educations`, `Experiences`).
- **Priority**: A number or date for sorting. High numbers appear at the top.
- **Title**: A descriptive name for the content card (can be anything).

**Examples:**
- `About_4_Professional_Summary.md`
- `Experiences_20250901_UBC_ModSim.md`