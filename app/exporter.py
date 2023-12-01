from app.repo import AnsiColor, Repo
from typing import Union
from typing_extensions import TypedDict


class Export(TypedDict, total=False):
    # The coach's rapid rating as listed on the site they were sourced from.
    rapid: int


class BaseExporter(Repo):
    def __init__(self, site: str, username: str):
        super().__init__(site)
        self.username = username

    def export_rapid(self) -> Union[int, None]:
        raise NotImplementedError()

    def export(self) -> Export:
        """Transform coach-specific data into uniform format."""
        export: Export = {}

        rapid = self.export_rapid()
        if rapid:
            export["rapid"] = rapid

        self.log(
            [
                (AnsiColor.INFO, "[INFO]"),
                (None, ": Exported "),
                (AnsiColor.DATA, self.username),
            ]
        )

        return export
