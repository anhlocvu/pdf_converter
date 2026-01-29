import wx
import os
import threading
from .pdf_viewer import PDFViewer
from .converter import ConverterLogic
from . import config
from .i18n import _
import modules.i18n as i18n

APP_VERSION = "2.0"
APP_TITLE = f"{_('PDF Converter, version: ')} {APP_VERSION}"

# Dark Theme Colors
COLOR_BG = "#2E2E2E" # Dark Grey
COLOR_FG = "#FFFFFF" # White
COLOR_ACCENT = "#007ACC" # Blue
COLOR_PANEL = "#3C3C3C" # Components BG
COLOR_BUTTON = "#505050" 

class DarkPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.SetBackgroundColour(COLOR_BG)
        self.SetForegroundColour(COLOR_FG)

class SettingsDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title=_("Settings"), size=(400, 300))
        self.SetBackgroundColour(COLOR_BG)
        self.SetForegroundColour(COLOR_FG)
        
        # Notebook for Tabs
        notebook = wx.Notebook(self)
        
        # General Tab
        general_panel = wx.Panel(notebook)
        general_panel.SetBackgroundColour(COLOR_BG)
        general_panel.SetForegroundColour(COLOR_FG)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Language Selection
        lbl_lang = wx.StaticText(general_panel, label=_("Language:"))
        lbl_lang.SetForegroundColour(COLOR_FG)
        vbox.Add(lbl_lang, 0, wx.ALL, 10)
        
        self.languages = i18n.get_available_languages()
        current_lang = config.get_language()
        
        self.combo_lang = wx.ComboBox(general_panel, choices=self.languages, style=wx.CB_READONLY)
        if current_lang in self.languages:
            self.combo_lang.SetSelection(self.languages.index(current_lang))
        else:
            self.combo_lang.SetSelection(0) # Default to first (en)
            
        vbox.Add(self.combo_lang, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        
        general_panel.SetSizer(vbox)
        notebook.AddPage(general_panel, _("General"))
        
        # Main Layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 10)
        
        # Buttons
        btns = wx.BoxSizer(wx.HORIZONTAL)
        btn_save = wx.Button(self, wx.ID_OK, label=_("Save"))
        btn_cancel = wx.Button(self, wx.ID_CANCEL, label=_("Cancel"))
        
        btns.Add(btn_save, 1, wx.RIGHT, 10)
        btns.Add(btn_cancel, 1)
        
        main_sizer.Add(btns, 0, wx.EXPAND | wx.ALL, 10)
        
        self.SetSizer(main_sizer)
        self.CenterOnParent()

    def get_selected_language(self):
        idx = self.combo_lang.GetSelection()
        if idx != wx.NOT_FOUND:
            return self.languages[idx]
        return 'en'

class ConversionProgressDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title=_("Converting..."), size=(400, 300), style=wx.CAPTION)
        self.SetBackgroundColour(COLOR_BG)
        self.SetForegroundColour(COLOR_FG)
        
        panel = wx.Panel(self)
        panel.SetBackgroundColour(COLOR_BG)
        panel.SetForegroundColour(COLOR_FG)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        lbl = wx.StaticText(panel, label=_("Conversion in Progress"))
        lbl.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        lbl.SetForegroundColour(COLOR_FG)
        vbox.Add(lbl, 0, wx.ALL | wx.ALIGN_CENTER, 15)
        
        # Log Box
        self.log_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.log_text.SetBackgroundColour(COLOR_PANEL)
        self.log_text.SetForegroundColour(COLOR_FG)
        vbox.Add(self.log_text, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)
        
        panel.SetSizer(vbox)
        self.CenterOnParent()

    def append_log(self, msg):
        wx.CallAfter(self.log_text.AppendText, msg + "\n")

