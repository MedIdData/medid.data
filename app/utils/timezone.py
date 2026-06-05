"""
Utilitários para gerenciamento de timezone.
Padroniza uso de horário de Brasília (UTC-3).
"""
from datetime import datetime, date, timezone, timedelta
from typing import Optional, Union

# Timezone de Brasília (UTC-3)
BRASILIA_TZ = timezone(timedelta(hours=-3))


def agora_brasilia() -> datetime:
    """Retorna datetime atual em horário de Brasília (UTC-3)."""
    return datetime.now(BRASILIA_TZ)


def para_brasilia(dt: Optional[datetime]) -> Optional[datetime]:
    """Converte datetime UTC para horário de Brasília."""
    if dt is None:
        return None

    # Se já tem timezone, converte
    if dt.tzinfo is not None:
        return dt.astimezone(BRASILIA_TZ)

    # Se é naive (sem timezone), assume UTC e converte
    return dt.replace(tzinfo=timezone.utc).astimezone(BRASILIA_TZ)


def formatar_data_br(dt: Optional[Union[datetime, date]], formato: str = "%d/%m/%Y") -> str:
    """Formata date ou datetime no padrão brasileiro."""
    if dt is None:
        return "-"

    # Se for date (não datetime), formata diretamente
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return dt.strftime(formato)

    # Se for datetime, converte timezone e formata
    dt_br = para_brasilia(dt)
    return dt_br.strftime(formato)


def formatar_data_hora_br(dt: Optional[datetime], formato: str = "%d/%m/%Y %H:%M") -> str:
    """Formata datetime com hora no padrão brasileiro."""
    if dt is None:
        return "-"

    dt_br = para_brasilia(dt)
    return dt_br.strftime(formato)
