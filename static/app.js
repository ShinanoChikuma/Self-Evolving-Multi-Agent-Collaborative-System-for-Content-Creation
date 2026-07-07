const inspirationSeed = [
  {
    badge: "角色文案",
    title: "冷面新角色登场",
    description: "写一段冷感角色登场文案，适合短视频改成微博首发短帖，带一点宿命感。",
    payload: {
      content_type: "角色设定",
      user_prompt: "写一个冷面感角色登场文案，适合短视频与微博首发，要求有镜头感和人物弧光。",
      tone: "冷感克制",
      audience: "二次元与剧情向用户",
      length_hint: "中等",
      extra_requirements: "避免模板化的霸总语气，突出角色的缺口与矛盾。",
    },
  },
  {
    badge: "世界观企划",
    title: "潮汐钟城市场景",
    description: "写一段被潮汐钟控制的城市设定，带一点阴谋感，并给出三个可延展剧情钩子。",
    payload: {
      content_type: "公众号文章",
      user_prompt: "写一段被潮汐钟控制的城市设定，要求有世界观辨识度，并给出后续剧情钩子。",
      tone: "神秘锋利",
      audience: "设定党与剧情创作者",
      length_hint: "详细",
      extra_requirements: "先写设定，再给出三个冲突点。",
    },
  },
  {
    badge: "你的创作",
    title: "发布节奏三连",
    description: "给我一组预热、上线当天、反馈转发的微博文案，要求每条都有辨识度。",
    payload: {
      content_type: "产品文案",
      user_prompt: "给我一组预热、上线当天、反馈转发的三连微博文案，要求每条都不一样。",
      tone: "自然有劲",
      audience: "独立创作者粉丝团",
      length_hint: "中等",
      extra_requirements: "避免像 AI 总结，要像真的人在运营。",
    },
  },
  {
    badge: "去 AI 味",
    title: "把文案写得更像真人",
    description: "请把一段角色文案改得更像真人写作，句子更短，更有停顿和节奏。",
    payload: {
      content_type: "产品文案",
      user_prompt: "请把一段角色文案改得更像真人写作，句子更短，更有停顿和节奏。",
      tone: "克制真人感",
      audience: "社媒平台读者",
      length_hint: "中等",
      extra_requirements: "避免空泛修饰词，优先处理节奏和句式。",
    },
  },
];

const fallbackModels = {
  items: [
    { id: "deepseek-v4-flash", owned_by: "deepseek" },
    { id: "deepseek-v4-pro", owned_by: "deepseek" },
  ],
  recommended: { fast: "deepseek-v4-flash", expert: "deepseek-v4-pro" },
  availability: { fast: true, expert: true },
};

const state = {
  currentView: "create",
  currentRunId: null,
  selectedHistoryId: null,
  loading: false,
  iterating: false,
  nearBottom: true,
  toolsOpen: false,
  sidebarCollapsed: false,
  mobileSidebarOpen: false,
  settingsOpen: false,
  deleteModalOpen: false,
  historyMenuId: null,
  pendingDeleteRunId: null,
  pendingDeleteTitle: "",
  isComposing: false,
  statusText: "等待输入",
  currentPrompt: "",
  finalContent: "",
  steps: [],
  feedbackComment: "",
  feedbackRating: "",
  historyItems: [],
  modelCatalog: fallbackModels,
  // ── 新增 ──
  templates: [],
  selectedTemplateId: "",
  modificationInput: "",
  iterationChain: [],       //  [{run_id, iteration_round, preview}]
  evolutionLogCount: 0,
  evolutionFeedbackCount: 0,
  evolutionResult: "",
  memoryData: null,
  evolutionAnalysis: "",
  templateModalOpen: false,
  editingTemplateId: "",
  form: {
    contentType: "短视频脚本",
    audience: "",
    tone: "",
    lengthHint: "中等",
    extraRequirements: "",
  },
  settings: {
    mode: window.localStorage.getItem("ecroom_mode") === "expert" ? "expert" : "fast",
  },
};

const dom = {
  body: document.body,
  sidebar: document.getElementById("sidebar"),
  historyList: document.getElementById("historyList"),
  newChatButton: document.getElementById("newChatButton"),
  collapseSidebarButton: document.getElementById("collapseSidebarButton"),
  mobileSidebarButton: document.getElementById("mobileSidebarButton"),
  mobileSidebarOverlay: document.getElementById("mobileSidebarOverlay"),
  navButtons: [...document.querySelectorAll(".sidebar-nav-button")],
  mainTitle: document.getElementById("mainTitle"),
  toggleToolsButton: document.getElementById("toggleToolsButton"),
  closeToolsButton: document.getElementById("closeToolsButton"),
  composerTools: document.getElementById("composerTools"),
  contentType: document.getElementById("contentType"),
  audience: document.getElementById("audience"),
  tone: document.getElementById("tone"),
  lengthHint: document.getElementById("lengthHint"),
  extraRequirements: document.getElementById("extraRequirements"),
  templateGrid: document.getElementById("templateGrid"),
  selectedTemplateLabel: document.getElementById("selectedTemplateLabel"),
  chatScrollRegion: document.getElementById("chatScrollRegion"),
  chatThread: document.getElementById("chatThread"),
  composerForm: document.getElementById("composerForm"),
  composerInput: document.getElementById("composerInput"),
  sendButton: document.getElementById("sendButton"),
  statusText: document.getElementById("statusText"),
  quickInspirationButton: document.getElementById("quickInspirationButton"),
  quickAssetsButton: document.getElementById("quickAssetsButton"),
  settingsButton: document.getElementById("settingsButton"),
  accountButton: document.getElementById("accountButton"),
  settingsModal: document.getElementById("settingsModal"),
  settingsBackdrop: document.getElementById("settingsBackdrop"),
  closeSettingsButton: document.getElementById("closeSettingsButton"),
  fastModeButton: document.getElementById("fastModeButton"),
  expertModeButton: document.getElementById("expertModeButton"),
  currentModeLabel: document.getElementById("currentModeLabel"),
  currentModelLabel: document.getElementById("currentModelLabel"),
  modelStatusLabel: document.getElementById("modelStatusLabel"),
  modelList: document.getElementById("modelList"),
  modelError: document.getElementById("modelError"),
  deleteModal: document.getElementById("deleteModal"),
  deleteBackdrop: document.getElementById("deleteBackdrop"),
  deleteMessage: document.getElementById("deleteMessage"),
  closeDeleteButton: document.getElementById("closeDeleteButton"),
  cancelDeleteButton: document.getElementById("cancelDeleteButton"),
  confirmDeleteButton: document.getElementById("confirmDeleteButton"),
  // ── 新增 ──
  triggerEvolutionButton: document.getElementById("triggerEvolutionButton"),
  evolutionFeedbackCount: document.getElementById("evolutionFeedbackCount"),
  evolutionLogCount: document.getElementById("evolutionLogCount"),
  evolutionResult: document.getElementById("evolutionResult"),
  evolutionApplyRow: document.getElementById("evolutionApplyRow"),
  applyEvolutionButton: document.getElementById("applyEvolutionButton"),
  resetPromptsButton: document.getElementById("resetPromptsButton"),
  templateManageList: document.getElementById("templateManageList"),
  addTemplateButton: document.getElementById("addTemplateButton"),
  templateModal: document.getElementById("templateModal"),
  templateBackdrop: document.getElementById("templateBackdrop"),
  closeTemplateModalButton: document.getElementById("closeTemplateModalButton"),
  saveTemplateButton: document.getElementById("saveTemplateButton"),
  cancelTemplateButton: document.getElementById("cancelTemplateButton"),
  templateDeleteButton: document.getElementById("templateDeleteButton"),
};

