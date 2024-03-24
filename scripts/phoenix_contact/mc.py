#!/usr/bin/env python

import sys
import os
from helpers import *
import re
import fnmatch
import argparse
import yaml

from options_manager import OptionManager

#sys.path.append(os.path.join(sys.path[0],"..","..")) # load KicadModTree path
#add KicadModTree to searchpath using export PYTHONPATH="${PYTHONPATH}<absolute path>/kicad-footprint-generator/"
from KicadModTree import *

from mc_params import seriesParams, dimensions, generate_description, all_params

series = ['MC', '1,5']

def generate_one_footprint(motel, params, configuration):

    # Through-hole type shrouded header, Top entry type
    subseries, connector_style = params.series_name.split('-')
    pitch_mpn = '-{:g}'.format(params.pin_pitch)
    lib_name = configuration['lib_name_format_str'].format(series=series[0], style=series[1], pitch=params.pin_pitch)
    mpn = configuration['mpn_format_string'].format(subseries=subseries, style = connector_style,
        rating=series[1], num_pins=params.num_pins, pitch=pitch_mpn)
    footprint_name = configuration['fp_name_format_string'].format(man = configuration['manufacturer'],
        series = series[0], mpn = mpn, num_rows = 1,
        num_pins = params.num_pins, pitch = params.pin_pitch,
        orientation = configuration['orientation_str'][1] if params.angled else configuration['orientation_str'][0],
        flanged = configuration['flanged_str'][1] if params.flanged else configuration['flanged_str'][0],
        mount_hole = configuration['mount_hole_str'][1] if params.mount_hole else configuration['mount_hole_str'][0])

    calc_dim = dimensions(params)

    body_top_left=[calc_dim.left_to_pin,params.back_to_pin]
    body_bottom_right=v_add(body_top_left,[calc_dim.length,calc_dim.width])
    silk_top_left=v_offset(body_top_left, configuration['silk_body_offset'])
    silk_bottom_right=v_offset(body_bottom_right, configuration['silk_body_offset'])
    center_x = (params.num_pins-1)/2.0*params.pin_pitch
    kicad_mod = Footprint(footprint_name)


    kicad_mod.setDescription(generate_description(params))
    kicad_mod.setTags(configuration['keywords_format_string'].format(mpn=mpn, param_name=model,
        order_info = ', '.join(params.order_info)))

    #add the pads
    kicad_mod.append(Pad(number=1, type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
                        at=[0, 0], size=[params.pin_Sx, params.pin_Sy], \
                        drill=seriesParams.drill, layers=configuration['pin_layers']))
    for p in range(1,params.num_pins):
        Y = 0
        X = p * params.pin_pitch

        num = p+1
        kicad_mod.append(Pad(number=num, type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL,
                            at=[X, Y], size=[params.pin_Sx, params.pin_Sy], \
                            drill=seriesParams.drill, layers=configuration['pin_layers']))
    if params.mount_hole:
        kicad_mod.append(Pad(number='""', type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE,
                            at=calc_dim.mount_hole_left, size=[seriesParams.mount_drill, seriesParams.mount_drill], \
                            drill=seriesParams.mount_drill, layers=configuration['mount_hole_layers']))
        kicad_mod.append(Pad(number='""', type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE,
                            at=calc_dim.mount_hole_right, size=[seriesParams.mount_drill, seriesParams.mount_drill], \
                            drill=seriesParams.mount_drill, layers=configuration['mount_hole_layers']))
    #add an outline around the pins

    # create silscreen


    if params.angled:
        #kicad_mod.append(RectLine(start=silk_top_left, end=silk_bottom_right, layer='F.SilkS'))
        silkGab = params.pin_Sx/2.0+seriesParams.silk_pad_clearence
        kicad_mod.append(Line(start=silk_top_left, end=[silk_top_left[0], silk_bottom_right[1]], layer='F.SilkS', width=configuration['silk_line_width']))
        kicad_mod.append(Line(start=[silk_top_left[0], silk_bottom_right[1]], end=silk_bottom_right, layer='F.SilkS', width=configuration['silk_line_width']))
        kicad_mod.append(Line(start=silk_bottom_right, end=[silk_bottom_right[0], silk_top_left[1]], layer='F.SilkS', width=configuration['silk_line_width']))

        kicad_mod.append(Line(start=silk_top_left, end=[-silkGab, silk_top_left[1]], layer='F.SilkS', width=configuration['silk_line_width']))
        kicad_mod.append(Line(start=[silk_bottom_right[0], silk_top_left[1]], end=[(params.num_pins-1)*params.pin_pitch+silkGab, silk_top_left[1]],\
                        layer='F.SilkS', width=configuration['silk_line_width']))

        for p in range(params.num_pins-1):
            kicad_mod.append(Line(start=[p*params.pin_pitch+silkGab, silk_top_left[1]], \
                            end=[(p+1)*params.pin_pitch-silkGab, silk_top_left[1]], layer='F.SilkS', width=configuration['silk_line_width']))

        if configuration['with_fab_layer']:
            kicad_mod.append(RectLine(start=body_top_left, end=body_bottom_right, layer='F.Fab', width=configuration['fab_line_width']))

        left = silk_top_left[0] + (seriesParams.flange_lenght if params.flanged else 0)
        right = silk_bottom_right[0] - (seriesParams.flange_lenght if params.flanged else 0)
        scoreline_y = seriesParams.scoreline_from_back+params.back_to_pin
        kicad_mod.append(Line(start=[left, scoreline_y], end=[right, scoreline_y], layer='F.SilkS', width=configuration['silk_line_width']))
        if configuration['inner_details_on_fab']:
            kicad_mod.append(Line(start=[left +(0 if params.flanged else configuration['silk_body_offset']), scoreline_y],
                end=[right-(0 if params.flanged else configuration['silk_body_offset']), scoreline_y], layer='F.Fab', width=configuration['fab_line_width']))
        if params.flanged:
            kicad_mod.append(Line(start=[left, silk_top_left[1]], end=[left, silk_bottom_right[1]], layer='F.SilkS', width=configuration['silk_line_width']))
            kicad_mod.append(Line(start=[right, silk_top_left[1]], end=[right, silk_bottom_right[1]], layer='F.SilkS', width=configuration['silk_line_width']))
            if configuration['inner_details_on_fab']:
                kicad_mod.append(Line(start=[left, body_top_left[1]], end=[left, body_bottom_right[1]], layer='F.Fab', width=configuration['fab_line_width']))
                kicad_mod.append(Line(start=[right, body_top_left[1]], end=[right, body_bottom_right[1]], layer='F.Fab', width=configuration['fab_line_width']))
    else:
        if not params.flanged:
            kicad_mod.append(RectLine(start=silk_top_left, end=silk_bottom_right, layer='F.SilkS', width=configuration['silk_line_width']))
            if configuration['with_fab_layer']:
                kicad_mod.append(RectLine(start=body_top_left, end=body_bottom_right, layer='F.Fab', width=configuration['fab_line_width']))
        else:
            flange_cutout = calc_dim.width-calc_dim.flange_width
            outline_poly=[
                    {'x':silk_top_left[0], 'y':silk_bottom_right[1]},
                    {'x':silk_bottom_right[0], 'y':silk_bottom_right[1]},
                    {'x':silk_bottom_right[0], 'y':silk_top_left[1]+flange_cutout},
                    {'x':silk_bottom_right[0]-seriesParams.flange_lenght, 'y':silk_top_left[1]+flange_cutout},
                    {'x':silk_bottom_right[0]-seriesParams.flange_lenght, 'y':silk_top_left[1]},
                    {'x':silk_top_left[0]+seriesParams.flange_lenght, 'y':silk_top_left[1]},
                    {'x':silk_top_left[0]+seriesParams.flange_lenght, 'y':silk_top_left[1]+flange_cutout},
                    {'x':silk_top_left[0], 'y':silk_top_left[1]+flange_cutout},
                    {'x':silk_top_left[0], 'y':silk_bottom_right[1]}
                ]
            kicad_mod.append(PolygoneLine(polygone=outline_poly, layer='F.SilkS', width=configuration['silk_line_width']))
            if configuration['with_fab_layer']:
                outline_poly=offset_polyline(outline_poly,-configuration['silk_body_offset'],(center_x,0))
                kicad_mod.append(PolygoneLine(polygone=outline_poly, layer="F.Fab", width=configuration['fab_line_width']))

        if params.flanged:
            kicad_mod.append(Circle(center=calc_dim.mount_hole_left, radius=1.9, layer='F.SilkS', width=configuration['silk_line_width']))
            kicad_mod.append(Circle(center=calc_dim.mount_hole_right, radius=1.9, layer='F.SilkS', width=configuration['silk_line_width']))
            if not params.mount_hole:
                kicad_mod.append(Circle(center=calc_dim.mount_hole_left, radius=1, layer='F.SilkS', width=configuration['silk_line_width']))
                kicad_mod.append(Circle(center=calc_dim.mount_hole_right, radius=1, layer='F.SilkS', width=configuration['silk_line_width']))
            if configuration['inner_details_on_fab']:
                kicad_mod.append(Circle(center=calc_dim.mount_hole_left, radius=1.9, layer='F.Fab', width=configuration['fab_line_width']))
                kicad_mod.append(Circle(center=calc_dim.mount_hole_right, radius=1.9, layer='F.Fab', width=configuration['fab_line_width']))
                kicad_mod.append(Circle(center=calc_dim.mount_hole_left, radius=1, layer='F.Fab', width=configuration['fab_line_width']))
                kicad_mod.append(Circle(center=calc_dim.mount_hole_right, radius=1, layer='F.Fab', width=configuration['fab_line_width']))

        for i in range(params.num_pins):
            plug_outline_translation = Translation(i*params.pin_pitch, 0)
            plug_outline_poly=[
                {'x':-seriesParams.plug_arc_len/2.0, 'y':calc_dim.plug_front},
                {'x':-seriesParams.plug_cut_len/2.0, 'y':calc_dim.plug_front},
                {'x':-seriesParams.plug_cut_len/2.0, 'y':calc_dim.plug_front-seriesParams.plug_cut_width},
                {'x':-seriesParams.plug_seperator_distance/2.0, 'y':calc_dim.plug_front-seriesParams.plug_cut_width},
                {'x':-seriesParams.plug_seperator_distance/2.0, 'y':calc_dim.plug_back+seriesParams.plug_trapezoid_width},
                {'x':-seriesParams.plug_trapezoid_short/2.0, 'y':calc_dim.plug_back+seriesParams.plug_trapezoid_width},
                {'x':-seriesParams.plug_trapezoid_long/2.0, 'y':calc_dim.plug_back},
                {'x':seriesParams.plug_trapezoid_long/2.0, 'y':calc_dim.plug_back},
                {'x':seriesParams.plug_trapezoid_short/2.0, 'y':calc_dim.plug_back+seriesParams.plug_trapezoid_width},
                {'x':seriesParams.plug_seperator_distance/2.0, 'y':calc_dim.plug_back+seriesParams.plug_trapezoid_width},
                {'x':seriesParams.plug_seperator_distance/2.0, 'y':calc_dim.plug_front-seriesParams.plug_cut_width},
                {'x':seriesParams.plug_cut_len/2.0, 'y':calc_dim.plug_front-seriesParams.plug_cut_width},
                {'x':seriesParams.plug_cut_len/2.0, 'y':calc_dim.plug_front},
                {'x':seriesParams.plug_arc_len/2.0, 'y':calc_dim.plug_front}
            ]
            plug_outline_translation.append(PolygoneLine(polygone=plug_outline_poly, layer='F.SilkS', width=configuration['silk_line_width']))
            plug_outline_translation.append(Arc(start=[-seriesParams.plug_arc_len/2.0,calc_dim.plug_front], center=[0,calc_dim.plug_front+1.7], angle=47.6, layer='F.SilkS', width=configuration['silk_line_width']))
            if configuration['inner_details_on_fab']:
                plug_outline_translation.append(PolygoneLine(polygone=plug_outline_poly,  layer="F.Fab", width=configuration['fab_line_width']))
                plug_outline_translation.append(Arc(start=[-seriesParams.plug_arc_len/2.0,calc_dim.plug_front], center=[0,calc_dim.plug_front+1.7], angle=47.6,  layer="F.Fab", width=configuration['fab_line_width']))
            kicad_mod.append(plug_outline_translation)
    if params.mount_hole:
        kicad_mod.append(Circle(center=calc_dim.mount_hole_left, radius=seriesParams.mount_screw_head_r+configuration['silk_body_offset'], layer='B.SilkS', width=configuration['silk_line_width']))
        kicad_mod.append(Circle(center=calc_dim.mount_hole_right, radius=seriesParams.mount_screw_head_r+configuration['silk_body_offset'], layer='B.SilkS', width=configuration['silk_line_width']))

        kicad_mod.append(Circle(center=calc_dim.mount_hole_right, radius=seriesParams.mount_screw_head_r, layer='B.Fab', width=configuration['fab_line_width']))
        kicad_mod.append(Circle(center=calc_dim.mount_hole_left, radius=seriesParams.mount_screw_head_r, layer='B.Fab', width=configuration['fab_line_width']))

    ################################################## Courtyard ##################################################
    if params.angled:
        crtyd_top_left=v_offset([silk_top_left[0],-params.pin_Sy/2], configuration['courtyard_distance'])
    else:
        crtyd_top_left=v_offset(body_top_left, configuration['courtyard_distance'])
    crtyd_bottom_right=v_offset(body_bottom_right, configuration['courtyard_distance'])
    kicad_mod.append(RectLine(start=round_crty_point(crtyd_top_left, configuration['courtyard_grid']), end=round_crty_point(crtyd_bottom_right, configuration['courtyard_grid']), layer='F.CrtYd', width=configuration['courtyard_line_width']))

    if params.mount_hole and configuration['courtyard_for_mountscrews']:
        kicad_mod.append(Circle(center=calc_dim.mount_hole_right, radius=seriesParams.mount_screw_head_r+configuration['courtyard_distance'], layer='B.CrtYd', width=configuration['courtyard_line_width']))
        kicad_mod.append(Circle(center=calc_dim.mount_hole_left, radius=seriesParams.mount_screw_head_r+configuration['courtyard_distance'], layer='B.CrtYd', width=configuration['courtyard_line_width']))

    ################################################# Text Fields #################################################
    #getTextFieldDetails(field_definition, crtyd_top, crtyd_bottom, center_x, params)
    reference_fields = configuration['references']
    kicad_mod.append(Text(type='reference', text='REF**',
        **getTextFieldDetails(reference_fields[0], crtyd_top_left[1], crtyd_bottom_right[1], center_x, params)))

    for additional_ref in reference_fields[1:]:
        kicad_mod.append(Text(type='user', text='%R',
        **getTextFieldDetails(additional_ref, crtyd_top_left[1], crtyd_bottom_right[1], center_x, params)))

    value_fields = configuration['values']
    kicad_mod.append(Text(type='value', text=footprint_name,
        **getTextFieldDetails(value_fields[0], crtyd_top_left[1], crtyd_bottom_right[1], center_x, params)))

    for additional_value in value_fields[1:]:
        kicad_mod.append(Text(type='user', text='%V',
            **getTextFieldDetails(additional_value, crtyd_top_left[1], crtyd_bottom_right[1], center_x, params)))

    ################################################# Pin 1 Marker #################################################
    if not params.angled:
        pin1_marker_poly = create_pin1_marker_corner(crtyd_top_left[1],
            body_top_left[0] - configuration['courtyard_distance'] +
            (seriesParams.flange_lenght if params.flanged else 0), [2,1.25])
        kicad_mod.append(PolygoneLine(polygone=pin1_marker_poly, layer='F.SilkS', width=configuration['silk_line_width']))
        if configuration['with_fab_layer']:
            kicad_mod.append(PolygoneLine(polygone=pin1_marker_poly, layer='F.Fab', width=configuration['fab_line_width']))
    else:
        kicad_mod.append(PolygoneLine(polygone=create_pin1_marker_triangle(-params.pin_Sy/2-0.2),
            layer='F.SilkS', width=configuration['silk_line_width']))
        if configuration['with_fab_layer']:
            kicad_mod.append(PolygoneLine(
                polygone=create_pin1_marker_triangle(bottom_y = 0,
                    dimensions = [params.pin_Sx - 0.2, -body_top_left[1]], with_top_line = False),
                layer='F.Fab', width=configuration['fab_line_width']))

    #################################################### 3d file ###################################################
    p3dname = '{prefix:s}{lib_name:s}.3dshapes/{fp_name}.wrl'.format(prefix = configuration.get('3d_model_prefix', '${KISYS3DMOD}/'), lib_name=lib_name, fp_name=footprint_name)
    kicad_mod.append(Model(filename=p3dname,
                           at=[0, 0, 0], scale=[1, 1, 1], rotate=[0, 0, 0]))

    file_handler = KicadFileHandler(kicad_mod)
    out_dir = '{:s}.pretty/'.format(lib_name)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    file_handler.writeFile('{:s}.pretty/{:s}.kicad_mod'.format(lib_name, footprint_name))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='use confing .yaml files to create footprints.')
    parser.add_argument('--model_filter', type=str, nargs='?',
                        help='define a filter for what should be generated.', default="*")
    parser.add_argument('-c', '--config', type=str, nargs='?', help='the config file defining how the footprint will look like.', default='config_KLCv2.0.yaml')
    args = parser.parse_args()

    with open(args.config, 'r') as config_stream:
        try:
            configuration = yaml.load(config_stream)
        except yaml.YAMLError as exc:
            print(exc)

    model_filter_regobj=re.compile(fnmatch.translate(args.model_filter))
    for model, params in all_params.items():
        if model_filter_regobj.match(model):
            generate_one_footprint(model, params, configuration)
