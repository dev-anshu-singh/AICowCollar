import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
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
        border.set(qn('w:space'), '24')
        border.set(qn('w:color'), '000000')  # Strictly Black
        pgBorders.append(border)
    sectPr.append(pgBorders)

def create_report():
    doc = docx.Document()
    
    # Page Setup: A4 with 1.0 inch margins
    section = doc.sections[0]
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
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
    r_f.font.size = Pt(9)
    r_f.italic = True
    r_f.font.color.rgb = RGBColor(0, 0, 0)

    # Base Styles (Strictly Black)
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(12)
    normal_style.font.color.rgb = RGBColor(0, 0, 0)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(4)

    def add_p(text="", align=WD_ALIGN_PARAGRAPH.LEFT, bold=False, italic=False, size_pt=12, space_before=0, space_after=4, line_spacing=1.15, font_name="Times New Roman"):
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
            run.font.color.rgb = RGBColor(0, 0, 0)  # Strictly Black
        return p

    def add_chapter_header(chap_num_str, chap_title_str):
        p1 = add_p(chap_num_str.upper(), align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=14, space_before=16, space_after=2)
        p1.runs[0].font.color.rgb = RGBColor(0, 0, 0)
        p2 = add_p(chap_title_str.upper(), align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=15, space_before=2, space_after=14)
        p2.runs[0].font.color.rgb = RGBColor(0, 0, 0)
        return p2

    def add_h2(text):
        p = add_p(text, align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, size_pt=13, space_before=12, space_after=4)
        p.runs[0].font.color.rgb = RGBColor(0, 0, 0)
        return p

    def add_h3(text):
        p = add_p(text, align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, italic=True, size_pt=12, space_before=8, space_after=2)
        p.runs[0].font.color.rgb = RGBColor(0, 0, 0)
        return p

    def add_figure(img_path, caption_text, width=Inches(5.5)):
        if os.path.exists(img_path):
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(8)
            p_img.paragraph_format.space_after = Pt(4)
            run = p_img.add_run()
            run.add_picture(img_path, width=width)
            
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_before = Pt(2)
            p_cap.paragraph_format.space_after = Pt(10)
            r = p_cap.add_run(caption_text)
            r.font.name = "Times New Roman"
            r.font.size = Pt(10)
            r.italic = True
            r.font.color.rgb = RGBColor(0, 0, 0)
        else:
            add_p(f"[{caption_text}]", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size_pt=10)

    # =========================================================================
    # 1. TITLE / COVER PAGE
    # =========================================================================
    add_p("A", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=13, space_before=4, space_after=2)
    add_p("Minor Project Report", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=17, space_before=2, space_after=4)
    add_p("On", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size_pt=12, space_before=1, space_after=6)
    
    title_p = add_p("Design of a Smart Cow Collar for Health and Position Monitoring System using AI&ML",
                    align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=17, space_before=4, space_after=14)
    title_p.runs[0].font.color.rgb = RGBColor(0, 0, 0)

    add_p("Submitted in partial fulfillment of the requirements for the award of the degree of",
          align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size_pt=11, space_before=4, space_after=2)
    add_p("Bachelor of Technology", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=14, space_before=2, space_after=2)
    add_p("In", align=WD_ALIGN_PARAGRAPH.CENTER, size_pt=11, space_before=1, space_after=2)
    add_p("Mechatronics and Automation Engineering", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=14, space_before=2, space_after=14)

    # Candidate and Supervisor Table
    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    for row in table.rows:
        row.cells[0].width = Inches(3.2)
        row.cells[1].width = Inches(3.2)
        set_cell_margins(row.cells[0], top=80, bottom=80, left=100, right=100)
        set_cell_margins(row.cells[1], top=80, bottom=80, left=100, right=100)
        
    cell_l = table.cell(0, 0)
    p_l = cell_l.paragraphs[0]
    p_l.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p_l.add_run("Submitted by:\n")
    r.bold = True
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor(0, 0, 0)
    r2 = p_l.add_run("Devanshu Singh (Roll No. 230103012)\nMahima Patel (Roll No. 230103025)\n\nB.Tech (MAE), VII Semester")
    r2.font.size = Pt(10.5)
    r2.font.color.rgb = RGBColor(0, 0, 0)

    cell_r = table.cell(0, 1)
    p_r = cell_r.paragraphs[0]
    p_r.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p_r.add_run("Under the Supervision of:\n")
    r.bold = True
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor(0, 0, 0)
    r2 = p_r.add_run("Dr. Sunil Kumar\nAssistant Professor\nDepartment of Mechatronics &\nAutomation Engineering\nIIIT Bhagalpur")
    r2.font.size = Pt(10.5)
    r2.font.color.rgb = RGBColor(0, 0, 0)

    add_p("", space_before=8, space_after=4)

    # Official IIIT Bhagalpur Header Banner
    if os.path.exists("IIITBH-WEBPAGE-HEADER.png"):
        p_hdr = doc.add_paragraph()
        p_hdr.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_hdr.paragraph_format.space_before = Pt(6)
        p_hdr.paragraph_format.space_after = Pt(6)
        p_hdr.add_run().add_picture("IIITBH-WEBPAGE-HEADER.png", width=Inches(5.8))
    else:
        add_p("Indian Institute of Information Technology, Bhagalpur", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=13)

    p_dt = add_p("November 2026", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=11.5, space_before=4, space_after=2)
    p_dt.runs[0].font.color.rgb = RGBColor(0, 0, 0)

    doc.add_page_break()

    # =========================================================================
    # 2. DECLARATION
    # =========================================================================
    if os.path.exists("IIITBH-WEBPAGE-HEADER.png"):
        p_hdr = doc.add_paragraph()
        p_hdr.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_hdr.paragraph_format.space_before = Pt(0)
        p_hdr.paragraph_format.space_after = Pt(12)
        p_hdr.add_run().add_picture("IIITBH-WEBPAGE-HEADER.png", width=Inches(5.6))

    p_dec = add_p("DECLARATION", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=14, space_before=8, space_after=10)
    p_dec.runs[0].underline = True
    p_dec.runs[0].font.color.rgb = RGBColor(0, 0, 0)

    add_p(
        "We hereby declare that the Minor Project Report entitled \"Design of a Smart Cow Collar for Health and "
        "Position Monitoring System using AI&ML\" submitted to the Department of Mechatronics and Automation Engineering, "
        "Indian Institute of Information Technology, Bhagalpur, in partial fulfillment of the requirements for the award "
        "of the degree of Bachelor of Technology, is an authentic record of our own work carried out during the "
        "academic session 2026-2027.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=4, space_after=8
    )
    add_p(
        "The matter embodied in this report has not been submitted earlier for the award of any other degree or diploma to any other "
        "University or Institute. All sources of data, open-source software libraries, and published literature used in this work have been duly acknowledged.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=4, space_after=18
    )

    add_p("Date:  28 November 2026", bold=True, size_pt=11, space_after=2)
    add_p("Place: IIIT Bhagalpur, Bihar", bold=True, size_pt=11, space_after=24)

    sig_table = doc.add_table(rows=1, cols=2)
    sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sig_table.autofit = False
    sig_table.rows[0].cells[0].width = Inches(3.2)
    sig_table.rows[0].cells[1].width = Inches(3.2)
    
    p = sig_table.cell(0, 0).paragraphs[0]
    r = p.add_run("_____________________\nDevanshu Singh\nRoll No.: 230103012\nB.Tech (MAE)")
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor(0, 0, 0)
    
    p = sig_table.cell(0, 1).paragraphs[0]
    r = p.add_run("_____________________\nMahima Patel\nRoll No.: 230103025\nB.Tech (MAE)")
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor(0, 0, 0)

    doc.add_page_break()

    # =========================================================================
    # 3. CERTIFICATE
    # =========================================================================
    if os.path.exists("IIITBH-WEBPAGE-HEADER.png"):
        p_hdr = doc.add_paragraph()
        p_hdr.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_hdr.paragraph_format.space_before = Pt(0)
        p_hdr.paragraph_format.space_after = Pt(12)
        p_hdr.add_run().add_picture("IIITBH-WEBPAGE-HEADER.png", width=Inches(5.6))

    p_cert = add_p("CERTIFICATE", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=14, space_before=8, space_after=10)
    p_cert.runs[0].underline = True
    p_cert.runs[0].font.color.rgb = RGBColor(0, 0, 0)

    add_p(
        "This is to certify that the Minor Project Report entitled \"Design of a Smart Cow Collar for Health and "
        "Position Monitoring System using AI&ML\" being submitted by Devanshu Singh (Roll No. 230103012) and "
        "Mahima Patel (Roll No. 230103025) in partial fulfillment of the requirements for the award of the degree of "
        "Bachelor of Technology in Mechatronics and Automation Engineering at the Indian Institute of Information Technology, "
        "Bhagalpur, is a bonafide record of project work carried out by them under my supervision and guidance.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=4, space_after=8
    )
    add_p(
        "To the best of my knowledge, the algorithmic developments, system designs, and experimental evaluations presented "
        "in this report are original and have not been submitted to any other university or institution for the award of any degree or diploma.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=4, space_after=24
    )

    cert_table = doc.add_table(rows=1, cols=2)
    cert_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cert_table.autofit = False
    cert_table.rows[0].cells[0].width = Inches(3.2)
    cert_table.rows[0].cells[1].width = Inches(3.2)

    p = cert_table.cell(0, 0).paragraphs[0]
    r = p.add_run("___________________________\nDr. Sunil Kumar\n(Project Supervisor)\nAssistant Professor\nDept. of Mechatronics & Automation Engg.\nIIIT Bhagalpur")
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor(0, 0, 0)

    p = cert_table.cell(0, 1).paragraphs[0]
    r = p.add_run("___________________________\nHead of Department\nDept. of Mechatronics & Automation Engg.\nIIIT Bhagalpur")
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor(0, 0, 0)

    doc.add_page_break()

    # =========================================================================
    # 4. ACKNOWLEDGEMENT & ABSTRACT
    # =========================================================================
    p_ack = add_p("ACKNOWLEDGEMENT", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=14, space_before=6, space_after=8)
    p_ack.runs[0].underline = True
    p_ack.runs[0].font.color.rgb = RGBColor(0, 0, 0)

    add_p(
        "We express our sincere gratitude to our project supervisor, Dr. Sunil Kumar, Assistant Professor in the Department "
        "of Mechatronics and Automation Engineering, Indian Institute of Information Technology, Bhagalpur, for his continuous "
        "encouragement, technical guidance, and valuable advice throughout the development of this minor project.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=2, space_after=6
    )
    add_p(
        "We also thank the faculty members and technical staff of the Department of Mechatronics and Automation Engineering for "
        "providing the necessary computational facilities, laboratory guidance, and academic resources. In addition, we extend our gratitude "
        "to our peers and classmates for their helpful suggestions during the implementation and testing of the software telemetry pipeline. "
        "Finally, we express our heartfelt thanks to our parents and family members for their constant moral support and encouragement.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=2, space_after=14
    )

    p_abs = add_p("ABSTRACT", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=14, space_before=10, space_after=8)
    p_abs.runs[0].underline = True
    p_abs.runs[0].font.color.rgb = RGBColor(0, 0, 0)

    add_p(
        "In modern dairy farming, continuous monitoring of cattle health and physical behavior is essential for early diagnosis of diseases "
        "and efficient herd management. Traditional visual inspection by farm attendants is labor intensive, subjective, and often fails "
        "to detect illnesses in their early stages. In this minor project, the system design, signal processing methodology, and machine learning "
        "architecture for an automated smart cow collar platform are proposed and comprehensively evaluated.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=2, space_after=6
    )
    add_p(
        "The proposed system architecture is designed around a multi-sensor collar unit comprising an MPU-6050 6-axis inertial motion sensor "
        "(accelerometer and gyroscope), a waterproof DS18B20 contact temperature sensor, a MAX30102 optical pulse sensor, and a u-blox NEO-6M GPS receiver, "
        "coordinated by a low-power ESP32 microcontroller. In this stage of the project, primary focus is placed on the complete software pipeline, "
        "signal processing algorithms, and machine learning models evaluated on benchmark cattle telemetry data. To minimize collar power consumption, "
        "feature extraction and classification algorithms are offloaded to a central server. The triaxial motion signals are represented using 12 "
        "physically non-redundant features extracted from sliding windows. An ExtraTrees classifier achieves an overall classification accuracy of 95.54% "
        "and a walking F1-score of 91.80% in discriminating standing, lying, grazing, and walking states.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=2, space_after=6
    )
    add_p(
        "Physiological temperature monitoring incorporates an ambient thermal decoupling model and a Tabular Cumulative Sum (CUSUM) control chart "
        "to detect early fever inception while suppressing weather-induced fluctuations. Heart rate telemetry is evaluated using an activity-gated baseline "
        "comparison model. Pasture geofencing is implemented using a Ray-Casting Point-in-Polygon algorithm with a two-strike temporal debounce filter. "
        "Furthermore, an automated veterinary synthesis assistant powered by Gemini 3.8 Flash translates multi-sensor vitals into clear, standardized "
        "diagnostic cards for farm operators. The complete software architecture is integrated into a modular FastAPI backend, establishing a verified "
        "algorithmic foundation for future physical collar prototyping and field deployment.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=2, space_after=8
    )

    doc.add_page_break()

    # =========================================================================
    # 5. TABLE OF CONTENTS
    # =========================================================================
    p_toc = add_p("TABLE OF CONTENTS", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=14, space_before=6, space_after=12)
    p_toc.runs[0].underline = True
    p_toc.runs[0].font.color.rgb = RGBColor(0, 0, 0)

    toc_entries = [
        ("Declaration", "ii"),
        ("Certificate", "iii"),
        ("Acknowledgement", "iv"),
        ("Abstract", "v"),
        ("Table of Contents", "vi"),
        ("List of Figures", "viii"),
        ("List of Tables", "ix"),
        ("Chapter 1: Introduction", "1"),
        ("    1.1 Background and Motivation", "1"),
        ("    1.2 Practical Challenges in Precision Cattle Monitoring", "2"),
        ("    1.3 Problem Statement", "3"),
        ("    1.4 Objectives and Project Scope", "3"),
        ("    1.5 Organization of the Report", "4"),
        ("Chapter 2: Literature Review", "5"),
        ("    2.1 Evolution of Wearable Systems in Dairy Farming", "5"),
        ("    2.2 Inertial Sensor Classification and Feature Reduction", "6"),
        ("    2.3 Bovine Body Temperature Dynamics and Circadian Variations", "7"),
        ("    2.4 Cumulative Sum Control Charts in Animal Healthcare", "8"),
        ("    2.5 GPS Tracking and Pasture Boundary Containment", "9"),
        ("    2.6 Identification of Research Gaps", "10"),
        ("Chapter 3: System Design and Proposed Hardware Architecture", "11"),
        ("    3.1 Multi-Sensor Telemetry Architecture", "11"),
        ("    3.2 Proposed Sensor Suite Specifications", "12"),
        ("    3.3 Microcontroller Selection and Edge Transmission Strategy", "14"),
        ("    3.4 Power Consumption Analysis and Battery Life Estimation", "15"),
        ("Chapter 4: Methodology and Algorithmic Formulation", "16"),
        ("    4.1 Inertial Signal Pre-processing and 12 Physical Feature Reduction", "16"),
        ("    4.2 Machine Learning Classifier Architectures", "18"),
        ("    4.3 24-Hour Daily Time Budgeting and Clinical Rule Engine", "20"),
        ("    4.4 Temperature Anomaly Engine: Ambient Decoupling and CUSUM", "22"),
        ("    4.5 Heart Rate Telemetry: Activity Gating and Personal Baselines", "24"),
        ("    4.6 GPS Pasture Geofencing: Ray-Casting and Two-Strike Debounce", "25"),
        ("    4.7 Central Backend Server Architecture", "27"),
        ("    4.8 Automated Veterinary Diagnostic Synthesizer (Gemini 3.8 Flash)", "28"),
        ("Chapter 5: Experimental Results and Discussion", "30"),
        ("    5.1 Dataset Benchmarking and Biomechanical Feature Distributions", "30"),
        ("    5.2 Behavior Classifier Performance Comparison", "32"),
        ("    5.3 Activity Anomaly Rules Validation", "34"),
        ("    5.4 Temperature CUSUM Inception Validation", "35"),
        ("    5.5 Heart Rate and GPS Boundary Validation", "37"),
        ("    5.6 LLM Vet Clinical Assistant Evaluation", "38"),
        ("    5.7 Engineering Discussion", "39"),
        ("Chapter 6: Conclusion and Future Scope", "40"),
        ("    6.1 Summary of Contributions", "40"),
        ("    6.2 Key Engineering Takeaways", "41"),
        ("    6.3 Future Work and Hardware Prototyping", "41"),
        ("References", "43")
    ]

    toc_table = doc.add_table(rows=0, cols=2)
    toc_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    toc_table.autofit = False

    for title, page_no in toc_entries:
        row = toc_table.add_row()
        row.cells[0].width = Inches(5.6)
        row.cells[1].width = Inches(0.8)
        set_cell_margins(row.cells[0], top=30, bottom=30, left=50, right=50)
        set_cell_margins(row.cells[1], top=30, bottom=30, left=50, right=50)
        
        p0 = row.cells[0].paragraphs[0]
        p0.paragraph_format.space_before = Pt(1)
        p0.paragraph_format.space_after = Pt(2)
        r0 = p0.add_run(title)
        r0.font.name = "Times New Roman"
        r0.font.size = Pt(10.5)
        r0.font.color.rgb = RGBColor(0, 0, 0)
        if title.startswith("Chapter") or title in ["Declaration", "Certificate", "Acknowledgement", "Abstract", "References"]:
            r0.bold = True
            
        p1 = row.cells[1].paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p1.paragraph_format.space_before = Pt(1)
        p1.paragraph_format.space_after = Pt(2)
        r1 = p1.add_run(page_no)
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(10.5)
        r1.font.color.rgb = RGBColor(0, 0, 0)
        if title.startswith("Chapter") or title in ["Declaration", "Certificate", "Acknowledgement", "Abstract", "References"]:
            r1.bold = True

    doc.add_page_break()

    # =========================================================================
    # 6. LIST OF FIGURES & TABLES
    # =========================================================================
    p_lof = add_p("LIST OF FIGURES", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=14, space_before=6, space_after=8)
    p_lof.runs[0].underline = True
    p_lof.runs[0].font.color.rgb = RGBColor(0, 0, 0)

    figures_list = [
        ("Figure 3.1", "Multi-modal edge-to-server IoT telemetry architecture and system components", "11"),
        ("Figure 5.1", "Class distribution of bovine behavior samples across standing, lying, grazing, and walking", "30"),
        ("Figure 5.2", "Triaxial accelerometer and gyroscope feature distributions across behavioral states", "31"),
        ("Figure 5.3", "Mutual information ranking of the selected 12 biomechanical physical features", "31"),
        ("Figure 5.4", "Correlation matrix of the 12 selected physical features demonstrating lack of collinearity", "32"),
        ("Figure 5.5", "Normalized confusion matrix of the champion ExtraTrees activity classifier", "33"),
        ("Figure 5.6", "Receiver Operating Characteristic (ROC) curves across behavioral classes with AUC scores", "33"),
        ("Figure 5.7", "Gini impurity feature importance ranking of the 12-feature ExtraTrees classifier", "34")
    ]
    for fig_id, cap, pg in figures_list:
        add_p(f"{fig_id}: {cap}  ................................................................  {pg}", size_pt=10.5, space_before=1, space_after=3)

    add_p("", space_before=8, space_after=4)

    p_lot = add_p("LIST OF TABLES", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=14, space_before=8, space_after=8)
    p_lot.runs[0].underline = True
    p_lot.runs[0].font.color.rgb = RGBColor(0, 0, 0)

    tables_list = [
        ("Table 3.1", "Proposed collar hardware sensor specifications and measurement characteristics", "13"),
        ("Table 4.1", "Definitions and mathematical formulation of the 12 selected physical features", "17"),
        ("Table 4.2", "Clinical anomaly rules for 24-hour daily activity and time budget deviations", "21"),
        ("Table 5.1", "Performance comparison of machine learning classifiers across behavioral classes", "32")
    ]
    for tab_id, cap, pg in tables_list:
        add_p(f"{tab_id}: {cap}  ................................................................  {pg}", size_pt=10.5, space_before=1, space_after=3)

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
        "effort. As dairy operations expand and the number of animals per caretaker increases, early symptoms such as mild fevers "
        "or subtle behavioral changes often go unnoticed until the animal becomes visibly sick. When medical treatment is delayed, "
        "milk production drops significantly and veterinary treatment expenses increase.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )
    add_p(
        "Automating this monitoring process using wearable electronic devices offers a practical solution. Among various wearable "
        "form factors such as leg pedometers, ear tags, and halters, a neck collar provides several distinct advantages. It remains "
        "clean, does not get kicked or damaged easily like leg bands, and provides a stable mechanical platform for mounting motion, "
        "temperature, and location sensors.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("1.2 Practical Challenges in Precision Cattle Monitoring")
    add_p(
        "Although wearable sensor systems have been investigated in academic research, several practical engineering challenges remain:",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )
    add_p(
        "1. Microcontroller Power Consumption: Calculating complex statistical features and running machine learning models "
        "directly on an embedded microcontroller consumes significant battery energy. In a commercial farm setting, replacing "
        "or recharging collar batteries every few days is impractical.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )
    add_p(
        "2. Environmental Temperature Interference: The surface temperature of a cow's neck is influenced by ambient weather "
        "conditions such as direct sunlight or cold wind. Using a fixed threshold for body temperature leads to frequent false alarms "
        "during hot afternoons and missed fever events during cold mornings.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )
    add_p(
        "3. Sensor Noise from Animal Movement: Physical activities such as walking and grazing introduce motion artifacts into optical "
        "pulse sensors, making continuous raw pulse monitoring noisy if not properly filtered according to animal posture.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )
    add_p(
        "4. GPS Multipath Reflections and Drift: Satellite location readings often fluctuate near trees and barn walls, causing "
        "temporary false boundary breach alerts if raw GPS fixes are used directly.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )
    add_p(
        "5. Interpretability for Farm Operators: Many advanced machine learning architectures operate as black-box systems that output "
        "unexplained alert scores, which makes it difficult for farm staff to understand the underlying cause of an alert.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

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
        "and microcontroller interfaces, while physical fabrication and on-animal collar testing are designated for the subsequent "
        "implementation phase. The specific technical objectives of this project are:",
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
        "Precision Livestock Farming (PLF) involves the use of continuous sensing technologies to monitor animal health and productivity. "
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
    add_p(
        "1. Excessive Computational Burden on Microcontrollers: Many existing prototypes attempt to run complex feature extraction and "
        "classification directly on low-power collar hardware, leading to rapid battery depletion.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )
    add_p(
        "2. Single-Sensor Blind Spots: Systems relying solely on accelerometers cannot detect fevers or boundary escapes, while GPS-only trackers "
        "miss feeding and rumination changes. A multi-sensor fusion approach is needed.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )
    add_p(
        "3. Lack of Actionable Diagnostic Output: Most platforms display raw numerical graphs without explaining what the data means in practical "
        "veterinary terms.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

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
               "Figure 3.1: Multi-modal edge-to-server IoT telemetry architecture and system components.")

    add_h2("3.2 Proposed Sensor Suite Specifications")
    add_p(
        "The proposed collar hardware design specifies four primary sensing modules chosen for their reliability, low power consumption, and compact physical dimensions:",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )
    add_p(
        "1. Motion Tracking (InvenSense MPU-6050): An integrated 6-axis MEMS inertial measurement unit comprising a 3-axis accelerometer and a 3-axis gyroscope "
        "with an internal 16-bit analog-to-digital converter (ADC), communicating via standard I2C bus. The accelerometer measures gravitational tilt "
        "(distinguishing upright standing from recumbent lying), while the gyroscope captures dynamic rotational head velocities associated with chewing, grazing, and walking.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )
    add_p(
        "2. Body & Ambient Temperature (Dallas DS18B20 & DHT22 / LM35): A waterproof Dallas DS18B20 digital temperature probe is placed in direct contact "
        "with the cow's neck skin, communicating over a 1-Wire digital bus with 12-bit precision (0.0625 C resolution). A secondary sensor (DHT22 or LM35) "
        "records ambient air temperature so that environmental thermal bias can be subtracted mathematically.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )
    add_p(
        "3. Pulse & Heart Rate (Maxim Integrated MAX30102): A high-sensitivity optical pulse oximeter and heart-rate sensor module using red and infrared "
        "photoplethysmography (PPG) with an I2C interface. To avoid motion noise, pulse readings are evaluated primarily during resting states.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )
    add_p(
        "4. Geographic Positioning (u-blox NEO-6M GPS): A high-sensitivity satellite navigation receiver with an active ceramic patch antenna, communicating "
        "via UART serial interface at 9600 baud, providing latitude, longitude, altitude, ground speed, and UTC timestamp data.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    # Hardware Specifications Table (Strictly Black & White Academic Style)
    table_hw = doc.add_table(rows=6, cols=4)
    table_hw.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_hw.autofit = False

    hw_headers = ["Parameter Tracked", "Proposed Hardware Sensor", "Measurement Capabilities", "Interface & Rate"]
    for i, h in enumerate(hw_headers):
        cell = table_hw.cell(0, i)
        set_cell_background(cell, "000000")  # Black Header
        set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.5)
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
        bg = "FFFFFF"
        for col_idx, text in enumerate(r_data):
            cell = row.cells[col_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=50, bottom=50, left=80, right=80)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if col_idx < 3 else WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(text)
            r.font.name = "Times New Roman"
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(0, 0, 0)

    add_p("Table 3.1: Proposed collar hardware sensor specifications and measurement characteristics.", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size_pt=10, space_before=4, space_after=8)

    add_h2("3.3 Microcontroller Selection and Edge Transmission Strategy")
    add_p(
        "The proposed microcontroller unit is the Espressif ESP32-WROOM-32, chosen for its dual-core 32-bit Xtensa processor (240 MHz), "
        "integrated Wi-Fi (802.11 b/g/n) and Bluetooth (BLE 4.2), wide range of hardware peripherals (I2C, SPI, UART, ADC), and ultra-low-power "
        "deep sleep modes (consuming less than 15 microamperes). In the proposed firmware operational flow, the microcontroller operates in a "
        "sleep-and-wake duty cycle, buffering sampled sensor readings in local memory and transmitting the telemetry payload to the server before "
        "re-entering low-power sleep mode.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("3.4 Power Consumption Analysis and Battery Life Estimation")
    add_p(
        "A standard 3.7V 2500 mAh rechargeable lithium-ion battery is planned for the collar enclosure. In active transmission mode, the current draw is approximately 80 mA "
        "for 2 seconds. In deep sleep mode, current draw drops to under 0.15 mA. With a transmission interval of 60 seconds, the average current consumption "
        "is approximately 2.8 mA, providing an estimated operating lifespan of over 35 days on a single charge.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 4: METHODOLOGY & ALGORITHMIC FORMULATION
    # =========================================================================
    add_chapter_header("Chapter 4", "Methodology & Algorithmic Formulation")

    add_h2("4.1 Inertial Signal Pre-processing and 12 Physical Feature Reduction")
    add_p(
        "Raw 6-axis motion signals from the accelerometer and gyroscope are divided into fixed-duration sliding windows of 10 seconds. "
        "Existing studies frequently compute dozens of generic statistical metrics across each axis, creating over 100 features. "
        "In this work, we conducted feature importance and mutual information analyses to select 12 non-redundant physical features that directly "
        "correspond to bovine biomechanics.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    # 12 Features Table (Strictly Black & White)
    feat_table = doc.add_table(rows=13, cols=3)
    feat_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    feat_table.autofit = False

    headers = ["No.", "Feature Name", "Physical Significance in Cow Biomechanics"]
    for i, h in enumerate(headers):
        cell = feat_table.cell(0, i)
        set_cell_background(cell, "000000")  # Black Header
        set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(255, 255, 255)

    feat_table.rows[0].cells[0].width = Inches(0.6)
    feat_table.rows[0].cells[1].width = Inches(2.2)
    feat_table.rows[0].cells[2].width = Inches(3.6)

    features_data = [
        ("1", "acc_z_mean", "Gravitational alignment vector; distinguishes upright standing from recumbent lying."),
        ("2", "acc_x_mean", "Forward pitch tilt of neck; identifies head-down grazing posture."),
        ("3", "acc_y_mean", "Lateral roll tilt; indicates side-leaning posture while resting."),
        ("4", "acc_mag_mean", "Total acceleration magnitude; confirms overall static vs. dynamic state."),
        ("5", "acc_mag_std", "Intensity of motion; separates steady walking from stationary postures."),
        ("6", "acc_z_std", "Vertical oscillation variance; captures stepping cadence during walking."),
        ("7", "gyro_mag_mean", "Mean rotational velocity of the head; high during eating and walking."),
        ("8", "gyro_mag_std", "Variability in angular rate; indicates active jaw chewing movements."),
        ("9", "gyro_z_mean", "Horizontal yaw rotation; captures side-to-side head swinging while grazing."),
        ("10", "gyro_x_mean", "Vertical pitch angular velocity; captures up-and-down head motions."),
        ("11", "acc_x_range", "Maximum pitch excursion; reflects range of motion during feeding."),
        ("12", "gyro_mag_max", "Peak angular velocity pulse; identifies abrupt head shakes or turns.")
    ]
    for row_idx, r_data in enumerate(features_data):
        row = feat_table.rows[row_idx + 1]
        bg = "FFFFFF"
        for col_idx, text in enumerate(r_data):
            cell = row.cells[col_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=45, bottom=45, left=80, right=80)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col_idx == 0 else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(text)
            r.font.name = "Times New Roman"
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(0, 0, 0)

    add_p("Table 4.1: Definitions and mathematical formulation of the 12 selected physical features.", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size_pt=10, space_before=4, space_after=8)

    add_h2("4.2 Machine Learning Classifier Architectures")
    add_p(
        "Four supervised machine learning algorithms were trained and benchmarked on the 12-feature dataset: ExtraTrees, HistGradientBoosting, "
        "Random Forest, and Multi-Layer Perceptron (MLP). ExtraTrees was selected as the champion model because its randomized split thresholds "
        "provided superior generalization on the minority walking class without overfitting.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("4.3 24-Hour Daily Time Budgeting and Clinical Rule Engine")
    add_p(
        "Individual 1-minute behavioral classifications are aggregated into 24-hour daily time budgets measuring hours spent grazing, lying, "
        "standing, and walking. To identify potential health issues, the system compares daily totals against each cow's rolling 7-day baseline using three clinical rules:",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )
    add_p("Rule 1 (Feeding Deficit): Triggered when daily grazing time drops by more than 30% below the 7-day average. Indicates potential digestive disturbance, ketosis, or acute illness.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("Rule 2 (Estrus Restlessness): Triggered when daily walking time increases by more than 100% and lying time drops by more than 25%. Indicates standing heat; optimum artificial insemination window is 12 to 18 hours.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("Rule 3 (Lameness): Triggered when daily walking time decreases by more than 40% and lying time exceeds 14 hours per day. Indicates joint pain, foot rot, or sole ulcers.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_h2("4.4 Temperature Anomaly Engine: Ambient Decoupling and CUSUM")
    add_p(
        "To remove the confounding effect of ambient weather on skin temperature, a linear correction formula is applied:",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )
    add_p("T_corrected = T_skin - beta * (T_ambient - 22.0)", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=11.5)
    add_p(
        "where beta = 0.12 C/C is the empirical coupling coefficient and 22.0 C represents standard neutral temperature. "
        "Next, the expected circadian diurnal baseline T_baseline(t) is calculated from the time of day using a sinusoidal model:",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )
    add_p("T_baseline(t) = T_mean + A * cos(2 * pi * (t - phi) / 24)", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=11.5)
    add_p(
        "where T_mean = 38.5 C, A = 0.4 C, and phi = 16.0 (peak at 16:00). The temperature residual delta = T_corrected - T_baseline is fed "
        "into a Tabular CUSUM control chart:",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )
    add_p("S_pos(t) = max(0, S_pos(t-1) + delta(t) - k)", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=11)
    add_p("S_neg(t) = max(0, S_neg(t-1) - delta(t) - k)", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=11)
    add_p(
        "where k = 0.30 C is the slack parameter. When S_pos exceeds H = 1.20 C, a fever warning is issued; when S_pos exceeds 2.00 C, "
        "a critical fever alert is generated. S_neg detects subnormal body temperature associated with milk fever (hypocalcemia).",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("4.5 Heart Rate Telemetry: Activity Gating and Personal Baselines")
    add_p(
        "Heart rate readings are evaluated against each cow's rolling 7-day resting baseline (default 65 BPM). To avoid false alarms caused "
        "by physical exercise, readings are gated by activity state. If the cow is walking or running, tachycardia alerts are suppressed. "
        "When the animal is lying or standing calmly, a heart rate exceeding 85 BPM (or +30% above baseline) triggers an alert for acute pain or fever, "
        "while a rate below 45 BPM indicates severe lethargy or metabolic collapse.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("4.6 GPS Pasture Geofencing: Ray-Casting and Two-Strike Debounce")
    add_p(
        "Pasture boundaries are defined as ordered geometric polygons. For each incoming coordinate, the Ray-Casting Point-in-Polygon "
        "algorithm projects a horizontal ray eastward and counts boundary intersections. An odd intersection count indicates the cow is inside, "
        "while an even count indicates it is outside. To eliminate false alarms caused by temporary GPS drift near fence lines, a two-strike "
        "temporal debounce filter requires two consecutive outside fixes before triggering an escape alarm.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("4.7 Central Backend Server Architecture")
    add_p(
        "The server backend is implemented using FastAPI in Python 3.12 with SQLite/SQLAlchemy ORM for data persistence. "
        "The architecture is organized into modular services: classifier_service.py (activity prediction), temperature_service.py (CUSUM filter), "
        "heart_rate_service.py (pulse rules), gps_service.py (geofencing), and anomaly_service.py (time budgets). REST endpoints allow real-time "
        "querying and dashboard integration.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("4.8 Automated Veterinary Diagnostic Synthesizer (Gemini 3.8 Flash)")
    add_p(
        "To provide clear, practical interpretations for farm operators, an automated veterinary synthesis service was developed. "
        "The service aggregates multi-sensor telemetry (current behavior, 24-hour time budgets, CUSUM temperature scores, heart rate deviations, and GPS coordinates) "
        "and queries Gemini 3.8 Flash via a structured JSON schema. The model produces a Simple Diagnostic Card containing four clear fields:",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )
    add_p("1. Triage Level: NORMAL (green), MONITOR (yellow), ATTENTION (orange), or EMERGENCY (red).", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("2. Headline: A concise one-line summary of the animal's physical condition.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("3. Farmer Message: Two to three clear, plain-language sentences explaining the situation without confusing technical jargon.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("4. Key Indicators and Action Steps: Practical observations and concrete steps for farm staff.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p(
        "For offline farm installations without active internet connectivity, the service includes a built-in deterministic clinical rule engine "
        "that generates identical standardized diagnostic cards reliably.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 5: EXPERIMENTAL RESULTS & DISCUSSION
    # =========================================================================
    add_chapter_header("Chapter 5", "Experimental Results & Discussion")

    add_h2("5.1 Dataset Benchmarking and Biomechanical Feature Distributions")
    add_p(
        "The behavior classification models were evaluated using the dataset collected by Pongsanun et al. (2025), comprising 7,295 observation "
        "instances across four behavioral classes: Lying (2,684 samples), Standing (2,374 samples), Grazing (1,973 samples), and Walking (264 samples).",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_figure("cow_activity_experiments/plots/01_class_distribution.png",
               "Figure 5.1: Class distribution of bovine behavior samples across standing, lying, grazing, and walking.")

    add_figure("cow_activity_experiments/plots/02_biomechanical_boxplots.png",
               "Figure 5.2: Triaxial accelerometer and gyroscope feature distributions across behavioral states.")

    add_figure("cow_activity_experiments/plots/03_mutual_information_ranking.png",
               "Figure 5.3: Mutual information ranking of the selected 12 biomechanical physical features.")

    add_figure("cow_activity_experiments/plots/04_correlation_matrix_12_features.png",
               "Figure 5.4: Correlation matrix of the 12 selected physical features demonstrating lack of collinearity.")

    add_h2("5.2 Behavior Classifier Performance Comparison")
    add_p(
        "Four machine learning models were evaluated on an 80/20 stratified train/test split. Table 5.1 summarizes the experimental benchmark results.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    # Model Benchmark Table (Strictly Black & White)
    res_table = doc.add_table(rows=5, cols=6)
    res_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    res_table.autofit = False

    res_headers = ["Classifier Architecture", "CV Accuracy", "Precision", "Recall", "Overall F1", "Walking F1"]
    for i, h in enumerate(res_headers):
        cell = res_table.cell(0, i)
        set_cell_background(cell, "000000")  # Black Header
        set_cell_margins(cell, top=60, bottom=60, left=60, right=60)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    res_data = [
        ("HistGradientBoosting", "97.19%", "94.62%", "94.88%", "94.75%", "90.20%"),
        ("ExtraTrees (Champion)", "95.54%", "93.41%", "92.35%", "92.88%", "91.80%"),
        ("Random Forest", "95.20%", "92.85%", "91.90%", "92.37%", "89.41%"),
        ("Multi-Layer Perceptron", "93.42%", "89.15%", "88.60%", "88.87%", "81.25%")
    ]
    for row_idx, r_data in enumerate(res_data):
        row = res_table.rows[row_idx + 1]
        bg = "FFFFFF"
        for col_idx, text in enumerate(r_data):
            cell = row.cells[col_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=45, bottom=45, left=60, right=60)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if col_idx == 0 else WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(text)
            r.font.name = "Times New Roman"
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(0, 0, 0)
            if "Champion" in text:
                r.bold = True

    add_p("Table 5.1: Performance comparison of machine learning classifiers across behavioral classes.", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size_pt=10, space_before=4, space_after=8)

    add_figure("cow_activity_experiments/plots/05_confusion_matrix_champion.png",
               "Figure 5.5: Normalized confusion matrix of the champion ExtraTrees activity classifier.")

    add_figure("cow_activity_experiments/plots/06_roc_curves_champion.png",
               "Figure 5.6: Receiver Operating Characteristic (ROC) curves across behavioral classes with AUC scores.")

    add_figure("cow_activity_experiments/plots/07_champion_feature_importances.png",
               "Figure 5.7: Gini impurity feature importance ranking of the 12-feature ExtraTrees classifier.")

    add_h2("5.3 Activity Anomaly Rules Validation")
    add_p(
        "The 24-hour time budget rule engine was verified using three simulated clinical scenarios:",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )
    add_p("Scenario A (Acute Feeding Deficit): Daily grazing dropped from a normal 8.5 hours to 3.2 hours (-62.4%). The system correctly triggered FLAG_FEEDING_DEFICIT.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("Scenario B (Standing Heat Estrus): Daily walking surged from 2.0 to 4.8 hours (+140%) and lying decreased to 5.2 hours (-45%). The system correctly triggered FLAG_ESTRUS_RESTLESSNESS.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("Scenario C (Lameness): Walking time fell by 55% while lying time reached 15.5 hours. The system correctly triggered FLAG_EXCESSIVE_LYING_LAMENESS.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_h2("5.4 Temperature CUSUM Inception Validation")
    add_p(
        "In thermal validation experiments, raw skin temperature was subjected to ambient heat swings from 15 C to 35 C. "
        "The ambient decoupling equation successfully stabilized baseline residuals within +/-0.18 C. In simulated mastitis fever, "
        "a persistent +1.2 C rise triggered the CUSUM warning threshold S_pos >= 1.20 C after 90 minutes, providing early notification "
        "well before body temperature reached dangerous clinical levels. In milk fever testing, a drop to 37.1 C triggered S_neg >= 1.20 C.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("5.5 Heart Rate and GPS Boundary Validation")
    add_p(
        "In heart rate tests, pulse elevations to 92 BPM were flagged as acute pain during resting postures, whereas identical elevations "
        "during walking were correctly recognized as normal exercise. In GPS geofence tests, single-fix satellite drifts outside the polygon "
        "were successfully debounced; an alert was generated only when two consecutive fixes confirmed that the cow had left the pasture.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("5.6 LLM Vet Clinical Assistant Evaluation")
    add_p(
        "The Gemini 3.8 Flash veterinary synthesis engine was tested across all four diagnostic triage categories. For healthy cows, "
        "it produced NORMAL cards with routine care advice. For cows with elevated temperature and high resting pulse, it generated "
        "EMERGENCY cards diagnosing suspected toxic mastitis and recommending immediate California Mastitis Tests. For estrus cases, "
        "it identified the optimal 12-to-18 hour insemination window.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("5.7 Engineering Discussion")
    add_p(
        "The experimental results demonstrate that multi-sensor integration combined with targeted feature engineering provides robust cattle "
        "monitoring. Offloading heavy computation to the central server keeps the collar lightweight and energy efficient, while the CUSUM "
        "filter and two-strike debounce eliminate false alarms that commonly affect single-sensor prototypes.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 6: CONCLUSION & FUTURE SCOPE
    # =========================================================================
    add_chapter_header("Chapter 6", "Conclusion & Future Scope")

    add_h2("6.1 Summary of Contributions")
    add_p(
        "In this minor project, the system design, signal processing methodology, and machine learning models for an automated smart cow collar "
        "platform were formulated, implemented, and validated. The key engineering contributions of this work are:",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )
    add_p("1. Multi-Sensor Architecture Design: Developed the system specification for integrating MPU-6050 motion, DS18B20 temperature, MAX30102 pulse, and NEO-6M GPS sensors into a unified telemetry scheme with an ESP32 microcontroller.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("2. Biomechanical Feature Selection: Reduced feature dimensionality from over 117 variables to 12 physical indicators, eliminating collinearity while achieving 95.54% classification accuracy.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("3. CUSUM Thermal Anomaly Detection: Developed an ambient-decoupled thermal pipeline that detects subclinical fevers without false alarms.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("4. Robust Geofencing: Implemented Ray-Casting Point-in-Polygon geofencing with a two-strike debounce filter to eliminate GPS drift false alarms.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("5. AI Veterinary Synthesis: Integrated Gemini 3.8 Flash to translate multi-sensor vitals into simple, actionable diagnostic cards for farm operators.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("6. Modular Backend: Built a complete FastAPI backend with SQLite persistence and automated test suites verifying all services.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_h2("6.2 Key Engineering Takeaways")
    add_p(
        "The project demonstrated that edge-to-server task partitioning is an effective strategy for wearable livestock telemetry. "
        "By restricting the proposed collar hardware to data collection and wireless transmission, battery life is substantially extended. Furthermore, "
        "combining physiological vitals with behavioral time budgets yields far more reliable health warnings than monitoring motion alone.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )

    add_h2("6.3 Future Work and Hardware Prototyping")
    add_p(
        "Having established the software models, algorithmic pipelines, and cloud database backend in this minor project, the next phase "
        "will focus on hardware fabrication, physical packaging, and field experimentation:",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY
    )
    add_p("1. Physical PCB Fabrication and Collar Packaging: Design an integrated custom printed circuit board (PCB) with an IP67 waterproof enclosure to house the ESP32, MPU-6050, DS18B20, MAX30102, and NEO-6M modules on a heavy-duty nylon collar strap.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("2. On-Animal Live Telemetry Trials: Deploy the physical prototype on dairy cattle to record real-world on-animal sensor signals and validate battery endurance under live pasture conditions.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("3. LoRaWAN Long-Range Transceivers: Integrate SX1276/SX1262 LoRa modules to support multi-kilometer telemetry transmission across large rural farms without relying on local Wi-Fi or cellular networks.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("4. Solar Energy Harvesting: Incorporate a flexible solar panel on the upper strap of the collar to continuously recharge the battery, achieving indefinite operational lifespan.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("5. Edge TinyML Deployment: Deploy an 8-bit quantized micro-classifier on the ESP32 for basic motion pre-filtering during communication outages.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    doc.add_page_break()

    # =========================================================================
    # REFERENCES
    # =========================================================================
    p_ref = add_p("REFERENCES", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=14, space_before=6, space_after=12)
    p_ref.runs[0].underline = True
    p_ref.runs[0].font.color.rgb = RGBColor(0, 0, 0)

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
        p_ref.paragraph_format.left_indent = Inches(0.4)
        p_ref.paragraph_format.first_line_indent = Inches(-0.4)
        p_ref.paragraph_format.space_before = Pt(2)
        p_ref.paragraph_format.space_after = Pt(4)
        r = p_ref.add_run(f"[{i+1}] {ref}")
        r.font.name = "Times New Roman"
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(0, 0, 0)

    # Save to both target locations
    doc.save("Minor_Project_Report_Final.docx")
    doc.save("Minor Project Report.docx")
    doc.save("Minor_Project_Report_Final_Updated.docx")
    print("Successfully generated all reports with official title, strictly black typography, and proposed hardware specifications.")

if __name__ == "__main__":
    create_report()
