#!/usr/bin/env python3

'''
kicad-footprint-generator is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

kicad-footprint-generator is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with kicad-footprint-generator. If not, see < http://www.gnu.org/licenses/ >.
'''

import sys
import os
#sys.path.append(os.path.join(sys.path[0],"..","..","kicad_mod")) # load kicad_mod path

# export PYTHONPATH="${PYTHONPATH}<path to kicad-footprint-generator directory>"
sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))  # load parent path of KicadModTree
from math import sqrt
import argparse
import yaml
from helpers import *
from KicadModTree import *

sys.path.append(os.path.join(sys.path[0], "..", "..", "tools"))  # load parent path of tools
from footprint_text_fields import addTextFields

series = "DF12C"
series_long = 'DF12C SMD'
manufacturer = 'Hirose'
orientation = 'V'
number_of_rows = 2
datasheet = 'ola'

#Molex part number
#n = number of circuits per row
part_code = "43045-{n:02}00"

pitch = 0.5

#pins_per_row_range = range(1,13)
pins_per_row_range = [10,14,20,30,32,36,40,50,60,80]

def generate_one_footprint(idx, pins, configuration):
    pins_per_row = pins

    mpn = part_code.format(n=pins*2)

    # handle arguments
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pins_per_row, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    kicad_mod = Footprint(footprint_name)
    kicad_mod.setAttribute('smd')
    kicad_mod.setDescription("Hirose {:s}, {:s}, {:d} Pins per row ({:s}), generated with kicad-footprint-generator".format(series_long, mpn, pins_per_row, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))

    ########################## Dimensions ##############################

    A = 4.6 + (idx * 2.5)

    body_edge={
        'left': -A / 2,
        'right': A / 2,
        'top': -2.3,
        'bottom': 2.3
        }

    ############################# Pads ##################################
    #
    # Add pads
    #
    #kicad_mod.append(PadArray(start=[pad1_x, pad_row_1_y], initial=1,
    #    pincount=pins_per_row, increment=1,  x_spacing=pitch, size=pad_size,
    #    type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, layers=Pad.LAYERS_THT, drill=drill))

    #kicad_mod.append(PadArray(start=[pad1_x, pad_row_2_y], initial=pins_per_row+1,
    #    pincount=pins_per_row, increment=1, x_spacing=pitch, size=pad_size,
    #    type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, layers=Pad.LAYERS_THT, drill=drill))

    ######################## Fabrication Layer ###########################
    main_body_poly= [
        {'x': body_edge['left'], 'y': body_edge['bottom']},
        {'x': body_edge['left'], 'y': body_edge['top']},
        {'x': body_edge['right'], 'y': body_edge['top']},
        {'x': body_edge['right'], 'y': body_edge['bottom']},
        {'x': body_edge['left'], 'y': body_edge['bottom']}
    ]
    kicad_mod.append(PolygoneLine(polygone=main_body_poly,
        width=configuration['fab_line_width'], layer="F.Fab"))

    #main_arrow_poly= [
    #    {'x': -.75, 'y': body_edge['bottom']},
    #    {'x': 0, 'y': 0},
    #    {'x': 0.75, 'y': body_edge['bottom']}
    #]
    #kicad_mod.append(PolygoneLine(polygone=main_arrow_poly,
    #    width=configuration['fab_line_width'], layer="F.Fab"))

    ######################## SilkS Layer ###########################
    #poly_s_t= [
    #    {'x': body_edge['left'] - configuration['silk_fab_offset'], 'y': body_edge['bottom'] + configuration['silk_fab_offset']},
    #    {'x': body_edge['left'] - configuration['silk_fab_offset'], 'y': body_edge['top'] + 1 - configuration['silk_fab_offset']},
    #    {'x': body_edge['left'] + 1 - configuration['silk_fab_offset'], 'y': body_edge['top'] - configuration['silk_fab_offset']},
    #    {'x': body_edge['right'] - 1 + configuration['silk_fab_offset'], 'y': body_edge['top'] - configuration['silk_fab_offset']},
    #    {'x': body_edge['right'] + configuration['silk_fab_offset'], 'y': body_edge['top'] + 1 - configuration['silk_fab_offset']},
    #    {'x': body_edge['right']+ configuration['silk_fab_offset'], 'y': body_edge['bottom'] + configuration['silk_fab_offset']},
    #    {'x': body_edge['left'] - configuration['silk_fab_offset'], 'y': body_edge['bottom'] + configuration['silk_fab_offset']},
    #]
    #kicad_mod.append(PolygoneLine(polygone=poly_s_t,
    #    width=configuration['silk_line_width'], layer="F.SilkS"))

    ######################## CrtYd Layer ###########################
    #CrtYd_offset = configuration['courtyard_offset']['connector']
    #CrtYd_grid = configuration['courtyard_grid']

    #poly_yd = [
    #    {'x': roundToBase(body_edge['left'] - CrtYd_offset, CrtYd_grid), 'y': roundToBase(body_edge['bottom'] + CrtYd_offset, CrtYd_grid)},
    #    {'x': roundToBase(body_edge['left'] - CrtYd_offset, CrtYd_grid), 'y': roundToBase(body_edge['top'] - CrtYd_offset, CrtYd_grid)},
    #    {'x': roundToBase(body_edge['right'] + CrtYd_offset, CrtYd_grid), 'y': roundToBase(body_edge['top'] - CrtYd_offset, CrtYd_grid)},
    #    {'x': roundToBase(body_edge['right'] + CrtYd_offset, CrtYd_grid), 'y': roundToBase(body_edge['bottom'] + CrtYd_offset, CrtYd_grid)},
    #    {'x': roundToBase(B + pad_to_pad_clearance/2 + CrtYd_offset, CrtYd_grid), 'y': roundToBase(body_edge['bottom'] + CrtYd_offset, CrtYd_grid)},
    #    {'x': roundToBase(B + pad_to_pad_clearance/2 + CrtYd_offset, CrtYd_grid), 'y': roundToBase(pitch + pad_to_pad_clearance/2 + CrtYd_offset, CrtYd_grid)},
    #    {'x': roundToBase(- pad_to_pad_clearance/2 - CrtYd_offset, CrtYd_grid), 'y': roundToBase(pitch + pad_to_pad_clearance/2 + CrtYd_offset, CrtYd_grid)},
    #    {'x': roundToBase(- pad_to_pad_clearance/2 - CrtYd_offset, CrtYd_grid), 'y': roundToBase(body_edge['bottom'] + CrtYd_offset, CrtYd_grid)},
    #    {'x': roundToBase(body_edge['left'] - CrtYd_offset, CrtYd_grid), 'y': roundToBase(body_edge['bottom'] + CrtYd_offset, CrtYd_grid)}
    #]

    #kicad_mod.append(PolygoneLine(polygone=poly_yd,
    #    layer='F.CrtYd', width=configuration['courtyard_line_width']))

    ######################### Text Fields ###############################
    #cy1 = roundToBase(body_edge['top'] - configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    #cy2 = roundToBase(pad_row_2_y + pad_size[1] + configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    #addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
    #    courtyard={'top':cy1, 'bottom':cy2}, fp_name=footprint_name, text_y_inside_position='top')

    ##################### Write to File and 3D ############################
    model3d_path_prefix = configuration.get('3d_model_prefix','${KISYS3DMOD}/')

    lib_name = configuration['lib_name_format_string'].format(series=series, man=manufacturer)
    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}.wrl'.format(
        model3d_path_prefix=model3d_path_prefix, lib_name=lib_name, fp_name=footprint_name)
    kicad_mod.append(Model(filename=model_name))

    output_dir = '{lib_name:s}.pretty/'.format(lib_name=lib_name)
    if not os.path.isdir(output_dir): #returns false if path does not yet exist!! (Does not check path validity)
        os.makedirs(output_dir)
    filename =  '{outdir:s}{fp_name:s}.kicad_mod'.format(outdir=output_dir, fp_name=footprint_name)

    file_handler = KicadFileHandler(kicad_mod)
    file_handler.writeFile(filename)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='use confing .yaml files to create footprints.')
    parser.add_argument('--global_config', type=str, nargs='?', help='the config file defining how the footprint will look like. (KLC)', default='../../tools/global_config_files/config_KLCv3.0.yaml')
    parser.add_argument('--series_config', type=str, nargs='?', help='the config file defining series parameters.', default='../conn_config_KLCv3.yaml')
    args = parser.parse_args()

    with open(args.global_config, 'r') as config_stream:
        try:
            configuration = yaml.load(config_stream)
        except yaml.YAMLError as exc:
            print(exc)

    with open(args.series_config, 'r') as config_stream:
        try:
            configuration.update(yaml.load(config_stream))
        except yaml.YAMLError as exc:
            print(exc)

    idx = 0
    for pincount in pins_per_row_range:
        generate_one_footprint(idx, pincount, configuration)
        idx += 1
