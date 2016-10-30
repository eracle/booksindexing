import subprocess
import base64
import logging

logging.basicConfig(level=logging.INFO)
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
    Checks if there exists an index, if do not it creates it.
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

    # TODO: install tesseract - > italian language
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
    Use pdfminer3k library to extract the textual content from a pdf which path is passed through the
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
