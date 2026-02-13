import { Form, Modal, InputNumber, Select, message } from 'antd';
import { useCreatePaymentMutation } from '@/api/paymentsApi';
import { useGetPaymentProcessorsQuery } from '@/api/paymentsApi';
import { PAYMENT_METHOD_LABELS, ALL_PAYMENT_METHODS } from '@/utils/constants';

interface RecordPaymentModalProps {
  open: boolean;
  onClose: () => void;
  accountId: string;
}

interface PaymentFormValues {
  amount: number;
  payment_method: string;
  processor: string;
}

export function RecordPaymentModal({ open, onClose, accountId }: RecordPaymentModalProps) {
  const [form] = Form.useForm<PaymentFormValues>();
  const [createPayment, { isLoading }] = useCreatePaymentMutation();
  const { data: processors } = useGetPaymentProcessorsQuery();

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      await createPayment({
        account: accountId,
        processor: values.processor,
        amount: values.amount,
        payment_method: values.payment_method as never,
      }).unwrap();
      message.success('Payment recorded');
      form.resetFields();
      onClose();
    } catch {
      message.error('Failed to record payment');
    }
  };

  return (
    <Modal
      title="Record Payment"
      open={open}
      onOk={handleSubmit}
      onCancel={onClose}
      confirmLoading={isLoading}
      okText="Record Payment"
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="amount"
          label="Amount"
          rules={[
            { required: true, message: 'Amount is required' },
            { type: 'number', min: 0.01, message: 'Amount must be positive' },
          ]}
        >
          <InputNumber
            prefix="$"
            style={{ width: '100%' }}
            precision={2}
            placeholder="0.00"
          />
        </Form.Item>
        <Form.Item
          name="payment_method"
          label="Payment Method"
          rules={[{ required: true, message: 'Select a payment method' }]}
        >
          <Select
            placeholder="Select method"
            options={ALL_PAYMENT_METHODS.map((m) => ({
              value: m,
              label: PAYMENT_METHOD_LABELS[m],
            }))}
          />
        </Form.Item>
        <Form.Item
          name="processor"
          label="Processor"
          rules={[{ required: true, message: 'Select a processor' }]}
        >
          <Select
            placeholder="Select processor"
            options={(processors || []).map((p) => ({
              value: p.id,
              label: p.name,
            }))}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}
