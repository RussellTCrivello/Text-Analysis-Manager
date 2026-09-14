"""
Word Export Utility
Professional export with centralized header settings and proper column widths
Enhanced with full Arabic RTL support
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import os
from docx import Document
from docx.shared import Inches, Pt, Cm, Twips
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import OxmlElement, parse_xml
from translations.translations import TranslationManager

# Import print settings
try:
    from utils.print_utils import PrintSettings, get_print_settings
except ImportError:
    PrintSettings = None
    get_print_settings = None


def set_rtl_paragraph(paragraph, is_rtl: bool = True):
    """Set paragraph direction to RTL for Arabic text"""
    if not is_rtl:
        return
    
    pPr = paragraph._p.get_or_add_pPr()
    bidi = OxmlElement('w:bidi')
    bidi.set(qn('w:val'), '1')
    pPr.append(bidi)
    
    # Set RTL alignment
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT


def set_rtl_cell(cell, is_rtl: bool = True):
    """Set cell direction to RTL for Arabic text"""
    if not is_rtl:
        return
    
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    
    # Set text direction RTL
    tcDirection = OxmlElement('w:textDirection')
    tcDirection.set(qn('w:val'), 'btLr')  # Bottom-to-top, Left-to-right
    tcPr.append(tcDirection)
    
    # Set RTL for all paragraphs in cell
    for para in cell.paragraphs:
        set_rtl_paragraph(para, is_rtl)


def set_document_rtl(doc, is_rtl: bool = True):
    """Set document-level RTL properties"""
    if not is_rtl:
        return
    
    # Set section to RTL
    for section in doc.sections:
        sectPr = section._sectPr
        
        # Add RTL text direction
        bidi = sectPr.find(qn('w:bidi'))
        if bidi is None:
            bidi = OxmlElement('w:bidi')
            bidi.set(qn('w:val'), '1')
            sectPr.append(bidi)


def get_arabic_font_name():
    """Get the appropriate Arabic font name available on the system"""
    # Priority order: Noto Sans Arabic (included), Traditional Arabic, Simplified Arabic
    fonts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fonts')
    noto_path = os.path.join(fonts_dir, 'NotoSansArabic-Regular.ttf')
    
    if os.path.exists(noto_path):
        return 'Noto Sans Arabic'
    return 'Traditional Arabic'


def set_run_font(run, is_rtl: bool = False, bold: bool = False):
    """Set font properties for a run with Arabic support"""
    if is_rtl:
        font_name = get_arabic_font_name()
        run.font.name = font_name
        run._element.rPr.rFonts.set(qn('w:ascii'), font_name)
        run._element.rPr.rFonts.set(qn('w:hAnsi'), font_name)
        run._element.rPr.rFonts.set(qn('w:cs'), font_name)
        
        # Enable complex script for Arabic
        rPr = run._element.get_or_add_rPr()
        cs = OxmlElement('w:cs')
        cs.set(qn('w:val'), '1')
        rPr.append(cs)
        
        # Set RTL direction
        rtl = OxmlElement('w:rtl')
        rtl.set(qn('w:val'), '1')
        rPr.append(rtl)
    else:
        run.font.name = 'Segoe UI'
    
    if bold:
        run.font.bold = True


def export_to_word(
    data: List[Dict],
    columns: List[tuple],
    filename: str,
    translator: TranslationManager,
    table_name: str = "Data",
    include_all_fields: bool = True,
    selected_columns: Optional[List[tuple]] = None,
    column_widths: Optional[Dict[str, int]] = None
) -> bool:
    """
    Export data to Word document with professional header
    
    Args:
        data: List of dictionaries containing data to export
        columns: List of tuples (key, header, width) defining displayed columns
        filename: Output filename
        translator: Translation manager for localized text
        table_name: Name of the table/data being exported
        include_all_fields: If True, export all fields from data, not just displayed columns
        selected_columns: List of (key, header) tuples for columns to export
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get global print settings
        settings = get_print_settings() if get_print_settings else None
        
        # Create document
        doc = Document()
        
        # Set page orientation to landscape for comfortable table display
        section = doc.sections[0]
        section.orientation = WD_ORIENT.LANDSCAPE
        # Swap width and height to match landscape orientation
        new_width, new_height = section.page_height, section.page_width
        section.page_width = new_width
        section.page_height = new_height
        
        # Set up document properties for RTL if Arabic
        is_rtl = translator.current_language == 'ar'
        
        # Apply RTL to document if Arabic
        if is_rtl:
            set_document_rtl(doc, is_rtl)
        
        # Add professional header
        add_professional_header(doc, settings, translator, table_name, len(data), is_rtl)
        
        # Determine export columns
        if selected_columns:
            export_columns = selected_columns
        elif include_all_fields and data:
            all_keys = set()
            for row in data:
                all_keys.update(row.keys())
            
            export_columns = []
            column_dict = {col[0]: col[1] for col in columns}
            displayed_keys = [col[0] for col in columns]
            other_keys = sorted([k for k in all_keys if k not in displayed_keys])
            
            for key in displayed_keys + other_keys:
                header = column_dict.get(key, format_field_name(key))
                export_columns.append((key, header))
        else:
            export_columns = [(col[0], col[1]) for col in columns]
        
        # Add data table
        if data and export_columns:
            # Create table with row number column
            num_cols = len(export_columns) + 1  # +1 for row number
            table = doc.add_table(rows=1, cols=num_cols)
            table.style = 'Table Grid'
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.autofit = True
            
            # Style header row
            header_cells = table.rows[0].cells
            
            # Row number header
            header_cells[0].text = '#'
            set_cell_shading(header_cells[0], '2C3E50')
            set_cell_width(header_cells[0], Cm(1.2))
            for paragraph in header_cells[0].paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.size = Pt(10)
                    run.font.color.rgb = docx_rgb(255, 255, 255)
            
            # Calculate column widths based on content and settings
            # Use provided column_widths if available, otherwise use settings
            if column_widths:
                # Convert percentage to cm (assuming ~16cm usable width for table)
                # Word tables typically use ~16-17cm width on A4 page with margins
                total_table_width_cm = 16.0
                
                col_widths = {}
                total_percentage = sum(column_widths.get(col_key, 0) for col_key, _ in export_columns)
                
                # Normalize percentages if they don't sum to 100%
                normalize = total_percentage != 100 and total_percentage > 0
                
                for col_key, _ in export_columns:
                    if col_key in column_widths:
                        width_percentage = column_widths[col_key]
                        
                        # Normalize if needed
                        if normalize:
                            width_percentage = (width_percentage / total_percentage) * 100
                        
                        # Convert percentage to cm
                        col_widths[col_key] = (width_percentage / 100.0) * total_table_width_cm
                    else:
                        # Fallback to auto-calculation
                        col_widths[col_key] = None
                
                # Fill in missing widths with auto-calculation
                auto_widths = calculate_column_widths(data, export_columns, settings)
                missing_count = sum(1 for v in col_widths.values() if v is None)
                
                if missing_count > 0:
                    # Distribute remaining space among missing columns
                    used_percentage = sum(column_widths.get(col_key, 0) for col_key, _ in export_columns)
                    remaining_percentage = 100 - used_percentage
                    remaining_width_cm = (remaining_percentage / 100.0) * total_table_width_cm
                    
                    for col_key in col_widths:
                        if col_widths[col_key] is None:
                            # Distribute remaining space equally or use auto-calculated
                            if missing_count > 0:
                                col_widths[col_key] = remaining_width_cm / missing_count
                            else:
                                col_widths[col_key] = auto_widths.get(col_key, 4.0)
            else:
                col_widths = calculate_column_widths(data, export_columns, settings)
            
            # Data column headers
            for i, (col_key, col_name) in enumerate(export_columns, 1):
                header_cells[i].text = str(col_name)
                set_cell_shading(header_cells[i], '2C3E50')
                if col_key in col_widths:
                    set_cell_width(header_cells[i], Cm(col_widths[col_key]))
                
                # Apply RTL to header cell if Arabic
                if is_rtl:
                    set_rtl_cell(header_cells[i], True)
                
                for paragraph in header_cells[i].paragraphs:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in paragraph.runs:
                        set_run_font(run, is_rtl, bold=True)
                        run.font.size = Pt(10)
                        run.font.color.rgb = docx_rgb(255, 255, 255)
            
            # Add data rows
            for row_idx, row_data in enumerate(data, 1):
                row_cells = table.add_row().cells
                
                # Row number
                row_cells[0].text = str(row_idx)
                set_cell_width(row_cells[0], Cm(1.2))
                for paragraph in row_cells[0].paragraphs:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in paragraph.runs:
                        run.font.size = Pt(9)
                        run.font.bold = True
                        run.font.color.rgb = docx_rgb(127, 140, 141)
                        run.font.name = 'Segoe UI'  # Keep numbers in LTR font
                
                # Alternate row coloring
                if row_idx % 2 == 0:
                    set_cell_shading(row_cells[0], 'F8F9FA')
                
                # Data columns
                for i, (col_key, _) in enumerate(export_columns, 1):
                    value = row_data.get(col_key)
                    display_value = format_value_for_word(value, col_key)
                    row_cells[i].text = display_value
                    
                    if col_key in col_widths:
                        set_cell_width(row_cells[i], Cm(col_widths[col_key]))
                    
                    # Alternate row coloring
                    if row_idx % 2 == 0:
                        set_cell_shading(row_cells[i], 'F8F9FA')
                    
                    # Apply RTL to data cell if Arabic
                    if is_rtl:
                        set_rtl_cell(row_cells[i], True)
                    
                    for paragraph in row_cells[i].paragraphs:
                        if is_rtl:
                            paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                        for run in paragraph.runs:
                            set_run_font(run, is_rtl)
                            run.font.size = Pt(9)
                            # Style null values
                            if display_value == '-':
                                run.font.color.rgb = docx_rgb(189, 195, 199)
                                run.font.italic = True
        
        # Add footer
        add_professional_footer(doc, settings, translator, len(data), is_rtl)
        
        # Save document
        doc.save(filename)
        return True
    except Exception as e:
        raise Exception(f"Error exporting to Word: {str(e)}")


