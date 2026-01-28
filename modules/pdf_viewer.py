import fitz  # PyMuPDF
import wx

class PDFViewer:
    def __init__(self, pdf_path):
        self.doc = fitz.open(pdf_path)
        self.page_count = len(self.doc)

    def get_page_bitmap(self, page_num, width=None):
        if page_num < 0 or page_num >= self.page_count:
            return None
        
        page = self.doc.load_page(page_num)
        
        # Calculate zoom to fit width if provided
        zoom = 1.0
        if width:
            rect = page.rect
            zoom = width / rect.width
        
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to wx.Bitmap
        image = wx.Image(pix.width, pix.height, pix.samples)
        if pix.alpha:
             image.SetAlpha(pix.alphas)
             
        bitmap = wx.Bitmap(image)
        return bitmap

    def get_text(self):
        # Extract text from all pages for accessibility preview
        full_text = ""
        for page in self.doc:
            full_text += page.get_text() + "\n\n"
        return full_text

    def close(self):
        if self.doc:
            self.doc.close()
