import {
  HTTP_INTERCEPTORS,
  provideHttpClient,
  withInterceptorsFromDi,
  withXhr,
} from "@angular/common/http";
import { NgModule } from "@angular/core";
import { BrowserModule } from "@angular/platform-browser";
import { FormsModule } from "@angular/forms";
import { BrowserAnimationsModule } from "@angular/platform-browser/animations";

import { AppRoutingModule } from "./app-routing.module";
import { AppComponent } from "./app.component";
import { ParticipantComponent } from "./participant/participant.component";
import { ParticipantListComponent } from "./participant-list/participant-list.component";
import { Top3Component } from "./top3/top3.component";
import { ManagerComponent } from "./manager/manager.component";
import { WinnerComponent } from "./winner/winner.component";
import { TeamManagerRedComponent } from "./team-manager-red/team-manager-red.component";
import { TeamManagerBlueComponent } from "./team-manager-blue/team-manager-blue.component";
import { LoginComponent } from "./login/login.component";
import { MainViewComponent } from "./main-view/main-view.component";
import { TokensComponent } from "./tokens/tokens.component";
import { authInterceptor } from "./auth/auth.interceptor";

@NgModule({
  declarations: [
    AppComponent,
    ParticipantComponent,
    ParticipantListComponent,
    Top3Component,
    ManagerComponent,
    WinnerComponent,
    TeamManagerRedComponent,
    TeamManagerBlueComponent,
    LoginComponent,
    MainViewComponent,
    TokensComponent,
  ],
  bootstrap: [AppComponent],
  imports: [
    BrowserModule,
    AppRoutingModule,
    FormsModule,
    BrowserAnimationsModule,
  ],
  providers: [
    {
      provide: HTTP_INTERCEPTORS,
      useValue: { intercept: authInterceptor },
      multi: true,
    },
    provideHttpClient(withXhr(), withInterceptorsFromDi()),
  ],
})
export class AppModule {}
