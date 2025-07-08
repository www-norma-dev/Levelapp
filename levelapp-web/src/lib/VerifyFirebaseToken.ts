import admin, { auth } from "./firebaseAdmin";

export async function verifyFirebaseToken(
  idToken: string
): Promise<admin.auth.DecodedIdToken | null> {
  try {
    const decodedToken = await auth.verifyIdToken(idToken);
    return decodedToken;
  } catch (error) {
    console.error("Failed to verify Firebase token:", error);
    return null;
  }
}