function init() {
  hydrateForm();
  bindEvents();
  render();
  loadHistory().catch((error) => { setStatus(`初始化失败：${error.message}`); });
  loadModelCatalog().catch(() => {});
  loadTemplates().catch(() => {});
  loadEvolutionInfo().catch(() => {});
  loadMemory().catch(() => {});
}

function bindEvents() {
  dom.newChatButton.addEventListener("click", resetConversation);
  dom.collapseSidebarButton.addEventListener("click", toggleSidebarCollapse);
  dom.mobileSidebarButton.addEventListener("click", toggleMobileSidebar);
  dom.mobileSidebarOverlay.addEventListener("click", closeMobileSidebar);
  dom.toggleToolsButton.addEventListener("click", openTools);
  dom.closeToolsButton.addEventListener("click", closeTools);
  dom.quickInspirationButton.addEventListener("click", () => setView("inspiration"));
  dom.quickAssetsButton.addEventListener("click", () => setView("assets"));
  dom.settingsButton.addEventListener("click", openSettings);
  dom.accountButton.addEventListener("click", () => setStatus("当前版本尚未接入账号系统"));
  dom.settingsBackdrop.addEventListener("click", closeSettings);
  dom.closeSettingsButton.addEventListener("click", closeSettings);
  dom.fastModeButton.addEventListener("click", () => setMode("fast"));
  dom.expertModeButton.addEventListener("click", () => setMode("expert"));
  dom.deleteBackdrop.addEventListener("click", closeDeleteModal);
  dom.closeDeleteButton.addEventListener("click", closeDeleteModal);
  dom.cancelDeleteButton.addEventListener("click", closeDeleteModal);
  dom.confirmDeleteButton.addEventListener("click", confirmDeleteRun);
  dom.triggerEvolutionButton.addEventListener("click", triggerEvolution);
  dom.applyEvolutionButton.addEventListener("click", applyEvolution);
  dom.resetPromptsButton.addEventListener("click", resetPrompts);
  dom.addTemplateButton.addEventListener("click", () => openTemplateModal());
  dom.templateBackdrop.addEventListener("click", closeTemplateModal);
  dom.closeTemplateModalButton.addEventListener("click", closeTemplateModal);
  dom.cancelTemplateButton.addEventListener("click", closeTemplateModal);
  dom.saveTemplateButton.addEventListener("click", saveTemplate);
  dom.templateDeleteButton.addEventListener("click", deleteTemplate);

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    if (state.deleteModalOpen) { closeDeleteModal(); return; }
    if (state.settingsOpen) { closeSettings(); return; }
    if (state.toolsOpen) { closeTools(); return; }
    if (state.mobileSidebarOpen) { closeMobileSidebar(); return; }
    if (state.historyMenuId) { state.historyMenuId = null; renderHistory(state.historyItems); }
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest(".history-actions") && state.historyMenuId) {
      state.historyMenuId = null;
      renderHistory(state.historyItems);
    }
  });

  dom.navButtons.forEach((button) => {
    button.addEventListener("click", () => {
      setView(button.dataset.view);
      closeMobileSidebar();
    });
  });

  dom.chatScrollRegion.parentElement.addEventListener("scroll", onThreadScroll);
  dom.composerForm.addEventListener("submit", (event) => {
    event.preventDefault();
    createContent();
  });
  dom.composerInput.addEventListener("input", onComposerInput);
  dom.composerInput.addEventListener("keydown", onComposerKeydown);
  dom.composerInput.addEventListener("compositionstart", () => { state.isComposing = true; });
  dom.composerInput.addEventListener("compositionend", () => { state.isComposing = false; });

  dom.contentType.addEventListener("change", syncFormFromInputs);
  dom.audience.addEventListener("input", syncFormFromInputs);
  dom.tone.addEventListener("input", syncFormFromInputs);
  dom.lengthHint.addEventListener("change", syncFormFromInputs);
  dom.extraRequirements.addEventListener("input", syncFormFromInputs);

  dom.historyList.addEventListener("click", onHistoryClick);
  dom.chatThread.addEventListener("click", onThreadClick);
  dom.chatThread.addEventListener("input", onThreadInput);
}

// ── API ──────────────────────────────────────────────────

async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    ...options,
  });
  const raw = await response.text();
  let data;
  try { data = raw ? JSON.parse(raw) : {}; } catch {
    const snippet = raw.slice(0, 120).replace(/\s+/g, " ").trim();
    throw new Error(`接口返回了非 JSON 响应：${snippet || "empty response"}`);
  }
  if (!response.ok) throw new Error(data.error || "请求失败");
  return data;
}

async function loadHistory() {
  const data = await api("/api/history");
  state.historyItems = data.items || [];
  renderHistory(state.historyItems);
}

async function loadModelCatalog() {
  try {
    const data = await api("/api/models");
    const items = Array.isArray(data.items) ? data.items : [];
    state.modelCatalog = {
      items: items.length ? items : fallbackModels.items,
      recommended: data.recommended || fallbackModels.recommended,
      availability: data.availability || fallbackModels.availability,
      error: data.error || "",
    };
  } catch {
    state.modelCatalog = { ...fallbackModels, error: "" };
  }
  renderSettings();
}

// ── Templates ────────────────────────────────────────────

async function loadTemplates() {
  try {
    const data = await api("/api/templates");
    state.templates = data.items || [];
    renderTemplateGrid();
  } catch { /* silent */ }
}

function renderTemplateGrid() {
  if (!dom.templateGrid) return;
  if (!state.templates.length) {
    dom.templateGrid.innerHTML = '<div class="empty-history">暂无模板，可在设置中管理。</div>';
    return;
  }
  dom.templateGrid.innerHTML = state.templates.map((tpl) => {
    const selected = state.selectedTemplateId === tpl.id;
    return `
      <button class="template-mini-card ${selected ? "is-selected" : ""}"
              type="button" data-template-id="${escapeHtml(tpl.id)}">
        <div class="template-mini-card-title">${escapeHtml(tpl.name)}</div>
        <div class="template-mini-card-type">${escapeHtml(tpl.content_type)}</div>
      </button>
    `;
  }).join("");

  dom.selectedTemplateLabel.textContent = state.selectedTemplateId
    ? (state.templates.find(t => t.id === state.selectedTemplateId)?.name || "已选择")
    : "未选择模板";
}

function selectTemplate(templateId) {
  if (state.selectedTemplateId === templateId) {
    state.selectedTemplateId = "";
  } else {
    state.selectedTemplateId = templateId;
    // 自动填充表单
    const tpl = state.templates.find(t => t.id === templateId);
    if (tpl) {
      state.form.contentType = tpl.content_type || state.form.contentType;
      if (tpl.default_tone) state.form.tone = tpl.default_tone;
      if (tpl.default_audience) state.form.audience = tpl.default_audience;
      if (tpl.default_length) state.form.lengthHint = tpl.default_length;
      hydrateForm();
    }
  }
  renderTemplateGrid();
}

