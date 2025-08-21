import { NextRequest, NextResponse } from "next/server";
import { auth } from "../../../../../../auth";
import admin from "../../../../../lib/firebaseAdmin";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(
  req: NextRequest,
  { params }: { params: { projectId: string } }
) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const uid = session.user.id;
  const projectId = decodeURIComponent(params.projectId);
  const { searchParams } = new URL(req.url);

  const limit = Math.max(
    1,
    Math.min(50, Number(searchParams.get("limit") || 10))
  );
  const cursor = searchParams.get("cursor") || undefined;
  const includeFull =
    (searchParams.get("full") || "false").toLowerCase() === "true";

  const col = admin
    .firestore()
    .collection("users")
    .doc(uid)
    .collection("projects")
    .doc(projectId)
    .collection("batchTestMultiAgent");

  let q: FirebaseFirestore.Query = col.orderBy("updatedAt", "desc");
  if (cursor) {
    const cursorSnap = await col.doc(cursor).get();
    if (!cursorSnap.exists) {
      return NextResponse.json({ error: "Invalid cursor" }, { status: 400 });
    }
    q = q.startAfter(cursorSnap);
  }

  const snap = await q.limit(limit).get();

  const items = snap.docs.map((d) => {
    const raw = d.data() as any;

    const updatedAt =
      raw?.updatedAt?.toDate?.() instanceof Date
        ? raw.updatedAt.toDate().toISOString()
        : null;

    const scenarios: any[] = Array.isArray(raw?.scenarios) ? raw.scenarios : [];
    const scenariosCount = scenarios.length;
    const attemptsCount = scenarios.reduce(
      (acc, s) => acc + (Array.isArray(s?.attempts) ? s.attempts.length : 0),
      0
    );

    const firstAttempt = scenarios?.[0]?.attempts?.[0];
    const firstInteraction = firstAttempt?.interactions?.[0] ?? {};
    const sample = {
      user_message: firstInteraction?.user_message ?? null,
      agent_reply: firstInteraction?.agent_reply ?? null,
      reference_reply: firstInteraction?.reference_reply ?? null,
      openai: firstInteraction?.evaluation_results?.openai ?? null,
      ionos: firstInteraction?.evaluation_results?.ionos ?? null,
      execution_time: firstAttempt?.execution_time ?? null,
    };

    return {
      id: d.id,
      updatedAt,
      test_name: raw?.test_name ?? null,
      modelId: raw?.modelId ?? raw?.model_id ?? null,
      attempts: raw?.attempts ?? null,
      scenariosCount,
      attemptsCount,
      sample,
      ...(includeFull ? { scenarios } : {}),
    };
  });

  const nextCursor =
    snap.size === limit ? snap.docs[snap.docs.length - 1].id : null;

  return NextResponse.json(
    { items, nextCursor, count: items.length },
    { status: 200 }
  );
}