class ConvertOptionsDialog(wx.Dialog):
    def __init__(self, parent, default_path):
        super().__init__(parent, title=_("Conversion Options"), size=(450, 300))
        self.SetBackgroundColour(COLOR_BG)
        self.SetForegroundColour(COLOR_FG)
        
        panel = wx.Panel(self)
        panel.SetBackgroundColour(COLOR_BG)
        panel.SetForegroundColour(COLOR_FG)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # --- Format Section ---
        lbl_fmt = wx.StaticText(panel, label=_("Select Output Format:"))
        lbl_fmt.SetForegroundColour(COLOR_FG)
        vbox.Add(lbl_fmt, 0, wx.LEFT | wx.RIGHT | wx.TOP, 15)
        
        self.combo_format = wx.ComboBox(panel, choices=["TXT", "HTML", "DOCX"], style=wx.CB_READONLY)
        self.combo_format.SetSelection(0)
        vbox.Add(self.combo_format, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 15)
        
        # --- Output Path Section ---
        lbl_path = wx.StaticText(panel, label=_("Output Folder:"))
        lbl_path.SetForegroundColour(COLOR_FG)
        vbox.Add(lbl_path, 0, wx.LEFT | wx.RIGHT | wx.TOP, 15)
        
        hbox_path = wx.BoxSizer(wx.HORIZONTAL)
        self.txt_path = wx.TextCtrl(panel, value=default_path)
        self.txt_path.SetBackgroundColour(COLOR_PANEL)
        self.txt_path.SetForegroundColour(COLOR_FG)
        
        btn_browse = wx.Button(panel, label=_("Browse..."))
        btn_browse.Bind(wx.EVT_BUTTON, self.on_browse)
        
        hbox_path.Add(self.txt_path, 1, wx.RIGHT, 5)
        hbox_path.Add(btn_browse, 0)
        
        vbox.Add(hbox_path, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 15)
        
        # --- Buttons ---
        vbox.AddStretchSpacer(1)
        hbox_btns = wx.BoxSizer(wx.HORIZONTAL)
        btn_convert = wx.Button(panel, wx.ID_OK, label=_("Convert"))
        btn_cancel = wx.Button(panel, wx.ID_CANCEL, label="Cancel")
        
        btn_convert.SetDefault()
        
        hbox_btns.Add(btn_convert, 1, wx.RIGHT, 10)
        hbox_btns.Add(btn_cancel, 1)
        
        vbox.Add(hbox_btns, 0, wx.EXPAND | wx.ALL, 15)
        
        panel.SetSizer(vbox)
        self.CenterOnParent()

    def on_browse(self, event):
        with wx.DirDialog(self, "Select Output Directory", self.txt_path.GetValue(),
                          style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.txt_path.SetValue(dlg.GetPath())

    def get_settings(self):
        return {
            "format": self.combo_format.GetValue().lower(),
            "path": self.txt_path.GetValue()
        }

class AboutDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="About", size=(400, 350))
        self.SetBackgroundColour(COLOR_BG)
        self.SetForegroundColour(COLOR_FG)
        
        panel = wx.Panel(self)
        panel.SetBackgroundColour(COLOR_BG)
        panel.SetForegroundColour(COLOR_FG)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Content
        about_text = (
            _("You want to read a PDF file, but you don't have Word?\n") +
            _("Or you need to convert a PDF file to various formats?\n\n") +
            _("There is only PDF Converter.\n") +
            _("PDF Converter is a versatile software that helps users view and extract text easily.\n\n") +
            _("Version and Development Info:\n\n") +
            f"{_('Version, ')} {APP_VERSION}\n\n" +
            _("Developer: Technology Entertainment Studio.")
        )
        
        txt_info = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_CENTER)
        txt_info.SetBackgroundColour(COLOR_PANEL)
        txt_info.SetForegroundColour(COLOR_FG)
        txt_info.SetValue(about_text)
        
        vbox.Add(txt_info, 1, wx.EXPAND | wx.ALL, 15)
        
        # Close Button
        btn_close = wx.Button(panel, wx.ID_CANCEL, label="Close")
        vbox.Add(btn_close, 0, wx.ALIGN_CENTER | wx.BOTTOM, 15)
        
        panel.SetSizer(vbox)
        self.CenterOnParent()

