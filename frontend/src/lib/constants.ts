const FALLBACK_CONTACT_URL = 'https://wa.me/5511999999999';

export function getSafeContactUrl(rawUrl = import.meta.env.VITE_CONTACT_URL): string {
  const value = rawUrl || FALLBACK_CONTACT_URL;

  try {
    const url = new URL(value);
    const isAllowedWhatsAppHost = url.hostname === 'wa.me' || url.hostname === 'api.whatsapp.com';
    const isHttps = url.protocol === 'https:';

    if (isHttps && isAllowedWhatsAppHost) {
      return url.toString();
    }
  } catch {
    return FALLBACK_CONTACT_URL;
  }

  return FALLBACK_CONTACT_URL;
}

export function buildWhatsAppContactUrl(message: string, rawUrl = CONTACT_URL): string {
  const url = new URL(getSafeContactUrl(rawUrl));

  if (url.hostname === 'wa.me') {
    url.searchParams.set('text', message);
  } else {
    url.searchParams.set('text', message);
  }

  return url.toString();
}

export const CONTACT_URL = getSafeContactUrl();
