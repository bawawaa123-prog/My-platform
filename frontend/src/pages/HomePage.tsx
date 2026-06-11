export default function HomePage() {
  return (
    <section className="content-grid">
      <article className="panel panel--feature">
        <p className="panel-tag">Workspace</p>
        <h3>Authenticated dashboard shell is live</h3>
        <p>
          The app now routes authenticated users into the back-office layout with durable
          token storage and protected navigation.
        </p>
      </article>
      <article className="panel">
        <h3>Navigation</h3>
        <p>
          Use the sidebar to move between Dashboard, Tickets, and Knowledge. The business
          content for those areas is staged for the upcoming steps.
        </p>
      </article>
    </section>
  );
}
