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

# export PYTHONPATH="${PYTHONPATH}<path to kicad-footprint-generator directory>"
sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))  # load parent path of KicadModTree
import argparse
import yaml
from helpers import *
from KicadModTree import *
from math import sqrt

sys.path.append(os.path.join(sys.path[0], "..", "..", "tools"))  # load parent path of tools
from footprint_text_fields import addTextFields

series = "J2100"
manufacturer = 'JST'
orientation = 'H'
number_of_rows = 2
datasheet = 'http://www.jst-mfg.com/product/pdf/eng/eJFA-J2000.pdf'

pitch = 2.50

pin_range = [3,4,5,6,8,10] #number of pins in each row
row_pitch = 2.50

#FP name strings
part_base = "S{n:02}B-J21DK-GG" #JST part number format string

drill = 0.86 # 0.85 -0.03/+0.05 -> 0.86 +/-0.04
mh_drill = 2
mh_size = 3.4
pad_to_pad_clearance = 0.8
pad_copper_y_solder_length = 0.5
min_annular_ring = 0.15

def generatePadNumber(row_idx, pin_idx):
    row_name=['a','b']
    return '{:s}{:d}'.format(row_name[row_idx-1],pin_idx)
    #return 2*pin_idx if row_idx==2 else 2*pin_idx-1

#FP description and tags

def generate_one_footprint(pins, configuration):
    #calculate fp dimensions
    A = (pins - 1) * pitch
    B = A + 5.2

    #generate the name
    mpn = part_base.format(n=number_of_rows*pins)
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pins, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    kicad_mod = Footprint(footprint_name)
    kicad_mod.setDescription("JST {:s} series connector, {:s} ({:s}), generated with kicad-footprint-generator".format(series, mpn, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))


    pad_size = [pitch - pad_to_pad_clearance, row_pitch - pad_to_pad_clearance]
    if pad_size[0] - drill < 2*min_annular_ring:
        pad_size[0] = drill + 2*min_annular_ring

    if pad_size[1] - drill > 2*pad_copper_y_solder_length:
        pad_size[1] = drill + 2*pad_copper_y_solder_length
    if pad_size[1] - drill < 2*min_annular_ring:
        pad_size[1] = drill + 2*min_annular_ring

    for row_idx in range(1,3):
        for pin_idx in range(1,pins+1):
            shape=Pad.SHAPE_RECT if row_idx == 1 and pin_idx == 1 else Pad.SHAPE_CIRCLE
            position = [(pin_idx-1)*pitch, -(row_idx-1)*row_pitch]
            pad_num = generatePadNumber(row_idx, pin_idx)
            kicad_mod.append(Pad(number=pad_num, type=Pad.TYPE_THT, shape=shape,
                                 at=position, size=pad_size,
                                 drill=drill, layers=Pad.LAYERS_THT))
    # pa1 = PadArray(pincount=pins, x_spacing=pitch, type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, increment=2, size=1.6, drill=0.9, layers=['*.Cu','*.Mask'])
    # pa2 = PadArray(pincount=pins, x_spacing=pitch, type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, start=[0,-row_pitch], initial=2, increment=2, size=1.6, drill=0.9, layers=['*.Cu','*.Mask'])

    # kicad_mod.append(pa1)
    # kicad_mod.append(pa2)

    #draw the component outline
    x1 = A/2 - B/2
    x2 = x1 + B
    y1 = -2.5 - 0.62
    y2 = y1 + 17.8
    body_edge={'left':x1, 'right':x2, 'top':y1, 'bottom':y2}

    #draw the main outline around the footprint
    kicad_mod.append(RectLine(start=[x1,y1], end=[x2,y2], layer='F.Fab', width=configuration['fab_line_width']))

    ########################### CrtYd #################################
    cx1 = roundToBase(x1-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    if y1 < -row_pitch - pad_size[1]/2:
        cy1 = roundToBase(y1-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    else:
        cy1 = roundToBase(-row_pitch - pad_size[1]/2-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])


    cx2 = roundToBase(x2+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy2 = roundToBase(y2+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    kicad_mod.append(RectLine(
        start=[cx1, cy1], end=[cx2, cy2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    #offset off
    off = configuration['silk_fab_offset']

    x1 -= off
    y1 -= off
    x2 += off
    y2 += off

    #outline
    side = [
    {'x': -1,'y': y1},
    {'x': x1,'y': y1},
    {'x': x1,'y': y2},
    {'x': A/2,'y': y2},
    ]

    kicad_mod.append(PolygoneLine(polygone=side, layer="F.SilkS", width=configuration['silk_line_width']))
    kicad_mod.append(PolygoneLine(polygone=side, x_mirror=A/2, layer="F.SilkS", width=configuration['silk_line_width']))

    #add mounting holes
    if pins == 3:
        m = Pad(at=[pitch,7],layers=["*.Cu","*.Mask"],shape=Pad.SHAPE_CIRCLE,type=Pad.TYPE_THT,size=mh_size,drill=mh_drill)
        kicad_mod.append(m)
    else:
        m1 = Pad(at=[0,7],layers=["*.Cu",'*.Mask'],shape=Pad.SHAPE_CIRCLE,type=Pad.TYPE_THT,size=mh_size,drill=mh_drill)
        m2 = Pad(at=[A,7],layers=["*.Cu",'*.Mask'],shape=Pad.SHAPE_CIRCLE,type=Pad.TYPE_THT,size=mh_size,drill=mh_drill)

        kicad_mod.append(m1)
        kicad_mod.append(m2)

    #add p1 marker
    px = -3
    m = 0.3

    marker = [
    {'x': px,'y': 0},
    {'x': px-2*m,'y': m},
    {'x': px-2*m,'y': -m},
    {'x': px,'y': 0},
    ]

    kicad_mod.append(PolygoneLine(polygone=marker, layer="F.SilkS", width=configuration['silk_line_width']))

    sl = 1
    marker = [
        {'x': body_edge['left'],'y': sl/2},
        {'x': body_edge['left'] +sl/sqrt(2),'y': 0},
        {'x': body_edge['left'],'y': -sl/2}
    ]
    kicad_mod.append(PolygoneLine(polygone=marker, layer='F.Fab', width=configuration['fab_line_width']))

    ######################### Text Fields ###############################
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':cy1, 'bottom':cy2}, fp_name=footprint_name, text_y_inside_position='center')

    ##################### Output and 3d model ############################
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

    for pins_per_row in pin_range:
        generate_one_footprint(pins_per_row, configuration)
