import os
import subprocess
import textwrap


def get_example_dir():
    return _example_dir


def find_example_dir():
    """
    Find examples dir .. a little bit ugly..
    """
    # Replace %s with directory to check for shoebot menus.
    paths = [
        'share/shoebot/examples',  # default
        'examples/',               # user installed shoebot with -e
    ]
    code = textwrap.dedent("""
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
    cmd = ["python", "-c", code]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, errors = p.communicate()
    if errors:
        print('Shoebot experienced errors searching for install and examples.')
        print('Errors:\n{0}'.format(errors.decode('utf-8')))
        return None
    else:
        examples_dir = output.decode('utf-8').strip()
        if os.path.isdir(examples_dir):
            return examples_dir

        if examples_dir:
            print('Shoebot could not find examples at: {0}'.format(examples_dir))
        else:
            print('Shoebot could not find install dir and examples.')


_example_dir = find_example_dir()
