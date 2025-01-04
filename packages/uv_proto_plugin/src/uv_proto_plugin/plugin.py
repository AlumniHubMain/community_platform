import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, List, Optional

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


@dataclass
class Generator:
    """A generator configuration."""

    """The name of the plugin."""
    name: str

    """Templates for paths that will be output, relative to ``output_path``."""
    outputs: List[str]

    """Where to write output files."""
    output_path: Path


@dataclass
class Output:
    name: str
    input: Path
    output: Path


@dataclass
class Files:
    inputs: List[Path]
    outputs: List[Output]


def _get_package_name(path: Path) -> Optional[Path]:
    with open(path, 'r') as f:
        for line in f:
            if not line.startswith("package"):
                continue

            package_path = line.replace("package", "").strip(" ;\n").split('.')

            if not package_path:
                return None

            if len(package_path) > 2:
                return Path("/".join(package_path))
            else:
                if path.stem.startswith(package_path[-1]):
                    return Path("/".join(package_path))
                return None

    return None


class UvProtoPlugin(BuildHookInterface):
    PLUGIN_NAME = "protobuf"

    def initialize(self, version: str, build_data: Dict[str, Any]) -> None:
        if not self._files.outputs:
            # nothing to do
            return

        self.app.display_info("Generating code from Protobuf files")

        args = [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
        ]
        for path in self._proto_paths:
            args.append("--proto_path")
            args.append(path)
        for out in self._files.outputs:
            if not os.path.exists(out.output.parent):
                # Get postfix of last part of path
                # For ex: example/of/path/file.py -> "file.py" -> "file", "py" -> "py"
                postfix = out.output.parts[-1].split('.')[-1]
                
                # If last part - .py/pyi file
                if "py" in postfix:
                    directories = [part for part in out.output.parts[:-1]]
                    os.makedirs(Path(str(os.path.sep).join(directories)), exist_ok=True)
                    file = open(out.output, 'w')
                    file.close()
                # If out.output - directory path
                else:
                    os.makedirs(out.output, exist_ok=True)

            run_args = args.copy()
            run_args.append(f"--{out.name}_out={out.output.parent}")

            run_args += [str(out.input)]

            self.app.display_debug(f"Running {shlex.join(args)}")
            subprocess.run(run_args, cwd=self._root_path, check=True)

        build_data["artifacts"] += [p.output.as_posix() for p in self._files.outputs]

    def clean(self, versions: List[str]) -> None:
        if not self._files.outputs:
            # nothing to do
            return

        for output in self._files.outputs:
            (self._root_path / output.output).unlink(missing_ok=True)

    @cached_property
    def _root_path(self) -> Path:
        return Path(self.root)

    @cached_property
    def _default_proto_path(self) -> str:
        builder = self.build_config.builder
        for project_name in (
                builder.normalize_file_name_component(builder.metadata.core.raw_name),
                builder.normalize_file_name_component(builder.metadata.core.name),
        ):
            # check this first because that's what the wheel builder does
            if (self._root_path / project_name / "__init__.py").is_file():
                return "."
            if (self._root_path / "src" / project_name / "__init__.py").is_file():
                return "src"
        return "."

    @cached_property
    def _proto_paths(self) -> List[str]:
        return self.config.get("proto_paths", [self._default_proto_path])

    @cached_property
    def _generators(self) -> List[Generator]:
        gen_grpc = self.config.get("with_gen_grpc", True)
        gen_pyi = self.config.get("with_gen_pyi", True)

        output_path = self.config.get("output_path", self._default_proto_path)

        generators = [
            Generator(
                name="python",
                outputs=["{proto_path}/{proto_name}_pb2.py"],
                output_path=Path(output_path),
            )
        ]
        if gen_pyi:
            generators.append(
                Generator(
                    name="pyi",
                    outputs=["{proto_path}/{proto_name}_pb2.pyi"],
                    output_path=Path(output_path),
                )
            )
        if gen_grpc:
            generators.append(
                Generator(
                    name="grpc_python",
                    outputs=["{proto_path}/{proto_name}_pb2_grpc.py"],
                    output_path=Path(output_path),
                )
            )

        for g in self.config.get("generators", []):
            generators.append(
                Generator(
                    name=g["name"],
                    outputs=g["outputs"],
                    output_path=Path(g.get("output_path", output_path)),
                )
            )

        return generators

    @cached_property
    def _files(self) -> Files:
        """Find input .proto files and the output files they will generate."""
        inputs = []
        rel_inputs = []
        for path in map(Path, self._proto_paths):
            abs_path = self._root_path / path
            for proto in abs_path.glob("**/*.proto"):
                input_ = proto.relative_to(self._root_path)
                inputs.append(input_)
                proto_path = proto.relative_to(abs_path)
                if package := _get_package_name(proto):
                    proto_path = package
                rel_inputs.append(proto_path)

        patterns = [
            (output, g.output_path, g) for g in self._generators for output in g.outputs
        ]

        outputs = []
        for from_file, proto in zip(inputs, rel_inputs):
            proto_path = str(proto.parent)
            proto_name = str(proto.stem)
            for pattern, output_path, generator in patterns:
                output = pattern.replace("{proto_name}", proto_name).replace(
                    "{proto_path}", proto_path
                )
                outputs.append(Output(name=generator.name, input=from_file, output=output_path / output))

        return Files(inputs=inputs, outputs=outputs)
