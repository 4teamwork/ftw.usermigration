import errno
import os


def get_buildout_dir():
    instance_home = os.environ['INSTANCE_HOME']
    buildout_dir = os.path.sep.join(instance_home.split(os.path.sep)[:-2])
    return buildout_dir


def get_var_log():
    buildout_dir = get_buildout_dir()
    var_log = os.path.join(buildout_dir, os.path.join('var', 'log'))
    return var_log


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
