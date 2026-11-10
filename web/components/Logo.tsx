import Link from "next/link";

export default function Logo() {
  return (
    <Link href="/" className="logo" aria-label="DeepCut CFB home">
      <span className="word" aria-hidden="true">
        <span className="t1">DeepCut</span>
        <span className="t2">DeepCut</span>
      </span>
      <span className="tag" aria-hidden="true">CFB</span>
    </Link>
  );
}
