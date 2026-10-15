import type { Metadata } from "next";
import { getCrypto } from "@/lib/api/crypto";
import { CryptoView } from "@/components/views/crypto-view";

export const metadata: Metadata = { title: "بازار رمزارز · Crypto Market" };

export default async function CryptoPage() {
  return <CryptoView crypto={await getCrypto()} />;
}
