#!/usr/bin/env python3
"""
Problema das N-Rainhas - Algoritmo Genetico

Uso:
    python rainha_genetico.py                  -> 8x8 padrao
    python rainha_genetico.py --n 10           -> 10x10
    python rainha_genetico.py --n 12 --pop 200 -> 12x12 com populacao maior
    python rainha_genetico.py --max-sol 20     -> limita a 20 solucoes no PDF
"""

import random
import argparse
import sys
import time
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.colors import HexColor

# ----------------------------------------------
#  CORES DO TABULEIRO
# ----------------------------------------------
COR_CASA_CLARA  = HexColor("#F0D9B5")
COR_CASA_ESCURA = HexColor("#B58863")
COR_BORDA       = HexColor("#8B6914")
COR_FUNDO_PAG   = HexColor("#1A1A2E")
COR_TITULO      = HexColor("#FFD700")
COR_SUBTITULO   = HexColor("#A0A0C0")
COR_RODAPE      = HexColor("#60608A")
COR_COORD       = HexColor("#E8D5A3")
COR_RAINHA_CORP = HexColor("#1A1A2E")
COR_RAINHA_COR  = HexColor("#FFD700")


# ----------------------------------------------
#  ALGORITMO GENETICO
# ----------------------------------------------

def calcular_aptidao(cromossomo, n):
    conflitos = 0
    for i in range(n):
        for j in range(i + 1, n):
            if cromossomo[i] == cromossomo[j] or abs(cromossomo[i] - cromossomo[j]) == j - i:
                conflitos += 1
    return conflitos


def criar_populacao(tamanho, n):
    populacao = []
    for _ in range(tamanho):
        crom = list(range(n))
        random.shuffle(crom)
        populacao.append(crom)
    return populacao


def cruzar_pais(pai1, pai2, n):
    ponto = random.randint(1, n - 2)
    filho1 = pai1[:ponto] + [g for g in pai2 if g not in pai1[:ponto]]
    filho2 = pai2[:ponto] + [g for g in pai1 if g not in pai2[:ponto]]
    return filho1, filho2


def mutar(cromossomo, taxa, n):
    if random.random() < taxa:
        i, j = random.sample(range(n), 2)
        cromossomo[i], cromossomo[j] = cromossomo[j], cromossomo[i]
    return cromossomo


def selecao_torneio(populacao, aptidoes, k=3):
    candidatos = random.sample(list(zip(populacao, aptidoes)), min(k, len(populacao)))
    return min(candidatos, key=lambda x: x[1])[0]


def barra_progresso(atual, total, encontradas, largura=40):
    pct = atual / total
    preenchido = int(largura * pct)
    barra = "#" * preenchido + "-" * (largura - preenchido)
    print(f"\r  [{barra}] {atual}/{total}  solucoes: {encontradas}", end="", flush=True)


def encontrar_solucoes(n, tamanho_pop, geracoes, taxa_mutacao, max_solucoes, verbose=True):
    solucoes_unicas = set()
    inicio = time.time()
    max_iter = min(40320, 10 ** n)

    if verbose:
        print(f"\n{'='*55}")
        print(f"  Buscando solucoes para {n}-Rainhas...")
        print(f"  Pop: {tamanho_pop} | Geracoes: {geracoes} | Mutacao: {taxa_mutacao}")
        print(f"{'='*55}\n")

    for it in range(max_iter):
        if max_solucoes and len(solucoes_unicas) >= max_solucoes:
            break

        if verbose and it % 50 == 0:
            barra_progresso(it, max_iter, len(solucoes_unicas))

        populacao = criar_populacao(tamanho_pop, n)

        for _ in range(geracoes):
            aptidoes = [calcular_aptidao(c, n) for c in populacao]
            melhor_aptidao = min(aptidoes)

            if melhor_aptidao == 0:
                melhor = populacao[aptidoes.index(0)]
                chave = tuple(melhor)
                if chave not in solucoes_unicas:
                    solucoes_unicas.add(chave)
                break

            pares = sorted(zip(populacao, aptidoes), key=lambda x: x[1])
            nova_pop = [pares[0][0][:], pares[1][0][:]]

            while len(nova_pop) < tamanho_pop:
                p1 = selecao_torneio(populacao, aptidoes)
                p2 = selecao_torneio(populacao, aptidoes)
                f1, f2 = cruzar_pais(p1[:], p2[:], n)
                nova_pop.append(mutar(f1, taxa_mutacao, n))
                if len(nova_pop) < tamanho_pop:
                    nova_pop.append(mutar(f2, taxa_mutacao, n))

            populacao = nova_pop

    duracao = time.time() - inicio
    if verbose:
        barra_progresso(max_iter, max_iter, len(solucoes_unicas))
        print(f"\n\n  {len(solucoes_unicas)} solucoes unicas encontradas em {duracao:.1f}s\n")

    return [list(s) for s in solucoes_unicas]


