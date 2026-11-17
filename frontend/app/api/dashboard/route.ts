
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const backendUrl = process.env.BACKEND_API_URL;

  if (!backendUrl) {
    return NextResponse.json(
      { detail: "BACKEND_API_URL is not configured" },
      { status: 500 }
    );
  }

  try {
    const baseUrl = backendUrl.replace(/\/+$/, "");

    const response = await fetch(
      `${baseUrl}/api/dashboard`,
      {
        method: "GET",
        headers: {
          Accept: "application/json"
        },
        cache: "no-store"
      }
    );

    const body = await response.text();

    return new Response(body, {
      status: response.status,
      headers: {
        "Content-Type":
          response.headers.get("content-type") ||
          "application/json",
        "Cache-Control": "no-store"
      }
    });

  } catch (error) {
    const message =
      error instanceof Error
        ? error.message
        : "Unknown backend connection error";

    return NextResponse.json(
      {
        detail: "Backend connection failed",
        error: message
      },
      { status: 502 }
    );
  }
}