// ── Evolution ────────────────────────────────────────────

async function loadEvolutionInfo() {
  try {
    const data = await api("/api/evolution");
    state.evolutionLogCount = (data.items || []).length;
    // Count feedback
    try {
      const histData = await api("/api/history");
      state.evolutionFeedbackCount = (histData.items || []).length;
    } catch { /* silent */ }
    renderSettings();
  } catch { /* silent */ }
}

async function triggerEvolution() {
  dom.triggerEvolutionButton.disabled = true;
  dom.triggerEvolutionButton.textContent = "分析中...";
  dom.triggerEvolutionButton.classList.add("button-loading");
  dom.evolutionResult.classList.add("is-hidden");

  try {
    const data = await api("/api/evolution/trigger", { method: "POST" });
    if (data.status === "skipped") {
      state.evolutionResult = data.reason || "数据不足，无法触发进化。";
    } else {
      state.evolutionResult = data.analysis || "进化分析完成。";
      state.evolutionLogCount = (state.evolutionLogCount || 0) + 1;
    }
    state.evolutionFeedbackCount = data.feedback_count || state.evolutionFeedbackCount;
    renderSettings();
  } catch (error) {
    state.evolutionResult = `进化分析失败：${error.message}`;
    renderSettings();
  } finally {
    dom.triggerEvolutionButton.disabled = false;
    dom.triggerEvolutionButton.textContent = "触发自进化分析";
    dom.triggerEvolutionButton.classList.remove("button-loading");
  }
}

async function applyEvolution() {
  if (!state.evolutionResult || state.evolutionResult.includes("数据不足")) return;
  dom.applyEvolutionButton.disabled = true;
  dom.applyEvolutionButton.textContent = "应用中...";

  try {
    // Parse the evolution analysis to extract prompt suggestions
    // The LLM output has sections like "Planner: ...", "Writer: ..."
    const prompts = {};
    const text = state.evolutionResult;
    const agentMatch = text.match(/Planner[：:]\s*([\s\S]*?)(?=Writer[：:]|Critic[：:]|Editor[：:]|工作流|评分|模板|$)/i);
    const writerMatch = text.match(/Writer[：:]\s*([\s\S]*?)(?=Planner[：:]|Critic[：:]|Editor[：:]|工作流|评分|模板|$)/i);
    const criticMatch = text.match(/Critic[：:]\s*([\s\S]*?)(?=Planner[：:]|Writer[：:]|Editor[：:]|工作流|评分|模板|$)/i);
    const editorMatch = text.match(/Editor[：:]\s*([\s\S]*?)(?=Planner[：:]|Writer[：:]|Critic[：:]|工作流|评分|模板|$)/i);

    if (agentMatch) prompts.Planner = agentMatch[1].trim().slice(0, 2000);
    if (writerMatch) prompts.Writer = writerMatch[1].trim().slice(0, 2000);
    if (criticMatch) prompts.Critic = criticMatch[1].trim().slice(0, 2000);
    if (editorMatch) prompts.Editor = editorMatch[1].trim().slice(0, 2000);

    if (!Object.keys(prompts).length) {
      // If no structured sections found, apply the entire analysis as a general evolution note
      setStatus("未检测到结构化 prompt 建议，请在分析结果中手动标注 Planner:/Writer: 等段落。");
      dom.applyEvolutionButton.disabled = false;
      dom.applyEvolutionButton.textContent = "应用到所有 Agent";
      return;
    }

    await api("/api/evolution/apply", { method: "POST", body: JSON.stringify({ prompts }) });
    state.evolutionLogCount = (state.evolutionLogCount || 0) + 1;
    setStatus(`已应用进化 prompt 到：${Object.keys(prompts).join("、")}`);
    dom.evolutionApplyRow.classList.add("is-hidden");
    renderSettings();
  } catch (error) {
    setStatus(`应用失败：${error.message}`);
  } finally {
    dom.applyEvolutionButton.disabled = false;
    dom.applyEvolutionButton.textContent = "应用到所有 Agent";
  }
}

async function resetPrompts() {
  try {
    await api("/api/prompts/reset", { method: "POST" });
    setStatus("已重置所有 Agent prompt 为出厂默认值");
    renderSettings();
  } catch (error) {
    setStatus(`重置失败：${error.message}`);
  }
}

// ── Template Management ──────────────────────────────────

function openTemplateModal(templateId = "") {
  state.templateModalOpen = true;
  state.editingTemplateId = templateId;
  const tpl = templateId ? state.templates.find(t => t.id === templateId) : null;
  document.getElementById("templateFormName").value = tpl?.name || "";
  document.getElementById("templateFormType").value = tpl?.content_type || "";
  document.getElementById("templateFormDesc").value = tpl?.description || "";
  document.getElementById("templateFormTone").value = tpl?.default_tone || "";
  document.getElementById("templateFormAudience").value = tpl?.default_audience || "";
  document.getElementById("templateFormLength").value = tpl?.default_length || "中等";
  document.getElementById("templateFormHint").value = tpl?.system_hint || "";
  document.getElementById("templateModalTitle").textContent = templateId ? "编辑模板" : "新建模板";
  dom.templateDeleteButton.style.display = templateId ? "" : "none";
  renderTemplateModal();
}

function closeTemplateModal() {
  state.templateModalOpen = false;
  state.editingTemplateId = "";
  renderTemplateModal();
}

function renderTemplateModal() {
  dom.templateModal.classList.toggle("is-hidden", !state.templateModalOpen);
  dom.templateModal.setAttribute("aria-hidden", state.templateModalOpen ? "false" : "true");
}

async function saveTemplate() {
  const payload = {
    name: document.getElementById("templateFormName").value.trim(),
    content_type: document.getElementById("templateFormType").value.trim(),
    description: document.getElementById("templateFormDesc").value.trim(),
    default_tone: document.getElementById("templateFormTone").value.trim(),
    default_audience: document.getElementById("templateFormAudience").value.trim(),
    default_length: document.getElementById("templateFormLength").value,
    system_hint: document.getElementById("templateFormHint").value.trim(),
  };
  if (!payload.name || !payload.content_type) {
    setStatus("模板名称和内容类型为必填");
    return;
  }

  try {
    if (state.editingTemplateId) {
      await api("/api/templates", { method: "POST",
        body: JSON.stringify({ id: state.editingTemplateId, ...payload }) });
    } else {
      payload.id = "tpl_" + Date.now();
      await api("/api/templates", { method: "POST", body: JSON.stringify(payload) });
    }
    await loadTemplates();
    closeTemplateModal();
    renderSettings();
    renderTemplateGrid();
    setStatus("模板已保存");
  } catch (error) {
    setStatus(`保存模板失败：${error.message}`);
  }
}

async function deleteTemplate() {
  if (!state.editingTemplateId) return;
  try {
    await api(`/api/templates/${state.editingTemplateId}`, { method: "DELETE" });
    if (state.selectedTemplateId === state.editingTemplateId) {
      state.selectedTemplateId = "";
    }
    await loadTemplates();
    closeTemplateModal();
    renderSettings();
    renderTemplateGrid();
    setStatus("模板已删除");
  } catch (error) {
    setStatus(`删除失败：${error.message}`);
  }
}

