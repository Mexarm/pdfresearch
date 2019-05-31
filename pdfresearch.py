import sys
import csv
from os import path
from glob import glob
import argparse

from io import StringIO

from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams

EXAMPLE_USER_MODULE = r"""import re
from os import path

# search = [ ('LABEL', re.compile(r'regex',flags=...), lambda grps: grps <optional>) , .... ]

search = [
    (
        'P1',
        re.compile(
            r'(\d{5}|\d{4}).*Número de póliza\n(\w{5}\d{10})',
            flags=re.MULTILINE | re.DOTALL
        ),
        lambda grps, args: (grps[1], grps[0], path.abspath(args.file))
    ),
    (
        'P1',
        re.compile(
            r'().*Número de póliza\n(\w{5}\d{10})',
            flags=re.MULTILINE | re.DOTALL),
        lambda grps, args: (grps[1], grps[0], path.abspath(args.file))
    ),
    (
        'P2',
        re.compile(
            r'vigencia establecida\.\nPóliza\:\s(\w{5}\d{10})',
            flags=re.MULTILINE),
        lambda grps, args: (grps[0], '', path.abspath(args.file))
    ),
    (
        'P3',
        re.compile(
            r'CBNX\nPóliza\:\s\n(\w{5}\d{10})',
            flags=re.MULTILINE),
        lambda grps, args: (grps[0], '', path.abspath(args.file))
    ),
    (
        'P4',
        re.compile(
            r'Contacto\nReporte de siniestro\:',
            flags=re.MULTILINE),
        lambda grps, args: (grps[0], '', path.abspath(args.file))
    )
]
"""


def convert_pdf_to_txt(path, settings):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    laparams = LAParams()
    device = TextConverter(
        rsrcmgr, retstr, codec=settings.codec, laparams=laparams)
    fp = open(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = settings.password
    maxpages = settings.maxpages
    caching = True
    pagenos = set(settings.pagenos)
    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password, caching=caching, check_extractable=True):
        interpreter.process_page(page)
        txtpage = retstr.getvalue()
        retstr.truncate(0)
        retstr.seek(0)
        yield txtpage
    fp.close()
    device.close()


def parsed_args():
    parser = argparse.ArgumentParser(
        description="busca expresiones regulares en el texto de archivos PDF, la busqueda se realiza en cada pagina")
    parser.add_argument(
        'input', nargs='?', help="PDF file to read (it could be a pattern like ~/path/*.pdf)")
    parser.add_argument('user_module', nargs='?',
                        help="user module name (do not include .py)")
    parser.add_argument("-c", "--codec",
                        help="codec (default ascii)", default='ascii')
    parser.add_argument("--generate_usrmodule",
                        help="generate a user module example in the specified file")
    parser.add_argument("-o", "--output", type=argparse.FileType('w'),
                        help="output file name (default: stdout)", default=sys.stdout)
    parser.add_argument('--password', default='',
                        help='password to open the pdf file if required')
    parser.add_argument('--pagenos', metavar='F', type=int, nargs='+',
                        help="lista de paginas", default=[])
    parser.add_argument('--maxpages', type=int,
                        help="maximo numero de paginas a procesar (default: 0 -todas las paginas-)", default=0)
    parser.add_argument('--text_output', action='store_true',
                        help='output page text and do not evaluates user expressions')
    args = parser.parse_args()
    if args.input:
        args.files = glob(path.expanduser(args.input))

    if args.generate_usrmodule:
        with open(args.generate_usrmodule, 'w') as handle:
            handle.write(EXAMPLE_USER_MODULE)
        parser.exit()
    elif not (args.input and args.user_module):
        parser.error('positional arguments required [input] [user_module]')
    return args


def main():
    args = parsed_args()
    of = args.output
    w = csv.writer(of, quotechar='"', quoting=csv.QUOTE_ALL)
    lastmatch = ()
    usrmodule = __import__(args.user_module)
    assert hasattr(usrmodule, 'search')
    search = usrmodule.search
    for file in args.files:
        args.file = file
        for pnum, txtpage in enumerate(convert_pdf_to_txt(file, args)):
            label = None
            match = None
            res = None
            pageno = args.pagenos[pnum] if args.pagenos else pnum

            if args.text_output:
                of.write(f'@file: {file}\n')
                of.write(f'@page: {pageno}\n')
                of.write(('-' * 10)+'\n')
                of.write(txtpage)
            else:

                for f in search:
                    match = f[1].search(txtpage)
                    if match:
                        label = f[0]
                        if match.groups():
                            lastmatch = match
                        break

                if match:
                    if not match.groups():
                        match = lastmatch
                        lastmatch = ()

                    res = f[-1](match.groups(), args) if hasattr(f[-1],
                                                                 '__call__') else match.groups()
                    w.writerow((pageno, label) + res)


if __name__ == '__main__':
    main()
