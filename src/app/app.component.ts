import { Component } from '@angular/core';
import { AppService } from './services/app.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'II Torneo Motero de Escalabirras por equipos';
  subtitle = 'XV Concentración Motera Ría de Noia';

  constructor(private appService: AppService) {}

  getNewRecord(): any {
    return this.appService.getNewRecord();
  }

}