async function saveRunAsTemplate() {
  if (!state.currentRunId || !state.finalContent) return;
  const payload = {
    name: (state.currentPrompt || "").slice(0, 30) + " 模板",
    content_type: state.form.contentType,
    description: "从历史创作保存",
    default_tone: state.form.tone,
    default_audience: state.form.audience,
    default_length: state.form.lengthHint,
    system_hint: state.form.extraRequirements || "",
  };
  payload.id = "tpl_saved_" + Date.now();
  try {
    await api("/api/templates", { method: "POST", body: JSON.stringify(payload) });
    await loadTemplates();
    renderTemplateGrid();
    setStatus("已保存为模板");
  } catch (error) {
    setStatus(`保存失败：${error.message}`);
  }
}

function renderTemplateManageList() {
  if (!dom.templateManageList) return;
  if (!state.templates.length) {
    dom.templateManageList.innerHTML = '<div class="empty-history">暂无模板</div>';
    return;
  }
  dom.templateManageList.innerHTML = state.templates.map(tpl => `
    <div class="template-manage-row">
      <div class="template-manage-info">
        <div class="template-manage-name">${escapeHtml(tpl.name)}</div>
        <div class="template-manage-type">${escapeHtml(tpl.content_type)} · ${escapeHtml(tpl.description || "")}</div>
      </div>
      <div class="template-manage-actions">
        <button class="copy-button" type="button" data-edit-template="${escapeHtml(tpl.id)}">编辑</button>
      </div>
    </div>
  `).join("");
}

// ── Memory ───────────────────────────────────────────────

async function loadMemory() {
  try {
    state.memoryData = await api("/api/memory");
  } catch { /* silent */ }
}

// ── Form & State ─────────────────────────────────────────

function hydrateForm() {
  dom.contentType.value = state.form.contentType;
  dom.audience.value = state.form.audience;
  dom.tone.value = state.form.tone;
  dom.lengthHint.value = state.form.lengthHint;
  dom.extraRequirements.value = state.form.extraRequirements;
  dom.composerInput.value = state.currentPrompt;
  autoResizeComposer();
}

function syncFormFromInputs() {
  state.form.contentType = dom.contentType.value;
  state.form.audience = dom.audience.value.trim();
  state.form.tone = dom.tone.value.trim();
  state.form.lengthHint = dom.lengthHint.value;
  state.form.extraRequirements = dom.extraRequirements.value.trim();
}

function onComposerInput() {
  state.currentPrompt = dom.composerInput.value;
  autoResizeComposer();
  updateMainTitle();
  updateSendState();
}

function onComposerKeydown(event) {
  if (event.key === "Enter" && !event.shiftKey && !state.isComposing) {
    event.preventDefault();
    createContent();
  }
}

function onThreadScroll() {
  const el = dom.chatScrollRegion.parentElement;
  state.nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 120;
}

function autoResizeComposer() {
  const el = dom.composerInput;
  el.style.height = "0px";
  const next = Math.min(Math.max(el.scrollHeight, 56), 200);
  el.style.height = `${next}px`;
  el.style.overflowY = el.scrollHeight > 200 ? "auto" : "hidden";
}

function updateSendState() {
  dom.sendButton.disabled = !state.currentPrompt.trim() || state.loading;
}

function setStatus(text) {
  state.statusText = text;
  dom.statusText.textContent = text;
}

function toggleSidebarCollapse() {
  state.sidebarCollapsed = !state.sidebarCollapsed;
  renderSidebarState();
}

function toggleMobileSidebar() {
  state.mobileSidebarOpen = !state.mobileSidebarOpen;
  dom.body.classList.toggle("mobile-sidebar-open", state.mobileSidebarOpen);
}

function closeMobileSidebar() {
  state.mobileSidebarOpen = false;
  dom.body.classList.remove("mobile-sidebar-open");
}

function openTools() {
  state.toolsOpen = true;
  renderToolsState();
  renderTemplateGrid();
}

function closeTools() {
  state.toolsOpen = false;
  renderToolsState();
}

function setView(view) {
  state.currentView = view;
  updateMainTitle();
  dom.navButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.view === view);
  });
  renderThread();
}

function setMode(mode) {
  state.settings.mode = mode === "expert" ? "expert" : "fast";
  window.localStorage.setItem("ecroom_mode", state.settings.mode);
  renderSettings();
  setStatus(`已切换为${state.settings.mode === "expert" ? "专家模式" : "快速模式"}`);
}

function openSettings() {
  state.settingsOpen = true;
  renderSettings();
}

function closeSettings() {
  state.settingsOpen = false;
  renderSettings();
}

function renderToolsState() {
  dom.composerTools.classList.toggle("is-hidden", !state.toolsOpen);
  if (state.toolsOpen) renderTemplateGrid();
}

function renderSidebarState() {
  dom.body.classList.toggle("sidebar-collapsed", state.sidebarCollapsed);
  dom.sidebar.classList.toggle("is-collapsed", state.sidebarCollapsed);
  dom.sidebar.classList.toggle("is-expanded", !state.sidebarCollapsed);
}

function updateMainTitle() {
  if (state.currentView === "create") {
    dom.mainTitle.textContent = state.currentPrompt.trim()
      ? ellipsis(state.currentPrompt.trim(), 42)
      : "开始一段新的创作对话";
    return;
  }
  dom.mainTitle.textContent = state.currentView === "inspiration" ? "灵感页" : "资产页";
}

// ── Create & Iterate ─────────────────────────────────────

function payloadFromState() {
  syncFormFromInputs();
  return {
    content_type: state.form.contentType,
    user_prompt: state.currentPrompt.trim(),
    audience: state.form.audience,
    tone: state.form.tone,
    length_hint: state.form.lengthHint,
    extra_requirements: state.form.extraRequirements,
    mode: state.settings.mode,
    model: resolveCurrentModel(),
    template_id: state.selectedTemplateId,
  };
}

async function createContent() {
  const payload = payloadFromState();
  if (!payload.user_prompt) {
    setStatus("请先输入创作需求");
    dom.composerInput.focus();
    return;
  }

  // 立即清空输入框
  state.currentPrompt = payload.user_prompt;
  dom.composerInput.value = "";
  autoResizeComposer();
  updateSendState();

  state.loading = true;
  state.currentRunId = null;
  state.selectedHistoryId = null;
  state.finalContent = "";
  state.steps = [];
  state.modificationInput = "";
  state.iterationChain = [];
  setView("create");
  setStatus(`正在生成内容，当前为${state.settings.mode === "expert" ? "专家模式" : "快速模式"}...`);
  render();
  scrollThreadToBottom(true);

  try {
    const data = await api("/api/create", { method: "POST", body: JSON.stringify(payload) });
    state.currentRunId = data.run_id;
    state.selectedHistoryId = data.run_id;
    state.finalContent = data.final_content || "";
    state.steps = data.steps || [];
    state.loading = false;
    const evoNote = data.evolution_note ? ` ${data.evolution_note}` : "";
    setStatus(`已生成完成，当前模型 ${data.model || resolveCurrentModel()}。${evoNote}`);
    render();
    scrollThreadToBottom(true);
    await loadHistory();
  } catch (error) {
    state.loading = false;
    setStatus(`执行失败：${error.message}`);
    render();
  } finally {
    updateSendState();
  }
}

