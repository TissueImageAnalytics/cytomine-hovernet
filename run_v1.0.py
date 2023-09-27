# -*- coding: utf-8 -*-

# * Copyright (c) 2009-2022. Authors: see NOTICE file.
# *
# * Licensed under the Apache License, Version 2.0 (the "License");
# * you may not use this file except in compliance with the License.
# * You may obtain a copy of the License at
# *
# *      http://www.apache.org/licenses/LICENSE-2.0
# *
# * Unless required by applicable law or agreed to in writing, software
# * distributed under the License is distributed on an "AS IS" BASIS,
# * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# * See the License for the specific language governing permissions and
# * limitations under the License.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import numpy as np
import sys
import os
import torch

from glob import glob
import joblib
from shapely.geometry import Polygon, Point
from shapely import wkt

# sys.path.append('/home/adams/Projects/tiatoolbox_local/tiatoolbox/')
from tiatoolbox.models.engine.nucleus_instance_segmentor import NucleusInstanceSegmentor

from cytomine import CytomineJob
from cytomine.models import (
    Annotation, AnnotationCollection, ImageInstanceCollection, Job
)

__author__ = "Mostafa Jahanifar <mostafa.jahanifar@warwick.ac.uk> and Adam Shephard <adam.shephard@warwick.ac.uk>"


def main(argv):
    with CytomineJob.from_cli(argv) as conn:
        conn.job.update(status=Job.RUNNING, progress=0, statusComment="Initialization...")
        base_path = os.getenv("HOME")  # Mandatory for Singularity
        working_path = os.path.join(base_path, str(conn.job.id))

        # Select images to process
        images = ImageInstanceCollection().fetch_with_filter(
            "project",
            conn.parameters.cytomine_id_project
        )

        # Use TIAToolbox nucleus instance segmentor engine for HoVerNet model
        inst_segmentor = NucleusInstanceSegmentor(
            pretrained_model=conn.parameters.hovernet_model,
            num_loader_workers=0,
            num_postproc_workers=0,
            batch_size=2,
        )

        if conn.parameters.cytomine_id_images == 'all':
            list_imgs = [int(image.id) for image in images]
        else:
            list_imgs = [int(id_img) for id_img in conn.parameters.cytomine_id_images.split(',')]
            
        # generating cell ID dict
        cell_id_dict={0: conn.parameters.cytomine_id_cell_neo_term,
                      1: conn.parameters.cytomine_id_cell_inf_term,
                      2: conn.parameters.cytomine_id_cell_con_term,
                      3: conn.parameters.cytomine_id_cell_dead_term,
                      4: conn.parameters.cytomine_id_cell_nnepi_term}

        # Go over images
        for id_image in conn.monitor(list_imgs, prefix="Running detection on image", period=0.1):
            # Dump ROI annotations in img from Cytomine server to local images
            roi_annotations = AnnotationCollection(
                project=conn.parameters.cytomine_id_project,
                term=conn.parameters.cytomine_id_roi_term,
                image=id_image,
                showWKT=True
            ).fetch()

            print(roi_annotations)

            # Go over ROI in this image
            for roi in roi_annotations:
                # Get Cytomine ROI coordinates for remapping to whole-slide
                # Cytomine cartesian coordinate system, (0,0) is bottom left corner
                print("----------------------------ROI------------------------------")
                roi_geometry = wkt.loads(roi.location)
                print(f"ROI Geometry from Shapely: {roi_geometry}")
                print("ROI Bounds")
                print(roi_geometry.bounds)

                minx, miny = roi_geometry.bounds[0], roi_geometry.bounds[3]

                # Dump ROI image into local PNG file
                roi_path = os.path.join(
                    working_path,
                    str(roi_annotations.project),
                    str(roi_annotations.image),
                    str(roi.id)
                )
                roi_png_filename = os.path.join(roi_path, f'{roi.id}.png')
                print(f"roi_png_filename: {roi_png_filename}")
                roi.dump(dest_pattern=roi_png_filename, mask=True, alpha=True)

                X_files = sorted(glob(os.path.join(roi_path, f'{roi.id}*.png')))

                # Going over ROI images in ROI directory (in our case: one ROI per directory)
                for x in range(0, len(X_files)):
                    print(f"------------------- Processing ROI file {x}: {roi_png_filename}")

                    tile_output = inst_segmentor.predict(
                        [X_files[x]],
                        save_dir=os.path.join(roi_path, "hovernet_results"),
                        mode="tile",
                        on_gpu=False,
                        crash_on_exception=True,
                    )
                    
                    tile_preds = joblib.load(f"{tile_output[0][1]}.dat")

                    print("Number of detected nuclei: %d" % len(tile_preds))

                    cytomine_annotations = AnnotationCollection()
                    # Go over detections in this ROI, convert and upload to Cytomine
                    for nucleus in tile_preds:
                        # Converting to Shapely annotation
                        points = list()
                        contours = tile_preds[nucleus]['contour']
                        nuc_type = tile_preds[nucleus]['type']
                        for i in range(len(contours)):
                            # Cytomine cartesian coordinate system, (0,0) is bottom left corner
                            p = Point(minx + contours[i][0], miny - contours[i][1])
                            points.append(p)
# need to add way of including nuclei class
                        annotation = Polygon(points)
                        # Append to Annotation collection
                        cytomine_annotations.append(
                            Annotation(
                                location=annotation.wkt,
                                id_image=id_image,  # conn.parameters.cytomine_id_image,
                                id_project=conn.parameters.cytomine_id_project,
                                id_terms=[cell_id_dict[nuc_type]] #[int(nuc_type)] #
                            )
                        )
                        print(".", end='', flush=True)
                    print()

                    # Send Annotation Collection (for this ROI) to Cytomine server in one http request
                    cytomine_annotations.save()

        conn.job.update(status=Job.TERMINATED, progress=100, statusComment="Finished.")


if __name__ == "__main__":
    main(sys.argv[1:])
