import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from './auth.service';

const PUBLIC_AUTH_PATHS = ['/v1/auth/login', '/v1/auth/embed-token'];

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const token = auth.getToken();

  const authedReq = token
    ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : req;

  return next(authedReq).pipe(
    catchError((err) => {
      if (
        err instanceof HttpErrorResponse &&
        err.status === 401 &&
        !PUBLIC_AUTH_PATHS.some((path) => req.url.endsWith(path))
      ) {
        // Only bounce to /login when the protected API rejects our
        // session. Login / embed-token failures are handled locally by
        // the components themselves.
        auth.logout();
        void router.navigate(['/login']);
      }
      return throwError(() => err);
    })
  );
};