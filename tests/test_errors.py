from propeller.errors import PropellerError, PropellerValidationError


def test_propeller_error_is_exception():
    assert issubclass(PropellerError, Exception)


def test_propeller_validation_error_is_subclass():
    assert issubclass(PropellerValidationError, PropellerError)


def test_propeller_validation_error_is_raisable():
    try:
        raise PropellerValidationError("test")
    except PropellerError:
        pass
    else:
        raise AssertionError("PropellerValidationError should be caught as PropellerError")


class TestTopLevelErrorImports:
    def test_propeller_error_importable_from_propeller(self):
        from propeller import PropellerError
        assert PropellerError is not None

    def test_propeller_validation_error_importable_from_propeller(self):
        from propeller import PropellerValidationError
        assert PropellerValidationError is not None

    def test_propeller_connection_error_importable_from_propeller(self):
        from propeller import PropellerConnectionError
        assert PropellerConnectionError is not None

    def test_validation_error_is_propeller_error_subclass(self):
        from propeller import PropellerError, PropellerValidationError
        assert isinstance(PropellerValidationError(), PropellerError)

    def test_connection_error_is_propeller_error_subclass(self):
        from propeller import PropellerError, PropellerConnectionError
        assert isinstance(PropellerConnectionError(), PropellerError)

    def test_validation_error_not_subclass_of_connection_error(self):
        from propeller import PropellerValidationError, PropellerConnectionError
        assert not issubclass(PropellerValidationError, PropellerConnectionError)
