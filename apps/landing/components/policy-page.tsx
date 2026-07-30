import Image from "next/image";

type PolicyPageProps = {
  eyebrow: string;
  title: string;
  updated: string;
  children: React.ReactNode;
};

export function PolicyPage({ eyebrow, title, updated, children }: PolicyPageProps) {
  return (
    <main className="policy-page">
      <header>
        <a className="brand-lockup" href="/" aria-label="AXIGNAL home">
          <Image src="/brand/axignal-logo-dark.svg" alt="AXIGNAL" width={1895} height={406} />
        </a>
        <a href="/">Back to AXIGNAL</a>
      </header>
      <article>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p className="policy-updated">Operational publication · updated {updated}</p>
        {children}
      </article>
    </main>
  );
}
