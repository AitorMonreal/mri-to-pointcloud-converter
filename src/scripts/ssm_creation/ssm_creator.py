#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
"""
Created on Mon Nov 18 21:24:22 2019

@author: Aitor Monreal Urcelay
"""

# Arguments
import argcomplete
import argparse

# VTK & Vedo
import vtk
from vedo import *

# OS
import os

# SYS
import sys


class FemurSurface(object):
    def __init__(self, data_dir: str, filename: str):
        self.filename: str = filename
        self.femur_vtk_surface = self.__read_mhd_file(data_dir)
        self.smoothing_iterations: int = 14
        self.pass_band: float = 0.001
        self.feature_angle: float = 120.0
        self.femur_mesh = None
        self.downsampling_ratio = 0.2

    def __read_mhd_file(self, data_dir: str):
        mhd_file_path: str = data_dir + "/" + self.filename
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName(mhd_file_path)
        reader.Update()
        return reader

    def generate_smoothed_surface(self):
        self.__generate_marching_cubes()
        self.__smooth_surface()

    def __generate_marching_cubes(self):
        marching_cubes = vtk.vtkDiscreteMarchingCubes()
        marching_cubes.SetInputConnection(self.femur_vtk_surface.GetOutputPort())
        marching_cubes.GenerateValues(1, 1, 1)
        marching_cubes.Update()
        self.femur_vtk_surface = marching_cubes

    def __smooth_surface(self):
        smoother = vtk.vtkWindowedSincPolyDataFilter()
        smoother.SetInputConnection(self.femur_vtk_surface.GetOutputPort())
        smoother.SetNumberOfIterations(self.smoothing_iterations)
        smoother.SetFeatureAngle(self.feature_angle)
        smoother.SetPassBand(self.pass_band)
        smoother.BoundarySmoothingOff()
        smoother.FeatureEdgeSmoothingOff()
        smoother.NonManifoldSmoothingOn()
        smoother.NormalizeCoordinatesOn()
        smoother.Update()
        self.femur_vtk_surface = smoother.GetOutput()

    def downsample_vertices(self):
        self.femur_mesh = Mesh(self.femur_vtk_surface)
        self.femur_mesh.decimate(fraction=self.downsampling_ratio)

    def visualise_surface(self):
        # create the outline of the data as polygonal mesh and show it
        cam = dict(pos=(100, 200, 20),
                   viewup=(-0.8, -1.2, -1.8))
        if self.femur_mesh is None:
            Mesh(self.femur_vtk_surface).show(camera=cam)
        else:
            self.femur_mesh.show(camera=cam)

    def get_surface(self):
        return self.femur_mesh


def __parse_arguments() -> argparse.Namespace:
    """Parse the incoming command line parameters
    Returns:
        argparse.Namespace: List of arguments that have been parsed
    """
    parser = argparse.ArgumentParser(description='Read data.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--segmented_data_dir", type=str, default='~/.config',
                        help="Directory where you are storing the 3D MRI segmented data as mhd (and raw) files.")
    parser.add_argument("--visualise", type=bool, default='False', help="Do you want to visualise the surfaces, "
                                                                        "True or False?")

    argcomplete.autocomplete(parser)

    return parser.parse_args()


def load_data(data_dir: str):
    load_femur_bone(data_dir)
    # load_tibia_bone()
    # load_femur_cartilage()
    # load_tibia_cartilage()


def load_femur_bone(data_dir: str, visualise: bool, pointcloud_dir: str):
    count: int = 0
    file_header: str = "femur_bone_"

    for filename in os.listdir(data_dir):
        if filename.endswith(".mhd") and count < 20:
            count += 1
            femur_id: str = filename[0:7]

            femur_surface = FemurSurface(data_dir, filename)
            femur_surface.generate_smoothed_surface()
            femur_surface.downsample_vertices()
            if count == 1 and visualise:
                femur_surface.visualise_surface()

            # NUMPY ARRAY
            points = femur_surface.get_surface().points()

            # VTK Follower - Vedo Points
            vedo_points = Points(femur_surface.get_surface().points())
            
            os.chdir(pointcloud_dir)
            io.write(Points(femur_surface.get_surface().points()), file_header + "cloud_" + femur_id + ".ply")


def main(argv):
    """Main function"""

    print('Application started')

    args = __parse_arguments()
    data_dir: str = args.segmented_data_dir
    visualise: bool = args.visualise

    data_dir = "/home/aitor/src/FemurPrediction/OAI-Data"
    pointcloud_dir = "/home/aitor/src/FemurPrediction/SmoothPointclouds"
    visualise = False

    load_femur_bone(data_dir, visualise, pointcloud_dir)


if __name__ == "__main__":
    main(sys.argv)
