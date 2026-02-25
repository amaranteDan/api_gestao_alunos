"""Configuração de logging estruturado."""
import sys
import logging
from pathlib import Path
from loguru import logger
from app.core.config import settings


class InterceptHandler(logging.Handler):
    """
    Handler para interceptar logs do logging padrão e redirecionar para loguru.
    """
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emite um log record."""
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    """
    Configura o sistema de logging da aplicação.
    
    - Remove handlers padrão do loguru
    - Configura saída para console com cores
    - Configura saída para arquivo (se configurado)
    - Intercepta logs de outras bibliotecas
    """
    # Remove handlers padrão
    logger.remove()
    
    # Formato de log
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Console handler
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # File handler (se configurado)
    if settings.LOG_FILE:
        log_path = Path(settings.LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_path,
            format=log_format,
            level=settings.LOG_LEVEL,
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            backtrace=True,
            diagnose=True,
        )
    
    # Intercepta logs de outras bibliotecas
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Configura níveis de log para bibliotecas específicas
    for logger_name in ["uvicorn", "uvicorn.access", "fastapi"]:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
    
    logger.info("Sistema de logging configurado com sucesso")


# Inicializa logging
setup_logging()
