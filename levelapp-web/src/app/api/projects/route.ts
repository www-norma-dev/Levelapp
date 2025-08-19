import { NextRequest, NextResponse } from "next/server";
import { auth } from "../../../../auth";
import admin from "../../../lib/firebaseAdmin";

export async function GET(req: NextRequest) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
    const uid = session.user.id;

    const { searchParams } = new URL(req.url);
    const limitParam = Number(searchParams.get("limit") ?? 20);
    const limit = Math.max(
      1,
      Math.min(50, isNaN(limitParam) ? 20 : limitParam)
    );
    const cursor = searchParams.get("cursor") ?? undefined; // doc id for pagination
    const status = searchParams.get("status") ?? undefined; // optional filter

    const colRef = admin
      .firestore()
      .collection("users")
      .doc(uid)
      .collection("projects");

    let q: FirebaseFirestore.Query<FirebaseFirestore.DocumentData> =
      colRef.orderBy("createdAt", "desc");

    if (status) {
      // NOTE: This + orderBy may require a Firestore composite index.
      // If Firestore asks for an index link in logs, create it once.
      q = q.where("status", "==", status);
    }

    if (cursor) {
      const cursorSnap = await colRef.doc(cursor).get();
      if (!cursorSnap.exists) {
        return NextResponse.json({ error: "Invalid cursor" }, { status: 400 });
      }
      q = q.startAfter(cursorSnap);
    }

    const snap = await q.limit(limit).get();

    const items = snap.docs.map((d) => {
      const data = d.data() as any;
      const toISO = (ts: any) =>
        ts?.toDate?.() instanceof Date ? ts.toDate().toISOString() : null;

      return {
        id: d.id,
        name: data.name ?? "",
        description: data.description ?? "",
        status: data.status ?? "active",
        createdBy: data.createdBy ?? uid,
        createdAt: toISO(data.createdAt),
        updatedAt: toISO(data.updatedAt),
      };
    });

    const nextCursor =
      snap.size === limit ? snap.docs[snap.docs.length - 1].id : null;

    return NextResponse.json(
      { items, nextCursor, count: items.length },
      { status: 200 }
    );
  } catch (err) {
    console.error("GET /api/projects failed:", err);
    return NextResponse.json(
      { error: "Internal Server Error" },
      { status: 500 }
    );
  }
}

export async function POST(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const uid = session.user.id;
  const body = await req.json();
  const { name, description = "" } = body;

  if (!name) {
    return NextResponse.json({ error: "name is required" }, { status: 400 });
  }

  const now = admin.firestore.FieldValue.serverTimestamp();
  const ref = await admin
    .firestore()
    .collection("users")
    .doc(uid)
    .collection("projects")
    .add({
      name,
      description,
      status: "active",
      createdBy: uid,
      createdAt: now,
      updatedAt: now,
    });

  const doc = await ref.get();
  return NextResponse.json({ id: ref.id, ...doc.data() }, { status: 201 });
}
