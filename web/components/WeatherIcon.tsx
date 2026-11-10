import { Cloud, CloudDrizzle, CloudFog, CloudLightning, CloudRain, CloudSun, Snowflake, Sun, Warehouse } from "lucide-react";
import type { WeatherIcon as Kind } from "@/lib/types";

const MAP = { clear: Sun, "partly-cloudy": CloudSun, cloudy: Cloud, fog: CloudFog, drizzle: CloudDrizzle, rain: CloudRain,
  snow: Snowflake, storm: CloudLightning } as const;

export default function WeatherIcon({ kind, indoors = false, className = "icon sm" }: { kind?: Kind | null; indoors?: boolean; className?: string }) {
  const I = indoors ? Warehouse : kind ? MAP[kind] ?? Cloud : null;
  return I ? <I className={className} aria-hidden /> : null;
}
