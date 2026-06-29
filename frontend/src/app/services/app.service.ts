import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, EMPTY, Observable } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { Participant } from '../participant/participant';

export interface BackendError {
  status: number;
  code: string;
  detail: string;
}

export interface CratesAdjustResponse {
  participant: Participant;
  is_new_record: boolean;
}

const TEAM_RED = 0;
const TEAM_BLUE = 1;

@Injectable({
  providedIn: 'root'
})
export class AppService {
  private readonly apiBaseUrl = environment.apiBaseUrl;
  private readonly celebrationDurationMs = environment.celebrationDurationMs;

  private readonly currentSlotsSubject = new BehaviorSubject<[Participant | null, Participant | null]>(
    [null, null]
  );
  private readonly top3Subject = new BehaviorSubject<Participant[]>([]);
  private readonly historySubject = new BehaviorSubject<Participant[]>([]);
  private readonly celebratingSubject = new BehaviorSubject<Participant | null>(null);
  private readonly errorSubject = new BehaviorSubject<string | null>(null);

  readonly currentSlots$ = this.currentSlotsSubject.asObservable();
  readonly top3$ = this.top3Subject.asObservable();
  readonly history$ = this.historySubject.asObservable();
  readonly celebrating$ = this.celebratingSubject.asObservable();
  readonly error$ = this.errorSubject.asObservable();

  private celebrationTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(private http: HttpClient) {
    this.bootstrap();
  }

  private bootstrap(): void {
    this.refreshHistory().subscribe({
      error: (err) => this.handleError(err, 'No se pudo cargar el historial'),
    });
    this.refreshTop3().subscribe({
      error: (err) => this.handleError(err, 'No se pudo cargar el Top 3'),
    });
  }

  createParticipant(name: string, team: 0 | 1): void {
    const trimmed = name.trim();
    if (!trimmed) {
      this.errorSubject.next('El nombre no puede estar vacío');
      return;
    }
    const slots = this.currentSlotsSubject.value;
    if (slots[team] !== null) {
      return;
    }
    this.http
      .post<Participant>(`${this.apiBaseUrl}/participants`, { name: trimmed })
      .pipe(
        tap((participant) => {
          const next: [Participant | null, Participant | null] = [null, null];
          next[TEAM_RED] = slots[TEAM_RED];
          next[TEAM_BLUE] = slots[TEAM_BLUE];
          next[team] = participant;
          this.currentSlotsSubject.next(next);
          this.refreshHistory().subscribe();
          this.refreshTop3().subscribe();
          this.clearError();
        }),
        catchError((err) => {
          this.handleError(err, 'No se pudo registrar al participante');
          return EMPTY;
        })
      )
      .subscribe();
  }

  addCrate(team: 0 | 1): void {
    const slot = this.currentSlotsSubject.value[team];
    if (!slot) {
      return;
    }
    this.http
      .post<CratesAdjustResponse>(
        `${this.apiBaseUrl}/participants/${slot.id}/crates/increment`,
        {}
      )
      .pipe(
        tap((response) => this.applyAdjustResponse(team, response)),
        catchError((err) => {
          this.handleError(err, 'No se pudo registrar la caja');
          return EMPTY;
        })
      )
      .subscribe();
  }

  removeCrate(team: 0 | 1): void {
    const slot = this.currentSlotsSubject.value[team];
    if (!slot) {
      return;
    }
    this.http
      .post<CratesAdjustResponse>(
        `${this.apiBaseUrl}/participants/${slot.id}/crates/decrement`,
        {}
      )
      .pipe(
        tap((response) => this.applyAdjustResponse(team, response)),
        catchError((err) => {
          this.handleError(err, 'No se pudo restar la caja');
          return EMPTY;
        })
      )
      .subscribe();
  }

  clearSlot(team: 0 | 1): void {
    const slots = this.currentSlotsSubject.value;
    if (slots[team] === null) {
      return;
    }
    const next: [Participant | null, Participant | null] = [slots[0], slots[1]];
    next[team] = null;
    this.currentSlotsSubject.next(next);
  }

  dismissError(): void {
    this.clearError();
  }

  private applyAdjustResponse(team: 0 | 1, response: CratesAdjustResponse): void {
    const slots = this.currentSlotsSubject.value;
    const next: [Participant | null, Participant | null] = [slots[0], slots[1]];
    next[team] = response.participant;
    this.currentSlotsSubject.next(next);
    this.refreshTop3().subscribe();
    this.clearError();

    if (response.is_new_record) {
      this.startCelebration(response.participant);
    }
  }

  private startCelebration(participant: Participant): void {
    this.celebratingSubject.next(participant);
    if (this.celebrationTimer !== null) {
      clearTimeout(this.celebrationTimer);
    }
    this.celebrationTimer = setTimeout(() => {
      this.celebratingSubject.next(null);
      this.celebrationTimer = null;
    }, this.celebrationDurationMs);
  }

  private refreshHistory(): Observable<Participant[]> {
    return this.http
      .get<Participant[]>(`${this.apiBaseUrl}/history?limit=10`)
      .pipe(tap((history) => this.historySubject.next(history)));
  }

  private refreshTop3(): Observable<Participant[]> {
    return this.http
      .get<Participant[]>(`${this.apiBaseUrl}/leaderboard/top?limit=3`)
      .pipe(tap((top) => this.top3Subject.next(top)));
  }

  private clearError(): void {
    if (this.errorSubject.value !== null) {
      this.errorSubject.next(null);
    }
  }

  private handleError(err: unknown, fallback: string): void {
    const message = this.errorMessage(err, fallback);
    this.errorSubject.next(message);
  }

  private errorMessage(err: unknown, fallback: string): string {
    if (err instanceof HttpErrorResponse) {
      if (err.status === 0) {
        return 'No se pudo contactar con el servidor';
      }
      const body = err.error as { detail?: string; code?: string } | null;
      const code = body?.code ?? '';
      if (code === 'participant_not_found') {
        return 'Participante no encontrado';
      }
      if (code === 'crates_underflow') {
        return 'No se puede bajar de 0 cajas';
      }
      if (code === 'invalid_name') {
        return 'Nombre inválido (1-20 caracteres)';
      }
      if (code === 'validation_error') {
        return 'Solicitud inválida';
      }
      // Do not leak the backend's raw `detail` (e.g. "invalid token:
      // Signature verification failed") to the operator. Fall back to
      // the caller-provided message.
      return fallback;
    }
    return fallback;
  }
}

export const TEAM_RED_INDEX = TEAM_RED;
export const TEAM_BLUE_INDEX = TEAM_BLUE;