async function iterateContent() {
  const modification = state.modificationInput.trim();
  if (!modification || !state.currentRunId) return;

  state.iterating = true;
  setStatus("正在根据修改意见重生成...");
  renderThread();
  scrollThreadToBottom(true);

  try {
    const data = await api("/api/iterate", {
      method: "POST",
      body: JSON.stringify({
        run_id: state.currentRunId,
        modification_request: modification,
        mode: state.settings.mode,
        model: resolveCurrentModel(),
      }),
    });
    // Add to iteration chain
    state.iterationChain.push({
      run_id: state.currentRunId,
      preview: state.finalContent.slice(0, 80),
    });
    state.currentRunId = data.run_id;
    state.selectedHistoryId = data.run_id;
    state.finalContent = data.final_content || "";
    state.steps = data.steps || [];
    state.modificationInput = "";
    state.iterating = false;
    setStatus(`第${data.iteration_round || "?"}轮修改完成，当前模型 ${data.model || resolveCurrentModel()}`);
    render();
    scrollThreadToBottom(true);
    await loadHistory();
  } catch (error) {
    state.iterating = false;
    setStatus(`修改失败：${error.message}`);
    render();
  }
}

async function submitFeedback() {
  if (!state.currentRunId) {
    setStatus("请先完成一次创作，再提交反馈");
    return;
  }

  try {
    const data = await api("/api/feedback", {
      method: "POST",
      body: JSON.stringify({
        run_id: state.currentRunId,
        rating: state.feedbackRating || "",
        comment: state.feedbackComment.trim(),
      }),
    });
    state.feedbackComment = "";
    state.feedbackRating = "";
    const evoMsg = data.evolution_recommended ? " 反馈数据已积累，可在设置中触发自进化分析。" : "";
    setStatus(`反馈已保存，本地偏好已更新。${evoMsg}`);
    renderThread();
  } catch (error) {
    setStatus(`反馈失败：${error.message}`);
  }
}

// ── Delete ───────────────────────────────────────────────

async function requestDeleteRun(runId) {
  const attempts = [
    async () => api("/api/run/delete", { method: "POST", body: JSON.stringify({ id: runId }) }),
    async () => api(`/api/run?id=${encodeURIComponent(runId)}`, { method: "DELETE" }),
  ];
  let lastError = null;
  for (const attempt of attempts) {
    try { return await attempt(); } catch (error) {
      lastError = error;
      const message = String(error?.message || "");
      const retryable = message.includes("Not found") || message.includes("非 JSON 响应")
        || message.includes("Unexpected token") || message.includes("Failed to fetch");
      if (!retryable) throw error;
    }
  }
  throw lastError || new Error("删除失败");
}

function resetConversation() {
  state.currentView = "create";
  state.currentRunId = null;
  state.selectedHistoryId = null;
  state.loading = false;
  state.iterating = false;
  state.currentPrompt = "";
  state.finalContent = "";
  state.steps = [];
  state.feedbackComment = "";
  state.feedbackRating = "";
  state.historyMenuId = null;
  state.pendingDeleteRunId = null;
  state.pendingDeleteTitle = "";
  state.deleteModalOpen = false;
  state.selectedTemplateId = "";
  state.modificationInput = "";
  state.iterationChain = [];
  state.form = {
    contentType: "短视频脚本",
    audience: "",
    tone: "",
    lengthHint: "中等",
    extraRequirements: "",
  };
  hydrateForm();
  render();
  setStatus("等待输入");
  closeMobileSidebar();
  loadHistory().catch(() => {});
  renderTemplateGrid();
}

// ── History ──────────────────────────────────────────────

async function loadRun(runId) {
  const data = await api(`/api/run?id=${encodeURIComponent(runId)}`);
  state.currentRunId = data.id;
  state.selectedHistoryId = data.id;
  state.loading = false;
  state.currentPrompt = data.user_prompt || "";
  state.finalContent = data.final_content || "";
  state.steps = data.steps || [];
  state.feedbackComment = "";
  state.feedbackRating = "";
  state.modificationInput = "";
  state.iterationChain = [];
  state.form.contentType = data.content_type || "短视频脚本";
  state.form.audience = data.audience || "";
  state.form.tone = data.tone || "";
  state.form.lengthHint = data.length_hint || "中等";
  state.form.extraRequirements = data.extra_requirements || "";
  state.settings.mode = data.mode === "expert" ? "expert" : state.settings.mode;
  state.selectedTemplateId = data.template_id || "";
  state.iterationChain = [];

  // Load iteration chain
  if (data.parent_run_id || data.iteration_round > 0) {
    await loadIterationChain(runId);
  }

  hydrateForm();
  renderTemplateGrid();
  setView("create");
  render();
  setStatus("已加载历史对话");
  scrollThreadToBottom(true);
  await loadHistory();
}

async function loadIterationChain(runId) {
  try {
    const data = await api(`/api/run/iterations?id=${encodeURIComponent(runId)}`);
    const items = data.items || [];
    state.iterationChain = items
      .filter(r => r.id !== runId)
      .map(r => ({
        run_id: r.id,
        iteration_round: r.iteration_round || 0,
        preview: (r.user_prompt || "").slice(0, 60),
      }));
  } catch { /* silent */ }
}

async function deleteRun(runId) {
  await requestDeleteRun(runId);
  if (state.currentRunId === runId || state.selectedHistoryId === runId) {
    resetConversation();
  }
  state.historyMenuId = null;
  await loadHistory();
  setStatus("聊天记录已删除");
}

function renderHistory(items) {
  if (!items.length) {
    dom.historyList.innerHTML = '<div class="empty-history">还没有历史任务。</div>';
    return;
  }
  dom.historyList.innerHTML = items.map((item) => {
    const menuOpen = state.historyMenuId === item.id;
    const modeText = item.mode === "expert" ? "专家" : "快速";
    return `
      <div class="conversation-row ${item.id === state.selectedHistoryId ? "is-selected" : ""}">
        <button class="conversation-item" data-history-id="${item.id}" type="button">
          <span class="sidebar-label-wrapper conversation-item-label-wrapper">
            <span class="conversation-item-title label">${escapeHtml(ellipsis(item.user_prompt, 26))}</span>
            <span class="conversation-item-meta label">${escapeHtml(modeText)} · ${escapeHtml(item.content_type || "")}</span>
          </span>
        </button>
        <div class="history-actions">
          <button class="history-more-button" type="button" data-history-menu="${item.id}" aria-label="更多操作">⋯</button>
          <div class="history-menu ${menuOpen ? "is-open" : ""}">
            <button class="history-menu-item history-menu-danger" type="button" data-delete-history="${item.id}">删除聊天</button>
          </div>
        </div>
      </div>
    `;
  }).join("");
}

// ── Event Delegation ─────────────────────────────────────