def calculate_column_widths(data: List[Dict], columns: List[tuple], settings) -> Dict[str, float]:
    """Calculate optimal column widths in cm based on content"""
    widths = {}
    
    # Get settings column widths if available (legacy support)
    if settings and hasattr(settings, 'column_widths') and settings.column_widths:
        for col_key, _ in columns:
            if col_key in settings.column_widths:
                # Convert percentage to cm (assuming ~16cm usable width)
                widths[col_key] = settings.column_widths[col_key] * 0.16
    
    # Calculate based on content for columns without specified width
    for col_key, col_header in columns:
        if col_key not in widths:
            max_len = len(str(col_header))
            
            # Sample first 50 rows for width calculation
            for row in data[:50]:
                value = row.get(col_key)
                if value is not None:
                    val_str = str(value)
                    # Take first line if multi-line
                    first_line = val_str.split('\n')[0] if '\n' in val_str else val_str
                    max_len = max(max_len, min(len(first_line), 50))
            
            # Convert character length to cm (approximate)
            widths[col_key] = min(max(max_len * 0.2, 2.0), 8.0)
    
    return widths


def add_professional_header(doc: Document, settings, translator, table_name: str, total_records: int, is_rtl: bool = False):
    """Add professional 3-section header to document with Arabic support"""
    
    # Create header table (3 columns)
    header_table = doc.add_table(rows=1, cols=3)
    header_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    # Remove borders from header table
    for row in header_table.rows:
        for cell in row.cells:
            set_cell_border(cell, None)
    
    cells = header_table.rows[0].cells
    
    # Set column widths for header (left: 40%, center: 20%, right: 40%)
    # Swap for RTL
    if is_rtl:
        set_cell_width(cells[2], Cm(6.5))  # Right becomes left in RTL
        set_cell_width(cells[1], Cm(3.5))  # Center stays center
        set_cell_width(cells[0], Cm(6.5))  # Left becomes right in RTL
    else:
        set_cell_width(cells[0], Cm(6.5))
        set_cell_width(cells[1], Cm(3.5))
        set_cell_width(cells[2], Cm(6.5))
    
    # For RTL, swap left and right sections
    left_cell = cells[2] if is_rtl else cells[0]
    right_cell = cells[0] if is_rtl else cells[2]
    center_cell = cells[1]
    
    # Left section (org info) - becomes right in RTL
    left_para = left_cell.paragraphs[0]
    has_left_content = False
    
    if is_rtl:
        set_rtl_paragraph(left_para, True)
        left_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    if settings and settings.header_left_line1:
        run = left_para.add_run(settings.header_left_line1)
        set_run_font(run, is_rtl, bold=True)
        run.font.size = Pt(14)
        run.font.color.rgb = docx_rgb(44, 62, 80)
        has_left_content = True
    
    if settings and settings.header_left_line2:
        if has_left_content:
            left_para.add_run('\n')
        run = left_para.add_run(settings.header_left_line2)
        set_run_font(run, is_rtl)
        run.font.size = Pt(11)
        run.font.color.rgb = docx_rgb(52, 73, 94)
        has_left_content = True
    
    if settings and settings.header_left_line3:
        if has_left_content:
            left_para.add_run('\n')
        run = left_para.add_run(settings.header_left_line3)
        set_run_font(run, is_rtl)
        run.font.size = Pt(9)
        run.font.color.rgb = docx_rgb(127, 140, 141)
    
    # Center section (logo)
    center_para = center_cell.paragraphs[0]
    center_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if settings and settings.header_logo_path:
        if os.path.exists(settings.header_logo_path):
            try:
                run = center_para.add_run()
                run.add_picture(settings.header_logo_path, width=Inches(1.2))
            except:
                pass
    
    # Right section (doc number/date) - becomes left in RTL
    right_para = right_cell.paragraphs[0]
    
    if is_rtl:
        right_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    else:
        right_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    # Document number (keep LTR for numbers)
    if settings:
        doc_number = settings.generate_doc_number()
        if doc_number:
            run = right_para.add_run(f"#{doc_number}")
            run.bold = True
            run.font.size = Pt(12)
            run.font.color.rgb = docx_rgb(44, 62, 80)
            # Numbers should stay LTR
            run.font.name = 'Segoe UI'
            right_para.add_run('\n')
        
        # Date (keep LTR for dates)
        if settings.header_right_show_date:
            run = right_para.add_run(settings.get_formatted_date())
            run.font.size = Pt(10)
            run.font.color.rgb = docx_rgb(52, 73, 94)
            run.font.name = 'Segoe UI'
            right_para.add_run('\n')
        
        # Extra info
        if settings.header_right_extra:
            run = right_para.add_run(settings.header_right_extra)
            set_run_font(run, is_rtl)
            run.font.size = Pt(9)
            run.font.color.rgb = docx_rgb(127, 140, 141)
    
    # Add separator line
    separator = doc.add_paragraph()
    add_horizontal_line(separator)
    
    # Add title
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if is_rtl:
        set_rtl_paragraph(title_para, True)
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER  # Override RTL alignment for center
    
    run = title_para.add_run(f"{table_name}")
    set_run_font(run, is_rtl, bold=True)
    run.font.size = Pt(14)
    run.font.color.rgb = docx_rgb(102, 126, 234)
    
    # Add record count
    count_para = doc.add_paragraph()
    count_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Use translator for "Total Records" text
    if translator:
        total_label = translator.tr('report_total_records')
        records_label = translator.tr('report_records')
        total_text = f"{total_label}: {total_records} {records_label}"
    elif is_rtl:
        total_text = f"إجمالي السجلات: {total_records}"
    else:
        total_text = f"Total Records: {total_records}"
    
    run = count_para.add_run(total_text)
    set_run_font(run, is_rtl)
    run.font.size = Pt(10)
    run.font.color.rgb = docx_rgb(127, 140, 141)
    
    doc.add_paragraph()


