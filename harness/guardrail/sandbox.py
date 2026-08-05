import re
from pathlib import Path

class Sandbox:
    def __init__(self, workdir: Path, allowed_paths: list[Path]):
        self.workdir = workdir.resolve()
        self.allowed = [p.resolve() for p in allowed_paths]

    def validate_path(self, path: Path) -> bool:
        resolved = path.resolve()
        if resolved == self.workdir or self.workdir in resolved.parents:
            return True
        for allowed in self.allowed:
            if resolved == allowed or allowed in resolved.parents:
                return True
        return False

    def validate_command(self, command: str) -> bool:
        if re.search(r"cd\s+\.\.", command):
            resolved = self._resolve_cd_target(command)
            if resolved and not self.validate_path(resolved):
                return False
        if re.search(r"\s+/(etc|var|root|home|usr|bin)/", command):
            return False
        return True

    def _resolve_cd_target(self, command: str) -> Path | None:
        m = re.search(r"cd\s+(\S+)", command)
        if m:
            return (self.workdir / m.group(1)).resolve()
        return None
