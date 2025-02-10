class IntegerRangeValidator:
    def __init__(self, min: int | None = None, max: int | None = None, field_name: str | None = None) -> None:
        assert min < max, "Min value must be less than max value for IntegerRangeValidator"
        self.min = min
        self.max = max
        self.name = field_name
    
    def _raise_named_value_error(self, message):
        prefix = ""
        if self.name:
            prefix = f"Error while parsing field {self.name}: "
        else:
            prefix = "Error while parsing ranged integer value: "
        raise ValueError(prefix + message)
        
    def validate(self, value) -> None:
        if not isinstance(value, int):
            raise self._raise_named_value_error(f"value must be integer, got {type(value)}")
        if self.min and value < self.min:
            raise self._raise_named_value_error(f"value must be greater or equal to {self.min}")
        if self.max and value > self.max:
            raise self._raise_named_value_error(f"value must be less or equal to {self.max}")
