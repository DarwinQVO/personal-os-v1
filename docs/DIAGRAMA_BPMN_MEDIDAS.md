# Medidas Exactas del Diagrama BPMN

**Archivo:** `docs/mapeo-proceso-completo.html`
**Fecha:** 2025-10-14
**Estado:** ✅ Medidas finales verificadas

---

## 📐 DIMENSIONES DEL SVG

```
<svg width="1400" height="1100" viewBox="0 0 1400 1100">
```

**Total:**
- Width: 1400px
- Height: 1100px
- Responsive: viewBox ajusta automáticamente

---

## 🏊 SWIMLANES (Carriles Horizontales)

### INPUT
```
Y: 0px
Height: 150px
Fill: #f9fafb (gris muy claro)
```

### STAGE 1: EXTRACTION
```
Y: 150px
Height: 160px
Fill: white
```

### STAGE 2: OBSERVATION LAYER
```
Y: 310px
Height: 160px
Fill: #f9fafb (gris muy claro)
```

### STAGE 2.5: ENTITY RESOLUTION
```
Y: 470px
Height: 180px
Fill: white
```

### STAGE 3: RECONCILIATION
```
Y: 650px
Height: 170px
Fill: #f9fafb (gris muy claro)
```

### STAGE 4: CANONICAL LEDGER
```
Y: 820px
Height: 180px
Fill: white
```

**Total Height usado:** 1000px (deja 100px de margen inferior)

---

## 📦 ELEMENTOS ESTÁNDAR

### Labels Verticales (Texto rotado)
```
X: 30px (desde el borde izquierdo)
Font-size: 16px
Font-weight: bold
Color: #374151 (gris oscuro)
Transform: rotate(-90)
```

### Círculos (Inicio/Fin)
```
Radius: 25px
Fill: white
Stroke: #333 (negro)
Stroke-width: 2px

Posiciones:
- Inicio: cx="150" cy="75"
- Fin: cx="850" cy="895"
```

### Rectángulos de Proceso
```
Width: 180-220px
Height: 70px
Border-radius: 5px
Fill: white
Stroke: #333 (negro)
Stroke-width: 2px

Posiciones X típicas: 150, 250, 390, 510
Espaciado horizontal: ~40-60px entre elementos
```

### Rectángulos de Data/Output
```
Width: 200-240px
Height: 50px
Border-radius: 5px
Fill: #e5e7eb (gris claro)
Stroke: #6b7280 (gris medio)
Stroke-width: 1px
Stroke-dasharray: 4,4 (línea punteada)

Posiciones X típicas: 540, 630, 750
```

### Elipse de Decisión
```
RX: 65px (radio horizontal)
RY: 35px (radio vertical)
Fill: white
Stroke: #333 (negro)
Stroke-width: 2px

Posición: cx="930" cy="545"
```

### Flechas
```
Stroke: #333 (negro)
Stroke-width: 2px
Marker: arrowhead (punta de flecha)

Arrowhead spec:
  markerWidth: 10
  markerHeight: 10
  refX: 9
  refY: 3
```

---

## 🔤 TIPOGRAFÍA

### Títulos de Proceso
```
Font-family: Arial, sans-serif
Font-size: 14px
Font-weight: bold
Fill: #333 (negro)
Text-anchor: middle
```

### Subtítulos (scripts, tiempos)
```
Font-family: Arial, sans-serif
Font-size: 11px
Fill: #666 (gris)
Text-anchor: middle
```

### Labels de Swimlane
```
Font-family: Arial, sans-serif
Font-size: 16px
Font-weight: bold
Fill: #374151 (gris oscuro)
```

---

## 📍 POSICIONES CLAVE (X, Y)

### Columna 1 (Procesos principales)
```
X: 250-470px
Ancho típico: 220px
```

### Columna 2 (Data/Output)
```
X: 540-780px
Ancho típico: 200-240px
```

### Columna 3 (Elementos adicionales)
```
X: 850-995px
Ancho típico: 180px
```

### Leyenda
```
X: 1100px (esquina superior derecha)
Y: 40px
Espacio entre líneas: 25px
```

---

## 🎨 PALETA DE COLORES

### Backgrounds
```
#ffffff - Blanco (procesos, swimlanes alternados)
#f9fafb - Gris muy claro (swimlanes alternados)
#e5e7eb - Gris claro (data boxes)
```

### Borders
```
#d1d5db - Gris medio (swimlanes)
#6b7280 - Gris oscuro (data boxes)
#333333 - Negro (procesos, flechas)
```

