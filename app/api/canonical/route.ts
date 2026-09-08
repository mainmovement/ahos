import { authorizeWebApi, sanitizePublicError } from "@/web_api_auth";
import { loadCanonicalReadModel } from "@/canonical_read_model";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  const denied = authorizeWebApi(req);
  if (denied) return denied;
  try {
    const model = await loadCanonicalReadModel();
    return Response.json({
      ok: true,
      source: "python_canonical_decision_authority",
      advisoryOnly: false,
      presentation: true,
      ...model,
    });
  } catch (error) {
    return Response.json(
      {
        ok: false,
        status: "UNAVAILABLE",
        error: sanitizePublicError(error),
        decisions: [],
        no_invented_evidence: true,
      },
      { status: 200 },
    );
  }
}
