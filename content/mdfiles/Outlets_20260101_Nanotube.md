### Nanotube Builder and Mesher

An **interactive browser-based tool** for **parametric design** and **3D visualization** of nanochannel geometries, **mesh generation** in real time, and **export**.

- Access the tool [**here**](_Nanotube.html).

The channel profile is described by two **wall functions** over the **axial coordinate** `ξ`:

- `w₁(ξ) = α₁ sin(α₃πξ/5) + α₂ sin(7πξ/5)`
- `w₂(ξ) = r₀ + α₁ sin(α₃πξ/5) − α₂ sin(7πξ/5)`

The **local channel radius** at any point along the axis is:

- `r(ξ) = (w₂ − w₁) / 2`

The **centerline position** is the midpoint between `w₁` and `w₂`, producing a tube whose axis can curve and whose radius varies continuously along its length.

**Parameters**

| Symbol | Range | Description |
|:---|:---|:---|
| **α₁** | [0, 1] | **Asymmetry amplitude** — shifts the centerline, producing a curved or off-axis channel |
| **α₂** | [0, 1] | **Corrugation amplitude** — modulates the radius periodically, creating constrictions and expansions |
| **α₃** | [0.5, 4] | **Wavenumber multiplier** — controls the spatial frequency of the α₁ modulation |
| **r₀** | [0.2, 2] | **Minimum base radius** — sets the baseline channel width |
| **L**  | [2, 40] | **Tube length** in the `ξ` domain |
| **Nₐ** | >20 | **Axial mesh points** — higher values give a smoother profile along the length |
| **Nᵣ** | >8  | **Radial mesh points** — higher values give a rounder cross-section |

Each parameter has a **slider** for quick exploration and a **number input** for precise entry. Press **Enter** or leave the field to **apply** a typed value.

Live **vertex**, **face**, and **estimated file size** statistics update automatically as you adjust these values.

**Viewport Navigation**

| Action | Result |
|:---|:---|
| Left-click drag | **Pan** — recenters the view |
| Right-click drag | **Rotate** the channel |
| Shift + drag | **Rotate** the channel |
| Scroll wheel | **Zoom** in / out |
| Pinch (touch) | **Zoom** in / out |
| Single finger (touch) | **Pan** |
| `+` / `−` buttons | **Step zoom** in / out |
| `RST` button | **Reset** zoom, pan, and rotation to defaults |

Select a format, check the **estimated file size**, then click **Download**.

The exported file contains the following information:

- `surface` — `outer` or `inner`
- `face_indices` — semicolon-separated list of all face IDs the vertex belongs to
- `nx, ny, nz` — surface normal vector
- `u, v` — UV texture coordinates

![Nanotube Builder and Mesher](images/Images_Outlets_20260101_Nanotube.png)