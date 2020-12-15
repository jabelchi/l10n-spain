# -*- coding: utf-8 -*-
# Copyright 2017 Consultoría Informática Studio 73 S.L.
# Copyright 2017 Comunitea Servicios Tecnológicos S.L.
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    @api.depends('tax_line')
    def _compute_sii_enabled(self):
        for invoice in self:
            if invoice.fiscal_position.name == u'Importación con DUA' and \
                    not invoice.sii_dua_invoice:
                invoice.sii_enabled = False
            else:
                super(AccountInvoice, invoice)._compute_sii_enabled()

    @api.multi
    def _compute_dua_invoice(self):
        for invoice in self:
            if invoice.fiscal_position.name == u'Importación con DUA' and \
                    invoice.tax_line.\
                    filtered(lambda x: x.tax_code_id.code in
                             ['DIBYSCC21', 'DIBYSCC10', 'DIBYSCC4']):
                invoice.sii_dua_invoice = True
            else:
                invoice.sii_dua_invoice = False

    sii_dua_invoice = fields.Boolean("SII DUA Invoice",
                                     compute="_compute_dua_invoice")

    @api.multi
    def _get_sii_invoice_dict_in(self, cancel=False):
        """
        Según la documentación de la AEAT, la operación de importación se
        registra con TipoFactura = F5, sin FechaOperacion y con el NIF de la
        propia compañia en IDEmisorFactura y Contraparte
        Más información en: 8.1.2.2.Ejemplo mensaje XML de alta de importación
        en el documento de descripción de los servicios web:
        http://bit.ly/2rGWiAI

        """
        res = super(AccountInvoice, self)._get_sii_invoice_dict_in(
            cancel=cancel,
        )
        if not cancel and res.get('FacturaRecibida') and self.sii_dua_invoice:
            res['FacturaRecibida']['TipoFactura'] = 'F5'
            res['FacturaRecibida'].pop('FechaOperacion', None)
            res['FacturaRecibida']['IDEmisorFactura'] = \
                {'NIF': self.company_id.vat[2:]}
            res['IDFactura']['IDEmisorFactura'] = \
                {'NIF': self.company_id.vat[2:]}
            res['FacturaRecibida']['Contraparte']['NIF'] = \
                self.company_id.vat[2:]
            res['FacturaRecibida']['Contraparte']['NombreRazon'] = \
                self.company_id.name
            res["FacturaRecibida"].pop("ImporteTotal", False)
        return res
