### Convert a Drawing to GPX (Route Pattern Mapper)

A **web app** that takes a **color-coded pattern image** (e.g., a design, logo or similar), overlays it onto a **(multi)-city street network** (downloaded from OpenStreetMap), extracts **GPS coordinates** for each color layer, and outputs the result as one or more **GPX track files** — ready to be used in any **GPS-capable** navigation apps.

- **Access** the tool [**here**](tools/RoutPlanner.html). 

**Note:** To run this app **locally**, you need to intiiate a **server** first. To do so, open **terminal** and run **`python -m http.server 8000`** in the folder where the file is saved. Then use this link: **`http://localhost:8000/_RoutPlanner.html`**. 

![RoutPlanner_App](images/tool_RoutPlanner.png)

This app was originally written as an ipython notebook and here is what it does:

- **Downloads a (multi)-city's street network** from OpenStreetMap.
- **Loads a pattern image** and converts it to HSV color space.
- **Detects which colors are present** in the image above a minimum threshold.
- **Creates binary masks** for each detected color.
- **Extracts the outer contour** of each color region and produces a skeletal boundary.
- **Overlays the pattern** onto the street map at a user-specified scale and position.
- **Orders the boundary pixels** into a continuous path using nearest-neighbor traversal.
- **Converts pixel positions to GPS coordinates** (latitude/longitude).
- **Exports one `.gpx` file per color** layer.

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

#### Scripts

- **Preparing** (if running on google colab) 
```bash 
from google.colab import drive
drive.mount('/content/drive')
%cd /content/drive/My Drive/GPX/
```

- **Installing required modules** (if not already installed)
```bash 
!pip install osmnx -q
!pip install gpxpy -q
```

- **Loading required modules**
```bash 
import numpy as np
import cv2
from PIL import Image
import matplotlib.pyplot as plt
import osmnx as ox
from skimage.morphology import skeletonize
import gpxpy
import gpxpy.gpx
from datetime import datetime
from scipy import ndimage
from skimage import measure
import os
```

- **Getting city's street network from OpenStreetMap**
```bash 
place_name = "Vancouver, BC, Canada"
network_type = 'bike'
print(f"Downloading {network_type} network for {place_name}")
G = ox.graph_from_place(place_name, network_type=network_type)
print(f"Street network for {place_name}")
fig, ax = ox.plot_graph(G, node_size=0, edge_color='black', edge_linewidth=0.5, bgcolor='white')
plt.show()
plt.close(fig)
```

- **Processing the image**
```bash 
filename = 'image.png'
filename_without_ext = os.path.splitext(filename)[0]
try:
  img = Image.open(filename).convert('RGB')
  img_np = np.array(img)
  hsv_img = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
except FileNotFoundError:
  print(f"Error: {filename} not found.")
plt.figure()
plt.imshow(img_np)
plt.axis('off')
plt.close()
```

- **Color range hsv** (update to be inclusive if needed) - _moved to the botoom of the this post_. 

- **Detects colors used in the image**
```bash 
detected_colors = []
total_pixels = img_np.shape[0] * img_np.shape[1]
min_pixels_threshold = total_pixels * 0.001 #

for color, ranges in color_ranges.items():
  if color in ['black', 'white']:
    gray_img = img.convert('L')
    gray_img_np = np.array(gray_img)
    if color == 'black':
        ret, mask = cv2.threshold(gray_img_np, 10, 255, cv2.THRESH_BINARY_INV)
    else: # color == 'white'
        ret, mask = cv2.threshold(gray_img_np, 245, 255, cv2.THRESH_BINARY)
  elif color == 'red':
    mask1 = cv2.inRange(hsv_img, np.array(ranges[0]), np.array(ranges[1]))
    mask2 = cv2.inRange(hsv_img, np.array(ranges[2]), np.array(ranges[3]))
    mask = mask1 + mask2
  else:
    lower, upper = ranges
    mask = cv2.inRange(hsv_img, np.array(lower), np.array(upper))
  pixel_count = np.sum(mask > 0)
  if pixel_count > min_pixels_threshold:
      detected_colors.append(color)
print(f"Detected colors in the image: {detected_colors}")
#
if 'white' in detected_colors: detected_colors.remove('white')
if 'black' in detected_colors: detected_colors.remove('black')
#
print(f"[cleaned] Detected colors in the image: {detected_colors}")
##digitizes colors in image and prepares image binary format
masks = {}
for color in detected_colors:
  if color.lower() in color_ranges:
    if color == 'red':
      ranges = color_ranges[color]
      mask1 = cv2.inRange(hsv_img, np.array(ranges[0]), np.array(ranges[1]))
      mask2 = cv2.inRange(hsv_img, np.array(ranges[2]), np.array(ranges[3]))
      mask = mask1 + mask2
    elif color in ['black', 'white']:
      gray_img = img.convert('L')
      gray_img_np = np.array(gray_img)
      if color == 'black':
          ret, mask = cv2.threshold(gray_img_np, 10, 255, cv2.THRESH_BINARY_INV)
      else: # color == 'white'
          ret, mask = cv2.threshold(gray_img_np, 245, 255, cv2.THRESH_BINARY)
    else:
      lower, upper = color_ranges[color]
      mask = cv2.inRange(hsv_img, np.array(lower), np.array(upper))
    masks[color] = mask
  else:
    print(f"Warning: color '{color}' not supported - not in color_ranges.")
###visualizing
for color in detected_colors:
  binary_img = masks[color]
  plt.figure()
  plt.subplot(1, 2, 1)
  plt.imshow(img, cmap='gray')
  plt.title('Original Image')
  plt.axis('off')
  #
  plt.subplot(1, 2, 2)
  plt.imshow(binary_img, cmap='gray')
  plt.title(f'Binary Image ({color})')
  plt.axis('off')
  plt.tight_layout()
  plt.show()
plt.close()
```

