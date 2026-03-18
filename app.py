"""
Pipeline Governance Compliance Agent — Streamlit UI
"""

import streamlit as st
import json
from agent import analyse_pipeline, analyse_multiple

st.set_page_config(page_title="CoE Compliance Agent", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    .block-container { padding: 1.5rem 2rem 1rem 2rem; max-width: 1400px; }
    html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
    .header-banner { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); color: white; padding: 1.8rem 2rem; border-radius: 12px; margin-bottom: 1.5rem; }
    .header-banner h1 { margin: 0; font-size: 1.75rem; font-weight: 700; }
    .header-banner p { margin: 0.4rem 0 0 0; font-size: 0.92rem; color: #b0c4d8; }
    .metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.8rem; margin-bottom: 1rem; }
    .metric-card { background: linear-gradient(135deg, #fff, #f8fafc); border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem 0.8rem; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
    .metric-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .metric-value { font-size: 1.6rem; font-weight: 700; color: #1e40af; line-height: 1.2; }
    .metric-label { font-size: 0.75rem; color: #64748b; margin-top: 0.3rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em; }
    .sev-critical { background: #dc2626; color: white; padding: 3px 10px; border-radius: 6px; font-weight: 600; font-size: 0.78em; }
    .sev-high { background: #ea580c; color: white; padding: 3px 10px; border-radius: 6px; font-weight: 600; font-size: 0.78em; }
    .sev-medium { background: #d97706; color: white; padding: 3px 10px; border-radius: 6px; font-weight: 600; font-size: 0.78em; }
    .sev-low { background: #16a34a; color: white; padding: 3px 10px; border-radius: 6px; font-weight: 600; font-size: 0.78em; }
    .h-stage { background: #7c3aed; color: white; padding: 3px 12px; border-radius: 6px; font-weight: 600; }
    .h-job { background: #2563eb; color: white; padding: 3px 12px; border-radius: 6px; font-weight: 600; }
    .h-task { background: #059669; color: white; padding: 3px 12px; border-radius: 6px; font-weight: 600; }
    .h-script { background: #dc2626; color: white; padding: 3px 12px; border-radius: 6px; font-weight: 600; }
    .h-connector { text-align: center; padding: 0.3rem 0; color: #94a3b8; font-size: 0.85rem; font-weight: 500; }
    .section-head { font-size: 0.85rem; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.06em; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.4rem; margin: 1rem 0 0.8rem 0; }
    .reduction-bar-bg { background: #e2e8f0; border-radius: 8px; height: 28px; overflow: hidden; margin: 0.5rem 0; }
    .reduction-bar-fill { height: 100%; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.82rem; color: white; transition: width 0.6s ease; }
    section[data-testid="stSidebar"] { background: #0f172a; }
    section[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h3 { color: #f1f5f9 !important; }
    #MainMenu, footer, .stDeployButton { display: none !important; visibility: hidden !important; }
</style>
""", unsafe_allow_html=True)


def render_readme(content):
    if content and content.strip():
        st.markdown(content)


def display_single_result(result):
    """Display analysis results for a single pipeline."""
    tool = result.get("tool_detected", "?")
    score_before = result.get("compliance_score_before", result.get("compliance_score", 0))
    score_after = result.get("compliance_score_after", 100)
    orig = result.get("original_line_count", "?")
    comp = result.get("compliant_line_count", "?")
    reduction = result.get("reduction_percentage", 0)

    before_color = "#dc2626" if float(score_before) < 40 else "#d97706" if float(score_before) < 70 else "#16a34a"
    after_color = "#16a34a" if float(score_after) >= 90 else "#d97706"

    st.markdown(f"""<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:0.8rem;margin-bottom:1rem;">
        <div class="metric-card"><div class="metric-value">{tool}</div><div class="metric-label">Tool Detected</div></div>
        <div class="metric-card"><div class="metric-value" style="color:{before_color}">{score_before}%</div><div class="metric-label">Compliance (Before)</div></div>
        <div class="metric-card"><div class="metric-value" style="color:{after_color}">{score_after}%</div><div class="metric-label">Compliance (After)</div></div>
        <div class="metric-card"><div class="metric-value">{orig} → {comp}</div><div class="metric-label">Lines Before → After</div></div>
        <div class="metric-card"><div class="metric-value">{reduction}%</div><div class="metric-label">Config Reduction</div></div>
    </div>""", unsafe_allow_html=True)

    bar_color = "#16a34a" if float(reduction) >= 70 else "#d97706" if float(reduction) >= 40 else "#dc2626"
    st.markdown(f"""<div style="margin-bottom:1rem;"><div style="display:flex;justify-content:space-between;margin-bottom:0.2rem;"><span style="font-size:0.8rem;font-weight:600;color:#475569;">Configuration Reduction (DS-01)</span><span style="font-size:0.8rem;font-weight:700;color:{bar_color};">{reduction}%</span></div><div class="reduction-bar-bg"><div class="reduction-bar-fill" style="width:{min(float(reduction),100)}%;background:{bar_color};">{reduction}%</div></div></div>""", unsafe_allow_html=True)

    tab_v, tab_c, tab_h, tab_r, tab_a, tab_j = st.tabs(["🚨 Violations", "✅ Consuming Pipeline", "📦 Template Hierarchy", "📖 READMEs", "🤖 Agent Trace", "🔧 Raw JSON"])

    with tab_v:
        violations = result.get("violations", [])
        st.markdown(f"**{len(violations)} violation(s) identified**")
        for v in violations:
            sev = v.get("severity", "MEDIUM").upper()
            with st.expander(f"{v.get('rule','')} — {v.get('description','')[:80]}"):
                st.markdown(f"<span class='sev-{sev.lower()}'>{sev}</span>", unsafe_allow_html=True)
                st.markdown(f"**Description:** {v.get('description','')}")
                st.markdown(f"**Evidence:** `{v.get('evidence','')}`")
                st.markdown(f"**Remediation:** {v.get('remediation','')}")

    with tab_c:
        st.markdown("**Layer 1 — Consuming Pipeline** (paste into app repo)")
        st.code(result.get("compliant_yaml", ""), language="yaml")

    with tab_h:
        tfiles = result.get("template_files", [])
        stages = [f for f in tfiles if f.get("hierarchy_level") == "stage"]
        jobs = [f for f in tfiles if f.get("hierarchy_level") == "job"]
        tasks = [f for f in tfiles if f.get("hierarchy_level") == "task"]
        scripts = [f for f in tfiles if f.get("hierarchy_level") == "script"]
        st.markdown(f"**{len(tfiles)} files generated**")

        if stages:
            st.markdown("<div class='section-head'><span class='h-stage'>STAGE</span> Layer 2</div>", unsafe_allow_html=True)
            for f in stages:
                with st.expander(f"📄 {f['filename']}"):
                    st.caption(f"{f.get('description','')} → calls `{f.get('calls','')}`")
                    st.code(f.get("content", ""), language="yaml")
        if jobs:
            st.markdown("<div class='h-connector'>↓ Stage calls Job</div>", unsafe_allow_html=True)
            st.markdown("<div class='section-head'><span class='h-job'>JOB</span> Layer 3</div>", unsafe_allow_html=True)
            for f in jobs:
                with st.expander(f"📄 {f['filename']}"):
                    st.caption(f"{f.get('description','')} → calls `{f.get('calls','')}`")
                    st.code(f.get("content", ""), language="yaml")
        if tasks:
            st.markdown("<div class='h-connector'>↓ Job calls Task</div>", unsafe_allow_html=True)
            st.markdown("<div class='section-head'><span class='h-task'>TASK</span> Layer 4</div>", unsafe_allow_html=True)
            for f in tasks:
                with st.expander(f"📄 {f['filename']}"):
                    st.caption(f"{f.get('description','')} → calls `{f.get('calls','')}`")
                    st.code(f.get("content", ""), language="yaml")
        if scripts:
            st.markdown("<div class='h-connector'>↓ Task calls Scripts via <code>- bash:</code></div>", unsafe_allow_html=True)
            st.markdown("<div class='section-head'><span class='h-script'>SCRIPT</span> Layer 5</div>", unsafe_allow_html=True)
            for f in scripts:
                with st.expander(f"📜 {f['filename']}"):
                    st.caption(f.get("description", ""))
                    st.code(f.get("content", ""), language="bash")

    with tab_r:
        rfiles = result.get("readme_files", [])
        if rfiles:
            st.markdown(f"**{len(rfiles)} README(s)**")
            for rf in rfiles:
                with st.expander(f"📖 {rf['filename']}"):
                    st.caption(f"Template: `{rf.get('template_ref','')}`")
                    render_readme(rf.get("content", ""))
        else:
            st.info("No READMEs generated.")

    with tab_a:
        meta = result.get("agent_metadata", {})
        if meta:
            st.markdown("**Agentic Execution Trace**")
            a1, a2, a3 = st.columns(3)
            with a1:
                st.markdown(f"**Tool Detected**")
                st.markdown(f"`{meta.get('detected_tool', 'N/A')}`")
            with a2:
                st.markdown(f"**Attempts**")
                st.markdown(f"`{meta.get('attempts', 'N/A')}`")
            with a3:
                validated = meta.get("self_validated", False)
                st.markdown(f"**Self-Validated**")
                st.markdown("✅ Passed" if validated else "⚠️ Best Effort")

            st.markdown("**Validation Loop**")
            for log_entry in meta.get("validation_log", []):
                attempt_num = log_entry.get("attempt", "?")
                is_valid = log_entry.get("valid", None)
                issues = log_entry.get("issues", [])
                score_after = log_entry.get("score_after", "?")
                struct_issues = log_entry.get("structural_issues", len(issues))

                if is_valid is True:
                    st.success(f"Attempt {attempt_num}: ✅ Passed — compliance: {score_after}%, 0 issues")
                elif is_valid is False:
                    label = f"Attempt {attempt_num}: ❌ Failed — compliance: {score_after}%, {struct_issues} issue(s)"
                    if attempt_num < meta.get("attempts", 99):
                        label += " → agent self-corrected"
                    with st.expander(label):
                        for issue in issues:
                            st.markdown(f"- {issue}")
                else:
                    st.warning(f"Attempt {attempt_num}: {log_entry.get('error', 'Parse error')} → agent retried")

            st.markdown("---")
            st.markdown("**Agent Decision Flow**")
            flow = f"1. Tool Detection → {meta.get('detected_tool', '?')}\n"
            flow += f"2. Generate compliant hierarchy\n"
            flow += f"3. Self-validate (structure + compliance score ≥ 90%)\n"
            if meta.get("self_validated"):
                flow += f"4. Validation passed in {meta.get('attempts', '?')} attempt(s) → output delivered"
            else:
                flow += f"4. Retried {meta.get('attempts', '?')} times → best-effort output delivered"
            st.code(flow, language=None)
        else:
            st.info("No agent metadata available.")

    with tab_j:
        st.json(result)

    st.markdown("---")
    st.markdown("**Executive Summary**")
    st.info(result.get("summary", ""))


# ---- Sidebar ----
with st.sidebar:
    st.markdown("### 🛡️ CoE Compliance Agent")
    st.caption("Pipeline Governance PoC")
    st.caption("CSC3101 Capstone — Jiang Weimin")
    st.markdown("---")
    st.markdown("##### About")
    st.markdown("AI agent that reads inline Azure DevOps pipeline YAML, identifies governance violations, and generates the full 5-layer template hierarchy with documentation.")
    st.markdown("---")
    st.markdown("##### Load Example")
    example_choice = st.selectbox("Demo:", ["— Select —", "Mend SCA (104 lines)", "SonarQube CLI (20 lines)", "Mend SAST (148 lines)", "Container Scanning (175 lines)", "Multi-Tool (3 files)"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("##### Analysis Mode")
    auto_multi = (example_choice == "Multi-Tool (3 files)")
    multi_mode = st.toggle("Multi-file analysis", value=auto_multi, help="Paste multiple YAML blocks separated by '---'")
    st.markdown("---")
    st.markdown("##### Template Hierarchy")
    st.code("L1  Consuming Pipeline\n └─ L2  Stage\n     └─ L3  Job\n         └─ L4  Orchestrator Task\n             └─ L5  Scripts (.sh)", language=None)

# ---- Examples ----
EXAMPLES = {
    "Mend SCA (104 lines)": "# Mend SCA Inline Configuration (BEFORE CoE migration)\ntrigger:\n  branches:\n    include:\n      - main\n      - develop\n\npool:\n  name: 'BuildAgentPool'\n\nvariables:\n  WS_APIKEY: 'hardcoded-api-key-12345'\n  WS_USERKEY: 'hardcoded-user-key-67890'\n  WS_PRODUCTNAME: 'Website'\n  WS_PROJECTNAME: $(Build.Repository.Name)\n  WS_WSS_URL: 'https://saas.mend.io/agent'\n\nsteps:\n  - script: |\n      echo \"Downloading WhiteSource Unified Agent...\"\n      curl -LJO https://unified-agent.s3.amazonaws.com/wss-unified-agent.jar\n    displayName: 'Download WhiteSource Unified Agent'\n\n  - script: |\n      echo \"Configuring WhiteSource scan...\"\n      cat > wss-unified-agent.config << 'EOF'\n      apiKey=$(WS_APIKEY)\n      userKey=$(WS_USERKEY)\n      productName=$(WS_PRODUCTNAME)\n      projectName=$(WS_PROJECTNAME)\n      wss.url=$(WS_WSS_URL)\n      includes=**/*.jar,**/*.tgz,**/*.whl\n      excludes=**/node_modules/**,**/test/**\n      resolveAllDependencies=false\n      npm.resolveLockFile=true\n      npm.includeDevDependencies=false\n      maven.resolveDependencies=true\n      gradle.resolveDependencies=true\n      python.resolveDependencies=true\n      python.pipPath=pip3\n      log.level=info\n      forceCheckAllDependencies=false\n      offline=false\n      generateProjectDetailsJson=true\n      generateScanReport=true\n      scanReportFilenameFormat=\n      scanReportTimeoutMinutes=10\n      EOF\n    displayName: 'Configure WhiteSource'\n\n  - script: |\n      echo \"Running WhiteSource scan...\"\n      java -jar wss-unified-agent.jar \\\n        -c wss-unified-agent.config \\\n        -apiKey $(WS_APIKEY) \\\n        -userKey $(WS_USERKEY) \\\n        -project $(WS_PROJECTNAME) \\\n        -product $(WS_PRODUCTNAME) \\\n        -d .\n    displayName: 'Run WhiteSource Scan'\n    env:\n      WS_APIKEY: $(WS_APIKEY)\n      WS_USERKEY: $(WS_USERKEY)\n    continueOnError: true\n\n  - script: |\n      if [ -f \"whitesource/scan_report.json\" ]; then\n        cat whitesource/scan_report.json | python3 -c \"\n        import json, sys\n        data = json.load(sys.stdin)\n        vulns = data.get('vulnerabilities', [])\n        critical = sum(1 for v in vulns if v.get('severity') == 'CRITICAL')\n        if critical > 0: sys.exit(1)\n        \"\n      fi\n    displayName: 'Parse Scan Results'\n\n  - script: |\n      mkdir -p $(Build.ArtifactStagingDirectory)/whitesource\n      cp -r whitesource/* $(Build.ArtifactStagingDirectory)/whitesource/ 2>/dev/null || true\n    displayName: 'Stage Artifacts'\n\n  - task: PublishBuildArtifacts@1\n    inputs:\n      pathtoPublish: '$(Build.ArtifactStagingDirectory)/whitesource'\n      artifactName: 'WhiteSourceReport'\n    condition: always()\n\n  - script: |\n      POLICY_STATUS=$(cat whitesource/policy_check.json 2>/dev/null | python3 -c \"\n      import json, sys\n      try:\n          data = json.load(sys.stdin)\n          print(len(data.get('policyViolations', [])))\n      except: print(0)\n      \" 2>/dev/null || echo \"0\")\n      if [ \\\"$POLICY_STATUS\\\" -gt 0 ]; then\n        echo \\\"##vso[task.logissue type=error]Policy violations: $POLICY_STATUS\\\"\n        exit 1\n      fi\n    displayName: 'Enforce Policy Check'",
    "SonarQube CLI (20 lines)": "# SonarQube CLI Inline Configuration\nsteps:\n  - task: SonarQubePrepare@7\n    inputs:\n      SonarQube: 'SonarQubeConnection'\n      scannerMode: 'cli'\n      configMode: 'manual'\n      cliProjectKey: 'Website:MyRepo'\n      cliProjectName: 'Website:MyRepo'\n      cliSources: '.'\n      extraProperties: |\n        sonar.exclusions=**/node_modules/**\n        sonar.coverage.exclusions=**/*.test.js\n  - task: SonarQubeAnalyze@7\n    inputs:\n      jdkversion: 'JAVA_HOME_17_X64'\n  - task: SonarQubePublish@7\n    inputs:\n      pollingTimeoutSec: '300'\n  - script: |\n      echo \"Checking quality gate...\"\n    displayName: 'Check Quality Gate'",
    "Mend SAST (148 lines)": "# Mend SAST Inline Configuration\ntrigger:\n  branches:\n    include:\n      - main\n\npool:\n  name: 'BuildAgentPool'\n\nvariables:\n  MEND_URL: 'https://sast.mend.io'\n  MEND_API_KEY: 'hardcoded-key-12345'\n  MEND_USER_KEY: 'hardcoded-key-67890'\n  MEND_EMAIL: 'dev-team@example.com'\n  FAIL_ON_CRITICAL: 'true'\n  FAIL_ON_HIGH: 'false'\n\nsteps:\n  - script: |\n      curl -sL https://downloads.mend.io/cli/linux_amd64/mend -o /usr/local/bin/mend\n      chmod +x /usr/local/bin/mend\n    displayName: 'Install Mend CLI'\n\n  - script: |\n      export MEND_URL=$(MEND_URL)\n      export MEND_EMAIL=$(MEND_EMAIL)\n      export MEND_USER_KEY=$(MEND_USER_KEY)\n      mend sast --non-interactive --formats \"json,html\" --report-dir \"$(Build.ArtifactStagingDirectory)/mend-sast\" --scope \"$(Build.Repository.Name)\" .\n    displayName: 'Run Mend SAST Scan'\n    env:\n      MEND_URL: $(MEND_URL)\n      MEND_EMAIL: $(MEND_EMAIL)\n      MEND_USER_KEY: $(MEND_USER_KEY)\n      MEND_API_KEY: $(MEND_API_KEY)\n    continueOnError: true\n\n  - task: PublishBuildArtifacts@1\n    inputs:\n      pathtoPublish: '$(Build.ArtifactStagingDirectory)/mend-sast'\n      artifactName: 'MendSASTReport'\n    condition: always()\n\n  - script: |\n      SHOULD_FAIL=0\n      if [ \"$(FAIL_ON_CRITICAL)\" = \"true\" ] && [ \"$(SAST_CRITICAL)\" -gt 0 ]; then SHOULD_FAIL=1; fi\n      if [ \"$SHOULD_FAIL\" -eq 1 ]; then exit 1; fi\n    displayName: 'Enforce SAST Policy'",
    "Container Scanning (175 lines)": "# Container Scanning Inline\ntrigger:\n  branches:\n    include:\n      - main\n\npool:\n  name: 'BuildAgentPool'\n\nvariables:\n  DOCKER_REGISTRY: 'myregistry.azurecr.io'\n  IMAGE_NAME: 'myapp'\n  IMAGE_TAG: '$(Build.BuildId)'\n  MEND_URL: 'https://saas.mend.io'\n  MEND_API_KEY: 'hardcoded-key-12345'\n  MEND_USER_KEY: 'hardcoded-key-67890'\n  MEND_EMAIL: 'dev-team@example.com'\n  FAIL_ON_CRITICAL: 'true'\n  FAIL_ON_HIGH: 'false'\n\nsteps:\n  - script: |\n      docker build -t $(DOCKER_REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG) -f ./Dockerfile .\n    displayName: 'Build Docker Image'\n\n  - script: |\n      docker save $(DOCKER_REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG) -o image.tar\n    displayName: 'Export Image to Tar'\n\n  - script: |\n      curl -sL https://downloads.mend.io/cli/linux_amd64/mend -o /usr/local/bin/mend\n      chmod +x /usr/local/bin/mend\n    displayName: 'Install Mend CLI'\n\n  - script: |\n      export MEND_URL=$(MEND_URL)\n      mend image $(DOCKER_REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG) --non-interactive --formats \"json,sarif,spdx-json,cyclonedx-json\" --report-dir \"$(Build.ArtifactStagingDirectory)/container-scan\" --filename image.tar\n    displayName: 'Run Mend Container Scan'\n    env:\n      MEND_URL: $(MEND_URL)\n      MEND_EMAIL: $(MEND_EMAIL)\n      MEND_USER_KEY: $(MEND_USER_KEY)\n      MEND_API_KEY: $(MEND_API_KEY)\n    continueOnError: true\n\n  - task: PublishBuildArtifacts@1\n    inputs:\n      pathtoPublish: '$(Build.ArtifactStagingDirectory)/container-scan'\n      artifactName: 'ContainerScanReport'\n    condition: always()\n\n  - script: |\n      SHOULD_FAIL=0\n      if [ \"$(FAIL_ON_CRITICAL)\" = \"true\" ] && [ \"$(CONTAINER_CRITICAL)\" -gt 0 ]; then SHOULD_FAIL=1; fi\n      if [ \"$SHOULD_FAIL\" -eq 1 ]; then exit 1; fi\n    displayName: 'Enforce Container Policy'\n\n  - script: |\n      docker login $(DOCKER_REGISTRY) -u $(ACR_USERNAME) -p $(ACR_PASSWORD)\n      docker push $(DOCKER_REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)\n    displayName: 'Push to Registry'\n    env:\n      ACR_USERNAME: $(ACR_USERNAME)\n      ACR_PASSWORD: $(ACR_PASSWORD)\n    condition: succeeded()",
    "Multi-Tool (3 files)": "# File 1: SonarQube inline\nsteps:\n  - task: SonarQubePrepare@7\n    inputs:\n      SonarQube: 'SonarQubeConnection'\n      scannerMode: 'cli'\n      configMode: 'manual'\n      cliProjectKey: 'Website:MyRepo'\n      cliProjectName: 'Website:MyRepo'\n      cliSources: '.'\n      extraProperties: |\n        sonar.exclusions=**/node_modules/**\n  - task: SonarQubeAnalyze@7\n    inputs:\n      jdkversion: 'JAVA_HOME_17_X64'\n  - task: SonarQubePublish@7\n    inputs:\n      pollingTimeoutSec: '300'\n---\n# File 2: Mend SAST inline\nvariables:\n  MEND_URL: 'https://sast.mend.io'\n  MEND_API_KEY: 'hardcoded-sast-key-12345'\n  MEND_USER_KEY: 'hardcoded-sast-user-67890'\n  MEND_EMAIL: 'dev-team@example.com'\n\nsteps:\n  - script: |\n      curl -sL https://downloads.mend.io/cli/linux_amd64/mend -o /usr/local/bin/mend\n      chmod +x /usr/local/bin/mend\n    displayName: 'Install Mend CLI'\n\n  - script: |\n      export MEND_URL=$(MEND_URL)\n      export MEND_EMAIL=$(MEND_EMAIL)\n      export MEND_USER_KEY=$(MEND_USER_KEY)\n      mend sast --non-interactive --formats \"json,html\" --report-dir \"$(Build.ArtifactStagingDirectory)/mend-sast\" --scope \"$(Build.Repository.Name)\" .\n    displayName: 'Run Mend SAST'\n    env:\n      MEND_API_KEY: $(MEND_API_KEY)\n    continueOnError: true\n\n  - script: |\n      if [ \"$(SAST_CRITICAL)\" -gt 0 ]; then exit 1; fi\n    displayName: 'Enforce SAST Policy'\n---\n# File 3: Container scanning inline\nvariables:\n  DOCKER_REGISTRY: 'myregistry.azurecr.io'\n  IMAGE_NAME: 'myapp'\n  MEND_API_KEY: 'hardcoded-container-key-abc'\n\nsteps:\n  - script: |\n      docker build -t $(DOCKER_REGISTRY)/$(IMAGE_NAME):$(Build.BuildId) .\n    displayName: 'Build Docker Image'\n\n  - script: |\n      docker save $(DOCKER_REGISTRY)/$(IMAGE_NAME):$(Build.BuildId) -o image.tar\n    displayName: 'Export to Tar'\n\n  - script: |\n      mend image $(DOCKER_REGISTRY)/$(IMAGE_NAME):$(Build.BuildId) --non-interactive --formats \"json,sarif,spdx-json,cyclonedx-json\" --filename image.tar\n    displayName: 'Mend Container Scan'\n    continueOnError: true\n\n  - script: |\n      docker login $(DOCKER_REGISTRY) -u $(ACR_USERNAME) -p $(ACR_PASSWORD)\n      docker push $(DOCKER_REGISTRY)/$(IMAGE_NAME):$(Build.BuildId)\n    displayName: 'Push to Registry'\n    condition: succeeded()",
}

# ---- Header ----
st.markdown("""<div class="header-banner"><h1>🛡️ Pipeline Governance Compliance Agent</h1><p>Analyse inline Azure DevOps YAML against CoE governance rules • Generate full 5-layer template hierarchy • Auto-produce documentation</p></div>""", unsafe_allow_html=True)

default_yaml = EXAMPLES.get(example_choice, "") if example_choice and example_choice != "— Select —" else ""

col_in, col_out = st.columns([5, 7], gap="large")

with col_in:
    st.markdown('<div class="section-head">INPUT — INLINE PIPELINE YAML</div>', unsafe_allow_html=True)
    if multi_mode:
        st.caption("Paste multiple YAML blocks separated by `---`")
    input_yaml = st.text_area("yaml", value=default_yaml, height=520, label_visibility="collapsed", placeholder="Paste inline Azure DevOps YAML...")
    btn = st.button("🔍  Analyse & Generate Hierarchy", type="primary", use_container_width=True)

with col_out:
    st.markdown('<div class="section-head">ANALYSIS RESULTS</div>', unsafe_allow_html=True)

    if btn and input_yaml.strip():
        if multi_mode:
            yaml_blocks = [b.strip() for b in input_yaml.split("---") if b.strip()]
            st.markdown(f"**Multi-file mode: {len(yaml_blocks)} YAML block(s) detected**")
            with st.spinner(f"🤖 Agent processing {len(yaml_blocks)} files: detecting → generating → validating..."):
                results = analyse_multiple(yaml_blocks)
            for r in results:
                idx = r.get("file_index", "?")
                meta = r.get("agent_metadata", {})
                tool_name = meta.get("detected_tool", r.get("tool_detected", "Unknown"))
                with st.expander(f"📄 File {idx}: {tool_name}", expanded=(idx == 1)):
                    if "error" in r:
                        st.error(r["error"])
                    else:
                        display_single_result(r)
        else:
            with st.spinner("🤖 Agent running: detecting tool → generating hierarchy → self-validating → correcting if needed..."):
                result = analyse_pipeline(input_yaml)

            if "error" in result:
                st.error(f"Agent error: {result['error']}")
                with st.expander("Raw response"):
                    st.code(result.get("raw_response", ""), language="text")
            else:
                display_single_result(result)

    elif btn:
        st.warning("Paste some YAML first.")
    else:
        st.markdown("*Select an example or paste YAML, then click **Analyse & Generate Hierarchy**.*")