function onHistoryClick(event) {
  const menuButton = event.target.closest("[data-history-menu]");
  if (menuButton) {
    event.stopPropagation();
    const nextId = menuButton.dataset.historyMenu;
    state.historyMenuId = state.historyMenuId === nextId ? null : nextId;
    renderHistory(state.historyItems);
    return;
  }
  const deleteButton = event.target.closest("[data-delete-history]");
  if (deleteButton) {
    event.stopPropagation();
    openDeleteModal(deleteButton.dataset.deleteHistory);
    return;
  }
  const item = event.target.closest("[data-history-id]");
  if (!item) return;
  loadRun(item.dataset.historyId);
  closeMobileSidebar();
}

function onThreadClick(event) {
  // Inspiration card
  const inspirationCard = event.target.closest("[data-inspiration-index]");
  if (inspirationCard) {
    const item = inspirationSeed[Number(inspirationCard.dataset.inspirationIndex)];
    applyPayload(item.payload);
    setView("create");
    render();
    setStatus("灵感已带入聊天框，可以直接发送");
    return;
  }

  // Template card in composer
  const templateCard = event.target.closest("[data-template-id]");
  if (templateCard) {
    selectTemplate(templateCard.dataset.templateId);
    return;
  }

  // Code copy
  const copyCodeButton = event.target.closest("[data-copy-code]");
  if (copyCodeButton) {
    const code = decodeCode(copyCodeButton.dataset.copyCode);
    navigator.clipboard.writeText(code).then(() => flashButton(copyCodeButton, "已复制"));
    return;
  }

  // Final content copy
  const copyFinalButton = event.target.closest("[data-copy-final]");
  if (copyFinalButton) {
    navigator.clipboard.writeText(state.finalContent || "").then(() => flashButton(copyFinalButton, "已复制"));
    return;
  }

  // Submit feedback
  const feedbackButton = event.target.closest("#submitFeedbackButton");
  if (feedbackButton) { submitFeedback(); return; }

  // Submit modification (iterate)
  const modifyButton = event.target.closest("#submitModifyButton");
  if (modifyButton) { iterateContent(); return; }

  // Iteration chain link
  const chainLink = event.target.closest("[data-iteration-link]");
  if (chainLink) {
    loadRun(chainLink.dataset.iterationLink);
    return;
  }

  // Save as template
  const saveTplButton = event.target.closest("[data-save-template]");
  if (saveTplButton) { saveRunAsTemplate(); return; }

  // Edit template from settings
  const editTplButton = event.target.closest("[data-edit-template]");
  if (editTplButton) { openTemplateModal(editTplButton.dataset.editTemplate); return; }
}

function onThreadInput(event) {
  if (event.target.id === "finalContentEditor") {
    state.finalContent = event.target.value;
    return;
  }
  if (event.target.id === "feedbackComment") {
    state.feedbackComment = event.target.value;
    return;
  }
  if (event.target.id === "feedbackRating") {
    state.feedbackRating = event.target.value;
    return;
  }
  if (event.target.id === "modificationInput") {
    state.modificationInput = event.target.value;
  }
}

function applyPayload(payload) {
  state.currentPrompt = payload.user_prompt || "";
  state.form.contentType = payload.content_type || "短视频脚本";
  state.form.audience = payload.audience || "";
  state.form.tone = payload.tone || "";
  state.form.lengthHint = payload.length_hint || "中等";
  state.form.extraRequirements = payload.extra_requirements || "";
  state.currentRunId = null;
  state.selectedHistoryId = null;
  state.finalContent = "";
  state.steps = [];
  state.selectedTemplateId = "";
  state.modificationInput = "";
  state.iterationChain = [];
  hydrateForm();
  renderTemplateGrid();
  renderThread();
  updateMainTitle();
  setStatus("灵感已填入输入框");
}

// ── Delete Modal ─────────────────────────────────────────

function openDeleteModal(runId) {
  const item = state.historyItems.find((row) => row.id === runId);
  state.pendingDeleteRunId = runId;
  state.pendingDeleteTitle = item?.user_prompt || "这条聊天记录";
  state.deleteModalOpen = true;
  state.historyMenuId = null;
  renderHistory(state.historyItems);
  renderDeleteModal();
}

function closeDeleteModal() {
  state.deleteModalOpen = false;
  state.pendingDeleteRunId = null;
  state.pendingDeleteTitle = "";
  renderDeleteModal();
}

async function confirmDeleteRun() {
  const runId = state.pendingDeleteRunId;
  if (!runId) { closeDeleteModal(); return; }
  try { await deleteRun(runId); closeDeleteModal(); }
  catch (error) { closeDeleteModal(); setStatus(`删除失败：${error.message}`); }
}

// ── Render ───────────────────────────────────────────────

function render() {
  renderToolsState();
  renderSidebarState();
  renderSettings();
  renderDeleteModal();
  updateMainTitle();
  renderThread();
  updateSendState();
}

function renderSettings() {
  const open = state.settingsOpen;
  dom.settingsModal.classList.toggle("is-hidden", !open);
  dom.settingsModal.setAttribute("aria-hidden", open ? "false" : "true");
  dom.fastModeButton.classList.toggle("is-active", state.settings.mode === "fast");
  dom.expertModeButton.classList.toggle("is-active", state.settings.mode === "expert");

  const currentModeText = state.settings.mode === "expert" ? "专家模式" : "快速模式";
  const currentModel = resolveCurrentModel();
  dom.currentModeLabel.textContent = currentModeText;
  dom.currentModelLabel.textContent = currentModel;

  const availability = state.modelCatalog.availability || {};
  const currentAvailability = state.settings.mode === "expert" ? availability.expert : availability.fast;
  dom.modelStatusLabel.textContent = currentAvailability ? "可用" : "未确认";

  const items = state.modelCatalog.items || [];
  dom.modelList.innerHTML = items.map((item) => {
    const isCurrent = item.id === currentModel;
    return `
      <div class="model-chip ${isCurrent ? "is-current" : ""}">
        <span>${escapeHtml(item.id)}</span>
        <span class="model-chip-owner">${escapeHtml(item.owned_by || "")}</span>
      </div>
    `;
  }).join("");

  const errorMessage = state.modelCatalog.error || "";
  dom.modelError.classList.toggle("is-hidden", !errorMessage);
  dom.modelError.textContent = errorMessage ? `模型列表获取失败，当前展示为本地兜底配置。${errorMessage}` : "";

  // Evolution info
  dom.evolutionFeedbackCount.textContent = state.evolutionFeedbackCount || "—";
  dom.evolutionLogCount.textContent = state.evolutionLogCount || "—";
  dom.evolutionResult.classList.toggle("is-hidden", !state.evolutionResult);
  dom.evolutionResult.textContent = state.evolutionResult || "";
  const hasAnalysis = state.evolutionResult && !state.evolutionResult.includes("数据不足");
  dom.evolutionApplyRow.classList.toggle("is-hidden", !hasAnalysis);

  // Template management list
  renderTemplateManageList();
}

function renderDeleteModal() {
  const open = state.deleteModalOpen;
  dom.deleteModal.classList.toggle("is-hidden", !open);
  dom.deleteModal.setAttribute("aria-hidden", open ? "false" : "true");
  const title = state.pendingDeleteTitle ? `"${ellipsis(state.pendingDeleteTitle, 36)}"` : "这条聊天记录";
  dom.deleteMessage.textContent = `确认删除 ${title} 吗？删除后无法恢复。`;
}

// ── Thread Render ────────────────────────────────────────

