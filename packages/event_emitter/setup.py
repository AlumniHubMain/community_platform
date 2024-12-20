import os

from grpc_tools import protoc
from setuptools import setup, Command
from setuptools.command.build_py import build_py


class BuildProtosCommand(Command):
    """Custom command to generate Protobuf files."""

    description = "Generate Python code from .proto files"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        proto_dir = "../../proto"
        output_dir = "src/alumnihub/community_platform/event_emitter"

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for proto_file in os.listdir(proto_dir):
            if proto_file.endswith(".proto"):
                proto_path = os.path.join(proto_dir, proto_file)
                protoc.main(
                    [
                        "grpc_tools.protoc",
                        f"--proto_path={proto_dir}",
                        f"--python_out={output_dir}",
                        f"--pyi_out={output_dir}",
                        proto_path,
                    ]
                )


class CustomBuildCommand(build_py):
    """Generate Protobuf files before building the package."""

    def run(self):
        self.run_command("build_protos")
        super().run()


setup(
    cmdclass={
        "build_protos": BuildProtosCommand,
        "build_py": CustomBuildCommand,
    },
    # Other setup configuration...
)
