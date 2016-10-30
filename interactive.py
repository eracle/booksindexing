# TODO:

# Pipeline:

# - ocr recognition: trovare un euristica - parzialmente implementata la lettura del contenuto
# if to be ocr-ed:
# - language recognition: dal nome
# - pages rotation (use ocr-ize) - > ok
# if double layer:
# 	- pages splitting
# Come dividere il file di cui si è sicuri possegga un double layer.
# convert pdf file to ppm (pdftoppm) or PIL import Image... (https://github.com/jbarlow83/OCRmyPDF/blob/master/ocrmypdf/unpaper.py)
# run unpaper --layout double input.ppm output.ppm se non layout singolo
# convert ppm to pdf

# - rotation again, cleaning, ocr
# - indexing

#############################

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator
import pdfminer

# path = '/home/eracle/python/projects/booksindexing/libri/en_ocr_side_small_53_ocr-ized.pdf'
path = '/home/eracle/python/projects/booksindexing/libri/en_pdf.pdf'

# Open a PDF file.
fp = open(path, 'rb')

# Create a PDF parser object associated with the file object.
parser = PDFParser(fp)

# Create a PDF document object that stores the document structure.
# Password for initialization as 2nd parameter
document = PDFDocument(parser)

# Check if the document allows text extraction. If not, abort.
if not document.is_extractable:
    raise PDFTextExtractionNotAllowed

# Create a PDF resource manager object that stores shared resources.
rsrcmgr = PDFResourceManager()

# Create a PDF device object.
device = PDFDevice(rsrcmgr)

# BEGIN LAYOUT ANALYSIS
# Set parameters for analysis.
laparams = LAParams()

# Create a PDF page aggregator object.
device = PDFPageAggregator(rsrcmgr, laparams=laparams)

# Create a PDF interpreter object.
interpreter = PDFPageInterpreter(rsrcmgr, device)

points = []


def parse_obj(lt_objs):
    # loop over the object list
    for obj in lt_objs:
        if isinstance(obj, pdfminer.layout.LTText):
            text = obj.get_text()
            if len(text) > 2:
                print(type(obj))

                print("Text:" + text[:20])
                print("Len:" + str(len(text)))

                points.append((obj.bbox[0], obj.bbox[1], len(text)))

        if hasattr(obj, '_objs'):
            parse_obj(obj._objs)

            # if it's a textbox, print text and location

# loop over all pages in the document
for page in PDFPage.create_pages(document):
    # read the page into a layout object
    interpreter.process_page(page)
    layout = device.get_result()

    # extract text from this object
    parse_obj(layout._objs)

import matplotlib.pyplot as plt

xs = [x[0] for x in points]
ys = [x[1] for x in points]
labels = [x[2] for x in points]

plt.scatter(xs, ys)
for x, y, label in points:
    plt.annotate(
        label,
        xy=(x, y),
        xytext=(-20, 20),
        textcoords='offset points',
        ha='right',
        va='bottom',
        bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

plt.show()

#TODO: provare con nuovi pdf, magari li cerchiamo on-line,
# per quanto riguarda quelli italiani installare tesseract in italiano  e documentarlo, dioo cane.