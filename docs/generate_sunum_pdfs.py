"""SENTİNEL sunum PDF’leri: slayt metinleri, slayt konuşması, canlı demo konuşması."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
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
FONT_DIR = Path(r"C:\Windows\Fonts")

NAVY = colors.HexColor("#0B1F3A")
NAVY2 = colors.HexColor("#12355B")
GOLD = colors.HexColor("#B8860B")
TEAL = colors.HexColor("#0E7490")
CYAN = colors.HexColor("#0E7490")
INK = colors.HexColor("#1F2937")
MUTED = colors.HexColor("#4B5563")
LIGHT = colors.HexColor("#F4F7FB")
LINE = colors.HexColor("#D1D9E6")


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
    s["kicker"] = ParagraphStyle(
        "kicker",
        parent=base["Normal"],
        fontName=bold,
        fontSize=9,
        textColor=GOLD,
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    s["doc_title"] = ParagraphStyle(
        "doc_title",
        parent=base["Normal"],
        fontName=bold,
        fontSize=18,
        leading=23,
        textColor=NAVY,
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    s["doc_sub"] = ParagraphStyle(
        "doc_sub",
        parent=base["Normal"],
        fontName=reg,
        fontSize=11,
        leading=15,
        textColor=NAVY2,
        alignment=TA_CENTER,
        spaceAfter=10,
    )
    s["meta"] = ParagraphStyle(
        "meta",
        parent=base["Normal"],
        fontName=reg,
        fontSize=9,
        leading=13,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    s["h1"] = ParagraphStyle(
        "h1",
        parent=base["Heading1"],
        fontName=bold,
        fontSize=13,
        leading=17,
        textColor=NAVY,
        spaceBefore=8,
        spaceAfter=6,
        keepWithNext=1,
    )
    s["slide_no"] = ParagraphStyle(
        "slide_no",
        parent=base["Normal"],
        fontName=bold,
        fontSize=9,
        textColor=GOLD,
        spaceAfter=4,
    )
    s["slide_title"] = ParagraphStyle(
        "slide_title",
        parent=base["Normal"],
        fontName=bold,
        fontSize=16,
        leading=20,
        textColor=NAVY,
        alignment=TA_CENTER,
        spaceAfter=8,
    )
    s["slide_sub"] = ParagraphStyle(
        "slide_sub",
        parent=base["Normal"],
        fontName=italic,
        fontSize=12,
        leading=16,
        textColor=TEAL,
        alignment=TA_CENTER,
        spaceAfter=10,
    )
    s["body"] = ParagraphStyle(
        "body",
        parent=base["Normal"],
        fontName=reg,
        fontSize=11,
        leading=16,
        alignment=TA_LEFT,
        textColor=INK,
        spaceAfter=6,
    )
    s["body_c"] = ParagraphStyle(
        "body_c",
        parent=s["body"],
        alignment=TA_CENTER,
        fontSize=12,
        leading=17,
    )
    s["note"] = ParagraphStyle(
        "note",
        parent=s["body"],
        fontName=italic,
        fontSize=10,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceBefore=6,
    )
    s["speak"] = ParagraphStyle(
        "speak",
        parent=base["Normal"],
        fontName=reg,
        fontSize=11,
        leading=16.5,
        alignment=TA_JUSTIFY,
        textColor=INK,
        spaceAfter=8,
    )
    s["who"] = ParagraphStyle(
        "who",
        parent=base["Normal"],
        fontName=bold,
        fontSize=10,
        textColor=TEAL,
        spaceBefore=4,
        spaceAfter=3,
    )
    s["li"] = ParagraphStyle(
        "li",
        parent=s["body"],
        leftIndent=4,
        spaceAfter=4,
        fontSize=11,
        leading=15,
    )
    s["footer"] = ParagraphStyle(
        "footer",
        parent=base["Normal"],
        fontName=reg,
        fontSize=8,
        textColor=MUTED,
        alignment=TA_CENTER,
    )
    s["box"] = ParagraphStyle(
        "box",
        parent=s["body_c"],
        fontName=bold,
        fontSize=10,
        leading=13,
        textColor=NAVY,
    )
    return s


def _header_footer(title: str):
    def _draw(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, A4[1] - 8 * mm, A4[0], 8 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Body", 8)
        canvas.drawString(16 * mm, A4[1] - 5.4 * mm, "SENTİNEL  ·  10 dakikalık teknik sunum")
        canvas.drawRightString(A4[0] - 16 * mm, A4[1] - 5.4 * mm, title)
        canvas.setFillColor(LINE)
        canvas.rect(0, 0, A4[0], 10 * mm, fill=1, stroke=0)
        canvas.setFillColor(MUTED)
        canvas.setFont("Body", 8)
        canvas.drawString(16 * mm, 4.2 * mm, "Nirvana Ekibi  ·  slayt + canlı proje")
        canvas.drawRightString(A4[0] - 16 * mm, 4.2 * mm, f"s. {doc.page}")
        canvas.restoreState()

    return _draw


def _header_footer_land(title: str):
    w, h = landscape(A4)

    def _draw(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, h - 8 * mm, w, 8 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Body", 8)
        canvas.drawString(16 * mm, h - 5.4 * mm, "SENTİNEL  ·  slaytta görünen metin  ·  7 sayfa")
        canvas.drawRightString(w - 16 * mm, h - 5.4 * mm, title)
        canvas.setFillColor(LINE)
        canvas.rect(0, 0, w, 10 * mm, fill=1, stroke=0)
        canvas.setFillColor(MUTED)
        canvas.setFont("Body", 8)
        canvas.drawString(16 * mm, 4.2 * mm, "Bu metinleri slayta olduğu gibi aktarın. Konuşma ayrı PDF’tedir.")
        canvas.drawRightString(w - 16 * mm, 4.2 * mm, f"{doc.page} / 7")
        canvas.restoreState()

    return _draw


def _bullets(items: list[str], style: ParagraphStyle) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(x, style), leftIndent=12, bulletColor=TEAL) for x in items],
        bulletType="bullet",
        start="•",
        leftIndent=18,
        bulletFontName="Body-Bold",
        bulletFontSize=11,
    )


def _boxes(labels: list[str], styles: dict) -> Table:
    cells = [[Paragraph(x, styles["box"]) for x in labels]]
    t = Table(cells, colWidths=[42 * mm] * len(labels))
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.4, TEAL),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, LINE),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    return t


def build_slides(styles: dict) -> list:
    story: list = []
    story.append(Paragraph("SLAYT 01 / 07", styles["slide_no"]))
    story.append(Paragraph("SENTİNEL", styles["slide_title"]))
    story.append(
        Paragraph("Akıllı sensör veri iletimi ve anomali tespiti", styles["slide_sub"])
    )
    story.append(
        Paragraph(
            "Sınırlı bantta uçta karar, yerde izleme.",
            styles["body_c"],
        )
    )
    story.append(Spacer(1, 8 * mm))
    story.append(
        Paragraph(
            "SENTİNEL, dar bant ve gecikmeli bağlantıda sensör verisini uçta analiz eden, "
            "önceliklendiren ve yalnızca gerekli paketi ileten uçtan uca bir veri mimarisidir.",
            styles["body_c"],
        )
    )
    story.append(Spacer(1, 14 * mm))
    story.append(Paragraph("Teknik sunum  ·  slayt + canlı proje  ·  10 dakika", styles["note"]))
    story.append(PageBreak())

    story.append(Paragraph("SLAYT 02 / 07", styles["slide_no"]))
    story.append(Paragraph("Nirvana Ekibi", styles["slide_title"]))
    rows = [
        ["İbrahim Halil Akgül", "Sistem mimarı", "Edge tabanlı veri mimarisi ve boru hattı tasarımı"],
        ["Elif Kavurga", "Frontend ve raporlama", "Web arayüzü ve veri raporlama"],
        ["Emircan Can", "Güvenlik", "Güvenlik senaryoları, yazma koruması, sistem güvenliği"],
        ["Zehra Çiçek", "Sunum ve görselleştirme", "Görsel anlatım, arayüz ve sunum deneyimi"],
    ]
    head = [
        Paragraph("<b>Ad</b>", styles["box"]),
        Paragraph("<b>Rol</b>", styles["box"]),
        Paragraph("<b>Sorumluluk</b>", styles["box"]),
    ]
    data = [head]
    for a, b, c in rows:
        data.append(
            [
                Paragraph(a, styles["li"]),
                Paragraph(b, styles["li"]),
                Paragraph(c, styles["li"]),
            ]
        )
    tbl = Table(data, colWidths=[55 * mm, 50 * mm, 95 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.4, NAVY),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, LINE),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    # fix header text color via white paragraphs
    head_w = [
        Paragraph("<font color='white'><b>Ad</b></font>", styles["box"]),
        Paragraph("<font color='white'><b>Rol</b></font>", styles["box"]),
        Paragraph("<font color='white'><b>Sorumluluk</b></font>", styles["box"]),
    ]
    data[0] = head_w
    tbl = Table(data, colWidths=[55 * mm, 50 * mm, 95 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("BACKGROUND", (0, 1), (-1, 1), colors.white),
                ("BACKGROUND", (0, 2), (-1, 2), LIGHT),
                ("BACKGROUND", (0, 3), (-1, 3), colors.white),
                ("BACKGROUND", (0, 4), (-1, 4), LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.4, NAVY),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, LINE),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(Spacer(1, 6 * mm))
    story.append(tbl)
    story.append(PageBreak())

    story.append(Paragraph("SLAYT 03 / 07", styles["slide_no"]))
    story.append(Paragraph("Asıl sorun veri değil, seçim", styles["slide_title"]))
    story.append(Spacer(1, 4 * mm))
    story.append(
        _bullets(
            [
                "Sensör sürekli veri üretir; hepsini göndermek mümkün değildir.",
                "Fazla paket bantı tıkar; az paket kritik bilgiyi kaçırır.",
                "Soru: <b>Bu okuma şimdi gitsin mi, düşsün mü?</b>",
            ],
            styles["li"],
        )
    )
    story.append(PageBreak())

    story.append(Paragraph("SLAYT 04 / 07", styles["slide_no"]))
    story.append(Paragraph("Uçta karar, yerde izleme", styles["slide_title"]))
    story.append(Spacer(1, 3 * mm))
    story.append(_boxes(["Sensör", "Karar", "Kuyruk", "Yer istasyonu"], styles))
    story.append(Spacer(1, 8 * mm))
    story.append(
        Paragraph(
            "Skor eşiğin üstündeyse gider, altındaysa düşer. Batarya düşünce eşik yükselir.",
            styles["body_c"],
        )
    )
    story.append(
        Paragraph(
            "Canlı Mars hattı yok. NASA MSL / Curiosity kaydı sırayla replay edilir.",
            styles["note"],
        )
    )
    story.append(PageBreak())

    story.append(Paragraph("SLAYT 05 / 07", styles["slide_no"]))
    story.append(Paragraph("Millî Teknoloji Hamlesi", styles["slide_title"]))
    story.append(Paragraph("Yazılım da kritik teknolojidir", styles["slide_sub"]))
    story.append(
        _bullets(
            [
                "Hamle: dışa bağımlılığı azaltmak, yerli yetkinlik biriktirmek.",
                "SENTİNEL donanım üretmez; <b>görev veri mimarisi ve uç karar</b> katmanında yerli prototiptir.",
                "AYAP-2 sınıfı bir gezen araçta “hangi bilimsel paket Dünya’ya gitsin” kuralı da millidir.",
                "Kanıt: skor, eşik, sıkıştırma, kuyruk, Türkçe pano — kapalı kutu yabancı karar motoru yok.",
            ],
            styles["li"],
        )
    )
    story.append(
        Paragraph(
            "İddia etmiyoruz: uydu, RF veya uçuş yazılımı değil. Öğrenme nesnesi ve referans senaryo.",
            styles["note"],
        )
    )
    story.append(PageBreak())

    story.append(Paragraph("SLAYT 06 / 07", styles["slide_no"]))
    story.append(Paragraph("Şimdi panelde üç şey", styles["slide_title"]))
    story.append(Spacer(1, 6 * mm))
    story.append(
        _bullets(
            [
                "<b>1.</b> Verinin 8 adımda yürümesi  —  VERİ_AKIŞI",
                "<b>2.</b> Hangisinin gittiği  —  TX / anomali",
                "<b>3.</b> Bantın neden düştüğü  —  iletim / kuyruk",
            ],
            styles["li"],
        )
    )
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("Bu slayttan sonra tarayıcıya geçilir.", styles["note"]))
    story.append(PageBreak())

    story.append(Paragraph("SLAYT 07 / 07", styles["slide_no"]))
    story.append(Paragraph("Daha az paket, doğru paket", styles["slide_title"]))
    story.append(Spacer(1, 4 * mm))
    story.append(
        _bullets(
            [
                "Uçta seçim + sıkıştırma + kuyruk.",
                "Aynı fikir dar bant ve IoT için de geçerlidir.",
                "Veri göndermek yerine doğru kararı göndermeyi hedefler.",
            ],
            styles["li"],
        )
    )
    story.append(Spacer(1, 12 * mm))
    story.append(Paragraph("Sorular?", styles["slide_title"]))
    return story


def build_slide_speech(styles: dict) -> list:
    story: list = []
    story.append(Paragraph("KONUŞMA METNİ 1", styles["kicker"]))
    story.append(Paragraph("Slaytı sunarken okunacak metin", styles["doc_title"]))
    story.append(
        Paragraph(
            "Süre: yaklaşık 4 dakika (0:00–4:20). Konuşan: A. B bu sürede tarayıcıyı hazırlar, slaytta konuşmaz.",
            styles["doc_sub"],
        )
    )
    story.append(
        Paragraph(
            "Nasıl kullanın: slayt değişince kalın başlığı görün, altındaki metni doğal okuyun. "
            "Parantez içi sahne notudur, jüriye okunmaz.",
            styles["meta"],
        )
    )

    blocks = [
        (
            "0:00–0:40  ·  Slayt 1 ve 2  ·  Kapak + Nirvana Ekibi",
            "A konuşur",
            "Merhaba. Bu sunum SENTİNEL. Sınırlı bantta çalışan bir sensör veri mimarisi. "
            "Rover uçta hangi paketin gideceğine karar veriyor; yer istasyonu bunu canlı izliyor. "
            "İki parçayız: önce slaytta hikâye ve kural, hemen ardından aynı kuralı açık projede göstereceğiz. "
            "Ekip: İbrahim sistem mimarisi, Elif arayüz ve raporlama, Emircan güvenlik, Zehra sunum ve görselleştirme. "
            "On dakikamız var; teknik iddiayı slaytta tutuyoruz, kanıtı panelde.",
        ),
        (
            "0:40–1:40  ·  Slayt 3  ·  Asıl sorun veri değil, seçim",
            "A konuşur",
            "Sensör durmadan veri üretir. Uzayda ve dar hatta her şeyi Dünya’ya atamazsınız: bant dar, enerji az, gecikme var. "
            "İki kötü uç var. Birincisi her paketi göndermek — hat dolar, önemsiz gürültü gider. "
            "İkincisi çok az göndermek — bilimsel olarak değerli olan kaçabilir. "
            "Bizim sorduğumuz tek şey şu: bu okuma şimdi gitsin mi, düşsün mü? "
            "Asıl problem veri üretmek değil, seçmek.",
        ),
        (
            "1:40–3:00  ·  Slayt 4  ·  Uçta karar, yerde izleme",
            "A konuşur",
            "Dört kutu. Sensör, karar, kuyruk, yer istasyonu. "
            "Sensörden gelen değere bir skor veriyoruz. Skor eşiğin üstündeyse paket uplink kuyruğuna girer. "
            "Altındaysa düşer, Dünya’ya gitmez. Batarya zayıfsa çıtayı yükseltiriz; daha az şey gider. "
            "Ayrıca bilimsel öncelik var: metan ve organik imza önce, sıcaklık sonra. "
            "Dürüst sınır: canlı Mars bağlantımız yok. NASA’nın Curiosity, yani MSL, kaydını sırayla oynatıyoruz. "
            "Uçta Keras ile LSTM çalıştırmıyoruz. Asıl gösterdiğimiz şey uçtan yere veri azaltma mimarisi.",
        ),
        (
            "3:00–4:10  ·  Slayt 5  ·  Millî Teknoloji Hamlesi",
            "A konuşur",
            "Millî Teknoloji Hamlesi yalnızca uydu gövdesi veya itki değildir. "
            "Görev çoğu zaman veri yolunda kaybedilir: yanlış öncelik, dolu kuyruk, gereksiz bit. "
            "Türkiye AYAP-2 gibi bir gezen araç indirdiğinde, bilimsel değeri olan örneği hangi kurala göre "
            "Dünya’ya göndereceğini uçta kararlaştıran yazılım da kritik teknolojidir. "
            "Bu yazılım yurt dışında kara kutu kalırsa, haberleşme egemenliği veri katmanında yeniden dışa bağımlı olur. "
            "SENTİNEL bir milli rover değildir, TÜRKSAT değildir, uçuş yazılımı değildir. "
            "Yerli tasarım bir prototiptir. Karar izlenebilir, veri seti etiketi karara karışmaz, "
            "sıkıştırma gerçek bir codec, arayüz Türkçe. Hamleye katkımız abartılı bir iddia değil; "
            "öğrenilebilir, tekrar edilir bir omurga.",
        ),
        (
            "4:10–4:20  ·  Slayt 6  ·  Demo köprüsü",
            "A konuşur, B tarayıcıyı paylaşır",
            "Şimdi aynı kuralı panelde göstereceğiz. Üç şey: verinin sekiz adımda yürümesi, "
            "hangisinin gittiği, bantın neden düştüğü. Slaytı bırakıyoruz.",
        ),
    ]
    for title, who, text in blocks:
        story.append(
            KeepTogether(
                [
                    Paragraph(title, styles["h1"]),
                    Paragraph(who, styles["who"]),
                    Paragraph(text, styles["speak"]),
                ]
            )
        )

    story.append(Paragraph("Slayt 7 bu PDF’te okunmaz", styles["h1"]))
    story.append(
        Paragraph(
            "Kapanış slaytı canlı demo bittikten sonra açılır. O metin üçüncü PDF’in sonundadır. "
            "Burada 4:20’de tarayıcıya geçin.",
            styles["speak"],
        )
    )

    story.append(Paragraph("Slayt sırasında söylemeyin", styles["h1"]))
    story.append(
        _bullets(
            [
                "Canlı DSN, canlı Mars, gerçek rover bağlantısı.",
                "Uçta Keras / TensorFlow çıkarımı.",
                "Makaledeki F1 veya 0,69 bizim sonucumuz.",
                "Federated learning üretimde var.",
                "Milli uydu / milli rover ürettik.",
            ],
            styles["li"],
        )
    )
    return story


def build_demo_speech(styles: dict) -> list:
    story: list = []
    story.append(Paragraph("KONUŞMA METNİ 2", styles["kicker"]))
    story.append(Paragraph("Canlı projede okunacak metin", styles["doc_title"]))
    story.append(
        Paragraph(
            "Süre: yaklaşık 5 dakika (4:20–9:00) + kapanış (9:00–10:00). Ekranı B sürer, A yalnızca işaret eder.",
            styles["doc_sub"],
        )
    )
    story.append(
        Paragraph(
            "Hazırlık: http://localhost:5173 açık. VERİ_AKIŞI, GÖSTERGE_PANELİ, ANOMALİ_TESPİT, "
            "İLETİM_ANALİZİ veya UPLINK_KUYRUĞU sekmeleri hazır olsun. Ana sayfa 3D, CASPIAN, NASA_ARŞİV, "
            "ROVER_ZEKASI’na girmeyin.",
            styles["meta"],
        )
    )

    story.append(Paragraph("Sahne notu — başlamadan 30 saniye", styles["h1"]))
    story.append(
        Paragraph(
            "B: tarayıcı tam ekran, adres çubuğu sade. Simülasyon en az iki üç tur dönmüş olsun; tablo boş görünmesin. "
            "Wi-Fi düşerse yedek ekran videosuna geçin: “aynı koşunun kaydı” deyin.",
            styles["speak"],
        )
    )

    blocks = [
        (
            "4:20–5:20  ·  Ekran 1  ·  /veri_akisi",
            "B konuşur",
            "Burası VERİ_AKIŞI. Rover’dan Dünya’ya veri sekiz adımda yürüyor: toplama, tampon, anomali skoru, "
            "karar, öncelik, sıkıştırma, iletim, yer istasyonu. Hızı yavaşlattık ki adımlar görünsün. "
            "Bu ekran bir eğitim şeması; uçuş yazılımının birebir kopyası değil. Alttaki sayılar mümkün olduğunca "
            "canlı backend’den geliyor. Slayttaki dört kutunun açılmış hali bu.",
        ),
        (
            "5:20–6:20  ·  Ekran 2  ·  /gosterge_paneli",
            "B konuşur",
            "Gösterge paneli. Canlı tablo. TX yazan satır Dünya’ya giden paket. TX olmayanı rover düşürdü; "
            "eşik altı skor. Yüksek skorlu satır anomali. Burada slayttaki kuralı görüyorsunuz: "
            "skor eşiğin üstündeyse gider, altındaysa düşer. A, yalnızca “şu TX satırı” diye işaret edebilir.",
        ),
        (
            "6:20–7:20  ·  Ekran 3  ·  /anomali_tespit",
            "B konuşur",
            "Anomali merkezi. Bir alarm açıyorum. Skor yüksek, tip var, bilimsel öncelik var. "
            "Metan veya spektral sapma sıcaklıktan önce gider. Onay düğmesi yerdeki bilimci içindir; "
            "iletme kararı uçta, skora göre, zaten alınmıştır. Veri setindeki etiket bu karara karışmaz; "
            "yalnızca sonra doğruluk ölçmek için saklanır.",
        ),
        (
            "7:20–8:40  ·  Ekran 4  ·  /iletim_analizi veya /uplink_kuyrugu",
            "B konuşur",
            "İletim ve kuyruk. Giden paket sayısı toplam okumadan az. Tasarruf buradan. "
            "Yüksek öncelikli paket kuyrukta bekler, sonra sınırlı sayıda gönderilir. "
            "Dar bantta her şey aynı anda gitmez; sıra ve eşik birlikte çalışır. "
            "Sıkıştırma da var: gidecek sayılar fark ve zlib ile küçülür. "
            "Millî Teknoloji tarafına bağlarsak: görev başarısı çoğu zaman bu kuyrukta ve bu seçimde belli olur.",
        ),
        (
            "8:40–9:00  ·  Demo kapanışı, slayta dönüş",
            "B bir cümle, A slayt 7’yi açar",
            "B: Üç şeyi gördünüz. Akış nasıl yürüyor, kim gidiyor, bant neden düşüyor. "
            "A: Slayta dönüyoruz.",
        ),
        (
            "9:00–10:00  ·  Slayt 7  ·  Kapanış",
            "A konuşur",
            "Özet: daha az paket, doğru paket. Uçta seç, sıkıştır, kuyruğa al, yerde izle. "
            "Bu bir yazılım prototipi; canlı Mars hattı değil. Aynı desen dar bantta ve IoT’ta da geçerli. "
            "Millî Teknoloji Hamlesi için söylediğimiz şey şu: gezen araç indirdiğinizde "
            "hangi bilimsel bitin gideceğine karar veren yazılım da yerli ve izlenebilir olmalı. "
            "Sorunuz var mı?",
        ),
    ]
    for title, who, text in blocks:
        story.append(
            KeepTogether(
                [
                    Paragraph(title, styles["h1"]),
                    Paragraph(who, styles["who"]),
                    Paragraph(text, styles["speak"]),
                ]
            )
        )

    story.append(Paragraph("Göstermeyin", styles["h1"]))
    story.append(
        _bullets(
            [
                "Ana sayfa 3D rover turu, HYPERDRIVE, CASPIAN.",
                "NASA_ARŞİV — telemetri değil, süre yer.",
                "ROVER_ZEKASI — Groq gecikirse boş kalabilir.",
                "Kod editörü, terminal, /health ham JSON.",
            ],
            styles["li"],
        )
    )

    story.append(Paragraph("Jüri sorusu gelirse (ezber, slaytta yok)", styles["h1"]))
    qa = [
        ["Canlı Mars mı?", "Hayır. NASA MSL / Curiosity kaydını sırayla replay ediyoruz."],
        ["LSTM uçta mı?", "Keras yüklemiyoruz. Hata dosyası varsa skora karışır; yoksa z-score ve çevrimiçi model."],
        ["F1 0,69 sizin mi?", "Hayır. 2018 Hundman makalesi. Bizim güç yanımız uçtan yere veri azaltma."],
        ["Milli rover mı?", "Değil. Yerli yazılım prototipi. Donanım ve RF yok."],
        ["MTH kanıtı nedir?", "Karar kodu yerli ve izlenebilir; etiket sızmaz; Türkçe pano; kapalı kutu motor yok."],
        ["Neden TX yok?", "Skor o anda eşiğin altında. Batarya yüksek eşiği de yükseltebilir."],
    ]
    head = [
        Paragraph("<font color='white'><b>Soru</b></font>", styles["box"]),
        Paragraph("<font color='white'><b>Tek cümle</b></font>", styles["box"]),
    ]
    data = [head]
    for q, a in qa:
        data.append([Paragraph(q, styles["li"]), Paragraph(a, styles["li"])])
    qt = Table(data, colWidths=[48 * mm, 132 * mm])
    qt.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("BACKGROUND", (0, 1), (-1, -1), LIGHT),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                ("BOX", (0, 0), (-1, -1), 0.4, NAVY),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, LINE),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(qt)
    return story


def _build_portrait(path: Path, title: str, flow, styles: dict) -> None:
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=title,
        author="Nirvana Ekibi",
        subject="SENTİNEL 10 dakikalık teknik sunum",
    )
    doc.build(flow, onFirstPage=_header_footer(title), onLaterPages=_header_footer(title))


def main() -> None:
    reg, bold, italic = _register_fonts()
    styles = _styles(reg, bold, italic)

    p1 = ROOT / "SENTINEL_Sunum_1_Slayt_Metinleri.pdf"
    doc = SimpleDocTemplate(
        str(p1),
        pagesize=landscape(A4),
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="SENTİNEL slayt metinleri (7 sayfa)",
        author="Nirvana Ekibi",
    )
    doc.build(
        build_slides(styles),
        onFirstPage=_header_footer_land("Slayt metinleri"),
        onLaterPages=_header_footer_land("Slayt metinleri"),
    )

    p2 = ROOT / "SENTINEL_Sunum_2_Konusma_Slayt.pdf"
    _build_portrait(p2, "Slayt konuşma metni", build_slide_speech(styles), styles)

    p3 = ROOT / "SENTINEL_Sunum_3_Konusma_Canli_Demo.pdf"
    _build_portrait(p3, "Canlı proje konuşma metni", build_demo_speech(styles), styles)

    print(p1)
    print(p2)
    print(p3)


if __name__ == "__main__":
    main()
