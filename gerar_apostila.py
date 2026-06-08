"""
Gerador de Apostila TUEG — Terreiro de Umbanda Estrela Guiada
=============================================================
Uso:
    python gerar_apostila.py

Dependências:
    pip install reportlab pillow

Fontes necessárias:
    - GFS Didot Regular  → baixada automaticamente de github.com/google/fonts
    - Liberation Serif   → /usr/share/fonts/truetype/liberation/ (padrão Ubuntu/Claude)

Ilustrações (JPG, em /mnt/user-data/uploads/ ou mesmo diretório):
    Baianos.jpg, Boiadeiros.jpg, Caboclos.jpg, Caboclos_de_Ogum.jpg,
    Caboclos_de_Xango_.jpg, Ciganos.jpg, Esquerda.jpg, Malandros.jpg,
    Marinheiros.jpg

Logo TUEG:
    Fonte: /mnt/user-data/uploads/29314d_4c3da2987f45490f9c389045313c4fa9_mv2.png
    Processado para: /home/claude/tueg_logo_transparent.png
"""

import os, io, csv, html as html_mod, urllib.request, urllib.parse
from PIL import Image as PILImage
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate,
                                 Paragraph, Spacer, KeepTogether,
                                 HRFlowable, NextPageTemplate, PageBreak)
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader

# ──────────────────────────────────────────────
# CONFIGURAÇÃO — edite aqui antes de rodar
# ──────────────────────────────────────────────
GIRA = 'Caboclos de Ogum'   # nome exato da aba no Google Sheets
PRESENT = {                  # médiuns presentes na gira
    "Claudia",
    "Eric Oliveira",
    "Lu",
    "Pai Erick",
    "Pai Marcos",
}
OUTPUT_DIR = '/mnt/user-data/outputs'   # onde salvar o PDF gerado
ILL_DIR    = '/mnt/user-data/uploads'  # onde estão os JPGs das ilustrações
LOGO_SRC   = '/mnt/user-data/uploads/29314d_4c3da2987f45490f9c389045313c4fa9_mv2.png'
LOGO_PATH  = '/home/claude/tueg_logo_transparent.png'

# ──────────────────────────────────────────────
# MAPA DE ILUSTRAÇÕES POR GIRA
# ──────────────────────────────────────────────
ILL_MAP = {
    'Caboclos de Ogum':   os.path.join(ILL_DIR, 'Caboclos_de_Ogum.jpg'),
    'Caboclos de Oxóssi': os.path.join(ILL_DIR, 'Caboclos.jpg'),
    'Caboclos de Xangô':  os.path.join(ILL_DIR, 'Caboclos_de_Xango_.jpg'),
    'Baianos':            os.path.join(ILL_DIR, 'Baianos.jpg'),
    'Boiadeiros':         os.path.join(ILL_DIR, 'Boiadeiros.jpg'),
    'Ciganos':            os.path.join(ILL_DIR, 'Ciganos.jpg'),
    'Esquerda':           os.path.join(ILL_DIR, 'Esquerda.jpg'),
    'Malandros':          os.path.join(ILL_DIR, 'Malandros.jpg'),
    'Marinheiros':        os.path.join(ILL_DIR, 'Marinheiros.jpg'),
}

# ──────────────────────────────────────────────
# FONTES
# ──────────────────────────────────────────────
FONT_DIR = '/home/claude/fonts'
DIDOT_PATH = os.path.join(FONT_DIR, 'GFSDidot-Regular.ttf')
SERIF_PATH = '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'
SERIFI_PATH= '/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf'

def ensure_fonts():
    os.makedirs(FONT_DIR, exist_ok=True)
    if not os.path.exists(DIDOT_PATH):
        print("Baixando GFS Didot...")
        url = ("https://github.com/google/fonts/raw/main/ofl/gfsdidot/"
               "GFSDidot-Regular.ttf")
        urllib.request.urlretrieve(url, DIDOT_PATH)
    pdfmetrics.registerFont(TTFont('Didot',  DIDOT_PATH))
    pdfmetrics.registerFont(TTFont('Serif',  SERIF_PATH))
    pdfmetrics.registerFont(TTFont('SerifI', SERIFI_PATH))

