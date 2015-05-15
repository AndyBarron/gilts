#! /usr/bin/env python

import os
import os.path as path

SELF = path.realpath(__file__)
DIR = path.dirname(__file__)
IGNORE = [__file__, './TODO.md']

def process(dirpath, dirnames, filenames):
    for filename in filenames:
        if not (filename.endswith('.py') or filename.endswith('.md')):
            continue
        p = path.join(dirpath, filename)
        if p in IGNORE:
            continue
        split = path.normpath(p).split(os.sep)
        if '.git' in split:
            continue
        print "\n***** " + p[1:] + "\n"
        with open(p, 'r') as f:
            # print f.read()
            pass

# print IGNORE
# print DIR
map(lambda f: process(*f), os.walk(DIR))