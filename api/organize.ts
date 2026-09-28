declare const process: { env: Record<string, string | undefined> };

type RequestLike = {
  method?: string;
  body?: unknown;
  headers: Record<string, string | string[] | undefined>;
};

type ResponseLike = {
  setHeader(name: string, value: string): void;
  status(code: number): ResponseLike;
  json(body: unknown): void;
};

const SYSTEM_PROMPT = `Extract actionable tasks and events from the user's note.
Use the supplied reference time to resolve relative dates. Never invent details.
Return events for notable occurrences such as exams, appointments, or presentations.
Return tasks only for actions the user needs to do. Preparation tasks may reference an event.
Use null for unknown dates and details. A date without a time is an all-day item at midnight.
A date with a time is timed. Task priority is low, normal, or high.
Do not include IDs; the app assigns IDs locally.

Reference time: `;

const ORGANIZE_SCHEMA = {
  type: "object",
  additionalProperties: false,
  required: ["tasks", "message", "events"],
  properties: {
    tasks: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        required: [
          "title", "description", "scheduledStart", "isAllDay", "deadline",
          "durationMinutes", "priority", "parentRef", "eventRef",
        ],
        properties: {
          title: { type: "string" },
          description: { type: "string" },
          scheduledStart: { anyOf: [{ type: "string" }, { type: "null" }] },
          isAllDay: { type: "boolean" },
          deadline: { anyOf: [{ type: "string" }, { type: "null" }] },
          durationMinutes: { anyOf: [{ type: "integer", minimum: 1 }, { type: "null" }] },
          priority: { type: "string", enum: ["low", "normal", "high"] },
          parentRef: { anyOf: [{ type: "string" }, { type: "null" }] },
          eventRef: { anyOf: [{ type: "string" }, { type: "null" }] },
        },
      },
    },
    message: { anyOf: [{ type: "string" }, { type: "null" }] },
    events: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        required: ["title", "description", "scheduledStart", "isAllDay"],
        properties: {
          title: { type: "string" },
          description: { type: "string" },
          scheduledStart: { anyOf: [{ type: "string" }, { type: "null" }] },
          isAllDay: { type: "boolean" },
        },
      },
    },
  },
};

function getStringEnv(name: string): string {
  return (process.env[name] || "").trim();
}

function positiveLimit(name: string, fallback: number): number {
  const value = Number.parseInt(process.env[name] || "", 10);
  return Number.isFinite(value) && value > 0 ? value : fallback;
}

function redisRestUrl(): string {
  return getStringEnv("UPSTASH_REDIS_REST_URL") || getStringEnv("KV_REST_API_URL");
}

function redisRestToken(): string {
  return getStringEnv("UPSTASH_REDIS_REST_TOKEN") || getStringEnv("KV_REST_API_TOKEN");
}

async function redisCommand(command: string, ...args: string[]): Promise<number> {
  const redisUrl = redisRestUrl().replace(/\/+$/, "");
  const redisToken = redisRestToken();
  if (!redisUrl || !redisToken) throw new Error("Rate limit storage is not configured");

  const path = [command, ...args].map(encodeURIComponent).join("/");
  const response = await fetch(`${redisUrl}/${path}`, {
    headers: { Authorization: `Bearer ${redisToken}` },
    cache: "no-store",
  });
  if (!response.ok) throw new Error("Rate limit storage request failed");
  const result = await response.json() as { result?: number; error?: string };
  if (result.error || typeof result.result !== "number") {
    throw new Error("Rate limit storage returned an invalid response");
  }
  return result.result;
}

async function incrementDaily(key: string): Promise<number> {
  const count = await redisCommand("INCR", key);
  if (count === 1) await redisCommand("EXPIRE", key, "172800");
  return count;
}

function getClientIp(request: RequestLike): string | null {
  const raw = request.headers["x-forwarded-for"];
  const forwarded = Array.isArray(raw) ? raw[0] : raw;
  if (!forwarded) return null;
  // Vercel appends the connecting client address to this proxy header.
  const addresses = forwarded.split(",").map((value) => value.trim()).filter(Boolean);
  return addresses.length ? addresses[addresses.length - 1] : null;
}

async function hashClientIp(ip: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(ip));
  return Array.from(new Uint8Array(digest))
    .map((value) => value.toString(16).padStart(2, "0"))
    .join("")
    .slice(0, 24);
}

function sendError(response: ResponseLike, status: number, error: string): void {
  response.status(status).json({ error });
}

export default async function handler(request: RequestLike, response: ResponseLike): Promise<void> {
  response.setHeader("Cache-Control", "no-store");
  if (request.method !== "POST") {
    response.setHeader("Allow", "POST");
    sendError(response, 405, "Use POST to organize a note.");
    return;
  }

  const groqKey = getStringEnv("GROQ_API_KEY");
  if (!groqKey) {
    sendError(response, 503, "The demo organizer needs GROQ_API_KEY in its Vercel environment.");
    return;
  }
  if (!redisRestUrl() || !redisRestToken()) {
    sendError(response, 503, "The demo organizer needs its Redis usage-limit connection configured.");
    return;
  }

  const body = request.body as { text?: unknown } | undefined;
  const text = typeof body?.text === "string" ? body.text.trim() : "";
  const maxCharacters = positiveLimit("DEMO_MAX_INPUT_CHARS", 3000);
  if (!text) {
    sendError(response, 400, "Enter a note to organize.");
    return;
  }
  if (text.length > maxCharacters) {
    sendError(response, 413, `Keep demo notes under ${maxCharacters} characters.`);
    return;
  }

  const ip = getClientIp(request);
  if (!ip) {
    sendError(response, 503, "The demo organizer could not check its usage limit.");
    return;
  }

  const today = new Date().toISOString().slice(0, 10);
  try {
    const ipHash = await hashClientIp(ip);
    const ipCount = await incrementDaily(`tsundoku:ip:${today}:${ipHash}`);
    if (ipCount > positiveLimit("DEMO_IP_DAILY_LIMIT", 10)) {
      sendError(response, 429, "You've reached today's demo limit. Please try again tomorrow.");
      return;
    }

    const totalCount = await incrementDaily(`tsundoku:total:${today}`);
    if (totalCount > positiveLimit("DEMO_GLOBAL_DAILY_LIMIT", 100)) {
      sendError(response, 429, "The demo has reached today's usage limit. Please try again tomorrow.");
      return;
    }
  } catch {
    // Fail closed: never call the paid model when usage checks are unavailable.
    sendError(response, 503, "The demo organizer is temporarily unavailable.");
    return;
  }

  try {
    const referenceTime = new Date().toISOString();
    const groqResponse = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${groqKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "openai/gpt-oss-120b",
        max_completion_tokens: positiveLimit("DEMO_MAX_OUTPUT_TOKENS", 1000),
        messages: [
          { role: "system", content: SYSTEM_PROMPT + referenceTime },
          { role: "user", content: text },
        ],
        response_format: {
          type: "json_schema",
          json_schema: { name: "organize_result", schema: ORGANIZE_SCHEMA },
        },
      }),
    });
    if (!groqResponse.ok) {
      sendError(response, 502, "The organizer service couldn't complete that request.");
      return;
    }
    const completion = await groqResponse.json() as {
      choices?: Array<{ message?: { content?: string | null } }>;
    };
    const content = completion.choices?.[0]?.message?.content;
    if (!content) {
      sendError(response, 502, "The organizer returned an empty response.");
      return;
    }
    const result = JSON.parse(content) as unknown;
    response.status(200).json(result);
  } catch {
    sendError(response, 502, "The organizer service is temporarily unavailable.");
  }
}