# ──────────────────────────────────────────────
# LOGO — processa transparência
# ──────────────────────────────────────────────
def ensure_logo():
    if os.path.exists(LOGO_PATH):
        return
    img = PILImage.open(LOGO_SRC).convert('RGBA')
    data = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = data[x, y]
            if r > 230 and g > 230 and b > 230:
                data[x, y] = (255, 255, 255, 0)
    img.save(LOGO_PATH)

# ──────────────────────────────────────────────
# CORES E MEDIDAS
# ──────────────────────────────────────────────
BG       = HexColor('#ffffff')
BC       = HexColor('#7a6a60')
DARK     = HexColor('#1c1c1c')
MUTED    = HexColor('#555555')
GOLD     = HexColor('#8a7050')
TOQUE_C  = HexColor('#9a8a7a')
DIV_C    = HexColor('#c5b5a8')

PW, PH   = A4
MH = MV  = 1.8 * cm
GAP      = 0.6 * cm
CW       = (PW - 2*MH - GAP) / 2
CH       = PH - 2*MV
TITLE_H  = 1.8 * cm
GAP_V    = 0.15 * cm
CH_SEC   = CH - TITLE_H - GAP_V

# ──────────────────────────────────────────────
# DADOS — GitHub
# ──────────────────────────────────────────────
BASE_URL = "https://raw.githubusercontent.com/lucasvallimdacosta/tueg-pontos/main/"

def fetch_csv(aba):
    url = BASE_URL + urllib.parse.quote(aba + ".csv")
    raw = urllib.request.urlopen(url, timeout=15).read().decode()
    return list(csv.DictReader(io.StringIO(raw)))

# ──────────────────────────────────────────────
# ESTILOS
# ──────────────────────────────────────────────
def make_styles():
    S = lambda n, **k: ParagraphStyle(n, **k)
    return {
        'lbl':   S('lbl',  fontName='Didot',  fontSize=11, leading=16,
                   alignment=TA_CENTER, textColor=MUTED, spaceAfter=13),
        'cvt':   S('cvt',  fontName='Didot',  fontSize=38, leading=48,
                   alignment=TA_CENTER, textColor=DARK, spaceAfter=0),
        'sec':   S('sec',  fontName='Didot',  fontSize=13, leading=16,
                   alignment=TA_CENTER, textColor=GOLD,
                   spaceBefore=4, spaceAfter=4),
        'sti':   S('sti',  fontName='Didot',  fontSize=15, leading=19,
                   textColor=DARK, spaceBefore=0, spaceAfter=4),
        'med':   S('med',  fontName='SerifI', fontSize=11, leading=14,
                   textColor=MUTED, spaceAfter=3),
        'toque': S('toque',fontName='Didot',  fontSize=11, leading=14,
                   textColor=TOQUE_C, spaceAfter=7),
        'lyr':   S('lyr',  fontName='Serif',  fontSize=15, leading=19,
                   textColor=DARK),
    }

# ──────────────────────────────────────────────
# CALLBACKS DE PÁGINA
# ──────────────────────────────────────────────
def draw_border(c, pw, ph):
    c.setFillColor(BG); c.rect(0, 0, pw, ph, fill=1, stroke=0)
    c.setStrokeColor(BC); c.setLineWidth(0.8)
    c.rect(1.1*cm, 1.1*cm, pw-2.2*cm, ph-2.2*cm, fill=0, stroke=1)

