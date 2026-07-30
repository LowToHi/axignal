import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "AXIGNAL — Public Procurement Intelligence",
    short_name: "AXIGNAL",
    description: "Evidence-governed intelligence for organisations that sell to government.",
    start_url: "/",
    display: "standalone",
    background_color: "#030d12",
    theme_color: "#030d12",
    icons: [
      { src: "/brand/axignal-isotipo.svg", sizes: "any", type: "image/svg+xml" }
    ]
  };
}
