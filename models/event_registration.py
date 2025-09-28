'''
@license
@preserve
File: \event_registration.py
Project: models (<<projectversion>>)
Created Date: Sunday, September 28th 2025, 4:35:16 pm
Author: Jonathan Stevens

--------------------------------------------------------------------------------

Last Modified: Sunday, 28th September 2025 4:36:04 pm
Modified By: Jonathan Stevens <jonathan.stevens@resnovas.com>

--------------------------------------------------------------------------------

Code of Conduct: This project abides by the Contributor Covenant, v2.0.
Please interact in ways that contribute to an open, welcoming, diverse,
inclusive, and healthy community. Our Code of Conduct can be found at
https://github.com/eventiva/eventiva/blob/develop/CODE_OF_CONDUCT.md

Contributing: Please read through our contributing guidelines. Included
are directions for opening issues, coding standards, and notes on
development. These can be found at
https://github.com/eventiva/eventiva/blob/develop/CONTRIBUTING.md

--------------------------------------------------------------------------------

Copyright (c) 2025 Jonathan Stevens T/a Resnovas, Resnovas Ltd or its affiliates
License: Fair Core License, Version 1.0, MIT Future License (FCL-1.0-MIT)

This program has been provided under confidence of the copyright holder
and is licensed for copying, distribution andmodification under the terms
of the Fair Core License, Version 1.0, MIT Future License (FCL-1.0-MIT)
published as the License, or any later version of this license. You must
not move, change, disable, or circumvent the license key functionality in
the Software; or modify any portion of the Software protected by the
license key to: enable access to the protected functionality without a
valid license key; or remove the protected functionality. This program is
distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the Fair Core License, Version 1.0, MIT Future
License for more details. You should have received a copy of the
Fair Core License, Version 1.0, MIT Future License (FCL-1.0-MIT)
along with this program. If not, please write to:
licensing@resnovas.com, see the official website
https://fcl.dev/ or Review the GitHub repository
https://github.com/keygen-sh/fcl.dev/

This project abides the Resnovas Cooperation Commitment
Adapted from the GPL Cooperation Commitment (GPLCC). Before filing or
continuing to prosecute any legal proceeding or claim (other than a
Defensive Action) arising from termination of a Covered License, we
commit to adhering to the Resnovas Cooperation Commitment.
You should have received a copy of the Resnovas Cooperation Commitment
along with this program. If not, please write to:
licensing@resnovas.com.

--------------------------------------------------------------------------------

For the purpose of determining the applicable license terms, a file
history is provided herein. As this historical record may be
incomplete, it is recommended that the repository be cloned and the
following command executed:

git checkout `git rev-list -n 1 --before='2 years ago' main`.

In the event that the licensed file is subject to the FCL, the version
under the Open Source terms of the change license shall apply.

HISTORY:
Date      	By	Comments
----------	---	----------------------------------------------------------------
'''


# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools import email_normalize


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    # New field to link to contact
    contact_id = fields.Many2one(
        'res.partner',
        string='Contact',
        help='The contact associated with this registration',
        domain=[('is_company', '=', False)]
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to automatically find or create contacts"""
        for vals in vals_list:
            # Only process if we have the necessary information and no contact_id is provided
            if not vals.get('contact_id') and (vals.get('email') or vals.get('name')):
                contact = self._find_or_create_contact(vals)
                if contact:
                    vals['contact_id'] = contact.id

        return super().create(vals_list)

    def write(self, vals):
        """Override write to automatically find or create contacts when email/name changes"""
        result = super().write(vals)

        # Process records that have email or name changes but no contact_id
        for record in self:
            if not record.contact_id and (record.email or record.name):
                contact = record._find_or_create_contact({
                    'email': record.email,
                    'name': record.name,
                    'phone': record.phone,
                    'company_name': record.company_name,
                })
                if contact:
                    record.contact_id = contact.id

        return result

    def _find_or_create_contact(self, vals):
        """Find existing contact by email or create a new one"""
        email = vals.get('email')
        name = vals.get('name', '')
        phone = vals.get('phone', '')
        company_name = vals.get('company_name', '')

        if not email and not name:
            return False

        # Normalize email for searching
        if email:
            email_normalized = email_normalize(email)
            if email_normalized:
                # First, try to find existing contact by normalized email
                existing_contact = self.env['res.partner'].search([
                    ('email_normalized', '=', email_normalized),
                    ('is_company', '=', False)
                ], limit=1)

                if existing_contact:
                    # Update existing contact with new information if provided
                    update_vals = {}
                    if name and name != existing_contact.name:
                        update_vals['name'] = name
                    if phone and phone != existing_contact.phone:
                        update_vals['phone'] = phone
                    if company_name and company_name != existing_contact.company_name:
                        update_vals['company_name'] = company_name

                    if update_vals:
                        existing_contact.write(update_vals)

                    return existing_contact

        # If no existing contact found, create a new one
        create_vals = {
            'is_company': False,
        }

        if email:
            create_vals['email'] = email
            create_vals['name'] = name or email.split('@')[0]
        else:
            create_vals['name'] = name or 'Unknown Contact'

        if phone:
            create_vals['phone'] = phone
        if company_name:
            create_vals['company_name'] = company_name

        return self.env['res.partner'].create(create_vals)

    @api.onchange('contact_id')
    def _onchange_contact_id(self):
        """Update registration fields when contact is selected"""
        if self.contact_id:
            self.name = self.contact_id.name
            self.email = self.contact_id.email
            self.phone = self.contact_id.phone
            self.company_name = self.contact_id.company_name
            self.partner_id = self.contact_id

    @api.onchange('email', 'name', 'phone', 'company_name')
    def _onchange_contact_fields(self):
        """Try to find existing contact when registration fields change"""
        if self.email or self.name:
            # Only search if we don't already have a contact_id
            if not self.contact_id:
                contact = self._find_or_create_contact({
                    'email': self.email,
                    'name': self.name,
                    'phone': self.phone,
                    'company_name': self.company_name,
                })
                if contact:
                    self.contact_id = contact

    def _get_booking_status_for_user(self, user_id=None):
        """Get booking status for a specific user based on contact linking"""
        if not user_id:
            user_id = self.env.user.id
        
        user = self.env['res.users'].browse(user_id)
        if not user.exists():
            return False
            
        # Check if this registration is linked to the user's contact
        if self.contact_id and self.contact_id == user.partner_id:
            return True
            
        # Check if this registration was created by the user
        if self.partner_id and self.partner_id == user.partner_id:
            return True
            
        # Check if the registration email matches the user's email
        if self.email and user.email and self.email.lower() == user.email.lower():
            return True
            
        return False