def make_on_cover(ill_path, ill_w, ill_h):
    ill_dsp_h = 8.0 * cm
    ill_dsp_w = ill_dsp_h * (ill_w / ill_h)
    if ill_dsp_w > 10*cm:
        ill_dsp_w = 10*cm; ill_dsp_h = ill_dsp_w * (ill_h / ill_w)
    ill_top = PH - 2.0*cm
    ill_bot = ill_top - ill_dsp_h

    def on_cover(canvas, doc):
        draw_border(canvas, PW, PH)
        canvas.drawImage(ill_path, (PW-ill_dsp_w)/2, ill_bot,
                         width=ill_dsp_w, height=ill_dsp_h)
        logo_sz = 2.8*cm
        canvas.drawImage(LOGO_PATH, (PW-logo_sz)/2, 2.3*cm,
                         width=logo_sz, height=logo_sz,
                         preserveAspectRatio=True, mask='auto')
        canvas.setFont('SerifI', 7.5); canvas.setFillColor(MUTED)
        canvas.drawCentredString(PW/2, 1.8*cm,
                                 'Terreiro de Umbanda Estrela Guiada')
    return on_cover, ill_bot

def on_content(canvas, doc):
    draw_border(canvas, PW, PH)
    canvas.setStrokeColor(DIV_C); canvas.setLineWidth(0.35)
    cx = MH + CW + GAP/2
    canvas.line(cx, MV+.2*cm, cx, PH-MV-.2*cm)
    canvas.setFont('Serif', 10); canvas.setFillColor(MUTED)
    canvas.drawCentredString(PW/2, .55*cm, str(doc.page))

def on_section(canvas, doc):
    draw_border(canvas, PW, PH)
    sep_y = PH - MV - TITLE_H - GAP_V/2
    canvas.setStrokeColor(DIV_C); canvas.setLineWidth(0.4)
    canvas.line(MH, sep_y, PW-MH, sep_y)
    canvas.setStrokeColor(DIV_C); canvas.setLineWidth(0.35)
    cx = MH + CW + GAP/2
    canvas.line(cx, MV+.2*cm, cx, sep_y-0.1*cm)
    canvas.setFont('Serif', 10); canvas.setFillColor(MUTED)
    canvas.drawCentredString(PW/2, .55*cm, str(doc.page))

# ──────────────────────────────────────────────
# HELPERS DE CONTEÚDO
# ──────────────────────────────────────────────
def esc(t): return html_mod.escape(str(t))

def cover_title(t):
    return '<br/>'.join(esc(w) for w in str(t).upper().split())

def get_title(row):
    t = (row.get('Título do Ponto') or '').strip()
    if t: return t.split('\n')[0].strip()
    return ((row.get('Letra do Ponto') or '').split('\n')[0] or '—').strip()

def filter_row(row):
    mc = (row.get('Médium') or '').strip()
    if not mc: return True, None, None
    listed = [m.strip() for m in mc.split(',')]
    here = [m for m in listed if m in PRESENT]
    if not here: return False, None, None
    e = (row.get('Entidade') or '').strip() or None
    return True, ', '.join(here), e

def build_lyrics(lyr, STY):
    items = []
    for line in lyr.split('\n'):
        s = line.strip()
        if s: items.append(Paragraph(esc(s), STY['lyr']))
        else:  items.append(Spacer(1, 12))
    return items

def build_ponto(row, STY, show_med=True):
    ok, ms, ent = filter_row(row)
    if not ok: return []
    items = [Spacer(1, 10)]
    items.append(Paragraph(esc(get_title(row).upper()), STY['sti']))
    if show_med and ms:
        line = esc(ms)
        if ent: line += f' \xb7 {esc(ent)}'
        items.append(Paragraph(line, STY['med']))
    toque = (row.get('Toque') or '').strip()
    if toque:
        t = f'<font name="SerifI">\u266a\u00a0</font> {esc(toque)}'
        items.append(Paragraph(t, STY['toque']))
    lyr = (row.get('Letra do Ponto') or '').strip()
    if lyr: items.extend(build_lyrics(lyr, STY))
    items.append(HRFlowable(width='100%', thickness=0.3, color=DIV_C,
                             spaceBefore=14, spaceAfter=4))
    return [KeepTogether(items)]

