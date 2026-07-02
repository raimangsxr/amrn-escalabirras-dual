import { Injectable, NgZone, OnDestroy } from "@angular/core";
import { BehaviorSubject, Observable } from "rxjs";

export type WidthBucket = "compact" | "narrow" | "wide";
export type HeightBucket = "short" | "medium" | "tall";

export type LayoutBucket =
  | "layout-compact-short"
  | "layout-compact-medium"
  | "layout-compact-tall"
  | "layout-narrow-short"
  | "layout-narrow-medium"
  | "layout-narrow-tall"
  | "layout-wide-short"
  | "layout-wide-medium"
  | "layout-wide-tall";

export const LAYOUT_CLASSES: readonly LayoutBucket[] = [
  "layout-compact-short",
  "layout-compact-medium",
  "layout-compact-tall",
  "layout-narrow-short",
  "layout-narrow-medium",
  "layout-narrow-tall",
  "layout-wide-short",
  "layout-wide-medium",
  "layout-wide-tall",
];

const WIDTH_COMPACT_MAX = 480;
const WIDTH_NARROW_MAX = 768;
const HEIGHT_SHORT_MAX = 384;
const HEIGHT_MEDIUM_MAX = 576;

const FALLBACK_WIDTH = 1024;
const FALLBACK_HEIGHT = 768;

export function widthBucketFor(width: number): WidthBucket {
  if (width < WIDTH_COMPACT_MAX) {
    return "compact";
  }
  if (width < WIDTH_NARROW_MAX) {
    return "narrow";
  }
  return "wide";
}

export function heightBucketFor(height: number): HeightBucket {
  if (height < HEIGHT_SHORT_MAX) {
    return "short";
  }
  if (height < HEIGHT_MEDIUM_MAX) {
    return "medium";
  }
  return "tall";
}

export function combinedBucketFor(width: number, height: number): LayoutBucket {
  return `layout-${widthBucketFor(width)}-${heightBucketFor(
    height,
  )}` as LayoutBucket;
}

/**
 * Observes the iframe (or window) size and exposes the current
 * "layout bucket" both as a CSS class on `<html>` and as an
 * observable. The bucket combines the iframe's width bucket and
 * height bucket into a single class so callers can react to
 * either axis.
 *
 *   width  < 480        -> compact
 *   width  < 768        -> narrow
 *   width  >= 768       -> wide
 *   height < 384        -> short
 *   height < 576        -> medium
 *   height >= 576       -> tall
 *
 * Combined bucket names follow the pattern `layout-{width}-{height}`.
 */
@Injectable({ providedIn: "root" })
export class LayoutService implements OnDestroy {
  private readonly subject = new BehaviorSubject<LayoutBucket>(
    this.computeInitial(),
  );
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
    if (this.observer !== null || typeof ResizeObserver === "undefined") {
      return;
    }
    this.zone.runOutsideAngular(() => {
      this.observer = new ResizeObserver((entries) => {
        for (const entry of entries) {
          const width = entry.contentRect.width;
          const height = entry.contentRect.height;
          const next = combinedBucketFor(width, height);
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

  private computeInitial(): LayoutBucket {
    if (typeof document === "undefined") {
      return "layout-wide-tall";
    }
    const width =
      document.body.clientWidth || window.innerWidth || FALLBACK_WIDTH;
    const height =
      document.body.clientHeight || window.innerHeight || FALLBACK_HEIGHT;
    return combinedBucketFor(width, height);
  }

  private apply(bucket: LayoutBucket): void {
    if (typeof document === "undefined") {
      return;
    }
    const root = document.documentElement;
    for (const cls of LAYOUT_CLASSES) {
      if (cls === bucket) {
        root.classList.add(cls);
      } else {
        root.classList.remove(cls);
      }
    }
    root.dataset["layout"] = bucket;
  }
}
