// frontend/static/js/papriapp.js

// Global constants passed from Django template (papriapp.html)
// const CSRF_TOKEN, USER_IS_AUTHENTICATED, USER_EMAIL, USER_FIRST_NAME, USER_LAST_NAME, API_BASE_URL;

document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Element References ---
    const viewContainer = document.getElementById('view-container');
    const sidebar = document.getElementById('sidebar');
    const sidebarBackdrop = document.getElementById('sidebar-backdrop');
    const hamburgerMenuButton = document.getElementById('hamburger-menu');
    const dynamicTooltip = document.getElementById('dynamic-tooltip');

    // Search View Elements
    const searchForm = document.getElementById('papri-search-form');
    const searchQueryInput = document.getElementById('search-query-input');
    const searchImageInput = document.getElementById('search-image-input');
    const searchImageFilename = document.getElementById('search-image-filename');
    const searchSourceUrlInput = document.getElementById('search-source-url');
    const startSearchButton = document.getElementById('start-search-button');
    const clearSearchFormButton = document.getElementById('clear-search-form-button');
    const searchStatusDiv = document.getElementById('search-status');
    const searchResultsContainer = document.getElementById('search-results-container');
    const paginationControls = document.getElementById('pagination-controls');
    
    // Filter Elements
    const toggleFiltersButton = document.getElementById('toggle-filters-button');
    const toggleFiltersText = document.getElementById('toggle-filters-text');
    const searchFiltersContainer = document.getElementById('search-filters-container');
    const filterPlatformSelect = document.getElementById('filter-platform');
    const filterDurationSelect = document.getElementById('filter-duration');
    const filterDateAfterInput = document.getElementById('filter-date-after');
    // const filterDateBeforeInput = document.getElementById('filter-date-before'); // If you add this
    const filterSortBySelect = document.getElementById('filter-sort-by');
    const applyFiltersButton = document.getElementById('apply-filters-button');
    const clearFiltersButton = document.getElementById('clear-filters-button');

    // User Profile Elements
    const sidebarUserAvatar = document.getElementById('sidebar-user-avatar').querySelector('.user-initial');
    const sidebarUserName = document.getElementById('sidebar-user-name');
    const sidebarUserEmail = document.getElementById('sidebar-user-email');
    const adminPanelLink = document.getElementById('admin-panel-link'); // For staff users
    const logoutButton = document.getElementById('logout-button');

    // Settings View (if you populate profile info there too)
    const userNameSettings = document.querySelector('#settings-view .user-name-settings');
    const userEmailSettings = document.querySelector('#settings-view .user-email-settings');

    let activePlyrInstance = null;
    let tooltipTimeout = null;
    let currentSearchTaskId = null;
    let pollingInterval = null;
    
    // Store pagination and filter state globally for the current search session
    let currentApiPage = 1;
    let currentApiFilters = {}; 
    let currentApiSortBy = "relevance";
    let currentApiNextPageUrl = null;
    let currentApiPreviousPageUrl = null;
    let currentApiTotalResultsCount = 0;

    // --- Logger ---
    function logger(message, type = 'log', data = null) {
        const prefix = `[PapriApp]`;
        if (data) {
            console[type](`${prefix} ${message}`, data);
        } else {
            console[type](`${prefix} ${message}`);
        }
    }
    
    // --- Initialization ---
    function initializeApp() {
        if (typeof USER_IS_AUTHENTICATED === 'undefined' || !USER_IS_AUTHENTICATED) {
            logger("User not authenticated. Redirecting to login.", "warn");
            window.location.href = (API_BASE_URL || '') + "/accounts/google/login/?process=login&next=/app/";
            return;
        }
        initLucideIcons(); // Initial call
        setupNavigation();
        setupUserProfile();
        setupSearchForm();
        setupFilterControls();
        setupLogout();
        
        // Handle initial hash for view switching or load default view
        const initialHash = window.location.hash || '#search'; // Default to #search
        const targetViewId = initialHash.substring(1) + '-view';
        switchView(targetViewId, true);
        
        window.addEventListener('hashchange', () => {
            const hash = window.location.hash || '#search';
            switchView(hash.substring(1) + '-view', true);
        });
        logger("Papri App Initialized for authenticated user.");
    }

    function initLucideIcons() {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
            logger("Lucide icons created/refreshed.");
        } else {
            logger('Lucide icons library not found.', 'warn');
        }
    }

    function setupNavigation() {
        document.querySelectorAll('#sidebar .nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = item.getAttribute('data-target');
                if (targetId) {
                    switchView(targetId);
                    if (item.getAttribute('href')) window.location.hash = item.getAttribute('href');
                }
            });
        });

        if (hamburgerMenuButton && sidebar && sidebarBackdrop) {
            hamburgerMenuButton.addEventListener('click', () => toggleSidebar(true));
            sidebarBackdrop.addEventListener('click', () => toggleSidebar(false));
        }
        // Tooltip setup
        document.body.addEventListener('mouseover', handleTooltipShow);
        document.body.addEventListener('mouseout', handleTooltipHide);
        document.body.addEventListener('focusin', handleTooltipShow); // For keyboard accessibility
        document.body.addEventListener('focusout', handleTooltipHide);
    }
    
    function switchView(targetViewId, isInitialOrHistory = false) {
        logger(`Switching to view: ${targetViewId}`);
        destroyActivePlayer(); // Destroy player before switching views
        
        viewContainer.querySelectorAll('.app-view').forEach(view => view.classList.add('hidden'));
        const targetView = document.getElementById(targetViewId);
        
        if (targetView) {
            targetView.classList.remove('hidden');
            // Update active nav item
            document.querySelectorAll('#sidebar .nav-item').forEach(item => {
                item.classList.toggle('active', item.getAttribute('data-target') === targetViewId);
            });
        } else {
            logger(`Target view '${targetViewId}' not found, defaulting to search-view.`, 'warn');
            document.getElementById('search-view')?.classList.remove('hidden');
            document.querySelector('#sidebar .nav-item[data-target="search-view"]')?.classList.add('active');
            if (window.location.hash !== '#search' && !isInitialOrHistory) window.location.hash = '#search';
        }
        
        if (!isInitialOrHistory && window.innerWidth < 768) {
             toggleSidebar(false);
        }
        initLucideIcons(); // Re-run if new icons are revealed
    }

    function toggleSidebar(show) {
        // ... (your existing logic from papriapp.js V4 or Step 41 HTML example)
        if (sidebar && sidebarBackdrop) {
           if (show) {
                sidebar.classList.remove('-translate-x-full'); sidebar.classList.add('translate-x-0');
                sidebarBackdrop.classList.remove('hidden'); sidebarBackdrop.classList.add('opacity-100');
            } else {
                sidebar.classList.remove('translate-x-0'); sidebar.classList.add('-translate-x-full');
                sidebarBackdrop.classList.remove('opacity-100'); sidebarBackdrop.classList.add('hidden');
            }
        }
    }

    function setupUserProfile() {
        if (USER_IS_AUTHENTICATED) {
            const displayName = (USER_FIRST_NAME || USER_LAST_NAME) ? `${USER_FIRST_NAME || ''} ${USER_LAST_NAME || ''}`.trim() : (USER_EMAIL ? USER_EMAIL.split('@')[0] : "User");
            const initial = displayName.charAt(0).toUpperCase() || 'P';

            if (sidebarUserAvatar) sidebarUserAvatar.textContent = initial;
            if (sidebarUserName) sidebarUserName.textContent = displayName;
            if (sidebarUserEmail) sidebarUserEmail.textContent = USER_EMAIL || "No email";
            
            // For settings page
            if (userNameSettings) userNameSettings.textContent = displayName;
            if (userEmailSettings) userEmailSettings.textContent = USER_EMAIL || "No email";

            // Show admin link if user is staff (requires passing is_staff from Django)
            // For now, assume not staff unless explicitly told by Django context
            // if (USER_IS_STAFF && adminPanelLink) adminPanelLink.style.display = 'flex';
            
        } else {
            logger("User profile setup skipped: User not authenticated.", "warn");
        }
    }

    function setupLogout() {
        if (logoutButton) {
            logoutButton.addEventListener('click', (e) => {
                e.preventDefault();
                if (confirm('Are you sure you want to log out?')) {
                    const logoutForm = document.createElement('form');
                    logoutForm.method = 'POST';
                    logoutForm.action = (API_BASE_URL || '') + "/accounts/logout/"; 
                    const csrfInput = document.createElement('input');
                    csrfInput.type = 'hidden'; csrfInput.name = 'csrfmiddlewaretoken'; csrfInput.value = CSRF_TOKEN;
                    logoutForm.appendChild(csrfInput); document.body.appendChild(logoutForm);
                    logoutForm.submit();
                }
            });
        }
    }

    function setupSearchForm() {
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                currentApiPage = 1; // Reset to first page for new search from form
                // Filters and sort are collected from UI just before initiating search
                collectCurrentFilterAndSortState(); 
                initiateNewSearchTask();
            });
        }
        if (searchImageInput && searchImageFilename) {
            searchImageInput.addEventListener('change', () => {
                searchImageFilename.textContent = searchImageInput.files.length > 0 ? searchImageInput.files[0].name : '';
            });
        }
        if (clearSearchFormButton) {
            clearSearchFormButton.addEventListener('click', () => {
                searchForm.reset(); // Resets form fields
                if (searchImageFilename) searchImageFilename.textContent = '';
                searchQueryInput.focus();
            });
        }
        if (searchResultsContainer) {
            searchResultsContainer.addEventListener('click', handleResultCardAction);
        }
    }
    
    function setupFilterControls() {
        if (toggleFiltersButton && searchFiltersContainer && toggleFiltersText) {
            toggleFiltersButton.addEventListener('click', () => {
                searchFiltersContainer.classList.toggle('hidden');
                const isHidden = searchFiltersContainer.classList.contains('hidden');
                toggleFiltersText.textContent = isHidden ? 'Show Filters' : 'Hide Filters';
                toggleFiltersButton.setAttribute('aria-expanded', String(!isHidden));
                lucide.createIcons(); // Re-render if icon changes (e.g. filter to x)
            });
        }
        if (applyFiltersButton) {
            applyFiltersButton.addEventListener('click', () => {
                currentApiPage = 1; 
                collectCurrentFilterAndSortState();
                // If a search task was already completed, fetch results with new filters/sort
                // Otherwise, a new search will pick up these filters.
                if(currentSearchTaskId && searchStatusDiv.dataset.taskStatus === 'completed') {
                    fetchAndDisplayResults(currentSearchTaskId, currentApiPage, currentApiFilters, currentApiSortBy);
                } else if (currentSearchTaskId && searchStatusDiv.dataset.taskStatus === 'processing') {
                    // Optionally, backend could support updating filters for an in-progress task (more complex)
                    // For V1, user might have to wait or start a new search if they change filters mid-search.
                    showStatusMessage("Filters will apply once current search completes, or start a new search.", "info", searchStatusDiv);
                } else { // No active or completed task, new search will use these filters
                    initiateNewSearchTask();
                }
            });
        }
        if (clearFiltersButton) {
            clearFiltersButton.addEventListener('click', () => {
                if(filterPlatformSelect) filterPlatformSelect.value = "";
                if(filterDurationSelect) filterDurationSelect.value = "";
                if(filterDateAfterInput) filterDateAfterInput.value = "";
                if(filterSortBySelect) filterSortBySelect.value = "relevance";
                
                currentApiPage = 1;
                collectCurrentFilterAndSortState(); // This will clear currentApiFilters and reset sort
                // Similar logic to applyFiltersButton: re-fetch or trigger new search
                if(currentSearchTaskId && searchStatusDiv.dataset.taskStatus === 'completed') {
                    fetchAndDisplayResults(currentSearchTaskId, currentApiPage, currentApiFilters, currentApiSortBy);
                } else {
                    initiateNewSearchTask(); // Or simply clear results if desired on "Clear Filters"
                }
            });
        }
    }

    function collectCurrentFilterAndSortState() {
        currentApiFilters = {};
        if (filterPlatformSelect && filterPlatformSelect.value) currentApiFilters.platform = filterPlatformSelect.value;
        if (filterDurationSelect && filterDurationSelect.value) {
            const dur = filterDurationSelect.value;
            if (dur === "short") currentApiFilters.duration_max = 300;
            else if (dur === "medium") { currentApiFilters.duration_min = 300; currentApiFilters.duration_max = 1200; }
            else if (dur === "long") currentApiFilters.duration_min = 1200;
        }
        if (filterDateAfterInput && filterDateAfterInput.value) currentApiFilters.date_after = filterDateAfterInput.value;
        currentApiSortBy = (filterSortBySelect && filterSortBySelect.value) ? filterSortBySelect.value : "relevance";
        logger("Collected Filters: " + JSON.stringify(currentApiFilters) + ", Sort: " + currentApiSortBy, 'debug');
    }

    async function initiateNewSearchTask() {
        destroyActivePlayer();
        clearPolling();
        searchResultsContainer.innerHTML = '<p class="text-center text-slate-500 italic py-8">Initializing your multi-modal Papri AI search...</p>';
        paginationControls.classList.add('hidden'); paginationControls.innerHTML = '';

        const queryText = searchQueryInput.value.trim();
        const imageFile = searchImageInput.files[0];
        const sourceUrl = searchSourceUrlInput.value.trim(); // Optional

        if (!queryText && !imageFile) {
            showStatusMessage('Please provide a text query or upload an image to start a search.', 'error', searchStatusDiv);
            return;
        }

        const formData = new FormData();
        if (queryText) formData.append('query_text', queryText);
        if (imageFile) formData.append('query_image', imageFile);
        if (sourceUrl) formData.append('video_url', sourceUrl);
        // Add collected filters if they should be sent at initiation (backend currently expects this)
        formData.append('filters', JSON.stringify(currentApiFilters));


        showStatusMessage('<span><span class="spinner mr-2"></span>Initiating Papri AI Search...</span>', 'loading', searchStatusDiv);
        if(startSearchButton) startSearchButton.disabled = true;

        try {
            const response = await fetch((API_BASE_URL || '') + '/api/search/initiate/', {
                method: 'POST', headers: { 'X-CSRFToken': CSRF_TOKEN }, body: formData,
            });
            if (!response.ok) {
                const errData = await response.json().catch(() => ({error:`Server error ${response.status}`}));
                throw new Error(errData.error || `HTTP Error: ${response.status}`);
            }
            const data = await response.json(); // Expects SearchTaskSerializer data
            currentSearchTaskId = data.id;
            searchStatusDiv.dataset.taskStatus = data.status; // Store current status
            logger(`Search task initiated. ID: ${currentSearchTaskId}, Status: ${data.status}`);
            showStatusMessage(`<span><span class="spinner mr-2"></span>Search started (ID: ${currentSearchTaskId.substring(0,8)}...). Awaiting results...</span>`, 'loading', searchStatusDiv);
            startPollingStatus(currentSearchTaskId);

        } catch (error) {
            logger(`Search initiation error: ${error.message}`, 'error', error);
            showStatusMessage(`Search initiation failed: ${error.message}`, 'error', searchStatusDiv);
            currentSearchTaskId = null; if(startSearchButton) startSearchButton.disabled = false;
        }
    }

    function startPollingStatus(taskId) {
        clearPolling(); // Ensure no other poll is running for a different task
        logger(`Polling status for task ID: ${taskId}`);
        pollingInterval = setInterval(async () => {
            if (currentSearchTaskId !== taskId) { // If a new search started, stop this poll
                clearPolling(); return;
            }
            try {
                const response = await fetch((API_BASE_URL || '') + `/api/search/status/${taskId}/`);
                if (!response.ok) { /* ... (error handling for 404, etc. as in Step 41) ... */ 
                    if (response.status === 404) {showStatusMessage(`Task ${taskId.substring(0,8)} not found.`, 'error', searchStatusDiv); clearPolling(); currentSearchTaskId=null; if(startSearchButton) startSearchButton.disabled=false; return;}
                    throw new Error(`HTTP ${response.status}`);
                }
                const data = await response.json();
                searchStatusDiv.dataset.taskStatus = data.status;

                if (data.status === 'completed' || data.status === 'partial_results') {
                    clearPolling();
                    showStatusMessage(`Task ${taskId.substring(0,8)} complete! Fetching results...`, 'success', searchStatusDiv);
                    fetchAndDisplayResults(taskId, currentApiPage, currentApiFilters, currentApiSortBy);
                    if(startSearchButton) startSearchButton.disabled = false;
                } else if (data.status === 'failed') {
                    clearPolling();
                    showStatusMessage(`Search failed for task ${taskId.substring(0,8)}: ${data.error_message || 'Unknown processing error.'}`, 'error', searchStatusDiv);
                    currentSearchTaskId = null; if(startSearchButton) startSearchButton.disabled = false;
                } else { 
                    showStatusMessage(`<span><span class="spinner mr-2"></span>AI processing (Status: ${data.status})...</span>`, 'loading', searchStatusDiv);
                }
            } catch (error) { logger(`Polling error: ${error.message}`, 'error'); /* Consider stopping poll after N errors */ }
        }, 4000); // Poll every 4 seconds
    }

    function clearPolling() {
        if (pollingInterval) { clearInterval(pollingInterval); pollingInterval = null; logger("Polling cleared.");}
    }

    async function fetchAndDisplayResults(taskId, page = 1, filters = {}, sortBy = "relevance") {
        logger(`Workspaceing results for Task: ${taskId}, Page: ${page}, Filters: ${JSON.stringify(filters)}, Sort: ${sortBy}`);
        showStatusMessage('<span><span class="spinner mr-2"></span>Loading results page...</span>', 'loading', searchStatusDiv);
        if(startSearchButton) startSearchButton.disabled = true;

        let queryParams = `?page=${page}&sort_by=${sortBy}`;
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== "") { // Ensure value is meaningful
                queryParams += `&${encodeURIComponent(key)}=${encodeURIComponent(value)}`;
            }
        });
        
        try {
            const response = await fetch((API_BASE_URL || '') + `/api/search/results/${taskId}/${queryParams}`);
            if (!response.ok) throw new Error(`HTTP ${response.status} fetching results`);
            const data = await response.json(); // Expects DRF paginated response

            searchResultsContainer.innerHTML = ''; 
            if (data.results_data && data.results_data.length > 0) {
                displayResultCards(data.results_data); // data.results_data is the key from SearchResultsView
                currentApiNextPageUrl = data.next;
                currentApiPreviousPageUrl = data.previous;
                currentApiTotalResultsCount = data.count;
                currentApiPage = page; // Update current page
                setupPaginationControls();
                searchStatusDiv.classList.add('hidden'); // Hide status on successful display
            } else {
                searchResultsContainer.innerHTML = '<p class="text-center text-slate-500 italic py-8">No relevant results found for this page/filter combination.</p>';
                paginationControls.innerHTML = ''; paginationControls.classList.add('hidden');
                if(page === 1) showStatusMessage('No results found for your query.', 'info', searchStatusDiv);
            }
        } catch (error) {
            logger(`Workspace results error: ${error.message}`, 'error', error);
            showStatusMessage(`Failed to fetch results: ${error.message}`, 'error', searchStatusDiv);
            searchResultsContainer.innerHTML = '<p class="text-center text-red-500 italic py-8">Error loading results. Please try again.</p>';
        } finally {
            if(startSearchButton) startSearchButton.disabled = false;
        }
    }

    function displayResultCards(results) {
        results.forEach(video_result => {
            const card = createResultCardElement(video_result);
            searchResultsContainer.appendChild(card);
        });
        lucide.createIcons(); // Refresh icons
    }

    function createResultCardElement(video_result) { // Main card creation function (from Step 41)
        const card = document.createElement('div');
        card.id = `result-papri-${video_result.id}`; 
        card.className = 'result-card bg-white p-3 sm:p-4 rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-200 border border-slate-200 flex flex-col md:flex-row gap-4 overflow-hidden';

        const title = video_result.title || 'Untitled Video';
        const thumbnailUrl = video_result.primary_thumbnail_url || `https://via.placeholder.com/320x180.png?text=No+Thumb`;
        let description = video_result.description || 'No description available.';
        if (description.length > 180) description = description.substring(0, 177) + '...';
        
        const pubDateObj = video_result.publication_date ? new Date(video_result.publication_date) : null;
        const publicationDate = pubDateObj ? pubDateObj.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : 'N/A';
        
        const primarySource = video_result.sources && video_result.sources.length > 0 ? video_result.sources[0] : {};
        const sourcePlatform = primarySource.platform_name || 'Unknown';
        const originalUrl = primarySource.original_url || '#';
        
        const textSnippet = video_result.text_snippet;
        const matchTypes = video_result.match_types || [];
        const bestMatchTimestampMs = video_result.best_match_timestamp_ms;

        let matchInfoHtml = '';
        if (matchTypes.length > 0) {
            let typesString = matchTypes.map(type => {
                const typeMap = {'text_kw':'Keywords', 'text_sem':'Text Meaning', 'vis_cnn':'Image Content', 'vis_phash':'Similar Image', 'fallback_date':'Recent'};
                return typeMap[type] || type;
            }).join(', ');
            matchInfoHtml += `<p class="text-xs text-indigo-600 font-semibold mt-1.5">Matched via: <span class="text-indigo-500">${typesString}</span></p>`;
        }
        if (textSnippet) {
            const cleanSnippet = textSnippet.replace(/</g, "&lt;").replace(/>/g, "&gt;"); // Basic sanitize
            matchInfoHtml += `<div class="mt-1.5 text-xs text-slate-600 italic bg-slate-50 p-2 rounded-md border border-slate-200 max-h-20 overflow-y-auto"><strong class="text-slate-700">Snippet:</strong> "${cleanSnippet}"</div>`;
        }
        if (bestMatchTimestampMs !== null && bestMatchTimestampMs !== undefined) {
            matchInfoHtml += `<p class="text-xs text-green-600 font-semibold mt-1">Key visual match around: ${formatDuration(bestMatchTimestampMs / 1000)}</p>`;
            card.dataset.bestMatchTimestamp = bestMatchTimestampMs / 1000;
        }
        
        // Data attributes for Plyr
        const videoPlatformId = primarySource.platform_video_id || video_result.id; // Use platform_video_id if available
        let plyrProvider = 'html5'; // Default
        let plyrEmbedId = primarySource.embed_url || originalUrl;

        if (sourcePlatform.toLowerCase().includes('youtube')) { plyrProvider = 'youtube'; plyrEmbedId = videoPlatformId; }
        else if (sourcePlatform.toLowerCase().includes('vimeo')) { plyrProvider = 'vimeo'; plyrEmbedId = videoPlatformId; }
        // For direct MP4s, provider remains 'html5' and embedId is the URL

        card.dataset.plyrProvider = plyrProvider;
        card.dataset.plyrEmbedId = plyrEmbedId;

        card.innerHTML = `
            <div class="w-full md:w-48 lg:w-56 flex-shrink-0">
                <div class="aspect-video bg-slate-200 rounded-lg overflow-hidden relative group thumbnail-container cursor-pointer" 
                     aria-label="Play video: ${title}">
                    <img src="${thumbnailUrl}" alt="Thumbnail for ${title}" class="w-full h-full object-cover" loading="lazy">
                    <div class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 group-hover:bg-opacity-60 transition-all duration-200">
                        <i data-lucide="play" class="w-12 h-12 text-white opacity-0 group-hover:opacity-90 transform group-hover:scale-110 transition-all duration-200 pointer-events-none"></i>
                    </div>
                </div>
                <p class="text-xs text-center text-slate-500 mt-1.5 truncate" title="Source: ${sourcePlatform}">Source: ${sourcePlatform}</p>
            </div>

            <div class="flex-grow min-w-0">
                <h3 class="text-base sm:text-lg font-semibold text-indigo-700 mb-0.5 line-clamp-2 hover:text-indigo-800 transition-colors">
                    <a href="${originalUrl}" target="_blank" rel="noopener noreferrer" title="${title}">${title}</a>
                </h3>
                <div class="text-xs text-slate-500 mb-1.5 flex flex-wrap gap-x-2 items-center">
                    <span><i data-lucide="calendar-days" class="inline-block w-3 h-3 mr-0.5 opacity-70"></i> ${publicationDate}</span>
                    <span><i data-lucide="clock" class="inline-block w-3 h-3 mr-0.5 opacity-70"></i> ${formatDuration(video_result.duration_seconds)}</span>
                    ${video_result.relevance_score > 0 ? `<span><i data-lucide="bar-chart-2" class="inline-block w-3 h-3 mr-0.5 opacity-70"></i> Score: ${video_result.relevance_score.toFixed(2)}</span>` : ''}
                </div>
                <p class="text-sm text-slate-600 line-clamp-3 mb-2 result-description">${description}</p>
                
                <div class="match-info-area">${matchInfoHtml}</div>
                
                <div class="mt-auto pt-2.5 flex flex-wrap gap-2 items-center">
                    <button class="action-button btn-preview-segment" aria-label="Preview best segment" 
                        ${bestMatchTimestampMs === null && bestMatchTimestampMs === undefined ? 'disabled' : ''} title="${bestMatchTimestampMs === null && bestMatchTimestampMs === undefined ? 'No specific segment identified to preview' : 'Preview best matching segment'}"> 
                        <i data-lucide="film" class="action-icon"></i> Segment
                    </button>
                    <a href="${originalUrl}" target="_blank" rel="noopener noreferrer" class="action-button btn-source">
                        <i data-lucide="external-link" class="action-icon"></i> Source
                    </a>
                    <button class="action-button btn-add-collection" disabled title="Coming Soon">
                        <i data-lucide="plus-square" class="action-icon"></i> Collect
                    </button>
                </div>
            </div>
            <div class="video-player-container w-full md:col-span-2 mt-3 hidden rounded-lg overflow-hidden shadow-inner bg-black">
                <video class="papri-video-player" playsinline controls preload="none" style="--plyr-color-main: #4f46e5;"></video>
            </div>
        `;
        return card;
    }
    
    function destroyActivePlayer() {
        if (activePlyrInstance) {
            const oldCard = activePlyrInstance.elements.container.closest('.result-card');
            if (oldCard) {
                 oldCard.querySelector('.video-player-container')?.classList.add('hidden');
            }
            activePlyrInstance.destroy();
            activePlyrInstance = null;
            logger("Previous Plyr instance destroyed.");
        }
    }

    function handleResultCardAction(event) { // For Plyr integration
        const button = event.target.closest('button.action-button, .thumbnail-container');
        if (!button) return;

        const card = button.closest('.result-card');
        if (!card) return;
        
        destroyActivePlayer(); // Destroy any existing player before creating a new one or if clicking away

        if (button.classList.contains('thumbnail-container') || button.classList.contains('btn-preview-segment')) {
            event.preventDefault();
            const playerContainer = card.querySelector('.video-player-container');
            const videoElement = card.querySelector('video.papri-video-player');
            
            if (!playerContainer || !videoElement) { logger("Player elements missing in card.", "error"); return; }

            playerContainer.classList.remove('hidden');
            
            // Set dataset attributes for Plyr based on what's on the card
            videoElement.dataset.plyrProvider = card.dataset.plyrProvider;
            videoElement.dataset.plyrEmbedId = card.dataset.plyrEmbedId;
            
            activePlyrInstance = new Plyr(videoElement, {
                autoplay: true,
                // controls: ['play', 'progress', 'current-time', 'mute', 'volume', 'fullscreen'], // Customize controls
                tooltips: { controls: true, seek: true }
            });

            activePlyrInstance.on('ready', event => {
                const instance = event.detail.plyr;
                const startTime = parseFloat(card.dataset.bestMatchTimestamp);
                if (button.classList.contains('btn-preview-segment') && !isNaN(startTime) && startTime > 0) {
                    instance.currentTime = startTime;
                    logger(`Plyr: Ready. Seeking to best segment: ${startTime}s`);
                } else {
                    logger(`Plyr: Ready. Playing from start.`);
                }
                instance.play();
            });
             activePlyrInstance.on('error', event => {
                logger('Plyr Error:', 'error', event.detail.plyr.source);
                showStatusMessage('Error playing video.', 'error', searchStatusDiv); // Or a local error message
                playerContainer.classList.add('hidden'); // Hide on error
            });
            playerContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    function setupPaginationControls() {
        paginationControls.innerHTML = ''; // Clear
        if (!currentApiTotalResultsCount || currentApiTotalResultsCount === 0) {
            paginationControls.classList.add('hidden'); return;
        }
        paginationControls.classList.remove('hidden');

        const prevDisabled = !currentApiPreviousPageUrl;
        const nextDisabled = !currentApiNextPageUrl;

        // Previous Button
        const prevButton = document.createElement('button');
        prevButton.innerHTML = `<i data-lucide="arrow-left" class="mr-1 h-4 w-4 inline"></i> Previous`;
        prevButton.className = "px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed";
        prevButton.disabled = prevDisabled;
        if (!prevDisabled) {
            prevButton.addEventListener('click', () => {
                currentApiPage--;
                fetchAndDisplayResults(currentSearchTaskId, currentApiPage, currentApiFilters, currentApiSortBy);
            });
        }
        paginationControls.appendChild(prevButton);

        // Page Info
        const pageInfo = document.createElement('span');
        const itemsPerPage = parseInt(document.querySelector('.filter-input')?.dataset?.pageSize || StandardResultsSetPagination.page_size || 12); // Get from settings or default
        const totalPages = Math.ceil(currentApiTotalResultsCount / itemsPerPage);
        pageInfo.textContent = `Page ${currentApiPage} of ${totalPages} (Total: ${currentApiTotalResultsCount})`;
        pageInfo.className = "text-sm text-slate-600 px-3 py-2";
        paginationControls.appendChild(pageInfo);

        // Next Button
        const nextButton = document.createElement('button');
        nextButton.innerHTML = `Next <i data-lucide="arrow-right" class="ml-1 h-4 w-4 inline"></i>`;
        nextButton.className = "px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed";
        nextButton.disabled = nextDisabled;
        if (!nextDisabled) {
            nextButton.addEventListener('click', () => {
                currentApiPage++;
                fetchAndDisplayResults(currentSearchTaskId, currentApiPage, currentApiFilters, currentApiSortBy);
            });
        }
        paginationControls.appendChild(nextButton);
        lucide.createIcons(); // Refresh icons for buttons
    }

    // --- Utility Functions ---
    function formatDuration(totalSeconds) { /* ... (as in Step 41) ... */ 
        if (totalSeconds === null || totalSeconds === undefined || totalSeconds <= 0) return 'N/A';
        const h = Math.floor(totalSeconds / 3600); const m = Math.floor((totalSeconds % 3600) / 60); const s = Math.floor(totalSeconds % 60);
        return (h > 0 ? `${h}:${String(m).padStart(2, '0')}:` : `${String(m).padStart(2, '0')}:`) + String(s).padStart(2, '0');
    }
    function showStatusMessage(message, type = 'info', element) { /* ... (as in Step 41, ensure spinner works) ... */
         if (!element) return; element.innerHTML = message; element.className = 'search-status-message mb-4 p-3 rounded-md text-sm ';
        const typeClasses = {'error': 'bg-red-100 text-red-700','success': 'bg-green-100 text-green-700','loading': 'bg-blue-100 text-blue-700','info': 'bg-yellow-100 text-yellow-700'};
        element.classList.add(...(typeClasses[type] || typeClasses.info).split(' ')); element.classList.remove('hidden');
        if (message.includes('spinner')) initLucideIcons(); // If spinner is a lucide icon
    }
    function handleTooltipShow(e) { /* ... (as defined in your V4 JS or Step 41, ensure dynamicTooltip element exists) ... */
        const target = e.target.closest('[aria-label]'); if (!target || target.disabled) return;
        const label = target.getAttribute('aria-label'); if (!label || !dynamicTooltip) return;
        clearTimeout(tooltipTimeout); dynamicTooltip.textContent = label; dynamicTooltip.classList.remove('hidden');
        requestAnimationFrame(() => { positionTooltip(target); dynamicTooltip.classList.add('opacity-100');});
    }
    function handleTooltipHide() {  /* ... (as defined, ensure dynamicTooltip exists) ... */
        if (!dynamicTooltip) return; dynamicTooltip.classList.remove('opacity-100');
        clearTimeout(tooltipTimeout); tooltipTimeout = setTimeout(() => { if (!dynamicTooltip.classList.contains('opacity-100')) { dynamicTooltip.classList.add('hidden');}}, 300);
    }
    function positionTooltip(targetElement) { /* ... (as defined) ... */
        const rect = targetElement.getBoundingClientRect(); const tooltip = dynamicTooltip;
        tooltip.style.left = '0px'; tooltip.style.top = '0px'; const tooltipRect = tooltip.getBoundingClientRect();
        let top = rect.top - tooltipRect.height - 8; let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
        left = Math.max(5, Math.min(left, window.innerWidth - tooltipRect.width - 5));
        if (top < 5 || (top < 50 && rect.bottom + tooltipRect.height + 8 < window.innerHeight)) { top = rect.bottom + 8;}
        top = Math.max(5, Math.min(top, window.innerHeight - tooltipRect.height - 5));
        tooltip.style.left = `${left}px`; tooltip.style.top = `${top + window.scrollY}px`;
    }

    // --- Start the app ---
    initializeApp();
});
