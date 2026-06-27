import { Component } from '@angular/core';
import { Observable } from 'rxjs';
import { AppService } from '../services/app.service';
import { Participant } from '../participant/participant';

@Component({
  selector: 'app-participant-list',
  templateUrl: './participant-list.component.html',
  styleUrls: ['./participant-list.component.css']
})
export class ParticipantListComponent {
  readonly history$: Observable<Participant[]>;

  constructor(private appService: AppService) {
    this.history$ = this.appService.history$;
  }
}