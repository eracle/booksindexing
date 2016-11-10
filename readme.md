# Upload pdf to Elastic Search
Simple python library which provides a set of tools and functionalities used for, preprocessing, cleaning, ocr and (finally) upload pdfs to an ElasticSearch instance.

### Allowed document types:
- Normal pdfs:
- Scanned pdfs (where the characters are recognized with Tesseract and used for indexing).

### Install:

Install dependencies (Ubuntu 16.04) :

    sudo apt-get install python3-dev unpaper=6.1-1 tesseract-ocr

- Create a python 3 virtual environment
- install requirements.txt:


    pip install -r requirements.txt
    
### Test:
    pytest test.py

### Todo:
To finish the entire pipeline and document it.
