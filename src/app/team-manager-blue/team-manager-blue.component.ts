import {
  Component,
  EventEmitter,
  Output,
  ChangeDetectionStrategy,
} from "@angular/core";
import { Participant } from "../participant/participant";
import { AppService } from "../services/app.service";

@Component({
  selector: "app-team-manager-blue",
  templateUrl: "./team-manager-blue.component.html",
  styleUrls: ["./team-manager-blue.component.css"],
  changeDetection: ChangeDetectionStrategy.Eager,
  standalone: false,
})
export class TeamManagerBlueComponent {
  @Output() newParticipantEvent = new EventEmitter<string>();

  name: string = "";

  constructor(private appService: AppService) {}

  readonly slot$ = this.appService.currentSlots$;

  createParticipant(): void {
    const trimmed = this.name.trim();
    if (!trimmed) {
      return;
    }
    this.newParticipantEvent.emit(trimmed);
    this.name = "";
  }

  trackById(_index: number, item: Participant | null): number {
    return item?.id ?? -1;
  }
}
