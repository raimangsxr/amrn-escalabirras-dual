import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';
import { AuthService } from '../auth/auth.service';
import { AppService } from '../services/app.service';
import { Participant } from '../participant/participant';

@Component({
  selector: 'app-main-view',
  templateUrl: './main-view.component.html',
  styleUrls: ['./main-view.component.css']
})
export class MainViewComponent {
  title = 'II Torneo Motero de Escalabirras';
  subtitle = 'XV Concentración Motera Ría de Noia';

  readonly celebrating$: Observable<Participant | null>;
  readonly error$: Observable<string | null>;

  showTokens = false;

  constructor(
    private auth: AuthService,
    private router: Router,
    private appService: AppService
  ) {
    this.celebrating$ = this.appService.celebrating$;
    this.error$ = this.appService.error$;
  }

  openTokens(): void {
    this.showTokens = true;
  }

  closeTokens(): void {
    this.showTokens = false;
  }

  dismissError(): void {
    this.appService.dismissError();
  }

  logout(): void {
    this.auth.logout();
    void this.router.navigate(['/login']);
  }
}