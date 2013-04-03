#!/usr/bin/env python

# pylicense (https://github.com/ftalbrecht/pylicense): addheader.py
# Copyright Holders: Felix Albrecht
# License: BSD 2-Clause License (http://opensource.org/licenses/BSD-2-Clause)

'''
Add header to a given file.

Usage:
    addheader.py [-hv] [--help] [--verbose] --cfg=CONFIG_FILE FILE


Arguments:
    FILE    File to prepend the header to.

Options:
    -h, --help      Show this message.

    -v, --verbose   Be verbose.
'''


from __future__ import print_function
import ConfigParser
from docopt import docopt
from shutil import copyfile
from os import remove

# parse arguments
args = docopt(__doc__)
verbose = False
if args['--verbose']:
    verbose = True
config = ConfigParser.SafeConfigParser()
if args['--cfg'] is not None:
    config.readfp(open(args['--cfg']))
else:
    raise Exception('ERROR: no suitable config file given (try \'--cfg CONFIG_FILE\')!')
filename = args['FILE']

# parse config file
assert(config.has_option('header', 'name'))
project_name = config.get('header', 'name').strip()
assert(config.has_option('header', 'license'))
license = config.get('header', 'license').strip()
try:
    copyright_holders = [name.strip() for name in config.get('header', 'copyright_holders').strip().split(',')]
    if len(copyright_holders) == 0:
        raise Exception('ERROR: no copyright holders given!')
except:
    raise Exception('ERROR: no copyright holders given!')
list_contributors = False
if config.has_option('header', 'list_contributers'):
    list_contributors = config.getboolean('header', 'list_contributers')
prefix = '#'
if config.has_option('header', 'prefix'):
    prefix = config.get('header', 'prefix')

# create backup
backup_filename = filename + '~'
if verbose:
    print('adding header to \'{f}\'... '.format(f=filename), end='')
try:
    copyfile(filename, backup_filename)
except:
    raise Exception('ERROR: could not create backup file \'{f}\'!'.format(backup_filename))
# write header to original file
with open(backup_filename, 'r') as source:
    with open(filename, 'w') as target:
        target.write('{p} {n}: {f}\n'.format(p=prefix, n=project_name, f=filename))
        target.write('{p} Copyright Holders: {c}\n'.format(p=prefix, c=', '.join(copyright_holders)))
        target.write('{p} License: {l}\n'.format(p=prefix,l=license))
        if list_contributors:
            raise Exception('ERROR: listing of contributors not implemented yet!')
        target.write('\n')
        target.writelines(source.readlines())
# remove backup
try:
    remove(backup_filename)
    print('done')
except:
    print('done (but could not remove backup)')

