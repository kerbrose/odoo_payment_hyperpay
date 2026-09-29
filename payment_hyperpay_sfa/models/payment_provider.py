import json
import logging
import pprint

import requests

from odoo import _, fields, models
from odoo.addons.payment import utils as payment_utils
from odoo.exceptions import ValidationError

from odoo.addons.payment_hyperpay_sfa import const


_logger = logging.getLogger(__name__)

test_domain = 'https://eu-test.oppwa.com'
live_domain = 'https://eu-prod.oppwa.com'

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('hyperpay', "Hyperpay")], ondelete={'hyperpay': 'set default'}
    )

    hyperpay_entity_id = fields.Char(
        string="Hyperpay Entity/Merchant Id",
        help="The merchant id solely used to identify the account with Hyperpay.",
        required_if_provider='hyperpay',
        # groups='base.group_system',
    )

    hyperpay_auth_key = fields.Char(
        string="Hyperpay Auth Key",
        required_if_provider='hyperpay',
        # groups='base.group_system',
    )
    
    #=== COMPUTE METHODS ===#

    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'hyperpay').update({
            'support_manual_capture': 'full_only',
            'support_express_checkout': True,
            'support_refund': 'none',
            'support_tokenization': False,
        })

    # === BUSINESS METHODS - PAYMENT FLOW === #

    
    def _hyperpay_make_request(self, payload=None, method='POST'):
        """ Make a request to Hyperpay API at the specified endpoint.

        Note: self.ensure_one()

        :param str endpoint: The endpoint to be reached by the request.
        :param dict payload: The payload of the request.
        :param str method: The HTTP method of the request.
        :return The JSON-formatted content of the response.
        :rtype: dict
        :raise ValidationError: If an HTTP error occurs.
        """
        self.ensure_one()

        # TODO: Make api_version a kwarg in master.
        api_version = 'v1'
        _domain = live_domain if self.state == 'enabled' else test_domain
        url = f'{_domain}/{api_version}/checkouts'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Bearer {self.hyperpay_auth_key}',
        }
        try:
            response = requests.post(
                url,
                headers=headers,
                data=payload,
            )
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                _logger.exception(
                    "Invalid API request at %s with data:\n%s", url, pprint.pformat(payload),
                )
                raise ValidationError("Hyperpay: " + _(
                    "Hyperpay gave us the following information: '%s'",
                    response.json().get('error', {}).get('description')
                ))
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            _logger.exception("Unable to reach endpoint at %s", url)
            raise ValidationError(
                "hyperpay: " + _("Could not establish the connection to the API.")
            )
        return response.json()

    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'hyperpay':
            return default_codes
        return const.DEFAULT_PAYMENT_METHOD_CODES

    def _get_validation_amount(self):
        """ Override of `payment` to return the amount for Hyperpat validation operations.

        :return: The validation amount.
        :rtype: float
        """
        res = super()._get_validation_amount()
        if self.code != 'hyperpay':
            return res

        return 1.0

    def _hyperpay_get_inline_form_values(self, pm_code, amount=None, currency=None):
        """ Return a serialized JSON of the required values to render the inline form.

        Note: `self.ensure_one()`

        :return: The JSON serial of the required values to render the inline form.
        :rtype: str
        """
        self.ensure_one()

        formatted_amount = amount and currency and payment_utils.to_minor_currency_units(amount, currency)
        hyperpay_endpoint = 'https://eu-test.oppwa.com'
        if self.state == 'enabled':
            hyperpay_endpoint = 'https://eu-prod.oppwa.com'

        inline_form_values = {
            'hyperpay_entity_id': self.hyperpay_entity_id,
            'hyperpay_auth_key': self.hyperpay_auth_key,
            'formatted_amount': formatted_amount,
            'currency': currency.name,
            'endpoint': hyperpay_endpoint,
        }
        return json.dumps(inline_form_values)