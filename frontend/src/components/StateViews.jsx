// The three states the assignment requires in every view: loading, empty, error.
// Kept tiny and reusable so each page just drops them in.

export function Loading({ label = "Loading..." }) {
  return (
    <div className="state">
      <span className="spinner" />
      <span>{label}</span>
    </div>
  );
}

export function EmptyState({ label = "Nothing to show yet." }) {
  return <div className="state state--empty">{label}</div>;
}

export function ErrorView({ label = "Something went wrong. Please try again." }) {
  return <div className="state state--error">{label}</div>;
}
