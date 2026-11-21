"""Genera los datos del curso a partir del proyecto «Simulador elecciones».

Uso:
    python scripts/preparar_datos.py "E:/Datos/Claude/Simulador elecciones/resultados-generales-web"

Escribe en datos/:
  - bipartidismo.csv   (escaños y votos de los dos primeros partidos, 1977-2023)
  - provincias_2023.json (votos, escaños y color de cada partido por provincia, 2023)
  - mapa_provincias.json (contornos SVG de las provincias)
  - nep.csv            (número efectivo de partidos por votos y por escaños, 1977-2023)
  - congreso_2023.json (partidos con escaño en 2023: escaños, % de voto y color)
"""
import glob
import json
import os
import shutil
import sys

ORIGEN = sys.argv[1] if len(sys.argv) > 1 else "../Simulador elecciones/resultados-generales-web"
DESTINO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datos")

ETIQUETA = {"UCD": "UCD", "PSOE": "PSOE", "PP": "AP/PP"}
COLOR_BLOQUE = {"UCD": "#2e9e5b", "PSOE": "#e30613", "PP": "#1d84ce"}


def cargar(ruta):
    texto = open(ruta, encoding="utf-8").read()
    if texto.lstrip().startswith("("):
        texto = texto[texto.index("]=") + 2:].rstrip().rstrip(";")
    return json.loads(texto)


def dhondt(votos, escanos):
    asignados = [0] * len(votos)
    for _ in range(escanos):
        i = max(range(len(votos)), key=lambda k: votos[k] / (asignados[k] + 1))
        asignados[i] += 1
    return asignados


def main():
    os.makedirs(DESTINO, exist_ok=True)

    # 1. Bipartidismo
    filas = ["eleccion,anio,etiqueta,partido,escanos,pct_escanos,pct_votos,orden"]
    for ruta in sorted(glob.glob(os.path.join(ORIGEN, "datos", "*", "general.json*"))):
        if ruta.endswith(".json") and os.path.exists(ruta + ".js"):
            continue
        j = cargar(ruta)
        nat, partidos = j["nat"], j["parties"]
        total_votos = sum(nat["v"]) + nat.get("bl", 0)
        total_esc = sum(nat["es"])
        orden = sorted(range(len(partidos)), key=lambda i: -nat["es"][i])[:2]
        etiqueta = j["id"][:4] + (" (abr)" if j["id"] == "2019-04" else " (nov)" if j["id"] == "2019-11" else "")
        for pos, i in enumerate(orden, 1):
            k = partidos[i]["k"]
            filas.append(
                f'{j["id"]},{j["year"]},{etiqueta},{ETIQUETA.get(k, k)},{nat["es"][i]},'
                f'{100 * nat["es"][i] / total_esc:.2f},{100 * nat["v"][i] / total_votos:.2f},{pos}'
            )
    open(os.path.join(DESTINO, "bipartidismo.csv"), "w", encoding="utf-8").write("\n".join(filas) + "\n")

    # 2. Provincias 2023 (para el simulador D'Hondt)
    j = cargar(os.path.join(ORIGEN, "datos", "2023-07", "general.json.js"))
    partidos = j["parties"]
    provincias = []
    fallos = 0
    for p in j["prov"]:
        votos = [a + b for a, b in zip(p["v"], p.get("cera", [0] * len(p["v"])))]
        blancos = p["bl"] + p.get("cera_bl", 0)
        validos = sum(votos) + blancos
        lista = [
            {"k": partidos[i]["k"], "n": partidos[i]["n"], "c": partidos[i]["c"], "v": v, "es": p["es"][i]}
            for i, v in enumerate(votos)
            if v > 0 and (v / validos >= 0.01 or p["es"][i] > 0)
        ]
        lista.sort(key=lambda x: -x["v"])
        # comprobación: D'Hondt con barrera del 3 %
        elegibles = [x["v"] if x["v"] >= 0.03 * validos else 0 for x in lista]
        if dhondt(elegibles, p["s"]) != [x["es"] for x in lista]:
            fallos += 1
            print("Aviso: el reparto no coincide en", p["n"])
        provincias.append({"id": p["id"], "n": p["n"], "s": p["s"], "blancos": blancos, "validos": validos, "partidos": lista})
    json.dump(provincias, open(os.path.join(DESTINO, "provincias_2023.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(f"Provincias: {len(provincias)}; repartos que no coinciden con el oficial: {fallos}")

    # 3. Número efectivo de partidos (Laakso-Taagepera)
    filas = ["eleccion,anio,etiqueta,nep_votos,nep_escanos,partidos_con_escano"]
    for ruta in sorted(glob.glob(os.path.join(ORIGEN, "datos", "*", "general.json*"))):
        if ruta.endswith(".json") and os.path.exists(ruta + ".js"):
            continue
        j = cargar(ruta)
        nat = j["nat"]
        tv, te = sum(nat["v"]), sum(nat["es"])
        nep_v = 1 / sum((v / tv) ** 2 for v in nat["v"])
        nep_e = 1 / sum((e / te) ** 2 for e in nat["es"])
        etiqueta = j["id"][:4] + (" (abr)" if j["id"] == "2019-04" else " (nov)" if j["id"] == "2019-11" else "")
        filas.append(f'{j["id"]},{j["year"]},{etiqueta},{nep_v:.2f},{nep_e:.2f},{sum(1 for e in nat["es"] if e > 0)}')
    open(os.path.join(DESTINO, "nep.csv"), "w", encoding="utf-8").write("\n".join(filas) + "\n")

    # 4. Congreso 2023
    j = cargar(os.path.join(ORIGEN, "datos", "2023-07", "general.json.js"))
    nat, partidos = j["nat"], j["parties"]
    total = sum(nat["v"]) + nat.get("bl", 0)
    congreso = [
        {"k": p["k"], "n": p["n"], "c": p["c"], "es": nat["es"][i], "pct": round(100 * nat["v"][i] / total, 2)}
        for i, p in enumerate(partidos) if nat["es"][i] > 0
    ]
    json.dump(congreso, open(os.path.join(DESTINO, "congreso_2023.json"), "w", encoding="utf-8"), ensure_ascii=False)

    # 5. Mapa
    shutil.copy(os.path.join(ORIGEN, "fuentes", "mapa_provincias.json"), os.path.join(DESTINO, "mapa_provincias.json"))


if __name__ == "__main__":
    main()