### Texto
```
#333333 - Negro (títulos)
#666666 - Gris medio (subtítulos)
#374151 - Gris oscuro (labels)
```

---

## 📏 ESPACIADO

### Entre swimlanes
```
0px (sin gap, líneas continuas)
```

### Dentro de swimlane
```
Margen superior: 40-50px desde el borde del swimlane
Margen inferior: 40-50px hasta el borde del swimlane
```

### Entre elementos horizontales
```
Gap típico: 60-90px
```

### Entre procesos en secuencia
```
Gap vertical: 80-100px (cuando flujo va hacia abajo)
```

---

## 🔄 FLUJOS DE DATOS

### Verticales (entre swimlanes)
```
X consistente (ej: 360, 640, 740, 850)
Longitud típica: igual a height del swimlane
```

### Horizontales (dentro de swimlane)
```
Y consistente (centrado en el swimlane)
Longitud variable según distancia entre elementos
```

### Diagonal
```
Evitado en este diseño (solo vertical u horizontal)
```

---

## 📋 TEMPLATE PARA NUEVOS SWIMLANES

```xml
<!-- Swimlane: [NOMBRE] -->
<g>
    <rect x="0" y="[Y_POS]" width="1400" height="[HEIGHT]"
          fill="[#ffffff o #f9fafb]" stroke="#d1d5db" stroke-width="2"/>
    <text x="30" y="[Y_POS + HEIGHT/2]"
          font-family="Arial, sans-serif" font-size="16"
          font-weight="bold" fill="#374151"
          transform="rotate(-90 30 [Y_POS + HEIGHT/2])">[NOMBRE]</text>

    <!-- Proceso principal -->
    <rect x="250" y="[Y_POS + 40]" width="220" height="70"
          rx="5" fill="white" stroke="#333" stroke-width="2"/>
    <text x="360" y="[Y_POS + 67]"
          font-family="Arial, sans-serif" font-size="14"
          font-weight="bold" fill="#333" text-anchor="middle">[Título]</text>
    <text x="360" y="[Y_POS + 85]"
          font-family="Arial, sans-serif" font-size="11"
          fill="#666" text-anchor="middle">[Subtítulo]</text>

    <!-- Data box -->
    <rect x="540" y="[Y_POS + 50]" width="200" height="50"
          rx="5" fill="#e5e7eb" stroke="#6b7280"
          stroke-width="1" stroke-dasharray="4,4"/>
    <text x="640" y="[Y_POS + 72]"
          font-family="Arial, sans-serif" font-size="12"
          fill="#333" text-anchor="middle">[Output name]</text>
    <text x="640" y="[Y_POS + 88]"
          font-family="Arial, sans-serif" font-size="11"
          fill="#666" text-anchor="middle">[Size info]</text>

    <!-- Arrows -->
    <line x1="470" y1="[Y_POS + 75]" x2="540" y2="[Y_POS + 75]"
          stroke="#333" stroke-width="2" marker-end="url(#arrowhead)"/>
</g>
```

---

## ✅ CHECKLIST PARA NUEVOS DIAGRAMAS

- [ ] Total SVG width/height calculado antes de empezar
- [ ] Altura de cada swimlane definida (considerar contenido + margen)
- [ ] Posiciones Y calculadas acumulativamente
- [ ] Posiciones X en columnas consistentes
- [ ] Tamaños de fuente estandarizados (14px títulos, 11px texto)
- [ ] Colores de la paleta definida
- [ ] Espaciado entre elementos consistente (60-90px horizontal)
- [ ] Labels verticales con transform rotate(-90)
- [ ] Flechas con marker-end para puntas
- [ ] Responsive viewBox configurado

---

## 📐 FÓRMULAS DE CÁLCULO

### Posición Y de un swimlane
```
Y_swimlane = suma de heights de todos los swimlanes anteriores
```

### Centrado vertical de texto en box
```
Y_text = Y_box + (Height_box / 2) + 7px (ajuste óptico)
```

### Centrado horizontal de texto
```
X_text = X_box + (Width_box / 2)
text-anchor = "middle"
```

### Posición de label vertical
```
X = 30px (fijo)
Y = Y_swimlane + (Height_swimlane / 2)
transform = rotate(-90 X Y)
```

---

**Nota:** Estas medidas están probadas y verificadas en producción.
No ajustar sin recalcular todo el layout.

**Última verificación:** 2025-10-14 16:45
**Estado:** ✅ Funcionando perfectamente
