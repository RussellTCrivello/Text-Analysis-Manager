"""
Preview Attachments Widget - Supports Images, PDFs, and Documents
"""
import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QFileDialog, QMessageBox, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QFont
from translations.translations import TranslationManager
from styles.styles import AppStyles


class ImagePreviewWidget(QWidget):
    """Widget for previewing images"""
    
    def __init__(self, parent=None, translator: TranslationManager = None):
        super().__init__(parent)
        self.translator = translator or TranslationManager(None)
        self.current_image_path = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup image preview UI"""
        layout = QVBoxLayout(self)
        
        # Image label with scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(400)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(AppStyles.get_component_style('preview_placeholder'))
        self.image_label.setText(self.translator.tr('lbl_image_preview'))
        
        scroll.setWidget(self.image_label)
        layout.addWidget(scroll)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.open_btn = QPushButton(self.translator.tr('btn_open_file'))
        self.open_btn.setStyleSheet(AppStyles.get_button_style('primary'))
        self.open_btn.clicked.connect(self.open_image)
        controls_layout.addWidget(self.open_btn)
        
        self.download_btn = QPushButton(self.translator.tr('btn_download_file'))
        self.download_btn.setStyleSheet(AppStyles.get_button_style('default'))
        self.download_btn.clicked.connect(self.download_image)
        controls_layout.addWidget(self.download_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
    
    def load_image(self, image_path: str):
        """Load and display an image"""
        if not os.path.exists(image_path):
            QMessageBox.warning(self, self.translator.tr('msg_error'), 
                              self.translator.tr('msg_file_not_found'))
            return False
        
        try:
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                QMessageBox.warning(self, self.translator.tr('msg_error'), 
                                  self.translator.tr('msg_no_preview_available'))
                return False
            
            # Scale image to fit while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                QSize(800, 600), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.current_image_path = image_path
            return True
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
            return False
    
    def open_image(self):
        """Open image file dialog"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            self.translator.tr('btn_open_file'),
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;All Files (*)"
        )
        if filename:
            self.load_image(filename)
    
    def download_image(self):
        """Download/save current image"""
        if not self.current_image_path:
            QMessageBox.warning(self, self.translator.tr('msg_warning'), 
                              self.translator.tr('msg_no_preview_available'))
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.translator.tr('btn_download_file'),
            os.path.basename(self.current_image_path),
            "Image Files (*.png *.jpg *.jpeg);;All Files (*)"
        )
        if filename:
            try:
                from shutil import copyfile
                copyfile(self.current_image_path, filename)
                QMessageBox.information(self, self.translator.tr('msg_success'), 
                                      self.translator.tr('msg_file_not_found'))
            except Exception as e:
                QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))


class PDFPreviewWidget(QWidget):
    """Widget for previewing PDF files"""
    
    def __init__(self, parent=None, translator: TranslationManager = None):
        super().__init__(parent)
        self.translator = translator or TranslationManager(None)
        self.current_pdf_path = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup PDF preview UI"""
        layout = QVBoxLayout(self)
        
        # PDF preview area (simplified - would need pdf rendering library for full preview)
        self.preview_label = QLabel(self.translator.tr('lbl_pdf_preview'))
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet(AppStyles.get_component_style('pdf_preview_placeholder'))
        layout.addWidget(self.preview_label)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.open_btn = QPushButton(self.translator.tr('btn_open_file'))
        self.open_btn.setStyleSheet(AppStyles.get_button_style('primary'))
        self.open_btn.clicked.connect(self.open_pdf)
        controls_layout.addWidget(self.open_btn)
        
        self.download_btn = QPushButton(self.translator.tr('btn_download_file'))
        self.download_btn.setStyleSheet(AppStyles.get_button_style('default'))
        self.download_btn.clicked.connect(self.download_pdf)
        controls_layout.addWidget(self.download_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
    
    def load_pdf(self, pdf_path: str):
        """Load PDF file info"""
        if not os.path.exists(pdf_path):
            QMessageBox.warning(self, self.translator.tr('msg_error'), 
                              self.translator.tr('msg_file_not_found'))
            return False
        
        try:
            file_size = os.path.getsize(pdf_path) / 1024  # KB
            file_name = os.path.basename(pdf_path)
            
            info_text = f"""
            <h3>{self.translator.tr('lbl_pdf_preview')}</h3>
            <p><b>{self.translator.tr('lbl_name')}:</b> {file_name}</p>
            <p><b>Size:</b> {file_size:.2f} KB</p>
            <p><i>{self.translator.tr('msg_no_preview_available')}</i></p>
            <p>Click "{self.translator.tr('btn_open_file')}" to open with external viewer</p>
            """
            self.preview_label.setText(info_text)
            self.current_pdf_path = pdf_path
            return True
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
            return False
    
    def open_pdf(self):
        """Open PDF file"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            self.translator.tr('btn_open_file'),
            "",
            "PDF Files (*.pdf);;All Files (*)"
        )
        if filename:
            self.load_pdf(filename)
            # Try to open with system default viewer
            try:
                import subprocess
                import platform
                if platform.system() == 'Windows':
                    os.startfile(filename)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', filename])
                else:  # Linux
                    subprocess.run(['xdg-open', filename])
            except Exception:
                pass
    
    def download_pdf(self):
        """Download/save current PDF"""
        if not self.current_pdf_path:
            QMessageBox.warning(self, self.translator.tr('msg_warning'), 
                              self.translator.tr('msg_no_preview_available'))
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.translator.tr('btn_download_file'),
            os.path.basename(self.current_pdf_path),
            "PDF Files (*.pdf);;All Files (*)"
        )
        if filename:
            try:
                from shutil import copyfile
                copyfile(self.current_pdf_path, filename)
                QMessageBox.information(self, self.translator.tr('msg_success'), 
                                      "File saved successfully")
            except Exception as e:
                QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))


