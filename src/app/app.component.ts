import { Component, OnInit, ChangeDetectionStrategy } from "@angular/core";
import { AuthService } from "./auth/auth.service";
import { LayoutService } from "./services/layout.service";

@Component({
  selector: "app-root",
  template: `<router-outlet></router-outlet>`,
  styles: [
    `
      :host {
        display: block;
        height: 100%;
        min-height: 0;
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.Eager,
  standalone: false,
})
export class AppComponent implements OnInit {
  constructor(
    private auth: AuthService,
    // LayoutService is injected so its constructor runs and the
    // ResizeObserver is wired up for the lifetime of the app.
    private layout: LayoutService,
  ) {}

  ngOnInit(): void {
    void this.auth.bootstrap();
  }
}
