import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of, throwError } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface Session {
  token: string;
  expiresAt: Date;
}

interface LoginResponse {
  session_token: string;
  expires_at: string;
}

interface EmbedTokenExchangeResponse {
  session_token: string;
  expires_at: string;
}

interface StoredSession {
  token: string;
  expiresAt: string;
}

const STORAGE_KEY = environment.sessionStorageKey;

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly apiBaseUrl = environment.apiBaseUrl;
  private readonly sessionSubject = new BehaviorSubject<Session | null>(null);

  readonly session$: Observable<Session | null> = this.sessionSubject.asObservable();
  readonly isAuthenticated$: Observable<boolean> = this.session$.pipe(
    map((session) => session !== null)
  );

  constructor(private http: HttpClient) {}

  async bootstrap(): Promise<void> {
    this.restoreFromStorage();
    if (this.sessionSubject.value !== null) {
      return;
    }
    const params = new URLSearchParams(window.location.search);
    const embedToken = params.get(environment.embedTokenQueryParam);
    if (embedToken) {
      this.stripEmbedTokenFromUrl();
      try {
        await this.exchangeEmbedToken(embedToken).toPromise();
      } catch {
        // Make sure no stale session is reused after a failed exchange.
        this.clearSession();
      }
    }
  }

  login(password: string): Observable<Session> {
    return this.http
      .post<LoginResponse>(`${this.apiBaseUrl}/auth/login`, { password })
      .pipe(
        map((r) => this.toSession(r.session_token, r.expires_at)),
        tap((session) => this.acceptSession(session)),
        catchError((err) => this.translateLoginError(err))
      );
  }

  exchangeEmbedToken(token: string): Observable<Session> {
    return this.http
      .post<EmbedTokenExchangeResponse>(
        `${this.apiBaseUrl}/auth/embed-token`,
        { token }
      )
      .pipe(
        map((r) => this.toSession(r.session_token, r.expires_at)),
        tap((session) => this.acceptSession(session)),
        catchError((err) => this.translateEmbedTokenError(err))
      );
  }

  logout(): void {
    const token = this.getToken();
    if (token) {
      this.http
        .post(`${this.apiBaseUrl}/auth/logout`, {})
        .pipe(catchError(() => of(null)))
        .subscribe();
    }
    this.clearSession();
  }

  getToken(): string | null {
    return this.sessionSubject.value?.token ?? null;
  }

  private acceptSession(session: Session): void {
    this.sessionSubject.next(session);
    try {
      const stored: StoredSession = {
        token: session.token,
        expiresAt: session.expiresAt.toISOString(),
      };
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
    } catch {
      // sessionStorage unavailable (private mode etc.); session lives only in memory.
    }
  }

  private clearSession(): void {
    this.sessionSubject.next(null);
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
  }

  private restoreFromStorage(): void {
    let raw: string | null = null;
    try {
      raw = sessionStorage.getItem(STORAGE_KEY);
    } catch {
      return;
    }
    if (!raw) {
      return;
    }
    try {
      const stored = JSON.parse(raw) as StoredSession;
      const expiresAt = new Date(stored.expiresAt);
      if (Number.isNaN(expiresAt.getTime()) || expiresAt.getTime() <= Date.now()) {
        sessionStorage.removeItem(STORAGE_KEY);
        return;
      }
      this.sessionSubject.next({ token: stored.token, expiresAt });
    } catch {
      sessionStorage.removeItem(STORAGE_KEY);
    }
  }

  private stripEmbedTokenFromUrl(): void {
    const url = new URL(window.location.href);
    url.searchParams.delete(environment.embedTokenQueryParam);
    const newUrl = url.pathname + (url.search ? url.search : '') + url.hash;
    window.history.replaceState({}, '', newUrl);
  }

  private toSession(token: string, expiresAt: string): Session {
    return { token, expiresAt: new Date(expiresAt) };
  }

  private translateLoginError(err: unknown): Observable<never> {
    if (err instanceof HttpErrorResponse && err.status === 401) {
      return throwError(() => new Error('Contraseña incorrecta'));
    }
    if (err instanceof HttpErrorResponse && err.status === 0) {
      return throwError(() => new Error('No se pudo contactar con el servidor'));
    }
    return throwError(() => new Error('Error inesperado al iniciar sesión'));
  }

  private translateEmbedTokenError(err: unknown): Observable<never> {
    if (err instanceof HttpErrorResponse && err.status === 401) {
      return throwError(() => new Error('Token no válido o revocado'));
    }
    if (err instanceof HttpErrorResponse && err.status === 0) {
      return throwError(() => new Error('No se pudo contactar con el servidor'));
    }
    return throwError(() => new Error('Error inesperado al canjear el token'));
  }
}