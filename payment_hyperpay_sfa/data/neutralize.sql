-- disable hyperpay payment provider
UPDATE payment_provider
   SET hyperpay_entity_id = NULL,
       hyperpay_auth_key = NULL;
