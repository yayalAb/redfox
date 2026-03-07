# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by CandidRoot Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.


from odoo import models, _
import cv2
import pytesseract
import PyPDF2
import xlrd
import openpyxl
import csv
import odoo
import json
from odoo import http, _
from odoo.http import request, content_disposition
from PIL import Image

class DocumentController(http.Controller): 

    # READ CSV
    def search_str_from_csv(self, current_attachedfile, word):
        with open(current_attachedfile) as f:
            reader = csv.reader(f, delimiter=',')
            found_anything = False
            for row in reader:
                if word in row:
                    found_anything = True
            if found_anything:
                return True
            else:
                return False
        
    # READ XLS
    def search_str_from_xls(self, current_attachedfile, word):
        workbook = xlrd.open_workbook(current_attachedfile)
        worksheet = workbook.sheet_by_index(0)
        row = worksheet.nrows
        column = worksheet.ncols
        words = []
        for x in range(row):
            for y in range(column):
                words.append(worksheet.cell(x, y).value)
            x += 1
        if word in words:
            return True
        else:
            return False

    # READ TEXT FROM XLSX
    def search_str_from_xlsx(self, current_attachedfile, word):
        with open(current_attachedfile, 'r') as file:
            # read all content of a file
            content = file.read()

            # check if string present in a file
            content_list = []
            content_dict = json.loads(content)
            sheets = content_dict.get('sheets')
            if sheets != None:
                if len(sheets) > 1:
                    for sheet in sheets:
                        cells = sheet.get('cells')

                        if cells:
                            if len(cells) > 1:
                                for key in cells:
                                    formula = cells[key].get('formula')
                                    if formula:
                                        value = formula.get('value')
                                        content_list.append(value)
                            else:
                                formula = cells[list(cells.keys())[0]].get('formula')
                                if formula:
                                    value = formula.get('value')
                                    content_list.append(value)
                else:
                    cells = sheets[0].get('cells')
                    if cells:
                        if len(cells) > 1:
                            for key in cells:
                                formula = cells[key].get('formula')
                                if formula:
                                    value = formula.get('value')
                                    content_list.append(value)
                        else:
                            formula = cells[list(cells.keys())[0]].get('formula')
                            if formula:
                                value = formula.get('value')
                                content_list.append(value)
            for list_word in content_list:
                if word in str(list_word):
                    return True
            return False

    # READ IMAGES
    def search_str_from_image(self, current_attachedfile, word):
        img = Image.open(current_attachedfile)
        text = pytesseract.image_to_string(img)
        if word in text:
            return True
        else:
            return False

    # READ PDFS
    def search_str_from_pdf(self, current_attachedfile, word):
        # creating a pdf file object
        pdf_path = current_attachedfile
        pdfFileObject = open(pdf_path, 'rb')
        pdfReader = PyPDF2.PdfFileReader(pdfFileObject)
        pages = pdfReader.getNumPages()
        found_anything = False
        text = ''
        if pages > 1:
            for i in range(pages):
                current_page = pdfReader.getPage(i)
                text = current_page.extractText()
                if word in text:
                    found_anything = True
        else:
            current_page = pdfReader.getPage(0)
            text = current_page.extractText()
            if word in text:
                found_anything = True
        if found_anything:
            return True
        else:
            return False
        
    @http.route('/search_document', type='json', auth='user')
    def search_document(self, searching_for):
        search_key = searching_for
        found_records = []
        document_obj = request.env['documents.document'].search([])
        attachment_obj = request.env['ir.attachment'].sudo()

        filestore = odoo.tools.config.filestore(request.env.cr.dbname)

        for each_document in document_obj:
            attach_record = attachment_obj.search([('id', '=', each_document.attachment_id.id)])
            current_attachedfile = ''
            if attach_record:
                current_attachedfile = filestore + "/" + attach_record.store_fname
                if 'jpg' in attach_record.mimetype or 'jpeg' in attach_record.mimetype or 'png' in attach_record.mimetype:
                    if self.search_str_from_image(current_attachedfile, search_key):
                        found_records.append(each_document.id)
                if 'o-spreadsheet' in attach_record.mimetype or 'plain' in attach_record.mimetype or 'openxmlformats' in attach_record.mimetype:
                    if self.search_str_from_xlsx(current_attachedfile, search_key):
                        found_records.append(each_document.id)
                if 'pdf' in attach_record.mimetype:
                    if self.search_str_from_pdf(current_attachedfile, search_key):
                        found_records.append(each_document.id)
                if 'ms-excel' in attach_record.mimetype:
                    if self.search_str_from_xls(current_attachedfile, search_key):
                        found_records.append(each_document.id)
                if 'csv' in attach_record.mimetype:
                    if self.search_str_from_csv(current_attachedfile, search_key):
                        found_records.append(each_document.id)
        return found_records
