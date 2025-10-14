# 📘 Configuración de GitHub Pages

## Pasos para Publicar

### 1. Crear Repositorio en GitHub

Si aún no tienes un repositorio:

```bash
# En GitHub.com:
# 1. Ve a https://github.com/new
# 2. Nombre: "personal-os-v1" (o el que prefieras)
# 3. Público o Privado (GitHub Pages funciona en ambos con cuenta Pro)
# 4. NO inicialices con README (ya tienes archivos)
```

### 2. Conectar Repositorio Local

```bash
cd "/Users/darwinborges/personal control system /personal-os-v1"

# Si no has inicializado git:
git init

# Agrega el remote (reemplaza con tu usuario):
git remote add origin https://github.com/TU-USUARIO/personal-os-v1.git

# O si ya existe:
git remote set-url origin https://github.com/TU-USUARIO/personal-os-v1.git
```

### 3. Commit y Push

```bash
# Agrega todos los archivos
git add docs/index.html docs/README.md docs/DIAGRAMA_BPMN_MEDIDAS.md

# Commit
git commit -m "Add GitHub Pages with BPMN system diagram

- Interactive BPMN swimlane diagram
- Complete system documentation
- S1-S4 pipeline visualization
- Grayscale professional styling"

# Push
git push -u origin master
# O si usas 'main':
# git push -u origin main
```

### 4. Activar GitHub Pages

1. Ve a tu repositorio en GitHub
2. Click en **Settings** (⚙️)
3. En el menú izquierdo, click en **Pages**
4. En "Source":
   - Branch: `master` (o `main`)
   - Folder: `/docs`
5. Click **Save**

### 5. ¡Listo! 🎉

GitHub Pages generará tu sitio en:

```
https://TU-USUARIO.github.io/personal-os-v1/
```

**Tiempo:** Tarda ~1-2 minutos en publicarse la primera vez.

---

## 🔗 URL Final

Tu diagrama estará disponible en:

```
https://TU-USUARIO.github.io/personal-os-v1/
```

## 📱 Compartir

Puedes compartir la URL directamente. El diagrama es:
- ✅ Responsive (funciona en móvil/tablet/desktop)
- ✅ Interactivo (navegación por secciones)
- ✅ Completo (end-to-end system documentation)

---

## 🔄 Actualizaciones Futuras

Para actualizar el diagrama:

```bash
# 1. Edita docs/index.html
# 2. Commit y push
git add docs/index.html
git commit -m "Update system diagram"
git push

# GitHub Pages se actualiza automáticamente en ~1 minuto
```

---

## 🎨 Archivos Publicados

Todos los archivos en `docs/` estarán disponibles:

- `index.html` - Diagrama principal (landing page)
- `system-architecture-current.html` - Vista de arquitectura
- `hybrid-entity-resolution-docs.html` - Docs de Entity Resolution
- `DIAGRAMA_BPMN_MEDIDAS.md` - Especificaciones técnicas

**Acceso:**
```
https://TU-USUARIO.github.io/personal-os-v1/
https://TU-USUARIO.github.io/personal-os-v1/system-architecture-current.html
https://TU-USUARIO.github.io/personal-os-v1/hybrid-entity-resolution-docs.html
```

---

## ⚙️ Custom Domain (Opcional)

Si tienes un dominio propio:

1. En Settings → Pages → Custom domain
2. Agrega tu dominio (ej: `docs.tudominio.com`)
3. Configura DNS con un CNAME a `TU-USUARIO.github.io`

---

## 🐛 Troubleshooting

### No aparece el sitio

- Verifica que Branch = `master` y Folder = `/docs`
- Espera 2-3 minutos
- Verifica que `docs/index.html` existe en GitHub

### 404 Error

- Asegúrate de que el archivo se llame exactamente `index.html`
- Verifica que esté en la carpeta `/docs`
- Push los cambios con `git push`

### Estilos no cargan

- Verifica que el HTML tenga todos los estilos inline (ya incluidos)
- GitHub Pages usa HTTPS por defecto

---

**¿Necesitas ayuda?** Revisa: https://docs.github.com/pages

**Estado:** ✅ Configuración lista para publicar
**Última actualización:** 2025-10-14