- **Creates outlines for each color**
```bash 
outline_imgs = {}
#
for color in detected_colors:
  #
  binary_img = masks[color]
  #
  kernel_clean = np.ones((3,3), np.uint8)
  binary_cleaned = cv2.morphologyEx(binary_img, cv2.MORPH_CLOSE, kernel_clean)
  binary_cleaned = cv2.morphologyEx(binary_cleaned, cv2.MORPH_OPEN, kernel_clean)
  #
  contours, _ = cv2.findContours(binary_cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
  #
  if not contours:
    print(f'No contours found for color {color}!')
    outline_imgs[color] = None
  else:
    largest_contour = max(contours, key=cv2.contourArea)
    #
    outline_img = np.zeros_like(binary_img)
    cv2.drawContours(outline_img, [largest_contour], -1, 255, 1)  # thickness=1 for thin boundary
    outline_imgs[color] = outline_img
```

- **Attempts to get the boundary/perimeter of the pattern as a continuous path**
```bash 
skeleton_imgs = {}
#
for color in detected_colors:
  kernel = np.ones((2,2), np.uint8)
  skeleton_img = cv2.morphologyEx(outline_imgs[color], cv2.MORPH_CLOSE, kernel)
  skeleton_imgs[color] = skeleton_img
###visualizing
for color in detected_colors:
  binary_img = masks[color]
  skeleton_img = skeleton_imgs[color]
  #
  plt.figure()
  plt.subplot(1, 3, 1)
  plt.imshow(img, cmap='gray')
  plt.title('Original Image')
  plt.axis('off')
  #
  plt.subplot(1, 3, 2)
  plt.imshow(binary_img, cmap='gray')
  plt.title(f'Binary Image ({color})')
  plt.axis('off')
  #
  plt.subplot(1, 3, 3)
  plt.imshow(skeleton_img, cmap='gray')
  plt.title(f'Boundary Route ({color})')
  plt.axis('off')
  plt.tight_layout()
  plt.show()
plt.close()
```

