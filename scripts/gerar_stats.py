#!/usr/bin/env python3
"""Gera stats.svg com metricas reais do perfil, sem depender de servicos de terceiros.

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
SAIDA = "stats.svg"

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


def gerar_svg(metricas):
    largura, altura = 840, 200
    col = largura / len(metricas)
    blocos = []
    for i, (rotulo, valor, nota) in enumerate(metricas):
        cx = col * i + col / 2
        blocos.append(
            f'''  <g>
    <text x="{cx:.1f}" y="112" class="valor" text-anchor="middle">{escapar(valor)}</text>
    <text x="{cx:.1f}" y="140" class="rotulo" text-anchor="middle">{escapar(rotulo)}</text>
    <text x="{cx:.1f}" y="160" class="nota" text-anchor="middle">{escapar(nota)}</text>
  </g>'''
        )
        if i:
            x = col * i
            blocos.append(f'  <line x1="{x:.1f}" y1="80" x2="{x:.1f}" y2="165" class="divisor" />')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{altura}" viewBox="0 0 {largura} {altura}" role="img" aria-label="Estatísticas do GitHub de {USUARIO}">
  <defs>
    <linearGradient id="borda" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#8b5cf6" />
      <stop offset="50%" stop-color="#4d5bce" />
      <stop offset="100%" stop-color="#38bdf8" />
    </linearGradient>
    <linearGradient id="titulo" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#c4b5fd" />
      <stop offset="100%" stop-color="#7dd3fc" />
    </linearGradient>
  </defs>
  <style>
    .fundo {{ fill: #0d1117; }}
    .moldura {{ fill: none; stroke: url(#borda); stroke-width: 1.5; }}
    .titulo {{ font: 600 19px 'Segoe UI', Ubuntu, Sans-Serif; fill: url(#titulo); }}
    .valor {{ font: 700 40px 'Segoe UI', Ubuntu, Sans-Serif; fill: #e6edf3; }}
    .rotulo {{ font: 600 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: #8b5cf6; }}
    .nota {{ font: 400 11px 'Segoe UI', Ubuntu, Sans-Serif; fill: #7d8590; }}
    .divisor {{ stroke: #21262d; stroke-width: 1; }}
  </style>
  <rect class="fundo" x="0.75" y="0.75" width="{largura - 1.5}" height="{altura - 1.5}" rx="12" />
  <rect class="moldura" x="0.75" y="0.75" width="{largura - 1.5}" height="{altura - 1.5}" rx="12" />
  <text x="28" y="48" class="titulo">GitHub em números</text>
  <line x1="28" y1="64" x2="{largura - 28}" y2="64" class="divisor" />
{chr(10).join(blocos)}
</svg>
'''


if __name__ == "__main__":
    svg = gerar_svg(montar(buscar()))
    with open(SAIDA, "w", encoding="utf-8") as f:
        f.write(svg)
    print("gerado %s (%d bytes)" % (SAIDA, len(svg)))
