"""
Pipeline Governance Compliance Agent — Core Engine
"""

import json
import os
import streamlit as st
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Lazy client — created on first use, not at import time
# ---------------------------------------------------------------------------
_client = None
_deployment = None


def get_secret(key, default=None):
    """Read from Streamlit secrets first, then fall back to env vars."""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError, AttributeError):
        return os.getenv(key, default)


def _get_client():
    global _client, _deployment
    if _client is None:
        _client = AzureOpenAI(
            api_key=get_secret("AZURE_OPENAI_API_KEY"),
            api_version=get_secret("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
            azure_endpoint=get_secret("AZURE_OPENAI_ENDPOINT"),
        )
        _deployment = get_secret("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    return _client, _deployment


SYSTEM_PROMPT = r"""
You are the **Pipeline Governance Compliance Agent** for a CI/CD CoE on Azure DevOps.

TASK: Receive inline YAML → identify violations → generate full compliant hierarchy.

━━━ ARCHITECTURE ━━━
```
L1: Consuming Pipeline (app repo) → L2: Stage → L3: Job → L4: Orchestrator Task → L5: Scripts (.sh)
```
Orchestrator calls .sh scripts via `- bash:` steps. Parameters passed as env vars.

━━━ RULES ━━━
1. Template Distribution: shared repo via `resources: repositories`.
2. Parameters: tool-specific (see below). Global toggle: `WhiteSourceRun`.
3. Hierarchy: stages → jobs → tasks → scripts. Naming: `technology_verb_{scope}_type.yaml`.
4. Three-step deferred enforcement: scan → publish (continueOnError) → check. Exit code 9 = policy violation deferred.
5. Default-secure: `enableFailPolicy: true`.
6. Credentials from Key Vault only.
7. README: 9 sections per template (stage, job, task).
8. Artefacts: SCA: PDF, SBOM, reachability, logs. SAST: JSON+HTML. Container: JSON, SARIF, SPDX-JSON, CycloneDX-JSON.

━━━ TOOL-SPECIFIC PARAMETERS (use ONLY the matching set) ━━━

**Mend SCA**: `userKey`, `email`, `apiKey`, `productToken`, `mendUrl`, `version`, `productPrefix`, `azdoApplicationName`, `enableFailPolicy`(true), `tags`, `logLevel`(WARNING), `enableReachability`(true), `generateReport`(true), `exportSBOM`(true), `sbomFormat`(cyclonedx), `additionalFlags`, `condition`
**Mend SAST**: `userKey`, `email`, `apiKey`, `version`, `productPrefix`, `azdoApplicationName`, `enableFailPolicy`(true), `failOnCritical`(true), `failOnHigh`(false), `failOnMedium`(false), `mendUrl`, `condition`
**Container**: `userKey`, `email`, `apiKey`, `version`, `productPrefix`, `azdoApplicationName`, `dockerRegistry`, `imageName`, `imageTag`, `dockerfilePath`, `enableFailPolicy`(true), `failOnCritical`(true), `failOnHigh`(false), `mendUrl`, `condition`
**SonarQube**: `sonarQubeServiceConnection`, `projectPrefix`, `projectName`, `scannerMode`(cli|dotnet|other), `buildBreak`(true), `pollingTimeoutSec`(300), `sonarExclusions`, `sonarCoverageExclusions`, `verboseLogging`(false), `condition`

NEVER mix parameters across tools.

━━━ ORCHESTRATOR CALLS SCRIPTS ━━━

The orchestrator task calls scripts via `- bash:` steps. The number depends on the tool:
- **Mend SCA**: 3 scripts (scan → publish → check)
- **Mend SAST**: 3 scripts (scan → publish → check)
- **Container**: 4 scripts (build → scan → publish → check)
- **SonarQube**: uses AzDO built-in tasks (SonarQubePrepare@7, Analyze@7, Publish@7), no bash scripts
Example for Mend SCA:

```yaml
steps:
  # Step 1: SCAN
  - bash: |
      path="$TEMPLATE_DIR/scripts/mend-sca-scan.sh"
      dos2unix "$path"; chmod +x "$path"; "$path"
    displayName: 'Mend SCA Scan'
    name: 'mend_sca_scan'
    timeoutInMinutes: 15
    condition: and(${{ parameters.condition }}, eq(variables['WhiteSourceRun'], 'true'))
    env:
      TEMPLATE_DIR: '$(Pipeline.Workspace)/$(azTemplateRepo)'
      MEND_USER_KEY: '${{ parameters.userKey }}'

  # Step 2: PUBLISH (always runs even if scan found violations)
  - bash: |
      path="$TEMPLATE_DIR/scripts/mend-sca-publish.sh"
      dos2unix "$path"; chmod +x "$path"; "$path"
    displayName: 'Mend SCA Publish'
    condition: and(${{ parameters.condition }}, eq(variables['WhiteSourceRun'], 'true'))
    continueOnError: true
    env:
      TEMPLATE_DIR: '$(Pipeline.Workspace)/$(azTemplateRepo)'

  # Step 3: CHECK (deferred build break)
  - bash: |
      path="$TEMPLATE_DIR/scripts/mend-sca-check.sh"
      dos2unix "$path"; chmod +x "$path"; "$path"
    displayName: 'Mend SCA Check'
    condition: and(${{ parameters.condition }}, eq(variables['WhiteSourceRun'], 'true'))
    env:
      TEMPLATE_DIR: '$(Pipeline.Workspace)/$(azTemplateRepo)'
      MEND_EC: $(mend_sca_scan.EC_xxx)
```

Match the script count to the tool: Mend SCA/SAST = 3 (scan, publish, check). Container = 4 (build, scan, publish, check). SonarQube = 0 (uses built-in AzDO tasks, no scripts).

━━━ SCRIPT STRUCTURE (keep concise — 30-50 lines each) ━━━

```bash
#!/bin/bash
set -euo pipefail
# ─── Constants ────────────────────────────────────────────
MEND_EXIT_POLICY=9
BASE_DIR="${STAGING_DIR}/Mend"
# ─── Derived values ───────────────────────────────────────
product_name="${PRODUCT_PREFIX}_${PRODUCT_APP}"
# ─── Logging helpers ──────────────────────────────────────
log_info()    { echo "[INFO]  $*" >&2; }
log_success() { echo "[OK]    $*" >&2; }
log_warn()    { echo "[WARN]  $*" >&2; }
log_error()   { echo "[ERROR] $*" >&2; }
# ─── Functions ────────────────────────────────────────────
function_name() { ... }
# ─── Main ─────────────────────────────────────────────────
log_info "Starting..."
```

Keep scripts at 30-50 lines. Focus on key logic per step.

━━━ DATA MASKING (MANDATORY) ━━━

ALL output MUST mask sensitive/internal identifiers using bracketed placeholders:
- Organisation names: `[Organisation]`, `[Project]`, `[Pipeline Templates Repository]`
- Variable group names: `[Variable Group - Tools]`, `[Variable Group - Secrets]`
- Credential variable names: `$([Mend-User-Key])`, `$([Mend-Email])`, `$([Mend-API-Key])`, `$([Mend-Product-Token])`
- Product prefixes: `[ProductPrefix]` (never use real internal prefixes)
- Service connections: `[SonarQube-Service-Connection]`
- URLs: `[Mend-Platform-URL]`
- Any internal system names, team names, or repository-specific identifiers

Apply this to compliant_yaml, template_files, scripts, readme_files, and violations evidence.

━━━ CONFIGURATION REDUCTION CALCULATION ━━━

The reduction compares ORIGINAL inline YAML vs the CONSUMING PIPELINE (compliant_yaml) only.
- `original_line_count` = non-empty lines in the user's input YAML
- `compliant_line_count` = non-empty lines in the compliant_yaml (the template reference call)
- `reduction_percentage` = ((original - compliant) / original) * 100

━━━ CONSUMING PIPELINE EXAMPLES ━━━

**Mend SCA:**
```yaml
resources:
  repositories:
    - repository: templates
      type: git
      name: [Project]/[Pipeline Templates Repository]
      ref: refs/heads/main
variables:
  - group: [Variable Group - Tools]
  - group: [Variable Group - Secrets]
stages:
  - template: templates/stages/mend_sca_scan_stage.yaml@templates
    parameters:
      userKey: '$([Mend-User-Key])'
      email: '$([Mend-Email])'
      apiKey: '$([Mend-API-Key])'
      version: '$(GitVersion.MajorMinorPatch)'
      productPrefix: '[ProductPrefix]'
      azdoApplicationName: '$(Build.Repository.Name)'
      productToken: '$([Mend-Product-Token])'
```

**SonarQube:**
```yaml
resources:
  repositories:
    - repository: templates
      type: git
      name: [Project]/[Pipeline Templates Repository]
      ref: refs/heads/main
stages:
  - template: templates/stages/sonarqube_scan_stage.yaml@templates
    parameters:
      sonarQubeServiceConnection: '[SonarQube-Service-Connection]'
      projectPrefix: '[ProductPrefix]'
      projectName: '$(Build.Repository.Name)'
      scannerMode: 'cli'
```

━━━ README (9 sections, keep each section concise) ━━━
## Overview — 2-3 sentences
## Prerequisites — bullet list
## Parameters — table: | Name | Required | Default | Description | Example |
## Flow — Text-based step diagram showing execution flow with decision points. Use arrows and labels.
## Output — artifact tree
## Variables — table
## Secrets — variable groups
## Usage Examples — 1-2 yaml examples
## Error Handling — exit code table + 3-4 troubleshooting tips

━━━ OUTPUT FORMAT ━━━

{
  "tool_detected": "...",
  "scanner_mode": "...",
  "violations": [{ "rule":"...", "severity":"...", "description":"...", "evidence":"...", "remediation":"..." }],
  "compliance_score_before": 0-100,
  "compliance_score_after": 0-100,
  "original_line_count": <int>,
  "compliant_line_count": <int>,
  "reduction_percentage": <float>,
  "compliant_yaml": "<MUST be populated>",
  "template_files": [
    { "filename":"templates/stages/xxx.yaml", "hierarchy_level":"stage", "description":"...", "calls":"...", "content":"..." },
    { "filename":"templates/jobs/xxx.yaml", "hierarchy_level":"job", "description":"...", "calls":"...", "content":"..." },
    { "filename":"templates/tasks/xxx.yaml", "hierarchy_level":"task", "description":"Orchestrator — calls scripts via - bash:", "calls":"scripts/xxx-scan.sh, scripts/xxx-publish.sh, scripts/xxx-check.sh", "content":"..." },
    { "filename":"scripts/xxx-scan.sh", "hierarchy_level":"script", "description":"Step 1: Scan", "calls":null, "content":"..." },
    { "filename":"scripts/xxx-publish.sh", "hierarchy_level":"script", "description":"Step 2: Publish", "calls":null, "content":"..." },
    { "filename":"scripts/xxx-check.sh", "hierarchy_level":"script", "description":"Step 3: Check", "calls":null, "content":"..." }
  ],
  "readme_files": [
    { "filename":"README_xxx_stage.md", "template_ref":"templates/stages/xxx.yaml", "content":"<9 sections with content>" },
    { "filename":"README_xxx_job.md", "template_ref":"templates/jobs/xxx.yaml", "content":"<9 sections with content>" },
    { "filename":"README_xxx_task.md", "template_ref":"templates/tasks/xxx.yaml", "content":"<9 sections with content>" }
  ],
  "summary": "..."
}

CRITICAL:
- NEVER cross-contaminate tool parameters.
- compliant_yaml MUST be populated.
- compliance_score_before = how compliant the INPUT yaml is (0 = fully non-compliant, 100 = already compliant). Score against all 8 rules.
- compliance_score_after = how compliant the GENERATED output is (should be 90-100 after applying CoE templates). Score the compliant_yaml + template_files against all 8 rules.
- Orchestrator script count is tool-dependent: Mend SCA/SAST = 3 (scan, publish, check). Container = 4 (build, scan, publish, check). SonarQube = 0 (built-in tasks only).
- readme_files MUST have 3 entries (stage, job, task) each with full 9-section content. Empty content = WRONG.
- Keep scripts 30-50 lines. Keep READMEs concise but complete. Budget your tokens wisely.
- MASK ALL sensitive identifiers: use [Organisation], [Project], [Mend-User-Key], [Mend-Email], [Mend-API-Key], [Mend-Product-Token], [ProductPrefix], [SonarQube-Service-Connection], [Variable Group - Tools], [Variable Group - Secrets], [Mend-Platform-URL]. Never output real internal names.
- reduction_percentage = ((original_line_count - compliant_line_count) / original_line_count) * 100. Compare input YAML vs consuming pipeline (compliant_yaml) ONLY.
- Return ONLY JSON.
""".strip()

# ---------------------------------------------------------------------------
# Tool detection + validation are now code-based (no LLM calls) for speed.
# See detect_tool() and _validate_output() below.
# ---------------------------------------------------------------------------


def _parse_json_response(raw: str) -> dict:
    """Parse JSON from LLM response, stripping markdown fences if present."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("\n", 1)[0]
    return json.loads(raw)


def detect_tool(inline_yaml: str) -> str:
    """Classify which security tool the inline YAML implements (regex-based, no LLM)."""
    yaml_lower = inline_yaml.lower()
    if any(kw in yaml_lower for kw in ["sonarqubeprepare", "sonarqubeanalyze", "sonarqubepublish", "sonarqube", "sonar.exclusions"]):
        return "SonarQube"
    if any(kw in yaml_lower for kw in ["docker build", "docker save", "mend image", "container scan", "image.tar", "buildkit"]):
        return "Container Scanning"
    if any(kw in yaml_lower for kw in ["mend sast", "mend sast ", "--formats \"json,html\"", "sast scan"]):
        return "Mend SAST"
    if any(kw in yaml_lower for kw in ["whitesource", "wss-unified-agent", "mend dep", "mend sca", "unified-agent", "wss.url"]):
        return "Mend SCA"
    if any(kw in yaml_lower for kw in ["sourceanalyzer", "fortifyclient", "fortify", ".fpr"]):
        return "Fortify"
    return "Unknown"


def _validate_output(result: dict) -> dict:
    """Validate generated output using Python code checks (no LLM call)."""
    issues = []

    # Check 1: compliant_yaml populated
    cy = result.get("compliant_yaml", "")
    if not cy or len(cy.strip()) < 10:
        issues.append("compliant_yaml is empty or too short")
    elif "resources" not in cy.lower() and "repositories" not in cy.lower():
        issues.append("compliant_yaml missing 'resources: repositories' block")

    # Check 2: template_files present with all hierarchy levels
    tfiles = result.get("template_files", [])
    levels_found = {f.get("hierarchy_level") for f in tfiles}
    for level in ["stage", "job", "task"]:
        if level not in levels_found:
            issues.append(f"template_files missing '{level}' hierarchy level")

    # Check 3: orchestrator task uses bash steps
    tasks = [f for f in tfiles if f.get("hierarchy_level") == "task"]
    for t in tasks:
        content = t.get("content", "")
        if "- bash:" not in content and "bash:" not in content.lower():
            if "SonarQube" not in result.get("tool_detected", ""):
                issues.append(f"Orchestrator task '{t.get('filename', '?')}' missing '- bash:' steps")

    # Check 4-5: scripts structure
    scripts = [f for f in tfiles if f.get("hierarchy_level") == "script"]
    for s in scripts:
        content = s.get("content", "")
        if "#!/bin/bash" not in content:
            issues.append(f"Script '{s.get('filename', '?')}' missing #!/bin/bash shebang")
        if "set -euo pipefail" not in content:
            issues.append(f"Script '{s.get('filename', '?')}' missing 'set -euo pipefail'")

    # Check 6: sensitive data leak check
    full_output = json.dumps(result).lower()
    leak_patterns = ["devopstoolscontroller", "devopsvariable", "whitesource-user-key",
                     "whitesource-api-key", "whitesource-email", "wds-mend"]
    for pattern in leak_patterns:
        if pattern in full_output:
            issues.append(f"Sensitive identifier leak detected: '{pattern}'")

    # Check 7: readme_files present
    rfiles = result.get("readme_files", [])
    if len(rfiles) < 3:
        issues.append(f"readme_files has {len(rfiles)} entries — need 3 (stage, job, task)")
    for rf in rfiles:
        if not rf.get("content", "").strip():
            issues.append(f"README '{rf.get('filename', '?')}' has empty content")

    # Check 8: parameter cross-contamination
    tool = result.get("tool_detected", "").lower()
    if "sonarqube" in tool:
        for t in tfiles:
            c = t.get("content", "").lower()
            if "userkey" in c or "apikey" in c or "mendurl" in c:
                issues.append("SonarQube output contains Mend-specific parameters (cross-contamination)")
                break
    elif "mend" in tool or "container" in tool:
        for t in tfiles:
            c = t.get("content", "").lower()
            if "sonarqubeserviceconnection" in c:
                issues.append("Mend/Container output contains SonarQube parameters (cross-contamination)")
                break

    # Check 9: reduction calculation
    orig = result.get("original_line_count", 0)
    comp = result.get("compliant_line_count", 0)
    reported_reduction = result.get("reduction_percentage", 0)
    if orig > 0 and comp > 0:
        expected = round(((orig - comp) / orig) * 100, 2)
        if abs(float(reported_reduction) - expected) > 5:
            issues.append(f"reduction_percentage ({reported_reduction}%) doesn't match calculation ({expected}%)")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "fix_instructions": "; ".join(issues) if issues else "",
    }


def analyse_pipeline(inline_yaml: str, max_retries: int = 2) -> dict:
    """
    Agentic analysis loop:
    1. Detect tool type
    2. Generate compliant hierarchy
    3. Self-validate output
    4. Check compliance_score_after >= 90
    5. If validation fails OR score too low, retry with fix instructions
    """
    client, deployment = _get_client()

    # Step 1: Autonomous tool detection
    detected_tool = detect_tool(inline_yaml)

    # Step 2: Generate + validate loop
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Analyse this inline pipeline YAML for governance compliance:\n\n```yaml\n{inline_yaml}\n```"},
    ]

    attempt = 0
    validation_log = []
    best_result = None
    best_score = -1

    while attempt <= max_retries:
        attempt += 1

        response = client.chat.completions.create(
            model=deployment,
            messages=messages,
            max_tokens=16384,
            temperature=0.1,
        )

        raw = response.choices[0].message.content.strip()
        try:
            result = _parse_json_response(raw)
        except json.JSONDecodeError:
            validation_log.append({"attempt": attempt, "error": "JSON parse failed"})
            if attempt <= max_retries:
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyse this inline pipeline YAML for governance compliance. Your previous response was not valid JSON. Return ONLY a JSON object.\n\n```yaml\n{inline_yaml}\n```"},
                ]
                continue
            return {"error": "Failed to parse agent response as JSON after retries.", "raw_response": raw, "validation_log": validation_log}

        # Step 3: Self-validation
        validation = _validate_output(result)

        # Step 4: Compute real compliance score from validator (don't trust self-reported)
        issues = validation.get("issues", [])
        struct_pass = validation.get("valid", False)

        # Real score: start at 100, deduct per issue. Each structural issue = ~12 points off.
        validator_score = max(0, 100 - (len(issues) * 12))
        # Override the self-reported score with the validator-computed one
        result["compliance_score_after"] = validator_score if not struct_pass else max(validator_score, int(result.get("compliance_score_after", result.get("compliance_score", 0))))

        score_after = result["compliance_score_after"]
        score_pass = float(score_after) >= 90
        all_pass = struct_pass and score_pass

        # Track the best result across all attempts
        if float(score_after) > best_score:
            best_score = float(score_after)
            best_result = result.copy()

        if not score_pass and struct_pass:
            issues.append(f"Validator-adjusted compliance score is {score_after}% — must be >= 90%.")

        validation_log.append({
            "attempt": attempt,
            "valid": all_pass,
            "structural_valid": struct_pass,
            "structural_issues": len(issues),
            "score_after": score_after,
            "score_pass": score_pass,
            "issues": issues,
        })

        if all_pass:
            result["agent_metadata"] = {
                "detected_tool": detected_tool,
                "attempts": attempt,
                "validation_log": validation_log,
                "self_validated": True,
            }
            return result

        # Step 5: Self-correction — rebuild fresh messages with fix instructions
        if attempt <= max_retries:
            fix = validation.get("fix_instructions", "")
            correction_msg = f"Previous attempt failed validation. Fix these specific issues:\n"
            for i, issue in enumerate(issues, 1):
                correction_msg += f"{i}. {issue}\n"
            if fix:
                correction_msg += f"\n{fix}"
            correction_msg += f"\n\nRegenerate the complete JSON. compliance_score_after MUST be >= 90."

            # Reset messages — fresh context with fix instructions baked in
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyse this inline pipeline YAML for governance compliance. IMPORTANT — a previous generation attempt failed validation. Apply these fixes:\n\n{correction_msg}\n\nOriginal YAML:\n\n```yaml\n{inline_yaml}\n```"},
            ]

    # Exhausted retries — return BEST attempt (not last, which may be worse)
    final = best_result if best_result is not None else result
    final["agent_metadata"] = {
        "detected_tool": detected_tool,
        "attempts": attempt,
        "validation_log": validation_log,
        "self_validated": False,
        "best_score": best_score,
    }
    return final


def analyse_multiple(yaml_blocks: list) -> list:
    """
    Multi-file agentic analysis:
    1. Auto-detect tool for each YAML block
    2. Process each independently
    3. Return list of results
    """
    results = []
    for i, yaml_text in enumerate(yaml_blocks):
        if yaml_text.strip():
            result = analyse_pipeline(yaml_text)
            result["file_index"] = i + 1
            results.append(result)
    return results


if __name__ == "__main__":
    test_yaml = """\
steps:
  - task: SonarQubePrepare@7
    inputs:
      SonarQube: 'SonarQubeConnection'
      scannerMode: 'cli'
      configMode: 'manual'
      cliProjectKey: 'Website:MyRepo'
      cliProjectName: 'Website:MyRepo'
      cliSources: '.'
  - task: SonarQubeAnalyze@7
    inputs:
      jdkversion: 'JAVA_HOME_17_X64'
  - task: SonarQubePublish@7
    inputs:
      pollingTimeoutSec: '300'
  - script: |
      echo "Checking quality gate..."
"""
    print("Analysing with agentic loop...")
    result = analyse_pipeline(test_yaml)
    print(json.dumps(result, indent=2))
    if "agent_metadata" in result:
        meta = result["agent_metadata"]
        print(f"\n--- Agent Metadata ---")
        print(f"Detected tool: {meta['detected_tool']}")
        print(f"Attempts: {meta['attempts']}")
        print(f"Self-validated: {meta['self_validated']}")
        for log in meta["validation_log"]:
            print(f"  Attempt {log['attempt']}: valid={log.get('valid', 'N/A')}, issues={log.get('issues', [])}")