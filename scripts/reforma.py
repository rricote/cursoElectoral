"""Sesión 5: simulación de la propuesta de reforma electoral.

Circunscripción = comunidad autónoma. Ceuta y Melilla: 1 escaño cada una.
Cada comunidad: mínimo 6 escaños; los 246 restantes, por población (cociente y
restos mayores, como hace la LOREG con las provincias). Dentro de cada comunidad:
D'Hondt con barrera del 3 % de los votos válidos de la comunidad.

Población: cifras oficiales del padrón usadas en cada convocatoria
(1-1-2014 para 2015, 1-1-2015 para 2016, 1-1-2018 para 2019 y 1-1-2022 para 2023).
Fuentes: INE, recogidas en el Anuario de Estadística del MAPA (2014, 2015)
y en el CREM de la Región de Murcia (2018, 2022).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from preparar_datos import cargar, dhondt, UP_POR_ELECCION  # noqa: E402

ORDEN = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17"]
#        And   Ara   Ast   Bal   Can   Cant  CLM   CyL   Cat   Ext   Gal   Mad   Nav   PV    Mur   Rio   CV
POB = {
    "2015-12": [8402305, 1325385, 1061756, 1103442, 2104815, 588656, 2078611, 2494790, 7518903, 1099632, 2748695, 6454440, 640790, 2188985, 1466818, 319002, 5004844],
    "2016-06": [8399043, 1317847, 1051229, 1104479, 2100306, 585179, 2059191, 2472052, 7508106, 1092997, 2732347, 6436996, 640476, 2189257, 1467288, 317053, 4980689],
    "2019-04": [8384408, 1308728, 1028244, 1128908, 2127685, 580229, 2026807, 2409164, 7600065, 1072863, 2701743, 6578079, 647554, 2199088, 1478509, 315675, 4963703],
    "2023-07": [8500187, 1326315, 1004686, 1176659, 2177701, 585402, 2053328, 2372640, 7792611, 1054776, 2690464, 6750336, 664117, 2208174, 1531878, 319892, 5097967],
}
POB["2019-11"] = POB["2019-04"]
ELECCIONES = ["2015-12", "2016-06", "2019-04", "2019-11", "2023-07"]
ETIQUETAS = {"2015-12": "2015", "2016-06": "2016", "2019-04": "Abril 2019", "2019-11": "Noviembre 2019", "2023-07": "2023"}
NOMBRE_UP = {"2015-12": "Podemos y confluencias", "2016-06": "Unidos Podemos y confluencias",
             "2019-04": "Unidas Podemos", "2019-11": "Unidas Podemos"}
COLORES = {"PSOE": "#e30613", "PP": "#1d84ce", "CS": "#eb6109", "UP": "#7b3f98", "VOX": "#5aa31f", "SUMAR": "#e6007e"}
NOMBRES = {"CS": "Ciudadanos", "VOX": "Vox", "SUMAR": "Sumar"}


def reparto_escanos(pob, total=350, minimo=6, fijos=2):
    resto = total - fijos - minimo * len(pob)
    cuota = sum(pob) / resto
    base = [int(p / cuota) for p in pob]
    sobran = resto - sum(base)
    orden = sorted(range(len(pob)), key=lambda i: -(pob[i] / cuota - base[i]))
    for i in orden[:sobran]:
        base[i] += 1
    return [minimo + b for b in base]


def gallagher(votos, escanos):
    tv, te = sum(votos), sum(escanos)
    return (0.5 * sum((100 * v / tv - 100 * e / te) ** 2 for v, e in zip(votos, escanos))) ** 0.5


def simular(origen):
    salida = {}
    for el in ELECCIONES:
        j = cargar(os.path.join(origen, "datos", el, "general.json.js"))
        partidos, nat = j["parties"], j["nat"]
        claves = [p["k"] for p in partidos]
        nombres_cc = {c["id"]: c["n"] for c in j["ccaa"]}
        esc_cc = dict(zip(ORDEN, reparto_escanos(POB[el])))
        esc_cc["18"], esc_cc["19"] = 1, 1

        # votos por comunidad (con voto exterior), blancos y escaños actuales
        votos_cc, blancos_cc, actual_cc, provs_cc = {}, {}, {}, {}
        for p in j["prov"]:
            cc = p["cc"]
            v = [a + b for a, b in zip(p["v"], p.get("cera", [0] * len(p["v"])))]
            votos_cc[cc] = [a + b for a, b in zip(votos_cc.get(cc, [0] * len(v)), v)]
            blancos_cc[cc] = blancos_cc.get(cc, 0) + p["bl"] + p.get("cera_bl", 0)
            actual_cc[cc] = actual_cc.get(cc, 0) + p["s"]
            provs_cc.setdefault(cc, []).append(p["id"])

        up = UP_POR_ELECCION[el]
        # escaños actuales por partido en cada comunidad (suma de sus provincias)
        actual_partido_cc = {}
        for p in j["prov"]:
            acc = actual_partido_cc.setdefault(p["cc"], [0] * len(claves))
            actual_partido_cc[p["cc"]] = [a + b for a, b in zip(acc, p["es"])]

        def clave(k):
            return "UP" if k in up else k

        def nombre(i):
            k = claves[i]
            return NOMBRE_UP.get(el) if k in up else NOMBRES.get(k, partidos[i]["n"])

        def color(i):
            return COLORES.get(clave(claves[i]), partidos[i]["c"])

        reforma = [0] * len(claves)
        ccaa = []
        for cc, v in votos_cc.items():
            validos = sum(v) + blancos_cc[cc]
            elig = [x if x >= 0.03 * validos else 0 for x in v]
            r = dhondt(elig, esc_cc[cc])
            reforma = [a + b for a, b in zip(reforma, r)]
            filas = {}
            for i, k in enumerate(claves):
                d = filas.setdefault(clave(k), {"k": clave(k), "n": nombre(i), "c": color(i), "votos": 0, "actual": 0, "reforma": 0})
                d["votos"] += v[i]
                d["actual"] += actual_partido_cc[cc][i]
                d["reforma"] += r[i]
            filas = [d for d in filas.values() if d["actual"] or d["reforma"] or d["votos"] / validos >= 0.03]
            for d in filas:
                d["pct"] = round(100 * d["votos"] / validos, 2)
            filas.sort(key=lambda d: -d["votos"])
            ccaa.append({"id": cc, "n": nombres_cc[cc], "prov": provs_cc[cc],
                         "pob": POB[el][ORDEN.index(cc)] if cc in ORDEN else None,
                         "s_actual": actual_cc[cc], "s_reforma": esc_cc[cc], "partidos": filas})
        assert sum(reforma) == 350, (el, sum(reforma))

        # agregación por partido (UP con sus confluencias)
        tot_v = sum(nat["v"]) + nat.get("bl", 0)
        agg = {}
        for i, k in enumerate(claves):
            kk = "UP" if k in up else k
            d = agg.setdefault(kk, {"k": kk, "n": NOMBRE_UP.get(el) if kk == "UP" else NOMBRES.get(kk, partidos[i]["n"]),
                                    "c": COLORES.get(kk, partidos[i]["c"]), "votos": 0, "actual": 0, "reforma": 0})
            d["votos"] += nat["v"][i]
            d["actual"] += nat["es"][i]
            d["reforma"] += reforma[i]
        filas = [d for d in agg.values() if d["actual"] or d["reforma"]]
        for d in filas:
            d["pct"] = round(100 * d["votos"] / tot_v, 2)
            d["pct_actual"] = round(100 * d["actual"] / 350, 2)
            d["pct_reforma"] = round(100 * d["reforma"] / 350, 2)
        filas.sort(key=lambda d: (-d["actual"], -d["reforma"]))
        salida[el] = {
            "etiqueta": ETIQUETAS[el], "ccaa": sorted(ccaa, key=lambda c: -c["s_reforma"]), "partidos": filas,
            "gallagher_actual": round(gallagher(nat["v"], nat["es"]), 2),
            "gallagher_reforma": round(gallagher(nat["v"], reforma), 2),
            "nep_actual": round(1 / sum((e / 350) ** 2 for e in nat["es"]), 2),
            "nep_reforma": round(1 / sum((e / 350) ** 2 for e in reforma), 2),
        }
    return salida


if __name__ == "__main__":
    origen = sys.argv[1]
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datos", "reforma.json")
    datos = simular(origen)
    json.dump(datos, open(destino, "w", encoding="utf-8"), ensure_ascii=False)
    for el, d in datos.items():
        print(el, "Gallagher", d["gallagher_actual"], "->", d["gallagher_reforma"], "| NEP", d["nep_actual"], "->", d["nep_reforma"])
        print("   ", [(c["n"][:12], c["s_actual"], c["s_reforma"]) for c in d["ccaa"]])
        print("   ", [(p["n"][:14], p["actual"], p["reforma"]) for p in d["partidos"]])
