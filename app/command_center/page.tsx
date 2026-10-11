import CommandCenter from "../../CommandCenter";

export const dynamic = "force-dynamic";

/**
 * The real-data Command Center. The Dashi shell is the new main screen at `/`;
 * this route keeps the existing surface reachable and its code alive while the
 * new shell grows (M-D5..M-D8). Nothing is deleted and no evidence is lost.
 */
export default function CommandCenterPage() {
  return <CommandCenter />;
}
