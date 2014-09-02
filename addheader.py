#!/usr/bin/env python

# pylicense (https://github.com/ftalbrecht/pylicense): addheader.py
# Copyright Holders: Felix Albrecht
# License: BSD 2-Clause License (http://opensource.org/licenses/BSD-2-Clause)

'''
Add header to a given file.

Usage:
    addheader.py [-hv] [--help] [--verbose] --cfg=CONFIG_FILE DIR


Arguments:
    DIR             Directory to process.

Options:
    -h, --help      Show this message.

    -v, --verbose   Be verbose.
'''


from __future__ import print_function
import ConfigParser
from docopt import docopt
from shutil import copyfile
import subprocess
import os
import sys
import re
import fnmatch

def process_dir(dirname, config):
    os.chdir(dirname)
    include = re.compile('|'.join(fnmatch.translate(p) for p in config.get('files', 'include_patterns').split()))
    exclude = re.compile('|'.join(fnmatch.translate(p) for p in config.get('files', 'exclude_patterns').split()))
    for root, _, files in os.walk(dirname):
        for abspath in [os.path.join(root, f) for f in files]:
            if include.match(abspath) and not exclude.match(abspath):
                yield abspath, process_file(abspath, config, dirname)


def add_multiple_authors(author_list, prefix, first_line_label, target):
    first_author = True
    for author in author_list:
        label = first_line_label + ':' if first_author else ' ' * (len(first_line_label) + 1)
        line = '{} {} {}\n'.format(prefix, label, author)
        target.write(line)
        first_author = False


def process_file(filename, config, root):
    assert(config.has_option('header', 'name'))
    project_name = config.get('header', 'name').strip()
    assert(config.has_option('header', 'license'))
    license = config.get('header', 'license').strip()
    url = config.get('header', 'url').strip() if config.has_option('header', 'license') else None
    max_width = int(config.get('header', 'max_width')) if config.has_option('header', 'max_width') else 78
    try:
        copyright_holders = [name.strip() for name in config.get('header', 'copyright_holders').strip().split(',')]
        if len(copyright_holders) == 0:
            raise Exception('ERROR: no copyright holders given!')
    except:
        raise Exception('ERROR: no copyright holders given!')
    list_contributors = False
    if config.has_option('header', 'list_contributers'):
        list_contributors = config.getboolean('header', 'list_contributers')
    contributors = []
    if list_contributors:
        try:
            ret = subprocess.Popen('git shortlog -nse ' + filename + ' | cut -f2',
                                    shell=True,
                                    cwd=root,
                                    stdout=subprocess.PIPE,
                                    stderr=sys.stderr)
            out, _ = ret.communicate()
            contributors = out.splitlines()
            contributors = sorted([x for x in contributors if x.split('<')[0][:-1] not in copyright_holders])
            list_contributors = True if len(contributors) > 0 else False
        except:
            print('WARNING: there was a git related error, contributors will not be listed!')
            list_contributors = False
    prefix = '#'
    if config.has_option('header', 'prefix'):
        prefix = config.get('header', 'prefix')

    def insert_license_text(target):
        # project name and url
        line = '{p} {n}'.format(p=prefix, n=project_name)
        if url is not None:
            if len(line) + len(url) + len('().') <= max_width:
                target.write('{line} ({url}).\n'.format(line=line, url=url))
            else:
                target.write('{line}:\n'.format(line=line))
                target.write('{prefix}   {url}\n'.format(prefix=prefix, url=url))
        # copyright holders
        target.write(prefix + ' Copyright Holders: ' + ', '.join(copyright_holders) + '\n')
        target.write('{p} License: {l}\n'.format(p=prefix, l=license))
        # contributors
        if list_contributors:
            target.write(prefix + '\n')
            add_multiple_authors(contributors, prefix, 'Contributors', target)
        target.write('\n')

    source = open(filename).readlines()
    source.append(None)
    source_iter = iter(source)

    # write header to original file
    with open(filename, 'w') as target:

        line = next(source_iter)

        # skip shebang if present
        if line is not None and line.startswith('#!'):
            target.write(line)
            line = next(source_iter)

        # skip line defining file encoding
        if line is not None and re.match('.*coding[:=]\s*', line): #([-\w.]+)', line):
            target.write(line)
            line = next(source_iter)

        # skip lines containing whitespace
        while line is not None and line.isspace():
            line = next(source_iter)

        # remove all following comment lines, assuming they contain the previous
        # lincense text
        while line is not None and line.startswith('#'):
            line = next(source_iter)

        # write the new license text
        insert_license_text(target)

        # skip whitespace after license text
        while line is not None and line.isspace():
            line = next(source_iter)

        # copy all remaining content
        while line is not None:
            target.write(line)
            line = next(source_iter)

    return 0

if __name__ == '__main__':
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
    dirname = args['DIR']
    for fn, res in process_dir(dirname, config):
        print('{}: {}'.format(fn, 'failed' if res else 'success'))
