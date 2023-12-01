from app.repo import AnsiColor, Repo
from typing import Union
from typing_extensions import TypedDict


class Export(TypedDict, total=False):
    fide_rapid: int


class BaseExporter(Repo):
    def __init__(self, site: str, username: str):
        super().__init__(site)
        self.username = username

    def export_fide_rapid(self) -> Union[int, None]:
        raise NotImplementedError()

    def export(self) -> Export:
        """Transform coach-specific data into uniform format."""
        export: Export = {}

        fide_rapid = self.export_fide_rapid()
        if fide_rapid:
            export["fide_rapid"] = fide_rapid

        self.log(
            [
                (AnsiColor.INFO, "[INFO]"),
                (None, ": Exported "),
                (AnsiColor.DATA, self.username),
            ]
        )

        return export
