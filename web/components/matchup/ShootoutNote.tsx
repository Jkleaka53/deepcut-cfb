/** On the game page of the week's Shootout of the Week: why the site picked it. */
export default function ShootoutNote({ why }: { why: string }) {
  return (
    <div className="card shootout-note">
      <span className="pick-tag">Shootout of the Week</span>
      <p>{why}</p>
    </div>
  );
}
