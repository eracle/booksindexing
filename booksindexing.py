from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams, LTChar
from pdfminer.converter import PDFPageAggregator

import operator

import subprocess
import base64
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)

doc_type = 'book'

index_mapping = {
    "mappings": {
        doc_type: {
            "properties": {
                "cv": {"type": "attachment"}
            }}}}


def check_if_index_exists(es_conn, index_name, index_mapping):
    """
    Checks if there exists an index, if does not it creates it.
    :param es_conn: The elastic search (python) object;
    :param index_name: The name of the issued index;
    :param index_mapping: mapping of the new index.
    :return: None
    """
    logger.info('check if there is an index')
    if not es_conn.indices.exists(index_name):
        logger.info('lets create the index')
        res = es_conn.indices.create(index=index_name, ignore=400, body=index_mapping)
        logger.info(res)


def upload_file(es_conn, file, index_name):
    """
    Uploads a pdf to elasticsearch.
    :param es_conn: The elastic search (python) object;
    :param file: The path of the pdf to upload;
    :param index_name:  The name of the index to upload the file to.
    :return: None
    """
    logger.info('upload a pdf file:%s' % file)

    pdf_file = open(file, "rb")
    logger.info('encoding pdf file')
    encoded_string = base64.b64encode(pdf_file.read())
    file_body = {"cv": encoded_string.decode('utf-8')}

    logger.info('indexing pdf file')
    res = es_conn.index(index=index_name, doc_type=doc_type, body=file_body, request_timeout=1000)
    logger.debug(res)


def ocr_ize(input_file, output_file, lang='eng'):
    """
    Transform the pdf located by the input_file path parameter into an ocr-ized output file located in output_file path parameter,
    to ensure better precision a three character encoded language must be passed ('eng' english is default).
    The ocr performs:
    - automatically rotate pages based on detected text orientation;
    - deskew each page before performing OCR;
    - clean pages from scanning artifacts before performing OCR, and send the cleaned page to OCR,
        but do not include the cleaned page in the output;
    - clean page as above, and incorporate the cleaned image in the final PDF.

    :param input_file: Path of the input pdf file;
    :param output_file: Path of the final pdf file;
    :param lang: Three chars string encoding the language.
    :return: None
    """

    """
      -l LANGUAGE, --language LANGUAGE
                            languages of the file to be OCRed (see tesseract
                            --list-langs for all language packs installed in your
                            system)

      -r, --rotate-pages    automatically rotate pages based on detected text
                            orientation
      -d, --deskew          deskew each page before performing OCR
      -c, --clean           clean pages from scanning artifacts before performing
                            OCR, and send the cleaned page to OCR, but do not
                            include the cleaned page in the output
      -i, --clean-final     clean page as above, and incorporate the cleaned image
                            in the final PDF
    """
    logger.info('starting ocr of the file:%s' % input_file)
    bash_command = 'ocrmypdf -l %s -r -d -c -i --force-ocr %s %s' % (lang, input_file, output_file)

    logger.info('if no errors, created the file :%s' % output_file)

    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    logger.info("Ocrmypdf, error!: %s" % error)
    logger.debug("Ocrmypdf, output: %s" % output)


def read_pdf_content(input_file):
    """
    Use my pdfminer library version to extract the textual content from a pdf which path is passed through the
     input_file parameter.
    :param input_file: The path of the pdf file from where the content is extracted.
    :return: A string with the content of the file.
    """
    logger.info('reading pdf content:%s' % input_file)
    bash_command = 'pdf2txt.py %s' % input_file

    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    logger.info("pdf2txt.py, error!:%s" % error)
    return output.decode('utf-8')


def get_chars_coordinates(pdf_path):
    """
    Return an iterator over lists of coordinates (x,y).
    Every coordinate is associate with a single character in the pdf file.
    Every list of coordinates is associated with a single page of a pdf.
    The iterator iterates over all the pages of the pdf file which path is passed as a parameter.
    :param pdf_path: Path of the pdf file to analyse.
    :return: An iterator over lists of coordinates (x,y).
    """

    def _parse_obj(lt_objs, points):
        # loop over the object list
        for obj in lt_objs:
            if isinstance(obj, LTChar):
                points.append((obj.bbox[0], obj.bbox[1]))
            else:
                if hasattr(obj, '_objs'):
                    _parse_obj(obj._objs, points)

    # Liberally inspired from:
    # http://www.unixuser.org/~euske/python/pdfminer/programming.html

    fp = open(pdf_path, 'rb')
    parser = PDFParser(fp)
    document = PDFDocument(parser)
    if not document.is_extractable:
        raise PDFTextExtractionNotAllowed
    rsrcmgr = PDFResourceManager()
    device = PDFDevice(rsrcmgr)
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    # loop over all pages in the document
    for page in PDFPage.create_pages(document):
        interpreter.process_page(page)
        layout = device.get_result()
        points = []
        _parse_obj(layout._objs, points)
        yield points


def is_double_layered(coordinates):
    """
    Returns True if the list of coordinates (x,y) passed belongs to a double layer pdf page,
    False if they belongs to a single layer page.
    For the definition of single/double layer page check the unpaper documentation, in:
    https://github.com/Flameeyes/unpaper/blob/master/doc/basic-concepts.md
    :param coordinates: a list of coordinates (x,y) of all the single characters present in a pdf page.
    :return: True of False
    """
    # projecting all the character coordinates into the x axis
    # assuming the pdf was already correctly oriented
    xs = [x[0] for x in coordinates]
    sorted_xs = sorted(xs)

    # computing all the gaps between consecutive characters
    gaps = [b - a for a, b in zip(sorted_xs, sorted_xs[1:])]

    # computing the maximum gap between pairs of consecutive characters (projected in the x-axis)
    max_gap_index, max_gap = max(enumerate(gaps), key=operator.itemgetter(1))

    # computing the distance between the most left character and the most right one
    max_xs = max(xs)
    min_xs = min(xs)
    page_width = max_xs - min_xs

    # computing the mean x-position between the two consecutive characters with highest distance
    max_gap_x_position = (sorted_xs[max_gap_index] + sorted_xs[max_gap_index + 1]) / 2

    logger.debug("Page width: %s" % page_width)
    logger.debug("Max gap x position: %s" % max_gap_x_position)

    # import matplotlib.pyplot as plt
    # ys = [1 if x == max_xs else -1 if x == min_xs else 2 if x == sorted_xs[max_gap_index] else 3 if x == sorted_xs[max_gap_index + 1] else 0 for x in sorted_xs]
    # plt.scatter(sorted_xs, ys)
    # plt.show()

    return (max_gap > 0.1 * page_width) and (0.25 * page_width < (max_gap_x_position - min_xs) < page_width * 0.75)
