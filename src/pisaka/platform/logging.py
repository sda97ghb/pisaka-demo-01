import logging.config
from typing import Any, Literal, NewType

from pydantic import BaseModel, ConfigDict, Field

Level = Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]

FormatterId = NewType("FormatterId", str)
FilterId = NewType("FilterId", str)
HandlerId = NewType("HandlerId", str)
LoggerId = NewType("LoggerId", str)


class FormatterConfig(BaseModel):
    format: str | None = None
    datefmt: str | None = None
    style: Literal["%", "{", "$"] = "%"
    validate_: bool = Field(alias="validate", default=True)
    defaults: dict[str, Any] | None = None
    class_: str | None = Field(alias="class", default=None)


class FilterConfig(BaseModel):
    name: LoggerId = LoggerId("")


class HandlerConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    class_: str = Field(alias="class")
    level: Level | None = None
    formatter: FormatterId | None = None
    filters: list[FilterId] | None = None
    __pydantic_extra__: dict[str, Any] = Field(init=False)


class LoggerConfig(BaseModel):
    level: Level | None = None
    propagate: bool | None = None
    filters: list[FilterId] | None = None
    handlers: list[HandlerId] | None = None


class LoggingConfig(BaseModel):
    version: int = 1
    formatters: dict[FormatterId, FormatterConfig] = Field(default_factory=dict)
    filters: dict[FilterId, FilterConfig] = Field(default_factory=dict)
    handlers: dict[HandlerId, HandlerConfig] = Field(default_factory=dict)
    loggers: dict[LoggerId, LoggerConfig] = Field(default_factory=dict)
    root: LoggerConfig | None = None
    incremental: bool = False
    disable_existing_loggers: bool = True


def init_logging(config: LoggingConfig) -> None:
    config_dict = config.model_dump(by_alias=True)
    try:
        logging.config.dictConfig(config_dict)
    except:
        from pprint import pprint

        print("Logging config:")  # noqa: T201
        pprint(config_dict)  # noqa: T203
        raise
