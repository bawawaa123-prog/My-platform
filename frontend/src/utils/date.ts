/**
 * Ensure a datetime string has UTC timezone info so new Date() interprets it as UTC.
 * Naive strings (no "Z" or offset) get "Z" appended.
 */
export function parseApiDateTime(value: string | null | undefined): Date | null {
  if (!value) return null;

  // Already has timezone offset or "Z" — use as-is
  if (/[Z+-]\d{2}:\d{2}$/.test(value) || value.endsWith("Z")) {
    const d = new Date(value);
    return isNaN(d.getTime()) ? null : d;
  }

  // Naive datetime — treat as UTC by appending "Z"
  const d = new Date(value + "Z");
  return isNaN(d.getTime()) ? null : d;
}

/**
 * Format a datetime string for display in zh-CN locale.
 * Handles naive strings by treating them as UTC.
 */
export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "Not available";

  const date = parseApiDateTime(value);
  if (!date) return "Not available";

  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}
