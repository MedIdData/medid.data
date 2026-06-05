# Componentes UI - MedID Data

## 🎨 Design System

### Cores

```css
--azul:        #0F4C81  /* Primário */
--azul-escuro: #082D4D  /* Sidebar */
--azul-medio:  #1A6BB5  /* Links */
--teal:        #14B8A6  /* Destaque/Sucesso */
--teal-claro:  #2DD4BF  /* Hover */
--ambar:       #F59E0B  /* Atenção */
--vermelho:    #EF4444  /* Erro/Risco Alto */
--branco:      #FFFFFF
--fundo:       #F8FAFC  /* Background página */
--fundo-sec:   #EFF4F9  /* Background secundário */
--texto:       #1E293B  /* Texto primário */
--texto-sec:   #475569  /* Texto secundário */
--texto-ter:   #94A3B8  /* Texto terciário */
--borda:       #CBD5E1  /* Bordas */
```

### Tipografia

```css
/* Títulos */
font-family: 'Syne', sans-serif;
font-weight: 700 | 800;

/* Corpo */
font-family: 'DM Sans', sans-serif;
font-weight: 300 | 400 | 500;
```

### Raios de Borda

```css
--r-card:  12px  /* Cards */
--r-botao: 8px   /* Botões */
--r-campo: 8px   /* Inputs */
--r-etiq:  20px  /* Badges/Tags */
```

### Sombras

```css
--shadow-sm: 0 1px 3px rgba(0,0,0,.08);
--shadow-md: 0 4px 12px rgba(0,0,0,.10);
```

---

## 📦 Componentes Reutilizáveis

### `.card`
Container padrão com fundo branco, borda e sombra

```html
<div class="card">
  <div class="card-header">
    <h2 class="card-titulo">Título</h2>
    <span class="badge badge-info">Badge</span>
  </div>
  <div class="card-body">
    Conteúdo
  </div>
</div>
```

**CSS**:
```css
.card {
  background: var(--branco);
  border: 1px solid var(--borda);
  border-radius: var(--r-card);
  box-shadow: var(--shadow-sm);
}
.card-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--borda);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-body {
  padding: 20px 24px;
}
```

---

### `.btn`
Botões com variantes

```html
<button class="btn btn-primario">Ação Principal</button>
<button class="btn btn-secundario">Ação Secundária</button>
<button class="btn btn-perigo">Excluir</button>
```

**CSS**:
```css
.btn {
  padding: 10px 20px;
  border: none;
  border-radius: var(--r-botao);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}
.btn-primario {
  background: var(--azul);
  color: var(--branco);
}
.btn-primario:hover {
  background: var(--azul-escuro);
}
.btn-secundario {
  background: var(--fundo-sec);
  color: var(--texto-sec);
  border: 1px solid var(--borda);
}
.btn-perigo {
  background: var(--vermelho);
  color: var(--branco);
}
```

---

### `.badge`
Etiquetas/Tags coloridas

```html
<span class="badge badge-info">100 chaves</span>
<span class="badge badge-success">Ativo</span>
<span class="badge badge-warning">Atenção</span>
<span class="badge badge-danger">Inativo</span>
```

**CSS**:
```css
.badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: var(--r-etiq);
  font-size: 0.75rem;
  font-weight: 500;
}
.badge-info    { background: #EFF4F9; color: #0F4C81; }
.badge-success { background: #F0FDF4; color: #166534; }
.badge-warning { background: #FFFBEB; color: #92400E; }
.badge-danger  { background: #FFF1F2; color: #991B1B; }
```

---

### `.alerta`
Mensagens de feedback

```html
<div class="alerta alerta-sucesso">
  <div class="alerta-icone">✓</div>
  <div class="alerta-conteudo">
    <div class="alerta-titulo">Sucesso!</div>
    <div class="alerta-texto">Ação concluída.</div>
  </div>
</div>
```

