#!/usr/bin/env python3
#                                                  -*- coding: utf-8 -*-
# A library to display spinorama charts
#
# Copyright (C) 2020 Pierre Aubert pierreaubert(at)yahoo(dot)fr
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
usage: generate_html.py [--help] [--version] [--dev]\
 [--sitedev=<http>]  [--log-level=<level>]

Options:
  --help            display usage()
  --version         script version number
  --sitedev=<http>  default: http://localhost:8000/docs
  --log-level=<level> default is WARNING, options are DEBUG INFO ERROR.
"""
import json
import logging
import os
import shutil
import sys
from glob import glob
from mako.template import Template
from mako.lookup import TemplateLookup
from docopt import docopt


siteprod = 'https://pierreaubert.github.io/spinorama'
sitedev = 'http://localhost:8000/docs'
root = './'


def generate_speaker(mako, df, meta, site):
    speaker_html = mako.get_template('speaker.html')
    graph_html = mako.get_template('graph.html')
    for speaker_name, origins in df.items():
        for origin, measurements in origins.items():
            for m, dfs in measurements.items():
                # freq
                freq_filter = [
                    "CEA2034",
                    "On Axis",
                    "Early Reflections",
                    "Estimated In-Room Response",
                    "Horizontal Reflections", "Vertical Reflections",
                    "SPL Horizontal", "SPL Vertical",
                ]
                freq = {key: dfs[key] for key in freq_filter if key in dfs}
                # contour
                contour_filter = [
                    "SPL Horizontal Contour",
                    "SPL Vertical Contour",
                ]
                contour = {key: dfs[key] for key in contour_filter if key in dfs}
                # isoband
                isoband_filter = [
                    "SPL Horizontal IsoBand",
                    "SPL Vertical IsoBand",
                ]
                isoband = {key: dfs[key] for key in isoband_filter if key in dfs}
                # radar
                radar_filter = [
                    "SPL Horizontal Radar",
                    "SPL Vertical Radar",
                ]
                radar = {key: dfs[key] for key in radar_filter if key in dfs}

                # directivity
                directivity_filter = [
                    "Directivity Matrix",
                ]
                directivity = {key: dfs[key] for key in directivity_filter if key in dfs}

                # get index.html filename
                dirname = 'docs/' + speaker_name + '/'
                if origin == 'ASR' or origin == 'Princeton':
                    dirname += origin
                else:
                    dirname += meta[speaker_name]['brand']
                indexname = dirname + '/index.html'

                # write index.html
                logging.info('Writing index.html for {:s}'.format(speaker_name))
                with open(indexname, 'w') as f:
                    # write all
                    f.write(speaker_html.render(speaker=speaker_name,
                                                g_freq=freq,
                                                g_contour=contour,
                                                g_isoband=isoband,
                                                g_radar=radar,
                                                g_directivity=directivity,
                                                meta=meta,
                                                origin=origin,
                                                site=site))
                    f.close()

                # write a small file per graph to render the json generated by Vega
                for kind in [freq, contour, isoband, radar, directivity]:
                    for graph_name in kind:
                        graph_filename = dirname + '/default/' + graph_name + '.html'
                        logging.info('Writing default/{0} for {1}'.format(graph_filename, speaker_name))
                        with open(graph_filename, 'w') as f:
                            f.write(graph_html.render(graph=graph_name, meta=meta, site=site))
                            f.close()
    return 0


if __name__ == '__main__':
    args = docopt(__doc__,
                  version='update_html.py version 1.21',
                  options_first=True)

    # check args section
    dev = args['--dev']
    site = siteprod
    if dev is True:
        if args['--sitedev'] is not None:
            sitedev = args['--sitedev']
            if len(sitedev) < 4 or sitedev[0:4] != 'http':
                print('sitedev %s does not start with http!'.format(sitedev))
                exit(1)
        site = sitedev

    level = None
    if args['--log-level'] is not None:
        check_level = args['--log-level']
        if check_level in ['INFO', 'DEBUG', 'WARNING', 'ERROR']:
            level = check_level

    if level is not None:
        logging.basicConfig(
            format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d:%H:%M:%S',
            level=level)
    else:
        logging.basicConfig(
            format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d:%H:%M:%S')

    # load all metadata from generated json file
    json_filename = './docs/assets/metadata.json'
    if not os.path.exists(json_filename):
        logging.fatal('Cannot find {0}'.format(json_filename))
        sys.exit(1)

    meta = None
    with open(json_filename, 'r') as f:
        meta = json.load(f)

    # only build a dictionnary will all graphs
    df = {}
    speakers = glob('./docs/*')
    for speaker in speakers:
        if not os.path.isdir(speaker):
            continue
        # humm annoying
        if speaker in ('score', 'assets', 'stats', 'compare', 'logos', 'pictures'):
            continue
        speaker_name = speaker.replace('./docs/', '')
        df[speaker_name] = {}
        origins = glob(speaker + '/*')
        for origin in origins:
            if not os.path.isdir(origin):
                continue
            origin_name = os.path.basename(origin)
            df[speaker_name][origin_name] = {}
            defaults = glob(origin + '/*')
            for default in defaults:
                if not os.path.isdir(default):
                    continue
                default_name = os.path.basename(default)
                df[speaker_name][origin_name][default_name] = {}
                graphs = glob(default + '/*_large.png')
                for graph in graphs:
                    g = os.path.basename(graph).replace('_large.png', '')
                    df[speaker_name][origin_name][default_name][g] = {}

    # configure Mako
    mako_templates = TemplateLookup(directories=['templates'], module_directory='/tmp/mako_modules')

    # write index.html
    logging.info('Write index.html')
    index_html = mako_templates.get_template('index.html')

    def sort_meta(s):
        if 'pref_rating' in s.keys() and 'pref_score' in s['pref_rating']:
            return s['pref_rating']['pref_score']
        return -1

    keys_sorted = sorted(meta, key=lambda a: sort_meta(meta[a]), reverse=True)
    meta_sorted = {k: meta[k] for k in keys_sorted}

    with open('docs/index.html', 'w') as f:
        # by default sort by pref_rating decreasing
        f.write(index_html.render(df=df, meta=meta_sorted, site=site))
        f.close()

    # write various html files
    for item in ('help', 'compare', 'scores', 'statistics'):
        item_name = '{0}.html'.format(item)
        logging.info('Write {0}'.format(item_name))
        item_html = mako_templates.get_template(item_name)
        with open('./docs/' + item_name, 'w') as f:
            f.write(item_html.render(df=df, meta=meta_sorted, site=site))
            f.close()

    # write a file per speaker
    logging.info('Write a file per speaker')
    generate_speaker(mako_templates, df, meta=meta, site=site)

    # copy css/js files
    logging.info('Copy js/css files to docs')
    for f in ['search.js', 'bulma.js', 'compare.js', 'tabs.js', 'spinorama.css', 'graph.js']:
        file_ext = Template(filename='templates/assets/'+f)
        with open('./docs/assets/'+f, 'w') as fd:
            fd.write(file_ext.render(site=site))
            fd.close()

    # copy favicon(s)
    for f in ['favicon.ico', 'favicon-16x16.png']:
        file_in = './templates/assets/'+f
        file_out = './docs/assets/'+f
        shutil.copy(file_in, file_out)

    sys.exit(0)
