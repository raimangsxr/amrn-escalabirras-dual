import { Injectable, NgZone, OnDestroy } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export type LayoutBucket = 'layout-compact' | 'layout-narrow' | 'layout-wide';

const CLASSES: readonly LayoutBucket[] = ['layout-compact', 'layout-narrow', 'layout-wide'];

/**
 * Observes the iframe (or window) size and exposes the current
 * "layout bucket" both as a CSS class on `<html>` and as an
 * observable. Components can subscribe to the observable or rely
 * on the class for plain-CSS rules.
 *
 *   < 480 px  -> layout-compact
 *   < 768 px  -> layout-narrow
 *   >= 768 px -> layout-wide
 */
@Injectable({ providedIn: 'root' })
export class LayoutService implements OnDestroy {
  private readonly subject = new BehaviorSubject<LayoutBucket>(this.computeInitial());
  readonly layoutClass$: Observable<LayoutBucket> = this.subject.asObservable();

  private observer: ResizeObserver | null = null;

  constructor(private zone: NgZone) {
    this.apply(this.subject.value);
    this.start();
  }

  ngOnDestroy(): void {
    this.stop();
  }

  start(): void {
    if (this.observer !== null || typeof ResizeObserver === 'undefined') {
      return;
    }
    this.zone.runOutsideAngular(() => {
      this.observer = new ResizeObserver((entries) => {
        for (const entry of entries) {
          const width = entry.contentRect.width;
          const next = this.bucketFor(width);
          if (next !== this.subject.value) {
            this.zone.run(() => {
              this.subject.next(next);
              this.apply(next);
            });
          }
        }
      });
      this.observer.observe(document.body);
    });
  }

  stop(): void {
    this.observer?.disconnect();
    this.observer = null;
  }

  private bucketFor(width: number): LayoutBucket {
    if (width < 480) {
      return 'layout-compact';
    }
    if (width < 768) {
      return 'layout-narrow';
    }
    return 'layout-wide';
  }

  private computeInitial(): LayoutBucket {
    if (typeof document === 'undefined') {
      return 'layout-wide';
    }
    const width = document.body.clientWidth || window.innerWidth || 1024;
    return this.bucketFor(width);
  }

  private apply(bucket: LayoutBucket): void {
    if (typeof document === 'undefined') {
      return;
    }
    const root = document.documentElement;
    for (const cls of CLASSES) {
      if (cls === bucket) {
        root.classList.add(cls);
      } else {
        root.classList.remove(cls);
      }
    }
    root.dataset['layout'] = bucket;
  }
}