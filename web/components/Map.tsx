"use client";

import { useEffect, useRef } from "react";
import { LngLatBounds, Map as MapLibreMap, Marker, NavigationControl } from "maplibre-gl";
import { tekstit } from "@/lib/tekstit";

/**
 * MapLibre GL JS wrapper (asuntohaku-gate-SPEC.md section 7, "Map"): a free
 * vector tile source, no custom canvas map. Markers are plain DOM buttons
 * (see .map-pin in app/globals.css), not a symbol layer, so they are
 * keyboard-focusable and the search page's list-row <-> pin hover link is a
 * cheap class toggle rather than a map re-render.
 */
const STYLE_URL = "https://tiles.openfreemap.org/styles/liberty";

/** Roughly centres on mainland southern Finland when there is nothing to fit to. */
const FALLBACK_CENTER: [number, number] = [24.9, 60.3];
const FALLBACK_ZOOM = 8;

export interface MapPoint {
  id: number;
  lat: number;
  lng: number;
  /** Short pin label, e.g. "895 €" or "329 000 €". */
  label: string;
  /** Longer label for the pin's accessible name, e.g. "895 € — Kalliolan portti A 12". */
  title: string;
}

export interface MapProps {
  points: MapPoint[];
  /** Highlighted point, linked to the hovered/focused result row. */
  activeId?: number | null;
  onHoverPoint?: (id: number | null) => void;
  onSelectPoint?: (id: number) => void;
  className?: string;
}

export function Map({ points, activeId = null, onHoverPoint, onSelectPoint, className }: MapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const markersRef = useRef<Map<number, Marker>>(new globalThis.Map());

  // Callbacks are read through refs so the map-creation effect below doesn't
  // need to depend on (and therefore recreate the map for) new closures.
  const onHoverRef = useRef(onHoverPoint);
  const onSelectRef = useRef(onSelectPoint);
  useEffect(() => {
    onHoverRef.current = onHoverPoint;
    onSelectRef.current = onSelectPoint;
  }, [onHoverPoint, onSelectPoint]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const map = new MapLibreMap({
      container: containerRef.current,
      style: STYLE_URL,
      center: FALLBACK_CENTER,
      zoom: FALLBACK_ZOOM,
      cooperativeGestures: true,
      attributionControl: { compact: true },
    });
    if (reducedMotion) {
      // matches the site-wide prefers-reduced-motion rule in globals.css
      map.scrollZoom.disable();
    }
    map.addControl(new NavigationControl({ showCompass: false }), "top-right");
    // Style/tile fetch failures otherwise fail silently: no error surfaces,
    // "load" never fires, and the map just sits blank with nothing in the
    // console to explain why.
    map.on("error", (e) => {
      console.error("[Map] maplibre error:", e.error?.message ?? e);
    });
    // The container isn't always at its final size the instant this effect
    // runs (it can still be widening/settling from surrounding layout), and a
    // map created against a stale size can end up not painting until told to
    // re-measure. A ResizeObserver keeps it in sync for the container's whole
    // lifetime, not just once at mount.
    const resizeObserver = new ResizeObserver(() => map.resize());
    resizeObserver.observe(containerRef.current);
    mapRef.current = map;
    return () => {
      resizeObserver.disconnect();
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Keep markers in sync with `points`.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    function render() {
      const markers = markersRef.current;
      const seen = new Set<number>();
      for (const point of points) {
        seen.add(point.id);
        let marker = markers.get(point.id);
        if (!marker) {
          const el = document.createElement("button");
          el.type = "button";
          el.className = "map-pin";
          el.addEventListener("mouseenter", () => onHoverRef.current?.(point.id));
          el.addEventListener("mouseleave", () => onHoverRef.current?.(null));
          el.addEventListener("focus", () => onHoverRef.current?.(point.id));
          el.addEventListener("blur", () => onHoverRef.current?.(null));
          el.addEventListener("click", () => onSelectRef.current?.(point.id));
          marker = new Marker({ element: el, anchor: "bottom" }).setLngLat([
            point.lng,
            point.lat,
          ]);
          marker.addTo(map!);
          markers.set(point.id, marker);
        }
        const el = marker.getElement();
        el.textContent = point.label;
        el.setAttribute("aria-label", point.title);
        marker.setLngLat([point.lng, point.lat]);
      }
      for (const [id, marker] of markers) {
        if (!seen.has(id)) {
          marker.remove();
          markers.delete(id);
        }
      }

      if (points.length > 0) {
        const bounds = points.reduce(
          (b, p) => b.extend([p.lng, p.lat]),
          new LngLatBounds([points[0].lng, points[0].lat], [points[0].lng, points[0].lat]),
        );
        map!.fitBounds(bounds, { padding: 48, maxZoom: 15, duration: 0 });
      }
    }

    if (map.isStyleLoaded()) {
      render();
      return;
    }
    map.once("load", render);
    // Markers are positioned from the map's center/zoom transform, not from
    // the basemap tiles themselves — they don't need to wait on "load" at
    // all. A slow or stuck style/tile fetch shouldn't leave the pins missing
    // too, so place them on a short timer regardless; render() is safe to
    // call twice (it keys everything off point id).
    const fallback = window.setTimeout(render, 1200);
    return () => window.clearTimeout(fallback);
  }, [points]);

  // Reflect the hovered/focused result row on the matching pin.
  useEffect(() => {
    for (const [id, marker] of markersRef.current) {
      marker.getElement().setAttribute("data-active", String(id === activeId));
    }
  }, [activeId]);

  return (
    <div
      ref={containerRef}
      role="region"
      aria-label={tekstit.kartta}
      className={className}
    />
  );
}
