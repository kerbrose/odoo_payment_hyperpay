/** @odoo-module */

import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { onMounted, useRef } from "@odoo/owl";


export class HyperpayDialog extends ConfirmationDialog {
    static props = {
        ...ConfirmationDialog.props,
        HyperpayEL: { type: String },
    };
    static template = "payment_hyperpay_sfa.ConfirmationDialog";

    setup() {
        super.setup();
        this.hyperpaygatwayel = useRef("hyperpaygatewayel");
        onMounted(this._appendHyperpayEl);
    }

    _appendHyperpayEl() {
        let hyperpayIframe = document.createElement("iframe");
        hyperpayIframe.id = "hyperpay_iframe";
        hyperpayIframe.style = "display:none";
        hyperpayIframe.src = this.props.HyperpayEL;
        this.hyperpaygatwayel.el.appendChild(hyperpayIframe);
    }

}
