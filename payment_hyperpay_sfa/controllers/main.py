# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hmac
import logging
import pprint

from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request


_logger = logging.getLogger(__name__)


class HyperpayController(http.Controller):
    _webhook_url = '/payment/hyperpay/webhook'

    @http.route('/payment/hyperpay/payment_methods', type='jsonrpc', auth='public')
    def hyperpay_payment_methods(self, provider_id, formatted_amount=None, currency=None):
        """Query the available payment methods based on the payment context.

        :param int provider_id: The provider handling the transaction, as a `payment.provider` id
        :param dict formatted_amount: The Adyen-formatted amount.
        :param str currency: The currency of the transaction, as an ISO 4217 code
        :return: The JSON-formatted content of the response
        :rtype: dict
        """
        provider_sudo = request.env['payment.provider'].sudo().browse(provider_id)
        data = {
            'entityId': provider_sudo.hyperpay_entity_id,
            'amount': formatted_amount,
            'currency': currency,
            'paymentType': 'DB',
            'integrity': True,
        }
        response_content = provider_sudo._hyperpay_make_request(payload=data, method='POST')
        _logger.info('paymentMethods request response:\n%s', pprint.pformat(response_content))
        return response_content
