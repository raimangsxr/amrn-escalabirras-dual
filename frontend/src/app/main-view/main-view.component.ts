import { Component, ChangeDetectionStrategy, OnDestroy, OnInit } from "@angular/core";
import { Observable, Subscription } from "rxjs";
import { AppService } from "../services/app.service";
import { EventInfo, EventService } from "../services/event.service";
import { Participant } from "../participant/participant";

@Component({
  selector: "app-main-view",
  templateUrl: "./main-view.component.html",
  styleUrls: ["./main-view.component.css"],
  changeDetection: ChangeDetectionStrategy.Eager,
  standalone: false,
})
export class MainViewComponent implements OnInit, OnDestroy {
  readonly celebrating$: Observable<Participant | null>;
  readonly error$: Observable<string | null>;
  readonly event$: Observable<EventInfo | null>;

  private readonly subscriptions = new Subscription();

  constructor(
    private appService: AppService,
    private eventService: EventService,
  ) {
    this.celebrating$ = this.appService.celebrating$;
    this.error$ = this.appService.error$;
    this.event$ = this.eventService.event$;
  }

  ngOnInit(): void {
    this.subscriptions.add(this.appService.celebrating$.subscribe());
    this.subscriptions.add(this.appService.error$.subscribe());
    this.subscriptions.add(this.eventService.event$.subscribe());
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  dismissError(): void {
    this.appService.dismissError();
  }
}
