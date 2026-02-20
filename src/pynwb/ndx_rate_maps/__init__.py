from importlib.resources import files
from pynwb import load_namespaces

# Get path to the namespace.yaml file with the expected location when installed not in editable mode
__location_of_this_file = files(__name__)
__spec_path = __location_of_this_file / "spec" / "ndx-rate-maps.namespace.yaml"

# If that path does not exist, we are likely running in editable mode. Use the local path instead
if not __spec_path.exists():
    __spec_path = __location_of_this_file.parent.parent.parent / "spec" / "ndx-rate-maps.namespace.yaml"

# Load the namespace — MUST happen before @register_class imports
load_namespaces(str(__spec_path))

from .rate_map_table import RateMapTable  # noqa: E402, F401

__all__ = [
    "RateMapTable",
]

# Remove these functions/modules from the package
del load_namespaces, files, __location_of_this_file, __spec_path
