// Protecting routes with next-auth
// https://next-auth.js.org/configuration/nextjs#middleware
// https://nextjs.org/docs/app/building-your-application/routing/middleware

import NextAuth from "next-auth";
import authConfig from "../auth.config";

const { auth } = NextAuth(authConfig);

export default auth((req) => {
  // Not authenticated
  if (!req.auth) {
    const redirectUrl = req.nextUrl.clone();
    redirectUrl.pathname = "/";
    redirectUrl.searchParams.set("redirect", req.nextUrl.pathname + req.nextUrl.search);
    
    return Response.redirect(redirectUrl);
  }
});

export const config = { matcher: ["/dashboard/:path*"] };
