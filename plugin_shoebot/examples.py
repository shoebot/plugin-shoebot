import functools
import os
import subprocess
import sys
import textwrap


@functools.lru_cache(maxsize=1)
def find_example_dir(python="python"):
    """
    Find examples dir .. a little bit ugly..
    """
    # Replace %s with directory to check for shoebot menus.
    paths = [
        'share/shoebot/examples',  # default
        'examples/',               # user installed shoebot with -e
    ]
    code = textwrap.dedent("""
    from os.path import isdir
    from pkg_resources import resource_filename, Requirement, DistributionNotFound
    
    for path in {paths}:
        try:
            res_path = resource_filename(Requirement.parse('shoebot'), path)
            if isdir(res_path):
                print(res_path)
                break
        except DistributionNotFound:
            pass
    """.format(paths=paths))

    # Needs to run in same python env as shoebot (may be different to gedits)
    cmd = [python, "-c", code]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, errors = p.communicate()
    if errors:
        sys.stderr.write('Shoebot experienced errors searching for install and examples.')
        sys.stderr.write('Errors:\n{0}'.format(errors.decode('utf-8')))
        return None
    else:
        examples_dir = output.decode('utf-8').strip()
        if os.path.isdir(examples_dir):
            return examples_dir

        if examples_dir:
            sys.stderr.write('Shoebot could not find examples at: {0}'.format(examples_dir))
        else:
            sys.stderr.write('Shoebot could not find install dir and examples.')
