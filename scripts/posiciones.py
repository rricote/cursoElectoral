"""Genera 06-posiciones.qmd a partir de datos/issues.json.

Las posiciones (0-10) y las frases se editan en datos/issues.json;
las diapositivas las dibuja la propia presentación. Este script solo
hace falta volver a ejecutarlo si se añaden temas o se cambian las notas.
"""
import json
from pathlib import Path

raiz = Path(__file__).resolve().parent.parent
d = json.loads((raiz / "datos/issues.json").read_text(encoding="utf-8"))

cab = '''---
title: "Qué defiende cada partido"
subtitle: "Sesión 6 · Las posiciones de los partidos ante los grandes temas"
format:
  revealjs:
    theme: [default, recursos/curso.scss]
    slide-number: true
    hash-type: number
    transition: fade
    footer: "[Curso de política](index.html) · Sesión 6"
execute:
  echo: false
---

```{ojs}
//| output: false
issues = FileAttachment("datos/issues.json").json()
partidos = issues.partidos
tema = id => issues.temas.find(t => t.id === id)
tinte = (c, a) => c + Math.round(a * 255).toString(16).padStart(2, "0")
escala = id => {
  const t = tema(id)
  const filas = partidos.map(p => {
    const [v, txt] = t.pos[p.k]
    const marca = v === null
      ? html`<span class="ep-sp">sin posición clara</span>`
      : html`<span class="ep-punto" style="left:${v * 10}%;background:${p.c}"></span>`
    return html`<tr style="background:${tinte(p.c, 0.10)}">
      <td class="ep-n"><span class="ep-c" style="background:${p.c}"></span>${p.n}${p.nota ? html`<sup title="${p.nota}">*</sup>` : ""}</td>
      <td class="ep-pista"><div class="ep-linea">${marca}</div></td>
      <td class="ep-t">${v === null ? "—" : txt}</td></tr>`
  })
  return html`<table class="escala-pos">
    <thead><tr><th></th>
      <th><div class="ep-polos"><span>← ${t.izq}</span><span>${t.der} →</span></div></th>
      <th>En pocas palabras</th></tr></thead>
    <tbody>${filas}</tbody></table>
    <div class="ep-pie">Posición orientativa (0-10) a partir de programas, votaciones y declaraciones, noviembre de 2026.
    * CUP y Aliança Catalana no se presentan a las generales del 29-N.</div>`
}
matriz = () => {
  const col = d3.scaleLinear().domain([0, 5, 10]).range(["#5b3f8c", "#f2efe9", "#c8641e"])
  const cab = issues.temas.map(t => html`<th><div>${t.titulo}</div></th>`)
  const filas = partidos.map(p => html`<tr>
    <td class="ep-n"><span class="ep-c" style="background:${p.c}"></span>${p.n}</td>
    ${issues.temas.map(t => {
      const v = t.pos[p.k][0]
      return v === null
        ? html`<td class="mz-sp" title="${t.pos[p.k][1]}">·</td>`
        : html`<td style="background:${col(v)}" title="${t.titulo}: ${t.pos[p.k][1]}"></td>`
    })}</tr>`)
  return html`<table class="matriz-pos"><thead><tr><th></th>${cab}</tr></thead><tbody>${filas}</tbody></table>
  <div class="ep-pie"><span class="mz-ley" style="background:#5b3f8c"></span> primer polo de cada escala
  <span class="mz-ley" style="background:#f2efe9;border:1px solid #ccc"></span> intermedio
  <span class="mz-ley" style="background:#c8641e"></span> segundo polo · <span class="mz-ley" style="background:#fafafa;border:1px solid #ccc"></span> sin posición clara. Pasa el ratón por una casilla para ver la frase.</div>`
}
grupos = [
  {n: "La Izquierda", c: "#9e1b1b", es: 45},
  {n: "Verdes/ALE", c: "#3c9b3c", es: 53},
  {n: "S&D", c: "#e3001b", es: 135},
  {n: "Renew", c: "#f2b400", es: 78},
  {n: "PPE", c: "#3a8fd9", es: 184},
  {n: "ECR", c: "#0d4f8b", es: 84},
  {n: "Patriotas", c: "#3b2470", es: 85},
  {n: "ESN", c: "#6b4a2b", es: 27},
  {n: "No inscritos", c: "#a3a3a3", es: 28}
]
function hemiciclo(partidos, filas = 12, r0 = 0.42) {
  const total = d3.sum(partidos, p => p.es)
  const radios = d3.range(filas).map(i => r0 + (1 - r0) * i / (filas - 1))
  const sumR = d3.sum(radios)
  const porFila = radios.map(r => Math.round(total * r / sumR))
  porFila[filas - 1] += total - d3.sum(porFila)
  const asientos = []
  radios.forEach((r, i) => {
    const n = porFila[i]
    for (let j = 0; j < n; j++) {
      const a = Math.PI - Math.PI * j / (n - 1)
      asientos.push({a, r, x: r * Math.cos(a), y: r * Math.sin(a)})
    }
  })
  asientos.sort((p, q) => q.a - p.a || p.r - q.r)
  let k = 0
  for (const p of partidos) for (let i = 0; i < p.es; i++) Object.assign(asientos[k++], {partido: p.n, c: p.c})
  return asientos
}
eurocamara = () => {
  const plot = Plot.plot({
    width: 560, height: 310, margin: 6,
    x: {axis: null, domain: [-1.04, 1.04]}, y: {axis: null, domain: [-0.04, 1.04]},
    marks: [
      Plot.dot(hemiciclo(grupos), {x: "x", y: "y", fill: "c", r: 3.6, title: "partido"}),
      Plot.text(["720 escaños"], {x: 0, y: 0.2, fontSize: 22, fontWeight: 700, fill: "#333"}),
      Plot.text(["mayoría: 361"], {x: 0, y: 0.08, fontSize: 15, fill: "#555"})
    ]
  })
  const tabla = html`<table class="tabla-esc mini" style="font-size:18px !important">
    <tr><th>Grupo</th><th>Esc.</th><th>%</th></tr>
    ${grupos.map(g => html`<tr style="background:${g.c}22">
      <td><span style="display:inline-block;width:.8em;height:.8em;background:${g.c};border-radius:2px"></span> ${g.n}</td>
      <td><b>${g.es}</b></td><td>${(100 * g.es / 720).toLocaleString("es-ES", {minimumFractionDigits: 1, maximumFractionDigits: 1})}</td></tr>`)}
  </table>`
  return html`<div style="display:grid;grid-template-columns:minmax(0,1.5fr) minmax(0,1fr);gap:14px;align-items:center;width:100%">${plot}${tabla}</div>
  <div class="ep-pie">Composición aproximada a finales de 2026 (un escaño vacante). Grupos ordenados de izquierda a derecha.</div>`
}
```

## Cómo leer esta sesión

::: {.tarjetas}
::: {.tarjeta style="--c:#9b2226"}
[Una diapositiva, un tema]{.tt}
Cada tema tiene dos polos. Cada partido aparece como un punto en una escala de 0 a 10 entre esos dos polos, con una frase que resume su postura.
:::
::: {.tarjeta style="--c:#1d84ce"}
[Partidos en orden]{.tt}
Los partidos van ordenados de izquierda a derecha, como en la sesión 3. Fijaos en cuándo ese orden **se rompe**: ahí aparece el segundo eje.
:::
::: {.tarjeta style="--c:#5aa31f"}
[Es una aproximación]{.tt}
Las posiciones salen de programas del 29-N, votaciones en el Congreso y declaraciones. Son orientativas: discutidlas.
:::
:::

::: notes
Esta sesión cambia de enfoque: ya no hablamos de cómo se reparten los escaños, sino de lo que defiende cada partido. He incluido los partidos del Congreso más cuatro que interesan: CUP y Aliança Catalana (que solo se presentan en Cataluña y no van a las generales del 29-N), SALF de Alvise Pérez y Democracia 21 de Miriam González. Las posiciones son mías, no de un estudio académico: las he sacado de programas, votaciones y declaraciones de 2025 y 2026. Cuando un partido no ha dicho nada claro sobre un tema, lo marco como «sin posición clara» en vez de inventármelo. Lo interesante es ver qué temas ordenan a los partidos de izquierda a derecha y cuáles no.
:::

## Los partidos {.smaller}

::: {.columns}
::: {.column width="50%"}
- **CUP**: izquierda anticapitalista e independentista catalana.
- **Podemos**: izquierda; se presenta solo, salvo en Valencia y Canarias.
- **EH Bildu**: izquierda independentista vasca.
- **Frente Amplio**: Sumar, IU, Más Madrid, Comuns y otros, con Ada Colau.
- **ERC**: izquierda independentista catalana.
- **PSOE**: socialdemocracia; partido del Gobierno.
- **PNV**: nacionalismo vasco democristiano.
:::
::: {.column width="50%"}
- **Democracia 21**: Miriam González; regeneración institucional, se dice «transversal». Solo en Madrid y Barcelona.
- **Junts**: independentismo catalán de centroderecha.
- **PP**: centroderecha; principal partido de la oposición.
- **Aliança Catalana**: derecha radical independentista.
- **Vox**: derecha radical populista.
- **SALF**: Alvise Pérez; populismo antisistema.
:::
:::

::: notes
Un repaso rápido. Democracia 21 rechaza situarse en el eje izquierda-derecha; los análisis la colocan en un espacio liberal y reformista cercano al centro, y por eso la pongo entre el PNV y Junts. Aliança Catalana y Junts comparten el eje independentista pero no el económico ni el migratorio. SALF nació de la candidatura de Alvise a las europeas de 2024.
:::
'''

