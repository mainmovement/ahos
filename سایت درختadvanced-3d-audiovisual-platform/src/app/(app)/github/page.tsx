import { PageHeader } from "@/components/page-header";
import { GithubDesk } from "@/components/github-desk";
import { loadGithub } from "@/lib/queries";

export const dynamic = "force-dynamic";

export default async function GithubPage() {
  const items = await loadGithub();
  return (
    <div>
      <PageHeader
        kicker="GitHub hub"
        title="The source of truth is not a vibe."
        lede="Code, docs, issues, PRs, experiments, releases. Learn → compare → adapt → improve. License-respecting. No silent changes."
      />
      <div className="panel mb-6 rounded-3xl p-6 font-mono text-xs leading-7 text-[#efe6d6]/70">
        <p>ahos/</p>
        <p>├── docs/VISION.md</p>
        <p>├── src/app · dashboard chambers</p>
        <p>├── src/db · drizzle schema</p>
        <p>├── src/lib · bootstrap, queries, seed</p>
        <p>└── public/images · cinematic stills</p>
      </div>
      <GithubDesk items={items} />
    </div>
  );
}
