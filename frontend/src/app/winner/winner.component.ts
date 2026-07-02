import {
  Component,
  Input,
  ChangeDetectionStrategy,
  OnDestroy,
  OnInit,
} from "@angular/core";
import { Observable, Subscription } from "rxjs";
import {
  HeightBucket,
  LayoutBucket,
  LayoutService,
} from "../services/layout.service";
import { Participant } from "../participant/participant";

@Component({
  selector: "app-winner",
  templateUrl: "./winner.component.html",
  styleUrls: ["./winner.component.css"],
  changeDetection: ChangeDetectionStrategy.Eager,
  standalone: false,
})
export class WinnerComponent implements OnInit, OnDestroy {
  @Input() participant: Participant | null = null;

  readonly layoutClass$: Observable<LayoutBucket>;
  layoutClass: LayoutBucket = "layout-wide-tall";
  heightBucket: HeightBucket = "tall";

  private readonly subscriptions = new Subscription();

  constructor(private layoutService: LayoutService) {
    this.layoutClass$ = this.layoutService.layoutClass$;
  }

  ngOnInit(): void {
    this.subscriptions.add(
      this.layoutService.layoutClass$.subscribe((bucket) => {
        this.layoutClass = bucket;
        const suffix = bucket.slice(bucket.lastIndexOf("-") + 1);
        this.heightBucket =
          suffix === "short" || suffix === "medium" || suffix === "tall"
            ? suffix
            : "tall";
      }),
    );
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  flipBackground(): boolean {
    return Math.random() > 0.5;
  }

  isShort(): boolean {
    return this.heightBucket === "short";
  }

  isMedium(): boolean {
    return this.heightBucket === "medium";
  }
}
