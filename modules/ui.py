import wx
import os
import threading
from .pdf_viewer import PDFViewer
from .converter import ConverterLogic

APP_VERSION = "2.0"
APP_TITLE = f"PDF Converter, version: {APP_VERSION}"

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

class ConversionProgressDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Converting...", size=(400, 300), style=wx.CAPTION)
        self.SetBackgroundColour(COLOR_BG)
        self.SetForegroundColour(COLOR_FG)
        
        panel = wx.Panel(self)
        panel.SetBackgroundColour(COLOR_BG)
        panel.SetForegroundColour(COLOR_FG)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        lbl = wx.StaticText(panel, label="Conversion in Progress")
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
    def __init__(self, parent):
        super().__init__(parent, title="Conversion Options", size=(350, 200))
        self.SetBackgroundColour(COLOR_BG)
        self.SetForegroundColour(COLOR_FG)
        
        panel = wx.Panel(self)
        panel.SetBackgroundColour(COLOR_BG)
        panel.SetForegroundColour(COLOR_FG)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Label
        lbl = wx.StaticText(panel, label="Select Output Format:")
        lbl.SetForegroundColour(COLOR_FG)
        vbox.Add(lbl, 0, wx.ALL, 15)
        
        # Combo
        self.combo_format = wx.ComboBox(panel, choices=["TXT", "HTML", "DOCX"], style=wx.CB_READONLY)
        self.combo_format.SetSelection(0)
        vbox.Add(self.combo_format, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)
        
        # Buttons
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        btn_convert = wx.Button(panel, wx.ID_OK, label="Convert")
        btn_cancel = wx.Button(panel, wx.ID_CANCEL, label="Cancel")
        
        btn_convert.SetDefault()
        
        hbox.Add(btn_convert, 1, wx.RIGHT, 10)
        hbox.Add(btn_cancel, 1)
        
        vbox.Add(hbox, 0, wx.EXPAND | wx.ALL, 15)
        
        panel.SetSizer(vbox)
        self.CenterOnParent()

    def get_format(self):
        return self.combo_format.GetValue().lower()

class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title=APP_TITLE, size=(900, 700))
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
        m_open = file_menu.Append(wx.ID_OPEN, "&Open PDF\tCtrl+O", "Open a PDF file for reading")
        file_menu.AppendSeparator()
        m_exit = file_menu.Append(wx.ID_EXIT, "E&xit\tAlt+F4", "Exit the application")
        
        # Tools Menu
        tools_menu = wx.Menu()
        m_convert = tools_menu.Append(wx.ID_ANY, "&Convert Options...\tAlt+C", "Open conversion options")
        
        menubar.Append(file_menu, "&File")
        menubar.Append(tools_menu, "&Tools")
        self.SetMenuBar(menubar)
        
        # Bind Events
        self.Bind(wx.EVT_MENU, self.on_select_file, m_open)
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)
        self.Bind(wx.EVT_MENU, self.on_convert_options, m_convert)

        # --- Preview Area (Accessible Text Box) ---
        self.preview_text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        self.preview_text.SetBackgroundColour(COLOR_PANEL)
        self.preview_text.SetForegroundColour(COLOR_FG)
        self.preview_text.SetFont(wx.Font(11, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.preview_text.SetValue("Welcome. Press Ctrl+O to open a PDF file.")
        
        # --- Status Bar ---
        self.status_bar = self.CreateStatusBar()
        self.status_bar.SetBackgroundColour(COLOR_BG)
        self.status_bar.SetForegroundColour(COLOR_FG)
        self.status_bar.SetStatusText("Ready")

        # Layout
        self.main_sizer.Add(self.preview_text, 1, wx.EXPAND | wx.ALL, 10)
        
        self.SetSizer(self.main_sizer)

    def on_exit(self, event):
        self.Close()

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
            wx.MessageBox("Please open a PDF file first (Ctrl+O).", "No File Selected", wx.ICON_WARNING)
            return
            
        dlg = ConvertOptionsDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            fmt = dlg.get_format()
            dlg.Destroy()
            self.start_conversion(fmt)
        else:
            dlg.Destroy()

    def start_conversion(self, fmt):
        # Hide Main Window
        self.Hide()
        
        # Show Progress Dialog
        self.progress_dialog = ConversionProgressDialog(self)
        self.progress_dialog.Show()
        self.progress_dialog.append_log(f"Starting conversion of {os.path.basename(self.selected_file)}...")
        self.progress_dialog.append_log(f"Target format: {fmt.upper()}")
        
        # Start Thread
        thread = threading.Thread(target=self.run_conversion_thread, args=(fmt,))
        thread.start()

    def run_conversion_thread(self, fmt):
        try:
            base_path = os.path.splitext(self.selected_file)[0]
            output_path = f"{base_path}.{fmt}"
            
            if self.progress_dialog:
                self.progress_dialog.append_log("Processing file...")
            
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
            
        wx.MessageBox(f"Saved successfully to:\n{output_path}", "Success", wx.ICON_INFORMATION)
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
