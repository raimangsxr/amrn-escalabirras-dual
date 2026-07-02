import { HttpClient, HttpErrorResponse } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { BehaviorSubject, EMPTY, Observable, firstValueFrom } from "rxjs";
import { catchError, tap } from "rxjs/operators";
import { environment } from "../../environments/environment";

export interface EventInfo {
  id: number;
  title: string;
  subtitle: string;
  updated_at: string;
}

@Injectable({ providedIn: "root" })
export class EventService {
  private readonly apiBaseUrl = environment.apiBaseUrl;

  private readonly eventSubject = new BehaviorSubject<EventInfo | null>(null);
  readonly event$: Observable<EventInfo | null> = this.eventSubject.asObservable();

  constructor(private http: HttpClient) {}

  async bootstrap(): Promise<void> {
    try {
      const event = await firstValueFrom(
        this.http
          .get<EventInfo>(`${this.apiBaseUrl}/event`)
          .pipe(catchError((err: HttpErrorResponse) => {
            if (err.status === 404) {
              this.eventSubject.next(null);
              return EMPTY;
            }
            throw err;
          })),
      );
      this.eventSubject.next(event);
    } catch (err) {
      this.eventSubject.next(null);
      throw err;
    }
  }

  update(title: string, subtitle: string): Observable<EventInfo> {
    return this.http
      .put<EventInfo>(`${this.apiBaseUrl}/event`, { title, subtitle })
      .pipe(tap((event) => this.eventSubject.next(event)));
  }
}
