import dataclasses


@dataclasses.dataclass
class Config:
    project: str
    host_port: str
