"""
Report Generator for HoneyCloud
Generates CSV reports of attack events
"""
import csv
import logging
import os
from datetime import datetime
from typing import List

logger = logging.getLogger(__name__)


def generate_csv_report(events: List[dict], filename: str = None) -> str:
    """
    Generate CSV report from attack events.
    
    Args:
        events: List of attack event dictionaries
        filename: Output filename (optional)
        
    Returns:
        Path to generated CSV file
    """
    from .config import settings
    # Ensure reports directory exists
    os.makedirs(settings.reports_dir, exist_ok=True)
    
    if not filename:
        filename = os.path.join(settings.reports_dir, f"attack_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if not events:
                csvfile.write("No attack events to report\n")
                return filename
            
            fieldnames = ['id', 'timestamp', 'service', 'source_ip', 'username', 
                         'severity', 'ai_label', 'threat_score', 'command']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for event in events:
                writer.writerow({k: event.get(k, '') for k in fieldnames})
        
        logger.info(f"✅ CSV report generated: {filename}")
        return filename
    
    except Exception as e:
        logger.error(f"❌ Error generating CSV report: {e}")
        raise


def generate_pdf_report(events: List[dict], stats: dict, filename: str = None) -> str:
    """
    Generate a PDF report (fallback to text if reportlab not available).
    
    Args:
        events: List of attack event dictionaries
        stats: Statistics dictionary
        filename: Output filename (optional)
        
    Returns:
        Path to generated report file
    """
    from .config import settings
    # Ensure reports directory exists
    os.makedirs(settings.reports_dir, exist_ok=True)
    
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(settings.reports_dir, f"attack_report_{timestamp}.pdf")
    
    try:
        # Try to generate actual PDF
        return _generate_actual_pdf(events, stats, filename)
    except ImportError:
        # Fallback to text file if PDF libraries not available
        logger.warning("PDF libraries not available, generating text report instead")
        text_filename = filename.replace('.pdf', '.txt')
        return _generate_text_report(events, stats, text_filename)
    except Exception as e:
        logger.error(f"❌ Error generating PDF report: {e}")
        # Fallback to text file
        text_filename = filename.replace('.pdf', '.txt')
        return _generate_text_report(events, stats, text_filename)


def _format_risk_score(severity: str, raw_score: float) -> str:
    """Format the risk score into logical buckets based on severity."""
    severity = str(severity).upper().strip() if severity else "UNKNOWN"
    
    if raw_score is None:
        raw_score = 0.5
    elif raw_score > 1.0:
        raw_score = min(1.0, raw_score / 100.0)
        
    if severity == 'CRITICAL':
        score = 80 + int(raw_score * 20)
    elif severity == 'HIGH':
        score = 60 + int(raw_score * 20)
    elif severity == 'MEDIUM':
        score = 30 + int(raw_score * 30)
    elif severity == 'LOW':
        score = 10 + int(raw_score * 20)
    else:
        score = int(raw_score * 100)
        
    score = min(100, max(0, score))
    return f"{score}/100"


def _generate_actual_pdf(events: List[dict], stats: dict, filename: str) -> str:
    """Generate actual PDF using reportlab (premium SOC dark theme)"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        
        doc = SimpleDocTemplate(
            filename, 
            pagesize=A4,
            leftMargin=36, rightMargin=36,
            topMargin=36, bottomMargin=36
        )
        styles = getSampleStyleSheet()
        story = []
        
        # Custom Palette
        brand_dark = colors.HexColor('#0f172a')
        card_bg = colors.HexColor('#1e293b')
        accent_blue = colors.HexColor('#38bdf8')
        text_light = colors.HexColor('#f8fafc')
        text_slate = colors.HexColor('#e2e8f0')
        text_muted = colors.HexColor('#94a3b8')
        
        # Title Styles
        title_style = ParagraphStyle(
            'BannerTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            textColor=accent_blue,
            alignment=1,
            spaceAfter=4
        )
        
        subtitle_style = ParagraphStyle(
            'BannerSub',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=text_muted,
            alignment=1,
            spaceAfter=15
        )
        
        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=14,
            textColor=accent_blue,
            spaceBefore=12,
            spaceAfter=8,
            borderColor=accent_blue,
            borderWidth=0.5,
            borderPadding=4
        )
        
        # Header Banner block
        banner_data = [
            [Paragraph("🍯 HoneyCloud SOC Comprehensive Report", title_style)],
            [Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}", subtitle_style)]
        ]
        banner_table = Table(banner_data, colWidths=[523])
        banner_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), brand_dark),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOX', (0, 0), (-1, -1), 2, accent_blue),
        ]))
        story.append(banner_table)
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("📊 EXECUTIVE SUMMARY", section_heading))
        
        # Statistics Table
        stats_data = [['Metric', 'Value']]
        stats_data.append(["Total Attack Events", str(stats.get('total_events', 0))])
        
        # Add service stats
        for service, count in stats.get('events_by_service', {}).items():
            stats_data.append([f"Service: {service}", str(count)])
            
        # Add severity stats
        for severity, count in stats.get('events_by_severity', {}).items():
            stats_data.append([f"Severity: {severity}", str(count)])
            
        if len(stats_data) > 1:
            stats_table = Table(stats_data, colWidths=[300, 223])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), brand_dark),
                ('TEXTCOLOR', (0, 0), (-1, 0), accent_blue),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), card_bg),
                ('TEXTCOLOR', (0, 1), (-1, -1), text_slate),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#334155')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [card_bg, brand_dark])
            ]))
            story.append(stats_table)
            
        story.append(Spacer(1, 25))
        
        # Recent Events
        story.append(Paragraph("🚨 RECENT ATTACK EVENTS (Last 15)", section_heading))
        
        if events:
            events_data = [['Time (UTC)', 'Service', 'Source IP', 'Severity', 'Risk']]
            
            for event in events[:15]:
                timestamp = event.get('timestamp', '')
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        formatted_time = dt.strftime('%m/%d %H:%M')
                    except:
                        formatted_time = timestamp[:16]
                else:
                    formatted_time = 'N/A'
                    
                threat_score = event.get('threat_score', 0.0)
                risk_score = _format_risk_score(event.get('severity', ''), threat_score)
                
                events_data.append([
                    formatted_time,
                    event.get('service', 'N/A')[:15],
                    event.get('source_ip', 'N/A'),
                    event.get('severity', 'N/A'),
                    risk_score
                ])
                
            events_table = Table(events_data, colWidths=[90, 120, 110, 103, 100])
            events_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), brand_dark),
                ('TEXTCOLOR', (0, 0), (-1, 0), accent_blue),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), card_bg),
                ('TEXTCOLOR', (0, 1), (-1, -1), text_slate),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#334155')),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [card_bg, brand_dark])
            ]))
            story.append(events_table)
        else:
            story.append(Paragraph("No recent events to display.", styles['Normal']))
            
        doc.build(story)
        logger.info(f"✅ Premium PDF report generated: {filename}")
        return filename
        
    except ImportError as e:
        logger.warning(f"PDF generation libraries not available: {e}")
        raise


def _generate_text_report(events: List[dict], stats: dict, filename: str) -> str:
    """
    Generate a text-based report (fallback when PDF not available).
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("HoneyCloud Security Report\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")
            
            f.write("EXECUTIVE SUMMARY\n")
            f.write("-" * 70 + "\n")
            f.write(f"Total Attack Events: {stats.get('total_events', 0)}\n\n")
            
            f.write("Events by Service:\n")
            for service, count in stats.get('events_by_service', {}).items():
                f.write(f"  {service}: {count}\n")
            
            f.write("\nEvents by Severity:\n")
            for severity, count in stats.get('events_by_severity', {}).items():
                f.write(f"  {severity}: {count}\n")
            
            f.write("\nAI Classification:\n")
            for label, count in stats.get('ai_labels', {}).items():
                f.write(f"  {label}: {count}\n")
            
            f.write("\n" + "=" * 70 + "\n")
            f.write("RECENT ATTACK EVENTS (Last 20)\n")
            f.write("=" * 70 + "\n\n")
            
            for event in events[:20]:
                f.write(f"Event ID: {event.get('id')}\n")
                f.write(f"  Timestamp: {event.get('timestamp')}\n")
                f.write(f"  Service: {event.get('service')}\n")
                f.write(f"  Source IP: {event.get('source_ip')}\n")
                f.write(f"  Username: {event.get('username', 'N/A')}\n")
                f.write(f"  Severity: {event.get('severity')}\n")
                f.write(f"  AI Label: {event.get('ai_label')}\n")
                f.write(f"  Threat Score: {event.get('threat_score')}\n")
                if event.get('command'):
                    f.write(f"  Command: {event.get('command')}\n")
                f.write("\n")
        
        logger.info(f"✅ Text report generated: {filename}")
        return filename
    
    except Exception as e:
        logger.error(f"❌ Error generating text report: {e}")
        raise


def generate_incident_report_pdf(event: dict, filename: str = None) -> str:
    """
    Generate a detailed single incident report PDF.
    
    Args:
        event: Attack event dictionary.
        filename: Optional output filename.
        
    Returns:
        Path to the generated PDF.
    """
    from .config import settings
    # Ensure reports directory exists
    os.makedirs(settings.reports_dir, exist_ok=True)
    
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        event_id = event.get('id', 'new')
        filename = os.path.join(settings.reports_dir, f"incident_report_{event_id}_{timestamp}.pdf")
        
    try:
        return _generate_single_incident_pdf(event, filename)
    except ImportError:
        logger.warning("PDF libraries not available, generating text single incident report instead")
        text_filename = filename.replace('.pdf', '.txt')
        return _generate_single_incident_text_report(event, text_filename)
    except Exception as e:
        logger.error(f"❌ Error generating single incident PDF report: {e}")
        text_filename = filename.replace('.pdf', '.txt')
        return _generate_single_incident_text_report(event, text_filename)


def _generate_single_incident_pdf(event: dict, filename: str) -> str:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    import html

    # Build A4 Document
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Custom Palette
    brand_dark = colors.HexColor('#0f172a')
    card_bg = colors.HexColor('#1e293b')
    accent_blue = colors.HexColor('#38bdf8')
    text_light = colors.HexColor('#f8fafc')
    text_slate = colors.HexColor('#e2e8f0')
    text_muted = colors.HexColor('#94a3b8')
    
    severity_colors = {
        'CRITICAL': colors.HexColor('#ef4444'),
        'HIGH': colors.HexColor('#f97316'),
        'MEDIUM': colors.HexColor('#eab308'),
        'LOW': colors.HexColor('#84cc16')
    }
    
    severity = event.get('severity', 'UNKNOWN').upper()
    color_theme = severity_colors.get(severity, colors.HexColor('#64748b'))
    
    # Risk Score Formatting
    threat_score = event.get('threat_score', 0.0)
    risk_score_str = _format_risk_score(severity, threat_score)
    risk_score = int(risk_score_str.split('/')[0])
        
    # MITRE ATT&CK Resolution
    mitre_tech = "T1595 - Active Scanning"
    if event.get('endpoint'):
        endpoint_lower = event.get('endpoint', '').lower()
        if ".env" in endpoint_lower or "config" in endpoint_lower:
            mitre_tech = "T1552.001 - Credentials In Files"
        elif "login" in endpoint_lower or "admin" in endpoint_lower:
            mitre_tech = "T1110.001 - Password Guessing"
            
    persona = event.get('persona') or "Scanner"
    location = event.get('location', {})
    
    # Styles definition
    title_style = ParagraphStyle(
        'BannerTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=accent_blue,
        alignment=1,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'BannerSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=text_muted,
        alignment=1,
        spaceAfter=15
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=accent_blue,
        spaceBefore=12,
        spaceAfter=6,
        borderColor=accent_blue,
        borderWidth=0.5,
        borderPadding=4
    )
    
    label_style = ParagraphStyle(
        'GridLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=text_muted
    )
    
    val_style = ParagraphStyle(
        'GridValue',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=text_slate
    )
    
    val_bold = ParagraphStyle(
        'GridValueBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=text_light
    )
    
    val_risk = ParagraphStyle(
        'GridValueRisk',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=color_theme
    )
    
    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=9,
        textColor=text_slate,
        leading=11
    )
    
    list_item_style = ParagraphStyle(
        'ListItemStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=text_slate,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    # Header Banner block
    banner_data = [
        [Paragraph("🍯 HoneyCloud Security Operations Center", title_style)],
        [Paragraph(f"{severity} Incident Report &bull; ID: HC-INC-{event.get('id', 'new')}", subtitle_style)]
    ]
    banner_table = Table(banner_data, colWidths=[523])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), brand_dark),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOX', (0, 0), (-1, -1), 2, color_theme),
    ]))
    
    story.append(banner_table)
    story.append(Spacer(1, 15))
    
    # Section: Incident Overview
    story.append(Paragraph("🔍 INCIDENT OVERVIEW", section_heading))
    
    overview_data = [
        [Paragraph("Risk Score:", label_style), Paragraph(f"{risk_score}/100", val_risk),
         Paragraph("Severity Level:", label_style), Paragraph(severity, val_risk)],
        [Paragraph("Attack Type:", label_style), Paragraph(event.get('service', 'Demo E-Commerce'), val_bold),
         Paragraph("Persona:", label_style), Paragraph(persona, val_style)],
        [Paragraph("MITRE ATT&CK:", label_style), Paragraph(mitre_tech, val_style),
         Paragraph("Timestamp:", label_style), Paragraph(datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'), val_style)]
    ]
    
    overview_table = Table(overview_data, colWidths=[100, 161, 100, 162])
    overview_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#334155')),
        ('BACKGROUND', (0, 0), (-1, -1), card_bg)
    ]))
    story.append(overview_table)
    story.append(Spacer(1, 15))
    
    # Section: Network & Target Context
    story.append(Paragraph("🌐 NETWORK & TARGET CONTEXT", section_heading))
    
    geo_str = f"{location.get('flag', '🌍')} {location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}"
    
    network_data = [
        [Paragraph("Source IP:", label_style), Paragraph(event.get('source_ip', 'Unknown'), val_bold),
         Paragraph("Target Service:", label_style), Paragraph(event.get('service', 'Protected Webnode'), val_style)],
        [Paragraph("Target Endpoint:", label_style), Paragraph(event.get('endpoint', 'N/A') or 'N/A', val_bold),
         Paragraph("Request Method:", label_style), Paragraph(event.get('method', 'UNKNOWN'), val_style)],
        [Paragraph("Geo Location:", label_style), Paragraph(geo_str, val_style),
         Paragraph("ISP / Provider:", label_style), Paragraph(location.get('isp', 'Unknown'), val_style)]
    ]
    
    network_table = Table(network_data, colWidths=[100, 161, 100, 162])
    network_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#334155')),
        ('BACKGROUND', (0, 0), (-1, -1), card_bg)
    ]))
    story.append(network_table)
    story.append(Spacer(1, 15))
    
    # Section: Payload Logged
    payload_content = event.get('command') or event.get('payload') or 'No payload recorded'
    story.append(Paragraph("📝 PAYLOAD LOGGED", section_heading))
    
    escaped_payload = html.escape(payload_content)
    payload_p = Paragraph(escaped_payload, code_style)
    payload_table = Table([[payload_p]], colWidths=[523])
    payload_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), brand_dark),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#334155'))
    ]))
    story.append(payload_table)
    story.append(Spacer(1, 15))
    
    # Section: Incident Response Recommendations
    story.append(Paragraph("🛡️ RECOMMENDED MITIGATION PLAYBOOK", section_heading))
    
    recommendations = [
        "1. Investigate and monitor the attacker's activity through the HoneyCloud SOC dashboard.",
        "2. Evaluate deception action logs to check if the attacker attempted to access honeytokens or honeyfiles.",
        "3. Block the source IP at the firewall / network level if the attack persists or shows malicious intent.",
        "4. Audit access control configuration for the target endpoint to ensure credentials are secure."
    ]
    
    for rec in recommendations:
        story.append(Paragraph(rec, list_item_style))
        
    doc.build(story)
    logger.info(f"✅ Premium incident report generated: {filename}")
    return filename


