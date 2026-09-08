import { SoundButton } from "@/components/sound-button";

export default function NotFound() {
  return (
    <div className="grid min-h-screen place-items-center bg-[#05070b] px-6">
      <div className="panel max-w-lg rounded-3xl p-8 text-center">
        <p className="kicker">Unknown</p>
        <h1 className="font-display mt-3 text-4xl italic">This chamber does not exist.</h1>
        <p className="mt-3 text-[#efe6d6]/70">INSUFFICIENT EVIDENCE that this route was planted.</p>
        <SoundButton href="/dashboard" tone="gold" className="mt-6">
          Return to command
        </SoundButton>
      </div>
    </div>
  );
}
