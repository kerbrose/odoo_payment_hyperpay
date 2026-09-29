/** @odoo-module **/
/* global Hyperpay */

import { _t } from '@web/core/l10n/translation';
import paymentForm from '@payment/js/payment_form';
import { HyperpayDialog } from "./hyperpay_dialog";

import { getGeneratedPageURL } from "./generate_blob";

import { rpc } from '@web/core/network/rpc';


paymentForm.include({

    async _initiatePaymentFlow(providerCode, paymentOptionId, paymentMethodCode, flow) {
        if (providerCode !== 'hyperpay') {
            await this._super(...arguments); // Tokens are handled by the generic flow
            return;
        }
        this._setPaymentFlow('direct'); // Hyperpay only supports direct flow
        let hyperpayCss = `<link rel="stylesheet" href="/payment_hyperpay_sfa/static/src/css/hyperpay_style.css" />`;
        let hyperpayScript = `<script async src="${this.hyperpayComponent.endpoint}/v1/paymentWidgets.js?checkoutId=${this.hyperpayComponent.checkoutId}"></script>`;
        let jQScript = '<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js"></script>';
        let hyperpayForm = `<form action="/payment/hyperpay/result?acq=${23}" class="paymentWidgets" data-brands="MASTER VISA"></form>`;
        let hyperpayIframe = document.createElement("iframe");
        hyperpayIframe.id = "hyperpay_iframe";
        hyperpayIframe.style = "display:none";
        let hyperpayHtml = hyperpayScript + hyperpayForm;
        const hyperpayIframBody = getGeneratedPageURL({
            html: hyperpayHtml,
            css: hyperpayCss,
            js: jQScript
        });
        this.call('ui', 'unblock');

        let title = 'Hyperpay Gateway';
        this.call('dialog', 'add', HyperpayDialog, { title: title, HyperpayEL: hyperpayIframBody, confirm: false });
    },

    // #=== DOM MANIPULATION ===#

    /**
     * Update the payment context to set the flow to 'direct'.
     *
     * @override method from @payment/js/payment_form
     * @private
     * @param {number} providerId - The id of the selected payment option's provider.
     * @param {string} providerCode - The code of the selected payment option's provider.
     * @param {number} paymentOptionId - The id of the selected payment option
     * @param {string} paymentMethodCode - The code of the selected payment method, if any.
     * @param {string} flow - The online payment flow of the selected payment option.
     * @return {void}
     */
    async _prepareInlineForm(providerId, providerCode, paymentOptionId, paymentMethodCode, flow) {
        if (providerCode !== 'hyperpay') {
            this._super(...arguments);
            return;
        }
        // Overwrite the flow of the select payment method.
        this._setPaymentFlow('direct');
        this.hyperpayComponent ??= {};
        const radio = document.querySelector('input[name="o_payment_radio"]:checked');
        const inlineFormValues = JSON.parse(radio.dataset['hyperpayInlineFormValues']);
        this.hyperpayComponent.endpoint = structuredClone(inlineFormValues.endpoint);

        const response = await rpc(
            '/payment/hyperpay/payment_methods',
            {
                'provider_id': providerId,
                'formatted_amount': inlineFormValues.formatted_amount,
                'currency': inlineFormValues.currency,
            },
        );

        if (response && response.result.code === '000.200.100') {
            this.el.parentElement.querySelector('script')?.remove();
            this.hyperpayComponent.checkoutId = structuredClone(response.id);
            this.hyperpayComponent.integrity = structuredClone(response.integrity);
            return response;
        }
        else {
            return Promise.reject();

        }

    },

    // #=== PAYMENT FLOW ===#

    async _processDirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        if (providerCode !== 'hyperpay') {
            this._super(...arguments);
            return;
        }
        return;
    },

    /**
     * Prepare the options to init the RazorPay SDK Object.
     *
     * @param {object} processingValues - The processing values.
     * @return {object}
     */
    _prepareHyperpayOptions(processingValues) {
        return Object.assign({}, processingValues, {
            'entityId': processingValues['entityId'],
            'paymentType': processingValues['paymentType'],
            'integrity': processingValues['integrity'],
            'merchantTransactionId': processingValues['merchantTransactionId'],
            'handler': response => {
                conosole.log('Payment successful', response);
                window.location = '/payment/status';
            },
            'modal': {
                'ondismiss': () => {
                    window.location.reload();
                }
            },
        });
    },

});
