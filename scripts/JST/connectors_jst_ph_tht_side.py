#!/usr/bin/env python

import sys
import os
#sys.path.append(os.path.join(sys.path[0],"..","..","kicad_mod")) # load kicad_mod path

# export PYTHONPATH="${PYTHONPATH}<path to kicad-footprint-generator directory>"
sys.path.append(os.path.join(sys.path[0], "..", ".."))  # load parent path of KicadModTree
import argparse
import yaml
from helpers import *
from KicadModTree import *

series = "PH"
orientation = 'Horizontal'
number_of_rows = 1
datasheet = 'http://www.jst-mfg.com/product/pdf/eng/ePH.pdf'

silk_pin1_marker_type = 2
fab_pin1_marker_type = 3

pad_size=[1.2, 1.7]
drill_size = 0.75 #Datasheet: 0.7 +0.1/-0.0 => It might be better to assume 0.75 +/-0.05mm

pitch = 2.00

# Connector Parameters
silk_to_part_offset = 0.1
x_min = -1.95
y_max = 6.25
y_min = y_max-6-1.6
y_main_min = y_max - 6

body_back_protrusion_width=0.7

silk_x_min = x_min - silk_to_part_offset
silk_y_min = y_min - silk_to_part_offset
silk_y_main_min = y_main_min - silk_to_part_offset
silk_y_max = y_max + silk_to_part_offset

