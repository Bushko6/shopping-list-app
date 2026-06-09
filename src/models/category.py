from dataclasses import dataclass


@dataclass
class Category:
    id: str
    name: str
    color: str

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id cannot be empty")
        if not self.name.strip():
            raise ValueError("name cannot be empty")
        if not self.color.strip():
            raise ValueError("color cannot be empty")
