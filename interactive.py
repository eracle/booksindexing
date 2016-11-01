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


from booksindexing import *

#en_pdf = './test_pdf/double_layered/en_ocr_side_small_53_ocrized.pdf'
en_pdf = './test_pdf/en_ocr_small.pdf'
out = './test_pdf/en_ocr_small_ocrized.pdf'
ocr_ize(en_pdf, out)

# TODO:
# install tesseract italiano
# ocrize it* file in test_pdf/double_layered
# run tests
# write the code for recognize the layer of a entire pdf
# write the doc for the entire pipeline -> language recognition module

#for x, y, label in points:
#    plt.annotate(
#        label,
#        xy=(x, y),
#        xytext=(-20, 20),
#        textcoords='offset points',
#        ha='right',
#        va='bottom',
#        bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
#        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))



#TODO: provare con nuovi pdf, magari li cerchiamo on-line,
# per quanto riguarda quelli italiani installare tesseract in italiano  e documentarlo, dioo cane.