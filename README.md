# Curso de política

Presentaciones en [Quarto](https://quarto.org) (formato revealjs) para explicar cómo funciona el sistema político español.

| Archivo | Contenido |
|---|---|
| `index.qmd` | Portada del curso con enlaces a las sesiones |
| `01-teoria.qmd` | Sesión 1: Estado y legitimidad, notables y partidos de masas, clivajes, izquierda y derecha, sistemas electorales, Duverger y Michels |
| `02-espana.qmd` | Sesión 2: circunscripciones, D'Hondt (con simulador), bipartidismo, voto estratégico y dual |
| `03-partidos.qmd` | Sesión 3: tipos de sistemas de partidos, número efectivo de partidos, Congreso 2023, oferta 2019/2023 y Tarragona |
| `recursos/img/` | Capturas de la oferta de partidos (2019 y 2023) |
| `recursos/curso.scss` | Estilo visual común |
| `datos/` | Datos que usan los gráficos (generados desde *Simulador elecciones*) |
| `scripts/preparar_datos.py` | Regenera `datos/` a partir de `Simulador elecciones/resultados-generales-web` |

## Ver las presentaciones en tu ordenador

1. Instala Quarto: <https://quarto.org/docs/get-started/>
2. En esta carpeta, ejecuta:

   ```
   quarto preview
   ```

   Se abre el navegador y la página se recarga sola cada vez que guardas un `.qmd`.

Los gráficos interactivos necesitan un servidor, así que abrir los `.html` con doble clic no basta. Usa `quarto preview`.

## Publicar en GitHub Pages

1. Crea un repositorio en GitHub (por ejemplo `curso-politica`) y sube esta carpeta.
2. Ejecuta, una sola vez y después de cada cambio:

   ```
   quarto publish gh-pages
   ```

3. La web quedará en `https://<tu-usuario>.github.io/curso-politica/`.

## Actualizar los datos (por ejemplo, tras el 29-N)

```
python scripts/preparar_datos.py "E:/Datos/Claude/Simulador elecciones/resultados-generales-web"
```

El script lee todas las elecciones de `datos/` del simulador, así que, en cuanto añadas allí la de 2026, aparecerá en el gráfico del bipartidismo.

## Atajos durante la presentación

- `F`: pantalla completa
- `S`: notas del presentador
- `Esc`: vista general de diapositivas
