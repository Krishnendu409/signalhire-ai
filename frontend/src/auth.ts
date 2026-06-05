import NextAuth from "next-auth"
import Credentials from "next-auth/providers/credentials"
import { SignJWT } from "jose"
import { createHash } from "crypto"

const authSecretValue = process.env.AUTH_SECRET || process.env.NEXTAUTH_SECRET
const AUTH_SECRET = new TextEncoder().encode(authSecretValue || "development-only-secret-change-me")

function stableUserId(email: string): string {
  const hash = createHash("sha256").update(email.trim().toLowerCase()).digest("hex")
  const variantNibble = ((parseInt(hash[16], 16) & 0x3) | 0x8).toString(16)
  // Build an RFC4122-style deterministic UUID (v5-formatted, SHA-256-derived).
  return `${hash.slice(0, 8)}-${hash.slice(8, 12)}-5${hash.slice(12, 15)}-${variantNibble}${hash.slice(17, 20)}-${hash.slice(20, 32)}`
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Credentials({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        // For demo: accept any email/password and auto‑create a user in backend
        // In production, verify against your database or backend endpoint
        const email = typeof credentials?.email === "string" ? credentials.email : null
        if (!email) return null

        const id = stableUserId(email)
        return { id, email, name: email }
      },
    }),
  ],
  session: { strategy: "jwt" },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        // Store the user id in the token so we can create a custom JWT for the backend
        token.sub = user.id
      }
      return token
    },
    async session({ session, token }) {
      // Create a backend‑compatible JWT to attach to API requests
      const backendToken = await new SignJWT({ sub: token.sub })
        .setProtectedHeader({ alg: "HS256" })
        .setIssuedAt()
        .setExpirationTime("1h")
        .sign(AUTH_SECRET)

      session.backendToken = backendToken
      return session
    },
  },
})