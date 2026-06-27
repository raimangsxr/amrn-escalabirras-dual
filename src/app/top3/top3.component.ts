import { Component } from '@angular/core';
import { Observable } from 'rxjs';
import { Participant } from '../participant/participant';
import { AppService } from '../services/app.service';

@Component({
  selector: 'app-top3',
  templateUrl: './top3.component.html',
  styleUrls: ['./top3.component.css']
})
export class Top3Component {
  readonly top3$: Observable<Participant[]>;

  constructor(private appService: AppService) {
    this.top3$ = this.appService.top3$;
  }

  trackById(_index: number, item: Participant | null): number {
    return item?.id ?? -1;
  }
}