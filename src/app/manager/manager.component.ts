import {
  Component,
  ElementRef,
  ViewChild,
  ChangeDetectionStrategy,
} from "@angular/core";
import { AppService } from "../services/app.service";

@Component({
  selector: "app-manager",
  templateUrl: "./manager.component.html",
  styleUrls: ["./manager.component.css"],
  changeDetection: ChangeDetectionStrategy.Eager,
  standalone: false,
})
export class ManagerComponent {
  @ViewChild("fin", { static: true }) finField!: ElementRef;

  constructor(private appService: AppService) {}

  addParticipant(name: string, team: 0 | 1): void {
    this.appService.createParticipant(name, team);
  }

  addCrate(team: 0 | 1): void {
    this.appService.addCrate(team);
  }

  removeCrate(team: 0 | 1): void {
    this.appService.removeCrate(team);
  }

  clearSlot(team: 0 | 1): void {
    this.appService.clearSlot(team);
  }
}