def _generate_single_incident_text_report(event: dict, filename: str) -> str:
    """
    Generate a text-based incident report when PDF library is not available.
    """
    try:
        location = event.get('location', {})
        threat_score = event.get('threat_score', 0.0)
        if threat_score is None:
            risk_score = 50
        elif threat_score > 1.0:
            risk_score = int(min(100.0, threat_score))
        else:
            risk_score = int(min(100.0, threat_score * 100))
            
        mitre_tech = "T1595 - Active Scanning"
        if event.get('endpoint'):
            endpoint_lower = event.get('endpoint', '').lower()
            if ".env" in endpoint_lower or "config" in endpoint_lower:
                mitre_tech = "T1552.001 - Credentials In Files"
            elif "login" in endpoint_lower or "admin" in endpoint_lower:
                mitre_tech = "T1110.001 - Password Guessing"
                
        persona = event.get('persona') or "Scanner"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("🍯 HoneyCloud Incident Report\n")
            f.write(f"Report ID: HC-INCIDENT-{event.get('id', 'new')}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
            f.write("=" * 70 + "\n\n")
            
            f.write("INCIDENT OVERVIEW\n")
            f.write("-" * 30 + "\n")
            f.write(f"Severity Level: {event.get('severity', 'UNKNOWN')}\n")
            f.write(f"Risk Score:     {risk_score}/100\n")
            f.write(f"Attack Type:    {event.get('service', 'Reconnaissance Scan')}\n")
            f.write(f"MITRE ATT&CK:   {mitre_tech}\n")
            f.write(f"Persona:        {persona}\n\n")
            
            f.write("NETWORK & TARGET CONTEXT\n")
            f.write("-" * 30 + "\n")
            f.write(f"Source IP:      {event.get('source_ip', 'Unknown')}\n")
            f.write(f"Target Service: {event.get('service', 'Protected Webnode')}\n")
            f.write(f"Target Endpoint:{event.get('endpoint', 'N/A')}\n")
            f.write(f"Method:         {event.get('method', 'UNKNOWN')}\n")
            f.write(f"Geo Location:   {location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}\n")
            f.write(f"ISP / Provider: {location.get('isp', 'Unknown')}\n\n")
            
            f.write("PAYLOAD LOGGED\n")
            f.write("-" * 30 + "\n")
            f.write(f"{event.get('command') or event.get('payload') or 'No payload recorded'}\n\n")
            
            f.write("RECOMMENDED RESPONSE ACTIONS\n")
            f.write("-" * 30 + "\n")
            f.write("1. Investigate and monitor the attacker's activity through the HoneyCloud SOC dashboard.\n")
            f.write("2. Evaluate deception action logs to check if the attacker attempted to access honeytokens.\n")
            f.write("3. Block the source IP at the firewall level if the attack persists.\n")
            f.write("4. Audit access control configuration for the target endpoint.\n")
            
        logger.info(f"✅ Single incident text report generated: {filename}")
        return filename
    except Exception as e:
        logger.error(f"❌ Error generating single incident text report: {e}")
        raise
