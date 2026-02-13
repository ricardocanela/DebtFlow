/** Matches Payment.Status choices. */
export type PaymentStatus = 'pending' | 'completed' | 'failed' | 'refunded';

/** Matches Payment.Method choices. */
export type PaymentMethod = 'card' | 'bank_transfer' | 'check' | 'cash';

/** Matches PaymentSerializer fields. */
export interface Payment {
  id: string;
  account: string;
  processor: string;
  processor_name: string;
  amount: string;
  payment_method: PaymentMethod;
  status: PaymentStatus;
  processor_ref: string | null;
  idempotency_key: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

/** Matches PaymentCreateSerializer fields. */
export interface PaymentCreatePayload {
  account: string;
  processor: string;
  amount: number;
  payment_method: PaymentMethod;
}

/** Matches PaymentProcessorSerializer fields. */
export interface PaymentProcessor {
  id: string;
  name: string;
  slug: string;
  api_base_url: string;
  is_active: boolean;
  created_at: string;
}

/** Matches RefundSerializer fields. */
export interface RefundPayload {
  reason?: string;
}
