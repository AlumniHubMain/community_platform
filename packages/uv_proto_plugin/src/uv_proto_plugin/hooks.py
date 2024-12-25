from hatchling.plugin import hookimpl

from uv_proto_plugin.plugin import UvProtoPlugin


@hookimpl
def hatch_register_build_hook():
    return UvProtoPlugin
