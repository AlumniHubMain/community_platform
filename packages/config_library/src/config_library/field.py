from typing import Any, Generic, Type, TypeVar, get_origin, get_args

from pydantic import BaseModel
from pydantic import GetCoreSchemaHandler, ValidatorFunctionWrapHandler
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
    def __gen_python_schema__(cls, item_tp: Type[T], item_schema: core_schema.CoreSchema) -> core_schema.CoreSchema:
        return core_schema.union_schema([
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


    @classmethod
    def __gen_json_schema__(cls, item_tp: Type[T], item_schema: core_schema.CoreSchema) -> core_schema.CoreSchema:
        return core_schema.no_info_wrap_validator_function(
            cls.__val_item__, item_schema,
        )

    @classmethod
    def __get_pydantic_core_schema__(
            cls,
            _source_type: Any,
            _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        item_tp = cls.__get_item_type__(_source_type)
        item_schema = _handler.generate_schema(item_tp)

        return core_schema.json_or_python_schema(
            json_schema=cls.__gen_json_schema__(item_tp, item_schema),
            python_schema=cls.__gen_python_schema__(item_tp, item_schema),
        )


class ReloadField(Generic[T]):
    class _Holder(BaseModel):
        value: T
    _path: str
    _type: Type[T]
    _value: _Holder

    def __init__(self, path: str, type_: Type[T], value: T):
        self._path = path
        self._type = type_
        self._value = ReloadField._Holder(value=value)

    @property
    def value(self) -> T:
        return self._value.value

    def reload(self):
        self._value = ReloadField._Holder(value=STORAGE.get(self._path, self._type, force=True))


class ReloadableFieldType(FieldType[ReloadField[T]]):

    @classmethod
    def __gen_python_schema__(cls, item_tp: Type[T], item_schema: core_schema.CoreSchema) -> core_schema.CoreSchema:
        def __val_reload_item_from_str__(
                value: str,
                handler: ValidatorFunctionWrapHandler
        ) -> ReloadField[T]:
            STORAGE.register(value, item_tp)
            read_value = handler(STORAGE.get(value, item_tp))
            return ReloadField(value, item_tp, read_value)

        return core_schema.union_schema([
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_wrap_validator_function(
                    __val_reload_item_from_str__, item_schema,
                )
            ])
        ])
