class PropellerError(Exception):
    pass


class PropellerValidationError(PropellerError):
    pass


class PropellerConnectionError(PropellerError):
    pass


class PropellerResponseError(PropellerError):
    def __init__(self, code: str, message: str | None = None) -> None:
        self.code = code
        self.message = message
        super().__init__(f'{code}: {message}' if message else code)
