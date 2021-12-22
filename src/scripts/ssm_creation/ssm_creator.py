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

# VTK
import vtk
from vedo import *

# OS
import os

# SYS
import sys


class FemurSurface(object):
    def __init__(self, data_dir: str, filename: str):
        self.filename = filename
        self.femur_surface = self.read_mhd_file(data_dir)
        self.smoothing_iterations = 14
        self.pass_band = 0.001
        self.feature_angle = 120.0

    def read_mhd_file(self, data_dir: str):
        mhd_file_path: str = data_dir + "/" + self.filename
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName(mhd_file_path)
        reader.Update()
        return reader

    def generate_smoothed_surface(self):
        self.generate_discrete_marching_cubes()
        self.smooth_surface()

    def generate_marching_cubes(self):
        marching_cubes = vtk.vtkMarchingCubes()
        marching_cubes.SetInputConnection(self.femur_surface.GetOutputPort())
        marching_cubes.GenerateValues(1, 1, 1)
        marching_cubes.Update()
        self.femur_surface = marching_cubes

    def generate_discrete_marching_cubes(self):
        discrete_marching_cubes = vtk.vtkDiscreteMarchingCubes()
        discrete_marching_cubes.SetInputConnection(self.femur_surface.GetOutputPort())
        discrete_marching_cubes.GenerateValues(1, 1, 1)
        discrete_marching_cubes.Update()
        self.femur_surface = discrete_marching_cubes

    def smooth_surface(self):
        smoother = vtk.vtkWindowedSincPolyDataFilter()
        smoother.SetInputConnection(self.femur_surface.GetOutputPort())
        smoother.SetNumberOfIterations(self.smoothing_iterations)
        smoother.SetFeatureAngle(self.feature_angle)
        smoother.SetPassBand(self.pass_band)
        smoother.BoundarySmoothingOff()
        smoother.FeatureEdgeSmoothingOff()
        smoother.NonManifoldSmoothingOn()
        smoother.NormalizeCoordinatesOn()
        smoother.Update()
        self.femur_surface = smoother.GetOutput()

    def visualise_surface(self):
        # create the outline of the data as polygonal mesh and show it
        Mesh(self.femur_surface).show()

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


def load_femur_bone(data_dir: str, visualise: bool):
    count: int = 0
    for filename in os.listdir(data_dir):
        if filename.endswith(".mhd") and count < 1:
            count += 1
            femur_id: str = filename[0:7]

            femur_surface = FemurSurface(data_dir, filename)
            femur_surface.generate_smoothed_surface()
            if visualise:
                femur_surface.visualise_surface()


def main(argv):
    """Main function"""

    print('Application started')

    args = __parse_arguments()
    data_dir: str = args.segmented_data_dir
    visualise: bool = args.visualise

    data_dir = "/home/aitor/src/FemurPrediction/OAI-Data"
    visualise = True

    load_femur_bone(data_dir, visualise)


if __name__ == "__main__":
    main(sys.argv)
