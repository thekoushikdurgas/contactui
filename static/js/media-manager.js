/**
 * Media Manager – tabs, file list via API, view → preview.
 */
(function () {
  "use strict";

  const config = window.MEDIA_MANAGER_CONFIG || {};
  const base = config.baseUrl || "";
  const listUrl = config.urls?.listFiles || base + "/docs/api/media/files/";
  const previewBase = config.urls?.previewBase || base + "/docs/media/preview/";
  const viewerBase = config.urls?.viewerBase || base + "/docs/media/viewer/";
  const formEditBase = config.urls?.formEditBase || base + "/docs/media/form/edit/";
  const deleteBase = config.urls?.deleteBase || base + "/docs/media/delete/";
  const getCsrf = () => {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : "";
  };

  let currentTab = config.activeTab || "pages";
  let files = [];
  let selectedFiles = new Set();
  let filters = {
    search: '',
    syncStatus: '',
    sortBy: 'name',
    sortOrder: 'asc'
  };

  // Performance optimizations
  let cache = new Map();
  let cacheTimestamps = new Map();
  const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

  // Virtual scrolling for large datasets
  let virtualScrollEnabled = false;
  let visibleRange = { start: 0, end: 50 };
  const ITEMS_PER_PAGE = 50;

  // Bulk selection functions
  function updateBulkActions() {
    const bulkActionsBar = document.getElementById('bulk-actions-bar');
    const selectedCount = document.getElementById('selected-count');
    const bulkSyncBtn = document.getElementById('bulk-sync-btn');
    const bulkDeleteBtn = document.getElementById('bulk-delete-btn');

    if (selectedFiles.size > 0) {
      bulkActionsBar.classList.remove('hidden');
      selectedCount.textContent = selectedFiles.size;
      bulkSyncBtn.disabled = false;
      bulkDeleteBtn.disabled = false;
    } else {
      bulkActionsBar.classList.add('hidden');
      bulkSyncBtn.disabled = true;
      bulkDeleteBtn.disabled = true;
    }
  }

  function toggleFileSelection(filePath, checked) {
    if (checked) {
      selectedFiles.add(filePath);
    } else {
      selectedFiles.delete(filePath);
    }
    updateBulkActions();
  }

  function selectAllFiles() {
    const checkboxes = document.querySelectorAll('.file-checkbox');
    checkboxes.forEach(checkbox => {
      checkbox.checked = true;
      selectedFiles.add(checkbox.getAttribute('data-file-path'));
    });
    updateBulkActions();
  }

  function clearSelection() {
    const checkboxes = document.querySelectorAll('.file-checkbox');
    checkboxes.forEach(checkbox => {
      checkbox.checked = false;
    });
    selectedFiles.clear();
    updateBulkActions();
  }

  function bulkSyncFiles() {
    const filePaths = Array.from(selectedFiles);
    if (filePaths.length === 0) return;

    // Show loading state
    const btn = document.getElementById('bulk-sync-btn');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Syncing...';

    // Make bulk sync request
    fetch('/docs/api/media/bulk-sync/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrf()
      },
      body: JSON.stringify({
        resource_type: currentTab,
        direction: 'to_lambda',
        file_paths: filePaths
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Show success message
        showToast('Files synced successfully!', 'success');
        // Reload files to show updated sync status
        loadFiles();
        clearSelection();
      } else {
        showToast('Bulk sync failed: ' + (data.error || 'Unknown error'), 'error');
      }
    })
    .catch(error => {
      console.error('Bulk sync error:', error);
      showToast('Bulk sync failed. Please try again.', 'error');
    })
    .finally(() => {
      btn.disabled = false;
      btn.textContent = originalText;
    });
  }

  function bulkDeleteFiles() {
    const filePaths = Array.from(selectedFiles);
    if (filePaths.length === 0) return;

    if (!confirm(`Are you sure you want to delete ${filePaths.length} selected files?`)) {
      return;
    }

    // Show loading state
    const btn = document.getElementById('bulk-delete-btn');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Deleting...';

    // Delete files one by one (since bulk delete API might not exist yet)
    const deletePromises = filePaths.map(filePath => {
      return fetch('/docs/api/media/files/' + encodeURIComponent(filePath) + '/delete/', {
        method: 'DELETE',
        headers: {
          'X-CSRFToken': getCsrf()
        }
      });
    });

    Promise.all(deletePromises)
      .then(responses => {
        const successCount = responses.filter(r => r.ok).length;
        if (successCount === filePaths.length) {
          // All deleted successfully
          showToast(`Successfully deleted ${filePaths.length} files`, 'success');
          loadFiles();
          clearSelection();
        } else {
          showToast(`Deleted ${successCount} of ${filePaths.length} files. Some deletions failed.`, 'warning');
          loadFiles();
        }
      })
      .catch(error => {
        console.error('Bulk delete error:', error);
        showToast('Bulk delete failed. Please try again.', 'error');
      })
      .finally(() => {
        btn.disabled = false;
        btn.textContent = originalText;
      });
  }

  // Filtering functions
  function updateFilters() {
    filters.search = document.getElementById('file-search').value.trim();
    filters.syncStatus = document.getElementById('sync-status-filter').value;
    filters.sortBy = document.getElementById('sort-by-filter').value;
    filters.sortOrder = document.getElementById('sort-order-filter').value;
    loadFiles();
  }

  // Caching functions
  function getCacheKey(resourceType) {
    return `files_${resourceType}`;
  }

  function isCacheValid(key) {
    const timestamp = cacheTimestamps.get(key);
    if (!timestamp) return false;
    return Date.now() - timestamp < CACHE_DURATION;
  }

  function setCache(key, data) {
    cache.set(key, data);
    cacheTimestamps.set(key, Date.now());
  }

  function getCache(key) {
    if (isCacheValid(key)) {
      return cache.get(key);
    }
    return null;
  }

  function clearCache() {
    cache.clear();
    cacheTimestamps.clear();
  }

  // Background refresh for cache
  function scheduleBackgroundRefresh() {
    // Refresh cache in background every 4 minutes
    setTimeout(() => {
      const cacheKey = getCacheKey(currentTab);
      if (cache.has(cacheKey)) {
        fetch(listUrl + "?resource_type=" + encodeURIComponent(currentTab), {
          headers: { "Accept": "application/json" }
        })
        .then(r => r.json())
        .then(data => {
          if (data.success) {
            setCache(cacheKey, data.data);
          }
        })
        .catch(() => {
          // Silently fail background refresh
        });
      }
      scheduleBackgroundRefresh(); // Schedule next refresh
    }, 4 * 60 * 1000); // 4 minutes
  }

  function applyClientSideFilters(files) {
    let filtered = [...files];

    // Apply search filter
    if (filters.search) {
      const searchTerm = filters.search.toLowerCase();
      filtered = filtered.filter(file =>
        file.name.toLowerCase().includes(searchTerm) ||
        file.relative_path.toLowerCase().includes(searchTerm)
      );
    }

    // Apply sync status filter
    if (filters.syncStatus) {
      filtered = filtered.filter(file => file.sync_status === filters.syncStatus);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aVal, bVal;
      switch (filters.sortBy) {
        case 'modified':
          aVal = new Date(a.modified || 0);
          bVal = new Date(b.modified || 0);
          break;
        case 'size':
          aVal = a.size || 0;
          bVal = b.size || 0;
          break;
        default: // 'name'
          aVal = a.name.toLowerCase();
          bVal = b.name.toLowerCase();
      }

      if (aVal < bVal) return filters.sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return filters.sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered;
  }

  // Virtual scrolling functions
  function enableVirtualScrollingIfNeeded(fileCount) {
    virtualScrollEnabled = fileCount > 100;
    if (virtualScrollEnabled) {
      visibleRange = { start: 0, end: Math.min(ITEMS_PER_PAGE, fileCount) };
      setupScrollListener();
    }
  }

  function setupScrollListener() {
    const container = document.querySelector('.overflow-x-auto');
    if (container) {
      container.addEventListener('scroll', handleScroll, { passive: true });
    }
  }

  function handleScroll() {
    if (!virtualScrollEnabled) return;

    const container = document.querySelector('.overflow-x-auto');
    const scrollTop = container.scrollTop;
    const containerHeight = container.clientHeight;

    // Calculate visible range based on scroll position
    const itemHeight = 60; // Approximate height per row
    const start = Math.floor(scrollTop / itemHeight);
    const visibleCount = Math.ceil(containerHeight / itemHeight) + 10; // +10 for buffer
    const end = Math.min(start + visibleCount, files.length);

    if (start !== visibleRange.start || end !== visibleRange.end) {
      visibleRange = { start, end };
      renderRows(); // Re-render with new visible range
    }
  }

  function getVisibleFiles(filteredFiles) {
    if (!virtualScrollEnabled) return filteredFiles;
    return filteredFiles.slice(visibleRange.start, visibleRange.end);
  }

  function tabButtons() {
    const buttons = document.querySelectorAll("[data-media-tab]");
// #region agent log
fetch('http://127.0.0.1:7242/ingest/adfd807a-ef66-43c3-a0f8-1f2210dc4305',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'media-manager.js:tabButtons',message:'Found tab buttons',data:{count:buttons.length,buttons:Array.from(buttons).map(b=>b.getAttribute('data-media-tab'))},timestamp:Date.now(),sessionId:'debug-session',runId:'media-manager-debug',hypothesisId:'dom_elements'})}).catch(()=>{});
// #endregion
    return buttons;
  }

  function tabPanels() {
    const panels = document.querySelectorAll("[data-media-panel]");
// #region agent log
fetch('http://127.0.0.1:7242/ingest/adfd807a-ef66-43c3-a0f8-1f2210dc4305',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'media-manager.js:tabPanels',message:'Found tab panels',data:{count:panels.length,panels:Array.from(panels).map(p=>p.getAttribute('data-media-panel'))},timestamp:Date.now(),sessionId:'debug-session',runId:'media-manager-debug',hypothesisId:'dom_elements'})}).catch(()=>{});
// #endregion
    return panels;
  }

  function getTableBody() {
    const tbody = document.getElementById("media-files-tbody");
// #region agent log
fetch('http://127.0.0.1:7242/ingest/adfd807a-ef66-43c3-a0f8-1f2210dc4305',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'media-manager.js:getTableBody',message:'Found table body',data:{exists:!!tbody},timestamp:Date.now(),sessionId:'debug-session',runId:'media-manager-debug',hypothesisId:'dom_elements'})}).catch(()=>{});
// #endregion
    return tbody;
  }

  function getLoadingEl() {
    const loading = document.getElementById("media-files-loading");
// #region agent log
fetch('http://127.0.0.1:7242/ingest/adfd807a-ef66-43c3-a0f8-1f2210dc4305',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'media-manager.js:getLoadingEl',message:'Found loading element',data:{exists:!!loading},timestamp:Date.now(),sessionId:'debug-session',runId:'media-manager-debug',hypothesisId:'dom_elements'})}).catch(()=>{});
// #endregion
    return loading;
  }

  function getEmptyEl() {
    const empty = document.getElementById("media-files-empty");
// #region agent log
fetch('http://127.0.0.1:7242/ingest/adfd807a-ef66-43c3-a0f8-1f2210dc4305',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'media-manager.js:getEmptyEl',message:'Found empty element',data:{exists:!!empty},timestamp:Date.now(),sessionId:'debug-session',runId:'media-manager-debug',hypothesisId:'dom_elements'})}).catch(()=>{});
// #endregion
    return empty;
  }

  function getErrorEl() {
    // Create error element if it doesn't exist
    let errorEl = document.getElementById("media-files-error");
    if (!errorEl) {
      errorEl = document.createElement("div");
      errorEl.id = "media-files-error";
      errorEl.className = "hidden p-12 text-center";
      const container = document.querySelector('.overflow-x-auto');
      if (container) {
        container.appendChild(errorEl);
      }
    }
    return errorEl;
  }

  function showError(message, retryCallback = null) {
    const loading = getLoadingEl();
    const empty = getEmptyEl();
    const error = getErrorEl();
    const tbody = getTableBody();

    if (loading) loading.classList.add("hidden");
    if (empty) empty.classList.add("hidden");
    if (tbody) tbody.classList.add("hidden");
    if (error) {
      error.classList.remove("hidden");
      error.innerHTML = `
        <div class="text-center">
          <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 dark:bg-red-900/20 mb-4">
            <svg class="h-6 w-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/>
            </svg>
          </div>
          <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">Something went wrong</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">${message}</p>
          ${retryCallback ? '<button type="button" id="retry-btn" class="btn btn-primary btn-sm">Try Again</button>' : ''}
        </div>
      `;

      if (retryCallback) {
        document.getElementById('retry-btn')?.addEventListener('click', retryCallback);
      }
    }
  }

  function hideError() {
    const error = getErrorEl();
    if (error) error.classList.add("hidden");
  }

  function showToast(message, type = 'info', duration = 3000) {
    // Remove existing toasts
    const existingToasts = document.querySelectorAll('.toast-notification');
    existingToasts.forEach(toast => toast.remove());

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast-notification fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transform translate-x-full transition-transform duration-300`;

    // Set colors based on type
    const colors = {
      success: 'bg-green-100 border-green-500 text-green-800 dark:bg-green-900/30 dark:text-green-400',
      error: 'bg-red-100 border-red-500 text-red-800 dark:bg-red-900/30 dark:text-red-400',
      warning: 'bg-yellow-100 border-yellow-500 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
      info: 'bg-blue-100 border-blue-500 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
    };

    toast.classList.add(...colors[type].split(' '));

    // Add icon based on type
    const icons = {
      success: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
      error: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/></svg>',
      warning: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/></svg>',
      info: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
    };

    toast.innerHTML = `
      <div class="flex items-center gap-3">
        <div class="flex-shrink-0">
          ${icons[type]}
        </div>
        <div class="flex-1 text-sm font-medium">
          ${message}
        </div>
        <button type="button" class="flex-shrink-0 ml-2 text-current hover:opacity-75" onclick="this.parentElement.parentElement.remove()">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>
    `;

    // Add to page
    document.body.appendChild(toast);

    // Animate in
    setTimeout(() => {
      toast.classList.remove('translate-x-full');
    }, 100);

    // Auto remove
    setTimeout(() => {
      toast.classList.add('translate-x-full');
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }

  function setTab(tab) {
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/adfd807a-ef66-43c3-a0f8-1f2210dc4305',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'media-manager.js:setTab',message:'Setting tab',data:{tab:tab},timestamp:Date.now(),sessionId:'debug-session',runId:'media-manager-debug',hypothesisId:'tab_switch'})}).catch(()=>{});
    // #endregion

    currentTab = tab;
    // Clear selection when switching tabs
    clearSelection();
    tabButtons().forEach((btn) => {
      const t = btn.getAttribute("data-media-tab");
      btn.classList.toggle("border-blue-600", t === tab);
      btn.classList.toggle("text-blue-600", t === tab);
      btn.classList.toggle("border-transparent", t !== tab);
      btn.classList.toggle("text-gray-500", t !== tab);
    });
    tabPanels().forEach((panel) => {
      const t = panel.getAttribute("data-media-panel");
      panel.classList.toggle("hidden", t !== tab);
    });
    loadFiles();
  }

  function showLoading(show) {
    const loading = getLoadingEl();
    const empty = getEmptyEl();
    const tbody = getTableBody();
    const error = getErrorEl();
    if (loading) loading.classList.toggle("hidden", !show);
    if (tbody) tbody.classList.toggle("hidden", show);
    if (empty) empty.classList.add("hidden");
    if (error) error.classList.add("hidden");
  }

  function showEmpty(show) {
    const loading = getLoadingEl();
    const empty = getEmptyEl();
    const tbody = getTableBody();
    const error = getErrorEl();
    if (loading) loading.classList.add("hidden");
    if (tbody) tbody.classList.toggle("hidden", show);
    if (empty) empty.classList.toggle("hidden", !show);
    if (error) error.classList.add("hidden");
  }

  function formatDate(v) {
    if (v == null) return "—";
    if (typeof v === "number") {
      const d = new Date(v * 1000);
      return isNaN(d.getTime()) ? "—" : d.toLocaleString();
    }
    const d = new Date(v);
    return isNaN(d.getTime()) ? String(v) : d.toLocaleString();
  }

  function formatSize(n) {
    if (n == null || n === 0) return "0 B";
    const k = 1024;
    const u = ["B", "KB", "MB", "GB"];
    let i = 0;
    while (n >= k && i < u.length - 1) {
      n /= k;
      i++;
    }
    return n.toFixed(1) + " " + u[i];
  }

  function escapeHtml(s) {
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  function encodePath(p) {
    return p.split("/").map(function (s) { return encodeURIComponent(s); }).join("/");
  }

  function renderRows(filteredFiles, displayFiles = null) {
    const filesToRender = displayFiles || applyClientSideFilters(filteredFiles || files);
    const tbody = getTableBody();
// #region agent log
fetch('http://127.0.0.1:7242/ingest/adfd807a-ef66-43c3-a0f8-1f2210dc4305',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'media-manager.js:renderRows',message:'Rendering rows',data:{tbodyExists:!!tbody,filesCount:filesToRender.length,currentTab:currentTab,virtualScroll:virtualScrollEnabled,visibleRange:virtualScrollEnabled ? visibleRange : null},timestamp:Date.now(),sessionId:'debug-session',runId:'media-manager-debug',hypothesisId:'render'})}).catch(()=>{});
// #endregion
    if (!tbody) return;

    // Clear existing content
    tbody.innerHTML = "";

    // For virtual scrolling, add spacer rows
    if (virtualScrollEnabled && visibleRange.start > 0) {
      const spacerRow = document.createElement('tr');
      spacerRow.style.height = `${visibleRange.start * 60}px`; // Approximate row height
      spacerRow.className = 'spacer-row';
      tbody.appendChild(spacerRow);
    }

    filesToRender.forEach((f) => {
      const rel = (f.relative_path || f.file_path || "").replace(/\\/g, "/");
      const name = f.name || rel.split("/").pop() || "—";
      const viewerUrl = (viewerBase || "").replace(/\/+$/, "") + "/" + encodePath(rel);
      const editUrl = (formEditBase || "").replace(/\/+$/, "") + "/" + encodePath(rel);
      const deleteUrl = (deleteBase || "").replace(/\/+$/, "") + "/" + encodePath(rel);

      // Check if this file can be opened in Durgasman
      const canOpenInDurgasman = currentTab === 'postman' || currentTab === 'endpoints' || currentTab === 'n8n' || currentTab === 'pages' || currentTab === 'relationships';
      const durgasmanUrl = canOpenInDurgasman ? "/durgasman/import/?type=" + encodeURIComponent(currentTab) + "&file=" + encodeURIComponent(rel) : null;

      const tr = document.createElement("tr");
      tr.className = "hover:bg-gray-50 dark:hover:bg-gray-700/50";

      let actionsHtml =
        "<a href='" + escapeHtml(viewerUrl) + "' class='text-sm text-blue-600 dark:text-blue-400 hover:underline'>View</a>" +
        "<a href='" + escapeHtml(editUrl) + "' class='text-sm text-gray-600 dark:text-gray-400 hover:underline'>Edit</a>" +
        "<a href='" + escapeHtml(deleteUrl) + "' class='text-sm text-red-600 dark:text-red-400 hover:underline'>Delete</a>";

      // Add Durgasman button for compatible files
      if (canOpenInDurgasman && durgasmanUrl) {
        actionsHtml +=
          "<a href='" + escapeHtml(durgasmanUrl) + "' class='inline-flex items-center px-3 py-1 text-xs font-medium text-orange-600 bg-orange-50 hover:bg-orange-100 dark:bg-orange-900/20 dark:text-orange-400 dark:hover:bg-orange-900/40 rounded-full transition-colors ml-2' title='Open in Durgasman API Tester'>" +
          "<svg class='w-3 h-3 mr-1.5' fill='none' stroke='currentColor' viewBox='0 0 24 24'>" +
          "<path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M13 10V3L4 14h7v7l9-11h-7z'/>" +
          "</svg>" +
          "Open in Durgasman" +
          "</a>";
      }

      tr.innerHTML =
        "<td class='px-4 py-3'><input type='checkbox' class='file-checkbox rounded border-gray-300 dark:border-gray-600 text-blue-600 dark:text-blue-400 focus:ring-blue-500 dark:focus:ring-blue-400' data-file-path='" + escapeHtml(rel) + "'></td>" +
        "<td class='px-4 py-3 text-sm text-gray-900 dark:text-gray-100'>" +
        "<a href='" + escapeHtml(viewerUrl) + "' class='text-blue-600 dark:text-blue-400 hover:underline'>" + escapeHtml(name) + "</a>" +
        "</td>" +
        "<td class='px-4 py-3 text-sm text-gray-500 dark:text-gray-400'>" + escapeHtml(formatDate(f.modified)) + "</td>" +
        "<td class='px-4 py-3 text-sm text-gray-500 dark:text-gray-400'>" + escapeHtml(formatSize(f.size)) + "</td>" +
        "<td class='px-4 py-3'><span class='px-2 py-0.5 rounded text-xs " + (f.sync_status === "synced" ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400" : "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400") + "'>" + escapeHtml(f.sync_status || "unknown") + "</span></td>" +
        "<td class='px-4 py-3 flex flex-wrap gap-2 items-center'>" + actionsHtml + "</td>";
      tbody.appendChild(tr);

      // Add checkbox event listener
      const checkbox = tr.querySelector('.file-checkbox');
      if (checkbox) {
        checkbox.addEventListener('change', function() {
          toggleFileSelection(rel, this.checked);
        });
      }
    });
  }

  function loadFiles(forceRefresh = false) {
    showLoading(true);
    const cacheKey = getCacheKey(currentTab);

    // Check cache first (unless force refresh requested)
    if (!forceRefresh) {
      const cachedData = getCache(cacheKey);
      if (cachedData) {
        files = cachedData;
        const filteredFiles = applyClientSideFilters(files);
        enableVirtualScrollingIfNeeded(filteredFiles.length);
        const visibleFiles = getVisibleFiles(filteredFiles);
        showLoading(false);
        if (visibleFiles.length === 0) showEmpty(true);
        else {
          showEmpty(false);
          renderRows(filteredFiles, visibleFiles);
        }
        return Promise.resolve(); // Return resolved promise for consistency
      }
    }

    const url = listUrl + "?resource_type=" + encodeURIComponent(currentTab);

// #region agent log
fetch('http://127.0.0.1:7242/ingest/adfd807a-ef66-43c3-a0f8-1f2210dc4305',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'media-manager.js:loadFiles',message:'Loading files for tab',data:{currentTab:currentTab,url:url,cacheUsed:!forceRefresh && !!getCache(cacheKey)},timestamp:Date.now(),sessionId:'debug-session',runId:'media-manager-debug',hypothesisId:'api_call'})}).catch(()=>{});
// #endregion

    return fetch(url, { headers: { "Accept": "application/json" } })
      .then((r) => {
        if (!r.ok) {
          throw new Error(`HTTP ${r.status}: ${r.statusText}`);
        }

// #region agent log
fetch('http://127.0.0.1:7242/ingest/adfd807a-ef66-43c3-a0f8-1f2210dc4305',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'media-manager.js:loadFiles',message:'API response received',data:{status:r.status,statusText:r.statusText},timestamp:Date.now(),sessionId:'debug-session',runId:'media-manager-debug',hypothesisId:'api_response'})}).catch(()=>{});
// #endregion

        return r.json();
      })
      .then((data) => {

// #region agent log
fetch('http://127.0.0.1:7242/ingest/adfd807a-ef66-43c3-a0f8-1f2210dc4305',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'media-manager.js:loadFiles',message:'API data parsed',data:{success:data.success,total:data.total,filesCount:(data.data||[]).length},timestamp:Date.now(),sessionId:'debug-session',runId:'media-manager-debug',hypothesisId:'api_data'})}).catch(()=>{});
// #endregion

        if (data.success) {
          files = data.data || [];
          setCache(cacheKey, files); // Cache the response
          const filteredFiles = applyClientSideFilters(files);
          enableVirtualScrollingIfNeeded(filteredFiles.length);
          const visibleFiles = getVisibleFiles(filteredFiles);
          showLoading(false);
          if (visibleFiles.length === 0) showEmpty(true);
          else {
            showEmpty(false);
            renderRows(filteredFiles, visibleFiles);
          }
        } else {
          throw new Error(data.error || 'API returned unsuccessful response');
        }
      })
      .catch((e) => {

// #region agent log
fetch('http://127.0.0.1:7242/ingest/adfd807a-ef66-43c3-a0f8-1f2210dc4305',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'media-manager.js:loadFiles',message:'API call failed',data:{error:e.message},timestamp:Date.now(),sessionId:'debug-session',runId:'media-manager-debug',hypothesisId:'api_error'})}).catch(()=>{});
// #endregion

        console.error("Media Manager load error:", e);
        showLoading(false);
        showError("Failed to load files. Please check your connection and try again.", () => loadFiles(true));
      });
  }

  function init() {
// #region agent log
fetch('http://127.0.0.1:7242/ingest/adfd807a-ef66-43c3-a0f8-1f2210dc4305',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'media-manager.js:init',message:'Initializing Media Manager',data:{currentTab:currentTab,tabButtonsCount:tabButtons().length,tabPanelsCount:tabPanels().length},timestamp:Date.now(),sessionId:'debug-session',runId:'media-manager-debug',hypothesisId:'initialization'})}).catch(()=>{});
// #endregion

    tabButtons().forEach((btn) => {
      btn.addEventListener("click", () => {
        const t = btn.getAttribute("data-media-tab");
// #region agent log
fetch('http://127.0.0.1:7242/ingest/adfd807a-ef66-43c3-a0f8-1f2210dc4305',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'media-manager.js:tabClick',message:'Tab button clicked',data:{tab:t},timestamp:Date.now(),sessionId:'debug-session',runId:'media-manager-debug',hypothesisId:'tab_click'})}).catch(()=>{});
// #endregion
        if (t) setTab(t);
      });
    });

    // Bulk action event listeners
    document.getElementById('select-all-checkbox')?.addEventListener('change', function() {
      if (this.checked) {
        selectAllFiles();
      } else {
        clearSelection();
      }
    });

    document.getElementById('select-all-btn')?.addEventListener('click', function(e) {
      e.preventDefault();
      selectAllFiles();
    });

    document.getElementById('clear-selection-btn')?.addEventListener('click', function(e) {
      e.preventDefault();
      clearSelection();
    });

    document.getElementById('bulk-sync-btn')?.addEventListener('click', function() {
      bulkSyncFiles();
    });

    document.getElementById('bulk-delete-btn')?.addEventListener('click', function() {
      bulkDeleteFiles();
    });

    // Filter event listeners
    document.getElementById('file-search')?.addEventListener('input', function() {
      // Debounce search input
      clearTimeout(this.searchTimeout);
      this.searchTimeout = setTimeout(updateFilters, 300);
    });

    document.getElementById('sync-status-filter')?.addEventListener('change', updateFilters);
    document.getElementById('sort-by-filter')?.addEventListener('change', updateFilters);
    document.getElementById('sort-order-filter')?.addEventListener('change', updateFilters);

// #region agent log
fetch('http://127.0.0.1:7242/ingest/adfd807a-ef66-43c3-a0f8-1f2210dc4305',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'media-manager.js:init',message:'Setting initial tab',data:{initialTab:currentTab},timestamp:Date.now(),sessionId:'debug-session',runId:'media-manager-debug',hypothesisId:'initial_tab'})}).catch(()=>{});
// #endregion
    setTab(currentTab);

    // Start background cache refresh
    scheduleBackgroundRefresh();
  }

  // Statistics panel toggle functionality
  function initStatsToggle() {
    const toggleBtn = document.getElementById('stats-toggle-btn');
    const statsPanel = document.getElementById('stats-panels');
    const toggleText = document.getElementById('stats-toggle-text');
    const toggleIcon = document.getElementById('stats-toggle-icon');

    if (toggleBtn && statsPanel) {
      toggleBtn.addEventListener('click', function() {
        const isExpanded = toggleBtn.getAttribute('aria-expanded') === 'true';
        statsPanel.classList.toggle('hidden');
        toggleBtn.setAttribute('aria-expanded', !isExpanded);
        toggleText.textContent = isExpanded ? 'Show' : 'Hide';
        toggleIcon.style.transform = isExpanded ? 'rotate(180deg)' : '';
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function() {
      init();
      initStatsToggle();
    });
  } else {
    init();
    initStatsToggle();
  }

  window.MediaManager = { setTab, loadFiles };
})();
