"""Genera los datos del curso a partir del proyecto «Simulador elecciones».

Uso:
    python scripts/preparar_datos.py "E:/Datos/Claude/Simulador elecciones/resultados-generales-web"

Escribe en datos/:
  - bipartidismo.csv   (escaños y votos de los dos primeros partidos, 1977-2023)
  - provincias_2023.json (votos, escaños y color de cada partido por provincia, 2023)
  - mapa_provincias.json (contornos SVG de las provincias)
  - nep.csv            (número efectivo de partidos por votos y por escaños, 1977-2023)
  - congreso_2023.json (partidos con escaño en 2023: escaños, % de voto y color)
  - efectos.json       (sesión 4: escaños por provincia de cada partido o grupo, votos frente
                        a escaños, coste de un escaño e índice de Gallagher, 2015-2023)
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


# Grupos de la sesión 4 ------------------------------------------------------
UP_POR_ELECCION = {
    "2015-12": ["PODEMOS", "ECP", "COMPROMIS", "ENMAREA"],
    "2016-06": ["PODEMOS", "ECP", "COMPROMIS", "ENMAREA"],
    "2019-04": ["PODEMOS", "ECP"],
    "2019-11": ["PODEMOS", "ECP"],
    "2023-07": [],
}
GRUPOS = {
    "2015-12": [("PP", ["PP"]), ("PSOE", ["PSOE"]), ("UP", None), ("CS", ["CS"]),
                ("OTROS_IZQ", ["ERC", "BILDU", "IU"]), ("OTROS_DER", ["CIU", "PNV", "CC"])],
    "2016-06": [("PP", ["PP"]), ("PSOE", ["PSOE"]), ("UP", None), ("CS", ["CS"]),
                ("OTROS_IZQ", ["ERC", "BILDU"]), ("OTROS_DER", ["CIU", "PNV", "CC"])],
    "2019-04": [("PSOE", ["PSOE"]), ("PP", ["PP"]), ("CS", ["CS"]), ("UP", None), ("VOX", ["VOX"]), ("OTROS", "resto")],
    "2019-11": [("PSOE", ["PSOE"]), ("PP", ["PP"]), ("VOX", ["VOX"]), ("UP", None), ("CS", ["CS"]), ("OTROS", "resto")],
    "2023-07": [("PP", ["PP"]), ("PSOE", ["PSOE"]), ("VOX", ["VOX"]), ("SUMAR", ["SUMAR"]),
                ("OTROS_IZQ", ["ERC", "BILDU", "BNG", "CUP"]), ("OTROS_DER", ["JUNTS", "PNV", "CC", "UPN"])],
}
NOMBRE_UP = {"2015-12": "Podemos y confluencias", "2016-06": "Unidos Podemos y confluencias",
             "2019-04": "Unidas Podemos", "2019-11": "Unidas Podemos", "2023-07": "Unidas Podemos"}
NOMBRES = {"PSOE": "PSOE", "PP": "PP", "CS": "Ciudadanos", "VOX": "Vox", "SUMAR": "Sumar",
           "OTROS": "Otros y nacionalistas", "OTROS_IZQ": "Otros y nacionalistas de izquierda",
           "OTROS_DER": "Otros y nacionalistas de derecha"}
COLORES = {"PSOE": "#e30613", "PP": "#1d84ce", "CS": "#eb6109", "UP": "#7b3f98", "VOX": "#5aa31f", "SUMAR": "#e6007e",
           "OTROS": "#777777", "OTROS_IZQ": "#e8890c", "OTROS_DER": "#0b6b3a"}
ETIQUETAS = {"2015-12": "Diciembre de 2015", "2016-06": "Junio de 2016", "2019-04": "Abril de 2019",
             "2019-11": "Noviembre de 2019", "2023-07": "Julio de 2023"}
EVOLUCION = ["UP", "CS", "VOX", "SUMAR"]


def efectos(origen):
    salida = {}
    for eleccion, grupos in GRUPOS.items():
        j = cargar(os.path.join(origen, "datos", eleccion, "general.json.js"))
        partidos, nat = j["parties"], j["nat"]
        claves = [p["k"] for p in partidos]
        total_v = sum(nat["v"]) + nat.get("bl", 0)
        total_e = sum(nat["es"])
        up = UP_POR_ELECCION[eleccion]
        grupos = [(g, up if ks is None else ks) for g, ks in grupos]
        usados = set(k for _, ks in grupos if isinstance(ks, list) for k in ks)

        def indices(ks):
            if ks == "resto":
                return [i for i, k in enumerate(claves) if k not in usados]
            return [claves.index(k) for k in ks if k in claves]

        def grupo(g, ks):
            idx = indices(ks)
            v = sum(nat["v"][i] for i in idx)
            e = sum(nat["es"][i] for i in idx)
            prov = {}
            for p in j["prov"]:
                es = {claves[i]: p["es"][i] for i in idx if p["es"][i] > 0}
                if not es:
                    continue
                lider = max(es, key=es.get)
                prov[p["id"]] = {"es": sum(es.values()), "c": partidos[claves.index(lider)]["c"],
                                 "lider": partidos[claves.index(lider)]["n"],
                                 "detalle": ", ".join(f'{partidos[claves.index(k)]["n"]} {n}' for k, n in es.items())}
            return {"k": g, "n": NOMBRE_UP[eleccion] if g == "UP" else NOMBRES[g], "c": COLORES[g], "votos": v,
                    "pct": round(100 * v / total_v, 2), "es": e, "pct_es": round(100 * e / total_e, 2), "prov": prov}

        lista = [grupo(g, ks) for g, ks in grupos]
        evolucion = {g: grupo(g, up if g == "UP" else [g]) for g in EVOLUCION}

        # partidos individuales (UP agregado) para votos-escaños y coste
        indiv = {}
        for i, k in enumerate(claves):
            kk = "UP" if k in up else k
            d = indiv.setdefault(kk, {"k": kk, "n": NOMBRE_UP[eleccion] if kk == "UP" else NOMBRES.get(kk, partidos[i]["n"]),
                                      "c": COLORES.get(kk, partidos[i]["c"]), "votos": 0, "es": 0})
            d["votos"] += nat["v"][i]
            d["es"] += nat["es"][i]
        indiv = [d for d in indiv.values() if d["es"] > 0 or d["votos"] / total_v >= 0.01]
        for d in indiv:
            if d["k"] == "UP":
                d["n"] = "Unidas Podemos" if eleccion.startswith("2019") else ("Unidos Podemos" if eleccion == "2016-06" else "Podemos")
            d["pct"] = round(100 * d["votos"] / total_v, 2)
            d["pct_es"] = round(100 * d["es"] / total_e, 2)
            d["coste"] = round(d["votos"] / d["es"]) if d["es"] else None
        indiv.sort(key=lambda d: -d["votos"])

        gallagher = (0.5 * sum((100 * v / total_v - 100 * e / total_e) ** 2
                               for v, e in zip(nat["v"], nat["es"]))) ** 0.5
        salida[eleccion] = {
            "etiqueta": ETIQUETAS[eleccion],
            "escanos_prov": {p["id"]: p["s"] for p in j["prov"]},
            "grupos": lista, "evolucion": evolucion, "partidos": indiv, "gallagher": round(gallagher, 2),
        }
    return salida


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

    # 5. Sesión 4
    json.dump(efectos(ORIGEN), open(os.path.join(DESTINO, "efectos.json"), "w", encoding="utf-8"), ensure_ascii=False)

    # 6. Mapa
    shutil.copy(os.path.join(ORIGEN, "fuentes", "mapa_provincias.json"), os.path.join(DESTINO, "mapa_provincias.json"))


if __name__ == "__main__":
    main()
