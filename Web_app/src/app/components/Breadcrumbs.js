import Link from "next/link";

export default function Breadcrumbs({ category, brand, title }) {
  return (
    <nav className="breadcrumbs">
      <Link href="/">Home</Link>

      {category && (
        <>
          <span className="sep">›</span>
          <span className="crumb">{category}</span>
        </>
      )}

      {brand && (
        <>
          <span className="sep">›</span>
          <span className="crumb">{brand}</span>
        </>
      )}

      {title && (
        <>
          <span className="sep">›</span>
          <span className="crumb current">{title}</span>
        </>
      )}
    </nav>
  );
}