# ----------------------------------------------
#  DESENHO DA RAINHA (apenas reportlab)
# ----------------------------------------------

def desenhar_rainha(c, x, y, s):
    cx = x + s / 2

    base_w = s * 0.65
    top_w  = s * 0.40
    base_y = y + s * 0.18
    top_y  = y + s * 0.52
    coroa_base_y = top_y
    coroa_top_y  = y + s * 0.82

    # base inferior
    c.setFillColor(COR_RAINHA_CORP)
    c.setStrokeColor(COR_RAINHA_COR)
    c.setLineWidth(0.5)
    base_h = s * 0.12
    c.roundRect(cx - base_w / 2, base_y - base_h, base_w, base_h, s * 0.03, fill=1, stroke=0)

    # corpo (trapezio)
    p = c.beginPath()
    p.moveTo(cx - base_w / 2, base_y)
    p.lineTo(cx + base_w / 2, base_y)
    p.lineTo(cx + top_w / 2,  top_y)
    p.lineTo(cx - top_w / 2,  top_y)
    p.close()
    c.drawPath(p, fill=1, stroke=1)

    # coroa (poligono com dentes)
    nx_off = [-top_w / 2, -top_w / 4, 0, top_w / 4, top_w / 2]
    alturas = [
        coroa_top_y,
        top_y + (coroa_top_y - top_y) * 0.4,
        coroa_top_y,
        top_y + (coroa_top_y - top_y) * 0.4,
        coroa_top_y,
    ]

    c.setFillColor(COR_RAINHA_COR)
    c.setStrokeColor(COR_RAINHA_CORP)
    c.setLineWidth(0.5)

    pontos = [(cx - top_w / 2, coroa_base_y)]
    for i in range(5):
        pontos.append((cx + nx_off[i], alturas[i]))
    pontos.append((cx + top_w / 2, coroa_base_y))

    p = c.beginPath()
    p.moveTo(*pontos[0])
    for pt in pontos[1:]:
        p.lineTo(*pt)
    p.close()
    c.drawPath(p, fill=1, stroke=1)

    # bolinhas nos picos altos
    c.setFillColor(COR_RAINHA_CORP)
    r = s * 0.045
    for i in range(5):
        if alturas[i] == coroa_top_y:
            c.circle(cx + nx_off[i], alturas[i], r, fill=1, stroke=0)


# ----------------------------------------------
#  GERACAO DO PDF
# ----------------------------------------------

