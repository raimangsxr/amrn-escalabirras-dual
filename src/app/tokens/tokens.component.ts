import { HttpClient, HttpErrorResponse } from "@angular/common/http";
import {
  Component,
  EventEmitter,
  OnInit,
  Output,
  ChangeDetectionStrategy,
} from "@angular/core";
import { Observable, Subject } from "rxjs";
import { catchError, map, startWith, switchMap, tap } from "rxjs/operators";
import { environment } from "../../environments/environment";

interface EmbedTokenListItem {
  id: number;
  name: string;
  created_at: string;
  last_used_at: string | null;
  revoked_at: string | null;
}

interface EmbedTokenCreatedResponse {
  id: number;
  name: string;
  token: string;
  created_at: string;
}

interface ListResponse {
  tokens: EmbedTokenListItem[];
}

@Component({
  selector: "app-tokens",
  templateUrl: "./tokens.component.html",
  styleUrls: ["./tokens.component.css"],
  changeDetection: ChangeDetectionStrategy.Eager,
  standalone: false,
})
export class TokensComponent implements OnInit {
  @Output() closeRequested = new EventEmitter<void>();

  newName = "";
  newToken: string | null = null;
  errorMessage: string | null = null;
  list: EmbedTokenListItem[] = [];
  busy = false;

  private readonly refresh$ = new Subject<void>();

  readonly tokens$: Observable<EmbedTokenListItem[]> = this.refresh$.pipe(
    startWith(undefined),
    switchMap(() => this.fetchList()),
  );

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.tokens$.subscribe({
      next: (list) => (this.list = list),
      error: (err: Error) => (this.errorMessage = err.message),
    });
  }

  close(): void {
    this.closeRequested.emit();
  }

  create(): void {
    if (this.busy) {
      return;
    }
    this.busy = true;
    this.errorMessage = null;
    this.http
      .post<EmbedTokenCreatedResponse>(`${environment.apiBaseUrl}/tokens`, {
        name: this.newName.trim(),
      })
      .pipe(
        tap((response) => {
          this.newToken = response.token;
          this.newName = "";
          this.busy = false;
          this.refresh$.next();
        }),
        catchError((err: HttpErrorResponse) => {
          this.busy = false;
          this.errorMessage = this.translateError(err);
          return [];
        }),
      )
      .subscribe();
  }

  revoke(id: number): void {
    if (this.busy) {
      return;
    }
    this.busy = true;
    this.errorMessage = null;
    this.http
      .delete(`${environment.apiBaseUrl}/tokens/${id}`)
      .pipe(
        tap(() => {
          this.busy = false;
          this.refresh$.next();
        }),
        catchError((err: HttpErrorResponse) => {
          this.busy = false;
          this.errorMessage = this.translateError(err);
          return [];
        }),
      )
      .subscribe();
  }

  copy(): void {
    if (!this.newToken) {
      return;
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(this.newToken).catch(() => {
        this.errorMessage =
          "No se pudo copiar. Selecciona el texto manualmente.";
      });
      return;
    }
    // Fallback: select the code element so the operator can copy manually.
    const selection = window.getSelection();
    if (!selection) {
      this.errorMessage = "No se pudo copiar. Selecciona el texto manualmente.";
      return;
    }
    selection.removeAllRanges();
    const range = document.createRange();
    const codeEl = document.querySelector("code.token-preview");
    if (codeEl) {
      range.selectNode(codeEl);
      selection.addRange(range);
    }
  }

  trackById(_index: number, item: EmbedTokenListItem): number {
    return item.id;
  }

  private fetchList(): Observable<EmbedTokenListItem[]> {
    return this.http
      .get<ListResponse>(`${environment.apiBaseUrl}/tokens`)
      .pipe(map((r) => r.tokens));
  }

  private translateError(err: HttpErrorResponse): string {
    if (err.status === 0) {
      return "No se pudo contactar con el servidor";
    }
    const body = err.error as { detail?: string } | null;
    return body?.detail ?? "Error inesperado";
  }
}
