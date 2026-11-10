"use client";
import { ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";

// Back to wherever you came from; home if the page was opened directly. Home restores its week and tab itself.
export default function BackButton() {
  const router = useRouter();
  return (
    <button className="backbtn" aria-label="Back"
      onClick={() => (window.history.length > 1 ? router.back() : router.push("/"))}>
      <ArrowLeft className="icon" aria-hidden /><span>Games</span>
    </button>
  );
}
