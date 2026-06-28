import { Component, Input, ChangeDetectionStrategy } from "@angular/core";
import { Participant } from "../participant/participant";

@Component({
  selector: "app-winner",
  templateUrl: "./winner.component.html",
  styleUrls: ["./winner.component.css"],
  changeDetection: ChangeDetectionStrategy.Eager,
  standalone: false,
})
export class WinnerComponent {
  @Input() participant: Participant | null = null;

  flipBackground(): boolean {
    return Math.random() > 0.5;
  }
}
