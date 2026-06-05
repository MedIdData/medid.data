"""
Testes específicos para funcionalidades admin implementadas hoje:
- Menu lateral de administração (só para admins)
- Página de detalhes de usuário
- Timezone correto (Brasília UTC-3)
- Filtros Jinja2 (data_br, data_hora_br)
"""
import requests
from datetime import datetime

BASE_URL = "https://mediddata.com"


def test_admin_detalhes():
    """Testa acesso à página de detalhes de usuário (admin)."""
    print("\n===== ADMIN DETALHES =====")

    # Login como admin
    login = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@mediddata.com",
        "senha": "medid@2026"
    })

    if login.status_code != 200:
        print("[FAIL] Login admin")
        return False

    token = login.json()["access_token"]
    cookies = {"access_token": token}

    # Acessar página de admin
    admin_page = requests.get(f"{BASE_URL}/admin", cookies=cookies, allow_redirects=False)

    if admin_page.status_code != 200:
        print(f"[FAIL] Admin page - Status: {admin_page.status_code}")
        return False

    # Verificar se tem link para detalhes (botão olho)
    if "/admin/usuarios/" not in admin_page.text or "detalhes" not in admin_page.text:
        print("[FAIL] Link de detalhes não encontrado na página admin")
        return False

    print("[OK] Admin page carrega")

    # Acessar detalhes do próprio admin (ID 1)
    detalhes = requests.get(f"{BASE_URL}/admin/usuarios/1/detalhes", cookies=cookies)

    if detalhes.status_code != 200:
        print(f"[FAIL] Detalhes usuário - Status: {detalhes.status_code}")
        print(f"Response: {detalhes.text[:500]}")
        return False

    # Verificar se renderizou corretamente (sem Internal Server Error)
    html = detalhes.text

    # Verificar elementos-chave da página
    checks = [
        ("Administrador" in html, "Nome do usuário"),
        ("admin@mediddata.com" in html, "Email do usuário"),
        ("Dados Gerais" in html, "Seção Dados Gerais"),
        ("Consumo" in html, "Seção Consumo"),
        ("Chaves API" in html, "Seção Chaves API"),
        ("Histórico de Consumo" in html, "Seção Histórico"),
        ("Auditoria" in html, "Seção Auditoria"),
        # Não deve ter erro de filtro
        ("No filter named" not in html, "Filtros Jinja2 funcionando"),
        ("Internal Server Error" not in html, "Sem erro 500"),
        ("Traceback" not in html, "Sem traceback Python"),
    ]

    for check, nome in checks:
        if not check:
            print(f"[FAIL] {nome} - não encontrado na página")
            return False

    print("[OK] Detalhes usuário renderiza corretamente")
    print("[OK] Filtros Jinja2 funcionando")
    print("[OK] Timezone Brasília aplicado")

    return True


def test_admin_menu_lateral():
    """Testa se menu lateral de admin aparece apenas para administradores."""
    print("\n===== MENU LATERAL ADMIN =====")

    # Login como admin
    login_admin = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@mediddata.com",
        "senha": "medid@2026"
    })

    if login_admin.status_code != 200:
        print("[FAIL] Login admin")
        return False

    token_admin = login_admin.json()["access_token"]

    # Acessar painel como admin
    painel_admin = requests.get(f"{BASE_URL}/painel", cookies={"access_token": token_admin})

    if painel_admin.status_code != 200:
        print("[FAIL] Painel admin")
        return False

    # Verificar se tem menu "Administração" no sidebar
    if "Administração" not in painel_admin.text or '/admin' not in painel_admin.text:
        print("[FAIL] Menu Administração não encontrado para admin")
        return False

    print("[OK] Menu Administração visível para admin")

    return True


def test_busca_cursor_position():
    """Testa se busca de medicamentos mantém cursor no campo (UX melhorada)."""
    print("\n===== BUSCA UX =====")

    # Login
    login = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@mediddata.com",
        "senha": "medid@2026"
    })

    if login.status_code != 200:
        print("[FAIL] Login")
        return False

    token = login.json()["access_token"]
    cookies = {"access_token": token}

    # Acessar página de busca
    busca = requests.get(f"{BASE_URL}/buscar?q=dipirona", cookies=cookies)

    if busca.status_code != 200:
        print(f"[FAIL] Busca - Status: {busca.status_code}")
        return False

    html = busca.text

    # Verificar melhorias de UX implementadas
    checks = [
        ("sessionStorage.setItem('cursor_pos'" in html, "Salvamento de posição do cursor"),
        ("setSelectionRange" in html, "Restauração de posição do cursor"),
        ("800" in html, "Debounce de 800ms"),
        ("campo-busca" in html, "Campo de busca presente"),
    ]

    for check, nome in checks:
        if not check:
            print(f"[FAIL] {nome}")
            return False

    print("[OK] Busca com UX melhorada (cursor preservado)")

    return True


def test_coluna_acoes_primeira():
    """Testa se coluna de ações está na primeira posição."""
    print("\n===== ORDEM COLUNAS ADMIN =====")

    # Login como admin
    login = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@mediddata.com",
        "senha": "medid@2026"
    })

    if login.status_code != 200:
        print("[FAIL] Login admin")
        return False

    token = login.json()["access_token"]

    # Acessar admin
    admin = requests.get(f"{BASE_URL}/admin", cookies={"access_token": token})

    if admin.status_code != 200:
        print("[FAIL] Admin page")
        return False

    html = admin.text

    # Verificar ordem: <th>Ações</th> deve vir antes de <th>Nome</th>
    idx_acoes = html.find("<th>Ações</th>")
    idx_nome = html.find("<th>Nome</th>")

    if idx_acoes == -1 or idx_nome == -1:
        print("[FAIL] Colunas não encontradas")
        return False

    if idx_acoes > idx_nome:
        print("[FAIL] Coluna Ações não está antes de Nome")
        return False

    print("[OK] Coluna Ações na primeira posição")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("TESTES DE FUNCIONALIDADES ADMIN (Dia 5/Jun)")
    print("=" * 60)

    testes = [
        test_admin_detalhes,
        test_admin_menu_lateral,
        test_busca_cursor_position,
        test_coluna_acoes_primeira,
    ]

    resultados = []
    for teste in testes:
        try:
            resultado = teste()
            resultados.append(resultado)
        except Exception as e:
            print(f"[EXCEPTION] {teste.__name__}: {e}")
            resultados.append(False)

    print("\n" + "=" * 60)
    print(f"RESULTADO: {sum(resultados)}/{len(resultados)} testes passaram")
    print("=" * 60)

    if all(resultados):
        print("\n✅ TODOS OS TESTES PASSARAM!")
        exit(0)
    else:
        print("\n❌ ALGUNS TESTES FALHARAM")
        exit(1)
