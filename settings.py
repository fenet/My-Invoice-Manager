from datetime import date

# Default company (issuer) settings — can be edited later in DB/UI
COMPANY_DEFAULTS = {
    "name": "Sebastijan Alkesandar Kerculj e.U.",
    "address": "Simmeringer Hauptstraße 24\nA - 1110 Wien",
    "uid": "ATU78448967",
    "employer_no": "602379924",
    "email": "info@staffconnecting.at",
    "website": "www.staffconnecting.at",
    "reverse_charge_note": "Übertrag der Steuerschuld für Bauleistungen gemäß § 19 Abs 1a UStG",
}

INVOICE_NUMBER_FORMAT = "{year}{seq:04d}"  # e.g. 20251001
RESET_SEQUENCE_EACH_YEAR = True
INVOICE_CITY = "Wien"
DEFAULT_SERVICE_PERIOD = None  # e.g., "März"
DEFAULT_OBJECT = None
DEFAULT_UNIT = "h"  # used in UI labels