class MainFrame(wx.Frame):
    def __init__(self):
        # We use the key "APP_TITLE" to match the JSON file and format it with version
        super().__init__(None, title=_("APP_TITLE").format(APP_VERSION), size=(900, 700))
        self.SetBackgroundColour(COLOR_BG)
        
        self.viewer = None
        self.logic = ConverterLogic()
        self.selected_file = None
        self.progress_dialog = None
        
        self.init_ui()
        self.Center()
        self.Show()

    def init_ui(self):
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # --- Menu Bar ---
        menubar = wx.MenuBar()
        
        # File Menu
        file_menu = wx.Menu()
        self.m_open = file_menu.Append(wx.ID_OPEN, _("&Open PDF\tCtrl+O"), _("Open a PDF file for reading"))
        self.m_close = file_menu.Append(wx.ID_CLOSE, _("Close PDF\tCtrl+F4"), _("Close the current PDF"))
        self.m_close.Enable(False) # Initially disabled
        file_menu.AppendSeparator()
        self.m_exit = file_menu.Append(wx.ID_EXIT, _("E&xit\tAlt+F4"), _("Exit the application"))
        
        # Tools Menu
        tools_menu = wx.Menu()
        self.m_convert = tools_menu.Append(wx.ID_ANY, _("&Convert Options...\tAlt+C"), _("Open conversion options"))
        self.m_convert.Enable(False)
        tools_menu.AppendSeparator()
        self.m_options = tools_menu.Append(wx.ID_ANY, _("&Options...\tF4"), _("Open application options"))
        
        # Help Menu
        help_menu = wx.Menu()
        self.m_about = help_menu.Append(wx.ID_ABOUT, _("&About...\tF1"), _("About this application"))
        
        menubar.Append(file_menu, _("&File"))
        menubar.Append(tools_menu, _("&Tools"))
        menubar.Append(help_menu, _("&Help"))
        self.SetMenuBar(menubar)
        
        # Bind Events
        self.Bind(wx.EVT_MENU, self.on_select_file, self.m_open)
        self.Bind(wx.EVT_MENU, self.on_close_pdf, self.m_close)
        self.Bind(wx.EVT_MENU, self.on_exit, self.m_exit)
        self.Bind(wx.EVT_MENU, self.on_convert_options, self.m_convert)
        self.Bind(wx.EVT_MENU, self.on_options, self.m_options)
        self.Bind(wx.EVT_MENU, self.on_about, self.m_about)

        # --- Preview Area (Accessible Text Box) ---
        self.preview_text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        self.preview_text.SetBackgroundColour(COLOR_PANEL)
        self.preview_text.SetForegroundColour(COLOR_FG)
        self.preview_text.SetFont(wx.Font(11, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.preview_text.SetValue(_("Welcome. Press Ctrl+O to open a PDF file."))
        
        # --- Status Bar ---
        self.status_bar = self.CreateStatusBar()
        self.status_bar.SetBackgroundColour(COLOR_BG)
        self.status_bar.SetForegroundColour(COLOR_FG)
        self.status_bar.SetStatusText(_("Ready - Please select a PDF file."))

        # Layout
        self.main_sizer.Add(self.preview_text, 1, wx.EXPAND | wx.ALL, 10)
        
        self.SetSizer(self.main_sizer)

    def on_exit(self, event):
        self.Close()

    def on_about(self, event):
        dlg = AboutDialog(self)
        dlg.ShowModal()
        dlg.Destroy()

    def on_options(self, event):
        dlg = SettingsDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            lang = dlg.get_selected_language()
            if lang != config.get_language():
                config.set_language(lang)
                wx.MessageBox(_("Please restart the application to apply language changes."), 
                              _("Restart Required"), wx.ICON_INFORMATION)
        dlg.Destroy()

    def on_select_file(self, event):
        with wx.FileDialog(self, "Open PDF", wildcard="PDF files (*.pdf)|*.pdf",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_CANCEL:
                return
            
            path = dlg.GetPath()
            self.selected_file = path
            self.load_preview(path)
            self.status_bar.SetStatusText(f"Loaded. Use Alt+C to convert.")
            self.preview_text.SetFocus() 
            self.update_menu_state(True)

    def on_close_pdf(self, event):
        # Close viewer
        if self.viewer:
            self.viewer.close()
            self.viewer = None
        
        # Reset state
        self.selected_file = None
        self.preview_text.SetValue("Welcome. Press Ctrl+O to open a PDF file.")
        
        # Update Menu
        self.update_menu_state(False)
        self.status_bar.SetStatusText("PDF Closed.")

    def update_menu_state(self, has_file):
        self.m_close.Enable(has_file)
        self.m_convert.Enable(has_file)

    def load_preview(self, path):
        self.status_bar.SetStatusText("Loading text preview...")
        self.preview_text.SetValue("Loading document... Please wait.")
        self.Update()
        
        try:
            if self.viewer:
                self.viewer.close()
            
            self.viewer = PDFViewer(path)
            text = self.viewer.get_text()
            
            self.preview_text.SetValue(text)
            self.status_bar.SetStatusText("Preview loaded.")
            
        except Exception as e:
            self.status_bar.SetStatusText("Error loading preview")
            self.preview_text.SetValue(f"Error reading PDF text: {str(e)}")
            wx.MessageBox(f"Failed to load PDF preview: {e}", "Error", wx.ICON_ERROR)

    def on_convert_options(self, event):
        if not self.selected_file:
            return
            
        default_dir = os.path.dirname(self.selected_file)
        dlg = ConvertOptionsDialog(self, default_dir)
        
        if dlg.ShowModal() == wx.ID_OK:
            settings = dlg.get_settings()
            dlg.Destroy()
            self.start_conversion(settings)
        else:
            dlg.Destroy()

    def start_conversion(self, settings):
        fmt = settings['format']
        output_dir = settings['path']
        
        # Hide Main Window
        self.Hide()
        
        # Show Progress Dialog
        self.progress_dialog = ConversionProgressDialog(self)
        self.progress_dialog.Show()
        self.progress_dialog.append_log(f"{_('Starting conversion of ')} {os.path.basename(self.selected_file)}...")
        self.progress_dialog.append_log(f"{_('Target format: ')} {fmt.upper()}")
        self.progress_dialog.append_log(f"{_('Output folder: ')} {output_dir}")
        
        # Start Thread
        thread = threading.Thread(target=self.run_conversion_thread, args=(fmt, output_dir))
        thread.start()

    def run_conversion_thread(self, fmt, output_dir):
        try:
            base_name = os.path.basename(self.selected_file)
            name_no_ext = os.path.splitext(base_name)[0]
            output_path = os.path.join(output_dir, f"{name_no_ext}.{fmt}")
            
            if self.progress_dialog:
                self.progress_dialog.append_log(_("Processing file..."))
            
            if fmt == "txt":
                self.logic.convert_to_txt(self.selected_file, output_path)
            elif fmt == "html":
                self.logic.convert_to_html(self.selected_file, output_path)
            elif fmt == "docx":
                self.logic.convert_to_docx(self.selected_file, output_path)
                
            wx.CallAfter(self.on_conversion_complete, output_path)
        except Exception as e:
            wx.CallAfter(self.on_conversion_error, str(e))

    def on_conversion_complete(self, output_path):
        if self.progress_dialog:
            self.progress_dialog.append_log("Conversion Finished!")
            self.progress_dialog.Destroy()
            self.progress_dialog = None
            
        wx.MessageBox(f"{_('Saved successfully to:')}\n{output_path}", _("Success"), wx.ICON_INFORMATION)
        self.Show()
        self.status_bar.SetStatusText("Ready")
        self.preview_text.SetFocus()

    def on_conversion_error(self, err_msg):
        if self.progress_dialog:
            self.progress_dialog.Destroy()
            self.progress_dialog = None
            
        wx.MessageBox(f"Conversion Error:\n{err_msg}", "Error", wx.ICON_ERROR)
        self.Show()
        self.status_bar.SetStatusText("Error")

    def __del__(self):
        if self.viewer:
            self.viewer.close()
