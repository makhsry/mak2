**Portfolio Site Generator**

A Python-based static site generator that converts **Markdown files** into a professional, multi-page portfolio website with an **alternating grid layout**.

- **`mdfiles/`**: Contains all **Markdown content**, **CSS**, and the **build script**.
- **`images/`**: Contains all **images** used in the Markdown files.
- **`build_site.py`**: Generate the **HTML files** from the Markdown files.
- **`build_toc.py`**: Generate the **table of contents** for each HTML file.
- **`build_linkheaders.py`**: Generate the **internal links of contents** for the HTML files.
- **`main.css`**: The **primary styling file**.

The python script **`build_site.py`** will parse all **`.md`** files, apply an **alternating A/B grid layout** (where content cards span 2 columns and empty cards span 1), and output the results to the same directory. 

The **`markdown`** library is used to parse the **`.md`** files.

To ensure content is correctly grouped and sorted, this naming pattern is followed for Markdown files in the **`mdfiles/`** directory:

`Tab_Priority_Title.md`

- **Tab**: The name of the **navigation tab** (e.g., `About`, `Educations`, `Experiences`).
- **Priority**: A **number** or **date** for sorting. **High numbers appear at the top**.
- **Title**: A **descriptive name** for the **content card** (can be anything).

**Examples:**
- `About_4_Professional_Summary.md`
- `Experiences_20250901_UBC_ModSim.md`