"""
Serviço de autenticação: hashing de senha, JWT access/refresh tokens, chaves de acesso.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Senha ─────────────────────────────────────────────────────────────────

def hash_senha(senha: str) -> str:
    return pwd_context.hash(str(senha).strip())


def verificar_senha(senha: str, hash: str) -> bool:
    print("=" * 80)
    print("DEBUG LOGIN")
    print("SENHA_LEN =", len(str(senha)))
    print("SENHA_REPR =", repr(senha))
    print("HASH_LEN =", len(str(hash)))
    print("HASH_PREFIX =", str(hash)[:30])
    print("=" * 80)

    try:
        return pwd_context.verify(str(senha).strip(), hash)
    except Exception as e:
        print("ERRO VERIFY =", str(e))
        raise


def gerar_senha_temporaria() -> str:
    """Gera senha temporária aleatória (será substituída no primeiro acesso)."""
    return secrets.token_urlsafe(16)


# ── JWT ───────────────────────────────────────────────────────────────────

def criar_access_token(usuario_id: int, email: str, perfil: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": str(usuario_id),
        "email": email,
        "perfil": perfil,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def criar_refresh_token(usuario_id: int) -> tuple[str, datetime]:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    payload = {
        "sub": str(usuario_id),
        "exp": expire,
        "type": "refresh",
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token, expire


def decodificar_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# ── Chaves de Acesso ──────────────────────────────────────────────────────

def gerar_chave_acesso() -> tuple[str, str, str]:
    """Retorna (token_completo, prefixo_exibicao, hash_sha256)."""
    raw = secrets.token_hex(24)
    token = f"med_{raw}"
    prefixo = f"med_{raw[:8]}..."
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token, prefixo, token_hash


def hash_chave(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()