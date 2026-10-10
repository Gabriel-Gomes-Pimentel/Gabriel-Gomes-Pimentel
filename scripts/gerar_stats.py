#!/usr/bin/env python3
"""Gera assets/stats-light.svg e assets/stats-dark.svg com metricas reais do perfil, sem depender de servicos de terceiros.

Servicos gratuitos de card (github-readme-stats, profile-summary-cards) caem em
rate limit e mostram "ERROR!!!" no README. Aqui o SVG e commitado no proprio
repositorio e servido pelo raw.githubusercontent, entao nunca depende de um
terceiro estar de pe.

Uso: GITHUB_TOKEN=... python3 scripts/gerar_stats.py
"""
import json
import os
import urllib.request

USUARIO = "Gabriel-Gomes-Pimentel"
SAIDA = "assets/stats-%s.svg"

CONSULTA = """
{
  user(login: "%s") {
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar { totalContributions }
    }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes {
        isArchived
        languages(first: 20) { nodes { name } }
      }
    }
  }
}
""" % USUARIO


def buscar():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("defina GITHUB_TOKEN")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": CONSULTA}).encode(),
        headers={
            "Authorization": "bearer " + token,
            "Content-Type": "application/json",
            "User-Agent": USUARIO,
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        corpo = json.load(r)
    if "errors" in corpo:
        raise SystemExit("erro da API: %s" % corpo["errors"])
    return corpo["data"]["user"]


def montar(dados):
    contrib = dados["contributionsCollection"]
    repos = dados["repositories"]
    ativos = [r for r in repos["nodes"] if not r["isArchived"]]
    linguagens = {n["name"] for r in ativos for n in r["languages"]["nodes"]}
    return [
        ("Commits", str(contrib["totalCommitContributions"]), "últimos 12 meses"),
        ("Contribuições", str(contrib["contributionCalendar"]["totalContributions"]), "últimos 12 meses"),
        ("Repositórios", str(len(ativos)), "públicos e ativos"),
        ("Linguagens", str(len(linguagens)), "em uso nos projetos"),
    ]


def escapar(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


TEMAS = {
    "light": {"fundo": "#ffffff", "borda": "#d0d7de", "valor": "#0f172a", "rotulo": "#2563eb", "nota": "#57606a", "divisor": "#eaeef2"},
    "dark": {"fundo": "#0d1117", "borda": "#30363d", "valor": "#f0f6fc", "rotulo": "#58a6ff", "nota": "#9198a1", "divisor": "#21262d"},
}
FONTE = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"


def gerar_svg(metricas, tema):
    c = TEMAS[tema]
    largura, altura = 900, 132
    col = largura / len(metricas)
    blocos = []
    for i, (rotulo, valor, nota) in enumerate(metricas):
        cx = col * i + col / 2
        blocos.append(
            f'''  <text x="{cx:.1f}" y="62" text-anchor="middle" font-family="{FONTE}" font-size="32" font-weight="700" fill="{c['valor']}">{escapar(valor)}</text>
  <text x="{cx:.1f}" y="88" text-anchor="middle" font-family="{FONTE}" font-size="13" font-weight="600" fill="{c['rotulo']}">{escapar(rotulo)}</text>
  <text x="{cx:.1f}" y="106" text-anchor="middle" font-family="{FONTE}" font-size="11" fill="{c['nota']}">{escapar(nota)}</text>'''
        )
        if i:
            x = col * i
            blocos.append(f'  <line x1="{x:.1f}" y1="34" x2="{x:.1f}" y2="104" stroke="{c['divisor']}" />')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{altura}" viewBox="0 0 {largura} {altura}" role="img" aria-label="Estatísticas do GitHub de {USUARIO}">
  <rect x="0.5" y="0.5" width="{largura - 1}" height="{altura - 1}" rx="12" fill="{c['fundo']}" stroke="{c['borda']}" />
{chr(10).join(blocos)}
</svg>
'''


if __name__ == "__main__":
    metricas = montar(buscar())
    for tema in TEMAS:
        saida = SAIDA % tema
        svg = gerar_svg(metricas, tema)
        with open(saida, "w", encoding="utf-8") as f:
            f.write(svg)
        print("gerado %s (%d bytes)" % (saida, len(svg)))
