# -*- coding: utf-8 -*-

"""
PDF vulnerability report generator
Uses reportlab (clean, professional layout)
"""

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    ListItem,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch


def generate_pdf_report(
    file_path: str,
    domain: str,
    risk_level: str,
    score: int,
    threats: list,
    recommendations: list,
):
    """
    Generates a vulnerability scan PDF report
    """

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=22,
        spaceAfter=20,
    )

    header_style = ParagraphStyle(
        "HeaderStyle",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=16,
        spaceAfter=10,
    )

    normal_style = ParagraphStyle(
        "NormalStyle",
        parent=styles["Normal"],
        fontSize=11,
        spaceAfter=6,
    )

    elements = []

    # Title
    elements.append(Paragraph("Website Vulnerability Scan Report", title_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Meta info
    elements.append(Paragraph(f"<b>Target:</b> {domain}", normal_style))
    elements.append(Paragraph(f"<b>Risk Level:</b> {risk_level}", normal_style))
    elements.append(Paragraph(f"<b>Risk Score:</b> {score}/10", normal_style))

    elements.append(Spacer(1, 0.3 * inch))

    # Threats section
    elements.append(Paragraph("Identified Threats", header_style))

    threat_items = [
        ListItem(Paragraph(threat, normal_style)) for threat in threats
    ]

    elements.append(
        ListFlowable(
            threat_items,
            bulletType="bullet",
            start="circle",
            leftIndent=20,
        )
    )

    elements.append(Spacer(1, 0.25 * inch))

    # Recommendations section
    elements.append(Paragraph("Security Recommendations", header_style))

    rec_items = [
        ListItem(Paragraph(rec, normal_style)) for rec in recommendations
    ]

    elements.append(
        ListFlowable(
            rec_items,
            bulletType="bullet",
            start="square",
            leftIndent=20,
        )
    )

    elements.append(Spacer(1, 0.4 * inch))

    # Footer note
    elements.append(
        Paragraph(
            "<i>This is a passive security assessment. "
            "No exploitation or intrusive testing was performed.</i>",
            styles["Italic"],
        )
    )

    # Build PDF
    doc.build(elements)

    return file_path
