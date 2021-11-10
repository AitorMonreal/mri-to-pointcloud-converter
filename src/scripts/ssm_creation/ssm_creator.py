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
import vtkplotter

# OS
import os

# SYS
import sys


class FemurSurface(object):
    def __init__(self, data_dir: str, femur_id: str):
        self.femur_id = femur_id
        self.femur_surface = self.read_mhd_file(data_dir)

    def read_mhd_file(self, data_dir: str):
        mhd_file_path: str = data_dir + "/" + self.femur_id
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName(mhd_file_path)
        reader.Update()
        return reader

    def generate_smoothed_surface(self):
        self.generate_marching_cubes()
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
        smoother.SetInput(self.femur_surface.GetOutput())
        smoother.BoundarySmoothingOn()
        smoother.SetNumberOfIterations(40)
        smoother.Update()
        self.femur_surface = smoother.GetOutput()

    def visualise_surface(self):
        # create the outline of the data as polygonal mesh and show it
        vtkplotter.Mesh(self.femur_surface).c('viridis').alpha(1.0).show()


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


def load_femur_bone(data_dir: str):
    for filename in os.listdir(data_dir):
        if filename.endswith(".mhd"):
            femur_surface = FemurSurface(data_dir, filename)

            reader = read_mhd_file(filename, data_dir)

            # Discrete Marching Cubes
            dmc = vtk.vtkDiscreteMarchingCubes()
            dmc.SetInputConnection(reader.GetOutputPort())
            dmc.GenerateValues(1, 1, 1)
            dmc.Update()

            marching_cubes_surface = perform_marching_cubes(reader)

            smoothed_surface = smooth_surface(marching_cubes_surface)
            discrete_smoothed_surface = smooth_surface(dmc)

            visualise_surface(discrete_smoothed_surface)


def read_mhd_file(filename: str, data_dir: str):
    file_id: str = filename[0:7]
    mhd_file_path: str = data_dir + "/" + filename
    reader = vtk.vtkMetaImageReader()
    reader.SetFileName(mhd_file_path)
    reader.Update()
    return reader


def perform_marching_cubes(reader):
    marching_cubes = vtk.vtkMarchingCubes()
    marching_cubes.SetInputConnection(reader.GetOutputPort())
    marching_cubes.GenerateValues(1, 1, 1)
    marching_cubes.Update()
    return marching_cubes


def smooth_surface(surface) -> vtk.vtkWindowedSincPolyDataFilter:
    smoother = vtk.vtkWindowedSincPolyDataFilter()
    smoother.SetInput(surface.GetOutput())
    smoother.BoundarySmoothingOn()
    smoother.SetNumberOfIterations(40)
    smoother.Update()
    return smoother.GetOutput()


def visualise_surface(surface):
    # create the outline of the data as polygonal mesh and show it
    vtkplotter.Mesh(surface).c('viridis').alpha(1.0).show()


def main(argv):
    """Main function"""

    print('Application started')

    args = __parse_arguments()
    data_dir: str = args.segmented_data_dir
    visualise: bool = args.visualise

    data_dir = ""
    for filename in os.listdir(data_dir):
        if filename.endswith(".mhd"):
            break;
    femur_id = filename[0:7]
    femur_surface = FemurSurface(data_dir, femur_id)
    femur_surface.generate_smoothed_surface()
    femur_surface.visualise_surface()


if __name__ == "__main__":
    main(sys.argv)
