import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

export function formatDate(value: string | null | undefined): string {
  if (!value) return '—';
  return dayjs(value).format('MMM D, YYYY');
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—';
  return dayjs(value).format('MMM D, YYYY h:mm A');
}

export function formatRelativeTime(value: string | null | undefined): string {
  if (!value) return '—';
  return dayjs(value).fromNow();
}

export function isOverdue(dueDate: string | null | undefined): boolean {
  if (!dueDate) return false;
  return dayjs(dueDate).isBefore(dayjs(), 'day');
}

export function daysSince(date: string | null | undefined): number | null {
  if (!date) return null;
  return dayjs().diff(dayjs(date), 'day');
}
