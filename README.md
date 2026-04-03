# Portfolio Site Generator

A Python-based static site generator that converts structured Markdown files into a professional, multi-page portfolio website with an alternating grid layout.

## 📁 Folder Structure

- **`source/`**: Contains all Markdown content, CSS, and the build script.
  - `build_site.py`: The Python generator script.
  - `main.css`: The primary styling file.
- **`view/`**: The auto-generated output directory where the final HTML pages are stored.

## 🛠️ Filename Convention

To ensure content is correctly grouped and sorted, this naming pattern is followed for Markdown files in the `source/` directory:

`Tab_Priority_Title.md`

- **Tab**: The name of the navigation tab (e.g., `About`, `Educations`, `Experiences`).
- **Priority**: A number or date for sorting. High numbers appear at the top.
- **Title**: A descriptive name for the content card (can be anything).

**Examples:**
- `About_4_Professional_Summary.md`
- `Experiences_20250901_UBC_ModSim.md`

## 🏗️ Building the Site

To generate portfolio, the following steps are performed in by GitHub Actions:

   ```bash
   cd source
   python3 build_site.py
   ```

The script will automatically parse all `.md` files, apply an **alternating A/B grid layout** (where content cards span 2 columns and empty cards span 1), and output the results to the `view/` directory.

## 🍱 Styling Used

- **Alternating Layout**: Content sections alternate between a "Content-Left / Empty-Right" and "Empty-Left / Content-Right" 3-column grid for a dynamic, magazine-style feel.
- **Fully Responsive**: Adapts to mobile devices automatically.
- **Smart Formatting**: 
  - Preserves literal line breaks and empty lines.
  - Automatically highlights the active tab in the navigation menu.
  - Centers the main navigation bar.

## 📦 Dependencies

```bash
markdown
```
