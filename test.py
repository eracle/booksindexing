import pytest
from elasticsearch import Elasticsearch
from booksindexing import *
import random
import os

index_name = 'test_index_da39a3ee5e6b4b0d3255bfef95601890afd80709'

pdf_folder = 'test_pdf/'

en_pdf = pdf_folder + 'en_pdf.pdf'
en_pdf_search_phrase = "temporary promotion model"

it_pdf = pdf_folder + 'it_pdf.pdf'
it_pdf_search_phrase = "crittograficamente"

en_ocr_small = pdf_folder + 'en_ocr_small.pdf'
en_ocr_small_search_phrase = "aldol reaction"

en_ocr_side = pdf_folder + 'en_ocr_side_small_53.pdf'
en_ocr_side_search_phrase = 'TEXT COMPRESSION'


@pytest.fixture(scope="session")
def es_connection():
    es = Elasticsearch()
    check_if_index_exists(es, index_name=index_name, index_mapping=index_mapping)
    assert es.indices.exists(index=index_name)
    yield es
    es.indices.delete(index=index_name, ignore=[400, 404])
    assert not es.indices.exists(index=index_name)


def _tmp_filename(input_file):
    logger.info('generating random hash name for minimizing tmp file collisions')
    hashed_name = random.getrandbits(128)
    output_file = '.'.join(input_file.split('.')[:-1]) + '_' + "%032x" % hashed_name + '.pdf'
    logger.debug('generating tmp file:%s' % output_file)
    return output_file


def _check_if_present(connection, search_phrase):
    query = {
        "query": {
            "query_string": {
                "query": search_phrase
            }}}

    res = connection.search(index=index_name, body=query)
    total = res['hits']['total']
    logger.info('total returned %s' % total)
    assert int(total) >= 1


def _upload_and_search(connection, pdf_file, search_phrase):
    upload_file(connection, pdf_file, index_name)
    connection.indices.refresh(index=index_name)

    _check_if_present(connection, search_phrase)


def test_upload_pdf_en(es_connection):
    _upload_and_search(es_connection, en_pdf, en_pdf_search_phrase)


def test_upload_pdf_it(es_connection):
    _upload_and_search(es_connection, it_pdf, it_pdf_search_phrase)


def test_upload_pdf_en_ocred(es_connection):
    output_file = _tmp_filename(en_ocr_small)
    ocr_ize(en_ocr_small, output_file)

    _upload_and_search(es_connection, output_file, en_ocr_small_search_phrase)

    logger.info('removing the file: %s' % output_file)
    os.remove(output_file)


def test_ocr_ize_en_side():
    output_file = _tmp_filename(en_ocr_side)

    ocr_ize(en_ocr_side, output_file)

    in_content = read_pdf_content(en_ocr_side)
    out_content = read_pdf_content(output_file)
    assert en_ocr_side_search_phrase not in in_content
    assert en_ocr_side_search_phrase in out_content
    logger.info('removing the file: %s' % output_file)
    os.remove(output_file)



def test_read_pdf_content_empty():
    assert read_pdf_content(en_ocr_small) == '\f'



def test_read_pdf_content_not_empty():
    content = read_pdf_content(it_pdf)
    assert it_pdf_search_phrase in content
