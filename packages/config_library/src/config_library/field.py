from typing import Any, Generic, Type, TypeVar, get_origin, get_args

from pydantic import GetCoreSchemaHandler, ValidatorFunctionWrapHandler, EmailStr
from pydantic_core import core_schema

from config_library.storage import STORAGE


T = TypeVar('T')


class FieldType(Generic[T]):
    value: T

    @classmethod
    def __get_item_type__(
            cls,
            _source_type: Any,
    ) -> Any:
        origin = get_origin(_source_type)
        if origin is None:
            raise ValueError(f'Expected origin type, got: {_source_type}')

        return get_args(_source_type)[0]

    @classmethod
    def __val_item__(
            cls,
            value: T,
            handler: ValidatorFunctionWrapHandler
    ) -> T:
        value = handler(value)
        return value

    @classmethod
    def __val_from_str__(
            cls,
            item_tp: Type[T],
    ) -> 'FieldType[T]':
        def val_from_str(
            value: str, info: Any,
        ) -> FieldType[T]:
            STORAGE.register(value, item_tp)
            return STORAGE.get(value, item_tp)
        return val_from_str

    @classmethod
    def __get_pydantic_core_schema__(
            cls,
            _source_type: Any,
            _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        item_tp = cls.__get_item_type__(_source_type)
        item_schema = _handler.generate_schema(item_tp)

        python_schema = core_schema.union_schema([
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.with_info_before_validator_function(
                    cls.__val_from_str__(item_tp), item_schema,
                ),
                core_schema.no_info_wrap_validator_function(
                    cls.__val_item__, item_schema,
                )
            ]),
            core_schema.chain_schema([
                core_schema.is_instance_schema(cls),
                core_schema.no_info_wrap_validator_function(
                    cls.__val_item__, item_schema,
                )
            ])
        ])

        return core_schema.json_or_python_schema(
            json_schema=core_schema.no_info_wrap_validator_function(
                cls.__val_item__, item_schema,
            ),
            python_schema=python_schema,
        )