**Variantes**: `alerta-sucesso`, `alerta-erro`, `alerta-info`, `alerta-warning`

---

### `.tabela`
Tabelas responsivas

```html
<div class="tabela-wrapper">
  <table class="tabela">
    <thead>
      <tr>
        <th>Coluna 1</th>
        <th>Coluna 2</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Valor 1</td>
        <td>Valor 2</td>
      </tr>
    </tbody>
  </table>
</div>
```

**CSS**:
```css
.tabela-wrapper {
  overflow-x: auto;
}
.tabela {
  width: 100%;
  border-collapse: collapse;
}
.tabela th {
  text-align: left;
  padding: 12px 16px;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--texto-ter);
  text-transform: uppercase;
  border-bottom: 1px solid var(--borda);
}
.tabela td {
  padding: 14px 16px;
  font-size: 0.875rem;
  border-bottom: 1px solid var(--fundo-sec);
}
```

---

### `.modal`
Overlay modal

```html
<div id="modal" class="modal">
  <div class="modal-overlay" onclick="fecharModal()"></div>
  <div class="modal-conteudo">
    <div class="modal-header">
      <h2 class="modal-titulo">Título</h2>
      <button class="btn-fechar" onclick="fecharModal()">×</button>
    </div>
    <div class="modal-body">
      Conteúdo
    </div>
    <div class="modal-footer">
      <button class="btn btn-primario">Confirmar</button>
    </div>
  </div>
</div>
```

**CSS**:
```css
.modal {
  display: none;
  position: fixed;
  inset: 0;
  z-index: 1000;
}
.modal.ativo {
  display: block;
}
.modal-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
}
.modal-conteudo {
  position: relative;
  background: var(--branco);
  max-width: 500px;
  margin: 10% auto;
  border-radius: var(--r-card);
}
```

---

### `.dropdown-menu`
Menu dropdown (usado no header)

```html
<div class="dropdown-menu" id="menu">
  <a href="/perfil" class="dropdown-item">Perfil</a>
  <div class="dropdown-divider"></div>
  <button class="dropdown-item perigo">Sair</button>
</div>
```

**CSS** (ver base.html linhas 224-280)

---

### `.campo` / `.form-input`
Campos de formulário

```html
<div class="form-group">
  <label for="nome">Nome</label>
  <input type="text" id="nome" class="form-input" placeholder="Digite...">
</div>
```

**CSS**:
```css
.form-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--borda);
  border-radius: var(--r-campo);
  font-size: 0.95rem;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.form-input:focus {
  outline: none;
  border-color: var(--azul);
  box-shadow: 0 0 0 3px rgba(15, 76, 129, 0.1);
}
```

---

### `.medidor-card`
Gauge circular (análise.html)

```html
<div class="medidor-wrap">
  <svg class="medidor-svg" viewBox="0 0 120 120">
    <circle class="trilha" cx="60" cy="60" r="45" />
    <circle class="arco" id="arco-aderencia"
            data-valor="75" data-total-arco="283"
            cx="60" cy="60" r="45" />
  </svg>
  <div class="medidor-numero" id="num-aderencia">0</div>
</div>
```

**JavaScript** (animação):
```js
const arco = document.getElementById('arco-aderencia');
const valor = parseInt(arco.dataset.valor);
const totalArco = parseFloat(arco.dataset.totalArco);
const offset = totalArco * (1 - valor / 100);
arco.style.strokeDashoffset = offset;
```

---

## 📱 Grid Responsivo

```html
<div class="grid-2">
  <div class="card">Coluna 1</div>
  <div class="card">Coluna 2</div>
</div>
```

**CSS**:
```css
.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
@media (max-width: 768px) {
  .grid-2 { grid-template-columns: 1fr; }
}
```

Variantes: `.grid-3`, `.grid-4`

---

**Última atualização**: 2026-06-04  
**Versão**: 1.0.0
