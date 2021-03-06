# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Force computation of donation amounts
    env['partner.communication.job'].search([
        ('config_id', 'in', [50, 53]),
        ('state', 'not in', ['done', 'cancel'])
    ])._compute_donation_amount()
