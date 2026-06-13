"""
Logging estruturado + decorator de retry.

- get_logger(nome): logger que escreve em logs/sdr.log e no console.
- retry(...): repete uma função em caso de exceção, com espera entre tentativas.
"""
from __future__ import annotations

import functools
import logging
import time
from typing import Callable, TypeVar

from backend.config import config

_T = TypeVar("_T")
_LOGGER_CONFIGURADO = False


def get_logger(nome: str = "sdr") -> logging.Logger:
    global _LOGGER_CONFIGURADO
    config.ensure_dirs()
    logger = logging.getLogger(nome)
    if not _LOGGER_CONFIGURADO:
        logger.setLevel(logging.INFO)
        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
        )
        fh = logging.FileHandler(config.LOGS_DIR / "sdr.log", encoding="utf-8")
        fh.setFormatter(fmt)
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        logger.addHandler(fh)
        logger.addHandler(ch)
        _LOGGER_CONFIGURADO = True
    return logger


def retry(
    tentativas: int = 3,
    espera_seg: float = 2.0,
    excecoes: tuple = (Exception,),
) -> Callable[[Callable[..., _T]], Callable[..., _T]]:
    """Repete a função em caso de falha. Loga cada tentativa."""

    def decorator(func: Callable[..., _T]) -> Callable[..., _T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> _T:
            logger = get_logger()
            ultimo_erro: Exception | None = None
            for i in range(1, tentativas + 1):
                try:
                    return func(*args, **kwargs)
                except excecoes as e:  # noqa: BLE001
                    ultimo_erro = e
                    logger.warning(
                        "Tentativa %d/%d falhou em %s: %s",
                        i, tentativas, func.__name__, e,
                    )
                    if i < tentativas:
                        time.sleep(espera_seg)
            logger.error("Esgotadas as tentativas em %s", func.__name__)
            raise ultimo_erro  # type: ignore[misc]

        return wrapper

    return decorator
