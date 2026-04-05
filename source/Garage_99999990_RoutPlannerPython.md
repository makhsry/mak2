## Drawing to GPX (Route Pattern Mapper — Python Application)

A Google Colab notebook that takes a **color-coded pattern image** (e.g., a design, logo, or artwork), overlays it onto a real city street network from OpenStreetMap, extracts GPS coordinates for each color layer, and exports the result as one or more **GPX track files** — ready to use in any GPS-capable navigation app or fitness tracker.

[**Downalod the code here** (save as .ipynb file)](Garage_99999990_RoutPlannerPython.ipynb) 

**What It Does**     
The notebook performs the following stages in order:     
1. **Downloads a city's street network** from OpenStreetMap
2. **Loads a pattern image** and converts it to HSV color space
3. **Detects which colors are present** in the image above a minimum threshold
4. **Creates binary masks** for each detected color
5. **Extracts the outer contour** of each color region and produces a skeletal boundary
6. **Overlays the pattern** onto the street map at a user-specified scale and position
7. **Orders the boundary pixels** into a continuous path using nearest-neighbor traversal
8. **Converts pixel positions to GPS coordinates** (latitude/longitude)
9. **Exports one `.gpx` file per color** layer

**Pipeline Detail**     
**Stage 1 — Street Network Download**     

```python
place_name = "Vancouver, BC, Canada"
network_type = 'bike'
G = ox.graph_from_place(place_name, network_type=network_type)
```

Uses `osmnx` to fetch the road/path graph for a named city. `network_type` can be `'bike'`, `'walk'`, `'drive'`, etc.

**Stage 2 — Image Loading and Color Space Conversion**     

```python
img = Image.open(filename).convert('RGB')
img_np = np.array(img)
hsv_img = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
```

The image is opened as RGB then converted to **HSV (Hue, Saturation, Value)** space. HSV is used because it separates color identity (Hue) from brightness (Value) and intensity (Saturation), making color segmentation more robust than raw RGB thresholding.

**Stage 3 — Color Detection**     

Each named color in `color_ranges` is defined by an HSV lower-bound and upper-bound pair `[H, S, V]`:
- **Black** is detected in grayscale: pixels with grayscale value `≤ 10` (via `cv2.THRESH_BINARY_INV`)
- **White** is detected in grayscale: pixels with grayscale value `≥ 245` (via `cv2.THRESH_BINARY`)
- **Red** is handled specially because red **wraps around** the HSV hue circle (H ≈ 0° and H ≈ 180°); two separate ranges are combined: `[0,100,20]–[10,255,255]` and `[160,100,20]–[180,255,255]`, and the masks are summed
- All **other colors** are matched with a single `cv2.inRange(hsv_img, lower, upper)` call

A color is considered **present** in the image if the number of matching pixels exceeds the minimum threshold:

```
min_pixels_threshold = total_pixels × 0.001
```

where `total_pixels = image_height × image_width`. This 0.1% floor filters out noise and compression artifacts. Black and white are removed from the final detected list after this step, since they are used as background/border and not as route colors.

**Stage 4 — Binary Mask Generation**     

For each detected color, a binary mask is produced where matching pixels = `255` and all others = `0`. These masks are stored in a dictionary keyed by color name.

**Stage 5 — Contour Extraction and Boundary Skeletonization**     

For each color mask:
- **Morphological cleaning** is applied using a `3×3` structuring element:
  - `MORPH_CLOSE` (dilation then erosion) fills small holes and gaps
  - `MORPH_OPEN` (erosion then dilation) removes small noise blobs
- **External contours** are found with `cv2.findContours(..., cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)`. `CHAIN_APPROX_NONE` stores every single contour point (no compression), giving a dense boundary.
- The **largest contour by area** is selected: `max(contours, key=cv2.contourArea)`
- The contour is drawn onto a blank image with **thickness = 1**, producing a single-pixel-wide outline.
- A final `MORPH_CLOSE` with a `2×2` kernel closes any remaining small gaps in the outline to ensure path continuity.

**Stage 6 — Overlay onto Street Map**     

The pattern is scaled and positioned on top of the `osmnx` map axes.

**Scale calculation:**     

```
max_route_width  = graph_width  × scale_factor_x
max_route_height = graph_height × scale_factor_y
#
width_scale  = max_route_width  / img_width
height_scale = max_route_height / img_height
final_scale  = min(width_scale, height_scale)   ← preserves aspect ratio
#
new_width  = img_width  × final_scale
new_height = img_height × final_scale
```

**Positioning** (bottom-right anchor, first color only):     

```
route_right  = graph_xlim[1] − (graph_width  × position_offset_x)
route_left   = route_right − new_width
route_bottom = graph_ylim[0] + (graph_height × position_offset_y)
route_top    = route_bottom + new_height
#
reference_center = ( (route_left + route_right) / 2,
                     (route_bottom + route_top) / 2 )
```

All subsequent color layers use the same `reference_center` so every color is co-registered to the same position. Each color layer is rendered as an RGBA overlay (with `alpha=0.4`) and additionally dilated with a `5×5` kernel (`iterations=2`) for visual thickness on the map.

The user iterates on `scale_factor_x`, `scale_factor_y`, `position_offset_x`, and `position_offset_y` until the pattern fits visually within the street network.

**Stage 7 — Pixel-to-GPS Coordinate Conversion and Path Ordering**     

**Pixel → geographic coordinate mapping:**     

```
lon_per_pixel = (right − left) / width
lat_per_pixel = (top − bottom) / height
#
longitude = left + (x + 0.5) × lon_per_pixel
latitude  = top  − (y + 0.5) × lat_per_pixel
```

