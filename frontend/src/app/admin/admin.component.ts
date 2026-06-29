import {
  Component,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  OnDestroy,
  OnInit,
} from "@angular/core";
import { Router } from "@angular/router";
import { Subscription } from "rxjs";
import { AuthService } from "../auth/auth.service";
import { EventInfo, EventService } from "../services/event.service";

@Component({
  selector: "app-admin",
  templateUrl: "./admin.component.html",
  styleUrls: ["./admin.component.css"],
  changeDetection: ChangeDetectionStrategy.Eager,
  standalone: false,
})
export class AdminComponent implements OnInit, OnDestroy {
  title = "";
  subtitle = "";
  busy = false;
  saved = false;
  errorMessage: string | null = null;

  private readonly subscriptions = new Subscription();

  constructor(
    private auth: AuthService,
    private router: Router,
    private eventService: EventService,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.subscriptions.add(
      this.eventService.event$.subscribe((event) => {
        if (event && !this.title && !this.subtitle) {
          this.title = event.title;
          this.subtitle = event.subtitle;
          this.cdr.markForCheck();
        }
      }),
    );
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  canSave(): boolean {
    return (
      !this.busy &&
      this.title.trim().length > 0 &&
      this.subtitle.trim().length > 0 &&
      this.title.trim().length <= 80 &&
      this.subtitle.trim().length <= 80
    );
  }

  save(): void {
    if (!this.canSave()) {
      return;
    }
    this.busy = true;
    this.errorMessage = null;
    this.saved = false;
    this.eventService.update(this.title.trim(), this.subtitle.trim()).subscribe({
      next: (event: EventInfo) => {
        this.busy = false;
        this.title = event.title;
        this.subtitle = event.subtitle;
        this.saved = true;
        this.cdr.markForCheck();
      },
      error: (err: { status: number; detail?: string }) => {
        this.busy = false;
        this.errorMessage = err.detail ?? "No se pudo guardar la información";
        this.cdr.markForCheck();
      },
    });
  }

  logout(): void {
    this.auth.logout();
    void this.router.navigate(["/login"]);
  }
}