def generate_one_footprint(pincount, configuration):
    x_mid = (pincount-1)*pitch/2.0
    x_max = (pincount-1)*pitch + 1.95
    silk_x_max = x_max + silk_to_part_offset

    # Through-hole type shrouded header, Side entry type
    part = "S{n}B-PH-K".format(n=pincount) #JST part number format string
    footprint_name = configuration['fp_name_format_string'].format(series=series, mpn=part, num_rows=number_of_rows,
        pins_per_row=pincount, pitch=pitch, orientation=orientation)

    kicad_mod = Footprint(footprint_name)
    description = "JST PH series connector, " + part + ", side entry type, through hole, Datasheet: http://www.jst-mfg.com/product/pdf/eng/ePH.pdf"
    kicad_mod.setDescription(description)
    kicad_mod.setTags('connector jst ph')

    # create Silkscreen
    tmp_x1=x_min+body_back_protrusion_width+silk_to_part_offset
    tmp_x2=x_max-body_back_protrusion_width-silk_to_part_offset
    poly_silk_outline= [
                    {'x':-pad_size[0]/2.0-configuration['silk_pad_clearence'], 'y':silk_y_main_min},
                    {'x':tmp_x1, 'y':silk_y_main_min},
                    {'x':tmp_x1, 'y':silk_y_min},
                    {'x':silk_x_min, 'y':silk_y_min},
                    {'x':silk_x_min, 'y':silk_y_max},
                    {'x':silk_x_max, 'y':silk_y_max},
                    {'x':silk_x_max, 'y':silk_y_min},
                    {'x':tmp_x2, 'y':silk_y_min},
                    {'x':tmp_x2, 'y':silk_y_main_min},
                    {'x':(pincount-1)*pitch+pad_size[0]/2.0+configuration['silk_pad_clearence'], 'y':silk_y_main_min}
    ]
    kicad_mod.append(PolygoneLine(polygone=poly_silk_outline, layer='F.SilkS', width=configuration['silk_line_width']))

    if configuration['allow_silk_below_part'] == 'tht' or configuration['allow_silk_below_part'] == 'both':
        poly_big_cutout=[{'x':0.5, 'y':silk_y_max}
                                  ,{'x':0.5, 'y':2}
                                  ,{'x':x_max-2.45, 'y':2}
                                  ,{'x':x_max-2.45, 'y':silk_y_max}]
        kicad_mod.append(PolygoneLine(polygone=poly_big_cutout, layer='F.SilkS', width=configuration['silk_line_width']))

        kicad_mod.append(Line(start=[silk_x_min, silk_y_main_min], end=[tmp_x1, silk_y_main_min], layer='F.SilkS', width=configuration['silk_line_width']))
        kicad_mod.append(Line(start=[silk_x_max, silk_y_main_min], end=[tmp_x2, silk_y_main_min], layer='F.SilkS', width=configuration['silk_line_width']))

        kicad_mod.append(RectLine(start=[-1.3, 2.5], end=[-0.3, 4.1],
            layer='F.SilkS', width=configuration['silk_line_width']))
        kicad_mod.append(RectLine(start=[(pincount-1)*pitch+1.3, 2.5], end=[(pincount-1)*pitch+0.3, 4.1],
            layer='F.SilkS', width=configuration['silk_line_width']))

        kicad_mod.append(Line(start=[-0.3, 4.1], end=[-0.3, silk_y_max],
            layer='F.SilkS', width=configuration['silk_line_width']))
        kicad_mod.append(Line(start=[-0.8, 4.1], end=[-0.8, silk_y_max],
            layer='F.SilkS', width=configuration['silk_line_width']))

    # create Courtyard
    part_x_min = x_min
    part_x_max = x_max
    part_y_min = y_min
    part_y_max = y_max

    cx1 = roundToBase(part_x_min-configuration['courtyard_distance'], configuration['courtyard_grid'])
    cy1 = roundToBase(part_y_min-configuration['courtyard_distance'], configuration['courtyard_grid'])

    cx2 = roundToBase(part_x_max+configuration['courtyard_distance'], configuration['courtyard_grid'])
    cy2 = roundToBase(part_y_max+configuration['courtyard_distance'], configuration['courtyard_grid'])

    kicad_mod.append(RectLine(
        start=[cx1, cy1], end=[cx2, cy2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    # Fab layer outline
    tmp_x1=x_min+body_back_protrusion_width
    tmp_x2=x_max-body_back_protrusion_width
    poly_fab_outline= [
                    {'x':tmp_x1, 'y':y_main_min},
                    {'x':tmp_x1, 'y':y_min},
                    {'x':x_min, 'y':y_min},
                    {'x':x_min, 'y':y_max},
                    {'x':x_max, 'y':y_max},
                    {'x':x_max, 'y':y_min},
                    {'x':tmp_x2, 'y':y_min},
                    {'x':tmp_x2, 'y':y_main_min},
                    {'x':tmp_x1, 'y':y_main_min}
    ]
    kicad_mod.append(PolygoneLine(polygone=poly_fab_outline, layer='F.Fab', width=configuration['fab_line_width']))

    # create pads
    #add the pads
    kicad_mod.append(Pad(number=1, type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
                        at=[0, 0], size=pad_size,
                        drill=drill_size, layers=Pad.LAYERS_THT))
    for p in range(1, pincount):
        Y = 0
        X = p * pitch

        num = p+1
        kicad_mod.append(Pad(number=num, type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL,
                            at=[X, Y], size=pad_size,
                            drill=drill_size, layers=Pad.LAYERS_THT))


    # pin 1 marker
    poly_pin1_marker = [
        {'x':0, 'y':-1.2},
        {'x':-0.4, 'y':-1.6},
        {'x':0.4, 'y':-1.6},
        {'x':0, 'y':-1.2}
    ]
    if silk_pin1_marker_type == 1:
        kicad_mod.append(PolygoneLine(polygone=poly_pin1_marker, layer='F.SilkS', width=configuration['silk_line_width']))
    if silk_pin1_marker_type == 2:
        silk_pin1_marker_t2_x = -pad_size[0]/2.0-configuration['silk_pad_clearence']

        kicad_mod.append(Line(start=[silk_pin1_marker_t2_x, silk_y_main_min],
            end=[silk_pin1_marker_t2_x, -pad_size[1]/2.0-configuration['silk_pad_clearence']],layer='F.SilkS', width=configuration['silk_line_width']))

    if fab_pin1_marker_type == 1:
        kicad_mod.append(PolygoneLine(polygone=poly_pin1_marker, layer='F.Fab', width=configuration['fab_line_width']))

    if fab_pin1_marker_type == 2:
        poly_pin1_marker_type2 = [
            {'x':-0.75, 'y':y_main_min},
            {'x':0, 'y':y_main_min+0.75},
            {'x':0.75, 'y':y_main_min}
        ]
        kicad_mod.append(PolygoneLine(polygone=poly_pin1_marker_type2, layer='F.Fab', width=configuration['fab_line_width']))

    if fab_pin1_marker_type == 3:
        fab_pin1_marker_t3_y = pad_size[1]/2.0
        poly_pin1_marker_type2 = [
            {'x':0, 'y':fab_pin1_marker_t3_y},
            {'x':-0.5, 'y':fab_pin1_marker_t3_y+0.5},
            {'x':0.5, 'y':fab_pin1_marker_t3_y+0.5},
            {'x':0, 'y':fab_pin1_marker_t3_y}
        ]
        kicad_mod.append(PolygoneLine(polygone=poly_pin1_marker_type2, layer='F.Fab', width=configuration['fab_line_width']))

    center = [(part_x_min + part_x_max)/2, 2.5]
    reference_fields = configuration['references']
    kicad_mod.append(Text(type='reference', text='REF**',
        **getTextFieldDetails(reference_fields[0], cy1, cy2, center)))

    for additional_ref in reference_fields[1:]:
        kicad_mod.append(Text(type='user', text='%R',
        **getTextFieldDetails(additional_ref, cy1, cy2, center)))

    value_fields = configuration['values']
    kicad_mod.append(Text(type='value', text=footprint_name,
        **getTextFieldDetails(value_fields[0], cy1, cy2, center)))

    for additional_value in value_fields[1:]:
        kicad_mod.append(Text(type='user', text='%V',
            **getTextFieldDetails(additional_value, cy1, cy2, center)))

    model3d_path_prefix = configuration.get('3d_model_prefix','${KISYS3DMOD}')

    lib_name = configuration['lib_name_format_string'].format(series=series)
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
    parser.add_argument('-c', '--config', type=str, nargs='?', help='the config file defining how the footprint will look like.', default='config_KLCv3.0.yaml')
    args = parser.parse_args()

    with open(args.config, 'r') as config_stream:
        try:
            configuration = yaml.load(config_stream)
        except yaml.YAMLError as exc:
            print(exc)

    for pincount in range(2,17):
        generate_one_footprint(pincount, configuration)
