/** On a featured game's page (Shootout of the Week, Upset Watch): why the site picked it. */
export default function PickNote({ tag, heading, why }: { tag: string; heading?: string; why: string }) {
  return (
    <div className="card shootout-note">
      <span className="pick-tag">{tag}</span>
      {heading && <h4 className="pick-note-head">{heading}</h4>}
      <p>{why}</p>
    </div>
  );
}