The `+ 0.5` offset places the sample point at the pixel center. Note that the y-axis is inverted: image row 0 is at the top, but geographic latitude increases upward, so latitude is computed by subtracting from `top`.

**Nearest-neighbor path ordering:**
All non-background pixels belonging to each color are collected. Starting from the leftmost pixel (minimum x), the path is built greedily:

```
dist(current, candidate) = √( (Δx)² + (Δy)² )
```

At each step, all remaining pixels are sorted by Euclidean distance from the current pixel. The closest pixel within a 2-pixel radius is chosen as the next step. If no pixel falls within that radius (i.e., a gap exists in the skeleton), the globally nearest remaining pixel is used as a fallback. This produces an ordered sequence that approximates a continuous traversal of the boundary.

**Stage 8 — GPX Export**     

For each color, a GPX track is created using `gpxpy`:

```
GPX → GPXTrack → GPXTrackSegment → [GPXTrackPoint(lat, lon), ...]
```

The output file is named:

```
{image_filename_without_ext}_{color}_{YYYY-MM-DD_HH-MM-SS}.gpx
```

One `.gpx` file is produced per detected color layer.

**Dependencies**     

| Package | Purpose |
|---|---|
| `osmnx` | Download OpenStreetMap street networks |
| `gpxpy` | Create and export GPX track files |
| `opencv-python` (`cv2`) | HSV conversion, masking, morphology, contours |
| `Pillow` (`PIL`) | Image loading and grayscale conversion |
| `numpy` | Array operations and pixel math |
| `matplotlib` | Visualization of map and overlay |
| `scikit-image` | `skeletonize`, `measure` (imported, available for extension) |
| `scipy` | `ndimage` (imported, available for extension) |

Install non-default Colab packages:

```bash
pip install osmnx gpxpy
```

**Usage Instructions**     

**Environment Setup (Google Colab)**     

- Open the notebook in [Google Colab](https://colab.research.google.com/).
- Mount your Google Drive:

  ```python
  from google.colab import drive
  drive.mount('/content/drive')
  ```

- Navigate to the directory containing your pattern image:

  ```python
  %cd /content/drive/My Drive/GPX/
  ```

- Install required packages:

  ```bash
  !pip install osmnx -q
  !pip install gpxpy -q
  ```

**Configure the City and Network Type**     

```python
place_name = "Vancouver, BC, Canada"   # Any OSM-recognized place name
network_type = 'bike'                   # 'bike', 'walk', 'drive', 'all'
```

**Set the Input Image**     

```python
filename = 'AzadiSq.png'   # Your pattern image (PNG recommended)
```

The image should be a **color-coded flat design** where each distinct region uses a solid, distinguishable color. Gradients and photographic images will produce unpredictable results.

**Identify the Outermost Color**     

After the color detection cell runs, inspect the `detected_colors` list printed to output, then set:

```python
outermost_color = 'yellow'   # The color forming the outermost boundary of your pattern
```

This color is moved to the front of the processing order so it establishes the reference position for all inner layers.

**Tune Scale and Position (Trial and Error)**     

```python
scale_factor_y     = 0.5    # Pattern height as a fraction of map height (0.0–1.0)
scale_factor_x     = 0.5    # Pattern width as a fraction of map width  (0.0–1.0)
position_offset_x  = 0.10   # Horizontal offset from the right edge of the map (fraction)
position_offset_y  = 0.10   # Vertical offset from the bottom edge of the map (fraction)
```

Run the overlay cell and visually inspect the result. Adjust these four values until the pattern sits fully within the street network, then re-run.

**Run the Production Step**     

Once the overlay looks correct, run the production cells. The notebook will:
- Compute GPS coordinates for every boundary pixel of every color layer
- Plot the final coordinate paths on the map
- Save one `.gpx` file per color to the current working directory

**Use the GPX Files**     

Import the `.gpx` files into any GPS application (Garmin Connect, Komoot, Strava, Google Maps, etc.) or load them onto a GPS device to navigate the pattern as a real-world route.

**Key Parameters Reference**     

| Parameter | Location | Effect |
|---|---|---|
| `place_name` | Stage 1 | City/region for the street network |
| `network_type` | Stage 1 | Road type filter (`bike`, `walk`, `drive`) |
| `filename` | Stage 2 | Input pattern image path |
| `min_pixels_threshold` | Stage 3 | `total_pixels × 0.001` — minimum pixel count to register a color |
| `outermost_color` | Stage 6 | Color used to anchor position; processed first |
| `scale_factor_x/y` | Stage 6 | Pattern size relative to map extent |
| `position_offset_x/y` | Stage 6 | Pattern placement offset from bottom-right corner |
| `threshold_val` | Stage 6 | Defined but available for custom threshold extensions |

**Notes and Limitations**     

- **Color range definitions** use single-unit HSV hue bins (e.g., H=3 for yellow). These bins are very narrow and may need widening in `color_ranges` if the pattern image uses slightly off-hue colors.
- The **nearest-neighbor pixel ordering** is an O(n²) algorithm. For large or high-resolution images with many boundary pixels, this step can be slow.
- The **GPX output does not snap to streets**. Coordinates reflect the geometric shape of the pattern scaled to the map extent. For street-snapped routing, post-process the GPX in a routing engine.
- The notebook is designed for **Google Colab** and relies on Google Drive for file access. Adapting it to a local Jupyter environment requires removing the Drive mount cells and adjusting file paths.
