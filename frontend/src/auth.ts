import NextAuth from "next-auth"
import Credentials from "next-auth/providers/credentials"
import { SignJWT } from "jose"

const AUTH_SECRET = new TextEncoder().encode("188043feca145f51d8e6da3c44d8ac1f73fc9ac7ceaab249953258e585d9eec8") // your secret

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

        // We'll return a user object with an id (the backend expects a UUID)
        // For simplicity, we'll generate a fake UUID from the email hash
        const id = crypto.randomUUID() // temporary – replace with real user id from DB
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