function renderThread() {
  if (state.currentView === "inspiration") { dom.chatThread.innerHTML = renderInspirationView(); return; }
  if (state.currentView === "assets") { dom.chatThread.innerHTML = renderAssetsView(); return; }

  if (!state.currentPrompt.trim() && !state.finalContent && !state.loading && !state.steps.length) {
    dom.chatThread.innerHTML = renderHomeView();
    return;
  }

  if (state.currentPrompt.trim() && !state.currentRunId && !state.finalContent && !state.loading && !state.steps.length) {
    dom.chatThread.innerHTML = renderDraftView();
    return;
  }

  dom.chatThread.innerHTML = renderConversationView();
}

function renderHomeView() {
  return `
    <div class="home-shell">
      <div class="home-inner">
        <div class="home-title">今天想写点什么？</div>
        <div class="home-subtitle">多 Agent 协作 + 记忆进化 + RAG 检索，越用越懂你。</div>
        <div class="tag-row">
          <div class="tag-pill">Planner</div>
          <div class="tag-pill">Writer</div>
          <div class="tag-pill">Critic</div>
          <div class="tag-pill">Editor</div>
          <div class="tag-pill">Memory</div>
          <div class="tag-pill">Evolution</div>
        </div>
        <div class="prompt-suggestion-grid">
          ${inspirationSeed.map((item, index) => `
            <button class="suggestion-card" type="button" data-inspiration-index="${index}">
              <div class="suggestion-title">${escapeHtml(item.title)}</div>
              <div class="suggestion-copy">${escapeHtml(item.description)}</div>
            </button>
          `).join("")}
        </div>
      </div>
    </div>
  `;
}

function renderInspirationView() {
  return `
    <div class="thread-inner">
      <div class="assistant-meta">
        <div class="assistant-status-dot"></div>
        <span>灵感页</span>
      </div>
      <div class="markdown">
        <p>点击任意卡片会把需求带入输入框，你可以继续改参数后再生成。</p>
      </div>
      <div class="inspiration-grid">
        ${inspirationSeed.map((item, index) => `
          <button class="inspiration-card" type="button" data-inspiration-index="${index}">
            <div class="inspiration-title">${escapeHtml(item.title)}</div>
            <div class="inspiration-copy">${escapeHtml(item.description)}</div>
          </button>
        `).join("")}
      </div>
    </div>
  `;
}

function renderDraftView() {
  return `
    <div class="thread-inner">
      <div class="assistant-meta">
        <div class="assistant-status-dot"></div>
        <span>草稿已准备好</span>
      </div>
      <div class="markdown">
        <p>需求已经带入输入框。你可以直接发送，也可以先展开"创作参数"补充内容类型、受众、语气和额外要求。</p>
      </div>
      <div class="thread-panel">
        <div class="thread-panel-header">
          <span>待发送内容</span>
          <span>尚未开始生成</span>
        </div>
        <div class="thread-panel-body">
          <div class="step-item-copy">${escapeHtml(state.currentPrompt.trim())}</div>
        </div>
      </div>
    </div>
  `;
}

function renderAssetsView() {
  const memory = state.memoryData;
  const profile = memory?.user_profile || {};
  const patterns = memory?.successful_patterns || [];
  const tones = profile.preferred_tones || {};
  const cts = profile.preferred_content_types || {};
  const audiences = profile.common_audiences || [];

  return `
    <div class="thread-inner">
      <div class="assistant-meta">
        <div class="assistant-status-dot"></div>
        <span>资产页 · 用户记忆与进化数据</span>
      </div>

      <div class="thread-panel">
        <div class="thread-panel-header"><span>偏好语气</span><span>${Object.keys(tones).length ? '已学习' : '待积累'}</span></div>
        <div class="thread-panel-body">
          ${Object.keys(tones).length
            ? Object.entries(tones).sort((a,b) => b[1]-a[1]).map(([k,v]) => `<div class="tag-pill" style="display:inline-flex;margin:4px">${escapeHtml(k)} (${v.toFixed(1)})</div>`).join("")
            : '<div class="empty-history">多次高分反馈后，系统会自动学习你的语气偏好。</div>'}
        </div>
      </div>

      <div class="thread-panel">
        <div class="thread-panel-header"><span>擅长内容类型</span></div>
        <div class="thread-panel-body">
          ${Object.keys(cts).length
            ? Object.entries(cts).sort((a,b) => b[1]-a[1]).map(([k,v]) => `<div class="tag-pill" style="display:inline-flex;margin:4px">${escapeHtml(k)} (${v.toFixed(1)})</div>`).join("")
            : '<div class="empty-history">完成更多创作后，系统会了解你擅长的内容类型。</div>'}
        </div>
      </div>

      <div class="thread-panel">
        <div class="thread-panel-header"><span>常见受众</span></div>
        <div class="thread-panel-body">
          ${audiences.length
            ? audiences.map(a => `<div class="tag-pill" style="display:inline-flex;margin:4px">${escapeHtml(a)}</div>`).join("")
            : '<div class="empty-history">尚未积累受众数据。</div>'}
        </div>
      </div>

      <div class="thread-panel">
        <div class="thread-panel-header"><span>高分案例</span><span>${patterns.length} 条</span></div>
        <div class="thread-panel-body">
          ${patterns.length
            ? patterns.slice(-5).reverse().map(p => `
                <div class="step-item">
                  <div class="step-item-header">
                    <span>${escapeHtml(p.content_type || '')} · 评分${p.rating || '?'}/5</span>
                  </div>
                  <div class="step-item-copy">${escapeHtml((p.preview || '').slice(0, 150))}...</div>
                </div>
              `).join("")
            : '<div class="empty-history">评分≥4分的创作案例会自动收录。</div>'}
        </div>
      </div>

      <div class="thread-panel">
        <div class="thread-panel-header"><span>进化日志</span></div>
        <div class="thread-panel-body">
          <div class="asset-copy">可在设置 → 自进化引擎中触发系统进化分析。当前进化次数：${state.evolutionLogCount || 0}</div>
        </div>
      </div>
    </div>
  `;
}

