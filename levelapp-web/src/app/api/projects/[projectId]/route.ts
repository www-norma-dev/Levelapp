import { NextRequest, NextResponse } from "next/server";
import { auth } from "../../../../../auth";
import admin from "../../../../lib/firebaseAdmin";
export const runtime = "nodejs";

export async function GET(
  _req: NextRequest,
  { params }: { params: { projectId: string } }
) {
  const session = await auth();
  if (!session?.user?.id)
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const uid = session.user.id;
  const id = decodeURIComponent(params.projectId);

  const doc = await admin
    .firestore()
    .collection("users")
    .doc(uid)
    .collection("projects")
    .doc(id)
    .get();

  if (!doc.exists)
    return NextResponse.json({ error: "Not found" }, { status: 404 });

  const data = doc.data() || {};
  const toISO = (ts: any) =>
    ts?.toDate?.() instanceof Date ? ts.toDate().toISOString() : null;

  return NextResponse.json({
    id: doc.id,
    name: data.name ?? "",
    description: data.description ?? "",
    status: data.status ?? "active",
    createdAt: toISO(data.createdAt),
    updatedAt: toISO(data.updatedAt),
  });
}
