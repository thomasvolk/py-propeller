class PropellerError(Exception):
    pass


class PropellerValidationError(PropellerError):
    pass


class PropellerConnectionError(PropellerError):
    pass


class PropellerResponseError(PropellerError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)
