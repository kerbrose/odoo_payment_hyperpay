# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint
from datetime import datetime


from odoo import _, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_hyperpay_sfa import const


_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_processing_values(self, processing_values):
        """Override of `payment` to return hyperpay-specific processing values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the
                                       transaction.
        :return: The provider-specific processing values.
        :rtype: dict
        """
        res = super()._get_specific_processing_values(processing_values)
        if self.provider_code != 'hyperpay':
            return res

        if self.operation in ('online_token', 'offline'):
            return {}

        order_payload = self._hyperpay_prepare_order_payload()
        payload = {
            'entityId': self.provider_id.hyperpay_entity_id,
            'paymentType': 'DB',
            'integrity': True,
            'merchantTransactionId': self.reference,
            'operation': 'online_direct'
        }
        self.write({'operation': 'online_direct'})
        payload.update(order_payload)
        return payload

    def _hyperpay_prepare_order_payload(self):
        """Prepare the payload for the order request based on the transaction values.

        :param str customer_id: The ID of the Customer object to assign to the Order for
                                non-subsequent payments.
        :return: The request payload.
        :rtype: dict
        """
        converted_amount = payment_utils.to_minor_currency_units(self.amount, self.currency_id)
        # https://hyperpay.docs.oppwa.com/reference/parameters
        payload = {
            'amount': converted_amount,
            'currency': self.currency_id.name,
        }
        if self.operation not in ['online_direct', 'validation']:
            raise ValidationError(
                _(
                    'Hyperpay: '
                    + _(
                        "The operation '%s' is not supported by hyperpay.",
                        self.operation,
                    )
                )
            )
        return payload

    def _send_payment_request(self):
        """Override of `payment` to send a payment request to Hyperpay.

        Note: self.ensure_one()

        :return: None
        :raise UserError: If the transaction is not linked to a token.
        """
        super()._send_payment_request()
        if self.provider_code != 'hyperpay':
            return

        # Prepare the payment request to Hyperpay
        if not self.token_id:
            raise UserError('Hyperpay: ' + _('The transaction is not linked to a token.'))

        converted_amount = payment_utils.to_minor_currency_units(
            self.amount,
            self.currency_id,
            const.CURRENCY_DECIMALS.get(self.currency_id.name),
        )
        data = {
            'amount': converted_amount,
            'currency': self.currency_id.name,
            'entityId': self.provider_id.hyperpay_entity_id,
            'paymentType': 'DB',
            'integrity': True,
            'merchantTransactionId': self.reference,
        }

        try:
            response_content = self.provider_id._hyperpay_make_request(
                payload=data,
                method='POST',
            )
        except ValidationError as e:
            if self.operation == 'offline':
                self._set_error(str(e))  # Log the error message on linked documents' chatter.
                return  # There is nothing to process.
            else:
                raise e

        # Handle the payment request response
        _logger.info(
            'payment request response for transaction with reference %s:\n%s',
            self.reference,
            pprint.pformat(response_content),
        )
        self._handle_notification_data('hyperpay', response_content)

    def _send_capture_request(self, amount_to_capture=None):
        """Override of `payment` to send a capture request to Hyperpay."""
        child_capture_tx = super()._send_capture_request(amount_to_capture=amount_to_capture)
        if self.provider_code != 'hyperpay':
            return child_capture_tx

        converted_amount = payment_utils.to_minor_currency_units(self.amount, self.currency_id)
        payload = {
            'amount': converted_amount,
            'currency': self.currency_id.name,
        }
        _logger.info(
            "Payload of '/payments/<id>/capture' request for transaction with reference %s:\n%s",
            self.reference,
            pprint.pformat(payload),
        )
        response_content = self.provider_id._hyperpay_make_request(
            f'payments/{self.provider_reference}/capture', payload=payload
        )
        _logger.info(
            "Response of '/payments/<id>/capture' request for transaction with reference %s:\n%s",
            self.reference,
            pprint.pformat(response_content),
        )

        # Handle the capture request response.
        self._handle_notification_data('hyperpay', response_content)

        return child_capture_tx

    def _send_void_request(self, amount_to_void=None):
        """Override of `payment` to explain that it is impossible to void a Hyperpay transaction."""
        child_void_tx = super()._send_void_request(amount_to_void=amount_to_void)
        if self.provider_code != 'hyperpay':
            return child_void_tx

        raise UserError(_("Transactions processed by Hyperpay can't be manually voided from Odoo."))

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Override of `payment` to find the transaction based on hyperpay data.

        :param str provider_code: The code of the provider that handled the transaction
        :param dict notification_data: The normalized notification data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'hyperpay' or len(tx) == 1:
            return tx

        entity_type = notification_data.get('entity_type', 'payment')
        if entity_type == 'payment':
            reference = notification_data.get('description')
            if not reference:
                raise ValidationError('Hyperpay: ' + _('Received data with missing reference.'))
            tx = self.search([('reference', '=', reference), ('provider_code', '=', 'hyperpay')])
        else:  # 'refund'
            notes = notification_data.get('notes')
            reference = isinstance(notes, dict) and notes.get('reference')
            if reference:  # The refund was initiated from Odoo.
                tx = self.search([('reference', '=', reference), ('provider_code', '=', 'hyperpay')])
            else:  # The refund was initiated from Hyperpay.
                # Find the source transaction based on its provider reference.
                source_tx = self.search(
                    [
                        ('provider_reference', '=', notification_data['payment_id']),
                        ('provider_code', '=', 'hyperpay'),
                    ]
                )
                if source_tx:
                    # Manually create a refund transaction with a new reference.
                    tx = self._hyperpay_create_refund_tx_from_notification_data(source_tx, notification_data)
                else:  # The refund was initiated for an unknown source transaction.
                    pass  # Don't do anything with the refund notification.
        if not tx:
            raise ValidationError('Hyperpay: ' + _('No transaction found matching reference %s.', reference))

        return tx

    def _hyperpay_create_refund_tx_from_notification_data(self, source_tx, notification_data):
        """Create a refund transaction based on Hyperpay data.

        :param recordset source_tx: The source transaction for which a refund is initiated, as a
                                    `payment.transaction` recordset.
        :param dict notification_data: The notification data sent by the provider.
        :return: The newly created refund transaction.
        :rtype: recordset of `payment.transaction`
        :raise ValidationError: If inconsistent data were received.
        """
        refund_provider_reference = notification_data.get('id')
        amount_to_refund = notification_data.get('amount')
        if not refund_provider_reference or not amount_to_refund:
            raise ValidationError('Hyperpay: ' + _('Received incomplete refund data.'))

        converted_amount = payment_utils.to_major_currency_units(amount_to_refund, source_tx.currency_id)
        return source_tx._create_child_transaction(
            converted_amount,
            is_refund=True,
            provider_reference=refund_provider_reference,
        )

    def _process_notification_data(self, notification_data):
        """Override of `payment` to process the transaction based on Hyperpay data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider
        :return: None
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'hyperpay':
            return

        if 'id' in notification_data:  # We have the full entity data (S2S request or webhook).
            entity_data = notification_data
        else:  # The payment data are not complete (Payments made by a token).
            # Fetch the full payment data.
            entity_data = self.provider_id._hyperpay_make_request(
                f'payments/{notification_data["hyperpay_payment_id"]}', method='GET'
            )
            _logger.info(
                "Response of '/payments' request for transaction with reference %s:\n%s",
                self.reference,
                pprint.pformat(entity_data),
            )

        # Update the provider reference.
        entity_id = entity_data.get('id')
        if not entity_id:
            raise ValidationError('Hyperpay: ' + _('Received data with missing entity id.'))
        # One reference can have multiple entity ids as Hyperpay allows retry on payment failure.
        # Making sure the last entity id is the one we have in the provider reference.
        allowed_to_modify = self.state not in ('done', 'authorized')
        if allowed_to_modify:
            self.provider_reference = entity_id

        entity_status = entity_data.get('status')
        if entity_status in const.PAYMENT_STATUS_MAPPING['done']:
            if (
                not self.token_id
                and entity_data.get('token_id')
                and self.provider_id.allow_tokenization
            ):
                self._hyperpay_tokenize_from_notification_data(entity_data)
            self._set_done()
        # Update the payment state.
        x = 1

    def _hyperpay_tokenize_from_notification_data(self, notification_data):
        """Create a new token based on the notification data.

        :param dict notification_data: The notification data built with Hyperpay objects.
                                       See `_process_notification_data`.
        :return: None
        """
        pm_code = (self.payment_method_id.primary_payment_method_id or self.payment_method_id).code
        if pm_code == 'card':
            details = notification_data.get('card', {}).get('last4')
        elif pm_code == 'upi':
            temp_vpa = notification_data.get('vpa')
            details = temp_vpa[temp_vpa.find('@') - 1 :]
        else:
            details = pm_code

        token = self.env['payment.token'].create(
            {
                'provider_id': self.provider_id.id,
                'payment_method_id': self.payment_method_id.id,
                'payment_details': details,
                'partner_id': self.partner_id.id,
            }
        )
        self.write(
            {
                'token_id': token,
                'tokenize': False,
            }
        )
        _logger.info(
            'Created token with id %(token_id)s for partner with id %(partner_id)s from '
            'transaction with reference %(ref)s',
            {
                'token_id': token.id,
                'partner_id': self.partner_id.id,
                'ref': self.reference,
            },
        )
