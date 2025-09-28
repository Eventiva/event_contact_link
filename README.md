# Event Contact Link Module

## Overview

This Odoo 18 module automatically creates or finds contacts when people are added to event registrations. It establishes a many2one relationship between event registrations and contacts, allowing multiple registrations to be linked to a single contact.

## Features

### Automatic Contact Management

- **Auto-creation**: When a person is added to an event registration, the system automatically creates a contact if one doesn't exist
- **Auto-linking**: If a contact with the same email already exists, the registration is automatically linked to that contact
- **Smart matching**: Uses email normalization for accurate contact matching

### Contact-Event Registration Relationship

- **Many2One**: Multiple event registrations can be linked to a single contact
- **Bidirectional**: You can view all event registrations for a contact from the contact form
- **Data synchronization**: Contact information is automatically synchronized between the contact and registration

### User Interface Enhancements

- **Contact field**: Added a "Contact" field to event registration forms and lists
- **Search filters**: Added filters to find registrations with or without contacts
- **Contact view**: Added an "Event Registrations" tab to contact forms

## Installation

1. Place the module in your Odoo addons directory
2. Update the module list
3. Install the "Event Contact Link" module

## Dependencies

- `event` - Core event management
- `base` - Core Odoo functionality

## Usage

### For Event Managers

1. When creating or editing event registrations, the system will automatically:

   - Find existing contacts by email
   - Create new contacts if none exist
   - Link the registration to the contact

2. You can manually select a different contact using the "Contact" field

3. Use the search filters to find registrations with or without contacts

### For Contact Management

1. Open any contact form
2. Navigate to the "Event Registrations" tab
3. View all event registrations linked to that contact

## Technical Details

### Models Extended

- `event.registration` - Added `contact_id` field and automatic contact management
- `res.partner` - Added `event_registration_ids` one2many field

### Key Methods

- `_find_or_create_contact()` - Finds existing contacts or creates new ones
- `_onchange_contact_id()` - Synchronizes data when contact is selected
- `_onchange_contact_fields()` - Finds contacts when registration fields change

### Data Flow

1. User enters registration data (name, email, phone, company)
2. System searches for existing contact by email
3. If found, updates contact with new information and links registration
4. If not found, creates new contact and links registration
5. Registration and contact data are kept synchronized

## Configuration

No additional configuration is required. The module works automatically once installed.

## License

Other proprietary - Eventiva
