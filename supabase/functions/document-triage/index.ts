import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

interface TriageRequest {
  document_id: string;
  content: string;
  user_id: string;
}

interface PIIMatch {
  type: string;
  matches: string[];
}

// PII detection patterns (matching Lambda version)
const PII_PATTERNS: Record<string, RegExp> = {
  ssn: /\b\d{3}-\d{2}-\d{4}\b/g,
  aws_access_key: /\b(AKIA|ASCA|ASIA)[A-Z0-9]{16}\b/g,
  credit_card: /\b(?:\d[ -]*?){13,16}\b/g,
  email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
  phone_us: /\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g,
  api_key_generic: /\b(sk-|pk-|rk-)[A-Za-z0-9]{32,}\b/g,
};

function scanForPII(text: string): { hasPII: boolean; types: string[]; matches: PIIMatch[] } {
  const detectedTypes: string[] = [];
  const matches: PIIMatch[] = [];

  for (const [type, pattern] of Object.entries(PII_PATTERNS)) {
    const found = text.match(pattern);
    if (found && found.length > 0) {
      detectedTypes.push(type);
      matches.push({ type, matches: found.slice(0, 5) });
    }
  }

  return { hasPII: detectedTypes.length > 0, types: detectedTypes, matches };
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    // Initialize Supabase client with service role
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Parse request
    const { document_id, content, user_id } = await req.json() as TriageRequest;

    if (!document_id || !content || !user_id) {
      return new Response(
        JSON.stringify({ error: "Missing required fields: document_id, content, user_id" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Scan for PII
    const { hasPII, types, matches } = scanForPII(content);

    // Determine classification
    const status = hasPII ? "quarantined" : "approved";

    // Update document in database
    const { error } = await supabase
      .from("user_documents")
      .update({
        classification_status: status,
        pii_detected: hasPII,
        detected_pii_types: types,
        pii_matches: matches,
      })
      .eq("id", document_id);

    if (error) {
      console.error("Database update error:", error);
      return new Response(
        JSON.stringify({ error: "Failed to update document classification" }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    return new Response(
      JSON.stringify({
        document_id,
        status,
        pii_detected: hasPII,
        pii_types: types,
        matches,
        message: hasPII ? "Document quarantined — PII detected" : "Document approved for vector ingestion",
      }),
      { status: 200, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );

  } catch (err) {
    console.error("Edge function error:", err);
    return new Response(
      JSON.stringify({ error: "Internal server error" }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});