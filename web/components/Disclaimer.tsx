export const DISCLAIMER = "Not for gambling or betting. DeepCut CFB is a personal statistics project.";
export const AFFILIATION = "Not affiliated with any team, conference or the NCAA.";

export default function Disclaimer() {
  return (
    <footer className="disclaimer">
      <div className="wrap">
        <strong>{DISCLAIMER}</strong> {AFFILIATION}
        <br />
        Data: CollegeFootballData.com · Weather: Open-Meteo
      </div>
    </footer>
  );
}
