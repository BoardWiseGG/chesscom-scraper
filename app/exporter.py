from typing import Any, Union

from typing_extensions import TypedDict

from app.repo import AnsiColor, Repo


class Export(TypedDict, total=False):
    # The (site, username) make up a unique key for each coach.
    site: str
    username: str
    # The coach's real name.
    name: str
    # The profile image used on the source site.
    image_url: str
    # The coach's rapid rating relative to the site they were sourced from.
    rapid: int
    # The coach's blitz rating relative to the site they were sourced from.
    blitz: int
    # The coach's bullet rating relative to the site they were sourced from.
    bullet: int


def _insert(export: Export, key: str, value: Any):
    if value is not None:
        export[key] = value


class BaseExporter(Repo):
    def __init__(self, site: str, username: str):
        super().__init__(site)
        self.username = username

    def export_name(self) -> Union[str, None]:
        raise NotImplementedError()

    def export_image_url(self) -> Union[str, None]:
        raise NotImplementedError()

    def export_rapid(self) -> Union[int, None]:
        raise NotImplementedError()

    def export_blitz(self) -> Union[int, None]:
        raise NotImplementedError()

    def export_bullet(self) -> Union[int, None]:
        raise NotImplementedError()

    def export(self) -> Export:
        """Transform coach-specific data into uniform format."""
        export: Export = {}

        _insert(export, "site", self.site)
        _insert(export, "username", self.username)
        _insert(export, "name", self.export_name())
        _insert(export, "image_url", self.export_image_url())
        _insert(export, "rapid", self.export_rapid())
        _insert(export, "blitz", self.export_blitz())
        _insert(export, "bullet", self.export_bullet())

        self.log(
            [
                (AnsiColor.INFO, "[INFO]"),
                (None, ": Exported "),
                (AnsiColor.DATA, self.username),
            ]
        )

        return export
