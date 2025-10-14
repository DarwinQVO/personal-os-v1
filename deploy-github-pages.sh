#!/bin/bash

# 🚀 Deploy GitHub Pages - Personal OS V1
# Este script hace commit y push de los archivos de GitHub Pages

set -e  # Exit on error

echo "📊 Personal OS V1 - GitHub Pages Deploy"
echo "========================================"
echo ""

# Directorio del proyecto
cd "/Users/darwinborges/personal control system /personal-os-v1"

# Mostrar estado
echo "📋 Archivos para GitHub Pages:"
ls -lh docs/index.html docs/system-architecture-current.html docs/hybrid-entity-resolution-docs.html docs/README.md docs/DIAGRAMA_BPMN_MEDIDAS.md 2>/dev/null || echo "❌ Algunos archivos no encontrados"
echo ""

# Verificar si hay cambios
if [[ -z $(git status --porcelain docs/) ]]; then
    echo "✅ No hay cambios en docs/ para commit"
else
    echo "📝 Cambios detectados en docs/"
    echo ""

    # Mostrar cambios
    git status docs/
    echo ""

    # Preguntar confirmación
    read -p "¿Hacer commit y push a GitHub? (y/n): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Add files
        echo "📦 Adding files..."
        git add docs/index.html
        git add docs/README.md
        git add docs/DIAGRAMA_BPMN_MEDIDAS.md
        git add docs/system-architecture-current.html
        git add docs/hybrid-entity-resolution-docs.html
        git add GITHUB_PAGES_SETUP.md

        # Commit
        echo "💾 Creating commit..."
        git commit -m "Add GitHub Pages with interactive BPMN diagram

- Interactive BPMN swimlane diagram (S1-S4)
- Complete system documentation
- Production metrics visualization
- Responsive grayscale design
- System architecture and entity resolution pages"

        # Push
        echo "🚀 Pushing to GitHub..."
        git push origin master || git push origin main

        echo ""
        echo "✅ Deploy complete!"
        echo ""
        echo "🌐 Tu sitio estará disponible en:"
        echo "   https://[TU-USUARIO].github.io/personal-os-v1/"
        echo ""
        echo "📝 Próximos pasos:"
        echo "   1. Ve a GitHub.com → tu repositorio"
        echo "   2. Settings → Pages"
        echo "   3. Source: master (o main) → /docs"
        echo "   4. Save"
        echo "   5. Espera 1-2 minutos"
        echo ""
    else
        echo "❌ Deploy cancelado"
    fi
fi

echo ""
echo "📚 Ver instrucciones completas: GITHUB_PAGES_SETUP.md"