diapos = []
for t in d["temas"]:
    diapos.append(f'''## {t["titulo"]}

```{{ojs}}
escala("{t["id"]}")
```

::: notes
{t["notas"]}
:::
''')

pie = '''## Todo junto

```{ojs}
matriz()
```

::: notes
La misma información en una sola tabla. Morado es el primer polo de cada escala (normalmente la posición de la izquierda) y naranja el segundo. En la mayoría de temas económicos y sociales los colores van de morado a naranja de arriba abajo: el eje izquierda-derecha funciona. Pero mirad la columna del modelo territorial y la de la monarquía: Junts y Aliança Catalana se ponen morados, y el PSOE se va al centro. Y en la Unión Europea, la CUP y Podemos se acercan a Vox. Es el segundo eje de la sesión 3.
:::

## El Parlamento Europeo

```{ojs}
eurocamara()
```

::: notes
En el Parlamento Europeo los eurodiputados no se sientan por países, sino en grupos ideológicos: las familias de partidos. Para formar un grupo hacen falta al menos 23 eurodiputados de siete Estados distintos. Tras las elecciones de 2024 se formaron ocho grupos. El PPE es el mayor, seguido de los socialistas, y los Patriotas, el nuevo grupo de Orbán, Le Pen, Salvini y Vox, quedaron terceros. Las cifras de la tabla son las actuales y varían algo respecto a 2024 porque algunos eurodiputados cambian de grupo. Nadie tiene mayoría: la Comisión de Von der Leyen se apoya en el bloque central de populares, socialistas y liberales (y a veces los verdes), que suma unos 400 escaños. En algunas votaciones el PPE pacta hacia su derecha con ECR y Patriotas: por eso es el grupo bisagra.
:::

## Las familias europeas y los partidos españoles {.smaller}

<table class="tabla-partidos familias">
<tr><th>Grupo europeo</th><th>Familia ideológica</th><th>Partidos españoles</th></tr>
<tr style="background:#9e1b1b1c"><td><span class="punto" style="background:#9e1b1b"></span><b>La Izquierda</b></td><td>Izquierda radical, comunistas, ecosocialistas</td><td>Podemos (2), EH Bildu (1), parte de Sumar · <i>afines: IU, CUP</i></td></tr>
<tr style="background:#3c9b3c1c"><td><span class="punto" style="background:#3c9b3c"></span><b>Verdes / ALE</b></td><td>Ecologistas y regionalistas de izquierda</td><td>ERC (1), BNG (1), Comuns y Compromís (Sumar)</td></tr>
<tr style="background:#e3001b1c"><td><span class="punto" style="background:#e3001b"></span><b>S&amp;D</b></td><td>Socialdemócratas</td><td>PSOE (20)</td></tr>
<tr style="background:#f2b4001c"><td><span class="punto" style="background:#f2b400"></span><b>Renew</b></td><td>Liberales y centristas</td><td>PNV (1) · <i>afín: Democracia 21; antes, Ciudadanos</i></td></tr>
<tr style="background:#3a8fd91c"><td><span class="punto" style="background:#3a8fd9"></span><b>PPE</b></td><td>Democristianos y centroderecha</td><td>PP (22)</td></tr>
<tr style="background:#0d4f8b1c"><td><span class="punto" style="background:#0d4f8b"></span><b>ECR</b></td><td>Nacional-conservadores (Meloni)</td><td>— <i>(Vox estuvo aquí hasta 2024)</i></td></tr>
<tr style="background:#3b24701c"><td><span class="punto" style="background:#3b2470"></span><b>Patriotas</b></td><td>Derecha radical populista (Le Pen, Orbán)</td><td>Vox (6) · <i>afín: Aliança Catalana</i></td></tr>
<tr style="background:#6b4a2b1c"><td><span class="punto" style="background:#6b4a2b"></span><b>ESN</b></td><td>Extrema derecha soberanista (AfD)</td><td>—</td></tr>
<tr style="background:#a3a3a31c"><td><span class="punto" style="background:#a3a3a3"></span><b>No inscritos</b></td><td>Sin grupo</td><td>Junts (1), SALF</td></tr>
</table>

<div class="ep-pie">Entre paréntesis, eurodiputados elegidos en 2024 (España elige 61). «Afín»: partido sin eurodiputados que encajaría en esa familia.</div>

::: notes
Así se reparten los 61 eurodiputados españoles elegidos en 2024: PP 22, PSOE 20, Vox 6; tres para Ahora Repúblicas, tres para Sumar y tres para Se Acabó la Fiesta; dos para Podemos; uno para Junts y otro para la coalición del PNV. Dos cosas interesantes. Primera: las coaliciones se parten al llegar a Bruselas. Ahora Repúblicas mandó a ERC y al BNG con los Verdes y a EH Bildu con la Izquierda, y Sumar también se repartió entre Verdes e Izquierda. Segunda: Vox cambió de familia en 2024, de los conservadores de Meloni a los Patriotas de Le Pen y Orbán. Junts no se ha integrado en ningún grupo, y el PNV está con los liberales. Las familias europeas son una buena pista para situar a un partido: comparten manifiesto, financiación y votaciones en Bruselas.
:::

## Qué nos enseña

::: {.tarjetas}
::: {.tarjeta style="--c:#9b2226"}
[El eje izquierda-derecha manda]{.tt}
En impuestos, gasto social, vivienda, jornada laboral, aborto o inmigración el orden de los partidos se mantiene casi igual.
:::
::: {.tarjeta style="--c:#00a99d"}
[El eje territorial lo cruza]{.tt}
En independencia o monarquía, Junts y Aliança Catalana están con la izquierda independentista, y lejos del PP y de Vox.
:::
::: {.tarjeta style="--c:#5aa31f"}
[Hay temas transversales]{.tt}
En la Unión Europea o la OTAN se juntan los extremos; en la energía nuclear el PSOE gobierna a medio camino.
:::
:::

::: notes
Tres ideas. Primera: la mayoría de temas se ordenan de izquierda a derecha, lo que explica por qué el eje sigue siendo útil. Segunda: el eje territorial lo cruza, y por eso Junts puede votar con PP y Vox en economía y con ERC en autogobierno; es la llave de la legislatura. Tercera: algunos temas no siguen ningún eje claro, como la UE o la OTAN, donde los extremos de izquierda y derecha desconfían de las instituciones internacionales por razones distintas.
:::

## Resumen de la sesión

1. Cada partido ocupa un lugar distinto en **cada tema**, no solo en el eje izquierda-derecha.
2. Los temas **económicos y sociales** ordenan a los partidos casi siempre igual.
3. El **eje territorial** junta a independentistas de izquierda y de derecha.
4. En **Europa y defensa** los extremos se parecen más entre sí que al centro.
5. En Bruselas los partidos se agrupan en **familias europeas**; populares, socialistas y liberales forman el bloque central.
6. Las posiciones **cambian**: Vox con el aborto, Junts con la inmigración o el PSOE con Almaraz.

<div class="volver"><a href="index.html">← Volver al índice del curso</a></div>

::: notes
Cierre del curso. La última idea es importante: los partidos se mueven según la competencia. Vox ha suavizado su discurso sobre el aborto, Junts ha endurecido el de inmigración ante Aliança Catalana y el Gobierno del PSOE ha prorrogado Almaraz pese a su calendario de cierre. Para el debate: ¿en qué tema os sentís más lejos del partido al que votáis?
:::
'''

(raiz / "06-posiciones.qmd").write_text(cab + "\n".join(diapos) + "\n" + pie, encoding="utf-8")
print("ok")
