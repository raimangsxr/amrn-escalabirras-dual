import {
  Component,
  ChangeDetectionStrategy,
  OnDestroy,
  OnInit,
} from "@angular/core";
import { Observable, Subscription } from "rxjs";
import { AppService } from "../services/app.service";
import { EventInfo, EventService } from "../services/event.service";
import {
  HeightBucket,
  LayoutBucket,
  LayoutService,
} from "../services/layout.service";
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
  readonly layoutClass$: Observable<LayoutBucket>;

  layoutClass: LayoutBucket = "layout-wide-tall";
  heightBucket: HeightBucket = "tall";

  private readonly subscriptions = new Subscription();

  constructor(
    private appService: AppService,
    private eventService: EventService,
    private layoutService: LayoutService,
  ) {
    this.celebrating$ = this.appService.celebrating$;
    this.error$ = this.appService.error$;
    this.event$ = this.eventService.event$;
    this.layoutClass$ = this.layoutService.layoutClass$;
  }

  ngOnInit(): void {
    this.subscriptions.add(this.appService.celebrating$.subscribe());
    this.subscriptions.add(this.appService.error$.subscribe());
    this.subscriptions.add(this.eventService.event$.subscribe());
    this.subscriptions.add(
      this.layoutService.layoutClass$.subscribe((bucket) => {
        this.layoutClass = bucket;
        this.heightBucket = this.extractHeight(bucket);
      }),
    );
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  dismissError(): void {
    this.appService.dismissError();
  }

  isShort(): boolean {
    return this.heightBucket === "short";
  }

  isMedium(): boolean {
    return this.heightBucket === "medium";
  }

  private extractHeight(bucket: LayoutBucket): HeightBucket {
    const suffix = bucket.slice(bucket.lastIndexOf("-") + 1);
    if (suffix === "short" || suffix === "medium" || suffix === "tall") {
      return suffix;
    }
    return "tall";
  }
}
