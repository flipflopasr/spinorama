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
usage: generate_compare.py [--help] [--version] [--log-level=<level>]

Options:
  --help            display usage()
  --version         script version number
  --log-level=<level> default is WARNING, options are DEBUG INFO ERROR.
"""
import logging
import os
import sys

from docopt import docopt
import flammkuchen as fl
import pandas as pd
import ray

from src.spinorama.load_parse import parse_all_speakers
from src.spinorama.speaker_print_ray import print_compare
import datas.metadata as metadata


ray.init()


if __name__ == '__main__':
    args = docopt(__doc__,
                  version='generate_compare.py version 1.1',
                  options_first=True)

    # check args section
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

    df = fl.load('cache.parse_all_speakers.h5')
    if df is None:
        df = parse_all_speakers(metadata.speakers_info, None, './datas')
    force = True
    ptype = None
    print_compare(df, force, ptype)

    logging.info('Bye')
    sys.exit(0)
