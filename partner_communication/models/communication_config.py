# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import api, models, fields, _
from openerp.exceptions import ValidationError
import logging


logger = logging.getLogger(__name__)


class CommunicationConfig(models.Model):
    """ This class allows to configure if and how we will inform the
    sponsor when a given event occurs. """
    _name = 'partner.communication.config'
    _description = 'Communication Configuration'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(
        required=True, help='Rule name')
    model_id = fields.Many2one(
        'ir.model', 'Applies to', required=True,
        help="The kind of document with this communication can be used")
    model = fields.Char(related='model_id.model', store=True)
    user_id = fields.Many2one('res.users', 'From')
    send_mode = fields.Selection('_get_send_mode', required=True)
    send_mode_pref_field = fields.Char(
        'Partner preference field',
        help='Name of the field in res.partner in which to find the '
             'delivery preference'
    )
    print_if_not_email = fields.Boolean(
        help="Should we print the communication if the sponsor don't have "
             "an e-mail address"
    )
    email_template_id = fields.Many2one(
        'email.template', 'Email template',
        domain=[('model', '=', 'partner.communication.job')]
    )
    report_id = fields.Many2one(
        'ir.actions.report.xml', 'Letter template',
        domain=[('model', '=', 'partner.communication.job')]
    )
    attachments_function = fields.Char(
        help='Define a function in the communication_job model that will '
        'return all the attachment information for the communication in a '
        'dict of following format: {attach_name: [report_name, b64_data]}'
        'where attach_name is the name of the file generated,'
        'report_name is the name of the report used for printing,'
        'b64_data is the binary of the attachment'
    )

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.one
    @api.constrains('send_mode_pref_field')
    def _validate_config(self):
        """ Test if the config is valid. """
        valid = True
        if self.send_mode_pref_field:
            valid = hasattr(self.env['res.partner'], self.send_mode_pref_field)

        if not valid:
            raise ValidationError(
                "Following field does not exist in res.partner: %s." %
                self.send_mode_pref_field
            )

    @api.constrains('email_template_id', 'report_id')
    def _validate_attached_reports(self):
        for config in self:
            if config.email_template_id and config.email_template_id.model \
                    != 'partner.communication.job':
                raise ValidationError(
                    "Attached e-mail templates should be linked to "
                    "partner.communication.job objects!"
                )
            if config.report_id and config.report_id.model != \
                    'partner.communication.job':
                raise ValidationError(
                    "Attached report templates should be linked to "
                    "partner.communication.job objects!"
                )

    @api.constrains('attachments_function')
    def _validate_attachment_function(self):
        job_obj = self.env['partner.communication.job']
        for config in self.filtered('attachments_function'):
            if not hasattr(job_obj, config.attachments_function):
                raise ValidationError(
                    "partner.communication.job has no function called " +
                    config.attachments_function
                )

    def _get_send_mode(self):
        send_modes = self.get_delivery_preferences()
        send_modes.append(
            ('partner_preference', _('Partner specific'))
        )
        return send_modes

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def get_delivery_preferences(self):
        return [
            ('none', _("Don't inform sponsor")),
            ('auto_digital', _('Send e-mail automatically')),
            ('digital', _('Prepare e-mail (sent manually)')),
            ('auto_physical', _('Print letter automatically')),
            ('physical', _('Prepare report (print manually)')),
            ('both', _('Send e-mail + prepare report (print manually)')),
        ]

    def get_inform_mode(self, partner):
        """ Returns how the partner should be informed for the given
        communication (digital, physical or False).
        It makes the product of the communication preference and the partner
        preference :

        comm_pref   partner_pref    result
        ----------------------------------
        digital     physical        physical if "print if no e-mail" else none
        physical    digital         physical if not "email only"

        auto        manual          manual
        manual      auto            manual

        :param partner: res.partner record
        :returns: send_mode (physical/digital/False), auto_mode (True/False)
        """
        self.ensure_one()
        # First key is the comm send_mode, second key is the partner send_mode
        # value is the send_mode that should be selected.
        send_priority = {
            'physical': {
                'digital': 'physical' if not partner.email_only else 'none',
                'none': 'none',
                'both': 'physical',
                'physical': 'physical',
            },
            'digital': {
                'physical': 'physical' if self.print_if_not_email else 'none',
                'none': 'none',
                'both': 'both' if self.print_if_not_email else 'digital',
                'digital': 'digital',
            }
        }

        if self.send_mode != 'partner_preference':
            partner_mode = partner.global_communication_delivery_preference
            if self.send_mode == partner_mode:
                send_mode = self.send_mode
                auto_mode = 'auto' in send_mode or send_mode == 'both'
            else:
                auto_mode = (
                    'auto' in self.send_mode and 'auto' in partner_mode or
                    self.send_mode == 'both' and 'auto' in partner_mode or
                    'auto' in self.send_mode and partner_mode == 'both'
                )
                comm_mode = self.send_mode.replace('auto_', '')
                partner_mode = partner_mode.replace('auto_', '')
                send_mode = send_priority[comm_mode][partner_mode]

        else:
            send_mode = getattr(
                partner, self.send_mode_pref_field,  'none')
            auto_mode = 'auto' in send_mode or send_mode == 'both'

        send_mode = send_mode.replace('auto_', '')
        if send_mode == 'none':
            send_mode = False
        if send_mode == 'digital' and not partner.email:
            if self.print_if_not_email:
                send_mode = 'physical'
            else:
                send_mode = False
        return send_mode, auto_mode