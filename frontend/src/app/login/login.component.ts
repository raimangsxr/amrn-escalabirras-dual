import { Component, ChangeDetectionStrategy } from "@angular/core";
import { Router } from "@angular/router";
import { AuthService } from "../auth/auth.service";

@Component({
  selector: "app-login",
  templateUrl: "./login.component.html",
  styleUrls: ["./login.component.css"],
  changeDetection: ChangeDetectionStrategy.Eager,
  standalone: false,
})
export class LoginComponent {
  password = "";
  errorMessage: string | null = null;
  busy = false;

  constructor(
    private auth: AuthService,
    private router: Router,
  ) {}

  submit(): void {
    if (this.busy) {
      return;
    }
    this.busy = true;
    this.errorMessage = null;
    this.auth.login(this.password).subscribe({
      next: () => {
        this.busy = false;
        void this.router.navigate(["/"]);
      },
      error: (err: Error) => {
        this.busy = false;
        this.errorMessage = err.message;
      },
    });
  }
}
