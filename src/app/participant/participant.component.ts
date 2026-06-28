import { Component, Input, ChangeDetectionStrategy } from "@angular/core";
import { Participant } from "./participant";

@Component({
  selector: "app-participant",
  templateUrl: "./participant.component.html",
  styleUrls: ["./participant.component.css"],
  changeDetection: ChangeDetectionStrategy.Eager,
  standalone: false,
})
export class ParticipantComponent {
  @Input() participant!: Participant;
}
