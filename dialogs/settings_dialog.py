"""
Settings Dialog with Language, Theme, and Accessibility Selection
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QPushButton,
    QComboBox, QLabel, QTabWidget, QWidget, QMessageBox, QCheckBox,
    QSpinBox, QSlider, QGroupBox, QApplication, QButtonGroup
)
from icons.icon_manager import setup_icon_button
from PyQt5.QtCore import Qt
from translations.translations import TranslationManager
from config.config_manager import ConfigManager
from styles.styles import AppStyles
from utils.logger import get_logger

logger = get_logger(__name__)


class SettingsDialog(QDialog):
    """Settings dialog for application configuration"""
    
    def __init__(self, parent, translator: TranslationManager):
        super().__init__(parent)
        self.translator = translator
        self.config = ConfigManager()
        self.parent_window = parent
        self._original_theme = AppStyles.get_current_theme()
        self.setWindowTitle(self.translator.tr('settings_title'))
        # Apply fixed size to prevent resizing on button clicks or content changes
        AppStyles.apply_fixed_size(self, 550, 550)
        self._apply_rtl_direction()
        self.setup_ui()
        self.load_settings()
        self._apply_rtl_direction()
    
    def _apply_rtl_direction(self):
        """Apply RTL/LTR direction based on current language"""
        is_rtl = self.translator.current_language == 'ar'
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        self.setLayoutDirection(direction)
        for child in self.findChildren(QWidget):
            child.setLayoutDirection(direction)
    
    def setup_ui(self):
        """Setup settings UI with scrollable tabs"""
        from PyQt5.QtWidgets import QScrollArea
        
        layout = QVBoxLayout(self)
        m = AppStyles.get_spacing(2)
        layout.setContentsMargins(m, m, m, m)
        layout.setSpacing(AppStyles.get_spacing(2))
        is_rtl = self.translator.current_language == 'ar'
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # Helper function to create scrollable tab content
        def create_scrollable_tab():
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll.setFrameShape(scroll.NoFrame)
            scroll.setStyleSheet(AppStyles.get_component_style('settings_scroll'))
            content = QWidget()
            scroll.setWidget(content)
            return scroll, content
        
        # General tab with scroll
        general_scroll, general_tab = create_scrollable_tab()
        general_layout = QFormLayout(general_tab)
        AppStyles.apply_form_layout_for_language(general_layout, is_rtl)
        
        # Language
        self.language_combo = QComboBox()
        available_langs = self.translator.get_available_languages()
        lang_names = {'en': 'English', 'ar': 'العربية (Arabic)', 'tr': 'Türkçe (Turkish)'}
        for lang_code in available_langs:
            lang_name = lang_names.get(lang_code, lang_code.upper())
            self.language_combo.addItem(lang_name, lang_code)
        
        general_layout.addRow(self.translator.tr('settings_language') + ":", self.language_combo)
        
        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItem(self.translator.tr('settings_theme_light'), 'light')
        self.theme_combo.addItem(self.translator.tr('settings_theme_dark'), 'dark')
        self.theme_combo.currentIndexChanged.connect(self._preview_theme)
        
        general_layout.addRow(self.translator.tr('lbl_theme') + ":", self.theme_combo)
        
        # Font size
        font_layout = QHBoxLayout()
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 16)
        self.font_size_spin.setValue(10)
        self.font_size_spin.setSuffix(" " + self.translator.tr('settings_points'))
        font_layout.addWidget(self.font_size_spin)
        font_layout.addStretch()
        
        general_layout.addRow(self.translator.tr('settings_font_size') if hasattr(self.translator, 'tr') else "Font Size:", font_layout)
        
        # Timeline density mode
        density_layout = QHBoxLayout()
        self.density_mode_group = QButtonGroup(self)
        density_modes = ['compact', 'comfortable', 'expansive']
        self.density_buttons = []
        for mode in density_modes:
            btn = QPushButton(self.translator.tr(f'timeline_density_{mode}') if hasattr(self.translator, 'tr') else mode.title())
            btn.setCheckable(True)
            btn.setMinimumWidth(100)
            density_layout.addWidget(btn)
            self.density_buttons.append(btn)
            self.density_mode_group.addButton(btn)
        
        general_layout.addRow(
            self.translator.tr('timeline_density_mode') if hasattr(self.translator, 'tr') else "Timeline Density Mode:",
            density_layout
        )
        
        tab_widget.addTab(general_scroll, self.translator.tr('settings_general'))
        
        # Accessibility tab with scroll
        accessibility_scroll, accessibility_tab = create_scrollable_tab()
        accessibility_layout = QVBoxLayout(accessibility_tab)
        
        # Visual accessibility group
        visual_group = QGroupBox(self.translator.tr('settings_visual') if hasattr(self.translator, 'tr') else "Visual Accessibility")
        visual_layout = QFormLayout(visual_group)
        AppStyles.apply_form_layout_for_language(visual_layout, is_rtl)
        
        # High contrast mode
        self.high_contrast_check = QCheckBox()
        visual_layout.addRow(
            self.translator.tr('settings_high_contrast') if hasattr(self.translator, 'tr') else "High Contrast Mode:",
            self.high_contrast_check
        )
        
        # Font size multiplier
        multiplier_layout = QHBoxLayout()
        self.font_multiplier_slider = QSlider(Qt.Horizontal)
        self.font_multiplier_slider.setRange(100, 200)
        self.font_multiplier_slider.setValue(100)
        self.font_multiplier_slider.setTickPosition(QSlider.TicksBelow)
        self.font_multiplier_slider.setTickInterval(25)
        
        self.font_multiplier_label = QLabel("100%")
        self.font_multiplier_slider.valueChanged.connect(
            lambda v: self.font_multiplier_label.setText(f"{v}%")
        )
        
        multiplier_layout.addWidget(self.font_multiplier_slider)
        multiplier_layout.addWidget(self.font_multiplier_label)
        
        visual_layout.addRow(
            self.translator.tr('settings_font_scale') if hasattr(self.translator, 'tr') else "Font Scale:",
            multiplier_layout
        )
        
        # Color blind mode
        self.color_blind_combo = QComboBox()
        self.color_blind_combo.addItem(self.translator.tr('settings_none'), 'none')
        self.color_blind_combo.addItem(self.translator.tr('settings_protanopia'), 'protanopia')
        self.color_blind_combo.addItem(self.translator.tr('settings_deuteranopia'), 'deuteranopia')
        self.color_blind_combo.addItem(self.translator.tr('settings_tritanopia'), 'tritanopia')
        
        visual_layout.addRow(
            self.translator.tr('settings_color_blind') if hasattr(self.translator, 'tr') else "Color Blind Mode:",
            self.color_blind_combo
        )
        
        accessibility_layout.addWidget(visual_group)
        
        # Keyboard accessibility group
        keyboard_group = QGroupBox(self.translator.tr('settings_keyboard') if hasattr(self.translator, 'tr') else "Keyboard Accessibility")
        keyboard_layout = QFormLayout(keyboard_group)
        AppStyles.apply_form_layout_for_language(keyboard_layout, is_rtl)
        
        # Keyboard navigation hints
        self.keyboard_hints_check = QCheckBox()
        self.keyboard_hints_check.setChecked(True)
        keyboard_layout.addRow(
            self.translator.tr('settings_keyboard_hints') if hasattr(self.translator, 'tr') else "Show Keyboard Shortcuts:",
            self.keyboard_hints_check
        )
        
        # Focus indicator
        self.focus_indicator_check = QCheckBox()
        self.focus_indicator_check.setChecked(True)
        keyboard_layout.addRow(
            self.translator.tr('settings_focus_indicator') if hasattr(self.translator, 'tr') else "Enhanced Focus Indicator:",
            self.focus_indicator_check
        )
        
        accessibility_layout.addWidget(keyboard_group)
        
        # Screen reader group
        screen_reader_group = QGroupBox(self.translator.tr('settings_screen_reader') if hasattr(self.translator, 'tr') else "Screen Reader Support")
        screen_reader_layout = QFormLayout(screen_reader_group)
        AppStyles.apply_form_layout_for_language(screen_reader_layout, is_rtl)
        
        self.screen_reader_check = QCheckBox()
        screen_reader_layout.addRow(
            self.translator.tr('settings_screen_reader_support') if hasattr(self.translator, 'tr') else "Enable Screen Reader Support:",
            self.screen_reader_check
        )
        
        accessibility_layout.addWidget(screen_reader_group)
        accessibility_layout.addStretch()
        
        tab_widget.addTab(accessibility_scroll, self.translator.tr('settings_accessibility') if hasattr(self.translator, 'tr') else "Accessibility")
        
        # Performance tab with scroll
        performance_scroll, performance_tab = create_scrollable_tab()
        performance_layout = QVBoxLayout(performance_tab)
        
        perf_group = QGroupBox(self.translator.tr('settings_performance') if hasattr(self.translator, 'tr') else "Performance Settings")
        perf_form = QFormLayout(perf_group)
        AppStyles.apply_form_layout_for_language(perf_form, is_rtl)
        
        # Page size
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(['25', '50', '100', '200', '500'])
        self.page_size_combo.setCurrentText('50')
        perf_form.addRow(
            self.translator.tr('settings_page_size') if hasattr(self.translator, 'tr') else "Default Page Size:",
            self.page_size_combo
        )
        
        # Auto-save
        self.auto_save_check = QCheckBox()
        self.auto_save_check.setChecked(True)
        perf_form.addRow(
            self.translator.tr('settings_auto_save') if hasattr(self.translator, 'tr') else "Auto-save Drafts:",
            self.auto_save_check
        )
        
        # Auto-save interval
        interval_layout = QHBoxLayout()
        self.auto_save_interval = QSpinBox()
        self.auto_save_interval.setRange(30, 600)
        self.auto_save_interval.setValue(300)
        self.auto_save_interval.setSuffix(" " + self.translator.tr('settings_seconds'))
        interval_layout.addWidget(self.auto_save_interval)
        interval_layout.addStretch()
        
        perf_form.addRow(
            self.translator.tr('settings_auto_save_interval') if hasattr(self.translator, 'tr') else "Auto-save Interval:",
            interval_layout
        )
        
        performance_layout.addWidget(perf_group)
        performance_layout.addStretch()
        
        tab_widget.addTab(performance_scroll, self.translator.tr('settings_performance') if hasattr(self.translator, 'tr') else "Performance")
        
        layout.addWidget(tab_widget)
        
        # Buttons - properly aligned in a single row
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment
        btn_layout.setSpacing(AppStyles.get_spacing(2))  # 16px - 8px grid spacing
        btn_layout.addStretch()
        
        btn_reset = QPushButton(self.translator.tr('btn_reset') if hasattr(self.translator, 'tr') else "Reset to Defaults")
        # Disable autoDefault to prevent Enter key from triggering buttons unexpectedly
        btn_reset.setAutoDefault(False)
        btn_reset.setDefault(False)
        btn_reset.clicked.connect(self.reset_to_defaults)
        btn_layout.addWidget(btn_reset, alignment=Qt.AlignVCenter)
        
        btn_save = QPushButton()
        setup_icon_button(btn_save, 'btn_save', self.translator.tr('btn_save'))
        btn_save.setAutoDefault(False)
        btn_save.setDefault(False)
        btn_save.clicked.connect(self.save_settings)
        
        btn_cancel = QPushButton()
        setup_icon_button(btn_cancel, 'btn_cancel', self.translator.tr('btn_cancel'))
        btn_cancel.setAutoDefault(False)
        btn_cancel.setDefault(False)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_save, alignment=Qt.AlignVCenter)
        btn_layout.addWidget(btn_cancel, alignment=Qt.AlignVCenter)
        layout.addLayout(btn_layout)
    
    def _preview_theme(self):
        """Preview theme when selection changes"""
        selected_theme = self.theme_combo.currentData()
        if selected_theme:
            # Apply theme preview
            AppStyles.set_theme(selected_theme)
            if self.parent_window:
                self.parent_window.setStyleSheet(AppStyles.get_stylesheet())
                if hasattr(self.parent_window, 'refresh_menu_icons'):
                    self.parent_window.refresh_menu_icons()
            self.setStyleSheet(AppStyles.get_stylesheet())
            
            # Apply to application
            app = QApplication.instance()
            if app:
                AppStyles.apply_theme_to_app(app)
    
    def load_settings(self):
        """Load current settings"""
        try:
            # Load language
            current_lang = self.config.get('Application', 'language', 'en')
            index = self.language_combo.findData(current_lang)
            if index >= 0:
                self.language_combo.setCurrentIndex(index)
            
            # Load theme
            current_theme = self.config.get('Application', 'theme', 'light')
            index = self.theme_combo.findData(current_theme)
            if index >= 0:
                self.theme_combo.setCurrentIndex(index)
            
            # Load font size
            font_size = self.config.get('Application', 'font_size', 10)
            self.font_size_spin.setValue(int(font_size))
            
            # Load timeline density mode
            density_mode = self.config.get_timeline_density_mode()
            density_modes = ['compact', 'comfortable', 'expansive']
            if density_mode in density_modes and hasattr(self, 'density_buttons'):
                idx = density_modes.index(density_mode)
                if idx < len(self.density_buttons):
                    self.density_buttons[idx].setChecked(True)
            
            # Load accessibility settings
            high_contrast = self.config.get('Accessibility', 'high_contrast', False)
            self.high_contrast_check.setChecked(bool(high_contrast))

            focus_indicator = self.config.get('Accessibility', 'focus_indicator', True)
            self.focus_indicator_check.setChecked(bool(focus_indicator))
            
            font_multiplier = self.config.get('Accessibility', 'font_size_multiplier', 1.0)
            self.font_multiplier_slider.setValue(int(float(font_multiplier) * 100))
            
            color_blind_mode = self.config.get('Accessibility', 'color_blind_mode', 'none')
            index = self.color_blind_combo.findData(color_blind_mode)
            if index >= 0:
                self.color_blind_combo.setCurrentIndex(index)
            else:
                # Older configurations used a boolean false value for the
                # disabled color-blind mode.
                self.color_blind_combo.setCurrentIndex(0)
            
            keyboard_nav = self.config.get('Accessibility', 'keyboard_navigation', True)
            self.keyboard_hints_check.setChecked(bool(keyboard_nav))
            
            screen_reader = self.config.get('Accessibility', 'screen_reader_support', True)
            self.screen_reader_check.setChecked(bool(screen_reader))
            
            # Load performance settings
            auto_save = self.config.get('Application', 'auto_save', True)
            self.auto_save_check.setChecked(bool(auto_save))
            
            auto_save_interval = self.config.get('Application', 'auto_save_interval', 300)
            self.auto_save_interval.setValue(int(auto_save_interval))

            page_size = self.config.get('Application', 'page_size', 50)
            if self.page_size_combo.findText(str(page_size)) < 0:
                page_size = 50
            self.page_size_combo.setCurrentText(str(page_size))
            
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings"""
        try:
            # Save language
            selected_lang = self.language_combo.currentData()
            if selected_lang:
                self.config.set('Application', 'language', selected_lang)
                self.translator.set_language(selected_lang)
            
            # Save theme
            selected_theme = self.theme_combo.currentData()
            if selected_theme:
                self.config.set('Application', 'theme', selected_theme)
                AppStyles.set_theme(selected_theme)
                
                # Apply theme to main window and all dialogs
                if self.parent_window:
                    self.parent_window.setStyleSheet(AppStyles.get_stylesheet())
                
                # Apply to application palette
                app = QApplication.instance()
                if app:
                    AppStyles.apply_theme_to_app(app)
            
            # Save font size
            font_size = self.font_size_spin.value()
            self.config.set('Application', 'font_size', font_size)
            AppStyles.FONT_SIZE = font_size
            
            # Save timeline density mode
            if hasattr(self, 'density_buttons'):
                for i, btn in enumerate(self.density_buttons):
                    if btn.isChecked():
                        density_modes = ['compact', 'comfortable', 'expansive']
                        if i < len(density_modes):
                            self.config.set_timeline_density_mode(density_modes[i])
                        break
            
            # Save accessibility settings
            self.config.set('Accessibility', 'high_contrast', self.high_contrast_check.isChecked())
            self.config.set('Accessibility', 'font_size_multiplier', self.font_multiplier_slider.value() / 100.0)
            self.config.set('Accessibility', 'color_blind_mode', self.color_blind_combo.currentData())
            self.config.set('Accessibility', 'keyboard_navigation', self.keyboard_hints_check.isChecked())
            self.config.set('Accessibility', 'focus_indicator', self.focus_indicator_check.isChecked())
            self.config.set('Accessibility', 'screen_reader_support', self.screen_reader_check.isChecked())
            
            # Save performance settings
            self.config.set('Application', 'auto_save', self.auto_save_check.isChecked())
            self.config.set('Application', 'auto_save_interval', self.auto_save_interval.value())
            self.config.set('Application', 'page_size', int(self.page_size_combo.currentText()))

            # Make the updated accessibility preference effective immediately.
            try:
                from utils.accessibility import get_accessibility_manager
                get_accessibility_manager().update_settings()
            except Exception as accessibility_error:
                logger.warning(f"Could not refresh accessibility settings: {accessibility_error}")
            
            # Save all settings to JSON
            self.config.save_all_to_json()
            
            QMessageBox.information(
                self,
                self.translator.tr('msg_success'),
                self.translator.tr('msg_settings_saved')
            )
            
            self.accept()
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(
                self,
                self.translator.tr('msg_error'),
                f"Error saving settings: {e}"
            )
    
    def reject(self):
        """Close without saving and restore any previewed theme."""
        if AppStyles.get_current_theme() != self._original_theme:
            AppStyles.set_theme(self._original_theme)
            app = QApplication.instance()
            if app:
                AppStyles.apply_theme_to_app(app)
            if self.parent_window:
                self.parent_window.setStyleSheet(AppStyles.get_stylesheet())
                if hasattr(self.parent_window, 'refresh_menu_icons'):
                    self.parent_window.refresh_menu_icons()
        super().reject()

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(
            self,
            self.translator.tr('msg_confirm') if hasattr(self.translator, 'tr') else 'Confirm',
            self.translator.tr('settings_reset_confirm') if hasattr(self.translator, 'tr') else 'Reset all settings to defaults?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Reset to defaults
            self.language_combo.setCurrentIndex(self.language_combo.findData('en'))
            self.theme_combo.setCurrentIndex(self.theme_combo.findData('light'))
            self.font_size_spin.setValue(10)
            self.high_contrast_check.setChecked(False)
            self.font_multiplier_slider.setValue(100)
            self.color_blind_combo.setCurrentIndex(0)
            self.keyboard_hints_check.setChecked(True)
            self.focus_indicator_check.setChecked(True)
            self.screen_reader_check.setChecked(True)
            self.auto_save_check.setChecked(True)
            self.auto_save_interval.setValue(300)
            self.page_size_combo.setCurrentText('50')
