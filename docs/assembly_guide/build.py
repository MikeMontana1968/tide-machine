#!/usr/bin/env python3
"""Build the guide with the repo's own copy of the flatpack-guide kit (kit/).

    python build.py                # everything
    python build.py --no-fritzing  # reuse the last Fritzing export
    python build.py --no-pdf
"""
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_BUILD = os.path.join(HERE, 'kit', 'scripts', 'build.py')
os.chdir(HERE)                      # the kit's build reads guide.json from here
sys.argv[0] = KIT_BUILD             # and finds its assets relative to itself
runpy.run_path(KIT_BUILD, run_name='__main__')
