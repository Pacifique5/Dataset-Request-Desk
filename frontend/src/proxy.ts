import { NextResponse, type NextRequest } from "next/server";

/**
 * Optimistic routing only: send visitors without a session cookie to /login.
 * The API still validates the token (and the role) on every request.
 */
export function proxy(request: NextRequest) {
  const hasSession = request.cookies.has("access_token");
  const isLogin = request.nextUrl.pathname === "/login";

  if (!hasSession && !isLogin) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  if (hasSession && isLogin) {
    return NextResponse.redirect(new URL("/requests", request.url));
  }
  return NextResponse.next();
}

export const config = {
  // Skip the API proxy, Next internals and static files.
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
