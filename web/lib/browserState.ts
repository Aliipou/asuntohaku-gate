/**
 * Small per-browser conveniences, all client-only and all optional to the
 * flows they support:
 *
 * - a session key for the anonymous favourites/saved-searches lists
 *   (api/app/routers/portal.py — "authenticates nobody and grants access to
 *   nothing but its own list", so it is fine to hold in localStorage)
 * - the most recently used application edit token, so returning to "/" on
 *   the same device/browser can offer "jatka hakemusta" without the visitor
 *   having to keep the muokkauslinkki (edit link) handy
 *
 * Neither is the system of record: an application's real, durable address is
 * its edit-link URL (/hakemus/[token]), which works from any device. Losing
 * localStorage loses nothing but this shortcut.
 */

import { createApplication, getApplication } from "./api";

const SESSION_KEY_STORAGE = "ahg_session_key";
const APPLICATION_TOKEN_STORAGE = "ahg_application_token";

function readLocalStorage(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeLocalStorage(key: string, value: string): void {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // Private browsing, blocked storage, etc. — the feature this backs is a
    // convenience, so silently doing nothing is the correct degradation.
  }
}

/** A stable per-browser id (min length 8, per FavouriteIn/SavedSearchIn). Created on first use. */
export function getSessionKey(): string {
  const existing = readLocalStorage(SESSION_KEY_STORAGE);
  if (existing) return existing;
  const created = crypto.randomUUID();
  writeLocalStorage(SESSION_KEY_STORAGE, created);
  return created;
}

export function getStoredApplicationToken(): string | null {
  return readLocalStorage(APPLICATION_TOKEN_STORAGE);
}

export function setStoredApplicationToken(token: string): void {
  writeLocalStorage(APPLICATION_TOKEN_STORAGE, token);
}

/**
 * The token backing "Lisää hakemukseen" / "Varaa näyttöaika": reuses the
 * stored one if it still resolves to a real application, otherwise starts a
 * fresh one (a stored token can go stale — the application expired, or this
 * is a different environment's data). Never throws; a failure to create an
 * application propagates to the caller, which already handles API errors.
 */
export async function ensureApplicationToken(): Promise<string> {
  const existing = getStoredApplicationToken();
  if (existing) {
    try {
      await getApplication(existing);
      return existing;
    } catch {
      // Stale or invalid — fall through and start a new application.
    }
  }
  const created = await createApplication();
  setStoredApplicationToken(created.edit_token);
  return created.edit_token;
}
