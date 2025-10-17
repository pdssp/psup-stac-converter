class OmegaCubeDataMissingError(Exception):
    """When data or partial data from the OMEGA cube dataset is missing"""

    pass


class OmegaOrbitCubeIndexNotFoundError(Exception):
    """When the idx isn't found in the dataset"""

    pass


class FileExtensionError(Exception):
    """When the expected file extension of the data file is incorrect"""

    def __init__(self, expected_extensions: list[str], current_extension: str, *args):
        self.expected_extensions = expected_extensions
        self.current_extension = current_extension
        super().__init__(self._format_message(), *args)

    def _format_message(self) -> str:
        if len(self.expected_extensions) > 1:
            fmt_exp_ext = (
                ", ".join(self.expected_extensions[:-1])
                + " or "
                + self.expected_extensions[-1]
            )
            is_single = False
        else:
            fmt_exp_ext = self.expected_extensions[0]
            is_single = True
        return f"""Expected {fmt_exp_ext} file{"" if is_single else "s"}. Got a {self.current_extension} file instead."""


class ValueNotAcceptedError(Exception):
    """When the expected value doesn't belong to a particular set of fields"""

    def __init__(self, expected_values: list[str], current_value: str, *args):
        super().__init__(
            f""""{current_value} not found among {expected_values}""", *args
        )


class FolderNotEmptyError(Exception):
    """Raises when the target folder is not empty"""

    pass


class PropertySetterError(Exception):
    """Raises when the user attempts to modify attributes"""

    pass
