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

EXAMPLE_USER_MODULE = r"""
import re

from research import Search

# search is a list of Search objects
search = [
    Search('P1',  # this is the label of this search

           # regular expresion capture groups are important to extract information,
           # capture groups en regular expresion are the values enclosed in (),
           #  you can practice on http://pythex.org
           r'(\d{5}|\d{4}).*Número de póliza\n(\w{5}\d{10})',

           flags=re.MULTILINE | re.DOTALL,  # optional: flags to pass to re.search

           # optional if you want to store a found value in a global store, this value can be used later on other search output
           # { 'your-key' : lambda groups: groups[index]}
           # then it can be used in other search like this self.context['your-key']

           store_actions={'p1_poliza': lambda grps: grps[1]},

           # optional specify how to build the output csv row
           # in this case the label, filename, page, and 2 values captured by the regular expresion are used
           output_map=lambda self: (self.label, self.context['file'], self.context['page'], self.groups[1], self.groups[0])),

    # more Searchs!!!
    Search('P1',
           r'.*Número de póliza\n(\w{5}\d{10})',
           flags=re.MULTILINE | re.DOTALL,
           store_actions={'p1_poliza': lambda grps: grps[0]},
           output_map=lambda self: (self.label, self.context['file'], self.context['page'], self.groups[0], '')),
    Search('P2',
           r'vigencia establecida\.\nPóliza\:\s(\w{5}\d{10})',
           flags=re.MULTILINE,
           output_map=lambda self: (self.label, self.context['file'], self.context['page'], self.groups[0], '')),
    Search('P3',
           r'CBNX\nPóliza\:\s\n(\w{5}\d{10})',
           flags=re.MULTILINE,
           output_map=lambda self: (self.label, self.context['file'], self.context['page'], self.groups[0], '')),
    Search('P4',
           # no capture groups specified
           r'Contacto\nReporte de siniestro\:',
           flags=re.MULTILINE,
           # self.context['p1_poliza'] is the value stored in search P1
           output_map=lambda self: (self.label, self.context['file'], self.context['page'], self.context['p1_poliza'], '')),
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
    parser.add_argument("--generate-usermodule",
                        help="generate a user module example in the specified file")
    parser.add_argument("-o", "--output", type=argparse.FileType('w'),
                        help="output file name (default: stdout)", default=sys.stdout)
    parser.add_argument('--password', default='',
                        help='password to open the pdf file if required')
    parser.add_argument('--pagenos', metavar='F', type=int, nargs='+',
                        help="lista de paginas", default=[])
    parser.add_argument('--maxpages', type=int,
                        help="maximo numero de paginas a procesar (default: 0 -todas las paginas-)", default=0)
    parser.add_argument('--extract-text', action='store_true',
                        help='output page text and do not evaluate user expressions')
    args = parser.parse_args()
    if args.input:
        args.files = glob(path.expanduser(args.input))

    if args.generate_usermodule:
        with open(args.generate_usermodule, 'w') as handle:
            handle.write(EXAMPLE_USER_MODULE)
        parser.exit()
    elif args.extract_text and args.input:
        return args
    elif not (args.input and args.user_module):
        parser.error('positional arguments required [input] [user_module]')
    return args


def main():
    args = parsed_args()
    of = args.output
    w = csv.writer(of, quotechar='"', quoting=csv.QUOTE_ALL)
    usrmodule = None
    search = None
    if args.user_module:
        usrmodule = __import__(args.user_module)
        assert hasattr(usrmodule, 'search')
        search = usrmodule.search
    global_context = dict()
    for file in args.files:
        args.file = file
        for pnum, txtpage in enumerate(convert_pdf_to_txt(file, args)):
            pageno = args.pagenos[pnum] if args.pagenos else pnum

            if args.extract_text:
                of.write(f'@file: {file}\n')
                of.write(f'@page: {pageno}\n')
                of.write(('-' * 10)+'\n')
                of.write(txtpage)
            else:
                for s in search:
                    context = dict(
                        page=pageno,
                        file=file,
                        text=txtpage,
                        args=args
                    )
                    context.update(global_context)
                    s.search(txtpage, context=context)
                    if not s.groups is None:
                        if s.store_actions:
                            global_context.update(s.get_store_values())
                        w.writerow(s.output_map())
                        break


if __name__ == '__main__':
    main()
