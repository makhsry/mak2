import os
import glob
import numpy as np
from scipy.spatial import ConvexHull # vertices detection
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import re
from datetime import datetime
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
#to read files (data exported from comsol)
def process_point_files(filename_pattern):
    data_dict = {}
    for filename in os.listdir('.'):
        if filename.startswith(filename_pattern):
            try:
                match = re.search(r"dom(\d+)", filename)
                if not match:
                    print(f"Could not extract number from {filename}")
                    continue
                file_number = int(match.group(1))

                with open(filename, 'r') as f:
                    lines = f.readlines()
                    data_lines = lines[9:] # line 10 onwards

                data = []
                for line in data_lines:
                    values = line.strip().split() #  space-separated
                    data.append([float(v) for v in values]) # to float

                if data:
                    numpy_data = np.array(data)
                    processed_data = numpy_data[:, :-1]
                    data_dict[filename] = {
                        'file_number': file_number,
                        'data': processed_data
                    }
                else:
                     data_dict[filename] = {
                        'file_number': file_number,
                        'data': np.array([]) # if no data lines
                    }

            except Exception as e:
                print(f"Error processing file {filename}: {e}")

    return data_dict
##building the convex hull over the imported mesh
def convexhull3dpoints(points):
  hull = ConvexHull(points)
  boundary_vertex_indices = np.unique(hull.simplices.flatten())
  boundary_vertices = points[boundary_vertex_indices]
  faces = [points[simplex] for simplex in hull.simplices]
  simplicez = hull.simplices
  return boundary_vertex_indices, boundary_vertices, faces, simplicez
# -------
filename_pattern="SC1_Assembly126_AR111_dom"
processed_data = process_point_files(filename_pattern)
points = processed_data[filename_pattern+'1']['data']
hull = ConvexHull(points)
faces = [points[simplex] for simplex in hull.simplices]
store = np.empty((0, 4))
triangulation = np.empty((0, 5)) # connect COM to each set of three points
# domainid, faceid, x, y, z
index_col = np.arange(triangulation.shape[0]).reshape(-1, 1)
triangulation_for_comsol = np.hstack((index_col, triangulation))
np.savetxt(output_filenames_triangulation_for_comsol, triangulation_for_comsol, delimiter=",", fmt="%.6f")