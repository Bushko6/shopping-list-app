from dataclasses import dataclass, field


@dataclass
class User:
    id: str
    username: str
    email: str
    is_active: bool = field(default=True)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id cannot be empty")
        if not self.username.strip():
            raise ValueError("username cannot be empty")
        if not self.email or "@" not in self.email:
            raise ValueError("email must contain @")
