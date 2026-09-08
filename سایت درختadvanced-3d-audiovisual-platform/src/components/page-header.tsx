export function PageHeader({
  kicker,
  title,
  lede,
}: {
  kicker: string;
  title: string;
  lede: string;
}) {
  return (
    <header className="mb-8 max-w-3xl">
      <p className="kicker">{kicker}</p>
      <h1 className="font-display mt-3 text-4xl italic leading-none text-[#fff6e4] md:text-5xl">{title}</h1>
      <p className="mt-4 text-[#efe6d6]/70">{lede}</p>
    </header>
  );
}
