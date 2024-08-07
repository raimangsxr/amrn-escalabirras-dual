import { NgModule } from "@angular/core";
import { BrowserModule } from "@angular/platform-browser";

import { AppRoutingModule } from "./app-routing.module";
import { AppComponent } from "./app.component";
import { FormsModule } from "@angular/forms";
import { BrowserAnimationsModule } from "@angular/platform-browser/animations";
import { MatIconModule } from "@angular/material/icon";
import { ParticipantComponent } from "./participant/participant.component";
import { ParticipantListComponent } from "./participant-list/participant-list.component";
import { Top3Component } from "./top3/top3.component";
import { ManagerComponent } from "./manager/manager.component";
import { WinnerComponent } from './winner/winner.component';
import { TeamManagerRedComponent } from './team-manager-red/team-manager-red.component';
import { TeamManagerBlueComponent } from './team-manager-blue/team-manager-blue.component';

@NgModule({
  declarations: [
    AppComponent,
    ParticipantComponent,
    ParticipantListComponent,
    Top3Component,
    ManagerComponent,
    WinnerComponent,
    TeamManagerRedComponent,
    TeamManagerBlueComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    FormsModule,
    BrowserAnimationsModule,
    MatIconModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
