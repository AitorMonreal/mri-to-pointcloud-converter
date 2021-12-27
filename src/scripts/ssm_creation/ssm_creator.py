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

# NumPy
import numpy as np


class FemurSurface(object):
    def __init__(self, data_dir: str, filename: str, downsampling_ratio: float):
        self.filename: str = filename
        self.femur_vtk_surface = self.__read_mhd_file(data_dir)
        self.smoothing_iterations: int = 14
        self.pass_band: float = 0.001
        self.feature_angle: float = 120.0
        self.femur_mesh = None
        self.downsampling_ratio: float = downsampling_ratio

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

    parser.add_argument('--visualise', action='store_true', help="Do you want to visualise the surfaces, "
                                                                            "True or False?")
    parser.set_defaults(visualise=False)
    parser.add_argument("--pointcloud_data_dir", type=str, default='~/.config',
                        help="Directory where you are storing the produced pointcloud files.")
    parser.add_argument("--downsampling_ratio", type=float, default='0.25',
                        help="Femur mesh downsampling ratio, from 0 to 1, where 1 equates to no downsampling.")

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    if args.downsampling_ratio <= 0.0 or args.downsampling_ratio > 1.0:
        raise argparse.ArgumentTypeError("Mesh downsampling ratio must be a float larger than 0 and no bigger than 1.")

    return args


def load_data(data_dir: str, visualise: bool, pointcloud_dir: str, downsampling_ratio: float):
    load_femur_bone(data_dir, visualise, pointcloud_dir, downsampling_ratio)
    # load_tibia_bone()
    # load_femur_cartilage()
    # load_tibia_cartilage()


def load_femur_bone(data_dir: str, visualise: bool, pointcloud_dir: str, downsampling_ratio: float):
    count: int = 0
    file_header: str = "femur_bone_"

    for filename in os.listdir(data_dir):
        if filename.endswith(".mhd") and count < 2:
            count += 1
            femur_id: str = filename[0:7]

            femur_surface = FemurSurface(data_dir, filename, downsampling_ratio)
            femur_surface.generate_smoothed_surface()
            femur_surface.downsample_vertices()
            if count == 1 and visualise:
                femur_surface.visualise_surface()

            pointcloud = femur_surface.get_surface().points()
            os.chdir(pointcloud_dir)
            pointcloud.tofile(file_header + "cloud_" + femur_id)


def main(argv):
    """Main function"""

    print('Application started')

    args = __parse_arguments()
    data_dir: str = args.segmented_data_dir
    visualise: bool = args.visualise
    pointcloud_dir: str = args.pointcloud_data_dir
    downsampling_ratio: float = args.downsampling_ratio

    data_dir = "/home/aitor/src/FemurPrediction/OAI-Data"
    pointcloud_dir = "/home/aitor/src/FemurPrediction/SmoothPointclouds"
    visualise = False
    downsampling_ratio = 0.25

    load_femur_bone(data_dir, visualise, pointcloud_dir, downsampling_ratio)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
