import type { MetadataRoute } from "next";

export const dynamic = "force-static";

// Lets Android "Add to Home screen" use the DeepCut icon and name.
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "DeepCut CFB",
    short_name: "DeepCut",
    start_url: "/",
    display: "browser",
    background_color: "#1f6feb",
    theme_color: "#1f6feb",
    icons: [
      { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
  };
}