class DocumentPreviewWidget(QWidget):
    """Widget for previewing text documents"""
    
    def __init__(self, parent=None, translator: TranslationManager = None):
        super().__init__(parent)
        self.translator = translator or TranslationManager(None)
        self.current_doc_path = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup document preview UI"""
        layout = QVBoxLayout(self)
        
        # Text preview area
        from PyQt5.QtWidgets import QTextEdit
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        self.text_preview.setPlaceholderText(self.translator.tr('lbl_document_preview'))
        self.text_preview.setStyleSheet(AppStyles.get_component_style('document_preview'))
        layout.addWidget(self.text_preview)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.open_btn = QPushButton(self.translator.tr('btn_open_file'))
        self.open_btn.setStyleSheet(AppStyles.get_button_style('primary'))
        self.open_btn.clicked.connect(self.open_document)
        controls_layout.addWidget(self.open_btn)
        
        self.download_btn = QPushButton(self.translator.tr('btn_download_file'))
        self.download_btn.setStyleSheet(AppStyles.get_button_style('default'))
        self.download_btn.clicked.connect(self.download_document)
        controls_layout.addWidget(self.download_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
    
    def load_document(self, doc_path: str, max_lines: int = 1000):
        """Load and preview text document"""
        if not os.path.exists(doc_path):
            QMessageBox.warning(self, self.translator.tr('msg_error'), 
                              self.translator.tr('msg_file_not_found'))
            return False
        
        try:
            # Try to read text content
            with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[:max_lines]
                content = ''.join(lines)
                if len(lines) == max_lines:
                    content += "\n... (truncated)"
            
            self.text_preview.setPlainText(content)
            self.current_doc_path = doc_path
            return True
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
            return False
    
    def open_document(self):
        """Open document file dialog"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            self.translator.tr('btn_open_file'),
            "",
            "Text Files (*.txt *.md *.log *.csv);;All Files (*)"
        )
        if filename:
            self.load_document(filename)
    
    def download_document(self):
        """Download/save current document"""
        if not self.current_doc_path:
            QMessageBox.warning(self, self.translator.tr('msg_warning'), 
                              self.translator.tr('msg_no_preview_available'))
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.translator.tr('btn_download_file'),
            os.path.basename(self.current_doc_path),
            "Text Files (*.txt);;All Files (*)"
        )
        if filename:
            try:
                from shutil import copyfile
                copyfile(self.current_doc_path, filename)
                QMessageBox.information(self, self.translator.tr('msg_success'), 
                                      "File saved successfully")
            except Exception as e:
                QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))


class AttachmentPreviewDialog(QWidget):
    """Main dialog for previewing all attachment types"""
    
    def __init__(self, parent=None, translator: TranslationManager = None):
        super().__init__(parent)
        self.translator = translator or TranslationManager(None)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup preview dialog UI"""
        from PyQt5.QtWidgets import QTabWidget
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel(self.translator.tr('lbl_preview_attachments'))
        title.setStyleSheet(AppStyles.get_component_style('preview_title'))
        layout.addWidget(title)
        
        # Tab widget for different preview types
        self.tab_widget = QTabWidget()
        
        self.image_preview = ImagePreviewWidget(self, self.translator)
        self.tab_widget.addTab(self.image_preview, "🖼️ " + self.translator.tr('lbl_image_preview'))
        
        self.pdf_preview = PDFPreviewWidget(self, self.translator)
        self.tab_widget.addTab(self.pdf_preview, "📄 " + self.translator.tr('lbl_pdf_preview'))
        
        self.doc_preview = DocumentPreviewWidget(self, self.translator)
        self.tab_widget.addTab(self.doc_preview, "📝 " + self.translator.tr('lbl_document_preview'))
        
        layout.addWidget(self.tab_widget)
    
    def preview_file(self, file_path: str):
        """Preview a file based on its extension"""
        if not os.path.exists(file_path):
            QMessageBox.warning(self, self.translator.tr('msg_error'), 
                              self.translator.tr('msg_file_not_found'))
            return
        
        ext = Path(file_path).suffix.lower()
        
        if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp']:
            self.tab_widget.setCurrentIndex(0)
            self.image_preview.load_image(file_path)
        elif ext == '.pdf':
            self.tab_widget.setCurrentIndex(1)
            self.pdf_preview.load_pdf(file_path)
        elif ext in ['.txt', '.md', '.log', '.csv']:
            self.tab_widget.setCurrentIndex(2)
            self.doc_preview.load_document(file_path)
        else:
            QMessageBox.information(self, self.translator.tr('msg_warning'), 
                                  self.translator.tr('msg_no_preview_available'))
