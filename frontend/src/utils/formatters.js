export function formatCurrency(amount, currency = 'USD') {
  if (amount === undefined || amount === null || isNaN(amount)) {
    return '$0';
  }
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'USD',
      maximumFractionDigits: 0,
    }).format(num);
  } catch (e) {
    return `${currency} ${num.toLocaleString()}`;
  }
}

export function formatDate(dateString) {
  if (!dateString) return '—';
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return String(dateString);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    }).format(d);
  } catch (e) {
    return String(dateString);
  }
}

export function formatDateTime(dateString) {
  if (!dateString) return '—';
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return String(dateString);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(d);
  } catch (e) {
    return String(dateString);
  }
}

export function getFollowUpState(dateString) {
  if (!dateString) return null;
  const d = new Date(dateString);
  if (isNaN(d.getTime())) return null;

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const target = new Date(d.getFullYear(), d.getMonth(), d.getDate());

  const diffTime = target.getTime() - today.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays < 0) {
    return {
      state: 'overdue',
      label: `Overdue by ${Math.abs(diffDays)}d`,
      badgeClass: 'badge-overdue',
      color: 'text-rose-400',
    };
  } else if (diffDays === 0) {
    return {
      state: 'today',
      label: 'Due Today',
      badgeClass: 'badge-today',
      color: 'text-amber-400',
    };
  } else {
    return {
      state: 'upcoming',
      label: `In ${diffDays}d (${formatDate(dateString)})`,
      badgeClass: 'badge-upcoming',
      color: 'text-emerald-400',
    };
  }
}

export function getInitials(name) {
  if (!name) return 'EU';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}
