"""SENTİNEL Yazılım Gereksinimleri Belirtimi (SRS) PDF üreticisi."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    CondPageBreak,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "SENTINEL_SRS_Yazilim_Gereksinimleri_Belirtimi.pdf"
FONT_DIR = Path(r"C:\Windows\Fonts")

NAVY = colors.HexColor("#0B1F3A")
NAVY2 = colors.HexColor("#12355B")
GOLD = colors.HexColor("#B8860B")
TEAL = colors.HexColor("#0E7490")
ROW_ALT = colors.HexColor("#F4F7FB")
LIGHT = colors.HexColor("#E8EEF5")
MUTED = colors.HexColor("#4B5563")


def _register_fonts() -> tuple[str, str, str]:
    regular = FONT_DIR / "arial.ttf"
    bold = FONT_DIR / "arialbd.ttf"
    italic = FONT_DIR / "ariali.ttf"
    if not regular.exists():
        raise FileNotFoundError("Arial bulunamadı; Windows yazı tipleri gerekli.")
    pdfmetrics.registerFont(TTFont("Body", str(regular)))
    pdfmetrics.registerFont(TTFont("Body-Bold", str(bold if bold.exists() else regular)))
    pdfmetrics.registerFont(TTFont("Body-Italic", str(italic if italic.exists() else regular)))
    return "Body", "Body-Bold", "Body-Italic"


def _styles(reg: str, bold: str, italic: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    s: dict[str, ParagraphStyle] = {}
    s["cover_kicker"] = ParagraphStyle(
        "cover_kicker",
        parent=base["Normal"],
        fontName=bold,
        fontSize=9,
        textColor=GOLD,
        alignment=TA_CENTER,
        tracking=1.2,
        spaceAfter=8,
    )
    s["cover_title"] = ParagraphStyle(
        "cover_title",
        parent=base["Normal"],
        fontName=bold,
        fontSize=22,
        leading=28,
        textColor=NAVY,
        alignment=TA_CENTER,
        spaceAfter=10,
    )
    s["cover_sub"] = ParagraphStyle(
        "cover_sub",
        parent=base["Normal"],
        fontName=reg,
        fontSize=12,
        leading=16,
        textColor=NAVY2,
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    s["cover_meta"] = ParagraphStyle(
        "cover_meta",
        parent=base["Normal"],
        fontName=reg,
        fontSize=10,
        leading=14,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceAfter=3,
    )
    s["h1"] = ParagraphStyle(
        "h1",
        parent=base["Heading1"],
        fontName=bold,
        fontSize=14,
        leading=18,
        textColor=NAVY,
        spaceBefore=12,
        spaceAfter=8,
        borderPadding=0,
        keepWithNext=1,
    )
    s["h2"] = ParagraphStyle(
        "h2",
        parent=base["Heading2"],
        fontName=bold,
        fontSize=12,
        leading=16,
        textColor=NAVY2,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=1,
    )
    s["h3"] = ParagraphStyle(
        "h3",
        parent=base["Heading3"],
        fontName=bold,
        fontSize=10.5,
        leading=14,
        textColor=TEAL,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=1,
    )
    s["body"] = ParagraphStyle(
        "body",
        parent=base["Normal"],
        fontName=reg,
        fontSize=9.5,
        leading=13.4,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor("#1F2937"),
        spaceAfter=7,
    )
    s["note"] = ParagraphStyle(
        "note",
        parent=s["body"],
        fontName=italic,
        textColor=MUTED,
        leftIndent=8,
        rightIndent=8,
        spaceBefore=2,
        spaceAfter=8,
    )
    s["caption"] = ParagraphStyle(
        "caption",
        parent=base["Normal"],
        fontName=italic,
        fontSize=8,
        leading=11,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceBefore=2,
        spaceAfter=10,
    )
    s["th"] = ParagraphStyle(
        "th",
        parent=base["Normal"],
        fontName=bold,
        fontSize=8,
        leading=11,
        textColor=colors.white,
        alignment=TA_CENTER,
    )
    s["td"] = ParagraphStyle(
        "td",
        parent=base["Normal"],
        fontName=reg,
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#111827"),
        alignment=TA_LEFT,
    )
    s["tdc"] = ParagraphStyle(
        "tdc",
        parent=s["td"],
        alignment=TA_CENTER,
    )
    s["toc"] = ParagraphStyle(
        "toc",
        parent=base["Normal"],
        fontName=reg,
        fontSize=10,
        leading=15,
        textColor=NAVY,
        leftIndent=6,
        spaceAfter=2,
    )
    s["li"] = ParagraphStyle(
        "li",
        parent=s["body"],
        leftIndent=2,
        spaceAfter=3,
    )
    s["footer"] = ParagraphStyle(
        "footer",
        parent=base["Normal"],
        fontName=reg,
        fontSize=7.5,
        textColor=MUTED,
    )
    return s


def P(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def bullets(items: list[str], style: ParagraphStyle) -> ListFlowable:
    return ListFlowable(
        [ListItem(P(x, style), leftIndent=12, bulletColor=NAVY) for x in items],
        bulletType="bullet",
        start="•",
        leftIndent=16,
        bulletFontName=style.fontName,
        bulletFontSize=9,
        spaceBefore=0,
        spaceAfter=8,
    )


def numbered(items: list[str], style: ParagraphStyle) -> ListFlowable:
    return ListFlowable(
        [ListItem(P(x, style), leftIndent=14) for x in items],
        bulletType="1",
        leftIndent=18,
        bulletFontName=style.fontName,
        bulletFontSize=9,
        spaceBefore=0,
        spaceAfter=8,
    )


def table(headers: list[str], rows: list[list[str]], styles: dict, col_widths: list[float]) -> list:
    th, td, tdc = styles["th"], styles["td"], styles["tdc"]
    data = [[P(h, th) for h in headers]]
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            cells.append(P(str(cell), tdc if i in {0, 1} and len(headers) > 3 else td))
        data.append(cells)
    t = Table(data, colWidths=col_widths, repeatRows=1)
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Body-Bold"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    t.setStyle(TableStyle(cmds))
    t.splitByRow = 1
    t.repeatRows = 1
    return [t, Spacer(1, 3)]


HEADING_NAMES = {"h1", "h2", "h3"}
_MIN_SPACE = {"h1": 52 * mm, "h2": 40 * mm, "h3": 32 * mm}


def _style_name(item) -> str:
    return item.style.name if isinstance(item, Paragraph) else ""


def _is_heading(item) -> bool:
    return _style_name(item) in HEADING_NAMES


def _take_caption_tail(flowables: list, j: int) -> tuple[list, int]:
    taken: list = []
    n = len(flowables)
    while j < n:
        nxt = flowables[j]
        if isinstance(nxt, Spacer):
            taken.append(nxt)
            j += 1
            continue
        if _style_name(nxt) == "caption":
            taken.append(nxt)
            j += 1
        break
    return taken, j


def bind_layout(flowables: list) -> list:
    """Başlığı sonraki paragraf/tablo ile kilitle; sayfa sonunda yalnız başlık bırakma."""
    out: list = []
    i = 0
    n = len(flowables)
    while i < n:
        item = flowables[i]
        if isinstance(item, (PageBreak, CondPageBreak, KeepTogether)):
            out.append(item)
            i += 1
            continue
        if _is_heading(item):
            block = [item]
            j = i + 1
            if j < n and _is_heading(flowables[j]):
                parent = item.style.name
                child = flowables[j].style.name
                deeper = (parent == "h1" and child in {"h2", "h3"}) or (
                    parent == "h2" and child == "h3"
                )
                if deeper:
                    block.append(flowables[j])
                    j += 1
            if j < n and not isinstance(flowables[j], PageBreak) and not _is_heading(
                flowables[j]
            ):
                block.append(flowables[j])
                j += 1
                extra, j = _take_caption_tail(flowables, j)
                block.extend(extra)
            out.append(CondPageBreak(_MIN_SPACE[block[0].style.name]))
            out.append(KeepTogether(block))
            i = j
            continue
        if isinstance(item, Table):
            extra, j = _take_caption_tail(flowables, i + 1)
            if extra:
                out.append(KeepTogether([item, *extra]))
                i = j
            else:
                out.append(item)
                i += 1
            continue
        out.append(item)
        i += 1
    return out


def header_footer(canvas, doc) -> None:
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 12 * mm, w, 12 * mm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, h - 12.6 * mm, w, 1.2, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Body", 8)
    canvas.drawString(18 * mm, h - 7.6 * mm, "SENTİNEL  •  Yazılım Gereksinimleri Belirtimi (SRS)")
    canvas.setFont("Body", 7.5)
    canvas.drawRightString(w - 18 * mm, h - 7.6 * mm, "Sürüm 1.0  •  Kamu / Akademik")
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, w, 12 * mm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, 12 * mm, w, 1.2, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Body", 7.5)
    canvas.drawString(18 * mm, 5.2 * mm, "ISO/IEC/IEEE 29148 uyarınca  •  6 Eylül 2026")
    canvas.drawRightString(w - 18 * mm, 5.2 * mm, f"Sayfa {doc.page}")
    canvas.restoreState()


def cover_page(canvas, doc) -> None:
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, h - 28 * mm, w, 8 * mm, fill=1, stroke=0)
    canvas.rect(0, 22 * mm, w, 3 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Body-Bold", 9)
    canvas.drawCentredString(w / 2, h - 24 * mm, "MİLLÎ TEKNOLOJİ HAMLESİ  •  UZAY VE UYDU VERİ MİMARİSİ")
    canvas.setFont("Body", 8)
    canvas.setFillColor(colors.HexColor("#94A3B8"))
    canvas.drawCentredString(w / 2, 14 * mm, "Belge kodu: SENTINEL-SRS-2026-01   •   Sınıflandırma: Kamu / Akademik")
    canvas.restoreState()


def build() -> None:
    reg, bold, italic = _register_fonts()
    styles = _styles(reg, bold, italic)
    story: list = []

    # --- KAPAK İÇ METİN (koyu zemin üzerine beyaz stiller) ---
    cover_white = ParagraphStyle("cw", parent=styles["cover_title"], textColor=colors.white)
    cover_sub_w = ParagraphStyle("csw", parent=styles["cover_sub"], textColor=colors.HexColor("#E2E8F0"))
    cover_meta_w = ParagraphStyle("cmw", parent=styles["cover_meta"], textColor=colors.HexColor("#CBD5E1"))

    story.append(Spacer(1, 42 * mm))
    story.append(P("YAZILIM GEREKSİNİMLERİ BELİRTİMİ", styles["cover_kicker"]))
    story.append(Spacer(1, 6 * mm))
    story.append(P("SENTİNEL", cover_white))
    story.append(
        P(
            "Astrobiyolojik Sensör Yükü Veri Mimarisi<br/>"
            "Uçtan Yer İstasyonuna Telemetri, Anomali ve Bant Optimizasyonu Yazılımı",
            cover_sub_w,
        )
    )
    story.append(Spacer(1, 14 * mm))
    story.append(P("Software Requirements Specification (SRS)", cover_meta_w))
    story.append(P("ISO/IEC/IEEE 29148:2018 ile uyumlu yapı", cover_meta_w))
    story.append(Spacer(1, 18 * mm))
    story.append(P("Sürüm 1.0  •  6 Eylül 2026", cover_meta_w))
    story.append(P("Durum: Taslak / İnceleme", cover_meta_w))
    story.append(
        P(
            "Özel bölümler: Millî Teknoloji Hamlesi hizalaması • "
            "Türksat uydu seçim gerekçesi • AYAP / derin uzay analogu",
            cover_meta_w,
        )
    )
    story.append(PageBreak())

    # --- BELGE KONTROL ---
    story.append(P("Belge Kontrol Bilgileri", styles["h1"]))
    story.extend(
        table(
            ["Alan", "Değer"],
            [
                ["Belge adı", "SENTİNEL Yazılım Gereksinimleri Belirtimi"],
                ["Belge kodu", "SENTINEL-SRS-2026-01"],
                ["Sürüm", "1.0"],
                ["Tarih", "6 Eylül 2026"],
                ["Dil", "Türkçe (birincil); teknik tanımlayıcılar İngilizce korunur"],
                ["Standart", "ISO/IEC/IEEE 29148:2018 (SRS bilgi öğeleri)"],
                ["Ürün adı", "SENTİNEL — Astrobiyolojik Sensör Yükü Veri Mimarisi"],
                ["Ürün sürümü", "1.0.0 (FastAPI + React 18)"],
                ["Sınıflandırma", "Kamu / Akademik — uçuş yazılımı belirtimi değildir"],
                ["Hedef okuyucu", "Geliştirici, danışman, jüri, TUA/TÜBİTAK/üniversite paydaşları"],
            ],
            styles,
            [45 * mm, 129 * mm],
        )
    )
    story.append(P("Tablo 1. Belge kimliği ve kontrol alanları.", styles["caption"]))

    story.append(P("Revizyon geçmişi", styles["h2"]))
    story.extend(
        table(
            ["Sürüm", "Tarih", "Açıklama", "Yazar"],
            [
                [
                    "1.0",
                    "2026-09-06",
                    "İlk tam SRS: işlevsel/NFR, MTH hizalaması, Türksat seçim analizi",
                    "Proje ekibi",
                ],
            ],
            styles,
            [22 * mm, 28 * mm, 92 * mm, 32 * mm],
        )
    )

    story.append(P("Onay ve dağıtım", styles["h2"]))
    story.append(
        P(
            "Bu belge, SENTİNEL yazılımının ne yapması gerektiğini (ne nasıl kodlandığını değil) "
            "paydaşlar arasında sözleşmeye yakın bir dilde sabitlemek için yazılmıştır. "
            "Uçuş yeterliliği (flight qualification), ITAR/EAR veya milli gizlilik kapsamı "
            "iddia etmez. Dağıtım: proje deposu, jüri dosyası, akademik rapor eki.",
            styles["body"],
        )
    )

    story.append(P("Belgenin özel içeriği", styles["h2"]))
    story.append(
        P(
            "Klasik SRS bölümlerinin yanı sıra bu belgede iki ulusal politika başlığı "
            "ayrıntılı işlenmiştir:",
            styles["body"],
        )
    )
    story.append(
        bullets(
            [
                "<b>Millî Teknoloji Hamlesi yönü:</b> SENTİNEL’in kritik teknolojilerde yerlilik, "
                "veri egemenliği, AYAP/derin uzay yetkinliği ve insan kaynağı ile ilişkisi.",
                "<b>Türksat uydu seçimi:</b> 3A / 4A / 4B / 5A / 5B / 6A karşılaştırması; "
                "hangi uydunun neden birincil, hangisinin kapasite ve kapsama yedeği olacağı; "
                "GEO haberleşme uydusunun Mars DSN’inin yerine geçemeyeceğinin açık ifadesi.",
            ],
            styles["li"],
        )
    )

    toc_items = [
        "1. Giriş",
        "    1.1 Amaç   1.2 Kapsam ve kapsam dışı   1.3 Tanımlar   1.4 Referanslar   1.5 Belge yapısı",
        "2. Genel tanım",
        "    2.1 Ürün perspektifi   2.2 Başlıca işlevler   2.3 Kullanıcı sınıfları",
        "    2.4 İşletim ortamı   2.5 Kısıtlar   2.6 Varsayımlar ve bağımlılıklar",
        "3. Millî Teknoloji Hamlesi yönü  (özel bölüm)",
        "    3.1 Hamlenin uzay ayağı   3.2 SENTİNEL hizalama matrisi   3.3 Yerlilik ve egemenlik",
        "    3.4 AYAP / gezen araç veri zinciri   3.5 Paydaş ve yetkinlik   3.6 Riskler",
        "4. Türksat uydu seçimi  (özel bölüm)",
        "    4.1 Problem ayrımı (derin uzay ≠ GEO)   4.2 Filo envanteri   4.3 Karar matrisi",
        "    4.4 Önerilen mimari (6A + 5B + 5A)   4.5 Bant ve protokol   4.6 Yer segmenti",
        "5. Sistem özellikleri (işlevsel gereksinimler)",
        "6. Dış arayüz gereksinimleri",
        "7. Veri modeli, API ve gerçek zamanlı akış",
        "8. Kalite öznitelikleri (işlevsel olmayan gereksinimler)",
        "9. Güvenlik ve gizlilik",
        "10. Doğrulama, kabul ve izlenebilirlik",
        "11. Ekler",
    ]
    toc_block = [P("İçindekiler", styles["h1"])]
    toc_block.extend(
        P(item.replace("  ", "&nbsp;&nbsp;"), styles["toc"]) for item in toc_items
    )
    story.append(PageBreak())
    story.append(KeepTogether(toc_block))
    story.append(PageBreak())

    # --- 1 GİRİŞ ---
    story.append(P("1. Giriş", styles["h1"]))
    story.append(P("1.1 Amaç", styles["h2"]))
    story.append(
        P(
            "Bu Yazılım Gereksinimleri Belirtimi (SRS), SENTİNEL adlı yazılım sisteminin "
            "paydaşlarca doğrulanabilir gereksinimlerini tanımlar. Belge; geliştirme ekibine "
            "uygulama sözleşmesi, jüriye değerlendirme çerçevesi, ulusal uzay/uydu paydaşlarına "
            "ise prototipin Millî Teknoloji Hamlesi ve Türksat yer segmenti ile nasıl "
            "konumlandığını anlatan referans metindir.",
            styles["body"],
        )
    )
    story.append(
        P(
            "Belge, yazılımın <i>ne</i> yapması gerektiğini belirtir. Algoritma seçiminin "
            "gerekçesi ve mevcut kodun gerçek davranışı (örneğin skor kaynağının LSTM "
            "smoothed error + River olması) izlenebilirlik için gereksinim diline "
            "dökülmüştür; bu bir tasarım belgesi (SDD) değildir.",
            styles["body"],
        )
    )

    story.append(P("1.2 Kapsam ve kapsam dışı", styles["h2"]))
    story.append(
        P(
            "<b>SENTİNEL</b>, NASA SMAP/MSL Anomali Tespiti veri setindeki MSL (Curiosity) "
            "kanallarından gelen normalize telemetriyi dosyadan <b>sıralı replay</b> eden; "
            "uçta (edge) anomali skoru, bilimsel öncelik, sıkıştırma ve uplink kuyruğu ile "
            "işleyen; PostgreSQL ve WebSocket üzerinden yer istasyonu panosunda canlı "
            "gösteren bir web uygulamasıdır. Skor, z-score + River hibritidir; "
            "<font face='Body-Italic'>smoothed_errors/*.npy</font> varsa LSTM hata sinyali "
            "karışıma girer. Çalışma zamanında TensorFlow/Keras veya .h5 yükleme yoktur.",
            styles["body"],
        )
    )
    story.append(P("Kapsam içi", styles["h3"]))
    story.append(
        bullets(
            [
                "12 MSL kanalının sıralı replay’i ve kanal kimliği izlenebilirliği (T-1, M-6, C-1, …).",
                "Uç işlemci: ring buffer, skor, eşik, yenilik (novelty), enerji ve RL ince ayarı.",
                "DSN analogu uplink kuyruğu; orbiter röle (Edge-2); yer/bulut eşik geri bildirimi.",
                "Delta kodlama + zlib (DEFLATE) ile gerçek ikili sıkıştırma metrikleri.",
                "Yer istasyonu panosu (React), REST + OpenAPI, WebSocket canlı akış.",
                "İsteğe bağlı NASA Open API vekili (APOD, Curiosity fotoğrafları) — replay değildir.",
                "Ulusal konumlandırma: MTH hizalaması ve Türksat yer-segmenti önerisi (bu belgede).",
            ],
            styles["li"],
        )
    )
    story.append(P("Kapsam dışı (açık sınır)", styles["h3"]))
    story.append(
        bullets(
            [
                "Canlı Mars bağlantısı, gerçek DSN anteni, uçuş yazılımı veya radyasyon sertleştirmesi.",
                "Keras/.h5 ile çalışma zamanı çıkarımı; modeller yalnızca veri seti mirasıdır.",
                "Türksat uydusuna gerçek RF uplink/downlink veya yasal frekans tahsisi.",
                "İnsanlı uzay görevi, silah sistemi, patojen sentezi veya çift kullanımlı biyoloji.",
                "GitHub Pages üzerindeki statik vitrin tek başına tam sistemi oluşturmaz "
                "(API + Postgres orada çalışmaz).",
            ],
            styles["li"],
        )
    )
    story.append(
        P(
            "Dürüstlük kaydı: Bu yazılım, hackathon / akademik prototip ölçeğinde "
            "<b>uçtan buluta veri azaltma mimarisini</b> gösterir. En iyi anomali tespit "
            "doğruluğunu iddia etmez. LSTM artifaktı olmadan F1 yaklaşık 0,24–0,26 bandındadır; "
            "Hundman ve arkadaşlarının F0.5 ≈ 0,69 sonucu bu deponun skoru değildir.",
            styles["note"],
        )
    )

    story.append(P("1.3 Tanımlar, kısaltmalar ve terimler", styles["h2"]))
    story.extend(
        table(
            ["Terim", "Anlamı"],
            [
                ["SENTİNEL", "Bu projenin ürün adı; uç + yer istasyonu yazılım yığını."],
                ["Edge / uç", "Rover üzerinde skor, eşik, filtre ve kuyruk kararının alındığı katman."],
                ["Replay", "Canlı sensör değil; .npy dosyasından sıralı okuma üretimi."],
                ["Ground truth", "labeled_anomalies.csv etiketi; karara katılmaz, değerlendirmeye girer."],
                ["DSN analogu", "Derin Uzay Ağı’nın yazılımda kuyruk + pencere ile taklidi."],
                ["Orbiter / Edge-2", "Yörünge rölesi: 30 sn pencere, skor &lt; 40 paket düşürme."],
                ["MTH", "Millî Teknoloji Hamlesi."],
                ["TUA", "Türkiye Uzay Ajansı."],
                ["AYAP", "Ay Araştırma Programı (AYAP-1 yörünge/temas, AYAP-2 yumuşak iniş + gezen araç)."],
                ["GEO", "Yer sabit yörünge (~35 786 km); Türksat filosunun bulunduğu sınıf."],
                ["HTS", "High Throughput Satellite; spot hüzme + frekans yeniden kullanımı."],
                ["Ku / Ka / Q-V", "Haberleşme uydu bantları; Ka ve Q-V yüksek veri hızına elverişlidir."],
                ["CCSDS", "Uzay veri sistemleri danışma komitesi; uzay linki standart ailesi."],
                ["NFR", "Non-functional requirement; kalite / kısıt gereksinimi."],
            ],
            styles,
            [38 * mm, 136 * mm],
        )
    )
    story.append(P("Tablo 2. Terimler sözlüğü.", styles["caption"]))

    story.append(P("1.4 Referans belgeler", styles["h2"]))
    story.append(
        numbered(
            [
                "ISO/IEC/IEEE 29148:2018 — Systems and software engineering — Life cycle processes — Requirements engineering.",
                "Hundman, K. vd. (2018). Detecting Spacecraft Anomalies Using LSTMs and Nonparametric Dynamic Thresholding. KDD 2018; telemanom veri seti.",
                "NASA SMAP/MSL Anomaly Detection Dataset (Kaggle / HuggingFace appleparan/telemanom).",
                "Türkiye Uzay Ajansı, Millî Uzay Programı Strateji Belgesi (2022–2030) ve 9 Şubat 2021 program tanıtımı.",
                "TÜRKSAT A.Ş. Uydu Filosu teknik sayfaları: Türksat 3A, 4A, 4B, 5A, 5B, 6A (erişim: 2026).",
                "TÜRKSAT 6A resmi teknik özet: fırlatma 08.07.2024; 42,0° Doğu; üretici TÜBİTAK UZAY, TUSAŞ, ASELSAN, CTECH.",
                "Sanayi ve Teknoloji Bakanlığı / TUA kamu açıklamaları: İMECE, TÜRKSAT 6A ile haberleşme uydusu üretebilen ülkeler kümesi, AYAP.",
                "NASA Open APIs (api.nasa.gov) — APOD ve Mars Rover Photos; bu projede isteğe bağlı vekil.",
                "SENTİNEL depo README ve OpenAPI (/docs) — uygulama davranışı için birincil yazılım kaynağı.",
            ],
            styles["li"],
        )
    )

    story.append(P("1.5 Belge yapısı", styles["h2"]))
    story.append(
        P(
            "Bölüm 2 ürünü bağlama oturtur. Bölüm 3 ve 4 paydaşın talep ettiği ulusal "
            "politika ve uydu seçimini, yazılım kapsamının dışına taşmadan ama kararı "
            "gerekçelendirerek işler. Bölüm 5–10 doğrulanabilir gereksinimlerdir. "
            "Her işlevsel gereksinim SENT-F-xxx, her NFR SENT-Q-xxx, her güvenlik "
            "maddesi SENT-S-xxx kimliğini taşır.",
            styles["body"],
        )
    )

    # --- 2 GENEL TANIM ---
    story.append(P("2. Genel tanım", styles["h1"]))
    story.append(P("2.1 Ürün perspektifi", styles["h2"]))
    story.append(
        P(
            "SENTİNEL bağımsız bir yazılım ürünüdür; uçuş bilgisayarına gömülü değildir. "
            "Dört mantıksal katmanı tek süreçte (FastAPI lifespan) simüle eder:",
            styles["body"],
        )
    )
    story.extend(
        table(
            ["Katman", "Rol", "Yazılımdaki karşılık"],
            [
                [
                    "1. Sensör",
                    "12 MSL kanalı, ilk sütun telemetri",
                    "simulator.py, backend/data/test/*.npy",
                ],
                [
                    "2. Rover / Edge-1",
                    "Skor, eşik, filtre, kuyruk, sıkıştırma, enerji, RL",
                    "edge_processor, river_learner, energy_controller, rl_agent, compressor",
                ],
                [
                    "3. Orbiter / Edge-2",
                    "30 sn pencere, skor &lt; 40 DROP, pass_id",
                    "orbiter_processor, orbiter_queue, orbiter_relay_log",
                ],
                [
                    "4. Yer / bulut + pano",
                    "20 röle sonra model_update; REST + WS + React",
                    "earth_cloud, PostgreSQL, routers/*, frontend",
                ],
            ],
            styles,
            [32 * mm, 62 * mm, 80 * mm],
        )
    )
    story.append(P("Tablo 3. Sistem bağlamı — dört katman.", styles["caption"]))
    story.append(
        P(
            "Dış sistemler: PostgreSQL 16 (kalıcı durum), isteğe bağlı Groq (rover düşünce metni), "
            "isteğe bağlı NASA Open API, geliştirmede Vite vekili (/api, /ws → :8000). "
            "Türksat RF zinciri bugün dış sistem değildir; Bölüm 4 bunu <b>hedef yer-segmenti "
            "mimarisi</b> olarak tanımlar.",
            styles["body"],
        )
    )

    story.append(P("2.2 Başlıca ürün işlevleri", styles["h2"]))
    story.append(
        numbered(
            [
                "Veri toplama: 12 kanaldan tur başına birer okuma; aralık varsayılan 10 sn (1–120 sn).",
                "Uç tampon: kanal başına son 500 okuma (ring buffer) ile z-score referansı.",
                "Anomali skoru: smoothed error varsa 0,50 LSTM + 0,50 River; yoksa 0,40 z + 0,60 River.",
                "Karar: tek dinamik eşik (40–85); is_anomaly ve uplink_eligible aynı koşuldur.",
                "Bilimsel sınıflama ve öncelik: organik (10) … sıcaklık ekstremi (4).",
                "Bant azaltma: eşik altı DROP; iletileceklerde delta + zlib.",
                "Uplink drain: tur başına sınırlı paket (varsayılan 12).",
                "Orbiter drain ve yer/bulut federated eşik önerisi.",
                "Canlı pano, değerlendirme uçları (nokta + Hundman dizi metrikleri), sağlık.",
            ],
            styles["li"],
        )
    )

    story.append(P("2.3 Kullanıcı sınıfları ve özellikleri", styles["h2"]))
    story.extend(
        table(
            ["Sınıf", "Hedef", "Yetki"],
            [
                [
                    "Görev operatörü",
                    "Canlı telemetri, kuyruk, bant, enerji",
                    "Okuma; WS akışı",
                ],
                [
                    "Bilim analisti",
                    "Anomali onay, kanal bağlamı, değerlendirme",
                    "PATCH acknowledge (jeton)",
                ],
                [
                    "Yer istasyonu mühendisi",
                    "Uplink / orbiter / model_update",
                    "Okuma + izleme",
                ],
                [
                    "Eğitmen / jüri",
                    "VERİ_AKIŞI pedagojisi, veri seti paneli",
                    "Okuma",
                ],
                [
                    "Geliştirici",
                    "Simülasyon tetikleme, ayar, migrasyon",
                    "Yazma uçları + .env",
                ],
            ],
            styles,
            [42 * mm, 72 * mm, 60 * mm],
        )
    )
    story.append(P("Tablo 4. Kullanıcı sınıfları.", styles["caption"]))

    story.append(P("2.4 İşletim ortamı", styles["h2"]))
    story.append(
        bullets(
            [
                "İstemci: modern tarayıcı; Vite geliştirme sunucusu varsayılan http://localhost:5173.",
                "Sunucu: Python 3.11+, FastAPI, Uvicorn, SQLAlchemy async + asyncpg.",
                "Veri tabanı: PostgreSQL 16; şema yalnızca Alembic (metadata.create_all yok).",
                "Yerel bağımlılık: docker compose ile 127.0.0.1:5432; kök .env kimlik bilgileri.",
                "Veri seti: repoda yoktur; scripts/fetch_dataset.py ile indirilir. Yoksa /health degraded.",
                "İsteğe bağlı: GROQ_API_KEY, NASA_API_KEY, SENTINEL_API_TOKEN.",
            ],
            styles["li"],
        )
    )

    story.append(P("2.5 Tasarım ve uygulama kısıtları", styles["h2"]))
    story.append(
        bullets(
            [
                "Arayüz ve OpenAPI etiketleri Türkçe birincildir; JSON alan adları İngilizce kalır.",
                "Harita ve anlatı Gale Krateri / Bradbury iniş ile hizalıdır; Jezero / PIXL / SHERLOC varsayılan anlatıda yoktur.",
                "Edge kararı etikete bakmaz (ground-truth leakage yasağı).",
                "Yazma uçları jeton yoksa 503 ile kapalıdır.",
                "VERİ_AKIŞI sayfası pedagojik sahnelemedir; uçuş yazılımının kopyası değildir.",
            ],
            styles["li"],
        )
    )

    story.append(P("2.6 Varsayımlar ve bağımlılıklar", styles["h2"]))
    story.append(
        bullets(
            [
                "Varsayım: Kullanıcı yerel Postgres ve Python sanal ortamını kurabilir.",
                "Varsayım: HuggingFace telemanom aynası erişilebilirdir (eski S3 adresi 403).",
                "Bağımlılık: Groq kotası aşılırsa düşünce metni fallback’e düşer; telemetri durmaz.",
                "Bağımlılık: NASA DEMO_KEY saatlik ~30 istektir; arşiv sayfası buna duyarlıdır.",
                "Varsayım (Bölüm 4): Türksat kapasitesi ileride yer-segmenti dağıtımı için kiralanabilir; bugünkü yazılım RF modem içermez.",
            ],
            styles["li"],
        )
    )

    # --- 3 MTH ---
    story.append(P("3. Millî Teknoloji Hamlesi yönü", styles["h1"]))
    story.append(
        P(
            "Bu bölüm, ürünün yalnızca bir NASA veri seti demosu olmadığını; Türkiye’nin "
            "uzayda yetkinlik biriktirme siyasetiyle nasıl konuştuğunu kayda geçirir. "
            "Hamle bir slogan değil, kritik teknolojilerde dışa bağımlılığı azaltma, "
            "insan kaynağı ve yerli sanayi ekosistemi üretme programıdır. SENTİNEL "
            "donanım üretmez; <b>görev veri mimarisi ve uç karar yazılımı</b> katmanında "
            "öğrenme nesnesi ve prototip sunar.",
            styles["body"],
        )
    )

    story.append(P("3.1 Hamlenin uzay ayağı — bağlayıcı çerçeve", styles["h2"]))
    story.append(
        P(
            "2018’de Türkiye Uzay Ajansı’nın kuruluşu ve 9 Şubat 2021’de ilan edilen "
            "Millî Uzay Programı, 2022–2030 strateji belgesi ile resmi yol haritasına "
            "dönüşmüştür. Kamu belgelerinde yinelenen ilkeler: uzaya bağımsız erişim, "
            "kritik teknolojilerde millilik, bilime katkı, barışçıl kullanım, yumuşak güç, "
            "ticari fayda ve toplumsal farkındalıktır. Programın somut işaret taşları "
            "şunlardır:",
            styles["body"],
        )
    )
    story.append(
        bullets(
            [
                "<b>TÜRKSAT 6A (2024):</b> İlk yerli haberleşme uydusu; TÜBİTAK UZAY, TUSAŞ, "
                "ASELSAN, CTECH üretimi. Türkiye’yi kendi haberleşme uydusunu üretebilen "
                "sınırlı ülke kümesine taşır. Bu, MTH’nin uzaydaki en görünür sanayi çıktısıdır.",
                "<b>İMECE ve GÖKTÜRK soyu:</b> Yer gözlemde metre-altı çözüm ve süreklilik; "
                "veri işleme ve yer istasyonu kültürü.",
                "<b>AYAP:</b> İlk derin uzay / Ay teması (AYAP-1) ve ileride yumuşak iniş + "
                "gezen araç (AYAP-2). Gezen araç, SENTİNEL’in modellediği sensör → uç → "
                "röle → yer zincirinin ulusal karşılığıdır.",
                "<b>Türk astronot ve bilim misyonu:</b> Toplumsal farkındalık ve STEM; "
                "SENTİNEL’in Türkçe panosu ve pedagojik VERİ_AKIŞI ekranı aynı hedefe hizmet eder.",
                "<b>Uzaya bağımsız erişim ve konumlama:</b> Uzay limanı ve bölgesel konumlama "
                "hedefleri; bu yazılımın doğrudan kapsamı değildir, bağımlılık olarak anılır.",
            ],
            styles["li"],
        )
    )

    story.append(P("3.2 SENTİNEL – MTH hizalama matrisi", styles["h2"]))
    story.append(
        P(
            "Aşağıdaki matris, hamle ilkesini yazılım kabiliyetine bağlar. "
            "“Katkı düzeyi” iddia değil, prototip ölçeğinde niyet ve kanıttır.",
            styles["body"],
        )
    )
    story.extend(
        table(
            ["MTH / MUP ilkesi", "SENTİNEL kanıtı", "Katkı", "Boşluk"],
            [
                [
                    "Kritik teknolojilerde millilik",
                    "Skor, eşik, sıkıştırma, kuyruk ve değerlendirme kodu yerli tasarım; yabancı kapalı kutu uç karar motoru yok",
                    "Yüksek (yazılım)",
                    "Uç donanım, rad-hard CPU, RF yok",
                ],
                [
                    "Veri egemenliği",
                    "Postgres yerelde; jetonlu yazma; etiket sızması yasağı; sırlar .env’de",
                    "Yüksek",
                    "Üretim kimlik yönetimi (SSO/KVKK süreci) yok",
                ],
                [
                    "Derin uzay / AYAP yetkinliği",
                    "Gezen araç veri azaltma, öncelik ve röle senaryosu yazılımda koşar",
                    "Orta (analog)",
                    "Gerçek gecikme, Doppler, CCSDS çerçeve yok",
                ],
                [
                    "Haberleşme bağımsızlığı",
                    "Bölüm 4: yer-segmenti için 6A birincil önerisi",
                    "Orta (hedef mimari)",
                    "Bugün RF entegrasyonu yok",
                ],
                [
                    "Bilime katkı",
                    "NASA MSL replay; Hundman dizi metrikleri; açık yöntem",
                    "Orta",
                    "Yeni bilimsel keşif üretmez; yöntem laboratuvarıdır",
                ],
                [
                    "İnsan kaynağı / STEM",
                    "Türkçe arayüz, 8 adımlı boru hattı sahnelemesi, açık depo",
                    "Yüksek",
                    "Resmî müfredat entegrasyonu yok",
                ],
                [
                    "Yumuşak güç ve anlatı",
                    "Gale/Curiosity doğruluğu; NASA arşivi ile kamu iletişimi",
                    "Orta",
                    "Uluslararası yayın/DOI planı bu SRS’in parçası değil",
                ],
                [
                    "Ticari fayda",
                    "Bant tasarrufu ve kuyruk, ileride yerli görevlerde lisanslanabilir desen",
                    "Düşük–orta",
                    "Ürünleştirme, SLA, satış modeli yok",
                ],
            ],
            styles,
            [38 * mm, 58 * mm, 32 * mm, 46 * mm],
        )
    )
    story.append(P("Tablo 5. Millî Teknoloji Hamlesi hizalama matrisi.", styles["caption"]))

    story.append(P("3.3 Yerlilik, egemenlik ve “neden yazılım da millidir”", styles["h2"]))
    story.append(
        P(
            "Kamusal tartışmada millilik çoğu zaman uydu gövdesi, itki veya elektro-optik "
            "ile ölçülür. Görev başarısızlığı ise sıklıkla <b>veri yolunda</b> olur: yanlış "
            "öncelik, dolu kuyruk, gereksiz bit, yerde okunamayan paket, sızan etiket, "
            "kapanan yabancı API. SENTİNEL’in MTH tezi şudur: Türkiye AYAP-2 sınıfı bir "
            "gezen araç indirdiğinde, bilimsel değeri olan örneği Dünya’ya hangi kurala "
            "göre göndereceğini uçta kararlaştıran yazılım da kritik teknolojidir. "
            "Bu yazılımın yurt dışında kara kutu olarak kalması, 6A ile kazanılan "
            "haberleşme egemenliğini veri katmanında yeniden dışa bağımlı kılar.",
            styles["body"],
        )
    )
    story.append(
        P(
            "Bu nedenle gereksinimler, kararın izlenebilir olmasını zorunlu kılar: "
            "kanal kimliği saklanır; edge kararı ile veri seti etiketi ayrı tutulur; "
            "skor kaynağı /health içinde açıklanır; sıkıştırma gerçek codec’dir "
            "(yalnızca yüzde göstergesi değil). Bunlar “açık bilim + milli kontrol” "
            "dengesinin yazılım karşılığıdır.",
            styles["body"],
        )
    )

    story.append(P("3.4 AYAP ve gezen araç veri zincirine katkı", styles["h2"]))
    story.append(
        P(
            "AYAP-1, Türkiye’nin ilk Ay ve derin uzay temasını; AYAP-2 ise yumuşak iniş "
            "ve yüzeyde gezen aracı hedefler. SENTİNEL bir Ay aracı değildir ve bunu "
            "iddia etmez. Sunduğu şey, AYAP-2 görev tanımının yazılım omurgasına "
            "aktarılabilir bir <b>referans senaryo</b>dur:",
            styles["body"],
        )
    )
    story.extend(
        table(
            ["AYAP-2 kavramı", "SENTİNEL’deki analog", "Aktarım notu"],
            [
                [
                    "Yüzey bilimsel yükü",
                    "TEMP, CH4, SPEC, MOIST, UV, PRESS, O2, CO2 kanalları",
                    "Ay’da enstrüman seti değişir; öncelik tablosu yeniden kalibre edilir",
                ],
                [
                    "Kısıtlı enerji",
                    "EnergyController: batarya → eşik ve zlib seviyesi",
                    "Güneş + gece ısıl çevrimi Ay’da daha serttir",
                ],
                [
                    "Kısıtlı bant / görünürlük penceresi",
                    "Uplink kuyruk + drain; orbiter 30 sn pencere",
                    "Gerçekte yörünge geçiş ephemeris’i gerekir",
                ],
                [
                    "Bilimsel önceliklendirme",
                    "organik 10 … sıcaklık 4",
                    "Ay’da su/buz, volatil, manyetik anomali öncelikleri yazılır",
                ],
                [
                    "Yer bilim ekibi",
                    "Anomali onay, değerlendirme API, Türkçe pano",
                    "TUA / üniversite SOC süreci eklenir",
                ],
            ],
            styles,
            [48 * mm, 62 * mm, 64 * mm],
        )
    )
    story.append(P("Tablo 6. AYAP-2 kavramlarının yazılımdaki analogları.", styles["caption"]))

    story.append(P("3.5 Ulusal paydaş haritası", styles["h2"]))
    story.extend(
        table(
            ["Paydaş", "İlgi", "Bu prototipten beklenen"],
            [
                ["TUA", "Program hizası, AYAP veri kavramı", "Açık, dürüst kapsam; uçuş iddiası yok"],
                ["TÜBİTAK UZAY", "Yerli uydu / görev yazılımı kültürü", "Veri azaltma ve skor şeffaflığı"],
                ["TÜRKSAT A.Ş.", "Yer-segmenti kapasitesi (6A/5B/5A)", "Bölüm 4 karar gerekçesi"],
                ["ASELSAN / CTECH", "Haberleşme yükü ve modem", "Protokol boşluğunun kabulü"],
                ["Üniversiteler", "Eğitim, tez, yarışma", "Türkçe pano + tekrarlanabilir kurulum"],
                ["Sanayi ve Teknoloji Bak.", "MTH anlatısı", "Yazılımın da kritik teknoloji sayılması"],
            ],
            styles,
            [40 * mm, 58 * mm, 76 * mm],
        )
    )
    story.append(P("Tablo 7. Paydaş haritası.", styles["caption"]))

    story.append(P("3.6 MTH açısından riskler ve mitigasyon", styles["h2"]))
    story.extend(
        table(
            ["Risk", "Etki", "Mitigasyon"],
            [
                [
                    "Prototipin “milli uydu / milli rover” olarak abartılması",
                    "Güven kaybı, jüri ve kamu itirazı",
                    "Bu SRS ve /health dürüstlüğü; kapsam dışı listesi",
                ],
                [
                    "Yabancı API’ye (Groq, NASA) operasyonel bağımlılık",
                    "Düşünce/arşiv kesilir",
                    "Fallback; telemetri çekirdeği çevrimdışı çalışır",
                ],
                [
                    "Veri setinin ABD menşeli olması",
                    "“Millilik” eleştirisi",
                    "Yöntem yerli; veri kamuya açık bilimsel kıyas standardıdır. İleride yerli kanal kataloğu takılır",
                ],
                [
                    "Türksat’ın Mars linki sanılması",
                    "Teknik hatalı mimari",
                    "Bölüm 4.1 zorunlu okuma; GEO ≠ DSN",
                ],
            ],
            styles,
            [52 * mm, 48 * mm, 74 * mm],
        )
    )
    story.append(P("Tablo 8. Politika ve anlatı riskleri.", styles["caption"]))

    story.append(
        P(
            "<b>SENT-P-001 (politika):</b> Ürün belgeleri, arayüz ve jüri sunumu; canlı Mars "
            "bağlantısı, Türksat üzerinden gezegenler arası comms veya uçuş yeterliliği "
            "iddia etmeyecektir. İhlal, belgenin geçersiz sayılması nedenidir.",
            styles["body"],
        )
    )
    story.append(
        P(
            "<b>SENT-P-002 (politika):</b> Türkçe birincil dil ve Gale/Curiosity anlatı "
            "tutarlılığı korunacaktır (Jezero/Perseverance enstrüman adları varsayılan "
            "metinde kullanılmaz).",
            styles["body"],
        )
    )

    # --- 4 TÜRKSAT ---
    story.append(P("4. Türksat uydu seçimi ve yer-segmenti haberleşme mimarisi", styles["h1"]))
    story.append(
        P(
            "Paydaş sorusu: “Bu proje için Türksat uydularından hangisi kullanılmalı?” "
            "Yanıt, tek bir uydu adı değil; <b>görev halkasına göre ayrılmış bir filo "
            "kararıdır.</b> Kararın ilk şartı fiziksel gerçekliktir.",
            styles["body"],
        )
    )

    story.append(P("4.1 Problem ayrımı: derin uzay linki ≠ yer sabit haberleşme", styles["h2"]))
    story.append(
        P(
            "Türksat 3A–6A ailesi <b>yer sabit (GEO)</b> haberleşme uydularıdır. "
            "Yaklaşık 35 786 km yükseklikte, Dünya’ya göre sabit dururlar; TV, VSAT, "
            "internet ve kurumsal omurga taşırlar. Mars veya Ay yüzeyinden gelen "
            "zayıf X/Ka derin uzay işaretini toplayacak 34–70 m sınıfı anten, maser "
            "alıcı, Doppler/ışık zamanı kompensasyonu ve CCSDS Proximity-1 / TC/TM "
            "yığını bu filonun görevi değildir. Bu nedenle:",
            styles["body"],
        )
    )
    story.append(
        bullets(
            [
                "<b>Kullanılmamalı (birincil derin uzay uplink):</b> Hiçbir Türksat GEO uydusu "
                "Curiosity/MSL veya AYAP gezen aracı için DSN yerine geçemez.",
                "<b>Kullanılmalı (ulusal yer segmenti):</b> Bilimsel ürün Dünya’ya (veya "
                "simülasyonda yer istasyonu sunucusuna) indikten sonra, Türkiye içi ve "
                "bölgesel dağıtım, yedek SOC, üniversite ağı ve kamu yayıncılığı için "
                "Türksat filosu doğrudur.",
                "<b>Kullanılmalı (bant kısıtı analogu):</b> Geliştirme ve tatbikatta Ka/Ku "
                "kiralanmış bir taşıyıcı, SENTİNEL’in eşik + zlib kararlarını gerçek "
                "gecikme/jitter ile stres testine sokabilir.",
            ],
            styles["li"],
        )
    )
    story.append(
        P(
            "Yanlış mimari: Rover → doğrudan Türksat 6A transponder. "
            "Doğru hedef mimari: Rover → (röle yörünge aracı) → derin uzay yer istasyonu "
            "(uluslararası DSN işbirliği veya ileride milli derin uzay anteni) → "
            "<b>ulusal dağıtım omurgası olarak Türksat</b> → TUA / üniversite / kamu.",
            styles["note"],
        )
    )

    story.append(P("4.2 Güncel filo envanteri (kamu kaynaklı özet, 2026)", styles["h2"]))
    story.append(
        P(
            "Sayısal değerler TÜRKSAT resmi filo sayfaları ve kamu duyurularına dayanır. "
            "Kiralanacak transponder için TÜRKSAT A.Ş. güncel kapasite tablosu esas alınır.",
            styles["body"],
        )
    )
    story.extend(
        table(
            ["Uydu", "Yörünge", "Öne çıkan özellik", "Bu proje için rol adayı"],
            [
                [
                    "3A (2008)",
                    "42°D",
                    "Ku; yaşlanan kapasite; TR uplink avantajı",
                    "Önerilmez (ömür / kapasite)",
                ],
                [
                    "4A (2014)",
                    "42°D",
                    "Ku/Ka; geniş DTH/VSAT; 5B yedeği",
                    "İkincil yayın / geçiş dönemi",
                ],
                [
                    "4B (2015)",
                    "50°D",
                    "3400 MHz; Ku + Ka spot; internet",
                    "Ka deneyi için mümkün, birincil değil",
                ],
                [
                    "5A (2021)",
                    "31°D",
                    "30+ yıl manevra; 1728 MHz yeni Ku; TR–Avrupa–Ortadoğu–Afrika",
                    "Kapsama ve 31°D hakları; kamu/işbirliği",
                ],
                [
                    "5B (2021)",
                    "42°D",
                    "HTS Ka; &gt;55 Gbps; 15 kW; 3A/4A yedeği",
                    "Yüksek hacimli bilim veri omurgası",
                ],
                [
                    "6A (2024)",
                    "42°D",
                    "İlk milli haberleşme uydusu; Ku, Ku-BSS, Ka, Q/V; 16 yıl; TR/Batı/Doğu",
                    "<b>Birincil ulusal seçim</b>",
                ],
            ],
            styles,
            [28 * mm, 24 * mm, 62 * mm, 60 * mm],
        )
    )
    story.append(P("Tablo 9. Türksat filosu ve SENTİNEL yer-segmenti rolleri.", styles["caption"]))
    story.append(
        P(
            "TÜRKSAT 6A resmi teknik özet: fırlatma 8 Temmuz 2024; 42,0° Doğu; üretici "
            "TÜBİTAK UZAY, TUSAŞ, ASELSAN, CTECH; manevra ömrü 16 yıl; kapsama Türkiye, "
            "Batı ve Doğu (kamu anlatısında Güneydoğu Asya’ya uzanan doğu hüzmesi). "
            "TÜRKSAT 5B: Ka’da 55 Gbps üzeri; filo içi en yüksek veri verimi. "
            "TÜRKSAT 5A: 31° Doğu’da 30 yılı aşan yörünge/frekans güvencesi.",
            styles["body"],
        )
    )

    story.append(P("4.3 Karar matrisi ve puanlama", styles["h2"]))
    story.append(
        P(
            "Kriterler 1–10 ölçeğinde, SENTİNEL’in <b>yer-segmenti bilim verisi dağıtımı</b> "
            "kullanım senaryosuna göredir. Derin uzay uygunluğu tüm GEO uydularda 0’dır "
            "ve birincil seçimi değiştiremez; tabloda ayrıca gösterilir.",
            styles["body"],
        )
    )
    story.extend(
        table(
            ["Kriter (ağırlık)", "3A", "4A", "4B", "5A", "5B", "6A"],
            [
                ["Millilik / MTH (0,25)", "2", "3", "3", "4", "5", "10"],
                ["Ka / yüksek veri (0,20)", "2", "5", "6", "3", "10", "7"],
                ["TR bilim ağı kapsaması (0,15)", "6", "7", "6", "8", "8", "9"],
                ["Uluslararası işbirliği kapsaması (0,10)", "5", "7", "7", "9", "8", "9"],
                ["Görev ömrü / hak (0,10)", "3", "5", "5", "10", "9", "8"],
                ["42°D ile yedeklilik (0,10)", "8", "8", "2", "1", "9", "9"],
                ["Q/V ve gelecek bant (0,05)", "1", "2", "2", "2", "4", "9"],
                ["Operasyonel olgunluk (0,05)", "8", "8", "8", "8", "8", "7"],
                ["Ağırlıklı yer-seg. puanı", "3,9", "5,5", "4,9", "5,7", "7,7", "8,7"],
                ["Derin uzay DSN puanı", "0", "0", "0", "0", "0", "0"],
            ],
            styles,
            [52 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm, 22 * mm],
        )
    )
    story.append(
        P(
            "Tablo 10. Yer-segmenti seçim matrisi. Ağırlıklı puan ≈ Σ(ağırlık × skor); "
            "yuvarlanmış. 6A birincil, 5B kapasite lideri, 5A kapsama/31°D lideridir.",
            styles["caption"],
        )
    )

    story.append(P("4.4 Önerilen karar — hangisi kullanılmalı?", styles["h2"]))
    story.append(
        P(
            "<b>Karar cümlesi:</b> SENTİNEL’in ulusal yer-segmenti haberleşmesinde "
            "<b>birincil uydu TÜRKSAT 6A</b> olmalıdır. Yüksek hacimli ham/işlenmiş "
            "bilim arşivi ve çok noktalı üniversite dağıtımı için <b>TÜRKSAT 5B</b> "
            "Ka-HTS kapasite tamamlayıcısıdır. Afrika–Avrupa kamu ve işbirliği "
            "yayını ile 31° Doğu haklarının yaşatılması için <b>TÜRKSAT 5A</b> "
            "kapsama tamamlayıcısıdır. 3A önerilmez; 4A/4B yalnızca geçiş veya "
            "tatbikat yedeğidir.",
            styles["body"],
        )
    )

    story.append(P("4.4.1 Neden birincil TÜRKSAT 6A?", styles["h3"]))
    story.append(
        numbered(
            [
                "Millî Teknoloji Hamlesi ile birebir örtüşür: yerli haberleşme uydusu "
                "üretebilme eşiği; üretici dörtlüsü ulusal ekosistemin kendisidir.",
                "Aynı 42° Doğu yuvasında 5B ile birlikte çalışır; anten yönelimi ve "
                "yer istasyonu (Gölbaşı ve mevcut 42°D terminaleri) paylaşılır.",
                "Ku + Ka + Q/V, hem operasyonel telemetri özeti (düşük bit hızlı Ku) "
                "hem ileri yüksek hızlı besleme (Ka/Q-V) için tek platformda yol açar.",
                "Doğu kapsaması, ileride Asya’daki bilim ortaklarına arşiv itmesi için "
                "5A/5B’nin Afrika-odaklı anlatısını tamamlar.",
                "Seri üretim öğrenmesi (6A’dan sonraki milli haberleşme uyduları) "
                "görev yazılımının “milli omurga” varsayımını kalıcı kılar.",
            ],
            styles["li"],
        )
    )

    story.append(P("4.4.2 Neden tek başına 5B değil?", styles["h3"]))
    story.append(
        P(
            "5B kapasitede üstündür ve SENTİNEL’in sıkıştırılmış olsa bile çoğalan "
            "zaman serisi + görüntü arşivi için doğru borudur. Ancak 5B yabancı "
            "platform kökenlidir; MTH anlatısında <b>birincil vitrin</b> olamaz. "
            "Ayrıca 5B’nin HTS spot hüzme modeli, küçük bir TUA SOC + birkaç "
            "üniversite için aşırı ve maliyetli olabilir. Doğru kullanım: 6A "
            "üzerinden kontrol/özet ve yetkilendirme; 5B üzerinden toplu arşiv "
            "ve çoklu indirme.",
            styles["body"],
        )
    )

    story.append(P("4.4.3 Neden 5A devrede kalsın?", styles["h3"]))
    story.append(
        P(
            "5A, 31° Doğu’daki frekans ve yörünge haklarını onlarca yıl kilitler. "
            "Bilim diplomasisi (Afrika üniversiteleri, Akdeniz ortakları) ve kamu "
            "yayını (görev anlatısı, eğitim kanalı) bu hüzmede doğaldır. "
            "SENTİNEL’in NASA_ARŞİV ve pedagojik ekranları, 5A üzerinden "
            "DTH/eğitim multipleksi ile toplum ayağına bağlanabilir.",
            styles["body"],
        )
    )

    story.append(P("4.4.4 Neden 3A / 4A / 4B birincil olamaz?", styles["h3"]))
    story.append(
        bullets(
            [
                "3A (2008): ömür ve spektrum verimi; yeni milli görev omurgası için uygun değil.",
                "4A: hâlâ işe yarar yayın uydusu; 5B zaten yedeğini üstlenir. Yeni mimarinin kalbi olmamalı.",
                "4B: 50° Doğu ayrı yuva — ek yer terminali demektir. Ka tatbikatı için nicel test yatağı olabilir.",
            ],
            styles["li"],
        )
    )

    story.append(P("4.5 Bant planı ve SENTİNEL veri sınıfları", styles["h2"]))
    story.extend(
        table(
            ["Veri sınıfı", "Örnek", "Önerilen uydu / bant", "Gerekçe"],
            [
                [
                    "Operasyon özeti",
                    "stats_update, eşik, enerji, kuyruk boyu",
                    "6A Ku",
                    "Düşük bit, yüksek süreklilik, milli kontrol kanalı",
                ],
                [
                    "Öncelikli anomali",
                    "organic_molecule, methane_spike paketleri",
                    "6A Ku veya 6A Ka (dar taşıyıcı)",
                    "Gecikme ve öncelik; HTS paylaşımına bırakılmaz",
                ],
                [
                    "Toplu bilim arşivi",
                    "sensor_readings zaman serisi, değerlendirme dökümü",
                    "5B Ka-HTS",
                    "Hacim; spot hüzme ile üniversite noktasına indirme",
                ],
                [
                    "Q/V deneyi",
                    "Gelecek nesil yüksek hızlı besleme",
                    "6A Q/V",
                    "Yağmur zayıflaması yüksek; yedek Ku şart",
                ],
                [
                    "Kamu / STEM yayını",
                    "Pano vitrini, APOD, eğitim",
                    "5A Ku (DTH)",
                    "31°D + Afrika/Avrupa ev anteni ekosistemi",
                ],
                [
                    "Derin uzay ham RF",
                    "Rover X-bant / Ka-uplink",
                    "Türksat dışı (DSN / milli derin uzay)",
                    "GEO transponder fiziken uygun değil",
                ],
            ],
            styles,
            [36 * mm, 42 * mm, 42 * mm, 54 * mm],
        )
    )
    story.append(P("Tablo 11. Veri sınıfı — uydu/bant eşlemesi.", styles["caption"]))

    story.append(P("4.6 Protokol yığını (hedef, yazılım boşluğu)", styles["h2"]))
    story.append(
        P(
            "Bugünkü SENTİNEL, yerde HTTP/JSON + WebSocket + zlib taşır. "
            "Türksat üzerinden gerçek dağıtım için hedef yığın önerisi:",
            styles["body"],
        )
    )
    story.append(
        bullets(
            [
                "Uzay linki (kapsam dışı bugün): CCSDS TC/TM veya Proximity-1; CFDP dosya.",
                "Yer omurgası: 6A/5B üzerinde DVB-S2X veya SCPC; mümkünse şifreli VLAN.",
                "Uygulama: mevcut REST/WS’in kurum ağına alınması; değişmez JSON şeması.",
                "Sıkıştırma: delta + DEFLATE zaten vardır; uzayda ileride Rice/CCSDS 121.0 "
                "düşünülebilir — şimdilik NFR olarak izlenir, zorunlu değildir.",
            ],
            styles["li"],
        )
    )

    story.append(P("4.7 Yer segmenti ve işletme modeli", styles["h2"]))
    story.append(
        P(
            "TÜRKSAT yer istasyonu ve ağ işletmesi Gölbaşı (Ankara) merkezlidir. "
            "Önerilen işletme: TÜRKSAT kapasite kirası + TUA görev merkezi (SOC) + "
            "üniversite uç noktaları (5B spot veya karasal yedek). SENTİNEL panosu "
            "SOC’un “görev farkındalık” ekranı olarak konumlanır; TÜRKSAT NOC’un "
            "yerine geçmez.",
            styles["body"],
        )
    )
    story.append(
        bullets(
            [
                "<b>SENT-C-001:</b> Yazılım, Türksat modem API’si yokken de tam işlevsel kalacaktır "
                "(mevcut simülasyon). Uydu, isteğe bağlı taşıyıcıdır.",
                "<b>SENT-C-002:</b> Gelecekte bir “uplink_carrier” alanı eklenecekse değer kümesi "
                "en az {sim_dsn, turksat_6a_ku, turksat_5b_ka, turksat_5a_ku} olacaktır.",
                "<b>SENT-C-003:</b> 6A birincil varsayılan ulusal taşıyıcı kimliği olarak belgelerde "
                "ve eğitim metninde kullanılacaktır; 5B/5A tamamlayıcı olarak anılacaktır.",
            ],
            styles["li"],
        )
    )

    # --- 5 FUNCTIONAL ---
    story.append(P("5. Sistem özellikleri (işlevsel gereksinimler)", styles["h1"]))
    story.append(
        P(
            "Öncelik: <b>Z</b> = zorunlu (yoksa ürün kabul edilmez), <b>Ö</b> = önemli, "
            "<b>İ</b> = isteğe bağlı. Doğrulama: I = inceleme, T = test, D = demo, A = analiz.",
            styles["body"],
        )
    )

    story.append(P("5.1 Veri toplama ve replay", styles["h2"]))
    story.extend(
        table(
            ["ID", "Ön.", "Doğr.", "Gereksinim"],
            [
                [
                    "SENT-F-010",
                    "Z",
                    "T",
                    "Sistem, backend/data/test altındaki 12 MSL kanalını (T-1, T-2, P-10, P-14, M-6, M-7, C-1, C-2, D-14, D-15, D-16, F-7) sıralı okuyacaktır. Her kanalda yalnızca ilk sütun telemetri olarak kullanılacaktır.",
                ],
                [
                    "SENT-F-011",
                    "Z",
                    "T",
                    "Tur aralığı SENTINEL_SIM_INTERVAL_SECONDS ile 1–120 sn arasında sınırlanacak, varsayılan 10 sn olacaktır. NIRVANA_SIM_INTERVAL_SECONDS geriye dönük kabul edilecektir.",
                ],
                [
                    "SENT-F-012",
                    "Z",
                    "T",
                    "Her kayıtta channel_id ve replay_index (varsa) saklanacaktır.",
                ],
                [
                    "SENT-F-013",
                    "Z",
                    "T",
                    "labeled_anomalies.csv okunup ground_truth_anomaly alanına yazılacaktır; bu alan edge kararına girmeyecektir.",
                ],
                [
                    "SENT-F-014",
                    "Z",
                    "T",
                    "Veri seti yoksa veya kanallar eksikse simülasyon okuma üretmeyecek; GET /health status=degraded ve dataset.ready=false dönecektir.",
                ],
            ],
            styles,
            [28 * mm, 14 * mm, 16 * mm, 116 * mm],
        )
    )
    story.append(P("Tablo 12. Replay gereksinimleri.", styles["caption"]))

    story.append(P("5.2 Uç işleme, skor ve karar", styles["h2"]))
    story.extend(
        table(
            ["ID", "Ön.", "Doğr.", "Gereksinim"],
            [
                [
                    "SENT-F-020",
                    "Z",
                    "T",
                    "Her sensör tipi için son 500 okuma ring buffer’da tutulacaktır.",
                ],
                [
                    "SENT-F-021",
                    "Z",
                    "T",
                    "smoothed_errors varsa skor = 0,50×min(100, se×300) + 0,50×River; yoksa 0,40×min(100, z×25) + 0,60×River.",
                ],
                [
                    "SENT-F-022",
                    "Z",
                    "T",
                    "GET /health dataset.anomaly_score_source alanı etkin yolu bildirecektir (lstm_smoothed_error+river veya zscore+river).",
                ],
                [
                    "SENT-F-023",
                    "Z",
                    "T",
                    "Çalışma zamanında .h5 / Keras yüklenmeyecektir.",
                ],
                [
                    "SENT-F-024",
                    "Z",
                    "T",
                    "is_anomaly ve uplink_eligible, skor ≥ dinamik eşik ile aynı anda belirlenecektir. Üç kademeli gizli sınıf olmayacaktır.",
                ],
                [
                    "SENT-F-025",
                    "Z",
                    "T",
                    "Eşik EnergyController tabanı + RL (±5) ile 40–85 aralığında tutulacaktır. Batarya &lt;%20 → taban 70 / zlib 9; %20–50 → 60 / 7; &gt;%50 → 50 / 6.",
                ],
                [
                    "SENT-F-026",
                    "Ö",
                    "T",
                    "Yenilik (cosine, son 1000 vektör) is_novel ise bilimsel önceliğe +2 uygulayacaktır.",
                ],
                [
                    "SENT-F-027",
                    "Z",
                    "T",
                    "Eşik altı okumalar iletilmeyecek (DROP); üstü uplink_queue ve orbiter_queue’ya yazılacaktır.",
                ],
            ],
            styles,
            [28 * mm, 14 * mm, 16 * mm, 116 * mm],
        )
    )
    story.append(P("Tablo 13. Uç karar gereksinimleri.", styles["caption"]))

    story.append(P("5.3 Anomali sınıflama ve bilimsel öncelik", styles["h2"]))
    story.extend(
        table(
            ["ID", "Ön.", "Doğr.", "Gereksinim"],
            [
                [
                    "SENT-F-030",
                    "Z",
                    "I/T",
                    "Öncelik tablosu: 3+ eşzamanlı sensör → organik 10; CH4 → 8; SPEC → 7; MOIST → 6; UV → 5; O2/CO2 → 5; PRESS → 4; TEMP → 4.",
                ],
                [
                    "SENT-F-031",
                    "Z",
                    "T",
                    "Anomali olayı anomaly_type, severity, Türkçe description, scientific_priority (1–10) ile saklanacaktır.",
                ],
                [
                    "SENT-F-032",
                    "Z",
                    "T",
                    "Yetkili kullanıcı jeton ile anomaly acknowledge edebilecektir.",
                ],
            ],
            styles,
            [28 * mm, 14 * mm, 16 * mm, 116 * mm],
        )
    )
    story.append(P("Tablo 14. Anomali gereksinimleri.", styles["caption"]))

    story.append(P("5.4 Sıkıştırma, uplink ve orbiter", styles["h2"]))
    story.extend(
        table(
            ["ID", "Ön.", "Doğr.", "Gereksinim"],
            [
                [
                    "SENT-F-040",
                    "Z",
                    "T",
                    "İletilecek raw_value ve anomaly_score çiftleri LE float64 paketlenip delta kodlanacak ve zlib ile sıkıştırılacaktır.",
                ],
                [
                    "SENT-F-041",
                    "Z",
                    "T",
                    "stats_update; payload_serialized_bytes, payload_deflated_bytes, payload_deflate_ratio, payload_deflate_savings_percent ve son batch byte alanlarını taşıyacaktır.",
                ],
                [
                    "SENT-F-042",
                    "Z",
                    "I",
                    "transmission_log.compression_ratio paket iletim oranı (iletilen/toplam) anlamına gelecek; DEFLATE oranı ile karıştırılmayacaktır.",
                ],
                [
                    "SENT-F-043",
                    "Z",
                    "T",
                    "Uplink drain tur başına SENTINEL_UPLINK_DRAIN_BATCH (varsayılan 12, 1–200) paket gönderecektir.",
                ],
                [
                    "SENT-F-044",
                    "Z",
                    "T",
                    "Orbiter: skor &lt; 40 DROP; ~30 sn pencere; relay_latency_ms ve pass_id üretilecektir.",
                ],
                [
                    "SENT-F-045",
                    "Ö",
                    "T",
                    "Her 20 orbiter batch’te earth_cloud model_updates kaydı ve RL epsilon/eşik geri bildirimi yayınlanacaktır.",
                ],
            ],
            styles,
            [28 * mm, 14 * mm, 16 * mm, 116 * mm],
        )
    )
    story.append(P("Tablo 15. İletim ve röle gereksinimleri.", styles["caption"]))

    story.append(P("5.5 Yer istasyonu panosu", styles["h2"]))
    story.extend(
        table(
            ["ID", "Ön.", "Doğr.", "Gereksinim"],
            [
                [
                    "SENT-F-050",
                    "Z",
                    "D",
                    "Rotalar: / ana sayfa; /gosterge_paneli, /veri_akisi, /anomali_tespit, /sensor_detay, /telemetri, /rover_harita, /iletim_analizi, /uplink_kuyrugu, /orbiter_role, /yer_istasyonu_bulut, /veri_seti, /rover_zekasi.",
                ],
                [
                    "SENT-F-051",
                    "Z",
                    "D",
                    "Pano WebSocket ile sensor_reading, anomaly_alert, stats_update, uplink_queue_update, orbiter_stats, model_update, energy/rl ve rover_thinking mesajlarını işleyecektir.",
                ],
                [
                    "SENT-F-052",
                    "Ö",
                    "D",
                    "VERİ_AKIŞI 8 adımlı pedagojik animasyon + canlı stats_update bağlayacaktır; uçuş kopyası olduğu iddia edilmeyecektir.",
                ],
                [
                    "SENT-F-053",
                    "Z",
                    "D",
                    "Canlı tabloda channel_id ve TX (is_transmitted) görünecektir.",
                ],
                [
                    "SENT-F-054",
                    "İ",
                    "D",
                    "NASA_ARŞİV APOD ve rover fotoğraflarını gösterebilir; bunlar replay telemetrisi değildir.",
                ],
            ],
            styles,
            [28 * mm, 14 * mm, 16 * mm, 116 * mm],
        )
    )
    story.append(P("Tablo 16. Arayüz gereksinimleri.", styles["caption"]))

    story.append(P("5.6 Değerlendirme, sağlık ve rover AI", styles["h2"]))
    story.extend(
        table(
            ["ID", "Ön.", "Doğr.", "Gereksinim"],
            [
                [
                    "SENT-F-060",
                    "Z",
                    "T",
                    "GET /api/evaluation/detection nokta precision/recall/F1 ve Hundman dizi metriklerini (replay_index varken) döndürecek; sensor_type ile filtrelenebilecektir.",
                ],
                [
                    "SENT-F-061",
                    "Z",
                    "T",
                    "GET /health; status, dataset (channels_loaded/expected/missing, has_smoothed_errors, anomaly_score_source, ready), rover_ai kotası ve energy özetini döndürecektir.",
                ],
                [
                    "SENT-F-062",
                    "Ö",
                    "T",
                    "Rover düşünce: turda skor ≥ eşik adaylarından en yüksek skorlu tek okuma için en fazla bir dış model çağrısı yapılacaktır (kota koruması).",
                ],
                [
                    "SENT-F-063",
                    "Ö",
                    "T",
                    "GROQ_API_KEY yoksa veya model rate_limited/skipped ise telemetri boru hattı durmayacak, düşünce fallback/atılacaktır.",
                ],
                [
                    "SENT-F-064",
                    "Ö",
                    "T",
                    "Model kimliği GROQ_MODEL ile override edilebilecek; varsayılan openai/gpt-oss-20b (eski llama-3.3-70b-versatile kapandığı için).",
                ],
                [
                    "SENT-F-065",
                    "Z",
                    "T",
                    "POST /api/sensor-data/simulate ve rover-thinking PATCH jeton ile korunacaktır.",
                ],
            ],
            styles,
            [28 * mm, 14 * mm, 16 * mm, 116 * mm],
        )
    )
    story.append(P("Tablo 17. Sağlık, değerlendirme ve AI.", styles["caption"]))

    # --- 6 INTERFACES ---
    story.append(P("6. Dış arayüz gereksinimleri", styles["h1"]))
    story.append(P("6.1 Kullanıcı arayüzü", styles["h2"]))
    story.append(
        P(
            "Arayüz siberpunk/neon operasyon teması ile yumuşak ana sayfa teması arasında "
            "ayrılır. Bağlantı durumu bileşeni WS kopukluğunu göstermelidir. "
            "Erişilebilirlik hedefi: renk körlüğü için TX/anomali yalnızca renge "
            "bağlı kalmamalıdır (metin/ikon yedeği).",
            styles["body"],
        )
    )

    story.append(P("6.2 Yazılım arayüzleri — REST", styles["h2"]))
    story.extend(
        table(
            ["Yöntem", "Uç", "Koruma", "Açıklama"],
            [
                ["GET", "/health", "—", "Sağlık + veri seti + kota + enerji"],
                ["GET", "/api/sensor-data", "—", "skip/limit, opsiyonel sensor_type"],
                ["GET", "/api/sensor-data/stats", "—", "Tip istatistikleri"],
                ["GET", "/api/sensor-data/{id}", "—", "UUID detay"],
                ["POST", "/api/sensor-data/simulate", "X-API-Token", "Manuel batch"],
                ["GET", "/api/anomalies", "—", "Filtre + sayfalama"],
                ["GET", "/api/anomalies/recent", "—", "Son 10"],
                ["GET", "/api/anomalies/stats", "—", "Tip dağılımı"],
                ["GET", "/api/anomalies/{id}/detail", "—", "Okuma ile birlikte"],
                ["PATCH", "/api/anomalies/{id}/acknowledge", "X-API-Token", "Onay"],
                ["GET", "/api/evaluation/detection", "—", "Nokta + dizi metrik"],
                ["GET", "/api/uplink-queue", "—", "Kuyruk anlığı"],
                ["GET", "/api/nasa/apod", "—", "NASA vekil"],
                ["GET", "/api/nasa/mars-photos/{rover}", "—", "Fotoğraf vekil"],
                ["GET", "/api/orbiter-log", "—", "Röle günlüğü"],
                ["GET", "/api/model-updates", "—", "Yer/bulut geçmişi"],
                ["GET/PATCH", "/api/settings/rover-thinking", "PATCH jeton", "Düşünce anahtarı"],
            ],
            styles,
            [22 * mm, 62 * mm, 28 * mm, 62 * mm],
        )
    )
    story.append(P("Tablo 18. REST uçları.", styles["caption"]))
    story.append(
        P(
            "Jeton SENTINEL_API_TOKEN ile backend’de, VITE_API_TOKEN ile panelde eşleşir. "
            "Tanımsızsa yazma uçları 503 döner — açık sunucuda kimliksiz yazma veya "
            "Groq harcaması tetiklenemez. Okuma uçları ve WS korumasızdır (SENT-S-010).",
            styles["body"],
        )
    )

    story.append(P("6.3 Yazılım arayüzleri — WebSocket", styles["h2"]))
    story.append(
        P(
            "Uç: WS /ws/live-feed. Mesaj zarfı {\"type\": string, \"data\": object}. "
            "Tipler: sensor_reading, anomaly_alert, stats_update (içinde river_stats, "
            "energy_stats, rl_stats, uplink_queue), uplink_queue_update, orbiter_stats, "
            "model_update, energy_stats, rl_stats, rover_thinking.",
            styles["body"],
        )
    )

    story.append(P("6.4 Donanım ve iletişim arayüzleri", styles["h2"]))
    story.append(
        bullets(
            [
                "Geliştirme: localhost TCP 5173 (Vite), 8000 (API), 127.0.0.1:5432 (Postgres).",
                "Sensör donanımı yoktur; .npy replay donanım arayüzünün yerine geçer.",
                "Türksat RF/modem arayüzü bu sürümde yoktur (SENT-C-001). Hedef eşleme Bölüm 4.5.",
            ],
            styles["li"],
        )
    )

    story.append(P("6.5 Veri tabanı arayüzü", styles["h2"]))
    story.append(
        P(
            "DATABASE_URL zorunludur (postgresql+asyncpg://…). Alembic senkron sürücü için "
            "DATABASE_URL_SYNC veya otomatik çeviri kullanılır. Şema yalnızca "
            "alembic upgrade head ile oluşur.",
            styles["body"],
        )
    )

    # --- 7 DATA ---
    story.append(P("7. Veri modeli, API ve gerçek zamanlı akış", styles["h1"]))
    story.append(P("7.1 Mantıksal veri modeli", styles["h2"]))
    story.extend(
        table(
            ["Varlık", "Ana alanlar", "Amaç"],
            [
                [
                    "sensor_readings",
                    "sensor_type, channel_id, raw_value, anomaly_score, is_anomaly, "
                    "ground_truth_anomaly, is_transmitted, is_novel, replay_index, lat/lon, sol",
                    "Zaman serisi ve karar izi",
                ],
                [
                    "anomaly_events",
                    "reading_id, anomaly_type, severity, description, scientific_priority, acknowledged",
                    "Bilim operasyonu",
                ],
                [
                    "transmission_log",
                    "batch_id, total/transmitted_packets, bytes_saved, compression_ratio, window",
                    "Bant özeti (oran ≠ DEFLATE)",
                ],
                [
                    "uplink_queue",
                    "reading_id unique, uplink_priority, status, queued_at, sent_at, dsn_station",
                    "DSN analogu",
                ],
                [
                    "orbiter_queue / orbiter_relay_log",
                    "skor, pass_id, relay_latency_ms",
                    "Edge-2",
                ],
                [
                    "model_updates",
                    "threshold_suggestion, federated_round, precision/recall",
                    "Yer/bulut geri bildirim",
                ],
            ],
            styles,
            [42 * mm, 78 * mm, 54 * mm],
        )
    )
    story.append(P("Tablo 19. Mantıksal varlıklar.", styles["caption"]))

    story.append(P("7.2 Kullanılan MSL kanalları", styles["h2"]))
    story.extend(
        table(
            ["Kanal", "Tip", "Anlam (anlatı)", "Test şekli"],
            [
                ["T-1", "TEMP", "Sıcaklık / REMS bağlamı", "8612×25"],
                ["T-2", "TEMP", "Termal kontrol", "8625×25"],
                ["P-10", "PRESS", "Basınç sistemi", "6100×55"],
                ["P-14", "PRESS", "Hidrolik basınç", "6100×55"],
                ["M-6", "CH4", "Metan; uç değerler (ör. 258) z-score’u şişirebilir", "2049×55"],
                ["M-7", "MOIST", "Nem", "2156×55"],
                ["C-1", "SPEC", "Spektrometre A", "2264×55"],
                ["C-2", "SPEC", "Spektrometre B", "2051×55"],
                ["D-14", "UV", "UV radyasyon", "2625×55"],
                ["D-15", "O2", "Oksijen", "2158×55"],
                ["D-16", "CO2", "Karbondioksit", "2191×55"],
                ["F-7", "SPEC", "FTIR spektroskopi", "5054×55"],
            ],
            styles,
            [22 * mm, 22 * mm, 88 * mm, 42 * mm],
        )
    )
    story.append(P("Tablo 20. Kanal kataloğu (numpy şekilleri depo doğrulaması).", styles["caption"]))

    # --- 8 NFR ---
    story.append(P("8. Kalite öznitelikleri (işlevsel olmayan gereksinimler)", styles["h1"]))
    story.extend(
        table(
            ["ID", "Ön.", "Öznitelik", "Ölçüt"],
            [
                [
                    "SENT-Q-010",
                    "Z",
                    "Doğruluk / sızıntı",
                    "Edge is_anomaly hiçbir zaman ground_truth_anomaly’den türetilmez.",
                ],
                [
                    "SENT-Q-011",
                    "Z",
                    "Dürüstlük",
                    "Değerlendirme uçları hem nokta hem (mümkünse) dizi metrik verir; "
                    "makale F0.5 değeri ürün skoru olarak sunulmaz.",
                ],
                [
                    "SENT-Q-020",
                    "Ö",
                    "Performans",
                    "Bir simülasyon turu (12 kanal + yazma + yayın) aralık süresinin %80’ini aşmamalıdır.",
                ],
                [
                    "SENT-Q-021",
                    "Z",
                    "Kuyruk kararlılığı",
                    "Drain ≥ üretim (varsayılan 12/12); aksi halde is_transmitted gecikir ve bant metriği şişer.",
                ],
                [
                    "SENT-Q-030",
                    "Z",
                    "Kullanılabilirlik",
                    "Veri seti yokken süreç çökmez; degraded sağlık döner.",
                ],
                [
                    "SENT-Q-031",
                    "Ö",
                    "Kullanılabilirlik",
                    "Groq/NASA hatası çekirdek telemetriyi durdurmaz.",
                ],
                [
                    "SENT-Q-040",
                    "Z",
                    "Sürdürülebilirlik",
                    "Şema yalnızca Alembic; create_all yasak.",
                ],
                [
                    "SENT-Q-041",
                    "Ö",
                    "Taşınabilirlik",
                    "Python 3.11+, modern tarayıcı, Docker ile Postgres; Windows/Linux.",
                ],
                [
                    "SENT-Q-050",
                    "Ö",
                    "Gözlemlenebilirlik",
                    "/health ve WS stats_update operatörün tek bakışta durum almasını sağlar.",
                ],
                [
                    "SENT-Q-060",
                    "İ",
                    "Uluslararasılaştırma",
                    "UI Türkçe; alan adları İngilizce kalır (makine okuma).",
                ],
            ],
            styles,
            [26 * mm, 14 * mm, 36 * mm, 98 * mm],
        )
    )
    story.append(P("Tablo 21. İşlevsel olmayan gereksinimler.", styles["caption"]))

    story.append(
        P(
            "Bilinen performans gerçeği (36 000 okuma, z-score + River, eşik 50): "
            "işaretleme ~%28, precision 0,170, recall 0,472, F1 0,250. Bu, ürünün "
            "tespit kalitesinden çok veri azaltma mimarisini öne çıkardığının "
            "sayısal kanıtıdır (SENT-Q-011).",
            styles["note"],
        )
    )

    # --- 9 SECURITY ---
    story.append(P("9. Güvenlik ve gizlilik", styles["h1"]))
    story.extend(
        table(
            ["ID", "Ön.", "Gereksinim"],
            [
                [
                    "SENT-S-010",
                    "Z",
                    "Yazma uçları (POST/PATCH) X-API-Token ister; jeton yoksa 503. "
                    "Okuma ve WS bu sürümde açıktır — yalnızca güvenilen ağda çalıştırılmalıdır.",
                ],
                [
                    "SENT-S-011",
                    "Z",
                    "Parola, jeton ve anahtarlar depoya girmez (.gitignore .env). "
                    "Örnek dosyalarda gerçek sır olmaz.",
                ],
                [
                    "SENT-S-012",
                    "Z",
                    "CORS varsayılanı localhost origin’leridir; üretimde CORS_ALLOW_ORIGINS zorunlu düşünülür.",
                ],
                [
                    "SENT-S-013",
                    "Ö",
                    "Postgres bind 127.0.0.1:5432; veritabanı LAN’a açılmaz.",
                ],
                [
                    "SENT-S-014",
                    "Ö",
                    "Kaggle kaggle.json commit edilmez; LSTM artifaktı isteğe bağlıdır.",
                ],
                [
                    "SENT-S-015",
                    "İ",
                    "KVKK: ürün kişisel veri işlemez. Groq’a giden düşünce metni telemetri özeti içerebilir; "
                    "üretimde yurt dışı aktarım kaydı tutulmalıdır.",
                ],
                [
                    "SENT-S-016",
                    "Z",
                    "Sistem silah, patojen veya yetkisiz erişim aracı sunmaz; kapsam dışı listesi bağlayıcıdır.",
                ],
            ],
            styles,
            [26 * mm, 14 * mm, 134 * mm],
        )
    )
    story.append(P("Tablo 22. Güvenlik gereksinimleri.", styles["caption"]))

    # --- 10 V&V ---
    story.append(P("10. Doğrulama, kabul ve izlenebilirlik", styles["h1"]))
    story.append(P("10.1 Doğrulama yöntemleri", styles["h2"]))
    story.append(
        bullets(
            [
                "Birim testler: compressor, edge, river, RL, energy, auth, sequence metrics, rover_ai.",
                "Sağlık kabulü: GET /health → ready=true ve 12 kanal.",
                "Çevrimdışı skor: python scripts/score_sanity_check.py --steps 3000.",
                "Demo kabulü: pano rotaları + WS mesaj tiplerinin görünmesi.",
                "İnceleme: bu SRS’teki SENT-P ve SENT-C politika maddeleri.",
            ],
            styles["li"],
        )
    )

    story.append(P("10.2 Kabul kriterleri (minimum uygulanabilir ürün)", styles["h2"]))
    story.append(
        numbered(
            [
                "Postgres + Alembic head + 12 kanal replay + /health ok.",
                "Anomali ve TX kararları skor eşiğine bağlı; etiket sızıntısı yok.",
                "Uplink kuyruğu dolup boşalıyor; drain varsayılanı üretimi karşılıyor.",
                "Panel 5173’te canlı akış gösteriyor.",
                "Sunum metni MTH ve Türksat 6A+5B+5A kararını, GEO≠DSN uyarısıyla birlikte içeriyor.",
            ],
            styles["li"],
        )
    )

    story.append(P("10.3 İzlenebilirlik özeti", styles["h2"]))
    story.extend(
        table(
            ["Paydaş ihtiyacı", "Bölüm", "Gereksinimler"],
            [
                ["NASA MSL replay ile uç karar", "5.1–5.2", "SENT-F-010 … 027"],
                ["Bilim önceliği ve onay", "5.3", "SENT-F-030 … 032"],
                ["Bant / kuyruk / röle", "5.4", "SENT-F-040 … 045"],
                ["Türkçe yer istasyonu", "5.5, P-002", "SENT-F-050 … 054"],
                ["MTH anlatısı ve dürüstlük", "3", "SENT-P-001/002, Q-011"],
                ["Türksat hangi uydu", "4", "SENT-C-001 … 003"],
                ["Güvenlik tabanı", "9", "SENT-S-010 … 016"],
            ],
            styles,
            [52 * mm, 32 * mm, 90 * mm],
        )
    )
    story.append(P("Tablo 23. İhtiyaç–gereksinim izlenebilirliği.", styles["caption"]))

    # --- 11 ANNEX ---
    story.append(P("11. Ekler", styles["h1"]))
    story.append(P("Ek A. Karar özeti (yönetici sayfası)", styles["h2"]))
    story.append(
        P(
            "<b>Ürün:</b> SENTİNEL, NASA MSL telemetrisini replay ederek uçta anomali skoru, "
            "öncelik, sıkıştırma ve kuyruk uygulayan; yerde canlı pano sunan yazılım "
            "prototipidir. Canlı Mars linki değildir.",
            styles["body"],
        )
    )
    story.append(
        P(
            "<b>Millî Teknoloji Hamlesi:</b> Katkı, gövde üretmek değil; AYAP-2 sınıfı "
            "gezen araçların ihtiyaç duyacağı <i>veri azaltma ve uç karar</i> yazılımını "
            "yerli, izlenebilir ve Türkçe operasyonel dilde prototiplemektir. "
            "6A ile kazanılan haberleşme egemenliği, veri katmanında yabancı kara kutuya "
            "teslim edilmemelidir.",
            styles["body"],
        )
    )
    story.append(
        P(
            "<b>Türksat kararı:</b> Derin uzay için hiçbir Türksat uydusu kullanılmaz. "
            "Yer-segmenti bilim dağıtımında <b>birincil TÜRKSAT 6A</b> (milli, 42°D, "
            "Ku/Ka/Q-V); <b>kapasite tamamlayıcı TÜRKSAT 5B</b> (Ka-HTS, &gt;55 Gbps); "
            "<b>kapsama / kamu / 31°D tamamlayıcı TÜRKSAT 5A</b>. 3A önerilmez; "
            "4A/4B geçiş veya tatbikat.",
            styles["body"],
        )
    )

    story.append(P("Ek B. Ortam değişkenleri (kurulum sözleşmesi)", styles["h2"]))
    story.extend(
        table(
            ["Değişken", "Zorunlu", "Anlam"],
            [
                ["DATABASE_URL", "Evet", "postgresql+asyncpg://…"],
                ["DATABASE_URL_SYNC", "Hayır", "Alembic; boşsa çeviri"],
                ["SENTINEL_API_TOKEN", "Yazma için", "Boşsa yazma 503"],
                ["NASA_API_KEY", "Hayır", "Boşsa DEMO_KEY"],
                ["GROQ_API_KEY / GROQ_MODEL", "Hayır", "Düşünce; fallback"],
                ["CORS_ALLOW_ORIGINS", "Üretimde", "Virgüllü origin"],
                ["SENTINEL_SIM_INTERVAL_SECONDS", "Hayır", "Varsayılan 10"],
                ["SENTINEL_UPLINK_DRAIN_BATCH", "Hayır", "Varsayılan 12"],
                ["Kök POSTGRES_*", "Docker için", "compose kimlik bilgisi"],
                ["VITE_API_TOKEN", "Panel yazma", "Jeton ile aynı"],
            ],
            styles,
            [58 * mm, 28 * mm, 88 * mm],
        )
    )
    story.append(P("Tablo 24. Ortam sözleşmesi.", styles["caption"]))

    story.append(P("Ek C. Kaynak ve sınırlılık bildirimi", styles["h2"]))
    story.append(
        P(
            "Uydu teknik sayıları TÜRKSAT resmi web ve kamu duyurularından derlenmiştir "
            "(erişim Eylül 2026). Transponder kiralama, doluluk ve güncel EIRP için "
            "TÜRKSAT A.Ş. ticari teklifi esastır. Millî Uzay Programı hedefleri TUA "
            "strateji belgesi ve bakanlık kamu metinlerine dayanır; AYAP takvimi "
            "program güncellemelerine tabidir. Bu SRS, yazılım deposunun 1.0.0 "
            "davranışı ile hizalanmıştır.",
            styles["body"],
        )
    )
    story.append(
        P(
            "— Belge sonu. SENTINEL-SRS-2026-01 / Sürüm 1.0 / 6 Eylül 2026 —",
            styles["cover_meta"],
        )
    )

    def first_page(canvas, doc):
        cover_page(canvas, doc)

    def later_pages(canvas, doc):
        header_footer(canvas, doc)

    cover_end = next(
        i for i, x in enumerate(story) if isinstance(x, PageBreak)
    )
    story = story[: cover_end + 1] + bind_layout(story[cover_end + 1 :])

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title="SENTİNEL Yazılım Gereksinimleri Belirtimi (SRS)",
        author="SENTİNEL proje ekibi",
        subject="ISO/IEC/IEEE 29148 uyumlu SRS — MTH ve Türksat seçimi",
        creator="SENTİNEL generate_srs.py",
    )
    doc.build(story, onFirstPage=first_page, onLaterPages=later_pages)
    print(f"Wrote: {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