- **Overlaying image onto map - to detect the main extent using color or outermost layer**
```bash 
####**specify the outermost color**
detected_colors
outermost_color = 'yellow'
detected_colors.remove(outermost_color)
detected_colors.insert(0, outermost_color)
print(f"[sorted] Detected colors in the image: {detected_colors}")
##Trial and Error step
**Update these until the outermost boundary sits within the network**
scale_factor_y = 0.5 # 60% of whole map
scale_factor_x = 0.5 # 60% of whole map
position_offset_x = 0.10 # % shift left bottomright corner image #% of map
position_offset_y = 0.10 # % shift upward bottomright corner image #% of map
threshold_val = 10
#
existing_extent = None
reference_center = None
rgba_imgs = {}
image_data = {}
fig, ax = ox.plot_graph(G, node_size=0, edge_color='black',
                        edge_linewidth=1, bgcolor='white', show=False, close=False)
#
for i, color in enumerate(detected_colors):
    binary_img = masks[color]
    skeleton_img = skeleton_imgs[color]
    thisimage = skeleton_imgs[color]
    #
    if existing_extent:
        graph_xlim = (existing_extent[0], existing_extent[1])
        graph_ylim = (existing_extent[2], existing_extent[3])
    else:
        graph_xlim = ax.get_xlim()
        graph_ylim = ax.get_ylim()
    #
    graph_width = graph_xlim[1] - graph_xlim[0]
    graph_height = graph_ylim[1] - graph_ylim[0]
    #
    img_height, img_width = thisimage.shape
    #
    max_route_width = graph_width * scale_factor_x
    max_route_height = graph_height * scale_factor_y
    #
    width_scale = max_route_width / img_width
    height_scale = max_route_height / img_height
    final_scale = min(width_scale, height_scale)
    #
    new_width = img_width * final_scale
    new_height = img_height * final_scale
    #
    image_data[color] = {
        'image': thisimage,
        'new_width': new_width,
        'new_height': new_height,
        'final_scale': final_scale,
        'img_height': img_height,
        'img_width': img_width
    }
    #
    if reference_center is None:
        offset_x, offset_y = position_offset_x, position_offset_y
        route_right = graph_xlim[1] - (graph_width * offset_x)
        route_left = route_right - new_width
        route_bottom = graph_ylim[0] + (graph_height * offset_y)
        route_top = route_bottom + new_height
        #
        reference_center = (
            (route_left + route_right) / 2, 
            (route_bottom + route_top) / 2
        )
#
for color in detected_colors:
    data = image_data[color]
    thisimage = data['image']
    new_width = data['new_width']
    new_height = data['new_height']
    img_height = data['img_height']
    img_width = data['img_width']
    #
    center_x, center_y = reference_center
    #
    route_left = center_x - new_width / 2
    route_right = center_x + new_width / 2
    route_bottom = center_y - new_height / 2
    route_top = center_y + new_height / 2
    #
    rgba_img = np.zeros((img_height, img_width, 4), dtype=np.uint8)
    rgba_img[thisimage > 0] = color_map_rgba.get(color.lower(), [255, 0, 0, 255])
    #
    extent = (route_left, route_right, route_bottom, route_top)
    #
    ax.imshow(rgba_img, extent=extent, alpha=0.4, zorder=100)
    #
    kernel = np.ones((5, 5), np.uint8)
    thicker_img = cv2.dilate(rgba_img, kernel, iterations=2)
    ax.imshow(thicker_img, extent=extent, alpha=0.4, zorder=100)
    #
    if existing_extent is None:
        existing_extent = extent
    rgba_imgs[color] = rgba_img
    #
plt.title(f"pattern as routes mapped to city street network", fontsize=16)
plt.show()
```

**Before continuing**:
- **Does it look good?**
- **Does it fit in the network?**

- **Production step**
```bash 
coordinates = {}
figv, axv = ox.plot_graph(G, node_size=0, edge_color='black',
                        edge_linewidth=0.5, bgcolor='white', show=False, close=False)
#
for _, color in enumerate(detected_colors):
  rgba_img = rgba_imgs[color]
  #
  left, right, bottom, top = extent
  height, width, _ = rgba_img.shape
  #
  lon_per_pixel = (right - left) / width
  lat_per_pixel = (top - bottom) / height
  #
  route_pixels = []
  #
  for y in range(height):
      for x in range(width):
          if np.array_equal(rgba_img[y, x], color_map_rgba.get(color.lower(), [255, 0, 0, 255])):
              route_pixels.append((x, y))
  #
  route_pixels = np.array(route_pixels)
  #
  start_idx = np.argmin(route_pixels[:, 0])
  ordered_pixels = [route_pixels[start_idx]]
  remaining = list(range(len(route_pixels)))
  remaining.remove(start_idx)
  #
  current_pixel = route_pixels[start_idx]
  #
  while remaining:
      distances = []
      for idx in remaining:
          pixel = route_pixels[idx]
          #
          dist = np.sqrt((current_pixel[0] - pixel[0])**2 + (current_pixel[1] - pixel[1])**2)
          distances.append((dist, idx))
      #
      distances.sort()
      #
      chosen_idx = None
      for dist, idx in distances:
          if dist <= 2.0: # Consider pixels within a 2-pixel radius
              chosen_idx = idx
              break
      if chosen_idx is None:
          chosen_idx = distances[0][1]
      current_pixel = route_pixels[chosen_idx]
      ordered_pixels.append(current_pixel)
      remaining.remove(chosen_idx)
  coords = []
  for x, y in ordered_pixels:
      latitude = top - (y + 0.5) * lat_per_pixel
      longitude = left + (x + 0.5) * lon_per_pixel
      coords.append((latitude, longitude))
  coordinates[color] = coords
  #
  if coords:
    lats = [coord[0] for coord in coords]
    lons = [coord[1] for coord in coords]
    #
    axv.scatter(lons, lats, s=1, alpha=0.7, label=f'Route ({len(coords)} points)')
    #
    axv.plot(lons, lats, linewidth=1, alpha=0.6)
    #
axv.set_title("final route - GPS coordinates on city map", fontsize=16)
axv.legend()
plt.show()
```

