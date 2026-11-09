"use client";

import { useEffect, useRef } from "react";
import { callApi } from "@/lib/api/client";

/**
 * Records "education viewed" once the result is actually on screen. It lives on the result page,
 * not in the API's result read, because the dashboard reads results too, and seeing a dashboard
 * isn't reading your result.
 */
export function MarkViewed({ caseId }: { caseId: string }) {
  const sent = useRef(false);
  useEffect(() => {
    if (sent.current) return;
    sent.current = true;
    void callApi(`journey/${caseId}/steps`, { method: "POST", body: { to_state: "EDUCATION_VIEWED" } });
  }, [caseId]);
  return null;
}
