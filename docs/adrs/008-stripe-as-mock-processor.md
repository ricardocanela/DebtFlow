# ADR-008: Stripe as Mock Payment Processor

**Date:** 2025-02-10

**Status:** Accepted

## Context

DebtFlow requires a payment processing integration to handle debtor payments
(one-time and recurring). In production, Aktos integrates with specialized
debt collection payment processors. For the purposes of this project (DebtFlow),
we need a payment processor integration that:

- Demonstrates real-world integration patterns (tokenization, webhooks, idempotency).
- Provides a sandbox/test mode for development without real money movement.
- Has well-documented APIs that are easy to onboard with.
- Simulates the type of processor interface Aktos uses in production.

Options considered:

- **Custom mock server:** Build a fake payment API. Full control but high
  maintenance cost and no realistic edge case simulation.
- **Stripe test mode:** Use Stripe's sandbox environment with test card numbers.
  Industry-leading documentation and realistic behavior.
- **Square sandbox:** Similar to Stripe but less comprehensive documentation
  and smaller ecosystem.

## Decision

We will use **Stripe in test mode** as the mock payment processor for DebtFlow.

Integration design:

- `PaymentProcessor` abstract base class defines the interface (charge,
  refund, create_customer, create_payment_method, create_subscription).
- `StripeProcessor` implements this interface using the Stripe Python SDK.
- All Stripe API calls use idempotency keys derived from internal transaction IDs.
- Stripe webhooks are received at `/api/webhooks/stripe/` and processed
  asynchronously via Celery tasks.
- Webhook signature verification enforced on all incoming events.

Key Stripe features used:

- **Payment Intents** for one-time payments.
- **Subscriptions** for recurring payment plans.
- **Test clocks** for simulating subscription lifecycle events.
- **Webhook event types:** `payment_intent.succeeded`, `payment_intent.payment_failed`,
  `invoice.payment_succeeded`, `invoice.payment_failed`.

## Consequences

**Positive:**

- Stripe's test mode provides realistic payment flow simulation including
  edge cases (declines, disputes, network errors) via special test card numbers.
- Excellent documentation reduces onboarding time for developers.
- The `PaymentProcessor` abstraction makes the Stripe dependency swappable.
  Replacing Stripe with a production debt collection processor requires only
  a new implementation of the interface.
- Stripe webhooks exercise the same asynchronous event handling patterns
  that production payment processors use.
- Test clocks enable deterministic testing of subscription billing cycles
  without waiting for real time to pass.

**Negative:**

- Stripe's API semantics do not perfectly mirror debt collection payment
  processors. Some translation will be needed when swapping to a production
  processor.
- Stripe test mode has rate limits that may affect load testing.
- Team members unfamiliar with Stripe must learn its API model, though
  documentation quality mitigates this.

**Mitigations:**

- `PaymentProcessor` interface designed around debt collection payment
  concepts, not Stripe-specific concepts. The adapter layer handles
  translation.
- Integration tests run against Stripe test mode in CI with a dedicated
  test API key.
- Load tests use the mock server fallback if Stripe rate limits are hit.