function renderConversationView() {
  const isBusy = state.loading || state.iterating;
  const chainHtml = state.iterationChain.length ? `
    <div class="iteration-chain">
      <span style="font-size:12px;color:var(--text-tertiary)">修改链：</span>
      ${state.iterationChain.map(c => `
        <button class="iteration-link" type="button" data-iteration-link="${escapeHtml(c.run_id)}">
          第${c.iteration_round || '?'}轮 → ${escapeHtml(ellipsis(c.preview, 20))}
        </button>
      `).join("")}
      <span class="iteration-link is-current">当前版本</span>
    </div>
  ` : "";

  return `
    <div class="message-row user">
      <div class="message-row-inner">
        <div class="message-bubble">${escapeHtml(state.currentPrompt.trim())}</div>
      </div>
    </div>

    <div class="message-row assistant">
      <div class="message-row-inner">
        <div class="assistant-block">
          <div class="assistant-avatar">EC</div>
          <div class="assistant-content">
            <div class="assistant-meta">
              <div class="assistant-status-dot ${isBusy ? "is-streaming" : ""}"></div>
              <span>${isBusy ? "正在生成" : "已完成生成"}</span>
              <span>·</span>
              <span>${state.settings.mode === "expert" ? "专家模式" : "快速模式"}</span>
              <span>·</span>
              <span>${escapeHtml(resolveCurrentModel())}</span>
            </div>
            <div class="markdown">
              ${isBusy
                ? "<p>Planner、Writer、Critic、Editor 正在协作，请稍候。</p>"
                : state.finalContent ? renderMarkdownLite(state.finalContent) : "<p>还没有可展示的结果。</p>"}
            </div>

            ${chainHtml}

            <div class="thread-panel">
              <div class="thread-panel-header">
                <span>终稿编辑</span>
                <div>
                  <button class="copy-button" type="button" data-save-template="true">保存为模板</button>
                  <button class="copy-button" type="button" data-copy-final="true">复制终稿</button>
                </div>
              </div>
              <div class="thread-panel-body">
                <textarea id="finalContentEditor" class="editor-textarea">${escapeHtml(state.finalContent)}</textarea>
              </div>
            </div>

            ${!isBusy ? `
            <div class="thread-panel">
              <div class="thread-panel-header"><span>修改迭代</span><span>输入修改意见，Trigger 重生成</span></div>
              <div class="thread-panel-body">
                <div class="modify-section">
                  <textarea id="modificationInput" class="modify-input" rows="1"
                    placeholder="例如：缩短开头、增加数据引用、语气更冷一点、把第二段删掉...">${escapeHtml(state.modificationInput)}</textarea>
                  <button id="submitModifyButton" class="modify-submit-button" type="button"
                    ${!state.modificationInput.trim() ? "disabled" : ""}>重新生成</button>
                </div>
              </div>
            </div>
            ` : ""}

            <div class="thread-panel">
              <div class="thread-panel-header">
                <span>协作过程</span>
                <span>${state.steps.length ? `${state.steps.length} 个阶段` : "等待结果"}</span>
              </div>
              <div class="thread-panel-body">${renderStepsPanel()}</div>
            </div>

            ${!isBusy ? `
            <div class="thread-panel">
              <div class="thread-panel-header">
                <span>任务反馈</span>
                <span>用于更新本地记忆</span>
              </div>
              <div class="thread-panel-body">
                <div class="feedback-row">
                  <select id="feedbackRating" class="feedback-select">
                    <option value="" ${state.feedbackRating === "" ? "selected" : ""}>满意度评分</option>
                    <option value="5" ${state.feedbackRating === "5" ? "selected" : ""}>5 分</option>
                    <option value="4" ${state.feedbackRating === "4" ? "selected" : ""}>4 分</option>
                    <option value="3" ${state.feedbackRating === "3" ? "selected" : ""}>3 分</option>
                    <option value="2" ${state.feedbackRating === "2" ? "selected" : ""}>2 分</option>
                    <option value="1" ${state.feedbackRating === "1" ? "selected" : ""}>1 分</option>
                  </select>
                  <button id="submitFeedbackButton" class="secondary-action" type="button">提交反馈</button>
                </div>
                <textarea id="feedbackComment" class="feedback-textarea"
                  placeholder="例如：语气更像真人一点；结构更紧一点；保留这种开头。">${escapeHtml(state.feedbackComment)}</textarea>
              </div>
            </div>
            ` : ""}
          </div>
        </div>
      </div>
    </div>
  `;
}

function renderStepsPanel() {
  if (!state.steps.length) {
    return '<div class="empty-history">生成完成后，这里会保留每个 Agent 的输出。</div>';
  }
  return `
    <div class="step-list">
      ${state.steps.map((step) => `
        <div class="step-item">
          <div class="step-item-header">
            <div class="step-item-title">${escapeHtml(step.agent)}</div>
            <div class="step-item-status">已完成</div>
          </div>
          <div class="step-item-copy">${escapeHtml(step.output)}</div>
        </div>
      `).join("")}
    </div>
  `;
}

// ── Markdown Lite ────────────────────────────────────────

function renderMarkdownLite(input) {
  if (!input || !input.trim()) return "<p>暂无内容。</p>";
  const source = input.replace(/\r\n/g, "\n");
  const regex = /```([a-zA-Z0-9_-]+)?\n([\s\S]*?)```/g;
  let cursor = 0, html = "", match;
  while ((match = regex.exec(source)) !== null) {
    html += renderTextBlocks(source.slice(cursor, match.index));
    html += renderCodeBlock(match[1] || "text", match[2] || "");
    cursor = regex.lastIndex;
  }
  html += renderTextBlocks(source.slice(cursor));
  return html;
}

function renderTextBlocks(text) {
  const trimmed = text.trim();
  if (!trimmed) return "";
  return trimmed.split(/\n{2,}/).map(renderBlock).join("");
}

function renderBlock(block) {
  const lines = block.split("\n").map((line) => line.trimEnd()).filter((line) => line !== "");
  if (!lines.length) return "";
  if (lines.every((line) => /^[-*]\s+/.test(line))) {
    return `<ul>${lines.map((line) => `<li>${formatInline(escapeHtml(line.replace(/^[-*]\s+/, "")))}</li>`).join("")}</ul>`;
  }
  if (lines.every((line) => /^\d+\.\s+/.test(line))) {
    return `<ol>${lines.map((line) => `<li>${formatInline(escapeHtml(line.replace(/^\d+\.\s+/, "")))}</li>`).join("")}</ol>`;
  }
  const heading = lines[0].match(/^(#{1,3})\s+(.+)$/);
  if (heading) {
    const level = Math.min(heading[1].length, 3);
    const title = formatInline(escapeHtml(heading[2]));
    const rest = lines.slice(1);
    return `<h${level}>${title}</h${level}>${rest.length ? `<p>${rest.map((line) => formatInline(escapeHtml(line))).join("<br>")}</p>` : ""}`;
  }
  return `<p>${lines.map((line) => formatInline(escapeHtml(line))).join("<br>")}</p>`;
}

function renderCodeBlock(language, code) {
  const encoded = encodeCode(code);
  return `
    <div class="code-block">
      <div class="code-block-header">
        <span>${escapeHtml(language)}</span>
        <button class="code-copy-button" type="button" data-copy-code="${encoded}">复制代码</button>
      </div>
      <pre><code>${escapeHtml(code)}</code></pre>
    </div>
  `;
}

function formatInline(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+?)`/g, '<code class="inline-code">$1</code>');
}

// ── Utilities ────────────────────────────────────────────

function flashButton(button, text) {
  const original = button.textContent;
  button.textContent = text;
  window.setTimeout(() => { button.textContent = original; }, 1200);
}

function scrollThreadToBottom(force = false) {
  if (!force && !state.nearBottom) return;
  requestAnimationFrame(() => {
    const el = dom.chatScrollRegion.parentElement;
    el.scrollTop = el.scrollHeight;
  });
}

function resolveCurrentModel() {
  const recommended = state.modelCatalog.recommended || fallbackModels.recommended;
  return state.settings.mode === "expert" ? recommended.expert : recommended.fast;
}

function ellipsis(text, maxLength) {
  const value = String(text || "");
  return value.length > maxLength ? `${value.slice(0, maxLength)}…` : value;
}

function escapeHtml(text) {
  return String(text || "")
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}

function encodeCode(code) { return btoa(unescape(encodeURIComponent(code))); }
function decodeCode(code) { return decodeURIComponent(escape(atob(code))); }

init();
