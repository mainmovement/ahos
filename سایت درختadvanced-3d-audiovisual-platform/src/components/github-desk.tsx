"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { SoundButton } from "@/components/sound-button";
import type { GithubItem } from "@/db/schema";

export function GithubDesk({ items }: { items: GithubItem[] }) {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [kind, setKind] = useState("issue");

  return (
    <div>
      <form
        className="panel mb-6 grid gap-3 rounded-3xl p-5 md:grid-cols-[1fr_1fr_auto]"
        onSubmit={async (e) => {
          e.preventDefault();
          await fetch("/api/github", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title, body, kind }),
          });
          setTitle("");
          setBody("");
          router.refresh();
        }}
      >
        <input className="input" placeholder="Issue / PR / doc title" value={title} onChange={(e) => setTitle(e.target.value)} required />
        <input className="input" placeholder="What / why / how" value={body} onChange={(e) => setBody(e.target.value)} required />
        <div className="flex gap-2">
          <select className="input" value={kind} onChange={(e) => setKind(e.target.value)}>
            <option value="issue">issue</option>
            <option value="pr">pr</option>
            <option value="doc">doc</option>
            <option value="commit">commit</option>
          </select>
          <SoundButton tone="gold" type="submit">File</SoundButton>
        </div>
      </form>
      <div className="space-y-3">
        {items.map((i) => (
          <article key={i.id} className="panel rounded-2xl p-5">
            <div className="flex items-center justify-between gap-3">
              <span className="badge">{i.kind}</span>
              <span className="badge">{i.status}</span>
            </div>
            <h3 className="mt-3 font-display text-2xl italic">{i.title}</h3>
            <p className="mt-1 text-sm text-[#efe6d6]/65">{i.body}</p>
          </article>
        ))}
      </div>
    </div>
  );
}
