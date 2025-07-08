import CredentialsProvider from "next-auth/providers/credentials";
import { signInWithEmailAndPassword } from "firebase/auth";
import { NextAuthConfig } from "next-auth"; // Correct Type for NextAuth
import { clientAuth } from "@/lib/firebase";

const authConfig: NextAuthConfig = {
  providers: [
    CredentialsProvider({
      name: "Firebase",
      credentials: {
        email: {
          label: "Email",
          type: "email",
          placeholder: "example@example.com",
        },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          throw new Error("Email and password are required");
        }

        try {
          // Ensure credentials.email and credentials.password are strings
          const email = credentials.email as string;
          const password = credentials.password as string;

          // Firebase authentication
          const userCredential = await signInWithEmailAndPassword(
            clientAuth,
            email,
            password
          );
          const user = userCredential.user;

          // Return the user object for the session
          return {
            id: user.uid,
            name: user.displayName || "User",
            email: user.email,
          };
        } catch (error) {
          console.error("Authentication error:", error);
          throw new Error("Invalid email or password");
        }
      },
    }),
  ],
  secret: process.env.NEXTAUTH_SECRET as string,
  session: {
    strategy: "jwt",
  },
  jwt: {
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  pages: {
    signIn: "/",
  },
  callbacks: {
    async jwt({ token, user }: any) {
      if (user) {
        token.id = user.id;
        token.name = user.name;
        token.email = user.email;
      }
      return token;
    },
    async session({ session, token }: any) {
      session.user = {
        id: token.id as string,
        name: token.name as string,
        email: token.email as string,
      };
      return session;
    },
  },
  debug: true,
};

export default authConfig;