def gerar_pdf(solucoes, n, nome_arquivo="rainhas.pdf"):
    tam_cel = min(inch * 0.75, 5 * inch / n)
    tam_tab = tam_cel * n
    margem  = inch * 0.6

    if n > 9:
        pagesize = landscape(letter)
    else:
        pagesize = letter

    pw, ph = pagesize
    c = rl_canvas.Canvas(nome_arquivo, pagesize=pagesize)

    letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    for idx, solucao in enumerate(solucoes):
        # fundo
        c.setFillColor(COR_FUNDO_PAG)
        c.rect(0, 0, pw, ph, fill=1, stroke=0)

        # titulo
        c.setFillColor(COR_TITULO)
        c.setFont("Helvetica-Bold", 18 if n <= 10 else 14)
        c.drawCentredString(pw / 2, ph - margem * 0.6, f"Problema das {n}-Rainhas")

        c.setFillColor(COR_SUBTITULO)
        c.setFont("Helvetica", 10)
        c.drawCentredString(pw / 2, ph - margem * 0.85,
                            f"Solucao {idx + 1} de {len(solucoes)}  |  Algoritmo Genetico")

        tab_x = (pw - tam_tab) / 2
        tab_y = (ph - tam_tab) / 2 - margem * 0.3

        # sombra
        c.setFillColor(HexColor("#000000"))
        c.setFillAlpha(0.35)
        c.rect(tab_x + 6, tab_y - 6, tam_tab, tam_tab, fill=1, stroke=0)
        c.setFillAlpha(1.0)

        # borda de madeira
        c.setFillColor(COR_BORDA)
        c.rect(tab_x - 10, tab_y - 10, tam_tab + 20, tam_tab + 20, fill=1, stroke=0)

        # celulas
        for row in range(n):
            for col in range(n):
                cx = tab_x + col * tam_cel
                cy = tab_y + (n - 1 - row) * tam_cel

                cor = COR_CASA_CLARA if (row + col) % 2 == 0 else COR_CASA_ESCURA
                c.setFillColor(cor)
                c.setStrokeColor(HexColor("#00000022"))
                c.setLineWidth(0.3)
                c.rect(cx, cy, tam_cel, tam_cel, fill=1, stroke=1)

                if solucao[row] == col:
                    desenhar_rainha(c, cx, cy, tam_cel)

        # coordenadas
        c.setFillColor(COR_COORD)
        font_size = max(6, int(tam_cel * 0.22))
        c.setFont("Helvetica-Bold", font_size)
        for i in range(n):
            col_cx = tab_x + i * tam_cel + tam_cel / 2
            c.drawCentredString(col_cx, tab_y - 9, letras[i])
            row_cy = tab_y + (n - 1 - i) * tam_cel + tam_cel / 2 - 3
            c.drawRightString(tab_x - 4, row_cy, str(i + 1))

        # rodape com vetor solucao
        c.setFillColor(COR_RODAPE)
        c.setFont("Courier", 9)
        vetor = "Posicoes: [" + ", ".join(str(v + 1) for v in solucao) + "]"
        c.drawCentredString(pw / 2, margem * 0.3, vetor)

        if idx < len(solucoes) - 1:
            c.showPage()

    c.save()
    print(f"  PDF salvo: {nome_arquivo}  ({len(solucoes)} paginas)")


# ----------------------------------------------
#  ENTRADA VIA TERMINAL
# ----------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Problema das N-Rainhas via Algoritmo Genetico",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--n",       type=int,   default=8,             help="Tamanho do tabuleiro NxN (padrao: 8)")
    parser.add_argument("--pop",     type=int,   default=100,           help="Tamanho da populacao (padrao: 100)")
    parser.add_argument("--ger",     type=int,   default=500,           help="Maximo de geracoes por tentativa (padrao: 500)")
    parser.add_argument("--mut",     type=float, default=0.15,          help="Taxa de mutacao 0-1 (padrao: 0.15)")
    parser.add_argument("--max-sol", type=int,   default=0,             help="Max. solucoes no PDF (0 = todas)")
    parser.add_argument("--saida",   type=str,   default="rainhas.pdf", help="Nome do arquivo PDF de saida")
    args = parser.parse_args()

    if args.n < 4:
        print("N minimo e 4.")
        sys.exit(1)
    if args.n > 20:
        print("N > 20 pode demorar muito. Considere --max-sol 10.")

    solucoes = encontrar_solucoes(
        n            = args.n,
        tamanho_pop  = args.pop,
        geracoes     = args.ger,
        taxa_mutacao = args.mut,
        max_solucoes = args.max_sol,
    )

    if not solucoes:
        print("Nenhuma solucao encontrada. Tente aumentar --pop ou --ger.")
        sys.exit(1)

    limite = args.max_sol if args.max_sol else len(solucoes)
    gerar_pdf(solucoes[:limite], args.n, args.saida)


if __name__ == "__main__":
    main()