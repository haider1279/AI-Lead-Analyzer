import io
from datetime import datetime
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header line (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "Euroshub — Commercial Proposal")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)

        # Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, page_text)
        self.drawString(54, 36, "CONFIDENTIAL — Prepared by Euroshub Software House")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 48, 558, 48)
        self.restoreState()

def generate_proposal_pdf(lead: Dict[str, Any], proposal: Dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    primary_color = colors.HexColor("#0f172a")
    accent_blue = colors.HexColor("#2563eb")
    text_dark = colors.HexColor("#1e293b")
    text_muted = colors.HexColor("#64748b")
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=14,
        textColor=text_muted,
        spaceAfter=15
    )

    h2_style = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=accent_blue,
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=text_dark,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=text_dark,
        leftIndent=15,
        spaceAfter=4
    )

    story = []

    # Title & Header
    story.append(Paragraph("EUROSHUB SOFTWARE HOUSE", ParagraphStyle('Brand', fontName='Helvetica-Bold', fontSize=12, leading=14, textColor=accent_blue)))
    story.append(Spacer(1, 4))
    proposal_title = proposal.get("title") or f"Project Proposal for {lead.get('company_name', 'Client')}"
    story.append(Paragraph(proposal_title, title_style))
    story.append(Paragraph(f"Prepared for: <b>{lead.get('company_name')}</b> | Date: {datetime.now().strftime('%B %d, %Y')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#e2e8f0"), spaceAfter=15))

    # Opportunity Meta Card Table
    meta_data = [
        [
            Paragraph("<b>Client Company:</b>", body_style), Paragraph(lead.get('company_name', '-'), body_style),
            Paragraph("<b>Primary Contact:</b>", body_style), Paragraph(lead.get('contact_name') or 'Lead Stakeholder', body_style)
        ],
        [
            Paragraph("<b>Industry:</b>", body_style), Paragraph(lead.get('industry') or 'Technology', body_style),
            Paragraph("<b>Project Title:</b>", body_style), Paragraph(lead.get('project_title') or 'Software Development', body_style)
        ],
        [
            Paragraph("<b>Estimated Budget:</b>", body_style), Paragraph(f"{lead.get('currency', 'USD')} {float(lead.get('budget', 0)):,.2f}", body_style),
            Paragraph("<b>Target Timeline:</b>", body_style), Paragraph(str(lead.get('expected_deadline') or 'Agile Delivery'), body_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[110, 140, 110, 140])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))

    content = proposal.get("content", {})

    # 1. Project Overview
    if content.get("project_overview"):
        story.append(Paragraph("1. Project Overview & Objectives", h2_style))
        story.append(Paragraph(content["project_overview"], body_style))
        story.append(Spacer(1, 10))

    # 2. Client Requirements
    reqs = content.get("client_requirements", [])
    if reqs:
        story.append(Paragraph("2. Key Requirements & Scope", h2_style))
        for r in reqs:
            story.append(Paragraph(f"• {r}", bullet_style))
        story.append(Spacer(1, 10))

    # 3. Proposed Solution & Architecture
    if content.get("proposed_solution"):
        story.append(Paragraph("3. Proposed Technical Solution", h2_style))
        story.append(Paragraph(content["proposed_solution"], body_style))
        story.append(Spacer(1, 10))

    # 4. Deliverables & Milestones
    deliverables = content.get("deliverables", [])
    if deliverables:
        story.append(Paragraph("4. Key Deliverables", h2_style))
        for d in deliverables:
            story.append(Paragraph(f"✓ <b>{d}</b>", bullet_style))
        story.append(Spacer(1, 10))

    # 5. Timeline & Pricing Summary Box
    timeline_text = content.get("timeline", "8-10 Weeks")
    pricing_text = content.get("pricing", f"{lead.get('currency', 'USD')} {float(lead.get('budget', 0)):,.2f}")
    
    pricing_data = [
        [Paragraph("<b>Estimated Timeline:</b>", body_style), Paragraph(timeline_text, body_style)],
        [Paragraph("<b>Commercial Pricing:</b>", body_style), Paragraph(f"<b>{pricing_text}</b>", ParagraphStyle('Price', parent=body_style, textColor=accent_blue))]
    ]
    pricing_table = Table(pricing_data, colWidths=[150, 350])
    pricing_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
        ('BOX', (0, 0), (-1, -1), 1.5, accent_blue),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#bfdbfe")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    story.append(KeepTogether([
        Paragraph("5. Commercials & Timeline", h2_style),
        pricing_table,
        Spacer(1, 10)
    ]))

    # 6. Assumptions & Prerequisites
    assumptions = content.get("assumptions", [])
    if assumptions:
        story.append(Paragraph("6. Assumptions & Client Responsibilities", h2_style))
        for a in assumptions:
            story.append(Paragraph(f"— {a}", bullet_style))
        story.append(Spacer(1, 10))

    # 7. Next Steps
    if content.get("next_steps"):
        story.append(Paragraph("7. Next Steps & Kickoff", h2_style))
        story.append(Paragraph(content["next_steps"], body_style))

    # Build PDF with custom NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()
