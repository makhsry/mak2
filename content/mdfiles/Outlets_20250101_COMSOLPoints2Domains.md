### Creating COMSOL-native Domains from Mesh Points Cloud Data

This is a **`java`** script in **`COMSOL Application Method`** designed to automate 3D geometry construction from point cloud data into COMSOL's native **domains**.

The point cloud data are generated using the **`python`** script that projects a **`convex hull`** to the cloud points and generates respectives faces for each set of points in a **`triangulations`**.

#### Java Script

```bash
package builder;
import com.comsol.api.*;
import com.comsol.api.database.*;
import com.comsol.api.database.param.*;
import com.comsol.api.database.result.*;
import com.comsol.model.*;
import com.comsol.model.physics.*;
import com.comsol.model.application.*;
import java.io.*;
import java.util.*;
import com.comsol.model.*;
import com.comsol.model.util.*;
public class via_csv_combined extends ApplicationMethod
{
  // SWITCH
  // 1: via_csv_with_faceid
  // 2: via_csv_with_faceid_with_scale
  // 3: via_csv_with_faceid_with_scale_with_fillet
  int jobType = 3; 
  String CompTag = "comp1";
  String GeoTag = "geom1";
  int maxIDX = 000000;
  int created_domains = 0;
  double tagetV = 1000.0; //0.500646235*1000;
  double currentV = 1000.0;
  double scaleV = Math.pow(tagetV/currentV, 1.0/3.0); // 1/3 is not 1.0/3.0
  public void execute()
  {
    ModelUtil.showProgress("COMSOL_Progress.txt");
    ArrayList<double[]> DomainPoints = new ArrayList<>();
    // initialization
    int domid_old = 0;
    for (int idx = 0; idx <= maxIDX; idx++)
    {
      double domid = model.param().evaluate("fid_domid("+idx+")");
      // populate domain points until domain changes
      if (idx < 1) {domid_old = (int) domid; } // initiate domain ids
      if ((int) domid == domid_old) // one family of points
      {
        double posx = model.param().evaluate("fid_posx("+idx+")");
        double posy = model.param().evaluate("fid_posy("+idx+")");
        double posz = model.param().evaluate("fid_posz("+idx+")");
        DomainPoints.add(new double[]{posx, posy, posz});
      } // end if - one family of points
      else // family changed - remember to reset
      {
        // containers - node group - packing (or node groupe in scale scripts)
        String GroupName = (jobType >= 2) ? "G"+Integer.toString(domid_old) : Integer.toString(domid_old);
        model.component(CompTag).geom(GeoTag).nodeGroup().create(GroupName);
        // containers - list of tetrahedrons
        ArrayList<String> tetraList = new ArrayList<>(); // to record actual builds
        // compute COM
        double[] pCOM = computeCOM(DomainPoints); // shared point in all tetrahedrons
        for (int pt = 0; pt <= DomainPoints.size()-3; pt += 3)
        {
          double[] p1 = DomainPoints.get(pt+0);
          double[] p2 = DomainPoints.get(pt+1);
          double[] p3 = DomainPoints.get(pt+2);
          // compact vertices matrix
          double[][] verts = {{p1[0], p2[0], p3[0], pCOM[0]},
                              {p1[1], p2[1], p3[1], pCOM[1]},
                              {p1[2], p2[2], p3[2], pCOM[2]}};
          // tetrahedron name tag
          String tetName = "tetra_"+Integer.toString(domid_old)+"_"+"com"+Integer.toString(pt);
          // initialize tetrahedron
          model.component(CompTag).geom(GeoTag).create(tetName, "Tetrahedron");
          // assign vertices
          model.component(CompTag).geom(GeoTag).feature(tetName).set("p", verts);
          // try to build
          try
          {
            model.component(CompTag).geom(GeoTag).run(tetName); // building
            tetraList.add(tetName); // add to list
            model.component(CompTag).geom(GeoTag).nodeGroup(GroupName).add(tetName); // add to group
          } // end try
          catch (Exception e) // if not built
          {
            continue; // not built, move along
          } // end - catch
        } // end - for pt
        // tetra list type conversion
        String[] tetraArray = tetraList.toArray(new String[0]);
        // performing boolean operations to unify the tetrahedrons
        String UnionName = (jobType >= 2) ? "U"+Integer.toString(domid_old) : Integer.toString(domid_old);
        //
        model.component(CompTag).geom(GeoTag).create(UnionName, "Union");
        model.component(CompTag).geom(GeoTag).feature(UnionName).selection("input").set(tetraArray);
        model.component(CompTag).geom(GeoTag).feature(UnionName).set("intbnd", false);
        model.component(CompTag).geom(GeoTag).feature(UnionName).set("repairtoltype", "auto");
        /*
        model.component(CompTag).geom(GeoTag).feature(Integer.toString(domid_old)).set("repairtoltype", "absolute");
        model.component(CompTag).geom(GeoTag).feature(Integer.toString(domid_old)).set("absrepairtol", "1E-14");
        */
        // building the union
        model.component(CompTag).geom(GeoTag).run(UnionName);
        // Logic for Job 2 and 3 (Scaling)
        if (jobType >= 2)
        {
          // getting the union and scaling it here
          String ScaleName = "S"+Integer.toString(domid_old);
          model.component(CompTag).geom(GeoTag).create(ScaleName, "Scale");
          model.component(CompTag).geom(GeoTag).feature(ScaleName).set("isotropic", scaleV);
          model.component(CompTag).geom(GeoTag).feature(ScaleName).selection("input").set(UnionName);
          model.component(CompTag).geom(GeoTag).feature(ScaleName).set("pos", new double[]{pCOM[0], pCOM[1], pCOM[2]});
          // Logic for Job 3 (Fillet)
          if (jobType == 3)
          {
            model.component(CompTag).geom(GeoTag).run(ScaleName);
            created_domains += 1;
            // now trying the fillet operation
            String filletName = "F"+Integer.toString(domid_old);
            model.component(CompTag).geom(GeoTag).create(filletName, "Fillet3D");
            model.component(CompTag).geom(GeoTag).feature(filletName).set("radius", "0.0001");
            GeomInfo info = model.component(CompTag).geom(GeoTag).obj(ScaleName);
            int fromDim = info.getSDim(); // e.g. 3 for 3D
            int toDim = 1; // edges
            int[][] adj = info.getAdj(fromDim, toDim);
            int[] edgeIndices = adj[0];
            model.component(CompTag).geom(GeoTag).feature(filletName).selection("edge").set(ScaleName, edgeIndices);
            model.component(CompTag).geom(GeoTag).run(filletName);
          }
        }
        // reset state for next round / domain
        DomainPoints.clear();
        tetraList.clear();
        domid_old = (int) domid;
        // do not forget current surpass in if
        double posx = model.param().evaluate("fid_posx("+idx+")");
        double posy = model.param().evaluate("fid_posy("+idx+")");
        double posz = model.param().evaluate("fid_posz("+idx+")");
        DomainPoints.add(new double[]{posx, posy, posz});
      } // end else - family changed - remember to reset
    } // end - for - idx
    // build final geometry
    model.component(CompTag).geom(GeoTag).run();
  } // end - public void execute
  // helper functions
  public double[] computeCOM(List<double[]> points)
  {
    double cx = 0, cy = 0, cz = 0;
    for (double[] pt : points)
    {
      cx += pt[0];
      cy += pt[1];
      cz += pt[2];
    } // end - for
    int n = points.size();
    return new double[]{cx/n, cy/n, cz/n};
  } // end - computeCOM
} // end public main
```

#### Python Script

```bash
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
```