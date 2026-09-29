# Part of Odoo. See LICENSE file for full copyright and licensing details.

# The currencies supported by hyperpay, in ISO 4217 format. Last updated on May 26, 2021.
# See https://hyperpay.docs.oppwa.com/integrations/widget/advanced-options.
# Last seen online: 16 November 2022.
SUPPORTED_CURRENCIES = [
    'AED',
    'ALL',
    'AMD',
    'ARS',
    'AUD',
    'AWG',
    'BBD',
    'BDT',
    'BMD',
    'BND',
    'BOB',
    'BSD',
    'BWP',
    'BZD',
    'CAD',
    'CHF',
    'CNY',
    'COP',
    'CRC',
    'CUP',
    'CZK',
    'DKK',
    'DOP',
    'DZD',
    'EGP',
    'ETB',
    'EUR',
    'FJD',
    'GBP',
    'GHS',
    'GIP',
    'GMD',
    'GTQ',
    'GYD',
    'HKD',
    'HNL',
    'HRK',
    'HTG',
    'HUF',
    'IDR',
    'ILS',
    'INR',
    'JMD',
    'JOD',
    'KES',
    'KGS',
    'KHR',
    'KYD',
    'KZT',
    'LAK',
    'LKR',
    'LRD',
    'LSL',
    'MAD',
    'MDL',
    'MKD',
    'MMK',
    'MNT',
    'MOP',
    'MUR',
    'MVR',
    'MWK',
    'MXN',
    'MYR',
    'NAD',
    'NGN',
    'NIO',
    'NOK',
    'NPR',
    'NZD',
    'PEN',
    'PGK',
    'PHP',
    'PKR',
    'QAR',
    'RUB',
    'SAR',
    'SCR',
    'SEK',
    'SGD',
    'SLL',
    'SOS',
    'SSP',
    'SVC',
    'SZL',
    'THB',
    'TTD',
    'TZS',
    'USD',
    'UYU',
    'UZS',
    'YER',
    'ZAR',
]

# The codes of the payment methods to activate when hyperpay is activated.
DEFAULT_PAYMENT_METHOD_CODES = {
    # Primary payment methods.
    'card',
    'netbanking',
    'upi',
    # Brand payment methods.
    'visa',
    'mastercard',
    'amex',
    'discover',
}

# The codes of payment methods that are not recognized by the orders API.
FALLBACK_PAYMENT_METHOD_CODES = {
    'wallets_india',
    'paylater_india',
    'emi_india',
}

# Mapping of payment method codes to hyperpay codes.
PAYMENT_METHODS_MAPPING = {
    'wallets_india': 'wallet',
    'paylater_india': 'paylater',
    'emi_india': 'emi',
}

# The maximum amount in INR that can be paid through an eMandate.
MANDATE_MAX_AMOUNT = {
    'card': 1000000,
    'upi': 100000,
}

# Mapping of transaction states to hyperpay's payment statuses.
# See https://hyperpay.docs.oppwa.com/integrations/widget/advanced-options
PAYMENT_STATUS_MAPPING = {
    'pending': ('created', 'pending'),
    'authorized': ('authorized',),
    'done': ('captured', 'refunded', 'processed'),  # refunded is included to discard refunded txs.
    'error': ('failed',),
}

# Events that are handled by the webhook.
HANDLED_WEBHOOK_EVENTS = [
    'payment.authorized',
    'payment.captured',
    'payment.failed',
    'refund.failed',
    'refund.processed',
]
