from .schemas import EnumValues


class EnumManger:
    @classmethod
    def get_possible_values(
            cls, etype # type is python type
    ) -> EnumValues:
        list_of_values = [e.value for e in etype]
        return EnumValues.model_validate({'values': list_of_values})