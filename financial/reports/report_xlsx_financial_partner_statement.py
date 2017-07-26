# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#    Daniel Sadamo <daniel.sadamo@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from openerp import _
from openerp import fields
from openerp.report import report_sxw
from psycopg2.extensions import AsIs

from .report_xlsx_financial_base import ReportXlsxFinancialBase


class ReportXslxFinancialPartnerStatement(ReportXlsxFinancialBase):
    def define_title(self):
        partner_name = self.report_wizard.partner_id.legal_name
        if self.report_wizard.type == '2receive':
            partner_type = 'Client'
        else:
            partner_type = 'Supplier'
        return _('%s Statement - %s' % partner_type, partner_name)

    def define_filters(self):
        date_from = fields.Datetime.from_string(self.report_wizard.date_from)
        date_from = date_from.date()
        date_to = fields.Datetime.from_string(self.report_wizard.date_to)
        date_to = date_to.date()

        filters = {
            0: {
                'title': _('Date'),
                'value': _('From %s to %s') %
                (date_from.strftime('%d/%m/%Y'),
                 date_to.strftime('%d/%m/%Y')),
            },
            1: {
                'title': _('Company'),
                'value': self.report_wizard.company_id.name,
            },

        }
        return filters

    def define_filter_title_column_span(self):
        return 2

    def define_filter_value_column_span(self):
        return 3

    def prepare_data(self):
        #
        # First, we prepare the report_data lines, time_span and accounts
        #
        report_data = {
            'lines': {},
            'total_lines': {},
        }

        SQL_INICIAL_VALUE = '''
            SELECT
               fm.id,
               fa.code,
               fa.name,
               fm.document_number,
               fm.date_document,
               fm.date_business_maturity,
               fm.date_payment,
               fm.amount_document,
               fm.amount_paid_discount,
               fm.amount_paid_penalty,
               fm.amount_paid_interest,
               fm.amount_paid_total,
               fm.partner_id
            FROM
              financial_move fm
              join financial_account fa on fa.id = fm.account_id
            WHERE
              fm.type = %(type)s
              and fm.date_business_maturity between %(date_from)s and
               %(date_to)s
              and fm.state = 'open'
            ORDER BY
              fm.%(group_by)s, fm.%(group_by2);
        '''
        filters = {
            'group_by': AsIs(self.report_wizard.group_by),
            'group_by2':
                AsIs('partner_id') if
                self.report_wizard.group_by == 'date_business_maturity' else
                AsIs('date_business_maturity'),
            'type': self.report_wizard.type,
            'date_to': self.report_wizard.date_to,
            'date_from': self.report_wizard.date_from,
        }
        self.env.cr.execute(SQL_INICIAL_VALUE, filters)
        data = self.env.cr.fetchall()
        for line in data:
            line_dict = {
                'cod_conta': line[1],
                'conta': line[2],
                'num_documento': line[3],
                'dt_doc': line[4],
                'date_business_maturity': line[5],
                'dt_quit': line[6],
                # 'prov': line[7],
                'vlr_original': line[7],
                'desc': line[8],
                'multa': line[9],
                'juros': line[10],
                'parc_total': line[11],
                'partner_id': line[12],
            }
            if self.report_wizard.group_by == "date_business_maturity":
                if report_data['lines'].get(line[5]):
                    report_data['lines'][line[5]].append(line_dict)
                else:
                    report_data['lines'][line[5]] = [line_dict]
            elif self.report_wizard.group_by == "partner_id":
                if report_data['lines'].get(line[12]):
                    report_data['lines'][line[12]].append(line_dict)
                else:
                    report_data['lines'][line[12]] = [line_dict]
        if self.report_wizard.group_by == "partner_id":
            SQL_VALUE = '''
                SELECT
                   fm.partner_id,
                   sum(fm.amount_document) as amount_document,
                   sum(fm.amount_paid_discount) as amount_paid_discount,
                   sum(fm.amount_paid_penalty) as amount_paid_penalty,
                   sum(fm.amount_paid_interest) as amount_paid_interest,
                   sum(fm.amount_paid_total) as amount_paid_total
                FROM
                    financial_move fm
                    join financial_account fa on fa.id = fm.account_id
                WHERE
                  fm.type = %(type)s
                  and fm.date_business_maturity between %(date_from)s and
                   %(date_to)s
                  and fm.state = 'open'
                GROUP BY
                  fm.%(group_by)s
                ORDER BY
                  fm.%(group_by)s;
            '''
            filters = {
                'group_by': AsIs(self.report_wizard.group_by),
                'type': self.report_wizard.type,
                'date_to': self.report_wizard.date_to,
                'date_from': self.report_wizard.date_from,
            }
            self.env.cr.execute(SQL_VALUE, filters)
            data = self.env.cr.fetchall()
            for line in data:
                line_dict = {
                    'vlr_original': line[1],
                    'desc': line[2],
                    'multa': line[3],
                    'juros': line[4],
                    'parc_total': line[5],
                    'partner_id': line[0],
                }
                report_data['total_lines'][line[0]] = line_dict
        elif self.report_wizard.group_by == "date_business_maturity":
            SQL_VALUE = '''
                SELECT
                   fm.date_business_maturity,
                   sum(fm.amount_document) as amount_document,
                   sum(fm.amount_paid_discount) as amount_paid_discount,
                   sum(fm.amount_paid_penalty) as amount_paid_penalty,
                   sum(fm.amount_paid_interest) as amount_paid_interest,
                   sum(fm.amount_paid_total) as amount_paid_total
                FROM
                    financial_move fm
                    join financial_account fa on fa.id = fm.account_id
                WHERE
                  fm.type = %(type)s
                  and fm.date_business_maturity between %(date_from)s and
                   %(date_to)s
                  and fm.state = 'open'
                GROUP BY
                  fm.%(group_by)s
                ORDER BY
                  fm.%(group_by)s;
            '''
            filters = {
                'group_by': AsIs(self.report_wizard.group_by),
                'type': self.report_wizard.type,
                'date_to': self.report_wizard.date_to,
                'date_from': self.report_wizard.date_from,
            }
            self.env.cr.execute(SQL_VALUE, filters)
            data = self.env.cr.fetchall()
            for line in data:
                line_dict = {
                    'vlr_original': line[1],
                    'desc': line[2],
                    'multa': line[3],
                    'juros': line[4],
                    'parc_total': line[5],
                    'date_business_maturity': line[0],
                }
                report_data['total_lines'][line[0]] = line_dict
        return report_data

    def define_columns(self):
        result = {
            0: {
                'header': _('Data Documento'),
                'field': 'document_date',
                'width': 12,
                'style': 'date',
                'type': 'date'
            },
            1: {
                'header': _('Nº Documento'),
                'field': 'document_number',
                'width': 25,
            },
            2: {
                'header': _('Vencimento'),
                'field': 'date_business_maturity',
                'width': 20,
                'style': 'date',
                'type': 'date'
            },
            3: {
                'header': _('Valor Bruto'),
                'field': 'amount_document',
                'width': 20,
                'style': 'currency',
                'type': 'currency',
            },
            4: {
                'header': _('Valor Pago'),
                'field': 'amount_paid',
                'width': 20,
                'style': 'currency',
                'type': 'currency',
            },
            5: {
                'header': _('Atraso'),
                'field': '',
                'width': 20,
            },
            6: {
                'header': _('Saldo Devido'),
                'field': 'amount_residual',
                'width': 20,
                'style': 'currency',
                'type': 'currency',
            },
            #
            #RECEBIMENTO/BAIXA
            #
            7: {
                'header': _('Valor'),
                'field': '',
                'width': 20,
                'style': 'currency',
                'type': 'currency',
            },
            8: {
                'header': _('Desc.'),
                'field': 'desc',
                'width': 20,
                'style': 'currency',
                'type': 'currency',
            },
            9: {
                'header': _('Multa'),
                'field': 'multa',
                'width': 20,
                'style': 'currency',
                'type': 'currency',
            },
            10: {
                'header': _('Juros'),
                'field': 'juros',
                'width': 20,
                'style': 'currency',
                'type': 'currency',
            },
            11: {
                'header': _('Data Recebimento'),
                'field': '',
                'width': 20,
                'style': 'date',
                'type': 'date',
            },
            12: {
                'header': _('Total Recebido'),
                'field': '',
                'width': 20,
                'style': 'currency',
                'type': 'currency'
            },
            13: {
                'header': _('Status'),
                'field': 'state',
                'width': 20,
            },
        }

        return result

    def write_content(self):
        self.sheet.set_zoom(85)

        for move_id in sorted(self.report_data['lines'].keys()):
            if self.report_wizard.group_by == "date_business_maturity":
                current_date = fields.Datetime.from_string(move_id)
                current_date = current_date.strftime('%d/%m/%Y')
                self.sheet.merge_range(
                    self.current_row, 0,
                    self.current_row + 1,
                    len(self.columns) - 1,
                    _('Data de Vencimento: ' + current_date),
                    self.style.header.align_left
                )
                self.current_row += 2
                self.write_header()
            elif self.report_wizard.group_by == "partner_id":
                partner = self.env['res.partner'].browse(move_id)
                partner_cnpj_cpf = " - " + \
                                   partner.cnpj_cpf if partner.cnpj_cpf else ""
                partner_email = " - " + \
                                partner.email if partner.email else ""
                self.sheet.merge_range(
                    self.current_row, 0,
                    self.current_row + 1,
                    len(self.columns) - 1,
                    _('Parceiro: ' + partner.display_name +
                      partner_cnpj_cpf + partner_email
                      ),
                    self.style.header.align_left
                )
                self.current_row += 2
                self.write_header()

            for line in self.report_data['lines'][move_id]:
                self.write_detail(line)

            if self.report_wizard.group_by == "date_business_maturity":
                self.sheet.merge_range(
                    self.current_row, 0,
                    self.current_row + 1,
                    len(self.columns) - 1,
                    _('Total'),
                    self.style.header.align_left
                )
                self.current_row += 1
                self.write_header()
                self.report_data['total_lines'][move_id].pop(
                    'date_business_maturity')
                self.write_detail(
                    self.report_data['total_lines'][move_id])
                self.current_row += 1
            elif self.report_wizard.group_by == "partner_id":
                self.sheet.merge_range(
                    self.current_row, 0,
                    self.current_row + 1,
                    len(self.columns) - 1,
                    _('Total'),
                    self.style.header.align_left
                )
                self.current_row += 1
                self.write_header()
                self.report_data['total_lines'][move_id].pop(
                    'partner_id')
                self.write_detail(
                    self.report_data['total_lines'][move_id])
                self.current_row += 1

    def generate_xlsx_report(self, workbook, data, report_wizard):
        super(ReportXslxFinancialPartnerStatement, self).generate_xlsx_report(
            workbook, data, report_wizard)

        workbook.set_properties({
            'title': self.title,
            'company': self.report_wizard.company_id.name,
            'comments': _('Created with Financial app on {now}').format(
                now=fields.Datetime.now())
        })

        #
        # Documentation for formatting pages here:
        # http://xlsxwriter.readthedocs.io/page_setup.html
        #
        self.sheet.set_landscape()
        self.sheet.set_paper(9)  # A4
        self.sheet.fit_to_pages(1, 99999)
        #
        # Margins, in inches, left, right, top, bottom;
        # 1 / 2.54 = 1 cm converted in inches
        #
        self.sheet.set_margins(1 / 2.54, 1 / 2.54, 1 / 2.54, 1 / 2.54)


ReportXslxFinancialPartnerStatement(
    #
    # Name of the report in report_xlsx_financial_cashflow_data.xml,
    # field name, *always* preceeded by "report."
    #
    'report.report_xlsx_financial_partner_statement',
    #
    # The model used to filter report data, or where the data come from
    #
    'report.xlsx.financial.partner.statement.wizard',
    parser=report_sxw.rml_parse
)