
def register_adapters_via_import():
    """all scripts registering an adapter have to be imported here.\n
    This is necessary because the register function call needs to be executed."""
    from .btypes import numeric

register_adapters_via_import()