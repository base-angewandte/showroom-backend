from datetime import datetime

from babel.dates import format_datetime as fd

from django.conf import settings
from django.utils.translation import get_language

DEFAULT_LANG = settings.LANGUAGE_CODE

DATE_FORMAT_JS = '%Y-%m-%d'
TIME_FORMAT_JS = '%H:%M'
DATETIME_FORMAT_JS = f'{DATE_FORMAT_JS}T{TIME_FORMAT_JS}:%S.%fZ'


def format_date(datetime, lang=None, short=False):
    if lang is None:
        lang = get_language() or DEFAULT_LANG
    return fd(
        datetime,
        format=settings.DATE_FORMATS[lang]
        if not short
        else settings.DATE_FORMATS_SHORT[lang],
        locale=settings.LOCALES[lang],
    )


def format_datetime(datetime, lang=None):
    if lang is None:
        lang = get_language() or DEFAULT_LANG
    return fd(
        datetime,
        format=settings.DATETIME_FORMATS[lang],
        locale=settings.LOCALES[lang],
    )


def format_datetime_string(datetime_string, lang=None):
    if lang is None:
        lang = get_language() or DEFAULT_LANG
    if len(datetime_string) <= 4:
        # year
        return datetime_string

    try:
        return format_date(datetime.strptime(datetime_string, DATE_FORMAT_JS), lang)
    except ValueError:
        return format_datetime(
            datetime.strptime(datetime_string, DATETIME_FORMAT_JS),
            lang,
        )


def format_datetime_range_string(from_datetime_string, to_datetime_string, lang=None):
    if lang is None:
        lang = get_language() or DEFAULT_LANG
    # TODO simple solution for now
    from_string = (
        format_datetime_string(from_datetime_string, lang)
        if from_datetime_string
        else ''
    )

    if from_datetime_string == to_datetime_string:
        return f'{from_string}'

    to_string = (
        format_datetime_string(to_datetime_string, lang) if to_datetime_string else ''
    )

    return f'{from_string}–{to_string}'


def format_time(datetime, lang=None):
    if lang is None:
        lang = get_language() or DEFAULT_LANG
    return fd(
        datetime,
        format=settings.TIME_FORMATS[lang],
        locale=settings.LOCALES[lang],
    )


def format_time_string(time_string, lang=None):
    if lang is None:
        lang = get_language() or DEFAULT_LANG
    return format_time(datetime.strptime(time_string, TIME_FORMAT_JS), lang)


def format_time_range_string(from_time_string, to_time_string, lang=None):
    if lang is None:
        lang = get_language() or DEFAULT_LANG
    # TODO simple solution for now
    from_string = format_time_string(from_time_string, lang) if from_time_string else ''

    if from_time_string == to_time_string:
        return f'{from_string}'

    to_string = format_time_string(to_time_string, lang) if to_time_string else ''

    return f'{from_string}–{to_string}'
