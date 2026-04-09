### Drawing to GPX (Route Pattern Mapper — Python Application)

A **Python notebook** that takes a **color-coded pattern image** (e.g., a design, logo, or artwork), overlays it onto a real city street network from **OpenStreetMap**, extracts **GPS coordinates** for each color layer, and exports the result as one or more **GPX track files** — ready to be used in any **GPS-capable** navigation app or **fitness tracker**.

- **Access** the code [**here**](Garage_99999990_RoutPlannerPython.ipynb)

**What It Does**

The notebook performs the following stages in order:

- **Downloads a city's street network** from OpenStreetMap
- **Loads a pattern image** and converts it to HSV color space
- **Detects which colors are present** in the image above a minimum threshold
- **Creates binary masks** for each detected color
- **Extracts the outer contour** of each color region and produces a skeletal boundary
- **Overlays the pattern** onto the street map at a user-specified scale and position
- **Orders the boundary pixels** into a continuous path using nearest-neighbor traversal
- **Converts pixel positions to GPS coordinates** (latitude/longitude)
- **Exports one `.gpx` file per color** layer

**Key Parameters Reference**

| Parameter | Location | Effect |
|:---|:---|:---|
| `place_name` | Stage 1 | City/region for the street network |
| `network_type` | Stage 1 | Road type filter (`bike`, `walk`, `drive`) |
| `filename` | Stage 2 | Input pattern image path |
| `min_pixels_threshold` | Stage 3 | `total_pixels × 0.001` — minimum pixel count to register a color |
| `outermost_color` | Stage 6 | Color used to anchor position; processed first |
| `scale_factor_x/y` | Stage 6 | Pattern size relative to map extent |
| `position_offset_x/y` | Stage 6 | Pattern placement offset from bottom-right corner |
| `threshold_val` | Stage 6 | Defined but available for custom threshold extensions |

**Notes and Limitations**

- **Color range definitions** use single-unit HSV hue bins (e.g., H=3 for yellow) that are very narrow and may need widening in `color_ranges` if the pattern image uses slightly off-hue colors.
- The **nearest-neighbor pixel ordering** is an O(n²) algorithm, and for large or high-resolution images with many boundary pixels, this step can be slow.
- The **GPX output does not snap to streets** always.