# ──────────────────────────────────────────────
# GERAÇÃO DO PDF
# ──────────────────────────────────────────────
def gerar(gira, present):
    ensure_fonts()
    ensure_logo()
    STY = make_styles()

    ill_path = ILL_MAP[gira]
    ir = ImageReader(ill_path); iw, ih = ir.getSize()
    on_cover, ill_bot = make_on_cover(ill_path, iw, ih)

    logo_area = 5.0*cm
    cov_frame_h = ill_bot - 0.6*cm - logo_area
    n_words = len(gira.split())
    content_h = (16+13) + 6 + (n_words*48+19)
    top_spacer = max(0.5*cm, (cov_frame_h - content_h)/2 - 2.0*cm)

    fname = gira.replace(' ', '_')
    out = os.path.join(OUTPUT_DIR, f'Apostila_Gira_{fname}.pdf')
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    doc = BaseDocTemplate(out, pagesize=A4,
                          leftMargin=MH, rightMargin=MH,
                          topMargin=MV,  bottomMargin=MV)

    fr_cov   = Frame(MH, logo_area, PW-2*MH, cov_frame_h, id='cov')
    fr_L     = Frame(MH, MV, CW, CH, id='L')
    fr_R     = Frame(MH+CW+GAP, MV, CW, CH, id='R')
    fr_sec_t = Frame(MH, PH-MV-TITLE_H, PW-2*MH, TITLE_H, id='sec_title')
    fr_sec_L = Frame(MH, MV, CW, CH_SEC, id='sec_L')
    fr_sec_R = Frame(MH+CW+GAP, MV, CW, CH_SEC, id='sec_R')

    doc.addPageTemplates([
        PageTemplate(id='Cover',   frames=[fr_cov],                      onPage=on_cover),
        PageTemplate(id='Content', frames=[fr_L, fr_R],                  onPage=on_content),
        PageTemplate(id='Section', frames=[fr_sec_t, fr_sec_L, fr_sec_R],onPage=on_section),
    ])

    print(f"Buscando dados do GitHub para '{gira}'...")
    ab_rows   = fetch_csv("Abertura")
    gira_rows = fetch_csv(gira)
    defumacao = [r for r in ab_rows if (r.get('Categoria') or '').strip().lower() == 'defumação']
    abertura  = [r for r in ab_rows if (r.get('Categoria') or '').strip().lower() != 'defumação']

    story = []
    # — Capa
    story.append(NextPageTemplate('Cover'))
    story.append(Spacer(1, top_spacer))
    story.append(Paragraph('G I R A', STY['lbl']))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(cover_title(gira), STY['cvt']))
    # — Defumação
    story.append(NextPageTemplate('Section')); story.append(PageBreak())
    story.append(Paragraph('DEFUMAÇÃO', STY['sec']))
    story.append(NextPageTemplate('Content'))
    for row in defumacao: story.extend(build_ponto(row, STY, show_med=False))
    # — Abertura da gira
    story.append(NextPageTemplate('Section')); story.append(PageBreak())
    story.append(Paragraph('ABERTURA DA GIRA', STY['sec']))
    story.append(NextPageTemplate('Content'))
    for row in abertura: story.extend(build_ponto(row, STY, show_med=False))
    # — Seção da gira (ordem exata do Sheets)
    story.append(NextPageTemplate('Section')); story.append(PageBreak())
    story.append(Paragraph(gira.upper(), STY['sec']))
    story.append(NextPageTemplate('Content'))
    for row in gira_rows: story.extend(build_ponto(row, STY, show_med=True))

    doc.build(story)
    inc = sum(1 for r in gira_rows if filter_row(r)[0])
    print(f"✓ PDF gerado: {out}  ({inc} pontos da gira incluídos)")
    return out

if __name__ == '__main__':
    gerar(GIRA, PRESENT)
