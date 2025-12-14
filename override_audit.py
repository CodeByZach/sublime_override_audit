import importlib
import sys


###----------------------------------------------------------------------------


def reload(prefix, modules=None):
    if modules is None:
        modules = [""]
    prefix = "OverrideAudit.%s." % prefix

    for module in modules:
        module = (prefix + module).rstrip(".")
        if module in sys.modules:
            importlib.reload(sys.modules[module])


###----------------------------------------------------------------------------


reload("lib")
reload("src")

from .lib import *
from .src import *


# ###----------------------------------------------------------------------------


def plugin_loaded():
    core.loaded()


def plugin_unloaded():
    core.unloaded()


###----------------------------------------------------------------------------