def add_horizontal_line(paragraph):
    """Add a horizontal line to paragraph"""
    p = paragraph._p
    pPr = p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '12')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), '2C3E50')
    pBdr.append(bottom)
    pPr.append(pBdr)


def add_professional_footer(doc: Document, settings, translator, total_records: int, is_rtl: bool = False):
    """Add professional footer to document with Arabic support"""
    doc.add_paragraph()
    
    # Separator line
    separator = doc.add_paragraph()
    add_horizontal_line(separator)
    
    # Footer info
    footer_para = doc.add_paragraph()
    footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    if is_rtl:
        set_rtl_paragraph(footer_para, True)
        footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER  # Override RTL alignment
    
    parts = []
    
    if settings:
        if settings.footer_left:
            parts.append(settings.footer_left)
        
        if settings.footer_center:
            parts.append(settings.footer_center)
        
        if settings.footer_right:
            parts.append(settings.footer_right)
    
    if settings and settings.show_print_date:
        # Use translator for "Printed" label
        if translator:
            printed_label = translator.tr('printed')
            parts.append(f"{printed_label}: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        elif is_rtl:
            parts.append(f"تمت الطباعة: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        else:
            parts.append(f"Printed: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Use translator for total text
    if translator:
        total_label = translator.tr('report_total')
        records_label = translator.tr('report_records')
        footer_text = ' | '.join(parts) if parts else f"{total_label}: {total_records} {records_label}"
    elif is_rtl:
        footer_text = ' | '.join(parts) if parts else f"الإجمالي: {total_records} سجلات"
    else:
        footer_text = ' | '.join(parts) if parts else f"Total: {total_records} records"
    
    run = footer_para.add_run(footer_text)
    set_run_font(run, is_rtl)
    run.font.size = Pt(9)
    run.font.color.rgb = docx_rgb(127, 140, 141)


def set_cell_shading(cell, color_hex: str):
    """Set cell background color"""
    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), color_hex)
    cell._tc.get_or_add_tcPr().append(shading)


def set_cell_width(cell, width):
    """Set cell width"""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcW = OxmlElement('w:tcW')
    tcW.set(qn('w:w'), str(int(width.twips)))
    tcW.set(qn('w:type'), 'dxa')
    tcPr.append(tcW)


def set_cell_border(cell, border_color):
    """Set or remove cell borders"""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for border_name in ['top', 'left', 'bottom', 'right']:
        border = OxmlElement(f'w:{border_name}')
        if border_color:
            border.set(qn('w:val'), 'single')
            border.set(qn('w:sz'), '4')
            border.set(qn('w:color'), border_color)
        else:
            border.set(qn('w:val'), 'nil')
        tcBorders.append(border)
    tcPr.append(tcBorders)


def docx_rgb(r: int, g: int, b: int):
    """Create RGB color for docx"""
    from docx.shared import RGBColor
    return RGBColor(r, g, b)


def format_field_name(key: str) -> str:
    """Format field name for display (convert snake_case to Title Case)"""
    return key.replace('_', ' ').title()


def format_value_for_word(value, col_key: str = None) -> str:
    """Format value for Word document - handles None values properly"""
    if value is None:
        return '-'  # Display dash for None values
    elif value == '':
        return '-'
    elif isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(value, bool):
        return 'Yes' if value else 'No'
    elif isinstance(value, (int, float)) and col_key:
        # Check if this is importance column
        if 'importance' in col_key.lower():
            try:
                return f"{float(value) * 100:.0f}%"
            except:
                return str(value)
    
    result = str(value) if value else '-'
    return result if result.strip() else '-'


def export_timeline_to_word(events: List[Dict], file_path: str, translator: TranslationManager, 
                           density_mode: str = 'comfortable', include_header: bool = True,
                           preserve_format: bool = True):
    """Export timeline events to Word document with preserved formatting"""
    from widgets.timeline_widget import TimelineDesignSystem
    
    doc = Document()
    settings = get_print_settings() if get_print_settings else None
    is_rtl = translator.current_language == 'ar' if translator else False
    
    # Set document RTL if needed
    if is_rtl:
        set_document_rtl(doc, True)
    
    # Add header if requested
    if include_header and settings:
        add_professional_header(doc, settings, translator, "Timeline Events", len(events), is_rtl)
    
    # Title
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if is_rtl:
        set_rtl_paragraph(title_para, True)
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    title_text = translator.tr('timeline_data_section', default='Timeline Events Report') if translator else 'Timeline Events Report'
    title_run = title_para.add_run(title_text)
    set_run_font(title_run, is_rtl)
    title_run.font.size = Pt(18)
    title_run.font.bold = True
    title_run.font.color.rgb = docx_rgb(44, 62, 80)
    
    doc.add_paragraph()  # Spacing
    
    # Get density config
    config = TimelineDesignSystem.get_density_config(density_mode)
    
    # Add events
    for event in events:
        # Event container paragraph
        event_para = doc.add_paragraph()
        if is_rtl:
            set_rtl_paragraph(event_para, True)
        
        # Get event date
        event_date = None
        date_fields = ['date_content', 'date_analysis', 'date_entry', 
                      'date_creation', 'source_date_entry', 'content_date_creation']
        for field in date_fields:
            if field in event and event[field]:
                date_val = event[field]
                if isinstance(date_val, datetime):
                    event_date = date_val
                elif isinstance(date_val, str):
                    try:
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S']:
                            try:
                                event_date = datetime.strptime(date_val[:19], fmt)
                                break
                            except:
                                continue
                    except:
                        pass
                if event_date:
                    break
        
        date_str = event_date.strftime('%Y-%m-%d %H:%M') if event_date else 'No Date'
        
        # Date and title
        header_run = event_para.add_run(f"{date_str} - ")
        set_run_font(header_run, is_rtl)
        header_run.font.size = Pt(config['font_date'])
        header_run.font.bold = True
        header_run.font.color.rgb = docx_rgb(44, 62, 80)
        
        # Title
        title = ""
        if 'content_title' in event and event['content_title']:
            title = str(event['content_title'])
        elif 'classification' in event and event['classification']:
            title = str(event['classification'])
        elif 'source_name' in event and event['source_name']:
            title = str(event['source_name'])
        else:
            title = translator.tr('timeline_event', default='Event') if translator else 'Event'
        
        title_run = event_para.add_run(title)
        set_run_font(title_run, is_rtl)
        title_run.font.size = Pt(config['font_title'])
        title_run.font.bold = True
        title_run.font.color.rgb = docx_rgb(44, 62, 80)
        
        # Description
        if 'content_data' in event and event['content_data']:
            desc_para = doc.add_paragraph()
            if is_rtl:
                set_rtl_paragraph(desc_para, True)
            
            content = str(event['content_data'])
            desc_text = content[:500] + "..." if len(content) > 500 else content
            desc_run = desc_para.add_run(desc_text)
            set_run_font(desc_run, is_rtl)
            desc_run.font.size = Pt(config['font_desc'])
            desc_run.font.color.rgb = docx_rgb(85, 85, 85)
        
        # Metadata badges
        meta_para = doc.add_paragraph()
        if is_rtl:
            set_rtl_paragraph(meta_para, True)
        
        people = event.get('list_names_people', '')
        places = event.get('list_names_places', '')
        classification = event.get('classification', '')
        
        if people:
            people_run = meta_para.add_run(f"People: {str(people)[:50]} ")
            set_run_font(people_run, is_rtl)
            people_run.font.size = Pt(config['font_meta'])
            people_run.font.color.rgb = docx_rgb(52, 152, 219)
        
        if places:
            places_run = meta_para.add_run(f"Places: {str(places)[:50]} ")
            set_run_font(places_run, is_rtl)
            places_run.font.size = Pt(config['font_meta'])
            places_run.font.color.rgb = docx_rgb(231, 76, 60)
        
        if classification:
            class_run = meta_para.add_run(f"Classification: {classification} ")
            set_run_font(class_run, is_rtl)
            class_run.font.size = Pt(config['font_meta'])
            class_run.font.color.rgb = docx_rgb(155, 89, 182)
        
        # Source
        source = event.get('source_name', '')
        if source:
            source_para = doc.add_paragraph()
            if is_rtl:
                set_rtl_paragraph(source_para, True)
            
            source_run = source_para.add_run(f"Source: {source}")
            set_run_font(source_run, is_rtl)
            source_run.font.size = Pt(config['font_meta'])
            source_run.font.italic = True
            source_run.font.color.rgb = docx_rgb(149, 165, 166)
        
        # Add spacing between events
        doc.add_paragraph()
    
    # Add footer
    if settings:
        add_professional_footer(doc, settings, translator, len(events), is_rtl)
    
    # Save document
    doc.save(file_path)


def export_table_data_to_word_timeline_style(
    data: List[Dict],
    file_path: str,
    translator: TranslationManager,
    table_name: str = "Data",
    selected_columns: Optional[List[tuple]] = None,
    include_header: bool = True
) -> bool:
    """
    Export table data to Word document in timeline-style format (not table format)
    Similar to timeline export but adapted for Sources/Content/Analysis data
    
    Args:
        data: List of dictionaries containing data to export
        file_path: Output file path
        translator: Translation manager for localized text
        table_name: Name of the table/data being exported
        selected_columns: List of (key, header) tuples for columns to export
        include_header: Whether to include professional header
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from widgets.timeline_widget import TimelineDesignSystem
        
        # Handle empty data
        if not data:
            raise ValueError("No data to export")
        
        doc = Document()
        settings = get_print_settings() if get_print_settings else None
        is_rtl = translator.current_language == 'ar' if translator else False
        
        # Set document RTL if needed
        if is_rtl:
            set_document_rtl(doc, True)
        
        # Add header if requested
        if include_header and settings:
            add_professional_header(doc, settings, translator, table_name, len(data), is_rtl)
        
        # Title
        title_para = doc.add_paragraph()
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if is_rtl:
            set_rtl_paragraph(title_para, True)
            title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        title_text = f"{table_name} Report"
        title_run = title_para.add_run(title_text)
        set_run_font(title_run, is_rtl)
        title_run.font.size = Pt(18)
        title_run.font.bold = True
        title_run.font.color.rgb = docx_rgb(44, 62, 80)
        
        doc.add_paragraph()  # Spacing
        
        # Get density config
        density_mode = 'comfortable'
        config = TimelineDesignSystem.get_density_config(density_mode)
        
        # Determine which columns to export
        if selected_columns:
            export_columns = selected_columns
            # Create a set of selected column keys for fast lookup
            selected_keys = {col[0] for col in selected_columns}
        elif data:
            # Use all available keys
            all_keys = set()
            for row in data:
                all_keys.update(row.keys())
            export_columns = [(key, format_field_name(key)) for key in sorted(all_keys)]
            selected_keys = all_keys
        else:
            export_columns = []
            selected_keys = set()
        
        # If no selected_keys, use all keys from data
        if not selected_keys and data:
            for row in data:
                selected_keys.update(row.keys())
        
        # Filter data to only include selected fields
        filtered_data = []
        for entry in data:
            if selected_keys:
                # Only include fields that are in selected_columns
                filtered_entry = {key: value for key, value in entry.items() if key in selected_keys}
            else:
                filtered_entry = entry.copy()
            filtered_data.append(filtered_entry)
        
        # Add data entries in timeline style
        for entry in filtered_data:
            # Entry container paragraph
            entry_para = doc.add_paragraph()
            if is_rtl:
                set_rtl_paragraph(entry_para, True)
            
            # Get date for this entry
            event_date = None
            date_fields = ['date_content', 'date_analysis', 'date_entry', 
                          'date_creation', 'source_date_entry', 'content_date_creation',
                          'date_modified']
            for field in date_fields:
                if field in entry and entry[field]:
                    date_val = entry[field]
                    if isinstance(date_val, datetime):
                        event_date = date_val
                    elif isinstance(date_val, str):
                        try:
                            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S']:
                                try:
                                    event_date = datetime.strptime(date_val[:19], fmt)
                                    break
                                except:
                                    continue
                        except:
                            pass
                    if event_date:
                        break
            
            date_str = event_date.strftime('%Y-%m-%d %H:%M') if event_date else 'No Date'
            
            # Date and title/primary field
            header_run = entry_para.add_run(f"{date_str} - ")
            set_run_font(header_run, is_rtl)
            header_run.font.size = Pt(config['font_date'])
            header_run.font.bold = True
            header_run.font.color.rgb = docx_rgb(44, 62, 80)
            
            # Get primary title field (name, title, classification, etc.) - only if in selected columns
            title = ""
            title_field_used = None
            title_fields = ['name', 'title', 'classification', 'source_name', 'content_title']
            for field in title_fields:
                if field in selected_keys and field in entry and entry[field]:
                    title = str(entry[field])
                    title_field_used = field
                    break
            
            if not title:
                # Use first non-empty selected field as title
                for key, _ in export_columns:
                    if key in entry and entry[key] and key not in date_fields:
                        title = str(entry[key])[:100]
                        title_field_used = key
                        break
            
            if not title:
                title = translator.tr('entry', default='Entry') if translator else 'Entry'
            
            title_run = entry_para.add_run(title)
            set_run_font(title_run, is_rtl)
            title_run.font.size = Pt(config['font_title'])
            title_run.font.bold = True
            title_run.font.color.rgb = docx_rgb(44, 62, 80)
            
            # Track shown fields - start with date fields and the title field we used
            shown_fields = set(date_fields)
            if title_field_used:
                shown_fields.add(title_field_used)
            
            # Description/Content field (only if in selected columns)
            desc_fields = ['content_data', 'description', 'note', 'content_note', 'source_note']
            description_added = False
            desc_field_used = None
            for field in desc_fields:
                if field in selected_keys and field in entry and entry[field]:
                    desc_para = doc.add_paragraph()
                    if is_rtl:
                        set_rtl_paragraph(desc_para, True)
                    
                    content = str(entry[field])
                    desc_text = content[:500] + "..." if len(content) > 500 else content
                    desc_run = desc_para.add_run(desc_text)
                    set_run_font(desc_run, is_rtl)
                    desc_run.font.size = Pt(config['font_desc'])
                    desc_run.font.color.rgb = docx_rgb(85, 85, 85)
                    description_added = True
                    desc_field_used = field
                    break
            
            if desc_field_used:
                shown_fields.add(desc_field_used)
            
            # Metadata badges - show key fields (only if in selected columns)
            meta_para = doc.add_paragraph()
            if is_rtl:
                set_rtl_paragraph(meta_para, True)
            
            # People (only if in selected columns)
            if 'list_names_people' in selected_keys or 'people' in selected_keys:
                people = entry.get('list_names_people', '') or entry.get('people', '')
                if people:
                    people_run = meta_para.add_run(f"People: {str(people)[:50]} ")
                    set_run_font(people_run, is_rtl)
                    people_run.font.size = Pt(config['font_meta'])
                    people_run.font.color.rgb = docx_rgb(52, 152, 219)
                    shown_fields.add('list_names_people')
                    shown_fields.add('people')
            
            # Places (only if in selected columns)
            if 'list_names_places' in selected_keys or 'places' in selected_keys or 'city' in selected_keys or 'country' in selected_keys:
                places = entry.get('list_names_places', '') or entry.get('places', '')
                if not places:
                    # Try city/country
                    city = entry.get('city', '')
                    country = entry.get('country', '')
                    if city or country:
                        places = ", ".join(filter(None, [city, country]))
                if places:
                    places_run = meta_para.add_run(f"Places: {str(places)[:50]} ")
                    set_run_font(places_run, is_rtl)
                    places_run.font.size = Pt(config['font_meta'])
                    places_run.font.color.rgb = docx_rgb(231, 76, 60)
                    shown_fields.add('list_names_places')
                    shown_fields.add('places')
                    shown_fields.add('city')
                    shown_fields.add('country')
            
            # Classification (only if in selected columns)
            if 'classification' in selected_keys:
                classification = entry.get('classification', '')
                if classification:
                    class_run = meta_para.add_run(f"Classification: {classification} ")
                    set_run_font(class_run, is_rtl)
                    class_run.font.size = Pt(config['font_meta'])
                    class_run.font.color.rgb = docx_rgb(155, 89, 182)
                    shown_fields.add('classification')
            
            # Type (only if in selected columns)
            if 'type' in selected_keys or 'source_type' in selected_keys:
                type_val = entry.get('type', '') or entry.get('source_type', '')
                if type_val:
                    type_run = meta_para.add_run(f"Type: {str(type_val)[:50]} ")
                    set_run_font(type_run, is_rtl)
                    type_run.font.size = Pt(config['font_meta'])
                    type_run.font.color.rgb = docx_rgb(52, 73, 94)
                    shown_fields.add('type')
                    shown_fields.add('source_type')
            
            # Importance (only if in selected columns)
            if 'importance' in selected_keys:
                importance = entry.get('importance', '')
                if importance is not None and importance != '':
                    try:
                        imp_val = float(importance) * 100 if isinstance(importance, (int, float)) else str(importance)
                        imp_str = f"{imp_val:.0f}%" if isinstance(imp_val, float) else str(imp_val)
                        imp_run = meta_para.add_run(f"Importance: {imp_str} ")
                        set_run_font(imp_run, is_rtl)
                        imp_run.font.size = Pt(config['font_meta'])
                        imp_run.font.color.rgb = docx_rgb(241, 196, 15)
                        shown_fields.add('importance')
                    except:
                        pass
            
            # Show other selected fields that haven't been shown yet
            for key, header in export_columns:
                if key not in shown_fields and key in entry and entry[key]:
                    value = entry[key]
                    if value and str(value).strip() and str(value) != '-':
                        # Format the value
                        display_value = format_value_for_word(value, key)
                        if display_value and display_value != '-':
                            # Truncate long values
                            if len(display_value) > 100:
                                display_value = display_value[:97] + "..."
                            
                            field_run = meta_para.add_run(f"{header}: {display_value} ")
                            set_run_font(field_run, is_rtl)
                            field_run.font.size = Pt(config['font_meta'] - 1)
                            field_run.font.color.rgb = docx_rgb(127, 140, 141)
                            shown_fields.add(key)
            
            # Source (only if in selected columns)
            if 'source_name' in selected_keys:
                source = entry.get('source_name', '')
                if source:
                    source_para = doc.add_paragraph()
                    if is_rtl:
                        set_rtl_paragraph(source_para, True)
                    
                    source_run = source_para.add_run(f"Source: {source}")
                    set_run_font(source_run, is_rtl)
                    source_run.font.size = Pt(config['font_meta'])
                    source_run.font.italic = True
                    source_run.font.color.rgb = docx_rgb(149, 165, 166)
                    shown_fields.add('source_name')
            
            # Add spacing between entries
            doc.add_paragraph()
        
        # Add footer
        if settings:
            add_professional_footer(doc, settings, translator, len(data), is_rtl)
        
        # Save document
        doc.save(file_path)
        return True
    except Exception as e:
        raise Exception(f"Error exporting to Word (timeline style): {str(e)}")