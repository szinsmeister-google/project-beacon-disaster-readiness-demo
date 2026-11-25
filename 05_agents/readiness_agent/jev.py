"""JEV-like System-One Probabilistic Models (System-One Probabilistic Routing) for Beacon Readiness Agent.

Implements the System-One (`GEV` / `JEV`) architecture from
Judgment as Expected Value (GEV / System-One):

1. `Pointwise` / `Noul` (`ordinal9` 9-bin softmax expectation):
   - Single prefill pass (`max_output_tokens=1`, `response_logprobs=True`, `thinking_budget=0`)
     with assistant prefill `'{"answer": 0.'`.
   - Extracts logprobs over digits `'1'..'9'` and computes the expected bin value:
     E[bin] = sum_{k=1..9} k * P(k), mapped to [0.01, 0.99].
   - Used for `noul_needs_live_datacommons` (gating whether external Data Commons MCP tools
     should be exposed or pruned) and `noul_needs_write_action`.

2. `Choice` (1-token categorical logprob softmax):
   - Single prefill pass (`max_output_tokens=1`, `response_logprobs=True`, `thinking_budget=0`)
     with assistant prefill `'{"category": "'`.
   - Computes softmax probabilities across single-letter intent tokens (`P`, `A`, `U`, `R`,
     `D`, `W`, `L`, `G`) to route the user request in one prefill pass.

3. ADK `before_model_callback` (`before_model_jev_router`):
   - Runs before the main ADK `LlmAgent` model call.
   - Prunes external `datacommons_*` MCP tools when `Noul(needs_live_datacommons) < 0.50`.
   - Pre-executes deterministic Spanner Graph tools (`get_readiness_pulse`,
     `compare_registration_access`, `find_priority_counties`, `find_repeat_hit_counties`,
     `get_deployment_plan`) and injects the verified data into the single-pass synthesis request,
     collapsing a 2-turn deliberative loop into 1 zero-thinking pass.
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import time
from typing import Any, Optional

from google import genai
from google.genai import types

from . import tools

log = logging.getLogger(__name__)

# Fast Flash backbone for 1-token JEV prefill logprob evaluations (System-One 1-token prefill)
JEV_MODEL = os.environ.get("JEV_MODEL", "gemini-2.5-flash")
JEV_LOCATION = os.environ.get("JEV_LOCATION", "us-central1")

_jev_client: Optional[genai.Client] = None
_JEV_CACHE = tools.LRUCache(ttl_seconds=600)

JEV_CATEGORIES: dict[str, dict[str, str]] = {
    "P": {
        "name": "PULSE",
        "tool": "get_readiness_pulse",
        "description": "National readiness pulse, how we are set for next season, overall coverage gap",
    },
    "A": {
        "name": "ACCESS_CORR",
        "tool": "compare_registration_access",
        "description": "Why people struggle to register online, internet deficit vs age correlation with online FEMA registration",
    },
    "U": {
        "name": "PRIORITY_DEPLOY",
        "tool": "find_priority_counties",
        "description": "Where we should deploy next, top priority unserved high-vulnerability disaster counties lacking mobile team coverage",
    },
    "R": {
        "name": "REPEAT_HIT",
        "tool": "find_repeat_hit_counties",
        "description": "Counties hit repeatedly by multiple compound disaster declarations since 2023",
    },
    "D": {
        "name": "DEPLOY_PLAN",
        "tool": "get_deployment_plan",
        "description": "Show or inspect the current active DeploymentPlan table in Spanner",
    },
    "F": {
        "name": "FEDERAL_PROGRAMS",
        "tool": "compare_federal_programs",
        "description": "Compare households helped and online applications across top federal disaster programs",
    },
    "W": {
        "name": "WRITE_PLAN",
        "tool": "add_to_deployment_plan",
        "description": "Add or save recommended counties to the DeploymentPlan table",
    },
    "L": {
        "name": "LIVE_DC",
        "tool": "datacommons_mcp",
        "description": "Live Data Commons MCP query for statistics NOT in Spanner (e.g. households with no vehicle, satellite flood events, uninsured rate, UN data)",
    },
    "G": {
        "name": "GRAPH_ENTITY_OR_SQL",
        "tool": "multi_tool",
        "description": "Specific county/state profile, specific DR-XXXX disaster history, graph hierarchy path traversal, dataset counts, or custom SQL/GQL",
    },
}

# L0 deterministic fast rules (L0 0ms deterministic pattern gate before LLM call)
_L0_LIVE_DC_PATTERNS = re.compile(
    r"\b(no\s+vehicle|without\s+a?\s*vehicle|0\s+available\s+vehicles|dynamic\s+world|satellite\s+flood|"
    r"uninsured|health\s+insurance|data\.un\.org|united\s+nations|world\s+bank|live\s+data\s+commons)\b",
    re.IGNORECASE,
)
_L0_WRITE_PATTERNS = re.compile(
    r"\b(add\s+(them|these|those|to)\b.*deployment\s+plan|save\s+(them|these|those|actions)\b|insert\s+into\s+deployment)",
    re.IGNORECASE,
)
_L0_PULSE_PATTERNS = re.compile(
    r"\b(how\s+are\s+we\s+set|next\s+season|readiness\s+pulse|what\s+should\s+i\s+know\s+today|primary\s+coverage\s+gap)\b",
    re.IGNORECASE,
)
_L0_ACCESS_PATTERNS = re.compile(
    r"\b(struggle\s+to\s+register\s+online|lack\s+of\s+internet\s+or\s+age|is\s+it\s+us\s+or\s+the\s+market|"
    r"internet\s+deficit\s+correlate|online\s+fema\s+disaster\s+registration\s+share)\b",
    re.IGNORECASE,
)
_L0_PRIORITY_PATTERNS = re.compile(
    r"\b(where\s+should\s+we\s+deploy\s+next|priority\s+counties|unserved\s+areas|"
    r"no\s+mobile\s+response\s+team\s+coverage|unserved\s+high-vulnerability)\b",
    re.IGNORECASE,
)
_L0_REPEAT_PATTERNS = re.compile(
    r"\b(hit\s+repeatedly|compound\s+disaster\s+history|multiple\s+major\s+disaster|repeat\s+disaster\s+counties)\b",
    re.IGNORECASE,
)
_L0_SHOW_PLAN_PATTERNS = re.compile(
    r"\b(show\s+(the\s+|active\s+)?deployment\s+plan|what\s+is\s+in\s+the\s+deployment\s+plan|current\s+deployment\s+plan)\b",
    re.IGNORECASE,
)
_L0_PROGRAMS_PATTERNS = re.compile(
    r"\b(households\s+helped|assisted\s+households|top\s+federal\s+disaster\s+programs|flagship\s+u\.?s\.?\s+federal\s+disaster)\b",
    re.IGNORECASE,
)
_STATE_FILTER_PATTERN = re.compile(
    r"\b(?:in|for|across)\s+(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b"
)


def _get_jev_client() -> Optional[genai.Client]:
    global _jev_client
    if _jev_client is not None:
        return _jev_client
    project = (
        os.environ.get("SPANNER_PROJECT")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("GCP_PROJECT_ID", "")
    )
    try:
        _jev_client = genai.Client(vertexai=True, project=project, location=JEV_LOCATION)
        return _jev_client
    except Exception as exc:  # pylint: disable=broad-except
        log.warning("Could not initialize JEV genai.Client: %s", exc)
        return None


def _prefill_top_logprobs(
    system_instruction: str,
    user_prompt: str,
    assistant_prefill: str,
) -> tuple[dict[str, float], float]:
    """Executes a 1-token prefill-only JEV call (`max_output_tokens=1`, `response_logprobs=True`)."""
    client = _get_jev_client()
    if client is None:
        return {}, 0.0
    t0 = time.perf_counter()
    try:
        resp = client.models.generate_content(
            model=JEV_MODEL,
            contents=[
                types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)]),
                types.Content(role="model", parts=[types.Part.from_text(text=assistant_prefill)]),
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0,
                max_output_tokens=1,
                response_logprobs=True,
                logprobs=10,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        if not resp.candidates:
            return {}, elapsed_ms
        lp_res = resp.candidates[0].logprobs_result
        if not lp_res or not lp_res.top_candidates:
            return {}, elapsed_ms
        first_step = lp_res.top_candidates[0].candidates or []
        out: dict[str, float] = {}
        for cand in first_step:
            tok = (cand.token or "").strip()
            if tok and tok not in out and cand.log_probability is not None:
                out[tok] = float(cand.log_probability)
        return out, elapsed_ms
    except Exception as exc:  # pylint: disable=broad-except
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        log.warning("JEV 1-token prefill call failed (%.1f ms): %s", elapsed_ms, exc)
        return {}, elapsed_ms


def jev_noul(
    user_query: str,
    criterion: str,
    positive_guidance: str,
    negative_guidance: str,
) -> dict[str, Any]:
    """Implements `jev_api.Noul` (`ordinal9` 9-bin softmax expectation in [0.01, 0.99])."""
    sys_inst = (
        f"You are a System-One probabilistic classifier (`Noul`).\n"
        f"Criterion: {criterion}\n"
        f"Positive Guidance (score 0.9): {positive_guidance}\n"
        f"Negative Guidance (score 0.1): {negative_guidance}\n"
        f"Output JSON with key 'answer' as a probability in [0.1, 0.9]."
    )
    token_lps, latency_ms = _prefill_top_logprobs(
        system_instruction=sys_inst,
        user_prompt=f"Query: {user_query}",
        assistant_prefill='{"answer": 0.',
    )
    digits = [str(k) for k in range(1, 10)]
    present = {d: token_lps[d] for d in digits if d in token_lps}
    if not present:
        return {"score": 0.05, "latency_ms": round(latency_ms, 1), "bin_probs": {}}

    max_lp = max(present.values())
    weights = {d: math.exp(lp - max_lp) for d, lp in present.items()}
    total_w = sum(weights.values())
    probs = {d: w / total_w for d, w in weights.items()}
    expected_bin = sum(int(d) * p for d, p in probs.items())
    score = 0.01 + ((expected_bin - 1.0) / 8.0) * 0.98
    return {
        "score": round(score, 4),
        "latency_ms": round(latency_ms, 1),
        "bin_probs": {d: round(p, 4) for d, p in probs.items()},
    }


def jev_choice(user_query: str) -> dict[str, Any]:
    """Implements `jev_api.Choice` single-token categorical softmax over `JEV_CATEGORIES`."""
    cat_lines = "\n".join(
        f'- "{k}": {v["name"]} -> {v["description"]}'
        for k, v in JEV_CATEGORIES.items()
    )
    sys_inst = (
        "You are a System-One categorical router (`Choice`). Classify the user query into "
        "one of the single-letter category keys below:\n"
        f"{cat_lines}"
    )
    token_lps, latency_ms = _prefill_top_logprobs(
        system_instruction=sys_inst,
        user_prompt=f"Query: {user_query}",
        assistant_prefill='{"category": "',
    )
    valid_keys = list(JEV_CATEGORIES.keys())
    present = {k: token_lps[k] for k in valid_keys if k in token_lps}
    if not present:
        return {
            "key": "G",
            "category": "GRAPH_ENTITY_OR_SQL",
            "tool": "multi_tool",
            "confidence": 0.5,
            "latency_ms": round(latency_ms, 1),
            "probs": {},
        }

    max_lp = max(present.values())
    weights = {k: math.exp(lp - max_lp) for k, lp in present.items()}
    total_w = sum(weights.values())
    probs = {k: w / total_w for k, w in weights.items()}
    best_k = max(probs, key=probs.get)
    return {
        "key": best_k,
        "category": JEV_CATEGORIES[best_k]["name"],
        "tool": JEV_CATEGORIES[best_k]["tool"],
        "confidence": round(probs[best_k], 4),
        "latency_ms": round(latency_ms, 1),
        "probs": {JEV_CATEGORIES[k]["name"]: round(p, 4) for k, p in probs.items()},
    }


def classify_turn(user_text: str) -> dict[str, Any]:
    """Runs L0 deterministic gate + L1 JEV (`Choice` & `Noul`) classification with caching."""
    clean = (user_text or "").strip()
    if not clean:
        return {"key": "G", "category": "GRAPH_ENTITY_OR_SQL", "confidence": 1.0, "needs_live_dc": 0.0, "source": "empty"}

    def _compute() -> dict[str, Any]:
        # Path 4 (L0 deterministic gate): L0 0ms deterministic pattern check first
        if _L0_WRITE_PATTERNS.search(clean):
            return {"key": "W", "category": "WRITE_PLAN", "tool": "add_to_deployment_plan", "confidence": 0.99, "needs_live_dc": 0.01, "latency_ms": 0.0, "source": "L0_deterministic"}
        if _L0_LIVE_DC_PATTERNS.search(clean):
            return {"key": "L", "category": "LIVE_DC", "tool": "datacommons_mcp", "confidence": 0.99, "needs_live_dc": 0.99, "latency_ms": 0.0, "source": "L0_deterministic"}
        if _L0_PULSE_PATTERNS.search(clean):
            return {"key": "P", "category": "PULSE", "tool": "get_readiness_pulse", "confidence": 0.99, "needs_live_dc": 0.01, "latency_ms": 0.0, "source": "L0_deterministic"}
        if _L0_ACCESS_PATTERNS.search(clean):
            return {"key": "A", "category": "ACCESS_CORR", "tool": "compare_registration_access", "confidence": 0.99, "needs_live_dc": 0.01, "latency_ms": 0.0, "source": "L0_deterministic"}
        if _L0_PRIORITY_PATTERNS.search(clean):
            return {"key": "U", "category": "PRIORITY_DEPLOY", "tool": "find_priority_counties", "confidence": 0.99, "needs_live_dc": 0.01, "latency_ms": 0.0, "source": "L0_deterministic"}
        if _L0_REPEAT_PATTERNS.search(clean):
            return {"key": "R", "category": "REPEAT_HIT", "tool": "find_repeat_hit_counties", "confidence": 0.99, "needs_live_dc": 0.01, "latency_ms": 0.0, "source": "L0_deterministic"}
        if _L0_SHOW_PLAN_PATTERNS.search(clean):
            return {"key": "D", "category": "DEPLOY_PLAN", "tool": "get_deployment_plan", "confidence": 0.99, "needs_live_dc": 0.01, "latency_ms": 0.0, "source": "L0_deterministic"}
        if _L0_PROGRAMS_PATTERNS.search(clean):
            return {"key": "F", "category": "FEDERAL_PROGRAMS", "tool": "compare_federal_programs", "confidence": 0.99, "needs_live_dc": 0.01, "latency_ms": 0.0, "source": "L0_deterministic"}

        # L1 JEV 1-token prefill logprob classification
        choice_res = jev_choice(clean)
        if choice_res["key"] == "L":
            needs_live_dc = 0.95
        elif choice_res["key"] == "G" and choice_res.get("confidence", 0.0) < 0.85:
            noul_res = jev_noul(
                user_query=clean,
                criterion="Does this query require live external Data Commons indicators not stored in Spanner (such as households with 0 vehicles, Dynamic World satellite flood events, uninsured rate, or UN international stats)?",
                positive_guidance="Query asks for households with no vehicle, satellite flood events, uninsured population, or live Data Commons lookup.",
                negative_guidance="Query asks about disaster readiness pulse, internet vs age online registration, priority unserved counties, repeat-hit counties, county/state profiles, or the Spanner deployment plan.",
            )
            needs_live_dc = noul_res["score"]
        else:
            needs_live_dc = 0.02
        return {
            **choice_res,
            "needs_live_dc": needs_live_dc,
            "source": "L1_jev_logprob",
        }

    return _JEV_CACHE.get(f"jev:{clean.lower()}", _compute)


def should_enable_live_dc(readonly_context: Any) -> bool:
    """Evaluates whether the current user turn requires live Data Commons MCP tools (`Noul >= 0.50`)."""
    if readonly_context is None:
        return False
    user_content = getattr(readonly_context, "user_content", None)
    if user_content is None:
        return False
    texts = [
        getattr(p, "text", "")
        for p in (getattr(user_content, "parts", None) or [])
        if getattr(p, "text", None)
    ]
    user_text = "\n".join(texts).strip()
    if not user_text:
        return False
    route = classify_turn(user_text)
    return float(route.get("needs_live_dc", 0.0)) >= 0.50


def _execute_fast_spanner_tool(key: str, user_text: str) -> Optional[tuple[str, Any]]:
    """Executes the matched read-only Spanner Graph tool directly when confidence is high."""
    try:
        if key == "P":
            return "get_readiness_pulse", tools.get_readiness_pulse()
        if key == "A":
            factor = "no_internet"
            low = user_text.lower()
            if "disability" in low:
                factor = "disability"
            elif "poverty" in low:
                factor = "poverty"
            elif "age" in low and "internet" not in low:
                factor = "age_65"
            return f"compare_registration_access(comparison_factor='{factor}')", tools.compare_registration_access(comparison_factor=factor)
        if key == "U":
            st_match = _STATE_FILTER_PATTERN.search(user_text)
            state_code = st_match.group(1).upper() if st_match else None
            return f"find_priority_counties(top_n=5, state={state_code!r})", tools.find_priority_counties(top_n=5, state=state_code)
        if key == "R":
            return "find_repeat_hit_counties(min_disasters=3, limit=10)", tools.find_repeat_hit_counties(min_disasters=3, limit=10)
        if key == "D":
            return "get_deployment_plan()", tools.get_deployment_plan(strong=False)
        if key == "F":
            return "compare_federal_programs()", tools.compare_federal_programs()
    except Exception as exc:  # pylint: disable=broad-except
        log.warning("Fast Spanner tool execution failed for key=%s: %s", key, exc)
    return None


def _extract_latest_user_turn_info(llm_request: Any) -> tuple[str, bool]:
    """Returns (latest_user_text, has_function_response_after_latest_user)."""
    contents = getattr(llm_request, "contents", None) or []
    latest_user_idx = -1
    latest_user_text = ""
    for idx, content in enumerate(contents):
        if getattr(content, "role", "") == "user":
            texts = [
                getattr(p, "text", "")
                for p in (getattr(content, "parts", None) or [])
                if getattr(p, "text", None)
            ]
            if texts:
                latest_user_idx = idx
                latest_user_text = "\n".join(texts).strip()

    if latest_user_idx < 0:
        return "", False

    has_fn_resp = False
    for content in contents[latest_user_idx:]:
        for p in (getattr(content, "parts", None) or []):
            if getattr(p, "function_response", None) is not None:
                has_fn_resp = True
                break
    return latest_user_text, has_fn_resp


def _prune_mcp_tools_in_place(llm_request: Any) -> None:
    """Removes `datacommons_*` MCP function declarations when `Noul(needs_live_dc) < 0.50`."""
    cfg = getattr(llm_request, "config", None)
    if not cfg or not getattr(cfg, "tools", None):
        return
    new_tools = []
    for tool_obj in cfg.tools:
        fn_decls = getattr(tool_obj, "function_declarations", None)
        if not fn_decls:
            new_tools.append(tool_obj)
            continue
        kept = [
            fd for fd in fn_decls
            if not (getattr(fd, "name", "") or "").startswith("datacommons")
        ]
        if kept:
            tool_obj.function_declarations = kept
            new_tools.append(tool_obj)
    cfg.tools = new_tools
    if hasattr(llm_request, "tools_dict") and isinstance(llm_request.tools_dict, dict):
        for k in list(llm_request.tools_dict.keys()):
            if k.startswith("datacommons"):
                llm_request.tools_dict.pop(k, None)


def before_model_jev_router(callback_context: Any, llm_request: Any) -> Optional[Any]:  # pylint: disable=unused-argument
    """ADK `before_model_callback` applying JEV System-One routing and tool gating."""
    # Enforce zero thinking budget on the main model request (System-One zero-thinking synthesis)
    if getattr(llm_request, "config", None) is not None:
        llm_request.config.thinking_config = types.ThinkingConfig(thinking_budget=0)

    user_text, has_fn_resp = _extract_latest_user_turn_info(llm_request)
    if not user_text:
        return None

    route = classify_turn(user_text)
    log.info(
        "JEV System-One Router: key=%s category=%s conf=%.4f needs_live_dc=%.2f source=%s",
        route.get("key"),
        route.get("category"),
        route.get("confidence", 0.0),
        route.get("needs_live_dc", 0.0),
        route.get("source"),
    )

    # 1. Noul Tool Gate: prune external Data Commons MCP tools if not needed
    if route.get("needs_live_dc", 0.0) < 0.50:
        _prune_mcp_tools_in_place(llm_request)

    # 2. Choice Pre-Execution: if this is the initial pass of a high-confidence read-only
    #    canonical intent (P, A, U, R, D, F), execute the Spanner tool now and inject the result
    #    so the LLM answers in 1 single pass instead of 2 sequential turns!
    if not has_fn_resp and route.get("confidence", 0.0) >= 0.80 and route.get("key") in ("P", "A", "U", "R", "D", "F"):
        fast_exec = _execute_fast_spanner_tool(route["key"], user_text)
        if fast_exec is not None:
            tool_sig, tool_result = fast_exec
            # Disable tool calling for this single-pass synthesis so the LLM writes the final answer immediately
            if getattr(llm_request, "config", None) is not None:
                llm_request.config.tools = []
            injected_context = (
                f"\n\n[JEV System-One Pre-Executed Tool `{tool_sig}` "
                f"(category={route['category']}, confidence={route['confidence']}, source={route['source']}) — "
                f"Use the verified Spanner Graph result below to answer the user directly right now without calling any tools. "
                f"IMPORTANT: Place the visual comparison table / visual bar breakdown FIRST at the VERY TOP of your response, followed by the concise executive summary below]:\n"
                f"```json\n{json.dumps(tool_result, ensure_ascii=False)}\n```"
            )
            contents = getattr(llm_request, "contents", None) or []
            if contents and getattr(contents[-1], "role", "") == "user":
                contents[-1].parts.append(types.Part.from_text(text=injected_context))

    return None
