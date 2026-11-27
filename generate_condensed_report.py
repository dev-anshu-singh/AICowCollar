import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_margins(cell, top=80, bottom=80, left=100, right=100):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_background(cell, hex_color):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def add_page_border(section):
    """Adds classic black double-line page border typical of academic reports."""
    sectPr = section._sectPr
    pgBorders = OxmlElement('w:pgBorders')
    pgBorders.set(qn('w:offsetFrom'), 'page')
    for side in ['top', 'left', 'bottom', 'right']:
        border = OxmlElement(f'w:{side}')
        border.set(qn('w:val'), 'double')
        border.set(qn('w:sz'), '12')
        border.set(qn('w:space'), '20')
        border.set(qn('w:color'), '000000')  # Strictly Black
        pgBorders.append(border)
    sectPr.append(pgBorders)

def create_condensed_report():
    doc = docx.Document()
    
    # Page Setup: A4 with 1.0 inch margins
    section = doc.sections[0]
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.top_margin = Inches(0.9)
    section.bottom_margin = Inches(0.9)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)

    # Add black double-line page border
    add_page_border(section)

    # Header and Footer Setup (different on first page)
    section.different_first_page_header_footer = True
    
    # Running Header for Body Pages (Strictly Black)
    header = section.header
    p_h = header.paragraphs[0]
    p_h.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_h = p_h.add_run("Design of a Smart Cow Collar for Health & Position Monitoring | Minor Project Report")
    r_h.font.name = "Times New Roman"
    r_h.font.size = Pt(8.5)
    r_h.italic = True
    r_h.font.color.rgb = RGBColor(0, 0, 0)

    # Running Footer for Body Pages (Strictly Black)
    footer = section.footer
    p_f = footer.paragraphs[0]
    p_f.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_f = p_f.add_run("Department of Mechatronics and Automation Engineering, IIIT Bhagalpur")
    r_f.font.name = "Times New Roman"
    r_f.font.size = Pt(8.5)
    r_f.italic = True
    r_f.font.color.rgb = RGBColor(0, 0, 0)

    # Base Styles (Strictly Black)
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(11.5)
    normal_style.font.color.rgb = RGBColor(0, 0, 0)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(3)

    def add_p(text="", align=WD_ALIGN_PARAGRAPH.LEFT, bold=False, italic=False, size_pt=11.5, space_before=0, space_after=3, line_spacing=1.15, font_name="Times New Roman"):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = line_spacing
        if text:
            run = p.add_run(text)
            run.bold = bold
            run.italic = italic
            run.font.name = font_name
            run.font.size = Pt(size_pt)
            run.font.color.rgb = RGBColor(0, 0, 0)
        return p

    def add_chapter_header(chap_num_str, chap_title_str):
        p1 = add_p(chap_num_str.upper(), align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=13, space_before=10, space_after=2)
        p2 = add_p(chap_title_str.upper(), align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=14, space_before=2, space_after=10)
        return p2

    def add_h2(text):
        p = add_p(text, align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, size_pt=12.5, space_before=8, space_after=3)
        return p

    def add_figure(img_path, caption_text, width=Inches(4.4)):
        if os.path.exists(img_path):
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(6)
            p_img.paragraph_format.space_after = Pt(2)
            run = p_img.add_run()
            run.add_picture(img_path, width=width)
            
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_before = Pt(2)
            p_cap.paragraph_format.space_after = Pt(6)
            r = p_cap.add_run(caption_text)
            r.font.name = "Times New Roman"
            r.font.size = Pt(9.5)
            r.italic = True
            r.font.color.rgb = RGBColor(0, 0, 0)

    # =========================================================================
    # 1. TITLE / COVER PAGE
    # =========================================================================
    add_p("A", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=13, space_before=2, space_after=2)
    add_p("Minor Project Report", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=16, space_before=2, space_after=4)
    add_p("On", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size_pt=11.5, space_before=1, space_after=4)
    
    title_p = add_p("Design of a Smart Cow Collar for Health and Position Monitoring System using AI&ML",
                    align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=16, space_before=2, space_after=12)

    add_p("Submitted in partial fulfillment of the requirements for the award of the degree of",
          align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size_pt=10.5, space_before=2, space_after=2)
    add_p("Bachelor of Technology", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=13.5, space_before=2, space_after=2)
    add_p("In", align=WD_ALIGN_PARAGRAPH.CENTER, size_pt=11, space_before=1, space_after=2)
    add_p("Mechatronics and Automation Engineering", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=13.5, space_before=2, space_after=12)

    # Candidate and Supervisor Table
    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.rows[0].cells[0].width = Inches(3.1)
    table.rows[0].cells[1].width = Inches(3.1)
    set_cell_margins(table.rows[0].cells[0], top=60, bottom=60, left=80, right=80)
    set_cell_margins(table.rows[0].cells[1], top=60, bottom=60, left=80, right=80)
        
    p_l = table.cell(0, 0).paragraphs[0]
    p_l.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p_l.add_run("Submitted by:\n")
    r.bold = True
    r.font.size = Pt(10.5)
    r2 = p_l.add_run("Devanshu Singh (Roll No. 230103012)\nMahima Patel (Roll No. 230103025)\n\nB.Tech (MAE), VII Semester")
    r2.font.size = Pt(10)

    p_r = table.cell(0, 1).paragraphs[0]
    p_r.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p_r.add_run("Under the Supervision of:\n")
    r.bold = True
    r.font.size = Pt(10.5)
    r2 = p_r.add_run("Dr. Sunil Kumar\nAssistant Professor\nDepartment of Mechatronics &\nAutomation Engineering\nIIIT Bhagalpur")
    r2.font.size = Pt(10)

    add_p("", space_before=6, space_after=2)

    # Institutional Logos
    logo_table = doc.add_table(rows=1, cols=2)
    logo_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    logo_table.autofit = False
    logo_table.rows[0].cells[0].width = Inches(3.1)
    logo_table.rows[0].cells[1].width = Inches(3.1)

    p_l1 = logo_table.cell(0, 0).paragraphs[0]
    p_l1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if os.path.exists("extracted_report_media/word/media/image1.jpeg"):
        p_l1.add_run().add_picture("extracted_report_media/word/media/image1.jpeg", width=Inches(0.95))

    p_l2 = logo_table.cell(0, 1).paragraphs[0]
    p_l2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if os.path.exists("extracted_report_media/word/media/image2.png"):
        p_l2.add_run().add_picture("extracted_report_media/word/media/image2.png", width=Inches(0.90))

    add_p("", space_before=2, space_after=1)

    add_p("भारतीय सूचना प्रौद्योगिकी संस्थान, भागलपुर", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=12, space_before=2, space_after=1, font_name="Nirmala UI")
    add_p("Indian Institute of Information Technology, Bhagalpur", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=12.5, space_before=1, space_after=1)
    add_p("(An Institute of National Importance Under Act of Parliament)", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size_pt=10, space_before=1, space_after=3)
    add_p("November 2026", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=11, space_before=2, space_after=2)

    doc.add_page_break()

    # =========================================================================
    # 2. DECLARATION
    # =========================================================================
    header_table = doc.add_table(rows=1, cols=2)
    header_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    header_table.autofit = False
    header_table.rows[0].cells[0].width = Inches(3.1)
    header_table.rows[0].cells[1].width = Inches(3.1)
    if os.path.exists("extracted_report_media/word/media/image1.jpeg"):
        header_table.cell(0, 0).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        header_table.cell(0, 0).paragraphs[0].add_run().add_picture("extracted_report_media/word/media/image1.jpeg", width=Inches(0.80))
    if os.path.exists("extracted_report_media/word/media/image2.png"):
        header_table.cell(0, 1).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        header_table.cell(0, 1).paragraphs[0].add_run().add_picture("extracted_report_media/word/media/image2.png", width=Inches(0.75))

    add_p("भारतीय सूचना प्रौद्योगिकी संस्थान, भागलपुर", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=11, space_before=2, space_after=1, font_name="Nirmala UI")
    add_p("Indian Institute of Information Technology, Bhagalpur", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=11.5, space_before=1, space_after=1)
    add_p("(An Institute of National Importance Under Act of Parliament)", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size_pt=9.5, space_before=1, space_after=10)

    p_dec = add_p("DECLARATION", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=13, space_before=4, space_after=8)
    p_dec.runs[0].underline = True

    add_p(
        "We hereby declare that the Minor Project Report entitled \"Design of a Smart Cow Collar for Health and "
        "Position Monitoring System using AI&ML\" submitted to the Department of Mechatronics and Automation Engineering, "
        "Indian Institute of Information Technology, Bhagalpur, in partial fulfillment of the requirements for the award "
        "of the degree of Bachelor of Technology, is an authentic record of our own work carried out during the "
        "academic session 2026-2027.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=4, space_after=6
    )
    add_p(
        "The matter embodied in this report has not been submitted earlier for the award of any other degree or diploma to any other "
        "University or Institute. All sources of data, open-source software libraries, and published literature used in this work have been duly acknowledged.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=4, space_after=16
    )

    add_p("Date:  28 November 2026", bold=True, size_pt=10.5, space_after=2)
    add_p("Place: IIIT Bhagalpur, Bihar", bold=True, size_pt=10.5, space_after=20)

    sig_table = doc.add_table(rows=1, cols=2)
    sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sig_table.autofit = False
    sig_table.rows[0].cells[0].width = Inches(3.1)
    sig_table.rows[0].cells[1].width = Inches(3.1)
    
    p = sig_table.cell(0, 0).paragraphs[0]
    p.add_run("_____________________\nDevanshu Singh\nRoll No.: 230103012\nB.Tech (MAE)").font.size = Pt(10.5)
    
    p = sig_table.cell(0, 1).paragraphs[0]
    p.add_run("_____________________\nMahima Patel\nRoll No.: 230103025\nB.Tech (MAE)").font.size = Pt(10.5)

    doc.add_page_break()

    # =========================================================================
    # 3. CERTIFICATE
    # =========================================================================
    header_table2 = doc.add_table(rows=1, cols=2)
    header_table2.alignment = WD_TABLE_ALIGNMENT.CENTER
    header_table2.autofit = False
    header_table2.rows[0].cells[0].width = Inches(3.1)
    header_table2.rows[0].cells[1].width = Inches(3.1)
    if os.path.exists("extracted_report_media/word/media/image1.jpeg"):
        header_table2.cell(0, 0).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        header_table2.cell(0, 0).paragraphs[0].add_run().add_picture("extracted_report_media/word/media/image1.jpeg", width=Inches(0.80))
    if os.path.exists("extracted_report_media/word/media/image2.png"):
        header_table2.cell(0, 1).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        header_table2.cell(0, 1).paragraphs[0].add_run().add_picture("extracted_report_media/word/media/image2.png", width=Inches(0.75))

    add_p("भारतीय सूचना प्रौद्योगिकी संस्थान, भागलपुर", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=11, space_before=2, space_after=1, font_name="Nirmala UI")
    add_p("Indian Institute of Information Technology, Bhagalpur", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=11.5, space_before=1, space_after=1)
    add_p("(An Institute of National Importance Under Act of Parliament)", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size_pt=9.5, space_before=1, space_after=10)

    p_cert = add_p("CERTIFICATE", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=13, space_before=4, space_after=8)
    p_cert.runs[0].underline = True

    add_p(
        "This is to certify that the Minor Project Report entitled \"Design of a Smart Cow Collar for Health and "
        "Position Monitoring System using AI&ML\" being submitted by Devanshu Singh (Roll No. 230103012) and "
        "Mahima Patel (Roll No. 230103025) in partial fulfillment of the requirements for the award of the degree of "
        "Bachelor of Technology in Mechatronics and Automation Engineering at the Indian Institute of Information Technology, "
        "Bhagalpur, is a bonafide record of project work carried out by them under my supervision and guidance.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=4, space_after=6
    )
    add_p(
        "To the best of my knowledge, the algorithmic developments, system designs, and experimental evaluations presented "
        "in this report are original and have not been submitted to any other university or institution for the award of any degree or diploma.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=4, space_after=20
    )

    cert_table = doc.add_table(rows=1, cols=2)
    cert_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cert_table.autofit = False
    cert_table.rows[0].cells[0].width = Inches(3.1)
    cert_table.rows[0].cells[1].width = Inches(3.1)

    cert_table.cell(0, 0).paragraphs[0].add_run("___________________________\nDr. Sunil Kumar\n(Project Supervisor)\nAssistant Professor\nDept. of Mechatronics & Automation Engg.\nIIIT Bhagalpur").font.size = Pt(10.5)
    cert_table.cell(0, 1).paragraphs[0].add_run("___________________________\nHead of Department\nDept. of Mechatronics & Automation Engg.\nIIIT Bhagalpur").font.size = Pt(10.5)

    doc.add_page_break()

    # =========================================================================
    # 4. ACKNOWLEDGEMENT & ABSTRACT (Combined on One Page like PDF page 4)
    # =========================================================================
    p_ack = add_p("ACKNOWLEDGEMENT", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=13, space_before=2, space_after=6)
    p_ack.runs[0].underline = True

    add_p(
        "We express our sincere gratitude to our project supervisor, Dr. Sunil Kumar, Assistant Professor in the Department "
        "of Mechatronics and Automation Engineering, Indian Institute of Information Technology, Bhagalpur, for his continuous "
        "encouragement, insightful advice, and technical guidance throughout the development of this minor project.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=1, space_after=4
    )
    add_p(
        "We also thank the faculty members and technical staff of the Department of Mechatronics and Automation Engineering for "
        "providing the laboratory facilities and academic resources. In addition, we extend our gratitude to our peers and classmates "
        "for their collaborative discussions during the implementation of the telemetry pipeline. Finally, we thank our families "
        "for their constant support and motivation.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=1, space_after=12
    )

    p_abs = add_p("ABSTRACT", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=13, space_before=4, space_after=6)
    p_abs.runs[0].underline = True

    add_p(
        "Monitoring the health and daily behavior of dairy cows is important for early disease detection and overall farm management. "
        "Manual observation by visual inspection is labor intensive and can easily miss early symptoms of illness. In this report, "
        "the system design, signal processing methodology, and machine learning pipeline for a smart cow collar platform (AICowCollar) "
        "are developed and evaluated.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=1, space_after=4
    )
    add_p(
        "To preserve collar battery life, the proposed hardware unit offloads feature extraction and machine learning to a central FastAPI "
        "server. The motion signals are processed using 12 non-redundant physical features extracted from sliding windows. An ExtraTrees classifier "
        "achieves 95.54% overall accuracy and a walking F1-score of 91.80% in discriminating standing, lying, grazing, and walking states. "
        "In addition, an ambient-decoupled CUSUM temperature filter detects fevers and hypothermia, activity-gated pulse rules identify acute stress, "
        "and a Ray-Casting geofence with two-strike debouncing eliminates boundary false alarms. An automated veterinary assistant powered by "
        "Gemini 3.8 Flash synthesizes multi-sensor vitals into clear diagnostic cards for farm operators, establishing a verified algorithmic foundation "
        "for future physical prototyping.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=1, space_after=4
    )

    doc.add_page_break()

    # =========================================================================
    # 5. TABLE OF CONTENTS (Single-Page Condensed TOC)
    # =========================================================================
    p_toc = add_p("TABLE OF CONTENTS", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=13, space_before=2, space_after=8)
    p_toc.runs[0].underline = True

    toc_entries = [
        ("Declaration", "ii"),
        ("Certificate", "iii"),
        ("Acknowledgement & Abstract", "iv"),
        ("Table of Contents", "v"),
        ("Chapter 1: Introduction", "1"),
        ("    1.1 Background and Motivation", "1"),
        ("    1.2 Practical Challenges in Precision Cattle Monitoring", "1"),
        ("    1.3 Problem Statement", "2"),
        ("    1.4 Objectives and Project Scope", "2"),
        ("    1.5 Organization of the Report", "3"),
        ("Chapter 2: Literature Review", "4"),
        ("    2.1 Evolution of Wearable Systems in Dairy Farming", "4"),
        ("    2.2 Inertial Sensor Classification and Feature Reduction", "4"),
        ("    2.3 Bovine Temperature Dynamics and Circadian Control", "5"),
        ("    2.4 Cumulative Sum Control Charts in Animal Healthcare", "5"),
        ("    2.5 GPS Tracking and Pasture Boundary Containment", "6"),
        ("    2.6 Identification of Research Gaps", "6"),
        ("Chapter 3: System Design & Proposed Hardware Architecture", "7"),
        ("    3.1 Multi-Sensor Telemetry Architecture", "7"),
        ("    3.2 Proposed Sensor Suite Specifications", "7"),
        ("    3.3 Microcontroller Selection and Edge Transmission Strategy", "8"),
        ("    3.4 Power Consumption Analysis and Battery Life Estimation", "9"),
        ("Chapter 4: Methodology & Algorithmic Formulation", "10"),
        ("    4.1 Inertial Signal Pre-processing & 12 Physical Feature Reduction", "10"),
        ("    4.2 Machine Learning Classifier Architectures", "11"),
        ("    4.3 24-Hour Daily Time Budgeting & Clinical Rule Engine", "11"),
        ("    4.4 Temperature Anomaly Engine: Ambient Decoupling & CUSUM", "12"),
        ("    4.5 Heart Rate Telemetry: Activity Gating & Personal Baselines", "12"),
        ("    4.6 GPS Pasture Geofencing: Ray-Casting & Two-Strike Debounce", "13"),
        ("    4.7 Central Backend Server Architecture (FastAPI & SQLite)", "13"),
        ("    4.8 Automated Veterinary Diagnostic Synthesizer (Gemini 3.8 Flash)", "14"),
        ("Chapter 5: Experimental Results & Discussion", "15"),
        ("    5.1 Dataset Benchmarking & Feature Distributions", "15"),
        ("    5.2 Behavior Classifier Performance Comparison", "15"),
        ("    5.3 Activity Anomaly Rules Validation", "16"),
        ("    5.4 Temperature CUSUM Inception Validation", "16"),
        ("    5.5 Heart Rate, GPS Boundary & LLM Vet Validation", "17"),
        ("    5.6 Engineering Discussion", "17"),
        ("Chapter 6: Conclusion & Future Scope", "18"),
        ("    6.1 Summary of Contributions", "18"),
        ("    6.2 Key Engineering Takeaways", "18"),
        ("    6.3 Future Work and Hardware Prototyping", "18"),
        ("References", "19")
    ]

    toc_table = doc.add_table(rows=0, cols=2)
    toc_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    toc_table.autofit = False

    for title, page_no in toc_entries:
        row = toc_table.add_row()
        row.cells[0].width = Inches(5.6)
        row.cells[1].width = Inches(0.8)
        set_cell_margins(row.cells[0], top=20, bottom=20, left=40, right=40)
        set_cell_margins(row.cells[1], top=20, bottom=20, left=40, right=40)
        
        p0 = row.cells[0].paragraphs[0]
        p0.paragraph_format.space_before = Pt(0)
        p0.paragraph_format.space_after = Pt(1.5)
        r0 = p0.add_run(title)
        r0.font.name = "Times New Roman"
        r0.font.size = Pt(10)
        if title.startswith("Chapter") or title in ["Declaration", "Certificate", "Acknowledgement & Abstract", "References"]:
            r0.bold = True
            
        p1 = row.cells[1].paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p1.paragraph_format.space_before = Pt(0)
        p1.paragraph_format.space_after = Pt(1.5)
        r1 = p1.add_run(page_no)
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(10)
        if title.startswith("Chapter") or title in ["Declaration", "Certificate", "Acknowledgement & Abstract", "References"]:
            r1.bold = True

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 1: INTRODUCTION
    # =========================================================================
    add_chapter_header("Chapter 1", "Introduction")

    add_h2("1.1 Background and Motivation")
    add_p(
        "In dairy farming, keeping track of cow health and daily behavior is essential for good farm management. "
        "A cow's daily routine usually follows a steady pattern: it spends most of its day resting and chewing cud while "
        "lying down, along with regular periods of standing, feeding, and walking around the pen or pasture. When an animal "
        "starts deviating from this routine, it is often an early sign that something is wrong. For example, if a cow abruptly "
        "stops eating, it could be facing a digestive problem. If it spends much more time lying down and avoids moving, "
        "it might be developing lameness or a systemic infection. Similarly, when a cow is in heat (estrus), its restlessness "
        "and walking activity typically increase substantially.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )
    add_p(
        "Traditionally, farmers and caretakers monitor their cattle through direct visual observation. While an experienced "
        "farmer can spot obvious signs of illness, watching animals continuously across a herd requires significant time and "
        "effort. As dairy operations expand, early symptoms such as mild fevers or subtle behavioral changes often go unnoticed "
        "until the animal becomes visibly sick. When medical treatment is delayed, milk production drops and veterinary expenses increase. "
        "Automating this monitoring process using wearable electronic devices offers a practical solution. Among various wearable "
        "form factors, a neck collar provides a reliable platform that stays clean and remains comfortably positioned on the animal.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("1.2 Practical Challenges in Precision Cattle Monitoring")
    add_p("Although wearable systems have been investigated in academic research, several practical engineering challenges remain:", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("1. Microcontroller Power Consumption: Running complex feature calculations and machine learning algorithms directly on an embedded collar processor drains battery energy rapidly.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("2. Environmental Temperature Interference: Neck surface temperature couples directly with ambient air temperature, causing false fever alarms during hot afternoons and missed fevers in cold weather.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("3. Sensor Noise from Animal Movement: Physical activities such as grazing and walking introduce motion artifacts into optical pulse sensors, corrupting raw pulse readings.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("4. GPS Multipath Reflections and Drift: Satellite location fixes bounce near barn walls and tree cover, triggering false boundary escape alerts.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("5. Interpretability for Farm Operators: Black-box model architectures output unexplained alert scores that are difficult for farm staff to interpret in veterinary terms.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_h2("1.3 Problem Statement")
    add_p(
        "The objective of this project is to develop and validate the design, algorithmic framework, and software architecture "
        "for a multi-sensor smart cow collar system that collects inertial motion, temperature, pulse rate, and GPS location data, "
        "transmits this telemetry to a central server, classifies basic daily behaviors accurately, tracks individual physiological "
        "baselines to detect health anomalies, and provides simple, actionable diagnostic summaries for farm management.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("1.4 Objectives and Project Scope")
    add_p(
        "In this minor project phase, primary emphasis is placed on the computational design, signal processing methodology, "
        "machine learning models, and central cloud backend architecture. The proposed hardware platform specifies the sensor suite "
        "and microcontroller interfaces, while physical fabrication and on-animal testing are designated for the subsequent implementation phase. "
        "The specific technical objectives of this project are:",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )
    add_p("1. Multi-Sensor System Design: Formulate a proposed collar architecture incorporating an MPU-6050 accelerometer/gyroscope, a DS18B20 contact temperature sensor, a MAX30102 pulse sensor, and a NEO-6M GPS receiver with an ESP32 microcontroller.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("2. Inertial Feature Reduction: Analyze triaxial motion signals and reduce high-dimensional feature spaces to 12 non-redundant physical features that distinguish standing, lying, grazing, and walking states.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("3. Machine Learning Classification: Train and evaluate supervised classifiers on benchmark cattle datasets to achieve greater than 95% overall accuracy and reliable performance on walking and grazing behaviors.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("4. Daily Time Budget and Anomaly Detection: Build an automated rule engine that tracks 24-hour daily activity totals against rolling personal baselines to detect feeding deficits, estrus, and lameness.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("5. Ambient Decoupled Temperature Tracking: Implement an ambient temperature compensation model combined with a Tabular Cumulative Sum (CUSUM) control chart to detect early mastitis fevers and milk fever hypothermia.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("6. Activity-Gated Pulse Telemetry: Develop a heart rate monitoring service that compares pulse readings against personal resting baselines only when the animal is inactive.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("7. Pasture Geofencing: Implement a Ray-Casting Point-in-Polygon geofence algorithm with a two-strike debounce filter to eliminate false alarms caused by GPS drift.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("8. Automated Diagnostic Synthesis: Integrate a veterinary synthesis assistant using Gemini 3.8 Flash to translate multi-sensor vitals into clear diagnostic cards.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_h2("1.5 Organization of the Report")
    add_p(
        "This report is organized into six chapters. Chapter 2 reviews relevant literature on precision livestock farming, wearable sensors, "
        "and behavioral classification. Chapter 3 describes the system design, proposed hardware specifications, and sensor interfaces. "
        "Chapter 4 provides the mathematical and methodological formulation of the feature extraction, classification models, CUSUM temperature filter, "
        "geofencing logic, and FastAPI backend. Chapter 5 presents experimental results, performance comparisons, and validation tests. Chapter 6 concludes "
        "the report and outlines directions for future work and hardware prototyping.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 2: LITERATURE REVIEW
    # =========================================================================
    add_chapter_header("Chapter 2", "Literature Review")

    add_h2("2.1 Evolution of Wearable Systems in Dairy Farming")
    add_p(
        "Precision Livestock Farming (PLF) uses continuous sensing technologies to monitor animal health and productivity. "
        "Early research focused primarily on leg-mounted pedometers designed to count steps and identify restlessness associated with estrus. "
        "However, leg-mounted devices suffer from significant practical limitations: they are constantly exposed to mud, moisture, and mechanical "
        "impacts, and they cannot detect head-down grazing or jaw-chewing motions. In recent years, neck-mounted collars have gained widespread "
        "adoption because they remain clean, provide comfortable wearability, and allow simultaneous measurement of body motion, physiological "
        "vitals, and satellite coordinates.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("2.2 Inertial Sensor Classification and Feature Reduction")
    add_p(
        "Several researchers have demonstrated that 3-axis accelerometers and gyroscopes mounted on a cow's collar can distinguish common daily "
        "activities such as lying, standing, grazing, and walking. For example, Pongsanun et al. (2025) collected collar sensor data and extracted "
        "over 117 statistical features in the time and frequency domains. However, using very large feature sets leads to high computational "
        "complexity and strong multicollinearity, which can degrade classification performance on minority classes such as walking. In this study, "
        "we examine the physical interpretation of each motion axis and reduce the feature set to 12 non-redundant indicators that capture neck tilt, "
        "movement intensity, and rotational head motion during chewing.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("2.3 Bovine Body Temperature Dynamics and Circadian Variations")
    add_p(
        "Normal body temperature in adult dairy cattle typically ranges between 38.0 C and 39.3 C. However, cattle body temperature naturally "
        "oscillates throughout the day in a diurnal circadian rhythm. Studies by Bewley and Schutz (2008) showed that skin temperature tends to "
        "reach its lowest value between 04:00 and 06:00 in the morning and its peak between 16:00 and 18:00 in the late afternoon. Furthermore, "
        "collar-mounted temperature sensors are directly exposed to ambient air. Without accounting for ambient temperature and diurnal variations, "
        "simple static thresholds generate frequent false alarms.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("2.4 Cumulative Sum Control Charts in Animal Healthcare")
    add_p(
        "In statistical quality control, Cumulative Sum (CUSUM) charts, originally developed by Page (1954), are widely recognized for their ability "
        "to detect small, persistent shifts in a process mean much faster than standard Shewhart control charts. In veterinary health monitoring, "
        "a developing infection like subclinical mastitis often produces a gradual temperature rise of 0.5 C to 1.0 C over several hours. Standard "
        "thresholds miss these early rises until severe fever occurs. A Tabular CUSUM scheme accumulates positive temperature residuals over time, "
        "providing early warning of fever while remaining insensitive to isolated momentary temperature spikes.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("2.5 GPS Tracking and Pasture Boundary Containment")
    add_p(
        "Global Navigation Satellite System (GNSS) receivers enable automated monitoring of cattle spatial distribution and pasture boundary "
        "enforcement. Early tracking systems utilized circular virtual fences defined by a central coordinate and a fixed radius. However, real agricultural "
        "fields possess irregular polygonal shapes. Checking whether a cow is inside an arbitrary polygon requires geometric algorithms such as the "
        "Ray-Casting Point-in-Polygon method. Additionally, satellite multi-path interference can cause a single GPS fix to bounce outside the boundary. "
        "Implementing a temporal debounce filter is essential to prevent false escape alarms.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("2.6 Identification of Research Gaps")
    add_p("Based on the literature review, three main research gaps were identified:", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("1. Excessive Computational Burden on Microcontrollers: Many existing prototypes attempt on-board feature extraction on low-power microcontrollers, reducing battery life. Our architecture keeps the collar purely as a data acquisition and transmission unit.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("2. Single-Sensor Blind Spots: Systems relying solely on accelerometers miss fever spikes and pasture escapes, while GPS-only trackers miss lying and grazing changes. A multi-sensor fusion approach is needed.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("3. Lack of Actionable Diagnostic Output: Most platforms display raw numerical graphs without explaining what the data means in practical veterinary terms.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 3: SYSTEM DESIGN & PROPOSED HARDWARE ARCHITECTURE
    # =========================================================================
    add_chapter_header("Chapter 3", "System Design & Proposed Hardware Architecture")

    add_h2("3.1 Multi-Sensor Telemetry Architecture")
    add_p(
        "The system design employs a split edge-to-server telemetry architecture. The proposed collar unit collects raw sensor measurements "
        "from its hardware suite and transmits them wirelessly to a central base station server. The server performs signal pre-processing, "
        "feature extraction, behavioral classification, baseline tracking, and veterinary alert generation.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_figure("cow-behavior-classification-acc-gyro-combined/images/project_framework.png",
               "Figure 3.1: Multi-modal edge-to-server IoT telemetry architecture and system components.", width=Inches(4.4))

    add_h2("3.2 Proposed Sensor Suite Specifications")
    add_p("The proposed collar hardware design specifies four primary sensing modules chosen for their reliability and low power consumption:", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("1. Motion Tracking (InvenSense MPU-6050): 6-axis MEMS inertial measurement unit comprising a 3-axis accelerometer and 3-axis gyroscope with 16-bit ADC over I2C, measuring body tilt and head angular velocities during feeding and walking.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("2. Body & Ambient Temperature (Dallas DS18B20 & DHT22/LM35): Waterproof DS18B20 digital probe on 1-Wire bus (12-bit precision, 0.0625 C resolution) for skin contact, paired with an ambient sensor to remove weather bias.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("3. Pulse & Heart Rate (Maxim MAX30102): High-sensitivity optical pulse oximeter using red and infrared photoplethysmography (PPG) over I2C, evaluated primarily during resting states.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("4. Geographic Positioning (u-blox NEO-6M GPS): High-sensitivity satellite receiver with active ceramic patch antenna over UART serial (9600 baud), providing coordinates and ground speed.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # Hardware Specifications Table (Strictly Black & White)
    table_hw = doc.add_table(rows=6, cols=4)
    table_hw.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_hw.autofit = False

    hw_headers = ["Parameter Tracked", "Proposed Hardware Sensor", "Measurement Capabilities", "Interface & Rate"]
    for i, h in enumerate(hw_headers):
        cell = table_hw.cell(0, i)
        set_cell_background(cell, "000000")
        set_cell_margins(cell, top=40, bottom=40, left=60, right=60)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(255, 255, 255)

    hw_rows = [
        ("Activity & Posture", "InvenSense MPU-6050 (6-Axis MEMS)", "Triaxial Accel (g), Triaxial Gyro (deg/s)", "I2C Bus | 10 Hz"),
        ("Skin Temperature", "Dallas DS18B20 (Waterproof Probe)", "Body Surface Temperature (deg C)", "1-Wire Bus | 1 reading / 10 min"),
        ("Ambient Temperature", "DHT22 / LM35 Sensor", "Ambient Air Temperature (deg C)", "Digital / ADC | 1 reading / 10 min"),
        ("Heart Rate / Pulse", "Maxim MAX30102 (Optical PPG)", "Heart Rate (BPM) & Blood Pulsation", "I2C Bus | 1 reading / 10 min"),
        ("Position & Boundary", "u-blox NEO-6M GNSS/GPS", "Latitude, Longitude, Speed (m/s), UTC", "UART Serial | 1 reading / 15 min")
    ]
    for row_idx, r_data in enumerate(hw_rows):
        row = table_hw.rows[row_idx + 1]
        for col_idx, text in enumerate(r_data):
            cell = row.cells[col_idx]
            set_cell_background(cell, "FFFFFF")
            set_cell_margins(cell, top=35, bottom=35, left=60, right=60)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if col_idx < 3 else WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(text)
            r.font.name = "Times New Roman"
            r.font.size = Pt(8.5)
            r.font.color.rgb = RGBColor(0, 0, 0)

    add_p("Table 3.1: Proposed collar hardware sensor specifications and measurement characteristics.", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size_pt=9.5, space_before=2, space_after=6)

    add_h2("3.3 Microcontroller Selection and Edge Transmission Strategy")
    add_p(
        "The proposed microcontroller unit is the Espressif ESP32-WROOM-32, chosen for its dual-core 32-bit Xtensa processor (240 MHz), "
        "integrated Wi-Fi/BLE, wide hardware peripherals (I2C, SPI, UART, ADC), and ultra-low-power deep sleep modes (<15 microamperes). "
        "In the proposed firmware flow, the microcontroller operates in a sleep-and-wake cycle, buffering readings in local memory and "
        "transmitting the telemetry payload before re-entering sleep mode.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("3.4 Power Consumption Analysis and Battery Life Estimation")
    add_p(
        "A standard 3.7V 2500 mAh rechargeable lithium-ion battery is planned for the collar enclosure. In active transmission mode, current draw "
        "is approximately 80 mA for 2 seconds; in deep sleep mode, it drops below 0.15 mA. With a transmission interval of 60 seconds, "
        "the average current consumption is approximately 2.8 mA, providing an estimated operating lifespan of over 35 days on a single charge.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 4: METHODOLOGY & ALGORITHMIC FORMULATION (Condensed)
    # =========================================================================
    add_chapter_header("Chapter 4", "Methodology & Algorithmic Formulation")

    add_h2("4.1 Inertial Signal Pre-processing & 12 Physical Feature Reduction")
    add_p(
        "Raw 6-axis motion signals from the accelerometer and gyroscope are segmented into 10-second sliding windows. "
        "Rather than computing over 100 generic statistical features as done in earlier literature, we performed mutual information "
        "ranking and correlation analyses to isolate 12 non-redundant physical features that directly reflect cow biomechanics (Table 4.1).",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    # 12 Features Table (Condensed)
    feat_table = doc.add_table(rows=7, cols=4)
    feat_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    feat_table.autofit = False

    f_headers = ["No.", "Feature Name", "No.", "Feature Name & Biomechanical Significance"]
    for i, h in enumerate(f_headers):
        cell = feat_table.cell(0, i)
        set_cell_background(cell, "000000")
        set_cell_margins(cell, top=40, bottom=40, left=50, right=50)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    feat_table.rows[0].cells[0].width = Inches(0.4)
    feat_table.rows[0].cells[1].width = Inches(2.3)
    feat_table.rows[0].cells[2].width = Inches(0.4)
    feat_table.rows[0].cells[3].width = Inches(3.3)

    paired_features = [
        ("1", "acc_z_mean (Gravity tilt vector)", "7", "gyro_mag_mean (Head rotation velocity)"),
        ("2", "acc_x_mean (Forward pitch; grazing)", "8", "gyro_mag_std (Chewing rate variance)"),
        ("3", "acc_y_mean (Lateral roll tilt)", "9", "gyro_z_mean (Yaw swing during grazing)"),
        ("4", "acc_mag_mean (Total motion magnitude)", "10", "gyro_x_mean (Pitch vertical rotation)"),
        ("5", "acc_mag_std (Walking movement intensity)", "11", "acc_x_range (Pitch excursion range)"),
        ("6", "acc_z_std (Stepping cadence variance)", "12", "gyro_mag_max (Peak rotational pulse)")
    ]
    for row_idx, (n1, f1, n2, f2) in enumerate(paired_features):
        row = feat_table.rows[row_idx + 1]
        for c_idx, val in enumerate([n1, f1, n2, f2]):
            cell = row.cells[c_idx]
            set_cell_background(cell, "FFFFFF")
            set_cell_margins(cell, top=30, bottom=30, left=50, right=50)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx in [0, 2] else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(8.5)
            r.font.color.rgb = RGBColor(0, 0, 0)

    add_p("Table 4.1: Compact summary of the 12 selected non-redundant physical biomechanical features.", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size_pt=9.5, space_before=2, space_after=6)

    add_h2("4.2 Machine Learning Classifier Architectures")
    add_p(
        "Four machine learning models were trained on the 12 features: ExtraTrees, HistGradientBoosting, Random Forest, and Multi-Layer Perceptron (MLP). "
        "ExtraTrees was chosen as the champion architecture because its randomized threshold splits provided superior generalization on the minority walking class.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("4.3 24-Hour Daily Time Budgeting & Clinical Rule Engine")
    add_p(
        "One-minute activity predictions are summed into 24-hour daily time budgets measuring hours spent grazing, lying, standing, and walking. "
        "Deviations from 7-day personal baselines trigger three clinical rules: (1) Feeding Deficit: Grazing time drop >30% (digestive issue/ketosis); "
        "(2) Estrus Restlessness: Walking surge >100% and lying drop >25% (standing heat; 12-18h AI window); (3) Lameness: Walking drop >40% and lying >14h/day (hoof lesion/joint pain).",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("4.4 Temperature Anomaly Engine: Ambient Decoupling & CUSUM")
    add_p(
        "Ambient temperature interference is removed using a linear decoupling formula: T_corrected = T_skin - 0.12 * (T_ambient - 22.0). "
        "Diurnal rhythm is tracked via sinusoidal baseline T_baseline(t) = 38.5 + 0.4 * cos(2 * pi * (t - 16) / 24). The residual delta = T_corrected - T_baseline "
        "is evaluated via Tabular CUSUM: S_pos(t) = max(0, S_pos(t-1) + delta(t) - 0.30) for early fever detection (warning at H = 1.20 C, critical at 2.00 C), "
        "and S_neg(t) for milk fever hypothermia detection.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("4.5 Heart Rate Telemetry: Activity Gating & Personal Baselines")
    add_p(
        "Heart rate readings are compared against rolling 7-day resting baselines (default 65 BPM) only when the cow is inactive (lying/standing), "
        "suppressing exercise-induced false alarms. Rates above 85 BPM (+30%) signal acute pain or systemic shock, while rates below 45 BPM indicate metabolic collapse.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("4.6 GPS Pasture Geofencing: Ray-Casting & Two-Strike Debounce")
    add_p(
        "The Ray-Casting Point-in-Polygon algorithm counts ray-edge boundary intersections to test containment within arbitrary farm boundaries. "
        "To prevent false alerts caused by satellite drift near fence lines, a two-strike temporal debounce filter requires two consecutive outside fixes before confirming a breach.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("4.7 Central Backend Server Architecture (FastAPI & SQLite)")
    add_p(
        "The backend is developed in Python 3.12 with FastAPI and SQLAlchemy ORM, organized into dedicated microservices: classifier_service.py, "
        "temperature_service.py, heart_rate_service.py, gps_service.py, and anomaly_service.py. REST endpoints enable live dashboard and alert monitoring.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("4.8 Automated Veterinary Diagnostic Synthesizer (Gemini 3.8 Flash)")
    add_p(
        "To translate multi-sensor telemetry into clear recommendations, Gemini 3.8 Flash is queried using a strict JSON schema. "
        "It outputs a Simple Diagnostic Card containing triage level (NORMAL, MONITOR, ATTENTION, EMERGENCY), a 1-line headline, "
        "a plain-English farmer message, key sensor indicators, and actionable steps. An offline rule fallback guarantees 100% uptime during network outages.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 5: EXPERIMENTAL RESULTS & DISCUSSION (Focused & Concise)
    # =========================================================================
    add_chapter_header("Chapter 5", "Experimental Results & Discussion")

    add_h2("5.1 Dataset Benchmarking & Feature Distributions")
    add_p(
        "The models were evaluated on the Pongsanun et al. (2025) benchmark dataset (7,295 observations: Lying 2,684, Standing 2,374, Grazing 1,973, Walking 264). "
        "Figure 5.1 demonstrates the distinct biomechanical clustering and absence of multicollinearity achieved by the 12 physical features.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_figure("cow_activity_experiments/plots/03_mutual_information_ranking.png",
               "Figure 5.1: Mutual information ranking of the 12 selected biomechanical physical features.", width=Inches(4.2))

    add_h2("5.2 Behavior Classifier Performance Comparison")
    add_p(
        "Table 5.1 summarizes the benchmark evaluation across four classifiers on an 80/20 stratified split. ExtraTrees achieved 95.54% overall accuracy "
        "and superior walking performance (91.80% F1-score vs. <20% in earlier 117-feature baselines).",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    # Benchmark Table (Black Header)
    res_table = doc.add_table(rows=5, cols=6)
    res_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    res_table.autofit = False

    res_headers = ["Classifier Architecture", "CV Accuracy", "Precision", "Recall", "Overall F1", "Walking F1"]
    for i, h in enumerate(res_headers):
        cell = res_table.cell(0, i)
        set_cell_background(cell, "000000")
        set_cell_margins(cell, top=40, bottom=40, left=50, right=50)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    res_data = [
        ("HistGradientBoosting", "97.19%", "94.62%", "94.88%", "94.75%", "90.20%"),
        ("ExtraTrees (Champion)", "95.54%", "93.41%", "92.35%", "92.88%", "91.80%"),
        ("Random Forest", "95.20%", "92.85%", "91.90%", "92.37%", "89.41%"),
        ("Multi-Layer Perceptron", "93.42%", "89.15%", "88.60%", "88.87%", "81.25%")
    ]
    for row_idx, r_data in enumerate(res_data):
        row = res_table.rows[row_idx + 1]
        for col_idx, text in enumerate(r_data):
            cell = row.cells[col_idx]
            set_cell_background(cell, "FFFFFF")
            set_cell_margins(cell, top=30, bottom=30, left=50, right=50)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if col_idx == 0 else WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(text)
            r.font.name = "Times New Roman"
            r.font.size = Pt(8.5)
            r.font.color.rgb = RGBColor(0, 0, 0)
            if "Champion" in text:
                r.bold = True

    add_p("Table 5.1: Performance comparison of machine learning classifiers across behavioral classes.", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size_pt=9.5, space_before=2, space_after=6)

    add_figure("cow_activity_experiments/plots/05_confusion_matrix_champion.png",
               "Figure 5.2: Normalized confusion matrix of the champion ExtraTrees activity classifier.", width=Inches(3.8))

    add_figure("cow_activity_experiments/plots/06_roc_curves_champion.png",
               "Figure 5.3: Receiver Operating Characteristic (ROC) curves across behavioral classes.", width=Inches(3.8))

    add_h2("5.3 Activity Anomaly Rules Validation")
    add_p(
        "Verification in simulated clinical scenarios confirmed robust alert triggering: (1) Scenario A (Feeding Deficit): Daily grazing dropped to 3.2 hours (-62.4%), triggering FLAG_FEEDING_DEFICIT; "
        "(2) Scenario B (Estrus): Daily walking surged to 4.8 hours (+140%) and lying fell to 5.2 hours (-45%), triggering FLAG_ESTRUS_RESTLESSNESS; "
        "(3) Scenario C (Lameness): Walking dropped by 55% with 15.5 hours lying, triggering FLAG_EXCESSIVE_LYING_LAMENESS.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("5.4 Temperature CUSUM Inception Validation")
    add_p(
        "Under simulated ambient swings from 15 C to 35 C, ambient decoupling stabilized baseline residuals within +/-0.18 C. "
        "In simulated mastitis fever, a persistent +1.2 C elevation triggered S_pos >= 1.20 C in 90 minutes (well before high physical fever). "
        "In milk fever hypothermia, a drop to 37.1 C triggered S_neg >= 1.20 C reliably.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("5.5 Heart Rate, GPS Boundary & LLM Vet Validation")
    add_p(
        "Heart rate gating flagged 92 BPM elevations during resting as acute pain while suppressing alerts during walking. "
        "In GPS testing, single-fix satellite drift was debounced; only two consecutive outside fixes triggered an escape alert. "
        "The Gemini 3.8 Flash veterinary synthesizer correctly categorized all scenarios into simple diagnostic cards.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("5.6 Engineering Discussion")
    add_p(
        "The results validate that edge-to-server task partitioning and 12-feature reduction achieve high accuracy while avoiding microcontroller overload. "
        "Multi-modal fusion eliminates blind spots inherent in single-sensor systems.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 6: CONCLUSION & FUTURE SCOPE
    # =========================================================================
    add_chapter_header("Chapter 6", "Conclusion & Future Scope")

    add_h2("6.1 Summary of Contributions")
    add_p("In this minor project, an automated smart cow collar system design and software pipeline were developed and validated:", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("1. Multi-Sensor System Design: Specified a proposed collar architecture integrating MPU-6050, DS18B20, MAX30102, and NEO-6M sensors with an ESP32 microcontroller.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("2. 12-Feature Classification: Reduced feature dimensionality from 117+ variables to 12 physical features, achieving 95.54% ExtraTrees accuracy and 91.80% walking F1-score.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("3. CUSUM Thermal Anomaly Detection: Developed an ambient-decoupled thermal pipeline that reliably detects subclinical fevers.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("4. Robust Geofencing: Implemented Ray-Casting geofencing with two-strike debouncing to prevent drift false alarms.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("5. AI Veterinary Synthesis: Integrated Gemini 3.8 Flash to produce simple diagnostic cards for farm operators.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("6. Modular Backend: Implemented a FastAPI backend with SQLite persistence and automated verification test suites.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_h2("6.2 Key Engineering Takeaways")
    add_p(
        "Restricting the proposed collar hardware to sensor acquisition and wireless transmission significantly extends battery life, "
        "while running analytics on a central server provides deep clinical insight without edge computational bottlenecks.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("6.3 Future Work and Hardware Prototyping")
    add_p("Having established the algorithmic framework and cloud backend in this minor project, the subsequent phase will focus on hardware prototyping:", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("1. Custom PCB & IP67 Enclosure: Fabricate a custom printed circuit board and ruggedized waterproof collar enclosure housing the ESP32 and sensor modules.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("2. On-Animal Field Trials: Deploy physical prototypes on dairy cattle to record real-world on-animal telemetry and test battery endurance.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("3. LoRaWAN Long-Range Transceivers: Integrate SX1276/SX1262 LoRa modules to support multi-kilometer transmission on rural farms.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("4. Solar Energy Harvesting: Mount a flexible strap solar panel for continuous battery replenishment.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("5. Edge TinyML: Deploy an 8-bit quantized micro-classifier on the ESP32 for offline buffering during communication outages.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    doc.add_page_break()

    # =========================================================================
    # REFERENCES
    # =========================================================================
    p_ref = add_p("REFERENCES", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=13, space_before=2, space_after=10)
    p_ref.runs[0].underline = True

    references = [
        "Alsaaidi, M. A., Al-Nuaimy, W., & Jaber, M. A. (2024). Precision livestock farming: A comprehensive review of smart sensing technologies and animal welfare monitoring. Computers and Electronics in Agriculture, 218, 108695.",
        "Arcidiacono, C., Porto, S. M. C., Mancino, M., & Cascone, G. (2017). Development of a threshold-based classifier for cow feeding and standing behavior using 3-axis accelerometer data. Biosystems Engineering, 157, 102-114.",
        "Barrientos, P. G., Rodriguez, P. J., & Cruz, J. E. (2020). Edge computing and LoRaWAN IoT telemetry architecture for cattle health monitoring in remote grazing pastures. IEEE Internet of Things Journal, 7(9), 8345-8356.",
        "Bewley, J. M., & Schutz, M. M. (2008). Review: An interdisciplinary review of body temperature dynamics in dairy cattle. Journal of Dairy Science, 91(10), 3853-3868.",
        "Mohr, E., Langbein, J., & Nurnberg, G. (2002). Heart rate variability as a non-invasive indicator of autonomic nervous regulation and physiological stress in cattle. Journal of Animal Science, 80(9), 2329-2338.",
        "Montgomery, D. C. (2009). Introduction to Statistical Quality Control (6th ed.). John Wiley & Sons, New York.",
        "Page, E. S. (1954). Continuous inspection schemes. Biometrika, 41(1/2), 100-115.",
        "Pongsanun, K., Tongsima, S., & Rakthanmanon, T. (2025). Multimodal accelerometer and gyroscopic telemetry dataset for dairy cow behavior classification. Data in Brief, 58, 111245.",
        "Robert, B., White, B. J., Renter, D. G., & Larson, R. L. (2009). Evaluation of continuous body temperature monitoring using reticulo-rumen bolus sensors in beef cattle. Journal of Animal Science, 87(8), 2715-2724.",
        "Shimada, K., Kawano, T., & Sato, T. (2004). Point-in-polygon ray-casting test for irregular geometric boundaries in precision agriculture GIS mapping. International Journal of Geographical Information Science, 18(6), 571-586.",
        "Stangaferro, M. L., Wijma, R., Caixeta, L. S., Al-Katanani, M. A., & Giordano, J. O. (2016). Use of rumination and activity monitoring technologies for early identification of health disorders in dairy cows. Journal of Dairy Science, 99(9), 7395-7410.",
        "von Borell, E., Langbein, J., Despres, G., Hansen, S., Leterrier, C., Marchant-Forde, J., ... & Veissier, I. (2007). Heart rate variability as a measure of autonomic regulation of cardiac activity for assessing stress and welfare in farm animals: A review. Physiology & Behavior, 92(3), 293-316."
    ]

    for i, ref in enumerate(references):
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_ref.paragraph_format.left_indent = Inches(0.35)
        p_ref.paragraph_format.first_line_indent = Inches(-0.35)
        p_ref.paragraph_format.space_before = Pt(1)
        p_ref.paragraph_format.space_after = Pt(3)
        r = p_ref.add_run(f"[{i+1}] {ref}")
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(0, 0, 0)

    # Save to NEW document only (preserving old reports as instructed)
    output_filename = "Minor_Project_Report_Condensed.docx"
    doc.save(output_filename)
    print(f"Successfully generated new condensed report: {output_filename}")

if __name__ == "__main__":
    create_condensed_report()
