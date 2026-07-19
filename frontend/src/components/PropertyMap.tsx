"use client";

import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import type { Property } from "@/lib/api";

// Leaflet's default marker icons reference image paths that don't survive a webpack/Next.js
// bundle -- point them at the CDN copies that ship with the same leaflet version instead.
const markerIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

export default function PropertyMap({ properties }: { properties: Property[] }) {
  const located = properties.filter(
    (p): p is Property & { latitude: number; longitude: number } => p.latitude != null && p.longitude != null,
  );

  if (located.length === 0) {
    return (
      <p className="text-[12.5px] text-ink/50 py-6 text-center">
        No properties with map coordinates match this filter.
      </p>
    );
  }

  const center: [number, number] = [
    located.reduce((sum, p) => sum + p.latitude, 0) / located.length,
    located.reduce((sum, p) => sum + p.longitude, 0) / located.length,
  ];

  return (
    <MapContainer
      key={located.length === 1 ? `${located[0].latitude},${located[0].longitude}` : "all"}
      center={center}
      zoom={located.length === 1 ? 15 : 11}
      scrollWheelZoom={false}
      style={{ height: 360, width: "100%" }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {located.map((p, i) => (
        <Marker key={`${p.project}-${p.address}-${i}`} position={[p.latitude, p.longitude]} icon={markerIcon}>
          <Popup>
            <strong>{p.project}</strong>
            <br />
            {p.address}, {p.town}
            {p.n_units != null && (
              <>
                <br />
                {p.n_units} total units
              </>
            )}
            <br />
            <a
              href={`https://www.google.com/maps/search/?api=1&query=${p.latitude},${p.longitude}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              Open in Google Maps
            </a>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
