const pad = (n) => String(n).padStart(2, "0");

export function toInputValue(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function toApiValue(local) {
  return local ? new Date(local).toISOString() : null;
}

export function formatDateTime(iso) {
  return new Date(iso).toLocaleString("es-ES", {
    dateStyle: "short",
    timeStyle: "short",
  });
}