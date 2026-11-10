export const DISCLAIMER = "Not for gambling or betting. CFB Matchups is a personal statistics project.";

export default function Disclaimer() {
  return (
    <footer className="disclaimer">
      <div className="wrap">
        <strong>{DISCLAIMER}</strong> Data from CollegeFootballData.com.
      </div>
    </footer>
  );
}