- **Writing out**
```bash 
#Creating GPS and exporting GPX file
for _, color in enumerate(detected_colors):
  #
  filename_gpx=filename_without_ext+'_'+color
  timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
  output_filename = f"{filename_gpx}_{timestamp}.gpx"
  #
  coords = coordinates[color]
  #
  if not coords:
      print("No coordinates to save!")
  #
  gpx = gpxpy.gpx.GPX()
  gpx_track = gpxpy.gpx.GPXTrack()
  gpx.tracks.append(gpx_track)
  gpx_segment = gpxpy.gpx.GPXTrackSegment()
  gpx_track.segments.append(gpx_segment)
  #
  for lat, lon in coords:
    gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))
  #
  with open(output_filename, 'w') as f:
    f.write(gpx.to_xml())
  print(f"GPX route for color {color} saved to: {output_filename}")
```

**Note:** Put this at step 6. 
```bash 
color_ranges = {
            'black': None,
            'white': None,
            'red': ([0, 100, 20], [10, 255, 255], [160, 100, 20], [180, 255, 255]), # Red wraps around
            'orange': ([1, 100, 100], [1, 255, 255]),
            'amber': ([2, 100, 100], [2, 255, 255]),
            'yellow': ([3, 100, 100], [3, 255, 255]),
            'lime': ([4, 100, 100], [4, 255, 255]),
            'chartreuse': ([5, 100, 100], [5, 255, 255]),
            'green': ([6, 100, 100], [6, 255, 255]),
            'spring green': ([7, 100, 100], [7, 255, 255]),
            'cyan': ([8, 100, 100], [8, 255, 255]),
            'azure': ([9, 100, 100], [9, 255, 255]),
            'blue': ([10, 100, 100], [10, 255, 255]),
            'indigo': ([11, 100, 100], [11, 255, 255]),
            'violet': ([12, 100, 100], [12, 255, 255]),
            'purple': ([13, 100, 100], [13, 255, 255]),
            'magenta': ([14, 100, 100], [14, 255, 255]),
            'rose': ([15, 100, 100], [15, 255, 255]),
            'maroon': ([16, 100, 100], [16, 255, 255]),
            'brown': ([17, 100, 100], [17, 255, 255]),
            'olive': ([18, 100, 100], [18, 255, 255]),
            'teal': ([19, 100, 100], [19, 255, 255]),
            'turquoise': ([20, 100, 100], [20, 255, 255]),
            'sky blue': ([21, 100, 100], [21, 255, 255]),
            'navy': ([22, 100, 100], [22, 255, 255]),
            'coral': ([23, 100, 100], [23, 255, 255]),
            'salmon': ([24, 100, 100], [24, 255, 255]),
            'gold': ([25, 100, 100], [25, 255, 255]),
            'peach': ([26, 100, 100], [26, 255, 255]),
            'mint': ([27, 100, 100], [27, 255, 255]),
            'sea green': ([28, 100, 100], [28, 255, 255]),
            'forest green': ([29, 100, 100], [29, 255, 255]),
            'aqua': ([30, 100, 100], [30, 255, 255]),
            'lavender': ([31, 100, 100], [31, 255, 255]),
            'plum': ([32, 100, 100], [32, 255, 255]),
            'orchid': ([33, 100, 100], [33, 255, 255]),
            'periwinkle': ([34, 100, 100], [34, 255, 255]),
            'steel blue': ([35, 100, 100], [35, 255, 255]),
            'cadet blue': ([36, 100, 100], [36, 255, 255]),
            'khaki': ([37, 100, 100], [37, 255, 255]),
            'beige': ([38, 100, 100], [38, 255, 255]),
            'ivory': ([39, 100, 100], [39, 255, 255]),
            'slate blue': ([40, 100, 100], [40, 255, 255]),
            'royal blue': ([41, 100, 100], [41, 255, 255]),
            'midnight blue': ([42, 100, 100], [42, 255, 255]),
            'powder blue': ([43, 100, 100], [43, 255, 255]),
            'light cyan': ([44, 100, 100], [44, 255, 255]),
            'pale green': ([45, 100, 100], [45, 255, 255]),
            'dark green': ([46, 100, 100], [46, 255, 255]),
            'dark red': ([47, 100, 100], [47, 255, 255]),
            'crimson': ([48, 100, 100], [48, 255, 255]),
            'tomato': ([49, 100, 100], [49, 255, 255]),
            'firebrick': ([50, 100, 100], [50, 255, 255]),
            'chocolate': ([51, 100, 100], [51, 255, 255]),
            'sienna': ([52, 100, 100], [52, 255, 255]),
            'tan': ([53, 100, 100], [53, 255, 255]),
            'wheat': ([54, 100, 100], [54, 255, 255]),
            'light pink': ([55, 100, 100], [55, 255, 255]),
            'hot pink': ([56, 100, 100], [56, 255, 255]),
            'deep pink': ([57, 100, 100], [57, 255, 255]),
            'fuchsia': ([58, 100, 100], [58, 255, 255]),
            'thistle': ([59, 100, 100], [59, 255, 255]),
            'mauve': ([60, 100, 100], [60, 255, 255]),
            'indian red': ([61, 100, 100], [61, 255, 255]),
            'rosy brown': ([62, 100, 100], [62, 255, 255]),
            'dark orange': ([63, 100, 100], [63, 255, 255]),
            'light salmon': ([64, 100, 100], [64, 255, 255]),
            'sandy brown': ([65, 100, 100], [65, 255, 255]),
            'burlywood': ([66, 100, 100], [66, 255, 255]),
            'navajo white': ([67, 100, 100], [67, 255, 255]),
            'blanched almond': ([68, 100, 100], [68, 255, 255]),
            'moccasin': ([69, 100, 100], [69, 255, 255]),
            'papaya whip': ([70, 100, 100], [70, 255, 255]),
            'old lace': ([71, 100, 100], [71, 255, 255]),
            'linen': ([72, 100, 100], [72, 255, 255]),
            'antique white': ([73, 100, 100], [73, 255, 255]),
            'misty rose': ([74, 100, 100], [74, 255, 255]),
            'gainsboro': ([75, 100, 100], [75, 255, 255]),
            'light gray': ([76, 100, 100], [76, 255, 255]),
            'silver': ([77, 100, 100], [77, 255, 255]),
            'dark gray': ([78, 100, 100], [78, 255, 255]),
            'gray': ([79, 100, 100], [79, 255, 255]),
            'dim gray': ([80, 100, 100], [80, 255, 255]),
            'light slate gray': ([81, 100, 100], [81, 255, 255]),
            'slate gray': ([82, 100, 100], [82, 255, 255]),
            'dark slate gray': ([83, 100, 100], [83, 255, 255]),
            'black olive': ([84, 100, 100], [84, 255, 255]),
            'taupe': ([85, 100, 100], [85, 255, 255]),
            'charcoal': ([86, 100, 100], [86, 255, 255]),
            'jet': ([87, 100, 100], [87, 255, 255]),
            'onyx': ([88, 100, 100], [88, 255, 255]),
            'ebony': ([89, 100, 100], [89, 255, 255]),
            'ash gray': ([90, 100, 100], [90, 255, 255]),
            'cool gray': ([91, 100, 100], [91, 255, 255]),
            'warm gray': ([92, 100, 100], [92, 255, 255]),
            'neutral gray': ([93, 100, 100], [93, 255, 255]),
            'payne’s gray': ([94, 100, 100], [94, 255, 255]),
            'gunmetal': ([95, 100, 100], [95, 255, 255]),
            'smoke': ([96, 100, 100], [96, 255, 255]),
            'stormcloud': ([97, 100, 100], [97, 255, 255]),
            'outer space': ([98, 100, 100], [98, 255, 255]),
            'night': ([99, 100, 100], [99, 255, 255])
        }
#
color_map_rgba = {
            'black': [0, 0, 0, 255],
            'white': [255, 255, 255, 255],
            'red': [255, 0, 0, 255],
            'orange': [255, 165, 0, 255],
            'amber': [128, 128, 128, 255],
            'yellow': [255, 255, 0, 255],
            'lime': [0, 255, 0, 255],
            'chartreuse': [127, 255, 0, 255],
            'green': [0, 128, 0, 255],
            'spring green': [128, 128, 128, 255],
            'cyan': [0, 255, 255, 255],
            'azure': [240, 255, 255, 255],
            'blue': [0, 0, 255, 255],
            'indigo': [75, 0, 130, 255],
            'violet': [238, 130, 238, 255],
            'purple': [128, 0, 128, 255],
            'magenta': [255, 0, 255, 255],
            'rose': [128, 128, 128, 255],
            'maroon': [128, 0, 0, 255],
            'brown': [165, 42, 42, 255],
            'olive': [128, 128, 0, 255],
            'teal': [0, 128, 128, 255],
            'turquoise': [64, 224, 208, 255],
            'sky blue': [128, 128, 128, 255],
            'navy': [0, 0, 128, 255],
            'coral': [255, 127, 80, 255],
            'salmon': [250, 128, 114, 255],
            'gold': [255, 215, 0, 255],
            'peach': [128, 128, 128, 255],
            'mint': [128, 128, 128, 255],
            'sea green': [128, 128, 128, 255],
            'forest green': [128, 128, 128, 255],
            'aqua': [0, 255, 255, 255],
            'lavender': [230, 230, 250, 255],
            'plum': [221, 160, 221, 255],
            'orchid': [218, 112, 214, 255],
            'periwinkle': [128, 128, 128, 255],
            'steel blue': [128, 128, 128, 255],
            'cadet blue': [128, 128, 128, 255],
            'khaki': [240, 230, 140, 255],
            'beige': [245, 245, 220, 255],
            'ivory': [255, 255, 240, 255],
            'slate blue': [128, 128, 128, 255],
            'royal blue': [128, 128, 128, 255],
            'midnight blue': [128, 128, 128, 255],
            'powder blue': [128, 128, 128, 255],
            'light cyan': [128, 128, 128, 255],
            'pale green': [128, 128, 128, 255],
            'dark green': [128, 128, 128, 255],
            'dark red': [128, 128, 128, 255],
            'crimson': [220, 20, 60, 255],
            'tomato': [255, 99, 71, 255],
            'firebrick': [178, 34, 34, 255],
            'chocolate': [210, 105, 30, 255],
            'sienna': [160, 82, 45, 255],
            'tan': [210, 180, 140, 255],
            'wheat': [245, 222, 179, 255],
            'light pink': [128, 128, 128, 255],
            'hot pink': [128, 128, 128, 255],
            'deep pink': [128, 128, 128, 255],
            'fuchsia': [255, 0, 255, 255],
            'thistle': [216, 191, 216, 255],
            'mauve': [128, 128, 128, 255],
            'indian red': [128, 128, 128, 255],
            'rosy brown': [128, 128, 128, 255],
            'dark orange': [128, 128, 128, 255],
            'light salmon': [128, 128, 128, 255],
            'sandy brown': [128, 128, 128, 255],
            'burlywood': [222, 184, 135, 255],
            'navajo white': [128, 128, 128, 255],
            'blanched almond': [128, 128, 128, 255],
            'moccasin': [255, 228, 181, 255],
            'papaya whip': [128, 128, 128, 255],
            'old lace': [128, 128, 128, 255],
            'linen': [250, 240, 230, 255],
            'antique white': [128, 128, 128, 255],
            'misty rose': [128, 128, 128, 255],
            'gainsboro': [220, 220, 220, 255],
            'light gray': [128, 128, 128, 255],
            'silver': [192, 192, 192, 255],
            'dark gray': [128, 128, 128, 255],
            'gray': [128, 128, 128, 255],
            'dim gray': [128, 128, 128, 255],
            'light slate gray': [128, 128, 128, 255],
            'slate gray': [128, 128, 128, 255],
            'dark slate gray': [128, 128, 128, 255],
            'black olive': [128, 128, 128, 255],
            'taupe': [128, 128, 128, 255],
            'charcoal': [128, 128, 128, 255],
            'jet': [128, 128, 128, 255],
            'onyx': [128, 128, 128, 255],
            'ebony': [128, 128, 128, 255],
            'ash gray': [128, 128, 128, 255],
            'cool gray': [128, 128, 128, 255],
            'warm gray': [128, 128, 128, 255],
            'neutral gray': [128, 128, 128, 255],
            'payne’s gray': [128, 128, 128, 255],
            'gunmetal': [128, 128, 128, 255],
            'smoke': [128, 128, 128, 255],
            'stormcloud': [128, 128, 128, 255],
            'outer space': [128, 128, 128, 255],
            'night': [128, 128, 128, 255]
}
```