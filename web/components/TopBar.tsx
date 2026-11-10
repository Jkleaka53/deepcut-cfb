import Link from "next/link";
import { Search } from "lucide-react";
import Logo from "./Logo";
import ThemeToggle from "./ThemeToggle";

export default function TopBar() {
  return (
    <header className="topbar">
      <div className="wrap">
        <Logo />
        <div className="actions">
          <Link href="/#search" className="iconbtn" aria-label="Search games">
            <Search className="icon" aria-hidden />
          </Link>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
